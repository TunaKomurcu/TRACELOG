import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

load_dotenv(Path(__file__).parent / ".env")

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_ALERT_CHANNEL = os.getenv("SLACK_ALERT_CHANNEL", "#tracelog-alerts")
SLACK_PORT = int(os.getenv("SLACK_PORT", "3000"))

app = FastAPI()
client = WebClient(token=SLACK_BOT_TOKEN)


class SandboxResult(BaseModel):
    session_id: str
    command: str
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    finished_at: str | None = None


@app.post("/webhook/sandbox-result")
async def sandbox_result(payload: SandboxResult):
    status = "✅ Başarılı" if payload.exit_code == 0 else "❌ Başarısız"
    text = (
        f"*Sandbox sonucu*\n"
        f"*session_id:* {payload.session_id}\n"
        f"*command:* `{payload.command}`\n"
        f"*status:* {status}\n"
    )
    if payload.exit_code == 0 and payload.stdout:
        text += f"*stdout:*```\n{payload.stdout}\n```\n"
    if payload.exit_code != 0 and payload.stderr:
        text += f"*stderr:*```\n{payload.stderr}\n```\n"
    try:
        client.chat_postMessage(channel=SLACK_ALERT_CHANNEL, text=text)
    except SlackApiError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"status": "ok"}
