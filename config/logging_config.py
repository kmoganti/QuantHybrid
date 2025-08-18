"""
Logging configuration for QuantHybrid trading system.
Includes advanced features like JSON logging, error monitoring, and log rotation.
"""
import logging
import logging.handlers
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import os
from config.settings import LOG_DIR, LOG_LEVEL, LOG_FORMAT

# Error patterns to monitor
ERROR_PATTERNS = {
    'connection_error': r'Connection .* failed',
    'timeout_error': r'Timeout .*',
    'api_error': r'API .* error',
    'data_error': r'Invalid data .*',
    'system_error': r'System .*'
}

# Monitoring settings
LOG_MONITORING = {
    'error_alert_threshold': 10,  # Alert after 10 errors in 5 minutes
    'monitoring_interval': 300,  # 5 minutes
    'alert_channels': ['email', 'slack']
}

class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    def format(self, record):
        log_obj = {
            'timestamp': self.formatTime(record),
            'name': record.name,
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'line': record.lineno
        }
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

def setup_logger(name: str, log_file: str, level: str = LOG_LEVEL, enable_json: bool = True) -> logging.Logger:
    """
    Sets up a logger with file, JSON, and stream handlers.
    
    Args:
        name (str): Name of the logger
        log_file (str): Path to the log file
        level (str): Logging level
        enable_json (bool): Enable JSON formatted logging
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create formatters
    standard_formatter = logging.Formatter(LOG_FORMAT)
    json_formatter = JsonFormatter()
    
    # Create standard log handler
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_DIR / log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(standard_formatter)
    
    # Create JSON log handler if enabled
    if enable_json:
        json_handler = logging.handlers.RotatingFileHandler(
            LOG_DIR / f'{log_file}.json',
            maxBytes=10*1024*1024,
            backupCount=5
        )
        json_handler.setFormatter(json_formatter)
    
    # Create error log handler
    error_handler = logging.handlers.RotatingFileHandler(
        LOG_DIR / f'error_{log_file}',
        maxBytes=10*1024*1024,
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(standard_formatter)
    
    # Create console handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(standard_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    logger.addHandler(stream_handler)
    if enable_json:
        logger.addHandler(json_handler)
    
    return logger

# Create loggers for different components
LOGGERS: Dict[str, logging.Logger] = {
    'system': setup_logger('system', 'system.log'),
    'trading': setup_logger('trading', 'trading.log'),
    'risk': setup_logger('risk', 'risk.log'),
    'performance': setup_logger('performance', 'performance.log'),
    'api': setup_logger('api', 'api.log'),
    'ml': setup_logger('ml', 'ml.log'),
    'web': setup_logger('web', 'web.log')
}

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger by name.
    
    Args:
        name (str): Name of the logger
    
    Returns:
        logging.Logger: The requested logger
    """
    return LOGGERS.get(name, LOGGERS['system'])

def cleanup_old_logs(days: int = 30) -> None:
    """
    Clean up log files older than specified days.
    
    Args:
        days (int): Number of days to keep logs
    """
    cutoff = datetime.now() - timedelta(days=days)
    
    for file in os.listdir(LOG_DIR):
        if file.endswith(('.log', '.json')):
            file_path = LOG_DIR / file
            if datetime.fromtimestamp(os.path.getmtime(file_path)) < cutoff:
                os.remove(file_path)

def parse_error_logs(log_file: str, pattern: Optional[str] = None) -> list:
    """
    Parse error logs for specific patterns.
    
    Args:
        log_file (str): Path to log file
        pattern (str, optional): Regex pattern to match
    
    Returns:
        list: Matching log entries
    """
    import re
    matches = []
    
    with open(LOG_DIR / log_file, 'r') as f:
        for line in f:
            if pattern and re.search(pattern, line):
                matches.append(line.strip())
            elif pattern is None and '[ERROR]' in line:
                matches.append(line.strip())
    
    return matches

def monitor_errors(logger_name: str, interval: int = 300) -> Dict[str, int]:
    """
    Monitor error frequency for a specific logger.
    
    Args:
        logger_name (str): Name of the logger to monitor
        interval (int): Time interval in seconds
    
    Returns:
        Dict[str, int]: Error counts by pattern
    """
    error_counts = {pattern: 0 for pattern in ERROR_PATTERNS}
    log_file = f'error_{logger_name}.log'
    
    for pattern_name, pattern in ERROR_PATTERNS.items():
        matches = parse_error_logs(log_file, pattern)
        error_counts[pattern_name] = len(matches)
    
    return error_counts

# Create logging directories if they don't exist
LOG_DIR.mkdir(exist_ok=True)

# Example usage:
# logger = get_logger('trading')
# logger.info('Trading system initialized')
# error_counts = monitor_errors('trading')
# cleanup_old_logs(days=30)
