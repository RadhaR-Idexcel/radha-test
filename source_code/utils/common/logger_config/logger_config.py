"""
Centralized logger configuration for AWS Lambda.
"""
import logging
import os
import sys

_CONFIGURED = False
def get_logger(name: str = "app") -> logging.Logger:
    """Get a logger instance. Configures logging on first call."""
    global _CONFIGURED # pylint: disable=global-statement
    if not _CONFIGURED:
        log_level = (
            os.getenv("AWS_LAMBDA_LOG_LEVEL")
            or os.getenv("LOG_LEVEL")
            or "INFO"
        ).upper()
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level, logging.INFO))
        # AWS Lambda provides handlers automatically
        if not os.getenv("AWS_EXECUTION_ENV", "").startswith("AWS_Lambda"):
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter(
                "%(asctime)s - %(levelname)-8s - %(name)s - %(message)s",
                "%Y-%m-%d %H:%M:%S"
            ))
            root_logger.addHandler(handler)
        _CONFIGURED = True
    return logging.getLogger(name)
