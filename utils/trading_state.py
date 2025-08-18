"""
Trading state manager for QuantHybrid system.
"""
from threading import Lock
from typing import Dict, Any
from config.logging_config import get_logger

logger = get_logger('system')

class TradingState:
    """
    Manages the global trading state of the system.
    Implements a thread-safe singleton pattern.
    """
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TradingState, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._trading_enabled = False
        self._emergency_stop = False
        self._component_status = {
            'market_data': False,
            'risk_manager': False,
            'order_manager': False,
            'strategy_engine': False
        }
        self._strategy_status = {}
        self._lock = Lock()
        self._initialized = True
        
        logger.info("Trading state manager initialized")
    
    def enable_trading(self) -> bool:
        """Enable trading if all components are ready."""
        with self._lock:
            if all(self._component_status.values()) and not self._emergency_stop:
                self._trading_enabled = True
                logger.info("Trading enabled")
                return True
            logger.warning("Cannot enable trading - not all components are ready")
            return False
    
    def disable_trading(self) -> None:
        """Disable trading."""
        with self._lock:
            self._trading_enabled = False
            logger.info("Trading disabled")
    
    def emergency_stop(self) -> None:
        """Trigger emergency stop."""
        with self._lock:
            self._emergency_stop = True
            self._trading_enabled = False
            logger.critical("EMERGENCY STOP triggered")
    
    def reset_emergency_stop(self) -> None:
        """Reset emergency stop state."""
        with self._lock:
            self._emergency_stop = False
            logger.info("Emergency stop reset")
    
    def is_trading_enabled(self) -> bool:
        """Check if trading is enabled."""
        return self._trading_enabled and not self._emergency_stop
    
    def is_emergency_stop(self) -> bool:
        """Check if emergency stop is active."""
        return self._emergency_stop
    
    def set_component_status(self, component: str, status: bool) -> None:
        """Set the status of a system component."""
        with self._lock:
            if component in self._component_status:
                self._component_status[component] = status
                logger.info(f"Component {component} status set to {status}")
            else:
                logger.warning(f"Unknown component: {component}")
    
    def set_strategy_status(self, strategy: str, status: bool) -> None:
        """Set the status of a trading strategy."""
        with self._lock:
            self._strategy_status[strategy] = status
            logger.info(f"Strategy {strategy} status set to {status}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get complete system status."""
        return {
            'trading_enabled': self._trading_enabled,
            'emergency_stop': self._emergency_stop,
            'component_status': self._component_status.copy(),
            'strategy_status': self._strategy_status.copy()
        }
