"""Sazabi M4 - Test Suite
Run: pytest tests/test_m4.py -v
"""
import sys, os, pathlib, uuid, pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mem_db(tmp_path, monkeypatch):
    db_file = str(tmp_path / "test_memory.db")
    monkeypatch.setenv("MEMORY_DB_PATH", db_file)
    # Save original sys.path and clean competing paths
    original_path = sys.path.copy()
    m4_dir = str(pathlib.Path(__file__).parent.parent)
    # Remove competing module paths
    sys.path = [p for p in sys.path if not any(x in p for x in ["m1_logger","m2_storage","m3_compression","m5_sandbox","m6_slack"])]
    if m4_dir not in sys.path:
        sys.path.insert(0, m4_dir)
    # Clean stale module references before reimporting
    import importlib
    for mod_key in list(sys.modules.keys()):
        if mod_key in ('db', 'memory', 'api', 'git_tracker') or mod_key.startswith(('m4_memory.',)):
            del sys.modules[mod_key]
    # Import fresh modules in correct order
    import db as db_mod
    importlib.reload(db_mod)
    import memory as mem_mod
    importlib.reload(mem_mod)
    # Import api after db/memory are ready
    import api as api_mod
    importlib.reload(api_mod)
    db_mod.init_db()
    result = (db_mod, mem_mod, api_mod)
    yield result
    # Restore sys.path after test
    sys.path = original_path


@pytest.fixture
def client(mem_db):
    _, _, api_mod = mem_db
    with TestClient(api_mod.app) as c:
        yield c


@pytest.fixture
def m2_db(tmp_path):
    """Separate fixture to verify M2 db isolation."""
    return str(tmp_path / "sazabi.db")


