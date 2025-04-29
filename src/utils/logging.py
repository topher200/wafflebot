import logging
import sys
from pathlib import Path


def setup_logger(name: str, log_level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with consistent formatting and output.

    Args:
        name: The name of the logger (typically __name__)
        log_level: The logging level (default: INFO)

    Returns:
        A configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Create handlers
    console_handler = logging.StreamHandler(sys.stdout)

    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    file_handler = logging.FileHandler(logs_dir / f"{name}.log")

    # Create formatters and add it to handlers
    log_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(log_format)
    file_handler.setFormatter(log_format)

    # Add handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
