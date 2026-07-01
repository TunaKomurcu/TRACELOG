import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

load_dotenv(Path(__file__).parent / ".env")

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_ALERT_CHANNEL = os.getenv("SLACK_ALERT_CHANNEL", "#tracelog-alerts")
M3_URL = os.getenv("M3_URL", "http://localhost:8002")
HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "5"))
POLL_INTERVAL = 300

client = WebClient(token=SLACK_BOT_TOKEN)
seen_ids = set()


def _parse_timestamp(value: str):
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except Exception:
        return None


def _fetch_critical_alerts() -> list:
    try:
        response = httpx.get(f"{M3_URL.rstrip('/')}/compressions", timeout=HTTP_TIMEOUT)
        response.raise_for_status()
        items = response.json()
        if not isinstance(items, list):
            return []
        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        critical = []
        for item in items:
            if str(item.get("severity", "")).lower() != "critical":
                continue
            ts = _parse_timestamp(item.get("timestamp") or item.get("created_at") or "")
            if ts and ts < cutoff:
                continue
            item_id = item.get("id") or f"{item.get('timestamp')}-{item.get('msg', '')}"
            if item_id in seen_ids:
                continue
            seen_ids.add(item_id)
            critical.append(item)
        return critical
    except Exception:
        return []


def _format_message(items: list) -> str:
    if not items:
        return "✅ Son 1 saatte kritik hata yok"
    lines = ["*Yeni kritik hatalar:*"]
    for item in items:
        ts = item.get("timestamp") or item.get("created_at") or ""
        msg = item.get("msg") or item.get("message") or item.get("detail") or "(no message)"
        lines.append(f"• {ts} - {msg}")
    return "\n".join(lines)


def _post_alert(text: str):
    try:
        client.chat_postMessage(channel=SLACK_ALERT_CHANNEL, text=text)
    except SlackApiError:
        pass


def run_polling():
    while True:
        alerts = _fetch_critical_alerts()
        if alerts:
            _post_alert(_format_message(alerts))
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run_polling()
