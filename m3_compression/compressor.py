"""Sazabi M3 - Ollama compressor with retry, cost tracking for local LLM."""
import os, json, time, threading, logging, re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import httpx

logger = logging.getLogger("sazabi.m3.compressor")

MODEL = "qwen2.5:14b"
MAX_RETRIES = 3
BASE_BACKOFF = 1.0
TIMEOUT_SECONDS = 180  # Large model, local CPU/GPU can be slow
# Ollama is local, no per-token cost tracking (but keep structure for compatibility)
COST_PER_1M_INPUT = 0.0
COST_PER_1M_OUTPUT = 0.0

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


def _ollama_available() -> bool:
    """Check if Ollama is reachable at /api/tags endpoint."""
    try:
        url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        with httpx.Client(timeout=3.0) as client:
            r = client.get(f"{url}/api/tags")
            return r.status_code == 200
    except Exception:
        return False


def _call_ollama(ollama_url: str, model: str, log_text: str) -> tuple[Dict[str, Any], UsageRecord]:
    """Call Ollama /v1/chat/completions endpoint (OpenAI-compatible) with retry."""
    usage = UsageRecord(session_id="")
    last_err: Optional[Exception] = None

    for attempt in range(MAX_RETRIES):
        try:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": log_text},
                ],
                "temperature": 0.3,
                "response_format": {"type": "json_object"},
            }
            
            with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
                resp = client.post(f"{ollama_url}/v1/chat/completions", json=payload)
                resp.raise_for_status()
                
            data = resp.json()
            raw = data["choices"][0]["message"]["content"].strip()
            
            # Extract token counts from usage field if present
            if "usage" in data:
                usage.input_tokens = data["usage"].get("prompt_tokens", 0)
                usage.output_tokens = data["usage"].get("completion_tokens", 0)
            
            # Strip markdown fences if present
            if raw.startswith("```"):
                raw = re.sub(r"^```[a-z]*\n?", "", raw)
                raw = re.sub(r"\n?```$", "", raw)
            
            usage.calculate_cost()
            return json.loads(raw), usage
        except Exception as e:
            last_err = e
            wait = BASE_BACKOFF * (2 ** attempt)
            logger.warning(f"Ollama attempt {attempt+1} failed: {e}. Retry in {wait}s")
            time.sleep(wait)

    raise RuntimeError(f"Ollama API failed after {MAX_RETRIES} attempts: {last_err}") from last_err


def compress(log_lines: List[str], session_id: str = "") -> tuple[Dict[str, Any], Optional[UsageRecord]]:
    """Main entry: call Ollama if available, else return empty dict."""
    if not _ollama_available():
        logger.warning("Ollama not available, falling back to empty result")
        return {}, None
    
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    model = os.getenv("TRACELOG_LLM_MODEL", MODEL)
    log_text = chr(10).join(log_lines)
    
    result, usage = _call_ollama(ollama_url, model, log_text)
    usage.session_id = session_id
    logger.info(f"Ollama used {usage.input_tokens}in/{usage.output_tokens}out tokens, ${usage.cost_usd:.6f}")
    return result, usage
