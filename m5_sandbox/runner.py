"""Sazabi M5 - Sandbox runner: subprocess + timeout + resource limits."""
import os, sys, time, uuid, shutil, subprocess, pathlib, threading
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from security import validate_command, parse_command, SecurityError

MAX_TIMEOUT_SEC = int(os.getenv("SANDBOX_TIMEOUT", "30"))
MAX_OUTPUT_BYTES = 512 * 1024 # 512 KB
MAX_RAM_MB = int(os.getenv("SANDBOX_MAX_RAM_MB", "256"))


def _get_sandbox_base() -> pathlib.Path:
    if os.name == "nt":
        base = pathlib.Path(os.environ.get("TEMP", "C:/Temp")) / "sazabi_sandbox"
    else:
        base = pathlib.Path("/tmp/sazabi_sandbox")
    base.mkdir(parents=True, exist_ok=True)
    return base


def _make_sandbox_dir(sandbox_id: str) -> pathlib.Path:
    d = _get_sandbox_base() / f"sandbox_{sandbox_id}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _apply_resource_limits() -> None:
    """Apply rlimits on Linux. No-op on Windows (timeout enforced externally)."""
    if os.name == "nt":
        return
    try:
        import resource
        # CPU time (hard limit: TIMEOUT + 5s buffer)
        resource.setrlimit(resource.RLIMIT_CPU, (MAX_TIMEOUT_SEC, MAX_TIMEOUT_SEC + 5))
        # Virtual memory (256 MB)
        ram_bytes = MAX_RAM_MB * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (ram_bytes, ram_bytes))
        # Max processes (100)
        resource.setrlimit(resource.RLIMIT_NPROC, (100, 100))
    except Exception:
        pass # Non-fatal: timeout is the primary enforcer


def _peak_memory_mb(proc: subprocess.Popen) -> float:
    """Try to read peak RSS of subprocess. Returns 0.0 if unavailable."""
    try:
        if os.name == "nt":
            import ctypes
            PROCESS_QUERY_INFORMATION = 0x0400
            h = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, proc.pid)
            if h:
                info = ctypes.create_string_buffer(72)
                ctypes.windll.psapi.GetProcessMemoryInfo(h, info, 72)
                peak = int.from_bytes(info[28:36], "little")
                ctypes.windll.kernel32.CloseHandle(h)
                return round(peak / (1024*1024), 2)
        else:
            with open(f"/proc/{proc.pid}/status") as f:
                for line in f:
                    if line.startswith("VmPeak:"):
                        kb = int(line.split()[1])
                        return round(kb / 1024, 2)
    except Exception:
        pass
    return 0.0


def run_sandboxed(command: str, sandbox_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Main entry point. Validates, runs in sandbox dir, enforces timeout.
    Returns structured result dict compatible with M6 webhook format.
    """
    sandbox_id = sandbox_id or str(uuid.uuid4())
    sandbox_dir = _make_sandbox_dir(sandbox_id)
    started_at = time.monotonic()
    peak_mem = 0.0

    # Security validation
    try:
        argv = parse_command(command)
        validate_command(argv)
    except SecurityError as e:
        return {
            "sandbox_id": sandbox_id,
            "command": command,
            "exit_code": -1,
            "stdout": "",
            "stderr": f"[SECURITY] {e}",
            "duration_ms": 0,
            "resource_usage": {"peak_memory_mb": 0},
            "status": "rejected",
        }

    # Build safe environment
    safe_env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": str(sandbox_dir),
        "TEMP": str(sandbox_dir),
        "TMP": str(sandbox_dir),
        "TMPDIR": str(sandbox_dir),
        "NO_PROXY": "*",
        "no_proxy": "*",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": "",
    }

    # Windows needs SYSTEMROOT / SYSTEMDRIVE
    if os.name == "nt":
        safe_env["SYSTEMROOT"] = os.environ.get("SYSTEMROOT", "C:\\Windows")
        safe_env["SYSTEMDRIVE"] = os.environ.get("SYSTEMDRIVE", "C:")
        safe_env["USERPROFILE"] = str(sandbox_dir)

    try:
        proc = subprocess.Popen(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(sandbox_dir),
            env=safe_env,
            preexec_fn=None if os.name == "nt" else _apply_resource_limits,
        )
        try:
            stdout_bytes, stderr_bytes = proc.communicate(timeout=MAX_TIMEOUT_SEC)
            exit_code = proc.returncode
            status = "completed"
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout_bytes, stderr_bytes = proc.communicate()
            exit_code = -9
            status = "timeout"
        peak_mem = _peak_memory_mb(proc)

    except FileNotFoundError as e:
        return {
            "sandbox_id": sandbox_id, "command": command, "exit_code": -1,
            "stdout": "", "stderr": f"Command not found: {e}",
            "duration_ms": 0, "resource_usage": {"peak_memory_mb": 0}, "status": "error",
        }

    duration_ms = round((time.monotonic() - started_at) * 1000, 1)
    stdout = stdout_bytes.decode("utf-8", errors="replace")[:MAX_OUTPUT_BYTES]
    stderr = stderr_bytes.decode("utf-8", errors="replace")[:MAX_OUTPUT_BYTES]

    return {
        "sandbox_id": sandbox_id,
        "command": command,
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "duration_ms": duration_ms,
        "resource_usage": {"peak_memory_mb": peak_mem},
        "status": status,
        "sandbox_dir": str(sandbox_dir),
    }


def cleanup_sandbox(sandbox_id: str) -> bool:
    """Remove sandbox directory after use."""
    d = _get_sandbox_base() / f"sandbox_{sandbox_id}"
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)
        return True
    return False
