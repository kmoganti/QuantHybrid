"""
Safety monitoring system for QuantHybrid trading system.
"""
import asyncio
import psutil
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import numpy as np
from config.risk_settings import (
    MONITORING_THRESHOLDS,
    HEALTH_CHECK_SETTINGS,
    CIRCUIT_BREAKERS,
    RECOVERY_SETTINGS
)
from config.logging_config import get_logger
from utils.trading_state import TradingState

logger = get_logger('safety_monitor')

class SafetyMonitor:
    def __init__(self, trading_state: TradingState):
        self.trading_state = trading_state
        self.system_metrics = {}
        self.market_metrics = {}
        self.last_health_check = time.time()
        self.monitor_task = None
        self.is_running = False
        self.recovery_mode = False
        self.circuit_breaker_level = 0
        self.last_order_times = {}
        self.order_latencies = []
        self.quote_latencies = []
        self.error_counts = {
            'order_errors': 0,
            'data_errors': 0,
            'system_errors': 0
        }
        
    async def start_monitoring(self):
        """Start the safety monitoring system."""
        try:
            self.is_running = True
            self.monitor_task = asyncio.create_task(self._monitoring_loop())
            logger.info("Safety monitoring system started")
        except Exception as e:
            logger.error(f"Failed to start safety monitoring: {str(e)}")
            raise
    
    async def stop_monitoring(self):
        """Stop the safety monitoring system."""
        try:
            self.is_running = False
            if self.monitor_task:
                self.monitor_task.cancel()
            logger.info("Safety monitoring system stopped")
        except Exception as e:
            logger.error(f"Error stopping safety monitoring: {str(e)}")
            raise
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.is_running:
            try:
                # System health checks
                await self._check_system_health()
                
                # Market condition checks
                await self._check_market_conditions()
                
                # Trading safety checks
                await self._check_trading_safety()
                
                # Recovery mode management
                await self._manage_recovery_mode()
                
                # Circuit breaker management
                await self._manage_circuit_breakers()
                
                # Wait for next check interval
                await asyncio.sleep(HEALTH_CHECK_SETTINGS['check_interval'])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                self.error_counts['system_errors'] += 1
                await asyncio.sleep(5)
    
    async def _check_system_health(self):
        """Check system health metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent()
            if cpu_percent > MONITORING_THRESHOLDS['cpu_warning']:
                logger.warning(f"High CPU usage detected: {cpu_percent}%")
                self.trading_state.set_warning('high_cpu_usage')
            
            # Memory usage
            memory = psutil.virtual_memory()
            if memory.percent > MONITORING_THRESHOLDS['memory_warning']:
                logger.warning(f"High memory usage detected: {memory.percent}%")
                self.trading_state.set_warning('high_memory_usage')
            
            # Disk usage
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                logger.warning(f"High disk usage detected: {disk.percent}%")
                self.trading_state.set_warning('high_disk_usage')
            
            # Network latency
            if self.order_latencies:
                avg_latency = np.mean(self.order_latencies[-100:])
                if avg_latency > MONITORING_THRESHOLDS['latency_warning']:
                    logger.warning(f"High order latency detected: {avg_latency}ms")
                    self.trading_state.set_warning('high_order_latency')
            
            # Error rate monitoring
            total_errors = sum(self.error_counts.values())
            if total_errors > 10:  # More than 10 errors in monitoring period
                logger.warning(f"High error rate detected: {total_errors} errors")
                self.trading_state.set_warning('high_error_rate')
            
            # Update system metrics
            self.system_metrics.update({
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'disk_usage': disk.percent,
                'error_rate': total_errors,
                'avg_order_latency': avg_latency if self.order_latencies else 0
            })
            
        except Exception as e:
            logger.error(f"Error checking system health: {str(e)}")
            self.error_counts['system_errors'] += 1
    
    async def _check_market_conditions(self):
        """Check market conditions for safety."""
        try:
            # Quote staleness check
            for symbol, quote in self.market_metrics.get('quotes', {}).items():
                quote_age = time.time() - quote.get('timestamp', 0)
                if quote_age > HEALTH_CHECK_SETTINGS['max_quote_staleness']:
                    logger.warning(f"Stale quotes detected for {symbol}: {quote_age}ms old")
                    self.trading_state.set_warning('stale_quotes')
            
            # Tick frequency check
            tick_rates = self.market_metrics.get('tick_rates', {})
            for symbol, rate in tick_rates.items():
                if rate < HEALTH_CHECK_SETTINGS['min_tick_frequency']:
                    logger.warning(f"Low tick frequency for {symbol}: {rate} ticks/sec")
                    self.trading_state.set_warning('low_tick_frequency')
            
            # Spread monitoring
            for symbol, spread in self.market_metrics.get('spreads', {}).items():
                if spread > self.market_metrics.get('max_spread', 0.1):
                    logger.warning(f"Wide spread detected for {symbol}: {spread}")
                    self.trading_state.set_warning('wide_spread')
            
        except Exception as e:
            logger.error(f"Error checking market conditions: {str(e)}")
            self.error_counts['data_errors'] += 1
    
    async def _check_trading_safety(self):
        """Check trading safety conditions."""
        try:
            # Check margin usage
            margin_used = self.market_metrics.get('margin_used', 0)
            if margin_used > MONITORING_THRESHOLDS['margin_critical']:
                logger.critical(f"Critical margin usage: {margin_used}%")
                await self._trigger_emergency_stop()
            elif margin_used > MONITORING_THRESHOLDS['margin_warning']:
                logger.warning(f"High margin usage: {margin_used}%")
                self.trading_state.set_warning('high_margin_usage')
            
            # Check trade frequency
            trades_last_hour = len([
                t for t in self.market_metrics.get('recent_trades', [])
                if t['timestamp'] > time.time() - 3600
            ])
            if trades_last_hour > RISK_LIMITS['max_trades_per_hour']:
                logger.warning(f"High trade frequency: {trades_last_hour} trades/hour")
                self.trading_state.set_warning('high_trade_frequency')
            
            # Check for rapid consecutive orders
            for symbol, last_order_time in self.last_order_times.items():
                if time.time() - last_order_time < RISK_LIMITS['min_time_between_trades']:
                    logger.warning(f"Rapid orders detected for {symbol}")
                    self.trading_state.set_warning('rapid_orders')
            
        except Exception as e:
            logger.error(f"Error checking trading safety: {str(e)}")
            self.error_counts['system_errors'] += 1
    
    async def _manage_recovery_mode(self):
        """Manage recovery mode based on performance."""
        try:
            daily_pnl = self.market_metrics.get('daily_pnl', 0)
            
            # Check if we should enter recovery mode
            if not self.recovery_mode and daily_pnl < RECOVERY_SETTINGS['activation_threshold']:
                logger.warning("Entering recovery mode due to losses")
                self.recovery_mode = True
                self.trading_state.set_warning('recovery_mode')
            
            # Check if we can exit recovery mode
            if self.recovery_mode:
                recent_trades = self.market_metrics.get('recent_trades', [])
                if len(recent_trades) >= RECOVERY_SETTINGS['min_trades']:
                    win_rate = sum(1 for t in recent_trades if t['pnl'] > 0) / len(recent_trades)
                    if win_rate >= RECOVERY_SETTINGS['min_win_rate']:
                        logger.info("Exiting recovery mode - performance improved")
                        self.recovery_mode = False
                        self.trading_state.clear_warning('recovery_mode')
            
        except Exception as e:
            logger.error(f"Error managing recovery mode: {str(e)}")
    
    async def _manage_circuit_breakers(self):
        """Manage circuit breaker levels based on drawdown."""
        try:
            current_drawdown = self.market_metrics.get('current_drawdown', 0)
            
            # Check circuit breaker levels
            for level, settings in CIRCUIT_BREAKERS.items():
                if current_drawdown <= -settings['drawdown']:
                    if self.circuit_breaker_level < int(level[-1]):
                        logger.warning(f"Circuit breaker {level} triggered")
                        self.circuit_breaker_level = int(level[-1])
                        await self._apply_circuit_breaker(settings)
            
            # Check if we can remove circuit breaker
            if self.circuit_breaker_level > 0:
                if current_drawdown > -CIRCUIT_BREAKERS[f'level_{self.circuit_breaker_level}']['drawdown']:
                    logger.info("Removing circuit breaker - drawdown improved")
                    self.circuit_breaker_level -= 1
            
        except Exception as e:
            logger.error(f"Error managing circuit breakers: {str(e)}")
    
    async def _apply_circuit_breaker(self, settings: Dict):
        """Apply circuit breaker actions."""
        try:
            action = settings['action']
            if action == 'stop_trading':
                await self._trigger_emergency_stop()
            elif action == 'reduce_size':
                self.trading_state.set_position_size_factor(settings['reduction_factor'])
            elif action == 'hedge_only':
                self.trading_state.set_trading_mode('hedge_only')
            
            # Set cooldown period if specified
            if 'cooldown_minutes' in settings:
                self.trading_state.set_cooldown(timedelta(minutes=settings['cooldown_minutes']))
            
        except Exception as e:
            logger.error(f"Error applying circuit breaker: {str(e)}")
    
    async def _trigger_emergency_stop(self):
        """Emergency stop all trading activity."""
        try:
            logger.critical("EMERGENCY STOP TRIGGERED")
            self.trading_state.disable_trading()
            self.trading_state.set_emergency_stop()
            
            # Additional emergency actions can be added here
            
        except Exception as e:
            logger.error(f"Error in emergency stop: {str(e)}")
    
    def update_order_latency(self, latency_ms: float):
        """Update order latency metrics."""
        self.order_latencies.append(latency_ms)
        if len(self.order_latencies) > 1000:
            self.order_latencies = self.order_latencies[-1000:]
    
    def update_quote_latency(self, latency_ms: float):
        """Update quote latency metrics."""
        self.quote_latencies.append(latency_ms)
        if len(self.quote_latencies) > 1000:
            self.quote_latencies = self.quote_latencies[-1000:]
    
    def update_market_metrics(self, metrics: Dict):
        """Update market metrics."""
        self.market_metrics.update(metrics)
    
    def record_order_time(self, symbol: str):
        """Record the time of the last order for a symbol."""
        self.last_order_times[symbol] = time.time()
    
    def record_error(self, error_type: str):
        """Record an error occurrence."""
        if error_type in self.error_counts:
            self.error_counts[error_type] += 1
    
    def get_system_status(self) -> Dict:
        """Get current system status and metrics."""
        return {
            'system_metrics': self.system_metrics,
            'market_metrics': self.market_metrics,
            'error_counts': self.error_counts,
            'recovery_mode': self.recovery_mode,
            'circuit_breaker_level': self.circuit_breaker_level,
            'warnings': self.trading_state.get_warnings()
        }