class TestDBLayer:
    def test_init_creates_tables(self, mem_db):
        db_mod, _, _ = mem_db
        import sqlite3
        with sqlite3.connect(db_mod.get_memory_db_path()) as c:
            names={r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type=?", ("table",)).fetchall()}
        assert "agent_steps" in names and "file_snapshots" in names

    def test_insert_and_retrieve_step(self, mem_db):
        db_mod, _, _ = mem_db
        aid = str(uuid.uuid4())
        step_id = db_mod.insert_step(aid, 1, "bash", "ls -la", "listed files")
        assert step_id > 0
        steps = db_mod.get_agent_steps(aid)
        assert len(steps) == 1 and steps[0]["action_type"] == "bash"

    def test_insert_snapshot(self, mem_db):
        db_mod, _, _ = mem_db
        aid = str(uuid.uuid4())
        step_id = db_mod.insert_step(aid, 1, "file_write", "write app.py", "wrote")
        snap_id = db_mod.insert_snapshot(step_id, "app.py", "abc1234", "1 file changed")
        assert snap_id > 0
        snaps = db_mod.get_snapshots_for_step(step_id)
        assert len(snaps) == 1 and snaps[0]["git_hash"] == "abc1234"

    def test_count_steps(self, mem_db):
        db_mod, _, _ = mem_db
        aid = str(uuid.uuid4())
        for s in range(5): db_mod.insert_step(aid, s+1, "bash", f"step {s}", "ok")
        assert db_mod.count_steps(aid) == 5


class TestMemoryLayer:
    def test_record_step_basic(self, mem_db):
        _, mem_mod, _ = mem_db
        aid = str(uuid.uuid4())
        result = mem_mod.record_step(aid, 1, "decision", "choose strategy", "chose A")
        assert "step_id" in result and result["step_id"] > 0
        assert "snapshot_ids" in result

    def test_record_step_with_snapshots(self, mem_db):
        _, mem_mod, _ = mem_db
        aid = str(uuid.uuid4())
        result = mem_mod.record_step(aid, 1, "file_write", "write", "ok", file_paths=["x.py","y.py"])
        assert len(result["snapshot_ids"]) == 2

    def test_build_timeline_structure(self, mem_db):
        db_mod, mem_mod, _ = mem_db
        aid = str(uuid.uuid4())
        for s in range(5): mem_mod.record_step(aid, s+1, "bash", f"cmd {s}", f"res {s}")
        tl = mem_mod.build_timeline(aid)
        assert tl["agent_id"] == aid
        assert tl["total_steps"] == 5
        assert len(tl["steps"]) == 5
        assert "summary" in tl


class TestAcceptanceCriteria:
    def test_20_step_agent_run_and_timeline(self, mem_db):
        """AC1: 20-step agent run and timeline retrieval."""
        _, mem_mod, _ = mem_db
        aid = str(uuid.uuid4())
        actions = ["file_write","bash","api_call","decision"]
        for s in range(20):
            mem_mod.record_step(aid, s+1, actions[s%4], f"detail {s}", f"result {s}")
        tl = mem_mod.build_timeline(aid)
        assert tl["total_steps"] == 20
        assert len(tl["steps"]) == 20
        assert tl["steps"][0]["step_number"] == 1
        assert tl["steps"][19]["step_number"] == 20

    def test_same_file_3_snapshots(self, mem_db):
        """AC2: same file changed 3 times -> 3 separate snapshots."""
        db_mod, mem_mod, _ = mem_db
        aid = str(uuid.uuid4())
        for i in range(3):
            step_id = db_mod.insert_step(aid, i+1, "file_write", "edit app.py", f"edit {i}")
            db_mod.insert_snapshot(step_id, "app.py", f"hash{i}", f"diff {i}")
        snaps = db_mod.get_snapshots_for_file("app.py")
        assert len(snaps) == 3
        hashes = [s["git_hash"] for s in snaps]
        assert "hash0" in hashes and "hash1" in hashes and "hash2" in hashes

    def test_m2_db_not_affected(self, mem_db, m2_db):
        """AC3: M2 DB path is completely separate."""
        db_mod, _, _ = mem_db
        mem_path = db_mod.get_memory_db_path()
        assert mem_path != m2_db
        assert "memory" in mem_path.lower() or "test" in mem_path.lower()


class TestAPIEndpoints:
    def _make_step(self, aid, num, atype="bash"):
        return {"agent_id":aid,"step_number":num,"action_type":atype,
            "action_detail":f"detail {num}","result_summary":f"result {num}","file_paths":[]}

    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200 and r.json()["status"] == "ok"

    def test_post_step(self, client):
        aid = str(uuid.uuid4())
        r = client.post("/memory/steps", json=self._make_step(aid, 1))
        assert r.status_code == 201
        assert "step_id" in r.json()

    def test_timeline_404_unknown_agent(self, client):
        r = client.get("/memory/agent/nonexistent-agent-99/timeline")
        assert r.status_code == 404

    def test_timeline_returns_slack_ready_json(self, client):
        """AC4: timeline endpoint returns Slack-sendable JSON."""
        aid = str(uuid.uuid4())
        for s in range(5): client.post("/memory/steps", json=self._make_step(aid, s+1))
        r = client.get(f"/memory/agent/{aid}/timeline")
        assert r.status_code == 200
        data = r.json()
        assert "agent_id" in data and data["agent_id"] == aid
        assert "total_steps" in data and data["total_steps"] == 5
        assert "steps" in data and isinstance(data["steps"], list)
        assert "summary" in data
        # Slack requirement: JSON-serialisable, has agent_id, steps, summary
        import json; json.dumps(data) # must not raise

    def test_timeline_step_fields(self, client):
        aid = str(uuid.uuid4())
        client.post("/memory/steps", json=self._make_step(aid, 1, "api_call"))
        r = client.get(f"/memory/agent/{aid}/timeline")
        step = r.json()["steps"][0]
        for f in ["step_number","action_type","action_detail","result_summary","timestamp","snapshots"]:
            assert f in step, f"Missing field: {f}"


class TestGitTracker:
    def test_snapshot_no_git_repo(self, tmp_path):
        import git_tracker
        git_hash, diff = git_tracker.snapshot_file("app.py", str(tmp_path))
        # Non-git directory: graceful, returns None for both
        assert git_hash is None and diff is None

    def test_diff_stat_no_repo(self, tmp_path):
        import git_tracker
        result = git_tracker.diff_stat(str(tmp_path))
        assert result is None

    def test_is_git_repo_false(self, tmp_path):
        import git_tracker
        assert git_tracker.is_git_repo(str(tmp_path)) is False


class TestPersistence:
    def test_data_survives_reload(self, mem_db):
        """Data survives module reload (simulating restart)."""
        db_mod, _, _ = mem_db
        aid = str(uuid.uuid4())
        db_mod.insert_step(aid, 1, "bash", "echo hi", "printed hi")
        # Simulate restart: reload module (new connections, same file)
        import importlib
        importlib.reload(db_mod)
        steps = db_mod.get_agent_steps(aid)
        assert len(steps) == 1 and steps[0]["action_detail"] == "echo hi"


class TestSlackFormat:
    def test_timeline_json_slack_structure(self, mem_db):
        """Timeline must have agent_id, total_steps, steps[], summary for Slack."""
        _, mem_mod, _ = mem_db
        aid = str(uuid.uuid4())
        for s in range(3): mem_mod.record_step(aid, s+1, "bash", f"cmd {s}", f"ok {s}")
        tl = mem_mod.build_timeline(aid)
        import json; raw = json.dumps(tl)
        parsed = json.loads(raw)
        assert parsed["agent_id"] == aid
        assert isinstance(parsed["steps"], list)
        assert len(parsed["steps"]) == 3
        assert "summary" in parsed
