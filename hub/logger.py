"""
Maya Control Plane Logging System

Centralized logging configuration and utilities for the Maya control plane.
Supports structured logging with JSON output and multiple log levels.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import structlog
from datetime import datetime


class MayaLogger:
    """
    Centralized logging system for Maya Control Plane
    
    Features:
    - Structured logging with JSON output
    - Multiple log levels and handlers
    - File rotation and size management
    - Context-aware logging for requests
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.log_level = self.config.get('level', 'INFO')
        self.log_format = self.config.get('format', 'json')
        self.log_file = self.config.get('file', 'logs/maya.log')
        self.max_size = self.config.get('max_size', '10MB')
        self.backup_count = self.config.get('backup_count', 5)
        
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure structured logging with appropriate handlers"""
        
        # Ensure log directory exists
        log_path = Path(self.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure structlog processors
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
        
        if self.log_format == 'json':
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
        
        # Configure standard library logging
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=getattr(logging, self.log_level.upper())
        )
        
        # Add file handler with rotation
        if self.log_file:
            file_handler = logging.handlers.RotatingFileHandler(
                self.log_file,
                maxBytes=self._parse_size(self.max_size),
                backupCount=self.backup_count
            )
            file_handler.setLevel(getattr(logging, self.log_level.upper()))
            
            root_logger = logging.getLogger()
            root_logger.addHandler(file_handler)
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string like '10MB' to bytes"""
        size_str = size_str.upper()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    def get_logger(self, name: str) -> structlog.BoundLogger:
        """Get a structured logger instance"""
        return structlog.get_logger(name)
    
    def create_request_logger(self, request_id: str, **context) -> structlog.BoundLogger:
        """Create a logger with request context"""
        logger = structlog.get_logger()
        return logger.bind(request_id=request_id, **context)


# Global logger instance
_maya_logger = None


def get_maya_logger(config: Optional[Dict[str, Any]] = None) -> MayaLogger:
    """Get or create the global Maya logger instance"""
    global _maya_logger
    if _maya_logger is None:
        _maya_logger = MayaLogger(config)
    return _maya_logger


def get_logger(name: str) -> structlog.BoundLogger:
    """Convenience function to get a structured logger"""
    maya_logger = get_maya_logger()
    return maya_logger.get_logger(name)


# Pre-configured loggers for common components
orchestrator_logger = get_logger("orchestrator")
adapter_logger = get_logger("adapter")
helper_logger = get_logger("helper")
api_logger = get_logger("api")
campaign_logger = get_logger("campaign")