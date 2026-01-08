import logging
import os
from datetime import datetime

def setup_logger(name="AI_Trader", log_file="bot.log", level=logging.INFO):
    """
    Sets up a logger that writes to both console and a file.
    
    Args:
        name (str): The name of the logger.
        log_file (str): The file path to write logs to.
        level (int): The logging level (e.g., logging.INFO, logging.DEBUG).
        
    Returns:
        logging.Logger: The configured logger object.
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Check if handlers are already added to avoid duplicate logs
    if logger.hasHandlers():
        return logger

    # Create formatters
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Failed to create log file: {e}")

    return logger
