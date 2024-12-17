
import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional
import json
from pathlib import Path

class LogFormatter(logging.Formatter):
    """Custom formatter for OConsent logs."""
    
    def format(self, record):
        """Formats log records in a structured way."""
        # Get basic record attributes
        data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            data['exception'] = self.formatException(record.exc_info)
        
        # Add custom fields from record
        for key, value in record.__dict__.items():
            if key.startswith('oconsent_'):
                data[key[9:]] = value
        
        return json.dumps(data)

def setup_logging(
    log_dir: Optional[str] = None,
    log_level: int = logging.INFO,
    max_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """Sets up logging for OConsent."""
    logger = logging.getLogger('oconsent')
    logger.setLevel(log_level)
    
    # Clear any existing handlers
    logger.handlers = []
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(LogFormatter())
    logger.addHandler(console_handler)
    
    # Create file handler if log_dir is specified
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create rotating file handler
        log_file = log_dir / f"oconsent_{datetime.now():%Y%m%d}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_size,
            backupCount=backup_count
        )
        file_handler.setFormatter(LogFormatter())
        logger.addHandler(file_handler)
    
    return logger

class LogContext:
    """Context manager for adding context to logs."""
    
    def __init__(self, logger: logging.Logger, **context):
        self.logger = logger
        self.context = context
        self.old_context = {}
    
    def __enter__(self):
        # Store old context and set new context
        for key, value in self.context.items():
            context_key = f'oconsent_{key}'
            if hasattr(self.logger, context_key):
                self.old_context[context_key] = getattr(self.logger, context_key)
            setattr(self.logger, context_key, value)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore old context
        for key in self.context.keys():
            context_key = f'oconsent_{key}'
            if context_key in self.old_context:
                setattr(self.logger, context_key, self.old_context[context_key])
            else:
                delattr(self.logger, context_key)
                