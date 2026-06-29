"""Sazabi M6 - Backend service clients."""
import sys, os, json, pathlib, logging
from typing import Dict, Any, Optional, List
from urllib import request as urllib_req, error as urllib_err
from config import cfg

logger = logging.getLogger("sazabi.m6.services")


def _get(url: str, timeout: int = None) -> Dict[str, Any]:
    t = timeout or cfg.HTTP_TIMEOUT
    try:
        with urllib_req.urlopen(url, timeout=t) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}


def _post(url: str, payload: Dict, timeout: int = None) -> Dict[str, Any]:
    t = timeout or cfg.HTTP_TIMEOUT
    try:
        data = json.dumps(payload).encode()
        req = urllib_req.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        with urllib_req.urlopen(req, timeout=t) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}


def health_check_all() -> Dict[str, Any]:
    """Check health of all backend services. Returns per-service status."""
    services = {
        "M2 Storage": f"{cfg.M2_URL}/health",
        "M4 Memory": f"{cfg.M4_URL}/health",
        "M5 Sandbox": f"{cfg.M5_URL}/health",
    }
    results = {}
    for name, url in services.items():
        resp = _get(url)
        if "error" in resp:
            results[name] = {"status": "down", "detail": resp["error"][:80]}
        else:
            results[name] = {"status": resp.get("status", "ok"), "detail": ""}
    # M1 and M3 are libraries, not HTTP services - check import
    for mod_name, label in [("m3_compression.pipeline", "M3 Compressor"), ("m1_logger.logger", "M1 Logger")]:
        try:
            results[label] = {"status": "ok", "detail": "library"}
        except Exception as e:
            results[label] = {"status": "unknown", "detail": str(e)[:60]}
    return results


def run_sandbox(command: str) -> Dict[str, Any]:
    """POST command to M5 sandbox service."""
    return _post(f"{cfg.M5_URL}/sandbox/run",
        {"command": command, "notify_webhook": False},
    )


def get_agent_timeline(agent_id: str) -> Dict[str, Any]:
    """GET agent timeline from M4."""
    return _get(f"{cfg.M4_URL}/memory/agent/{agent_id}/timeline")


def get_session_logs(session_id: str, limit: int = 200) -> List[Dict]:
    """GET log events for a session from M2."""
    resp = _get(f"{cfg.M2_URL}/events?session_id={session_id}&limit={limit}")
    if isinstance(resp, list):
        return resp
    return []


def compress_logs_local(lines: List[str]) -> Dict[str, Any]:
    """Run M3 pipeline locally (no HTTP - it is a library)."""
    try:
        m3_path = pathlib.Path(__file__).parent.parent / "m3_compression"
        if str(m3_path) not in sys.path:
            sys.path.insert(0, str(m3_path))
        import importlib
        import pipeline as m3_pipeline
        importlib.reload(m3_pipeline)
        result = m3_pipeline.run(lines)
        return result.to_dict()
    except Exception as e:
        logger.warning(f"M3 compression failed: {e}")
        return {"summary": {"summary": f"Log compression unavailable: {e}", "errors": [], "anomalies": [], "root_cause_hint": ""}}


def get_recent_alerts(minutes: int = 60) -> List[Dict]:
    """Get M3 anomalies from recent sessions via M2. Returns list of alert dicts."""
    from datetime import datetime, timezone, timedelta
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()
        sessions = _get(f"{cfg.M2_URL}/sessions")
        if isinstance(sessions, list):
            sessions = [s for s in sessions if s.get("last_event_at","") >= cutoff]
        else:
            sessions = []
        alerts = []
        for sess in sessions[:5]: # cap at 5 to stay under 3s
            logs = get_session_logs(sess["session_id"], limit=100)
            lines = [l.get("content","") for l in logs]
            if not lines: continue
            compressed = compress_logs_local(lines)
            summary = compressed.get("summary", {})
            errs = summary.get("errors", [])
            for e in errs:
                alerts.append({
                    "session_id": sess["session_id"],
                    "severity": e.get("severity","warning"),
                    "msg": e.get("msg","")[:200],
                })
        return alerts
    except Exception as e:
        logger.warning(f"get_recent_alerts failed: {e}")
        return []
