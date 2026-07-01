"""Tracelog M6 - Slack Block Kit message builders."""
from typing import List, Dict, Any


def _sec(text: str) -> Dict:
    return {"type": "section", "text": {"type": "mrkdwn", "text": text}}


def _div() -> Dict:
    return {"type": "divider"}


def _header(text: str) -> Dict:
    return {"type": "header", "text": {"type": "plain_text", "text": text, "emoji": True}}


def error_block(msg: str) -> List[Dict]:
    return [_sec(f":x: *Error:* {msg}")]


def status_blocks(health: Dict[str, Any]) -> List[Dict]:
    blocks = [_header(":mag: Tracelog System Status")]
    for name, info in health.items():
        st = info.get("status", "unknown")
        emoji = ":white_check_mark:" if st == "ok" else ":red_circle:"
        detail = info.get("detail", "")
        d = f" _{detail}_" if detail else ""
        blocks.append(_sec(f"{emoji} *{name}*: {st}{d}"))
    return blocks


def run_blocks(result: Dict[str, Any]) -> List[Dict]:
    status = result.get("status","unknown")
    exit_code = result.get("exit_code",-1)
    stdout = result.get("stdout","").strip()
    stderr = result.get("stderr","").strip()[:500]
    dur = result.get("duration_ms",0)
    cmd = result.get("command","")[:120]
    emoji = ":white_check_mark:" if exit_code == 0 else ":x:"
    blocks = [_header(f"{emoji} Sandbox Result")]
    blocks.append(_sec(f"*Command:* `{cmd}`"))
    blocks.append(_sec(f"*Status:* {status} | *Exit:* `{exit_code}` | *Time:* {dur:.0f}ms"))
    if status == "rejected":
        blocks.append(_sec(f":no_entry: *Rejected:*\n```{stderr[:300]}```"))
        return blocks
    if stdout:
        blocks.append(_sec(f"*stdout:*\n```{stdout[:800]}```"))
    if stderr:
        blocks.append(_sec(f"*stderr:*\n```{stderr[:400]}```"))
    return blocks


def logs_blocks(session_id: str, compressed: Dict[str, Any]) -> List[Dict]:
    summary = compressed.get("summary", {})
    if isinstance(summary, str):
        summary = {"summary": summary, "errors": [], "anomalies": [], "root_cause_hint": ""}
    blocks = [_header(f":scroll: Log Summary")]
    blocks.append(_sec(f"*Session:* `{session_id}`"))
    blocks.append(_sec(summary.get("summary","No summary.")))
    errs = summary.get("errors",[])[:5]
    if errs:
        lines = []
        for e in errs:
            ln = e.get("line",0); msg = e.get("msg","")[:100]
            lines.append(f":warning: Line {ln}: {msg}")
        blocks.append(_sec(f"*Errors ({len(errs)}):*\n"+chr(10).join(lines)))
    hint = summary.get("root_cause_hint","")
    if hint:
        blocks.append(_sec(f"*Root cause:*\n>{hint[:300]}"))
    return blocks


def memory_blocks(agent_id: str, timeline: Dict[str, Any]) -> List[Dict]:
    blocks = [_header(f":brain: Agent Memory")]
    total = timeline.get("total_steps",0)
    blocks.append(_sec(f"*Agent:* `{agent_id}` | *Steps:* {total}"))
    for step in timeline.get("steps",[])[:10]:
        num = step.get("step_number","?")
        atype = step.get("action_type") or "unknown"
        rsumm = step.get("result_summary") or ""
        snaps = len(step.get("snapshots",[]))
        snap_str = f" :file_folder:{snaps}" if snaps else ""
        blocks.append(_sec(f"*Step {num}* `{atype}`: {rsumm[:100]}{snap_str}"))
    if total > 10:
        blocks.append(_sec(f"_...and {total-10} more_"))
    return blocks


def alerts_blocks(alerts: List[Dict]) -> List[Dict]:
    blocks = [_header(":rotating_light: Recent Alerts (60 min)")]
    if not alerts:
        blocks.append(_sec(":white_check_mark: No critical alerts."))
        return blocks
    critical = [a for a in alerts if a.get("severity")=="critical"]
    warnings = [a for a in alerts if a.get("severity")!="critical"]
    if critical:
        blocks.append(_sec(f":red_circle: *{len(critical)} critical alert(s)*"))
        for a in critical[:5]:
            sid = a.get("session_id","?")[:16]
            msg = a.get("msg","")[:150]
            blocks.append(_sec(f" `{sid}...` : {msg}"))
    if warnings:
        blocks.append(_sec(f":warning: {len(warnings)} warning(s)"))
    return blocks


def critical_alert_blocks(session_id: str, errors: List[Dict]) -> List[Dict]:
    blocks = [_header(":rotating_light: CRITICAL ALERT")]
    blocks.append(_sec(f"*Session:* `{session_id}`"))
    for e in errors[:3]:
        msg = e.get("msg","")[:200]
        blocks.append(_sec(f":red_circle: {msg}"))
    return blocks
