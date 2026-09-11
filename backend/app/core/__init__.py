"""
Core module initialization
"""
from app.core.config import settings
from app.core.logging import setup_logging

# Initialize logging
logger = setup_logging(settings.log_level)

__all__ = ["settings", "logger"]
