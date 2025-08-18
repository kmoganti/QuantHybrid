"""Basic test file for initial verification"""
import pytest
from pathlib import Path
import sys

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_basic():
    """Basic test to verify test running"""
    assert True

def test_python_path():
    """Test that we can import our project modules"""
    from config import settings
    assert settings is not None

@pytest.mark.asyncio
async def test_async_basic():
    """Basic async test"""
    assert True
