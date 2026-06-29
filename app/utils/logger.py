# app/utils/logger.py
# ============================================================
# Centralized logging setup for the entire application
# Using Python's built-in logging module (no extra dependencies)
# ============================================================

import logging
import sys
from app.utils.config import get_settings

settings = get_settings()


def get_logger(name: str) -> logging.Logger:
    """
    Create and return a logger with consistent formatting.

    Usage:
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Something happened")
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if the logger already exists
    if logger.handlers:
        return logger

    # Set log level from settings
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Console handler — outputs to stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    # Format: timestamp | level | module | message
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
