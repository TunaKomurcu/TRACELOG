"""Tracelog M3 - Rule-based fallback summarizer (no API key needed)."""
import re
from typing import List, Dict, Any

_ERROR_RE = re.compile(r"(?i)\b(error|exception|critical|fatal|traceback|failed)\b")
_WARN_RE = re.compile(r"(?i)\b(warning|warn)\b")
_TS_RE = re.compile(r"^\[[\d\-T:\.Z]+\]\s*(\[stdout\]|\[stderr\])?\s*")
_ERR_LINE_RE = re.compile(r"^[\w\.]+Error:|^[\w\.]+Exception:")


def _clean(line: str) -> str:
    """Strip ISO timestamp and stream prefix to get raw message."""
    return _TS_RE.sub("", line).strip()


def rule_based_summary(lines: List[str]) -> Dict[str, Any]:
    """Build a structured summary using only regex, no LLM."""
    errors = []
    anomalies = []
    tb_lines = []
    in_traceback = False

    for i, line in enumerate(lines, start=1):
        raw = line.strip()
        msg = _clean(raw)

        if "Traceback (most recent call last)" in msg:
            in_traceback = True

        if in_traceback:
            tb_lines.append(msg)
            if _ERR_LINE_RE.match(msg):
                in_traceback = False
                errors.append({"line": i, "msg": msg, "severity": "critical"})
        elif _ERROR_RE.search(msg):
            errors.append({"line": i, "msg": msg[:200], "severity": "warning"})
        elif _WARN_RE.search(msg):
            anomalies.append(f"Line {i}: {msg[:150]}")

    # Root cause: prefer last critical error, fall back to last tb line
    root_cause = ""
    crit = [e for e in errors if e["severity"] == "critical"]
    if crit:
        root_cause = crit[-1]["msg"][:300]
    elif tb_lines:
        root_cause = tb_lines[-1][:300]
    elif errors:
        root_cause = errors[-1]["msg"][:300]

    total = len(lines)
    err_count = len(errors)
    warn_count = len(anomalies)
    parts = [f"{total} log satirindan {err_count} hata ve {warn_count} uyari tespit edildi."]
    if errors:
        last_msg = errors[-1]["msg"][:150]
        parts.append(f"En ciddi hata: {last_msg}.")
    if tb_lines:
        parts.append("Python exception traceback bulundu.")

    return {
        "summary": " ".join(parts),
        "errors": errors[:20],
        "anomalies": anomalies[:10],
        "root_cause_hint": root_cause,
    }
