"""
Unit tests for Configuration components.
"""
import pytest
from pathlib import Path
import os
import logging
from datetime import datetime

from config.settings import Settings

@pytest.mark.asyncio
class TestConfiguration:
    """Test suite for configuration components."""
    
    @pytest.fixture(autouse=True)
    def setup_test_env(self, tmp_path):
        """Set up test environment."""
        self.test_log_dir = tmp_path / "test_logs"
        self.test_log_dir.mkdir()
        self.settings = Settings(
            LOG_DIR=str(self.test_log_dir),
            DATA_DIR=str(tmp_path / "data")
        )
        
    async def test_settings_loading(self):
        """Test settings loading and validation."""
        # Test default settings
        assert self.settings.DATABASE_URL is not None
        assert self.settings.IIFL_BASE_URL is not None
        assert self.settings.IIFL_BRIDGE_PORT is not None
        
        # Test environment variable override
        with pytest.MonkeyPatch.context() as m:
            m.setenv("WEB_PORT", "9000")
            test_settings = Settings()
            assert test_settings.WEB_PORT == 9000
            
    async def test_risk_limits_configuration(self):
        """Test risk limits configuration."""
        # Verify risk limits
        assert self.settings.MAX_POSITION_SIZE > 0
        assert self.settings.MAX_TOTAL_RISK > 0
        assert self.settings.STOP_LOSS_MULTIPLIER > 0
        
        # Test validation
        with pytest.raises(ValueError):
            Settings(MAX_POSITION_SIZE=-1000)
            
    async def test_logging_configuration(self):
        """Test logging configuration."""
        # Test log level validation
        with pytest.raises(ValueError):
            Settings(LOG_LEVEL="INVALID")
            
        # Test valid log level
        test_settings = Settings(LOG_LEVEL="DEBUG")
        assert test_settings.LOG_LEVEL == "DEBUG"
            
    async def test_environment_specific_config(self):
        """Test environment-specific configuration loading."""
        # Test development environment
        with pytest.MonkeyPatch.context() as m:
            m.setenv("DEBUG", "true")
            settings = Settings()
            assert settings.DEBUG is True
            
        # Test production environment
        with pytest.MonkeyPatch.context() as m:
            m.setenv("DEBUG", "false")
            settings = Settings()
            assert settings.DEBUG is False
            
    async def test_database_url_validation(self):
        """Test database URL validation."""
        # Test valid URLs
        Settings(DATABASE_URL="sqlite:///test.db")
        Settings(DATABASE_URL="postgresql://user:pass@localhost/db")
        
        # Test invalid URL
        with pytest.raises(ValueError):
            Settings(DATABASE_URL="invalid_url")
            
    async def test_trading_hours_validation(self):
        """Test trading hours configuration."""
        hours = self.settings.TRADING_HOURS
        assert "start" in hours
        assert "end" in hours
        assert len(hours["start"]) == 5  # HH:MM format
        assert len(hours["end"]) == 5    # HH:MM format
        
    async def test_market_regime_thresholds(self):
        """Test market regime thresholds configuration."""
        thresholds = self.settings.REGIME_THRESHOLDS
        assert "bullish" in thresholds
        assert "bearish" in thresholds
        assert "sideways" in thresholds
        
        for regime in ["bullish", "bearish", "sideways"]:
            assert "adx" in thresholds[regime]
            
    async def test_circuit_breaker_settings(self):
        """Test circuit breaker configuration."""
        cb = self.settings.CIRCUIT_BREAKER
        assert cb["max_drawdown"] > 0
        assert cb["volatility_threshold"] > 0
        assert cb["max_trades_per_day"] > 0
        assert cb["max_positions"] > 0
        
    async def test_ml_settings(self):
        """Test ML model settings configuration."""
        ml = self.settings.ML_SETTINGS
        assert ml["feature_window"] > 0
        assert ml["prediction_window"] > 0
        assert 0 < ml["confidence_threshold"] < 1
        
    async def test_telegram_settings(self):
        """Test Telegram configuration."""
        with pytest.MonkeyPatch.context() as m:
            m.setenv("TELEGRAM_CHAT_ID", "test_chat")
            m.setenv("TELEGRAM_BOT_TOKEN", "test_token")
            settings = Settings()
            assert settings.TELEGRAM_CHAT_ID == "test_chat"
            assert settings.TELEGRAM_BOT_TOKEN == "test_token"

if __name__ == '__main__':
    unittest.main()
