"""Centralized Logging Configuration"""

import logging
import sys

LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | "
    "%(name)s | %(message)s"
)


def configure_logging(level: int = logging.INFO) -> None:
    """
    Configure application logging safely for a Jupyter Notebook.
    Clears old handlers so you can re-run this function anytime.
    """
    root_logger = logging.getLogger()

    # Remove existing handlers in notebook kernel
    if root_logger.handlers:
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

    # Force reconfiguration with the correct stream for notebook output
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt="%H:%M:%S",   # Clean Timestamps
        stream=sys.stdout     # Forces logs to render beautifully in notebooks
    )


def get_logger(name: str) -> logging.Logger:
    """
    Create a named logger.
    """
    return logging.getLogger(name)
