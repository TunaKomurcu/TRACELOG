"""Sazabi M3 - Google Gemini API compressor with rate limiting, retry, cost tracking."""
import os, json, time, threading, logging, re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("sazabi.m3.compressor")

MODEL = "gemini-2.0-flash-lite"
MAX_CALLS_PER_MINUTE = 10
MAX_RETRIES = 3
BASE_BACKOFF = 1.0
# Gemini 2.0 Flash Lite pricing (per million tokens)
COST_PER_1M_INPUT = 0.075 # USD
COST_PER_1M_OUTPUT = 0.30 # USD

SYSTEM_PROMPT = (
    "Sen bir DevOps asistanisin. Sana verilen log satirlarini analiz et. SADECE JSON dondurmeli."
)


@dataclass
class UsageRecord:
    session_id: str
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = MODEL
    cost_usd: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def calculate_cost(self) -> float:
        self.cost_usd = (
            self.input_tokens / 1_000_000 * COST_PER_1M_INPUT +
            self.output_tokens / 1_000_000 * COST_PER_1M_OUTPUT
        )
        return self.cost_usd


class RateLimiter:
    """Token bucket: max N calls per 60s window."""
    def __init__(self, max_calls: int = MAX_CALLS_PER_MINUTE):
        self.max_calls = max_calls
        self._calls: List[float] = []
        self._lock = threading.Lock()

    def acquire(self) -> None:
        with self._lock:
            now = time.monotonic()
            self._calls = [t for t in self._calls if now - t < 60]
            if len(self._calls) >= self.max_calls:
                sleep_for = 60 - (now - self._calls[0]) + 0.05
                logger.info(f"Rate limit reached, sleeping {sleep_for:.1f}s")
                time.sleep(max(0, sleep_for))
                now = time.monotonic()
                self._calls = [t for t in self._calls if now - t < 60]
            self._calls.append(now)


_rate_limiter = RateLimiter()


def _call_gemini(api_key: str, log_text: str) -> tuple[Dict[str, Any], UsageRecord]:
    """Call Gemini API with rate limiting + exponential backoff retry."""
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    client = genai.GenerativeModel(
        model_name=MODEL,
        system_instruction=SYSTEM_PROMPT,
        generation_config={"response_mime_type": "application/json"},
    )
    usage = UsageRecord(session_id="")
    last_err: Optional[Exception] = None

    for attempt in range(MAX_RETRIES):
        try:
            _rate_limiter.acquire()
            resp = client.generate_content(log_text)
            # Token counts (Gemini returns usage_metadata)
            meta = getattr(resp, "usage_metadata", None)
            if meta:
                usage.input_tokens = getattr(meta, "prompt_token_count", 0) or 0
                usage.output_tokens = getattr(meta, "candidates_token_count", 0) or 0
            usage.calculate_cost()
            raw = resp.text.strip()
            # Strip markdown fences if present
            if raw.startswith("```"):
                raw = re.sub(r"^```[a-z]*\n?", "", raw)
                raw = re.sub(r"\n?```$", "", raw)
            return json.loads(raw), usage
        except Exception as e:
            last_err = e
            wait = BASE_BACKOFF * (2 ** attempt)
            logger.warning(f"Gemini attempt {attempt+1} failed: {e}. Retry in {wait}s")
            time.sleep(wait)

    raise RuntimeError(f"Gemini API failed after {MAX_RETRIES} attempts: {last_err}") from last_err


def compress(log_lines: List[str], session_id: str = "") -> tuple[Dict[str, Any], Optional[UsageRecord]]:
    """Main entry: call Gemini if API key available, else return empty dict."""
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        return {}, None
    log_text = chr(10).join(log_lines)
    result, usage = _call_gemini(api_key, log_text)
    usage.session_id = session_id
    logger.info(f"Gemini used {usage.input_tokens}in/{usage.output_tokens}out tokens, ${usage.cost_usd:.6f}")
    return result, usage
