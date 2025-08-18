"""
Settings class for managing configuration.
"""
from pathlib import Path
import os
from typing import Dict, Any, Optional
from pydantic_settings import BaseSettings
from pydantic import validator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """Settings management using Pydantic."""
    
    # Base paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    LOG_DIR: Path = BASE_DIR / "logs"
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create necessary directories
        self.DATA_DIR.mkdir(exist_ok=True)
        self.LOG_DIR.mkdir(exist_ok=True)
    
    # Database
    DATABASE_URL: str = "sqlite:///data/quanthybrid.db"
    
    # API Settings
    # API Settings
    IIFL_BASE_URL: str = "https://api.iiflcapital.com/v1"
    IIFL_BRIDGE_HOST: str = "bridge.iiflcapital.com"
    IIFL_BRIDGE_PORT: int = 9906
    IIFL_API_KEY: Optional[str] = None
    IIFL_API_SECRET: Optional[str] = None
    ENVIRONMENT: Optional[str] = None
    
    # Trading Settings
    TRADING_ENABLED: bool = False  # Master switch for trading
    TRADING_HOURS: Dict[str, str] = {
        "start": "09:15",
        "end": "15:30"
    }
    
    # Risk Management
    MAX_POSITION_SIZE: float = 0.02  # 2% of capital per trade
    MAX_TOTAL_RISK: float = 0.06    # 6% of capital at risk
    STOP_LOSS_MULTIPLIER: float = 2.0  # ATR multiplier for stop loss
    
    # Portfolio Settings
    CORE_ALLOCATION: float = 0.70   # 70% to core portfolio
    SATELLITE_ALLOCATION: float = 0.30  # 30% to satellite portfolio
    
    # Market Regime Thresholds
    REGIME_THRESHOLDS: Dict[str, Dict[str, float]] = {
        "bullish": {
            "adx": 25,
            "bb_expansion": 0.02,
            "ema_slope": 0.001
        },
        "bearish": {
            "adx": 25,
            "bb_contraction": -0.02,
            "ema_slope": -0.001
        },
        "sideways": {
            "adx": 20,
            "bb_width": 0.015,
            "ema_slope": 0.0005
        }
    }
    
    # ML Model Settings
    ML_SETTINGS: Dict[str, Any] = {
        "feature_window": 20,
        "prediction_window": 5,
        "confidence_threshold": 0.65,
        "retraining_interval": "1M"  # 1 month
    }
    
    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Circuit Breaker Settings
    CIRCUIT_BREAKER: Dict[str, Any] = {
        "max_drawdown": 0.05,  # 5% max drawdown
        "volatility_threshold": 2.5,  # 2.5x normal volatility
        "max_trades_per_day": 50,
        "max_positions": 10
    }
    
    # Telegram Settings
    TELEGRAM_ENABLED: bool = True
    TELEGRAM_CHAT_ID: Optional[str] = None
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    
    # Web Interface Settings
    WEB_HOST: str = "localhost"
    WEB_PORT: int = 8000
    DEBUG: bool = True
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        
        @classmethod
        def customise_sources(cls, init_settings, env_settings, file_secret_settings):
            return env_settings, init_settings, file_secret_settings
            
    @validator('LOG_LEVEL')
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Invalid log level. Must be one of {valid_levels}')
        return v.upper()
        
    @validator('DATABASE_URL')
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith('sqlite:///') and not v.startswith('postgresql://'):
            raise ValueError('Invalid database URL')
        return v
