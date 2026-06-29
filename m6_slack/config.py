"""Sazabi M6 - Configuration."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env", override=False)


class _Cfg:
    SLACK_BOT_TOKEN: str = os.getenv("SLACK_BOT_TOKEN", "")
    SLACK_SIGNING_SECRET: str = os.getenv("SLACK_SIGNING_SECRET", "")
    SLACK_ALERT_CHANNEL: str = os.getenv("SLACK_ALERT_CHANNEL", "#sazabi-alerts")
    # Backend service URLs
    M2_URL: str = os.getenv("M2_URL", "http://localhost:8765")
    M4_URL: str = os.getenv("M4_URL", "http://localhost:8766")
    M5_URL: str = os.getenv("M5_URL", "http://localhost:8767")
    # Timeouts
    HTTP_TIMEOUT: int = int(os.getenv("HTTP_TIMEOUT", "5"))
    SLACK_RESPONSE_TIMEOUT: float = 2.8 # Slack enforces 3s


cfg = _Cfg()
