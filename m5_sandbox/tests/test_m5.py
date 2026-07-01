"""Tracelog M5 - Secure Sandbox Test Suite"""
import sys, os, pathlib, uuid, json, pytest
from unittest.mock import patch, MagicMock
M5_DIR = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(M5_DIR))
from fastapi.testclient import TestClient
import security, runner, webhook, api as api_mod


@pytest.fixture
def client():
    with TestClient(api_mod.app) as c:
        yield c


class TestWhitelist:
    def test_allowed_python(self):
        security.validate_command(["python", "-c", "pass"])
    def test_reject_rm(self):
        with pytest.raises(security.SecurityError):
            security.validate_command(["rm", "-rf", "/"])
    def test_reject_curl(self):
        with pytest.raises(security.SecurityError):
            security.validate_command(["curl", "http://evil.com"])
    def test_reject_bash(self):
        with pytest.raises(security.SecurityError):
            security.validate_command(["bash", "-c", "echo"])
    def test_reject_empty(self):
        with pytest.raises(security.SecurityError):
            security.validate_command([])
    def test_reject_os_system(self):
        with pytest.raises(security.SecurityError, match="Dangerous"):
            security.validate_command(["python", "-c", "import os; os.system('ls')"])


class TestRunnerBasic:
    def test_simple_run(self):
        result = runner.run_sandboxed("python -c 'print(1+1)'")
        assert result["exit_code"] == 0
        assert "2" in result["stdout"]
    def test_exit_code_propagated(self):
        result = runner.run_sandboxed("python -c 'import sys; sys.exit(42)'")
        assert result["exit_code"] == 42
    def test_stderr_captured(self):
        result = runner.run_sandboxed("python -c 'import sys; sys.stderr.write(chr(101)+chr(114)+chr(114))'")
        assert "err" in result["stderr"]
    def test_result_fields(self):
        result = runner.run_sandboxed("python -c pass")
        for f in ["sandbox_id","command","exit_code","stdout","stderr","duration_ms","resource_usage","status"]:
            assert f in result, f"Missing: {f}"
    def test_sandbox_id_custom(self):
        sid = str(uuid.uuid4())
        result = runner.run_sandboxed("python -c pass", sandbox_id=sid)
        assert result["sandbox_id"] == sid


class TestSecurityEnforcement:
    def test_rm_rf_rejected(self):
        result = runner.run_sandboxed("rm -rf /")
        assert result["status"] == "rejected"
        assert result["exit_code"] == -1
        assert "[SECURITY]" in result["stderr"]
    def test_curl_rejected(self):
        result = runner.run_sandboxed("curl http://evil.com")
        assert result["status"] == "rejected"
    def test_os_system_rejected(self):
        result = runner.run_sandboxed("python -c import os; os.system('ls')")
        assert result["status"] == "rejected"
    def test_rejected_no_stdout(self):
        result = runner.run_sandboxed("bash -c echo pwned")
        assert result["status"] == "rejected"
        assert result["stdout"] == ""


class TestTimeout:
    def test_timeout_kill(self):
        import importlib
        with patch.dict(os.environ, {"SANDBOX_TIMEOUT": "2"}):
            importlib.reload(runner)
            result = runner.run_sandboxed("python -c 'while True: pass'")
            assert result["status"] == "timeout"
            assert result["exit_code"] == -9
            assert result["duration_ms"] < 10000
            importlib.reload(runner)
    def test_completes_before_timeout(self):
        result = runner.run_sandboxed("python -c pass")
        assert result["status"] == "completed"


class TestFilesystemIsolation:
    def test_write_path_inside_ok(self, tmp_path):
        box = str(tmp_path / "sandbox_x")
        pathlib.Path(box).mkdir()
        security.validate_write_path(str(tmp_path / "sandbox_x" / "out.txt"), box)
    def test_write_path_outside_raises(self, tmp_path):
        box = str(tmp_path / "sandbox_x")
        pathlib.Path(box).mkdir()
        with pytest.raises(security.SecurityError, match="outside sandbox"):
            security.validate_write_path("/etc/passwd", box)
    def test_run_uses_isolated_dir(self):
        result = runner.run_sandboxed("python -c pass")
        assert "sandbox_dir" in result
        assert "sandbox_" in result["sandbox_dir"]


class TestAPIEndpoints:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200 and r.json()["status"] == "ok"
    def test_run_ok(self, client):
        r = client.post("/sandbox/run", json={"command": "python -c pass", "notify_webhook": False})
        assert r.status_code == 200 and r.json()["status"] == "completed"
    def test_run_rejected(self, client):
        r = client.post("/sandbox/run", json={"command": "rm -rf /", "notify_webhook": False})
        assert r.json()["status"] == "rejected"
    def test_get_by_id(self, client):
        sid = str(uuid.uuid4())
        client.post("/sandbox/run", json={"command": "python -c pass", "sandbox_id": sid, "notify_webhook": False})
        r = client.get(f"/sandbox/{sid}")
        assert r.status_code == 200 and r.json()["sandbox_id"] == sid
    def test_unknown_id_404(self, client):
        assert client.get("/sandbox/no-such-id-000").status_code == 404


class TestWebhook:
    def test_no_url_skips(self):
        with patch.dict(os.environ, {"M6_WEBHOOK_URL": ""}, clear=False):
            assert webhook.send_result({"sandbox_id": "x"}) is False
    def test_url_set_fires(self):
        with patch.dict(os.environ, {"M6_WEBHOOK_URL": "http://localhost:9999/"}):
            with patch("webhook._post_json") as mp:
                webhook.send_result({"sandbox_id": "x"})
                import time; time.sleep(0.1)
                mp.assert_called_once()
    def test_webhook_endpoint(self, client):
        r = client.post("/webhook/sandbox-result", json={"sandbox_id": "wt", "status": "ok"})
        assert r.status_code == 200 and r.json()["received"] is True


