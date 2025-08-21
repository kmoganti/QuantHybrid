"""
SQLAlchemy database models for QuantHybrid system.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()

class OrderStatus(enum.Enum):
    PENDING = "pending"
    PLACED = "placed"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    MODIFIED = "modified"

class MarketRegime(enum.Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    SIDEWAYS = "sideways"
    AMBIGUOUS = "ambiguous"

class Trade(Base):
    """Model for executed trades."""
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    # Original fields used by execution layer
    instrument_id = Column(String)
    order_id = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    transaction_type = Column(String)
    quantity = Column(Integer)
    price = Column(Float)
    strategy = Column(String)
    pnl = Column(Float, default=0.0)
    portfolio_type = Column(String)
    
    # Additional fields expected by tests
    symbol = Column(String)  # e.g., 'RELIANCE'
    entry_price = Column(Float)
    exit_price = Column(Float)
    entry_time = Column(DateTime)
    exit_time = Column(DateTime)
    strategy_id = Column(Integer)

class Position(Base):
    """Model for current positions."""
    __tablename__ = 'positions'
    
    id = Column(Integer, primary_key=True)
    # Original fields
    instrument_id = Column(String)
    quantity = Column(Integer)
    average_price = Column(Float)
    current_price = Column(Float)
    pnl = Column(Float, default=0.0)
    portfolio_type = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Additional fields expected by tests
    symbol = Column(String, index=True)
    unrealized_pnl = Column(Float)
    strategy_id = Column(Integer)

class MarketState(Base):
    """Model for market regime and conditions."""
    __tablename__ = 'market_states'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    regime = Column(Enum(MarketRegime))
    adx = Column(Float)
    volatility = Column(Float)
    trend_strength = Column(Float)
    ml_confidence = Column(Float)

class Order(Base):
    """Model for orders."""
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    broker_order_id = Column(String, unique=True)
    # Original fields
    instrument_id = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    transaction_type = Column(String)  # BUY/SELL
    quantity = Column(Integer)
    price = Column(Float)
    trigger_price = Column(Float)
    # Adjusted to String to match tests that use raw strings like 'PENDING', 'EXECUTED'
    status = Column(String)
    strategy = Column(String)
    portfolio_type = Column(String)

    # Additional fields expected by tests
    symbol = Column(String, index=True)
    order_type = Column(String)  # e.g., 'MARKET', 'LIMIT'
    side = Column(String)  # 'BUY' or 'SELL'
    strategy_id = Column(Integer)

class Performance(Base):
    """Model for strategy performance metrics."""
    __tablename__ = 'performance'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    strategy = Column(String, nullable=False)
    daily_pnl = Column(Float, default=0.0)
    daily_trades = Column(Integer, default=0)
    win_rate = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    roi = Column(Float)

class SystemMetrics(Base):
    """Model for system health and performance metrics."""
    __tablename__ = 'system_metrics'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    api_latency = Column(Float)
    order_success_rate = Column(Float)
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    error_count = Column(Integer)
    warning_count = Column(Integer)

# Additional models required by tests
from sqlalchemy.types import JSON

class Strategy(Base):
    """Model for trading strategies.
    Provides minimal fields required by tests: name, parameters (JSON), status, and capital allocation.
    """
    __tablename__ = 'strategies'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    parameters = Column(JSON, default={})
    status = Column(String, default='INACTIVE')
    capital_allocated = Column(Float, default=0.0)

class Account(Base):
    """Model for account summary metrics used by web interface and tests."""
    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True)
    balance = Column(Float, default=0.0)
    equity = Column(Float, default=0.0)
    margin_used = Column(Float, default=0.0)
    free_margin = Column(Float, default=0.0)