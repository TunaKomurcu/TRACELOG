"""Sazabi M1 - Naked Logger
Bu script herhangi bir komutu wrap eder, stdout/stderr akislarini
real-time hem terminale hem log dosyasina yaziyor.
Bu script herhangi bir komutu wrap eder.
Kullanim: python logger.py -- KOMUT [args...]
"""
import os, sys, signal, subprocess, threading, uuid, json, pathlib
from datetime import datetime, timezone


def utc_now():
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


def get_log_dir():
    if os.name == "nt":
        base = pathlib.Path(os.environ.get("TEMP", "C:/Temp"))
    else:
        base = pathlib.Path("/tmp")
    log_dir = base / "sazabi"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


class NakedLogger:
    def __init__(self, command: list):
        self.command = command
        self.session_id = str(uuid.uuid4())
        self.log_path = get_log_dir() / f"session_{self.session_id}.log"
        self.log_file = None
        self.process = None
        self.exit_code = 0
        self.started_at = None
        self._lock = threading.Lock()

    def _write_log(self, line: str):
        with self._lock:
            if self.log_file and not self.log_file.closed:
                self.log_file.write(line + "\n")
                self.log_file.flush()

    def _format_line(self, stream: str, message: str):
        return f"[{utc_now()}] [{stream}] {message}"

    def _stream_reader(self, stream, stream_name: str):
        try:
            for raw in iter(stream.readline, b""):
                line = raw.decode("utf-8", errors="replace").rstrip("\n\r")
                formatted = self._format_line(stream_name, line)
                if stream_name == "stdout":
                    sys.stdout.write(formatted + "\n")
                    sys.stdout.flush()
                else:
                    sys.stderr.write(formatted + "\n")
                    sys.stderr.flush()
                self._write_log(formatted)
        except ValueError:
            pass

    def _signal_handler(self, signum, frame):
        if self.process and self.process.poll() is None:
            try:
                self.process.send_signal(signum)
            except (ProcessLookupError, OSError):
                pass

    def run(self):
        self.started_at = utc_now()
        self.log_file = open(self.log_path, "w", encoding="utf-8")
        start_meta = json.dumps({"session_id": self.session_id, "command": self.command, "pid": None, "started_at": self.started_at})
        self._write_log(f"[META:START] {start_meta}")
        signal.signal(signal.SIGINT, self._signal_handler)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, self._signal_handler)
        self.process = subprocess.Popen(self.command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        pid_meta = json.dumps({"session_id": self.session_id, "command": self.command, "pid": self.process.pid, "started_at": self.started_at})
        self._write_log(f"[META:PID] {pid_meta}")
        t_out = threading.Thread(target=self._stream_reader, args=(self.process.stdout, "stdout"), daemon=True)
        t_err = threading.Thread(target=self._stream_reader, args=(self.process.stderr, "stderr"), daemon=True)
        t_out.start(); t_err.start()
        self.process.wait()
        t_out.join(timeout=5); t_err.join(timeout=5)
        self.exit_code = self.process.returncode
        finished_at = utc_now()
        started_dt = datetime.fromisoformat(self.started_at.replace("Z", "+00:00"))
        finished_dt = datetime.fromisoformat(finished_at.replace("Z", "+00:00"))
        duration = (finished_dt - started_dt).total_seconds()
        end_meta = json.dumps({"finished_at": finished_at, "exit_code": self.exit_code, "duration_seconds": round(duration, 3)})
        self._write_log(f"[META:END] {end_meta}")
        self.log_file.close()
        return self.exit_code


def main():
    if "--" not in sys.argv:
        print("Kullanim: python logger.py -- KOMUT [args...]", file=sys.stderr)
        sys.exit(1)
    sep_idx = sys.argv.index("--")
    command = sys.argv[sep_idx + 1:]
    if not command:
        print("Hata: -- sonrasinda komut belirtilmedi.", file=sys.stderr)
        sys.exit(1)
    logger = NakedLogger(command)
    sys.stderr.write(f"[sazabi] Log: {logger.log_path}\n")
    sys.exit(logger.run())


if __name__ == "__main__":
    main()
