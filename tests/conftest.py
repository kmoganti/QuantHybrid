"""
Test configuration and fixtures.
"""
import os
import sys
import pytest
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

@pytest.fixture(scope='session')
def event_loop():
    """Create an instance of the default event loop for each test case."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment."""
    os.environ['TESTING'] = 'true'
    os.environ['LOG_LEVEL'] = 'DEBUG'
    yield
    os.environ.pop('TESTING', None)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_data_dir():
    """Create and return a test data directory."""
    data_dir = Path(__file__).parent / "test_data"
    data_dir.mkdir(exist_ok=True)
    yield data_dir
    # Cleanup after tests
    if data_dir.exists():
        for file in data_dir.glob("*"):
            file.unlink()
        data_dir.rmdir()

@pytest.fixture(scope="session")
async def test_db():
    """Create test database manager."""
    db = DatabaseManager(test_mode=True)
    await db.init_db()
    return db

@pytest.fixture(scope="session")
def test_log_dir():
    """Create and return a test log directory."""
    log_dir = Path(__file__).parent / "test_logs"
    log_dir.mkdir(exist_ok=True)
    yield log_dir
    # Cleanup after tests
    if log_dir.exists():
        for file in log_dir.glob("*"):
            file.unlink()
        log_dir.rmdir()
