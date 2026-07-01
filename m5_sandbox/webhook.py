"""Tracelog M5 - Webhook forwarder to M6 Slack Bot."""
import os, json, logging, threading
from typing import Dict, Any, Optional
from urllib import request as urllib_req

logger = logging.getLogger("tracelog.m5.webhook")

# M6_WEBHOOK_URL read per-call (supports env patching in tests)


def _post_json(url: str, payload: Dict[str, Any]) -> None:
    data = json.dumps(payload).encode("utf-8")
    req = urllib_req.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib_req.urlopen(req, timeout=5):
            pass
        logger.info(f"Webhook delivered to {url}")
    except Exception as e:
        logger.warning(f"Webhook delivery failed: {e}")


def send_result(result: Dict[str, Any], url: Optional[str] = None) -> bool:
    """
    Fire-and-forget POST of sandbox result to M6 webhook.
    Returns True if URL is configured, False if skipped.
    """
    target = url or os.getenv("M6_WEBHOOK_URL", "")
    if not target:
        logger.debug("No M6_WEBHOOK_URL set, skipping webhook delivery")
        return False
    t = threading.Thread(target=_post_json, args=(target, result), daemon=True)
    t.start()
    return True
