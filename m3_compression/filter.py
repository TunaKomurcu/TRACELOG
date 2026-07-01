"""Tracelog M3 - Rule-based pre-filter for log compression."""
import re
from dataclasses import dataclass, field
from typing import List

# Patterns that indicate DEBUG-level noise
_DEBUG_RE = re.compile(r"(?i)\b(debug|trace|verbose)\b")
_TIMESTAMP_RE = re.compile(r"\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z\]")


@dataclass
class FilterResult:
    kept: List[str] = field(default_factory=list)
    removed_debug: int = 0
    removed_duplicate: int = 0

    @property
    def total_removed(self) -> int:
        return self.removed_debug + self.removed_duplicate

    def stats(self) -> dict:
        return {
            "kept": len(self.kept),
            "removed_debug": self.removed_debug,
            "removed_duplicate": self.removed_duplicate,
        }


def _strip_timestamp(line: str) -> str:
    """Remove leading [ISO8601] [stream] prefix for dedup comparison."""
    line = _TIMESTAMP_RE.sub("", line)
    return re.sub(r"^\s*\[(stdout|stderr)\]\s*", "", line).strip()


def pre_filter(lines: List[str], max_bytes: int = 50_000) -> FilterResult:
    """
    Rule-based pre-filter:
     1. Remove DEBUG/TRACE lines.
     2. Remove consecutive duplicate lines (keep first + count).
     3. Truncate to max_bytes.
    """
    result = FilterResult()
    seen_content: dict = {} # normalised content -> first occurrence index
    last_norm = None
    consec_count = 0

    for raw_line in lines:
        # Skip empty META lines
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("[META:"):
            continue

        # Skip DEBUG / TRACE lines
        if _DEBUG_RE.search(stripped):
            result.removed_debug += 1
            continue

        norm = _strip_timestamp(stripped)

        # Collapse consecutive identical lines
        if norm == last_norm:
            consec_count += 1
            result.removed_duplicate += 1
            # Annotate first occurrence with repeat count
            if result.kept:
                result.kept[-1] = result.kept[-1].rstrip() + f" [x{consec_count+1}]"
            continue

        last_norm = norm
        consec_count = 0
        result.kept.append(stripped)

    # Byte-limit truncation
    total = 0
    truncated = []
    for line in result.kept:
        encoded = len(line.encode("utf-8")) + 1
        if total + encoded > max_bytes:
            break
        total += encoded
        truncated.append(line)
    result.kept = truncated
    return result
