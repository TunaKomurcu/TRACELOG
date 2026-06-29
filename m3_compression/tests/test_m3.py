"""Sazabi M3 - Test Suite
Run: pytest tests/test_m3.py -v
"""
import sys, os, json, pathlib, pytest
from unittest.mock import patch, MagicMock

# Make m3_compression importable
M3_DIR = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(M3_DIR))

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "sample_logs"

def load_fixture(name: str):
    return (FIXTURES / name).read_text("utf-8").splitlines()


class TestPreFilter:
    """Tests for filter.py pre-filter."""

    def test_removes_debug_lines(self):
        import filter as log_filter
        lines = [
            "[2025-01-15T14:00:01.000Z] [stdout] Normal log line",
            "[2025-01-15T14:00:02.000Z] [stderr] DEBUG: some debug info",
            "[2025-01-15T14:00:03.000Z] [stdout] Another normal line",
            "[2025-01-15T14:00:04.000Z] [stderr] TRACE: verbose trace",
        ]
        result = log_filter.pre_filter(lines)
        assert result.removed_debug == 2
        assert len(result.kept) == 2
        assert not any("DEBUG" in l for l in result.kept)

    def test_collapses_duplicate_lines(self):
        import filter as log_filter
        lines = [
            "[2025-01-15T14:00:01.000Z] [stdout] same message",
            "[2025-01-15T14:00:02.000Z] [stdout] same message",
            "[2025-01-15T14:00:03.000Z] [stdout] same message",
            "[2025-01-15T14:00:04.000Z] [stdout] different message",
        ]
        result = log_filter.pre_filter(lines)
        assert result.removed_duplicate == 2
        assert len(result.kept) == 2

    def test_respects_max_bytes(self):
        import filter as log_filter
        lines = ["x" * 1000] * 100
        result = log_filter.pre_filter(lines, max_bytes=5000)
        total = sum(len(l.encode())+1 for l in result.kept)
        assert total <= 5100 # allow small margin

    def test_filters_large_fixture(self):
        import filter as log_filter
        lines = load_fixture("large_1000_lines.log")
        result = log_filter.pre_filter(lines)
        assert result.removed_debug > 0
        assert len(result.kept) < len(lines)
        assert result.stats()["kept"] == len(result.kept)


class TestFallback:
    """Tests for rule-based fallback summarizer."""

    def test_fallback_normal_run(self):
        import fallback
        lines = load_fixture("normal_run.log")
        result = fallback.rule_based_summary(lines)
        assert "summary" in result
        assert "errors" in result
        assert "anomalies" in result
        assert "root_cause_hint" in result
        assert len(result["summary"]) > 10

    def test_fallback_detects_traceback(self):
        import fallback
        lines = load_fixture("python_traceback.log")
        result = fallback.rule_based_summary(lines)
        # root_cause_hint should mention the actual error
        hint = result["root_cause_hint"].lower()
        assert any(kw in hint for kw in ["operationalerror", "sqlite3", "table", "users_v2"])

    def test_fallback_1000_lines_produces_summary(self):
        """Acceptance criterion 1: 1000-line log -> meaningful summary."""
        import fallback
        lines = load_fixture("large_1000_lines.log")
        result = fallback.rule_based_summary(lines)
        assert result["summary"]
        assert "1000" in result["summary"]
        assert len(result["errors"]) > 0 # has ERROR lines
        assert len(result["anomalies"]) > 0 # has WARNING lines

    def test_fallback_summary_mentions_counts(self):
        import fallback
        lines = ["[2025-01-15T14:00:01.000Z] [stderr] ERROR: disk full"] * 5
        result = fallback.rule_based_summary(lines)
        assert result["errors"]
        assert result["root_cause_hint"]


class TestPipelineFallback:
    """Tests for pipeline without API key (fallback path)."""

    def test_no_api_key_uses_fallback(self):
        """Acceptance criterion 3: no API key -> graceful fallback."""
        import pipeline
        with patch.dict(os.environ, {"GOOGLE_API_KEY": ""}, clear=False):
            lines = load_fixture("normal_run.log")
            result = pipeline.run(lines, session_id="test-session-1")
            assert result.used_llm is False
            assert result.usage is None
            assert result.summary["summary"]
            d = result.to_dict()
            assert d["_meta"]["used_llm"] is False

    def test_pipeline_returns_required_fields(self):
        import pipeline
        with patch.dict(os.environ, {"GOOGLE_API_KEY": ""}, clear=False):
            lines = load_fixture("python_traceback.log")
            result = pipeline.run(lines)
            s = result.summary
            for field in ["summary", "errors", "anomalies", "root_cause_hint"]:
                assert field in s, f"Missing field: {field}"

    def test_pipeline_filter_stats_in_output(self):
        import pipeline
        with patch.dict(os.environ, {"GOOGLE_API_KEY": ""}, clear=False):
            lines = load_fixture("large_1000_lines.log")
            result = pipeline.run(lines, session_id="perf-test")
            d = result.to_dict()
            assert "filter_stats" in d["_meta"]
            assert "kept" in d["_meta"]["filter_stats"]


