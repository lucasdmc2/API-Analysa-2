"""
Structured logging configuration using structlog
"""

import logging
import sys
from typing import Any, Dict

import structlog
from src.core.config import settings


def configure_logging() -> None:
    """Configure structured logging for the application"""
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            # Add correlation ID to all log entries
            add_correlation_id,
            # Add timestamp
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            # JSON formatting for production, key-value for development
            structlog.processors.JSONRenderer()
            if settings.STRUCTURED_LOGGING
            else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def add_correlation_id(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add correlation ID to log entries"""
    # Try to get correlation ID from context
    # This would be set by middleware or background tasks
    try:
        import contextvars
        correlation_id = contextvars.ContextVar('correlation_id', default=None).get()
        if correlation_id:
            event_dict['correlation_id'] = correlation_id
    except Exception:
        # Fallback - correlation ID will be added by middleware
        pass
    
    return event_dict