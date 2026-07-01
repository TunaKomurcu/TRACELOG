import os
import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import blocks
import services
import config as cfg

logger = logging.getLogger("tracelog.m6.app")


def _cmd_status(say):
    say(blocks=blocks.status_blocks(services.health_check_all()))


def _cmd_run(say, command_str):
    if not command_str:
        say(blocks=blocks.error_block("Usage: /tracelog run <command>"))
        return
    say(blocks=blocks.run_blocks(services.run_sandbox(command_str)))


def _cmd_logs(say, session_id):
    if not session_id:
        say(blocks=blocks.error_block("Usage: /tracelog logs <session_id>"))
        return
    evts = services.get_session_logs(session_id)
    if not evts:
        say(blocks=blocks.error_block(f"No logs: {session_id}"))
        return
    lines = [e.get("content","") for e in evts]
    say(blocks=blocks.logs_blocks(session_id, services.compress_logs_local(lines)))


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
    say(blocks=blocks.alerts_blocks(services.get_recent_alerts()))


def get_app():
    """Create and configure Slack Bolt App instance."""
    return App(
        token=cfg.SLACK_BOT_TOKEN,
        signing_secret=cfg.SLACK_SIGNING_SECRET,
    )


def get_test_app():
    """Create a test app instance with mock client for testing."""
    from unittest.mock import MagicMock
    app = MagicMock()
    app.client = MagicMock()
    return app


def register_handlers(bolt_app):
    @bolt_app.command("/tracelog")
    def tracelog_command(ack, command, say):
            ack()
            text = (command.get("text") or "").strip()
            parts = text.split(None, 1)
            sub = parts[0].lower() if parts else "help"
            arg = parts[1].strip() if len(parts)>1 else ""
            try:
                if sub=="status": _cmd_status(say)
                elif sub=="run": _cmd_run(say, arg)
                elif sub=="logs": _cmd_logs(say, arg)
                elif sub=="memory": _cmd_memory(say, arg)
                elif sub=="alerts": _cmd_alerts(say)
                else: say(blocks=blocks.status_blocks(services.health_check_all()))
            except Exception as e:
                logger.exception(f"/{sub} failed")
                say(blocks=blocks.error_block(f"Error: {e}"))


def send_critical_alert(session_id, errors, channel=None, bolt_app=None):
    target = channel or cfg.SLACK_ALERT_CHANNEL
    client = (bolt_app or get_app()).client
    try:
            client.chat_postMessage(channel=target,
                blocks=blocks.critical_alert_blocks(session_id, errors),
                text=f"CRITICAL: {len(errors)} error(s) in {session_id}")
            return True
    except Exception as e:
            logger.warning(f"Alert failed: {e}")
            return False


if __name__ == "__main__":
    bolt_app = get_app()
    register_handlers(bolt_app)
    bolt_app.start(port=int(os.getenv("SLACK_PORT","3000")))
