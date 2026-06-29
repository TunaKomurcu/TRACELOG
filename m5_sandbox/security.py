"""Sazabi M5 - Security layer: whitelist, path validation, command parsing."""
import re, pathlib, shlex, os
from typing import List, Tuple

ALLOWED_COMMANDS = {"python", "python3", "pip", "pip3", "pytest", "git", "cat", "ls", "grep"}

# Patterns that are never allowed regardless of whitelist
_DANGEROUS_PATTERNS = [
    r"rm\s+-[rf]", r"rm\s+--recursive", r"mkfs", r"dd\s+if=",
    r"chmod\s+777", r"curl\s+.*\|\s*sh", r"wget\s+.*\|\s*sh",
    r">\s*/dev/", r"os\.system", r"subprocess\.call.*shell=True",
]
_DANGEROUS_RE = re.compile("|".join(_DANGEROUS_PATTERNS), re.IGNORECASE)


class SecurityError(Exception):
    """Raised when a command violates security policy."""


def parse_command(raw: str) -> List[str]:
    """Split raw command string into argv list."""
    try:
        return shlex.split(raw)
    except ValueError as e:
        raise SecurityError(f"Invalid command syntax: {e}") from e


def validate_command(argv: List[str]) -> None:
    """Raise SecurityError if command is not allowed."""
    if not argv:
        raise SecurityError("Empty command")

    # Check executable against whitelist
    exe = pathlib.Path(argv[0]).name.lower()
    # Strip .exe on Windows
    exe = exe.replace(".exe", "")
    if exe not in ALLOWED_COMMANDS:
        raise SecurityError(f"Command not allowed: {argv[0]!r}. Allowed: {sorted(ALLOWED_COMMANDS)}")

    # Check for dangerous patterns in full command string
    full = " ".join(str(a) for a in argv)
    if _DANGEROUS_RE.search(full):
        raise SecurityError(f"Dangerous pattern detected in command: {full[:200]!r}")


def validate_write_path(path: str, sandbox_dir: str) -> None:
    """Ensure path is inside sandbox_dir. Raises SecurityError otherwise."""
    try:
        resolved = pathlib.Path(path).resolve()
        sandbox_resolved = pathlib.Path(sandbox_dir).resolve()
        resolved.relative_to(sandbox_resolved) # raises ValueError if outside
    except ValueError:
        raise SecurityError(f"Write path {path!r} is outside sandbox {sandbox_dir!r}")
