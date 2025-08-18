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
    instrument_id = Column(String, nullable=False)
    order_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    transaction_type = Column(String, nullable=False)  # BUY/SELL
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    strategy = Column(String, nullable=False)
    pnl = Column(Float, default=0.0)
    portfolio_type = Column(String)  # CORE/SATELLITE

class Position(Base):
    """Model for current positions."""
    __tablename__ = 'positions'
    
    id = Column(Integer, primary_key=True)
    instrument_id = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    average_price = Column(Float, nullable=False)
    current_price = Column(Float)
    pnl = Column(Float, default=0.0)
    portfolio_type = Column(String)  # CORE/SATELLITE
    timestamp = Column(DateTime, default=datetime.utcnow)

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
    instrument_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    transaction_type = Column(String, nullable=False)  # BUY/SELL
    quantity = Column(Integer, nullable=False)
    price = Column(Float)
    trigger_price = Column(Float)
    status = Column(Enum(OrderStatus))
    strategy = Column(String, nullable=False)
    portfolio_type = Column(String)  # CORE/SATELLITE

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
