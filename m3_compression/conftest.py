# pytest rootdir marker for m3_compression
import sys, pathlib, pytest
sys.path.insert(0, str(pathlib.Path(__file__).parent))


def pytest_collection_modifyitems(config, items):
    """Apply 15-second timeout to all tests."""
    for item in items:
        item.add_marker(pytest.mark.timeout(15))
