"""
Simple test to verify pytest setup
"""
import pytest

def test_simple():
    """Simple test to verify pytest is working"""
    assert True

@pytest.mark.asyncio
async def test_async_simple():
    """Simple async test to verify pytest-asyncio is working"""
    assert True
