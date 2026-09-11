"""
Logging configuration for Job Pulse
"""
from loguru import logger
import sys


def setup_logging(log_level: str = "INFO"):
    """Configure Loguru logger."""
    # Remove default handler
    logger.remove()
    
    # Add console handler with pretty formatting
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )
    
    # Add file handler for errors
    logger.add(
        "logs/error_{time:YYYY-MM-DD}.log",
        level="ERROR",
        rotation="1 day",
        retention="7 days",
    )
    
    return logger
