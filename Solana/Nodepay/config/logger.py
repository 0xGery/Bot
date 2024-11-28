import logging
from logging.handlers import RotatingFileHandler
import os
from .settings import AppConfig

def setup_logger():
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)

    # Configure logger
    logger = logging.getLogger(AppConfig.NAME)
    logger.setLevel(logging.DEBUG)

    # File handler with detailed formatting
    file_handler = RotatingFileHandler(
        AppConfig.LOG_FILE,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler with less detailed formatting
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Detailed formatter for file
    file_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Simple formatter for console
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Log system startup information
    logger.info("=" * 50)
    logger.info(f"Starting {AppConfig.NAME} v{AppConfig.VERSION}")
    logger.info(f"Author: {AppConfig.AUTHOR}")
    logger.info("=" * 50)
    
    # Log configuration details
    logger.debug(f"Base URL: {AppConfig.BASE_URL}")
    logger.debug(f"Session URL: {AppConfig.SESSION_URL}")
    logger.debug(f"Retry Interval: {AppConfig.RETRY_INTERVAL}")
    logger.debug(f"Dashboard Update Interval: {AppConfig.DASHBOARD_UPDATE_INTERVAL}")
    logger.debug("Ping URLs:")
    for url in AppConfig.PING_URLS:
        logger.debug(f"  - {url}")
    logger.debug("=" * 50)

    return logger
