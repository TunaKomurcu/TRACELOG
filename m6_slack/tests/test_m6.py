"""Sazabi M6 - Test Suite"""
import sys, os, pathlib, pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

M6_DIR = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(M6_DIR))
import blocks, services, app as app_module, bot as bot_module, webhook_handler as webhook_module


class TestBlocks:
    def test_status_ok(self):
        h={"M2":{"status":"ok"},"M5":{"status":"down"}}
        assert any("ok" in str(b) for b in blocks.status_blocks(h))
        assert any("down" in str(b) for b in blocks.status_blocks(h))
    def test_run_ok(self):
        r={"sandbox_id":"x","command":"py","exit_code":0,"stdout":"2","stderr":"","duration_ms":5,"status":"completed"}
        assert any("2" in str(b) for b in blocks.run_blocks(r))
    def test_run_rejected(self):
        r={"sandbox_id":"x","command":"rm","exit_code":-1,"stdout":"","stderr":"[S]","duration_ms":0,"status":"rejected"}
        assert any("rejected" in str(b).lower() for b in blocks.run_blocks(r))
    def test_error_block(self):
        assert any("oops" in str(b) for b in blocks.error_block("oops"))
    def test_alerts_empty(self):
        assert any("No critical" in str(b) for b in blocks.alerts_blocks([]))
    def test_alerts_critical(self):
        a=[{"session_id":"s1","severity":"critical","msg":"DB down"}]
        assert any("critical" in str(b).lower() or "DB down" in str(b) for b in blocks.alerts_blocks(a))
    def test_memory_blocks(self):
        tl={"agent_id":"a1","total_steps":1,"summary":"ok","steps":[{"step_number":1,"action_type":"bash","result_summary":"ok","snapshots":[]}]}
        assert any("bash" in str(b) for b in blocks.memory_blocks("a1",tl))


class TestSlashCommands:
    def test_status_command(self):
        say=MagicMock()
        with patch("services.health_check_all",return_value={"M2":{"status":"ok"}}):
            app_module._cmd_status(say)
            say.assert_called_once()
            assert "blocks" in say.call_args[1]
    def test_run_success(self):
        say=MagicMock()
        mr={"sandbox_id":"x","command":"p","exit_code":0,"stdout":"2","stderr":"","duration_ms":5,"status":"completed"}
        with patch("services.run_sandbox",return_value=mr):
            app_module._cmd_run(say,"python -c pass")
            assert say.called
            assert any("2" in str(b) for b in say.call_args[1]["blocks"])
    def test_run_no_arg(self):
        say=MagicMock()
        app_module._cmd_run(say,"")
        assert any("Usage" in str(b) or "Error" in str(b) for b in say.call_args[1]["blocks"])
    def test_memory_command(self):
        say=MagicMock()
        mt={"agent_id":"a1","total_steps":1,"summary":"ok","steps":[{"step_number":1,"action_type":"bash","result_summary":"ok","snapshots":[]}]}
        with patch("services.get_agent_timeline",return_value=mt):
            app_module._cmd_memory(say,"a1")
            assert say.called
    def test_alerts_command(self):
        say=MagicMock()
        with patch("services.get_recent_alerts",return_value=[]):
            app_module._cmd_alerts(say)
            assert say.called


class TestCriticalAlert:
    def test_send_alert_mocked(self):
        bolt_app=app_module.get_test_app()
        errs=[{"msg":"DB down","severity":"critical"}]
        with patch.object(bolt_app.client,"chat_postMessage",return_value={"ok":True}) as mp:
            r=app_module.send_critical_alert("s1",errs,channel="#t",bolt_app=bolt_app)
            assert r is True
            mp.assert_called_once()
            assert mp.call_args[1]["channel"]=="#t"


class TestServicesUnit:
    def test_health_dict(self):
        with patch("services._get",return_value={"status":"ok"}):
            assert len(services.health_check_all())>=2
    def test_run_sandbox(self):
        with patch("services._post",return_value={"status":"completed","exit_code":0}) as mp:
            r=services.run_sandbox("python -c pass")
            assert r["status"]=="completed"
            assert "/sandbox/run" in mp.call_args[0][0]


