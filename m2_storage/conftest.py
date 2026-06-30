import sys, pathlib
_M2 = str(pathlib.Path(__file__).parent)
def pytest_configure(config):
    # Remove competing milestone paths, put M2 first
    competing = [p for p in sys.path if any(x in p for x in ["m4_memory","m3_compression","m5_sandbox","m6_slack"])]
    for p in competing:
        sys.path.remove(p)
    if _M2 not in sys.path:
        sys.path.insert(0, _M2)
