"""
Logging utilities for Maya Control Plane

Provides structured logging configuration and utilities.
"""

import structlog
import logging
from typing import Optional


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (optional)
        
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


def configure_logging(level: str = "INFO", json_format: bool = True):
    """
    Configure structured logging for the application.
    
    Args:
        level: Logging level
        json_format: Whether to use JSON format
    """
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    if json_format:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Set standard library logging level
    logging.basicConfig(level=getattr(logging, level.upper()))