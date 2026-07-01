"""Sazabi M1+M2 - HTTP forwarder to storage service"""
import os, json, threading, sys
from urllib import request, error


STORAGE_URL = os.getenv("TRACELOG_STORAGE_URL", "")


def _post(url: str, payload: dict) -> None:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with request.urlopen(req, timeout=2):
            pass
    except Exception as exc:
        print(f"Forwarder error: {exc}", file=sys.stderr)


def forward_event(session_id: str, timestamp: str, stream: str,
            content: str, source: str = "agent") -> None:
    """Fire-and-forget HTTP POST to storage service."""
    if not STORAGE_URL:
        return
    url = STORAGE_URL.rstrip("/") + "/events"
    payload = {
        "session_id": session_id,
        "timestamp": timestamp,
        "stream": stream,
        "content": content,
        "source": source,
    }
    t = threading.Thread(target=_post, args=(url, payload), daemon=True)
    t.start()
