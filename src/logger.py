import os
import threading
import traceback
import sys
from datetime import datetime
from enum import Enum

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class Logger:
    def __init__(self, output_dir):
        """
        Sets up a thread-safe logger with different log levels.

        Args:
            output_dir (str): The directory where the log file will be saved.
        """
        os.makedirs(output_dir, exist_ok=True)
        self.log_file_path = os.path.join(output_dir, "script_log.txt")
        self.log_lock = threading.Lock()
        self.min_level = LogLevel.INFO  # Default minimum level
        
        # Ensure the log file is empty before starting
        with open(self.log_file_path, "w", encoding="utf-8") as f:
            pass

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self._write_log(LogLevel.INFO, f"---")
        self._write_log(LogLevel.INFO, f"Script started at: {timestamp}")
    
    def set_min_level(self, level):
        """Set the minimum log level to output."""
        self.min_level = level
    
    def _write_log(self, level, message):
        """Internal method to write a log message with timestamp and level."""
        if level.value < self.min_level.value:
            return
            
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] [{level.value}] {message}"
        
        with self.log_lock:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(f"{formatted_message}\n")
    
    def debug(self, message):
        """Log a debug message."""
        self._write_log(LogLevel.DEBUG, message)
    
    def info(self, message, details=None):
        """Log an info message with optional details."""
        self._write_log(LogLevel.INFO, message)
        if details:
            self.debug(f"Info details: {details}")
    
    def warning(self, message, details=None):
        """Log a warning message with optional details."""
        self._write_log(LogLevel.WARNING, message)
        if details:
            self.debug(f"Warning details: {details}")
    
    def error(self, message, exception=None):
        """Log an error message with optional exception details."""
        self._write_log(LogLevel.ERROR, message)
        if exception:
            self._write_log(LogLevel.ERROR, f"Exception details: {str(exception)}")
            self._write_log(LogLevel.DEBUG, f"Traceback: {traceback.format_exc()}")
    
    def critical(self, message, exception=None):
        """Log a critical error message with optional exception details."""
        self._write_log(LogLevel.CRITICAL, message)
        if exception:
            self._write_log(LogLevel.CRITICAL, f"Exception details: {str(exception)}")
            self._write_log(LogLevel.DEBUG, f"Traceback: {traceback.format_exc()}")
    
    def log_step(self, step_name, details=None):
        """Log a step in the process with optional details."""
        self.info(f"STEP: {step_name}")
        if details:
            self.debug(f"Step details: {details}")
    
    def log_progress(self, current, total, item_description="items"):
        """Log progress information."""
        percentage = (current / total) * 100 if total > 0 else 0
        self.info(f"Progress: {current}/{total} {item_description} ({percentage:.1f}%)")
    
    def log_performance(self, operation, duration, details=None):
        """Log performance metrics."""
        self.info(f"PERFORMANCE: {operation} completed in {duration:.2f} seconds")
        if details:
            self.debug(f"Performance details: {details}")

def setup_logger(output_dir, debug_mode=False):
    """
    Sets up a logger instance.

    Args:
        output_dir (str): The directory where the log file will be saved.
        debug_mode (bool): Enable debug logging if True.

    Returns:
        Logger: A Logger instance.
    """
    logger = Logger(output_dir)
    
    if debug_mode:
        logger.set_min_level(LogLevel.DEBUG)
    else:
        logger.set_min_level(LogLevel.INFO)
    
    # Create a simple log function for backward compatibility
    def log(message):
        logger.info(message)
    
    # Attach the logger instance to the log function for advanced usage
    log.logger = logger
    
    return log
