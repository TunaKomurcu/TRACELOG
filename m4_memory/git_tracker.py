"""Sazabi M4 - Git integration: diff --stat and HEAD hash."""
import subprocess, os, pathlib
from typing import Optional, Tuple


def _run(args, cwd=None) -> Tuple[int, str, str]:
    """Run a subprocess, return (returncode, stdout, stderr)."""
    try:
        r = subprocess.run(
            args, capture_output=True, text=True, timeout=10,
            cwd=cwd or os.getcwd())
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return -1, "", str(e)


def is_git_repo(path: str = ".") -> bool:
    code, _, _ = _run(["git", "rev-parse", "--is-inside-work-tree"], cwd=path)
    return code == 0


def get_head_hash(path: str = ".") -> Optional[str]:
    """Return short HEAD commit hash, or None if not a git repo."""
    code, out, _ = _run(["git", "rev-parse", "--short", "HEAD"], cwd=path)
    return out if code == 0 and out else None


def diff_stat(path: str = ".") -> Optional[str]:
    """Return output of git diff --stat (working tree vs HEAD)."""
    code, out, _ = _run(["git", "diff", "--stat"], cwd=path)
    return out if code == 0 else None


def diff_stat_file(file_path: str, repo_root: str = ".") -> Optional[str]:
    """Return git diff --stat for a single file."""
    code, out, _ = _run(["git", "diff", "--stat", file_path], cwd=repo_root)
    return out if code == 0 else None


def snapshot_file(file_path: str, repo_root: str = ".") -> Tuple[Optional[str], Optional[str]]:
    """Return (git_hash, diff_summary) for a file. Graceful if no git repo."""
    if not is_git_repo(repo_root):
        return None, None
    git_hash = get_head_hash(repo_root)
    diff = diff_stat_file(file_path, repo_root)
    return git_hash, diff
