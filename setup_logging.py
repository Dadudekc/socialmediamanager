import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler


def setup_logging(
    script_name: str,
    log_dir: str | Path | None = None,
    max_log_size: int = 5 * 1024 * 1024,
    backup_count: int = 3,
    console_log_level: int = logging.INFO,
    file_log_level: int = logging.DEBUG,
) -> logging.Logger:
    """Configure and return a logger with console and rotating file handlers.

    Parameters
    ----------
    script_name: str
        Name used for the logger and log file.
    log_dir: str | Path | None
        Directory to store logs. Created if it doesn't exist. If ``None`` a
        ``logs/Utilities`` directory relative to this file is used.
    max_log_size: int
        Maximum size in bytes before the log file is rotated (default 5MB).
    backup_count: int
        Number of rotated files to keep.
    console_log_level: int
        Logging level for console output.
    file_log_level: int
        Logging level for file output.
    """
    logger = logging.getLogger(script_name)
    logger.setLevel(logging.DEBUG)

    # Clear existing handlers to avoid duplicate logs when called multiple times
    logger.handlers = []

    # Determine log directory
    if log_dir is None:
        project_root = Path(__file__).resolve().parent
        log_dir = project_root / "logs" / "Utilities"
    else:
        log_dir = Path(log_dir)

    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{script_name}.log"

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    try:
        file_handler = RotatingFileHandler(
            str(log_file), maxBytes=max_log_size, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setLevel(file_log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:  # pragma: no cover - handler errors are non-critical
        logger.warning(f"Error setting up file handler: {e}")

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

__all__ = ["setup_logging"]
