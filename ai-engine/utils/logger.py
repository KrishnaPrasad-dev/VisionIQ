import logging
import sys
from pathlib import Path
from datetime import datetime


AI_ENGINE_ROOT = Path(__file__).resolve().parent.parent


def setup_logger(name="VisionIQ", log_dir="logs"):
    """
    Setup logger with console and file output
    
    Args:
        name: Logger name
        log_dir: Directory to save log files
    
    Returns:
        Configured logger instance
    """
    # Create logs directory
    log_path = (AI_ENGINE_ROOT / log_dir).resolve()
    log_path.mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Log format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler - INFO and above
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler - DEBUG and above
    log_filename = log_path / f"visioniq_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


def get_logger(name="VisionIQ"):
    """Get existing logger"""
    return logging.getLogger(name)
