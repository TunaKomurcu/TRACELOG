"""Sazabi M6 - Slack Bot (bot.py)

Kullanim: python bot.py
Komutlar: /sazabi status, /sazabi logs, /sazabi memory, /sazabi run, /sazabi alerts
"""
import logging
import os
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

load_dotenv(Path(__file__).parent / ".env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sazabi.m6.bot")

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET", "")
SLACK_ALERT_CHANNEL = os.getenv("SLACK_ALERT_CHANNEL", "#sazabi-alerts")
M2_URL = os.getenv("M2_URL", "http://localhost:8765")
M3_URL = os.getenv("M3_URL", "http://localhost:8002")
M4_URL = os.getenv("M4_URL", "http://localhost:8766")
M5_URL = os.getenv("M5_URL", "http://localhost:8767")
HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "5"))
SLACK_PORT = int(os.getenv("SLACK_PORT", "3000"))

app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)


def _check_service(name: str, url: str) -> dict:
    """Tek bir servisi kontrol et. Hata olursa digerlerini etkilemez."""
    try:
        response = httpx.get(url, timeout=HTTP_TIMEOUT)
        response.raise_for_status()
        return {"name": name, "ok": True, "detail": response.json()}
    except Exception as exc:
        logger.warning("Health check failed for %s: %s", name, exc)
        return {"name": name, "ok": False, "detail": str(exc)}


def _format_status_text(result: dict) -> str:
    if not result["ok"]:
        return "erisilemiyor"

    detail = result.get("detail")
    if result["name"] == "M2 Storage" and isinstance(detail, dict):
        if "events" in detail:
            events = detail["events"]
            if isinstance(events, list):
                return f"calisiyor ({len(events)} events)"
            if isinstance(events, int):
                return f"calisiyor ({events} events)"
        if "count" in detail and isinstance(detail["count"], int):
            return f"calisiyor ({detail['count']} events)"
        if "event_count" in detail and isinstance(detail["event_count"], int):
            return f"calisiyor ({detail['event_count']} events)"

    return "calisiyor"


def _status_blocks(results: list) -> list:
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": ":mag: Sazabi Sistem Durumu", "emoji": True},
        }
    ]

    for result in results:
        emoji = ":white_check_mark:" if result["ok"] else ":warning:"
        status_text = _format_status_text(result)
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"{emoji} *{result['name']}*: {status_text}"},
            }
        )

    return blocks


def _get_json(url: str) -> dict:
    try:
        response = httpx.get(url, timeout=HTTP_TIMEOUT)
        response.raise_for_status()
        return {"ok": True, "data": response.json()}
    except Exception as exc:
        logger.warning("Request failed for %s: %s", url, exc)
        return {"ok": False, "error": str(exc)}


def _parse_timestamp(value: str):
    if not value:
        return None
    try:
        if isinstance(value, str) and value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except Exception:
        return None


def _alerts_blocks(alerts: list) -> list:
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":warning: Son 1 saatte kritik hatalar",
                "emoji": True,
            },
        }
    ]
    if not alerts:
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "✅ Son 1 saatte kritik hata yok"},
            }
        )
        return blocks

    for item in alerts[:10]:
        ts = item.get("timestamp") or item.get("created_at") or ""
        msg = item.get("msg") or item.get("message") or item.get("detail") or "(no message)"
        source = item.get("source") or item.get("id") or ""
        text = f"*{ts}* {source}: {msg}" if source else f"*{ts}* {msg}"
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": text},
            }
        )
    return blocks


def _post_json(url: str, payload: dict) -> dict:
    try:
        response = httpx.post(url, json=payload, timeout=HTTP_TIMEOUT)
        response.raise_for_status()
        return {"ok": True, "data": response.json()}
    except Exception as exc:
        logger.warning("POST failed for %s: %s", url, exc)
        return {"ok": False, "error": str(exc)}


def _run_blocks(result: dict) -> list:
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":runner: /sazabi run sonucu",
                "emoji": True,
            },
        }
    ]
    if not result.get("ok"):
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"❌ Zaman aşımı veya hata: {result.get('error', 'Bilinmeyen hata')}"},
            }
        )
        return blocks

    data = result.get("data") or {}
    exit_code = data.get("exit_code")
    stdout = data.get("stdout", "")
    stderr = data.get("stderr", "")
    if exit_code == 0:
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "✅ `exit_code=0`"},
            }
        )
        if stdout:
            blocks.append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"```\n{stdout}\n```"},
                }
            )
    else:
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"❌ `exit_code={exit_code}`"},
            }
        )
        if stderr:
            blocks.append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"```\n{stderr}\n```"},
                }
            )
    return blocks


def _background_run(command_text: str, channel: str, ts: str):
    result = _post_json(
        f"{M5_URL.rstrip('/')}/sandbox/run",
        {"command": command_text, "notify_webhook": False},
    )
    if not result.get("ok") and "timeout" in result.get("error", "").lower():
        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "❌ Zaman aşımı"},
            }
        ]
    else:
        blocks = _run_blocks(result)
    try:
        app.client.chat_update(channel=channel, ts=ts, text="/sazabi run sonucu", blocks=blocks)
    except Exception as exc:
        logger.warning("Failed to update run result message: %s", exc)


