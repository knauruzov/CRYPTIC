"""
Logging utility for DFIR CRYPTIC.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from ..config.settings import DATA_DIR, DEBUG

# Create logs directory
LOGS_DIR = DATA_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

def setup_logger(name=None, log_file=None, level=None):
    """
    Set up logger with file and console handlers.
    
    Args:
        name (str, optional): Logger name. Defaults to 'dfir_cryptic'.
        log_file (str, optional): Log file path. Defaults to 'dfir_cryptic.log'.
        level (int, optional): Logging level. Defaults to DEBUG if debug mode is on, else INFO.
        
    Returns:
        logging.Logger: Configured logger instance.
    """
    name = name or 'dfir_cryptic'
    
    if level is None:
        level = logging.DEBUG if DEBUG else logging.INFO
        
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers if any
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatters
    fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    datefmt = '%Y-%m-%d %H:%M:%S'
    
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
    
    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)
    
    # Set up file handler if log_file is provided
    if log_file:
        if not isinstance(log_file, Path):
            log_file = LOGS_DIR / log_file
            
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
    
    return logger

# Set up the root logger
root_logger = setup_logger(log_file='dfir_cryptic.log')

# Add a null handler to the package logger
logging.getLogger('dfir_cryptic').addHandler(logging.NullHandler()) 