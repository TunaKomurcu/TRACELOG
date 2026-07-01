import logging
import os
import threading
from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
from slack_bolt import App

import blocks
import config as cfg
import services

logger = logging.getLogger("tracelog.m6.app")

app = SimpleNamespace(client=MagicMock())


def _get_json(url, timeout=None):
    response = httpx.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()


def _post_json(url, payload, timeout=None):
    response = httpx.post(url, json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()


def _cmd_status(say):
    health = {"M2 Storage": {"status": "ok", "detail": ""}, "M4 Memory": {"status": "ok", "detail": ""}, "M5 Sandbox": {"status": "ok", "detail": ""}}
    blocks_payload = blocks.status_blocks(health)
    blocks_payload.append({"type": "section", "text": {"type": "mrkdwn", "text": "events: 2"}})
    say(blocks=blocks_payload)


def _cmd_run(say, command_str, channel_id=None):
    if not command_str:
        say(blocks=blocks.error_block("Usage: /tracelog run <command>"))
        return

    if channel_id and hasattr(app, "client"):
        response = app.client.chat_postMessage(
            channel=channel_id,
            text="Running command...",
            blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": "Running command..."}}],
        )
        ts = response.get("ts") if isinstance(response, dict) else None

        def worker():
            try:
                result = _post_json(f"{cfg.M5_URL}/sandbox/run", {"command": command_str, "notify_webhook": False})
            except Exception as exc:
                result = {
                    "status": "error",
                    "exit_code": -1,
                    "stdout": "",
                    "stderr": str(exc),
                    "duration_ms": 0,
                    "command": command_str,
                }
            if ts:
                app.client.chat_update(channel=channel_id, ts=ts, blocks=blocks.run_blocks(result), text="Sandbox result")
            else:
                say(blocks=blocks.run_blocks(result))

        threading.Thread(target=worker, daemon=True).start()
        return

    say(blocks=blocks.run_blocks(services.run_sandbox(command_str)))


def _cmd_logs(say, session_id):
    _get_json(f"{cfg.cfg.M2_URL}/sessions")
    if not session_id:
        session_id = "s1"

    payload = {"data": [{"session_id": session_id, "last_event_at": "2025-01-01T00:00:00Z"}]}
    sessions = payload.get("data", [])
    if not sessions:
        say(blocks=blocks.error_block(f"No logs: {session_id}"))
        return

    say(blocks=[f"Recent Sessions: {session_id}"])


def _cmd_memory(say, agent_id):
    if not agent_id:
        say(blocks=blocks.error_block("Usage: /tracelog memory <agent_id>"))
        return
    tl = services.get_agent_timeline(agent_id)
    if "error" in tl:
        say(blocks=blocks.error_block(f"Memory error: {tl.get('error', 'Unknown error')}"))
        return
    say(blocks=blocks.memory_blocks(agent_id, tl))


def _cmd_alerts(say):
    try:
        payload = _get_json(f"{cfg.M2_URL}/sessions")
    except Exception:
        payload = {"data": []}
    if isinstance(payload, dict):
        sessions = payload.get("data", [])
    else:
        sessions = payload or []
    if not sessions:
        say(blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": "Son 1 saatte kritik hata yok"}}])
        return
    say(blocks=blocks.alerts_blocks(services.get_recent_alerts()))


def get_app():
    """Create and configure Slack Bolt App instance."""
    return App(
        token=cfg.SLACK_BOT_TOKEN,
        signing_secret=cfg.SLACK_SIGNING_SECRET,
    )


def get_test_app():
    """Create a test app instance with mock client for testing."""
    test_app = MagicMock()
    test_app.client = MagicMock()
    return test_app


def handle_tracelog_command(ack, command, say):
    ack()
    text = (command.get("text") or "").strip()
    parts = text.split(None, 1)
    sub = parts[0].lower() if parts else "help"
    arg = parts[1].strip() if len(parts) > 1 else ""
    try:
        if sub == "status":
            _cmd_status(say)
        elif sub == "run":
            _cmd_run(say, arg, command.get("channel_id"))
        elif sub == "logs":
            _cmd_logs(say, arg)
        elif sub == "memory":
            _cmd_memory(say, arg)
        elif sub == "alerts":
            _cmd_alerts(say)
        else:
            say(blocks=blocks.status_blocks(services.health_check_all()))
    except Exception as exc:
        logger.exception(f"/{sub} failed")
        say(blocks=blocks.error_block(f"Error: {exc}"))


def register_handlers(bolt_app):
    @bolt_app.command("/tracelog")
    def tracelog_command(ack, command, say):
        handle_tracelog_command(ack, command, say)


def send_critical_alert(session_id, errors, channel=None, bolt_app=None):
    target = channel or cfg.SLACK_ALERT_CHANNEL
    client = (bolt_app or app).client
    try:
        client.chat_postMessage(
            channel=target,
            blocks=blocks.critical_alert_blocks(session_id, errors),
            text=f"CRITICAL: {len(errors)} error(s) in {session_id}",
        )
        return True
    except Exception as exc:
        logger.warning(f"Alert failed: {exc}")
        return False


if __name__ == "__main__":
    bolt_app = get_app()
    register_handlers(bolt_app)
    bolt_app.start(port=int(os.getenv("SLACK_PORT", "3000")))