def _logs_blocks(events: list, session_id: str) -> list:
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f":page_with_curl: Logs for {session_id}",
                "emoji": True,
            },
        }
    ]
    if not events:
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "No log events found."},
            }
        )
        return blocks

    for item in events[-20:]:
        content = item.get("content") or item.get("message") or "(empty)"
        ts = item.get("timestamp") or item.get("created_at") or ""
        line = f"*{ts}* {content}" if ts else content
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": line},
            }
        )
    return blocks


def _sessions_blocks(sessions: list) -> list:
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":date: Recent Sessions",
                "emoji": True,
            },
        }
    ]
    if not sessions:
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "No sessions found."},
            }
        )
        return blocks

    for session in sessions[:5]:
        sid = session.get("session_id") or session.get("id") or "unknown"
        last = session.get("last_event_at") or session.get("updated_at") or ""
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{sid}* {last}",
                },
            }
        )
    return blocks


def _memory_blocks(timeline: list, agent_id: str) -> list:
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f":brain: Memory Timeline {agent_id}",
                "emoji": True,
            },
        }
    ]
    if not timeline:
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "No timeline events found."},
            }
        )
        return blocks

    for item in timeline[-10:]:
        action = item.get("action_type", "step")
        detail = item.get("action_detail", "")
        result = item.get("result_summary", "")
        step_num = item.get("step_number", "?")
        failed = any(word in str(result).lower() for word in ["basarisiz", "hata", "fail", "failed", "error"])
        marker = "❌" if failed else "✅"
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{marker} *Step {step_num}* {action}: {detail} {result}",
                },
            }
        )
    return blocks


@app.command("/sazabi")
def handle_sazabi_command(ack, command, say):
    ack()
    text = (command.get("text") or "").strip()
    if not text:
        say(text="Kullanim: `/sazabi status`, `/sazabi logs [session_id]`, `/sazabi memory [agent_id]`, `/sazabi run [komut]`, `/sazabi alerts`")
        return

    parts = text.split(None, 1)
    sub = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    if sub == "status":
        results = [
            _check_service("M2 Storage", f"{M2_URL.rstrip('/')}/health"),
            _check_service("M4 Memory", f"{M4_URL.rstrip('/')}/health"),
            _check_service("M5 Sandbox", f"{M5_URL.rstrip('/')}/health"),
        ]
        say(blocks=_status_blocks(results))
        return

    if sub == "logs":
        if arg:
            resp = _get_json(f"{M2_URL.rstrip('/')}/events?session_id={arg}")
            if not resp["ok"]:
                say(text=f"M2 log endpoint error: {resp['error']}")
                return
            events = resp["data"] if isinstance(resp["data"], list) else []
            say(blocks=_logs_blocks(events, arg))
            return

        resp = _get_json(f"{M2_URL.rstrip('/')}/sessions")
        if not resp["ok"]:
            say(text=f"M2 sessions endpoint error: {resp['error']}")
            return
        sessions = resp["data"] if isinstance(resp["data"], list) else []
        say(blocks=_sessions_blocks(sessions))
        return

    if sub == "memory":
        if not arg:
            say(text="Kullanim: `/sazabi memory [agent_id]`")
            return
        resp = _get_json(f"{M4_URL.rstrip('/')}/memory/agent/{arg}/timeline")
        if not resp["ok"]:
            say(text=f"M4 memory endpoint error: {resp['error']}")
            return
        data = resp["data"] if isinstance(resp["data"], dict) else {}
        timeline = data.get("steps", [])
        say(blocks=_memory_blocks(timeline, arg))
        return

    if sub == "alerts":
        resp = _get_json(f"{M3_URL.rstrip('/')}/compressions")
        if not resp["ok"]:
            say(text=f"M3 alerts endpoint error: {resp['error']}")
            return
        items = resp["data"] if isinstance(resp["data"], list) else []
        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        critical = []
        for item in items:
            if str(item.get("severity", "")).lower() != "critical":
                continue
            ts = _parse_timestamp(item.get("timestamp") or item.get("created_at") or "")
            if ts and ts < cutoff:
                continue
            critical.append(item)
        say(blocks=_alerts_blocks(critical))
        return

    if sub == "run":
        if not arg:
            say(text="Kullanim: `/sazabi run [komut]`")
            return
        channel = command.get("channel_id")
        message = app.client.chat_postMessage(
            channel=channel,
            text="⏳ Çalışıyor...",
            blocks=[
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "⏳ Çalışıyor..."},
                }
            ],
        )
        ts = message.get("ts")
        thread = threading.Thread(target=_background_run, args=(arg, channel, ts), daemon=True)
        thread.start()
        return

    say(text="Kullanim: `/sazabi status`, `/sazabi logs [session_id]`, `/sazabi memory [agent_id]`, `/sazabi run [komut]`, `/sazabi alerts`")


if __name__ == "__main__":
    if not SLACK_BOT_TOKEN or not os.getenv("SLACK_APP_TOKEN"):
        logger.error("SLACK_BOT_TOKEN or SLACK_APP_TOKEN missing")
    handler = SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN"))
    handler.start()

