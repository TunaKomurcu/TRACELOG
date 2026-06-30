import sys, pathlib
_M4 = str(pathlib.Path(__file__).parent)
def pytest_configure(config):
    competing = [p for p in sys.path if any(x in p for x in ["m2_storage","m3_compression","m5_sandbox","m6_slack"])]
    for p in competing:
        sys.path.remove(p)
    if _M4 not in sys.path:
        sys.path.insert(0, _M4)
