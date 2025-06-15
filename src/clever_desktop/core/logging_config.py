"""
Logging Configuration

Advanced logging setup with file rotation, configurable levels,
and proper formatting for debugging and production use.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

from .settings import AppSettings


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}"
                f"{self.COLORS['RESET']}"
            )
        
        return super().format(record)


def setup_logging(log_file: Optional[Path] = None) -> None:
    """
    Setup comprehensive logging configuration.
    
    Args:
        log_file: Path to log file. If None, uses default location.
    """
    settings = AppSettings()
    
    # Get log level from settings
    log_level_str = settings.get_log_level()
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s | %(name)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    colored_formatter = ColoredFormatter(
        fmt='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Setup file logging
    if settings.is_file_logging_enabled() and log_file:
        try:
            # Create log directory if it doesn't exist
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                filename=log_file,
                maxBytes=settings.get_max_log_size_mb() * 1024 * 1024,  # Convert MB to bytes
                backupCount=settings.get_max_log_files(),
                encoding='utf-8'
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(detailed_formatter)
            root_logger.addHandler(file_handler)
            
            # Log the logging setup
            logging.info(f"File logging enabled: {log_file}")
            
        except Exception as e:
            # Fallback to console logging if file logging fails
            print(f"Failed to setup file logging: {e}", file=sys.stderr)
    
    # Setup console logging
    if settings.is_console_logging_enabled():
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        # Use colored formatter for console in development
        if sys.stdout.isatty():  # Terminal supports colors
            console_handler.setFormatter(colored_formatter)
        else:
            console_handler.setFormatter(simple_formatter)
        
        root_logger.addHandler(console_handler)
    
    # Setup application-specific loggers
    setup_application_loggers(log_level)
    
    # Log startup information
    logger = logging.getLogger(__name__)
    logger.info("="*50)
    logger.info("Clever Cloud Desktop Manager - Logging Initialized")
    logger.info(f"Log Level: {log_level_str}")
    logger.info(f"File Logging: {'Enabled' if settings.is_file_logging_enabled() else 'Disabled'}")
    logger.info(f"Console Logging: {'Enabled' if settings.is_console_logging_enabled() else 'Disabled'}")
    if log_file:
        logger.info(f"Log File: {log_file}")
    logger.info("="*50)


def setup_application_loggers(log_level: int) -> None:
    """Setup specific loggers for different application components."""
    
    # Application loggers with appropriate levels
    loggers_config = {
        'clever_desktop.core': log_level,
        'clever_desktop.api': log_level,
        'clever_desktop.ui': log_level,
        'clever_desktop.models': log_level,
        'clever_desktop.utils': log_level,
        
        # External libraries - usually less verbose
        'httpx': max(log_level, logging.WARNING),
        'urllib3': max(log_level, logging.WARNING),
        'requests': max(log_level, logging.WARNING),
        'websockets': max(log_level, logging.INFO),
        'git': max(log_level, logging.INFO),
        'PySide6': max(log_level, logging.WARNING),
    }
    
    for logger_name, level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)


def log_exception(logger: logging.Logger, message: str, exc_info: bool = True) -> None:
    """Log an exception with full traceback."""
    logger.error(message, exc_info=exc_info)


def log_performance(logger: logging.Logger, operation: str, duration: float) -> None:
    """Log performance metrics."""
    logger.info(f"Performance | {operation} | {duration:.3f}s")


def log_api_call(logger: logging.Logger, method: str, url: str, status_code: int, duration: float) -> None:
    """Log API call details."""
    logger.info(f"API | {method} {url} | {status_code} | {duration:.3f}s")


def log_user_action(logger: logging.Logger, action: str, details: str = "") -> None:
    """Log user actions for debugging."""
    logger.info(f"User Action | {action} | {details}")


class LogContext:
    """Context manager for logging operations with timing."""
    
    def __init__(self, logger: logging.Logger, operation: str):
        self.logger = logger
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        self.logger.debug(f"Starting {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        duration = time.time() - self.start_time
        
        if exc_type is None:
            self.logger.debug(f"Completed {self.operation} in {duration:.3f}s")
        else:
            self.logger.error(f"Failed {self.operation} after {duration:.3f}s: {exc_val}")
        
        return False  # Don't suppress exceptions


def configure_qt_logging() -> None:
    """Configure Qt logging to integrate with Python logging."""
    try:
        from PySide6.QtCore import qInstallMessageHandler, QtMsgType
        
        def qt_message_handler(msg_type, context, message):
            """Handle Qt log messages."""
            logger = logging.getLogger('PySide6')
            
            if msg_type == QtMsgType.QtDebugMsg:
                logger.debug(message)
            elif msg_type == QtMsgType.QtInfoMsg:
                logger.info(message)
            elif msg_type == QtMsgType.QtWarningMsg:
                logger.warning(message)
            elif msg_type == QtMsgType.QtCriticalMsg:
                logger.error(message)
            elif msg_type == QtMsgType.QtFatalMsg:
                logger.critical(message)
        
        qInstallMessageHandler(qt_message_handler)
        
    except ImportError:
        # PySide6 not available, skip Qt logging setup
        pass


def setup_crash_logging(log_file: Path) -> None:
    """Setup crash logging for unhandled exceptions."""
    def handle_exception(exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions."""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger = logging.getLogger('crash')
        logger.critical(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
    
    sys.excepthook = handle_exception 