class TestResponseTime:
    def test_status_under_3s(self):
        import time; say = MagicMock()
        with patch("services.health_check_all", return_value={"M2": {"status": "ok"}}):
            t0 = time.perf_counter(); app_module._cmd_status(say); dur = time.perf_counter() - t0
            assert dur < 3.0
    def test_run_under_3s(self):
        import time; say = MagicMock()
        mr = {"sandbox_id": "x", "command": "x", "exit_code": 0, "stdout": "2", "stderr": "", "duration_ms": 5, "status": "completed"}
        with patch("services.run_sandbox", return_value=mr):
            t0 = time.perf_counter(); app_module._cmd_run(say, "python -c pass"); dur = time.perf_counter() - t0
            assert dur < 3.0


class TestBotCommands:
    def test_status_command(self):
        ack = MagicMock()
        say = MagicMock()

        class FakeResponse:
            def __init__(self, data):
                self._data = data
            def raise_for_status(self):
                pass
            def json(self):
                return self._data

        side_effects = [
            FakeResponse({"status": "ok", "events": [1, 2]}),
            FakeResponse({"status": "ok"}),
            FakeResponse({"status": "ok"}),
        ]
        with patch.object(bot_module.httpx, "get", side_effect=side_effects):
            bot_module.handle_sazabi_command(ack, {"text": "status", "channel_id": "C123"}, say)

        ack.assert_called_once()
        say.assert_called_once()
        blocks = say.call_args[1]["blocks"]
        assert any("M2 Storage" in str(block) for block in blocks)
        assert any("M4 Memory" in str(block) for block in blocks)
        assert any("M5 Sandbox" in str(block) for block in blocks)
        assert any("events" in str(block) for block in blocks)

    def test_run_command_async(self):
        ack = MagicMock()
        say = MagicMock()
        command = {"text": "run echo hello", "channel_id": "C123"}

        def fake_thread_init(self, target, args=(), daemon=False):
            self._target = target
            self._args = args
            self._daemon = daemon
        def fake_thread_start(self):
            self._target(*self._args)

        def fake_thread_constructor(target, args=(), daemon=False):
            class FakeThread:
                def __init__(self, target, args=(), daemon=False):
                    self._target = target
                    self._args = args
                    self.daemon = daemon
                def start(self):
                    self._target(*self._args)
            return FakeThread(target, args, daemon)

        with patch.object(bot_module.app.client, "chat_postMessage", return_value={"ts": "123"}) as post_mock, \
             patch.object(bot_module.app.client, "chat_update", return_value=None) as update_mock, \
             patch.object(bot_module, "_post_json", return_value={"ok": True, "data": {"exit_code": 0, "stdout": "hello", "stderr": ""}}), \
             patch.object(bot_module, "threading", new=type("T", (), {"Thread": fake_thread_constructor})):
            bot_module.handle_sazabi_command(ack, command, say)

        post_mock.assert_called_once()
        update_mock.assert_called_once()
        assert not say.called

    def test_logs_no_session(self):
        ack = MagicMock()
        say = MagicMock()
        with patch.object(bot_module, "_get_json", return_value={"ok": True, "data": [{"session_id": "s1", "last_event_at": "2025-01-01T00:00:00Z"}]}) as get_json:
            bot_module.handle_sazabi_command(ack, {"text": "logs", "channel_id": "C123"}, say)

        get_json.assert_called_once()
        say.assert_called_once()
        blocks = say.call_args[1]["blocks"]
        assert any("Recent Sessions" in str(block) for block in blocks)
        assert any("s1" in str(block) for block in blocks)

    def test_alerts_empty(self):
        ack = MagicMock()
        say = MagicMock()
        with patch.object(bot_module, "_get_json", return_value={"ok": True, "data": []}):
            bot_module.handle_sazabi_command(ack, {"text": "alerts", "channel_id": "C123"}, say)

        say.assert_called_once()
        blocks = say.call_args[1]["blocks"]
        assert any("Son 1 saatte kritik hata yok" in str(block) for block in blocks)


class TestWebhookHandler:
    def test_webhook_handler(self):
        client = TestClient(webhook_module.app)
        payload = {
            "session_id": "s1",
            "command": "echo hi",
            "exit_code": 0,
            "stdout": "hi",
            "stderr": "",
            "finished_at": "2025-01-01T00:00:00Z"
        }
        with patch.object(webhook_module.client, "chat_postMessage", return_value={"ok": True}) as chat_post:
            response = client.post("/webhook/sandbox-result", json=payload)

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        chat_post.assert_called_once()


