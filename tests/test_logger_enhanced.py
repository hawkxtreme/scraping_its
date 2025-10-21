import os
import pytest
import tempfile
import logging
from pathlib import Path

from src.logger import setup_logger, ScraperLogger


class TestScraperLogger:
    """Test suite for the enhanced logging system."""
    
    def test_logger_initialization(self, tmp_path):
        """Test that logger initializes correctly."""
        logger = setup_logger(str(tmp_path), verbose=False)
        
        assert logger is not None
        assert isinstance(logger, ScraperLogger)
        assert logger.output_dir == str(tmp_path)
        assert logger.verbose == False
        
    def test_logger_verbose_mode(self, tmp_path):
        """Test verbose mode enables DEBUG logging."""
        logger = setup_logger(str(tmp_path), verbose=True)
        
        assert logger.verbose == True
        assert logger.logger.level == logging.DEBUG
        
    def test_log_files_created(self, tmp_path):
        """Test that log files are created on initialization."""
        logger = setup_logger(str(tmp_path), verbose=False)
        
        # Check main log file
        assert os.path.exists(os.path.join(tmp_path, "script_log.txt"))
        
        # Check error log file
        assert os.path.exists(os.path.join(tmp_path, "errors.log"))
        
    def test_info_logging(self, tmp_path):
        """Test INFO level logging."""
        logger = setup_logger(str(tmp_path), verbose=False)
        logger.info("Test info message", test_key="test_value")
        
        log_file = os.path.join(tmp_path, "script_log.txt")
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Test info message" in content
            assert "INFO" in content
            assert "test_key=test_value" in content
            
    def test_debug_logging(self, tmp_path):
        """Test DEBUG level logging in verbose mode."""
        logger = setup_logger(str(tmp_path), verbose=True)
        logger.debug("Test debug message", url="https://example.com")
        
        log_file = os.path.join(tmp_path, "script_log.txt")
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Test debug message" in content
            assert "DEBUG" in content
            assert "url=https://example.com" in content
            
    def test_debug_logging_not_visible_without_verbose(self, tmp_path):
        """Test that DEBUG messages are not logged in non-verbose mode."""
        logger = setup_logger(str(tmp_path), verbose=False)
        logger.debug("This should not appear")
        
        log_file = os.path.join(tmp_path, "script_log.txt")
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Debug message should not be in the log
            assert "This should not appear" not in content
            
    def test_warning_logging(self, tmp_path):
        """Test WARNING level logging."""
        logger = setup_logger(str(tmp_path), verbose=False)
        logger.warning("Test warning message", code=404)
        
        log_file = os.path.join(tmp_path, "script_log.txt")
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Test warning message" in content
            assert "WARNING" in content
            assert "code=404" in content
            
    def test_error_logging(self, tmp_path):
        """Test ERROR level logging."""
        logger = setup_logger(str(tmp_path), verbose=False)
        logger.error("Test error message", error_code="E001")
        
        # Check main log
        log_file = os.path.join(tmp_path, "script_log.txt")
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Test error message" in content
            assert "ERROR" in content
            
        # Check error log
        error_log = os.path.join(tmp_path, "errors.log")
        with open(error_log, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Test error message" in content
            assert "ERROR" in content
            assert "error_code=E001" in content
            
    def test_critical_logging(self, tmp_path):
        """Test CRITICAL level logging."""
        logger = setup_logger(str(tmp_path), verbose=False)
        logger.critical("Test critical message")
        
        # Check error log
        error_log = os.path.join(tmp_path, "errors.log")
        with open(error_log, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Test critical message" in content
            assert "CRITICAL" in content
            
    def test_exception_logging(self, tmp_path):
        """Test exception logging with traceback."""
        logger = setup_logger(str(tmp_path), verbose=False)
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.exception("An error occurred", operation="test")
        
        # Check error log
        error_log = os.path.join(tmp_path, "errors.log")
        with open(error_log, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "An error occurred" in content
            assert "ValueError: Test exception" in content
            assert "operation=test" in content
            
    def test_log_error_with_context(self, tmp_path):
        """Test logging error with full context."""
        logger = setup_logger(str(tmp_path), verbose=False)
        
        try:
            raise ConnectionError("Connection failed")
        except ConnectionError as e:
            logger.log_error_with_context(
                e, 
                "scraping", 
                url="https://example.com",
                article_id=123
            )
        
        # Check error log
        error_log = os.path.join(tmp_path, "errors.log")
        with open(error_log, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Error during scraping" in content
            assert "ConnectionError" in content
            assert "url=https://example.com" in content
            assert "article_id=123" in content
            
    def test_error_suggestions(self, tmp_path):
        """Test that error suggestions are provided."""
        logger = setup_logger(str(tmp_path), verbose=False)
        
        # Test timeout error suggestion
        try:
            raise TimeoutError("Operation timed out")
        except TimeoutError as e:
            logger.log_error_with_context(e, "page_load")
        
        log_file = os.path.join(tmp_path, "script_log.txt")
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Suggestion" in content
            assert "timeout" in content.lower()
            
    def test_statistics_logging(self, tmp_path):
        """Test statistics logging."""
        logger = setup_logger(str(tmp_path), verbose=False)
        
        stats = {
            "total_articles": 100,
            "successful": 95,
            "failed": 5,
            "duration": "5 minutes"
        }
        
        logger.log_statistics(stats)
        
        log_file = os.path.join(tmp_path, "script_log.txt")
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "STATISTICS" in content
            assert "total_articles: 100" in content
            assert "successful: 95" in content
            assert "failed: 5" in content
            
    def test_callable_logger(self, tmp_path):
        """Test that logger is callable for backward compatibility."""
        logger = setup_logger(str(tmp_path), verbose=False)
        
        # Call logger directly (should delegate to info())
        logger("Direct call message")
        
        log_file = os.path.join(tmp_path, "script_log.txt")
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Direct call message" in content
            assert "INFO" in content
            
    def test_context_formatting(self, tmp_path):
        """Test that context is properly formatted."""
        logger = setup_logger(str(tmp_path), verbose=False)
        
        logger.info("Test message", 
                   url="https://example.com", 
                   status_code=200, 
                   duration=1.5)
        
        log_file = os.path.join(tmp_path, "script_log.txt")
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "url=https://example.com" in content
            assert "status_code=200" in content
            assert "duration=1.5" in content
            
    def test_multiple_loggers(self, tmp_path):
        """Test that multiple loggers can coexist."""
        log1_dir = os.path.join(tmp_path, "log1")
        log2_dir = os.path.join(tmp_path, "log2")
        
        logger1 = setup_logger(log1_dir, verbose=False, console_output=False)
        logger2 = setup_logger(log2_dir, verbose=True, console_output=False)
        
        logger1.info("Logger 1 message")
        logger2.info("Logger 2 message")
        
        # Flush handlers to ensure writes are completed
        for handler in logger1.logger.handlers:
            handler.flush()
        for handler in logger2.logger.handlers:
            handler.flush()
        
        # Check log1
        log1_file = os.path.join(log1_dir, "script_log.txt")
        with open(log1_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Logger 1 message" in content
            assert "Logger 2 message" not in content
            
        # Check log2
        log2_file = os.path.join(log2_dir, "script_log.txt")
        with open(log2_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Logger 2 message" in content
            assert "Logger 1 message" not in content
            
    def test_log_rotation_config(self, tmp_path):
        """Test that log rotation is configured."""
        logger = setup_logger(str(tmp_path), verbose=False)
        
        # Check that rotating handlers are set up
        handlers = logger.logger.handlers
        assert len(handlers) > 0
        
        # Find rotating file handlers
        from logging.handlers import RotatingFileHandler
        rotating_handlers = [h for h in handlers if isinstance(h, RotatingFileHandler)]
        assert len(rotating_handlers) >= 2  # Main log and error log
        
        # Check max bytes configuration
        for handler in rotating_handlers:
            assert handler.maxBytes > 0
            assert handler.backupCount > 0


class TestErrorSuggestions:
    """Test error suggestion functionality."""
    
    def test_timeout_suggestion(self, tmp_path):
        """Test timeout error suggestion."""
        logger = setup_logger(str(tmp_path), verbose=False)
        suggestion = logger._get_error_suggestion("TimeoutError", "Operation timed out")
        assert suggestion is not None
        assert "timeout" in suggestion.lower()
        
    def test_connection_suggestion(self, tmp_path):
        """Test connection error suggestion."""
        logger = setup_logger(str(tmp_path), verbose=False)
        suggestion = logger._get_error_suggestion("ConnectionError", "Connection refused")
        assert suggestion is not None
        assert "browserless" in suggestion.lower()
        
    def test_auth_suggestion(self, tmp_path):
        """Test authentication error suggestion."""
        logger = setup_logger(str(tmp_path), verbose=False)
        suggestion = logger._get_error_suggestion("AuthError", "Login failed")
        assert suggestion is not None
        assert "credentials" in suggestion.lower() or ".env" in suggestion.lower()
        
    def test_no_suggestion(self, tmp_path):
        """Test that unknown errors return None."""
        logger = setup_logger(str(tmp_path), verbose=False)
        suggestion = logger._get_error_suggestion("UnknownError", "Something went wrong")
        assert suggestion is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

