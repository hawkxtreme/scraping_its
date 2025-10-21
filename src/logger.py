import os
import sys
import logging
import traceback
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Formatter that adds colors to console output."""
    
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
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


class ScraperLogger:
    """
    Enhanced logging system with multiple handlers and log levels.
    
    Features:
    - Standard Python logging module
    - Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - Rotating file handlers
    - Separate error log file
    - Thread-safe operations
    - Colored console output
    - Context-aware error messages
    """
    
    def __init__(self, output_dir: str, verbose: bool = False, name: str = "scraper", console_output: bool = True):
        """
        Initialize the logger.
        
        Args:
            output_dir (str): Directory where log files will be saved
            verbose (bool): Enable verbose (DEBUG) mode
            name (str): Logger name (should be unique for each logger instance)
            console_output (bool): Enable console output (disable when using tqdm)
        """
        self.output_dir = output_dir
        self.verbose = verbose
        self.name = name
        self.console_output = console_output
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Make logger name unique by adding output_dir hash
        unique_name = f"{name}_{abs(hash(output_dir)) % 10000}"
        
        # Initialize logger
        self.logger = logging.getLogger(unique_name)
        self.logger.setLevel(logging.DEBUG if verbose else logging.INFO)
        
        # Remove existing handlers if any
        self.logger.handlers.clear()
        
        # Prevent propagation to avoid duplicate logs
        self.logger.propagate = False
        
        # Setup handlers
        self._setup_file_handler()
        self._setup_error_handler()
        if console_output:
            self._setup_console_handler()
        
        # Log startup message
        self.info("=" * 70)
        self.info(f"Logging system initialized at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.info(f"Log directory: {output_dir}")
        self.info(f"Verbose mode: {'ON' if verbose else 'OFF'}")
        self.info("=" * 70)
    
    def _setup_file_handler(self):
        """Setup rotating file handler for main log."""
        log_file = os.path.join(self.output_dir, "script_log.txt")
        
        # Create rotating file handler (max 10MB, keep 5 backups)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Format: [2025-10-21 15:30:45] [INFO] [scraper] Message
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
    
    def _setup_error_handler(self):
        """Setup separate error log file for ERROR and CRITICAL messages."""
        error_log_file = os.path.join(self.output_dir, "errors.log")
        
        # Create rotating file handler for errors
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=5*1024*1024,  # 5 MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        
        # More detailed format for error log
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] [%(filename)s:%(lineno)d]\n'
            'Message: %(message)s\n'
            '%(stack_info)s\n',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        error_handler.setFormatter(formatter)
        
        self.logger.addHandler(error_handler)
    
    def _setup_console_handler(self):
        """Setup console handler with colored output."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG if self.verbose else logging.INFO)
        
        # Use colored formatter for console
        if sys.platform == 'win32':
            # Enable ANSI colors on Windows
            try:
                import colorama
                colorama.init()
            except ImportError:
                pass  # Colors won't work but logging will
        
        formatter = ColoredFormatter(
            '[%(levelname)s] %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
    
    def debug(self, message: str, **context):
        """Log DEBUG level message."""
        self.logger.debug(self._format_message(message, context))
    
    def info(self, message: str, **context):
        """Log INFO level message."""
        self.logger.info(self._format_message(message, context))
    
    def warning(self, message: str, **context):
        """Log WARNING level message."""
        self.logger.warning(self._format_message(message, context))
    
    def error(self, message: str, exc_info: bool = False, **context):
        """
        Log ERROR level message.
        
        Args:
            message: Error message
            exc_info: Include exception traceback
            **context: Additional context information
        """
        formatted_message = self._format_message(message, context)
        self.logger.error(formatted_message, exc_info=exc_info)
    
    def critical(self, message: str, exc_info: bool = True, **context):
        """
        Log CRITICAL level message.
        
        Args:
            message: Critical error message
            exc_info: Include exception traceback (default True)
            **context: Additional context information
        """
        formatted_message = self._format_message(message, context)
        self.logger.critical(formatted_message, exc_info=exc_info)
    
    def exception(self, message: str, **context):
        """Log exception with full traceback."""
        formatted_message = self._format_message(message, context)
        self.logger.exception(formatted_message)
    
    def _format_message(self, message: str, context: dict) -> str:
        """
        Format message with context information.
        
        Args:
            message: Main message
            context: Dictionary with context info (url, article_title, operation, etc.)
        
        Returns:
            Formatted message string
        """
        if not context:
            return message
        
        context_parts = []
        for key, value in context.items():
            context_parts.append(f"{key}={value}")
        
        context_str = " | ".join(context_parts)
        return f"{message} [{context_str}]"
    
    def log_error_with_context(self, error: Exception, operation: str, **context):
        """
        Log error with full context and suggestions.
        
        Args:
            error: The exception object
            operation: What operation was being performed
            **context: Additional context (url, article_title, etc.)
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        # Build detailed error message
        message = f"Error during {operation}: {error_type}: {error_message}"
        
        # Add context
        context['operation'] = operation
        context['error_type'] = error_type
        
        # Log the error
        self.error(message, exc_info=True, **context)
        
        # Add helpful suggestions based on error type
        suggestion = self._get_error_suggestion(error_type, error_message)
        if suggestion:
            self.warning(f"Suggestion: {suggestion}")
    
    def _get_error_suggestion(self, error_type: str, error_message: str) -> Optional[str]:
        """
        Get helpful suggestion based on error type.

    Args:
            error_type: Type of the error
            error_message: Error message

    Returns:
            Suggestion string or None
        """
        error_message_lower = error_message.lower()
        
        # Timeout errors
        if 'timeout' in error_message_lower or error_type == 'TimeoutError':
            return "Try increasing timeout with --timeout flag or check network connection"
        
        # Connection errors
        if 'connection' in error_message_lower or 'connect' in error_message_lower:
            return "Check if browserless service is running: docker ps | grep browserless"
        
        # Authentication errors
        if 'login' in error_message_lower or 'auth' in error_message_lower:
            return "Verify credentials in .env file (LOGIN_1C_USER, LOGIN_1C_PASSWORD)"
        
        # Browser closed errors
        if 'browser' in error_message_lower and 'closed' in error_message_lower:
            return "Browser connection lost. The scraper will attempt to reconnect automatically"
        
        # Parsing errors
        if 'parse' in error_message_lower or error_type == 'ValueError':
            return "Content structure may have changed. Check parser_v1.py or parser_v2.py"
        
        # File errors
        if 'file' in error_message_lower or error_type in ['FileNotFoundError', 'PermissionError']:
            return "Check file permissions and available disk space"
        
        return None
    
    def log_statistics(self, stats: dict):
        """
        Log statistics in a formatted way.
        
        Args:
            stats: Dictionary with statistics
        """
        self.info("=" * 70)
        self.info("STATISTICS")
        self.info("=" * 70)
        for key, value in stats.items():
            self.info(f"  {key}: {value}")
        self.info("=" * 70)
    
    def __call__(self, message: str):
        """
        Make logger callable for backward compatibility.
        Delegates to info() method.
        """
        self.info(message)
    
    def close(self):
        """Close all handlers to release file locks."""
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)


def setup_logger(output_dir: str, verbose: bool = False, console_output: bool = True) -> ScraperLogger:
    """
    Setup and return a configured logger instance.
    
    This is the main function to initialize logging for the scraper.
    
    Args:
        output_dir (str): Directory where log files will be saved
        verbose (bool): Enable verbose (DEBUG) logging
        console_output (bool): Enable console output (set False when using tqdm progress bar)
    
    Returns:
        ScraperLogger: Configured logger instance
    
    Example:
        >>> logger = setup_logger("out/myproject", verbose=True)
        >>> logger.info("Starting scraping process")
        >>> logger.error("Failed to load page", url="https://example.com")
        >>> # With progress bar:
        >>> logger = setup_logger("out/myproject", verbose=False, console_output=False)
    """
    return ScraperLogger(output_dir, verbose=verbose, console_output=console_output)


# Backward compatibility: provide a simple log function
def create_simple_logger(output_dir: str):
    """
    Create a simple logger for backward compatibility.
    Returns a callable that logs at INFO level.
    
    Args:
        output_dir (str): Directory for log files
    
    Returns:
        Callable logger function
    """
    logger = setup_logger(output_dir)
    return logger
