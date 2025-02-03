import logging
from logging.handlers import RotatingFileHandler
import os
from .settings import AppConfig

def setup_logger():
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)

    # Configure logger
    logger = logging.getLogger(AppConfig.NAME)
    logger.setLevel(logging.INFO)

    # File handler
    file_handler = RotatingFileHandler(
        AppConfig.LOG_FILE,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=5
    )
    
    # Console handler
    console_handler = logging.StreamHandler()

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger