"""
Centralized logging configuration.

Sets up structured logging with a consistent format across all
modules. Each module creates its own named logger via
logging.getLogger(__name__), so log messages always show which
component produced them.

Log level can be changed in one place here, affecting the entire
application. In production, level can be raised to WARNING to
silence the detailed retrieval/tool/embedding messages while
keeping error visibility.
"""

import logging
import os

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.environ.get("LOG_FILE", None)


def setup_logging():
    """
    Configures the root logger with a structured format.
    Call this once at application startup (in main.py).
    """
    handlers = [logging.StreamHandler()]

    if LOG_FILE:
        handlers.append(logging.FileHandler(LOG_FILE, encoding="utf-8"))

    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers
    )