class TestPipelineWithMockedGemini:
    """Tests that mock the Gemini API to verify LLM path without real key."""

    _MOCK_RESPONSE = {
        "summary": "Application processed 1000 requests. One connection timeout detected. Memory usage elevated.",
        "errors": [{"line": 75, "msg": "ERROR: timeout on attempt 75", "severity": "warning"}],
        "anomalies": ["High latency detected at multiple checkpoints"],
        "root_cause_hint": "Connection timeouts suggest backend service degradation or network issues.",
    }

    def _make_mock_usage(self):
        m = MagicMock()
        m.input_tokens = 2500
        m.output_tokens = 180
        return m

    def test_llm_path_returns_structured_output(self):
        """Acceptance criterion 1: LLM path returns structured JSON."""
        import pipeline, compressor
        mock_usage = self._make_mock_usage()
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "AIza-test-key"}, clear=False):
            with patch("compressor._call_gemini") as mock_call:
                ur = compressor.UsageRecord(session_id="t1", input_tokens=2500, output_tokens=180)
                ur.calculate_cost()
                mock_call.return_value = (self._MOCK_RESPONSE, ur)
                lines = load_fixture("large_1000_lines.log")
                result = pipeline.run(lines, session_id="t1")
                assert result.used_llm is True
                assert result.summary["summary"]
                assert "Application" in result.summary["summary"]

    def test_token_cost_logged(self):
        """Acceptance criterion 4: token cost is recorded."""
        import pipeline, compressor
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "AIza-test-key"}, clear=False):
            with patch("compressor._call_gemini") as mock_call:
                ur = compressor.UsageRecord(session_id="t2", input_tokens=3000, output_tokens=200)
                ur.calculate_cost()
                mock_call.return_value = (self._MOCK_RESPONSE, ur)
                lines = load_fixture("large_1000_lines.log")
                result = pipeline.run(lines, session_id="t2")
                assert result.usage is not None
                assert result.usage.input_tokens == 3000
                assert result.usage.cost_usd > 0
                d = result.to_dict()
                assert d["_meta"]["tokens"]["cost_usd"] > 0


class TestTracebackRootCause:
    """Acceptance criterion 2: traceback -> root_cause_hint correct."""

    def test_python_traceback_root_cause_fallback(self):
        import fallback
        lines = load_fixture("python_traceback.log")
        result = fallback.rule_based_summary(lines)
        hint = result["root_cause_hint"].lower()
        # Must identify the actual Python exception
        assert "operationalerror" in hint or "no such table" in hint or "sqlite3" in hint

    def test_python_traceback_root_cause_mocked_llm(self):
        """Same file, but via mocked LLM path."""
        import pipeline, compressor
        mock_resp = {
            "summary": "Migration failed due to missing table users_v2.",
            "errors": [{"line": 8, "msg": "sqlite3.OperationalError: no such table: users_v2", "severity": "critical"}],
            "anomalies": [],
            "root_cause_hint": "sqlite3.OperationalError: no such table: users_v2 - run pending migrations.",
        }
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "AIza-test-key"}, clear=False):
            with patch("compressor._call_gemini") as mock_call:
                ur = compressor.UsageRecord(session_id="tb", input_tokens=500, output_tokens=100)
                ur.calculate_cost()
                mock_call.return_value = (mock_resp, ur)
                lines = load_fixture("python_traceback.log")
                result = pipeline.run(lines, session_id="tb")
                hint = result.summary["root_cause_hint"].lower()
                assert "sqlite3" in hint or "no such table" in hint or "migration" in hint


class TestRateLimit:
    """Rate limiter unit tests."""

    def test_rate_limiter_tracks_calls(self):
        import compressor
        rl = compressor.RateLimiter(max_calls=5)
        for _ in range(5):
            rl.acquire()
        assert len(rl._calls) == 5

    def test_usage_record_cost_calculation(self):
        import compressor
        ur = compressor.UsageRecord(session_id="x", input_tokens=1_000_000, output_tokens=1_000_000)
        ur.calculate_cost()
        # 1M input @ $0.075 + 1M output @ $0.30 = $0.375 (Gemini 2.0 Flash Lite)
        assert abs(ur.cost_usd - 0.375) < 0.001
