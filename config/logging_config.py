"""
Logging configuration for the Ultimate Follow Builder.

Centralized logging setup for all system components.
"""

import logging
import logging.handlers
import os
from pathlib import Path

def setup_logging(
    log_level: str = "INFO",
    log_file: str = "data/logs/ultimate_follow_builder.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    Setup logging configuration for the Ultimate Follow Builder.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup log files to keep
    """
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Set up root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        datefmt=date_format,
        handlers=[
            # Console handler
            logging.StreamHandler(),
            # File handler with rotation
            logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
        ]
    )
    
    # Set specific loggers
    loggers = [
        "ultimate_follow_builder",
        "follow_automation", 
        "engagement_automation",
        "growth_engine",
        "ai_content_generator",
        "web_dashboard"
    ]
    
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, log_level.upper()))
    
    # Log startup message
    logging.info("🚀 Ultimate Follow Builder logging system initialized")
    logging.info(f"📁 Log file: {log_file}")
    logging.info(f"📊 Log level: {log_level.upper()}")

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific component.
    
    Args:
        name: Logger name (usually module name)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name) 