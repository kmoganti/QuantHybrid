"""
Debug test for settings import
"""
import pytest
import os
from pathlib import Path
import sys

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def test_import_settings():
    """Test that we can import the Settings class"""
    from config.settings import Settings
    assert Settings is not None
    
def test_create_settings():
    """Test that we can create a Settings instance"""
    from config.settings import Settings
    settings = Settings()
    assert settings is not None
    assert settings.DATABASE_URL is not None

@pytest.mark.asyncio
async def test_async_settings():
    """Test async functionality with settings"""
    from config.settings import Settings
    settings = Settings()
    assert settings.TRADING_ENABLED is not None
