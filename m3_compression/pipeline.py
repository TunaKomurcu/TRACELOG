"""Sazabi M3 - Main compression pipeline."""
import json, logging, pathlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import filter as log_filter
import compressor
import fallback

logger = logging.getLogger("sazabi.m3.pipeline")


@dataclass
class CompressionResult:
    summary: Dict[str, Any]
    filter_stats: Dict[str, Any]
    used_llm: bool = False
    usage: Optional[object] = None

    def to_dict(self) -> Dict[str, Any]:
        out = dict(self.summary)
        out["_meta"] = {
            "used_llm": self.used_llm,
            "filter_stats": self.filter_stats,
        }
        if self.usage:
            out["_meta"]["tokens"] = {
                "input": self.usage.input_tokens,
                "output": self.usage.output_tokens,
                "cost_usd": self.usage.cost_usd,
                "model": self.usage.model,
            }
        return out


def run(lines: List[str], session_id: str = "") -> CompressionResult:
    """
    Full pipeline:
     1. Pre-filter (dedup + DEBUG removal + byte cap)
     2. Try Gemini API
     3. Fallback to rule-based if no API key or API error
    """
    # Step 1: filter
    fres = log_filter.pre_filter(lines)
    logger.info(f"Filter: {fres.stats()}")

    # Step 2: try Gemini LLM
    try:
        result, usage = compressor.compress(fres.kept, session_id)
        if result:
            return CompressionResult(
                summary=result,
                filter_stats=fres.stats(),
                used_llm=True,
                usage=usage,
            )
    except Exception as e:
        logger.warning(f"Gemini compression failed, using fallback: {e}")

    # Step 3: fallback
    fb = fallback.rule_based_summary(fres.kept)
    return CompressionResult(summary=fb, filter_stats=fres.stats(), used_llm=False)
