import os, re, sys, json, subprocess, pathlib, pytest



LOGGER_DIR = pathlib.Path(__file__).parent.parent

LOGGER_SCRIPT = LOGGER_DIR / "logger.py"



ISO8601_PATTERN = re.compile(r"\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z\]")





def run_logger(*args, timeout=20):

    return subprocess.run(

        [sys.executable, str(LOGGER_SCRIPT), "--"] + list(args),

        capture_output=True, text=True, timeout=timeout,

    )





def find_latest_log():

    if os.name == "nt":

        log_dir = pathlib.Path(os.environ.get("TEMP", r"C:\\Temp")) / "tracelog"

    else:

        log_dir = pathlib.Path("/tmp") / "tracelog"

    logs = sorted(log_dir.glob("session_*.log"), key=lambda p: p.stat().st_mtime)

    assert logs, "Hic log dosyasi bulunamadi"

    return logs[-1]





class TestExitCodePropagation:

    def test_exit_code_zero(self):

        result = run_logger(sys.executable, "-c", "pass")

        assert result.returncode == 0



    def test_exit_code_one(self):

        result = run_logger(sys.executable, "-c", "import sys; sys.exit(1)")

        assert result.returncode == 1



    def test_exit_code_42(self):

        result = run_logger(sys.executable, "-c", "import sys; sys.exit(42)")

        assert result.returncode == 42



    def test_acceptance_exit_one_with_print(self):

        result = run_logger(sys.executable, "-c", "print(chr(104)+chr(101)+chr(108)+chr(108)+chr(111)); import sys; sys.exit(1)")

        combined = result.stdout + result.stderr

        assert "hello" in combined

        assert result.returncode == 1





class TestOutputPassthrough:

    def test_stdout_passthrough(self):

        result = run_logger(sys.executable, "-c", "print(chr(104)+chr(101)+chr(108)+chr(108)+chr(111)+chr(32)+chr(116)+chr(114)+chr(97)+chr(99)+chr(101)+chr(108)+chr(111)+chr(103))")

        combined = result.stdout + result.stderr

        assert "hello tracelog" in combined



    def test_stderr_passthrough(self):

        result = run_logger(sys.executable, "-c", "import sys; sys.stderr.write(chr(101)+chr(114)+chr(114)+chr(32)+chr(109)+chr(115)+chr(103)+chr(10))")

        combined = result.stdout + result.stderr

        assert "err msg" in combined



    def test_output_in_log_file(self):

        run_logger(sys.executable, "-c", "print(chr(117)+chr(110)+chr(105)+chr(113)+chr(117)+chr(101)+chr(95)+chr(109)+chr(97)+chr(114)+chr(107)+chr(101)+chr(114)+chr(95)+chr(120)+chr(121)+chr(122))")

        log = find_latest_log()

        content = log.read_text(encoding="utf-8")

        assert "unique_marker_xyz" in content





class TestLogLineFormat:

    def test_all_log_lines_have_timestamp(self):

        run_logger(sys.executable, "-c", "print(chr(116)+chr(115))")

        log = find_latest_log()

        content = log.read_text(encoding="utf-8")

        log_lines = [l for l in content.splitlines() if l.strip() and not l.startswith('[META:')]

        assert log_lines

        for line in log_lines:

            assert ISO8601_PATTERN.search(line), f"No timestamp: {line!r}"



    def test_stream_label_in_log(self):

        run_logger(sys.executable, "-c", "print(chr(115))")

        log = find_latest_log()

        content = log.read_text(encoding="utf-8")

        assert "[stdout]" in content or "[stderr]" in content



    def test_stderr_label_in_log(self):

        run_logger(sys.executable, "-c", "import sys; sys.stderr.write(chr(101)+chr(114)+chr(114)+chr(10))")

        log = find_latest_log()

        content = log.read_text(encoding="utf-8")

        assert "[stderr]" in content





class TestSessionMetadata:

    def test_start_metadata_present(self):

        run_logger(sys.executable, "-c", "pass")

        log = find_latest_log()

        assert "META:START" in log.read_text(encoding="utf-8")



    def test_end_metadata_present(self):

        run_logger(sys.executable, "-c", "pass")

        log = find_latest_log()

        assert "META:END" in log.read_text(encoding="utf-8")



    def test_end_metadata_has_exit_code(self):

        run_logger(sys.executable, "-c", "import sys; sys.exit(3)")

        log = find_latest_log()

        content = log.read_text(encoding="utf-8")

        end_line = next((l for l in content.splitlines() if "META:END" in l), None)

        assert end_line is not None

        meta = json.loads(end_line.split("[META:END] ", 1)[1])

        assert meta["exit_code"] == 3



    def test_metadata_has_command(self):

        run_logger(sys.executable, "-c", "pass")

        log = find_latest_log()

        content = log.read_text(encoding="utf-8")

        start_line = next((l for l in content.splitlines() if "META:START" in l), None)

        assert start_line is not None

        meta = json.loads(start_line.split("[META:START] ", 1)[1])

        assert "command" in meta

        assert "started_at" in meta





class TestLoggerCLI:

    def test_no_separator_exits_nonzero(self):

        result = subprocess.run([sys.executable, str(LOGGER_SCRIPT)], capture_output=True, text=True, timeout=10)

        assert result.returncode != 0



    def test_empty_command_after_separator(self):

        result = subprocess.run([sys.executable, str(LOGGER_SCRIPT), "--"], capture_output=True, text=True, timeout=10)

        assert result.returncode != 0



    def test_log_file_created(self):

        run_logger(sys.executable, "-c", "print(chr(102))")

        log = find_latest_log()

        assert log.exists()

        assert log.stat().st_size > 0

