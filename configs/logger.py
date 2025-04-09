import logging
import sys

log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter(log_format))

logger = logging.getLogger()

logger.setLevel(logging.INFO)

# Remove existing handlers to avoid duplicate logs
if logger.hasHandlers():
    logger.handlers.clear()

# Add the console handler to the root logger
logger.addHandler(console_handler)

# Example of how to get a specific logger in other modules


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


print("Logger configured.")
