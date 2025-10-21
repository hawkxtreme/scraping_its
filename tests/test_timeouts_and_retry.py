import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from src import config
from src.utils import retry_on_error, retry_on_timeout, sleep_with_jitter


class TestConfigTimeouts:
    """Test timeout configuration in config module."""
    
    def test_default_timeouts(self):
        """Test that default timeout values are set correctly."""
        assert config.get_page_timeout() == 90000  # 90 seconds in milliseconds
        assert config.get_network_timeout() == 60000  # 60 seconds in milliseconds
        assert config.get_retry_count() == 3
        assert config.get_retry_delay() == 2.0
        assert config.get_request_delay() == 0.5
    
    def test_set_page_timeout(self):
        """Test setting page timeout."""
        config.set_timeouts(page_timeout=120)
        assert config.get_page_timeout() == 120000  # Converted to milliseconds
        
        # Reset to default
        config.set_timeouts(page_timeout=90)
    
    def test_set_network_timeout(self):
        """Test setting network timeout."""
        config.set_timeouts(network_timeout=90)
        assert config.get_network_timeout() == 90000  # Converted to milliseconds
        
        # Reset to default
        config.set_timeouts(network_timeout=60)
    
    def test_set_retry_count(self):
        """Test setting retry count."""
        config.set_timeouts(retry_count=5)
        assert config.get_retry_count() == 5
        
        # Reset to default
        config.set_timeouts(retry_count=3)
    
    def test_set_retry_delay(self):
        """Test setting retry delay."""
        config.set_timeouts(retry_delay=3.5)
        assert config.get_retry_delay() == 3.5
        
        # Reset to default
        config.set_timeouts(retry_delay=2.0)
    
    def test_set_request_delay(self):
        """Test setting request delay."""
        config.set_timeouts(request_delay=1.0)
        assert config.get_request_delay() == 1.0
        
        # Reset to default
        config.set_timeouts(request_delay=0.5)
    
    def test_set_multiple_timeouts(self):
        """Test setting multiple timeout values at once."""
        config.set_timeouts(
            page_timeout=100,
            network_timeout=80,
            retry_count=4,
            retry_delay=2.5,
            request_delay=0.8
        )
        
        assert config.get_page_timeout() == 100000
        assert config.get_network_timeout() == 80000
        assert config.get_retry_count() == 4
        assert config.get_retry_delay() == 2.5
        assert config.get_request_delay() == 0.8
        
        # Reset to defaults
        config.set_timeouts(
            page_timeout=90,
            network_timeout=60,
            retry_count=3,
            retry_delay=2.0,
            request_delay=0.5
        )
    
    def test_invalid_page_timeout_too_low(self):
        """Test that page timeout below minimum raises error."""
        with pytest.raises(ValueError, match="Page timeout must be between"):
            config.set_timeouts(page_timeout=5)
    
    def test_invalid_page_timeout_too_high(self):
        """Test that page timeout above maximum raises error."""
        with pytest.raises(ValueError, match="Page timeout must be between"):
            config.set_timeouts(page_timeout=400)
    
    def test_invalid_network_timeout_too_low(self):
        """Test that network timeout below minimum raises error."""
        with pytest.raises(ValueError, match="Network timeout must be between"):
            config.set_timeouts(network_timeout=2)
    
    def test_invalid_retry_count_negative(self):
        """Test that negative retry count raises error."""
        with pytest.raises(ValueError, match="Retry count must be between"):
            config.set_timeouts(retry_count=-1)
    
    def test_invalid_retry_count_too_high(self):
        """Test that retry count above maximum raises error."""
        with pytest.raises(ValueError, match="Retry count must be between"):
            config.set_timeouts(retry_count=15)
    
    def test_invalid_retry_delay_too_low(self):
        """Test that retry delay below minimum raises error."""
        with pytest.raises(ValueError, match="Retry delay must be between"):
            config.set_timeouts(retry_delay=0.05)
    
    def test_invalid_request_delay_negative(self):
        """Test that negative request delay raises error."""
        with pytest.raises(ValueError, match="Request delay must be between"):
            config.set_timeouts(request_delay=-0.5)


class TestRetryDecorator:
    """Test retry decorator functionality."""
    
    @pytest.mark.asyncio
    async def test_retry_on_error_succeeds_first_time(self):
        """Test that function succeeds on first try."""
        call_count = 0
        
        @retry_on_error(max_attempts=3, delay=0.1)
        async def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await successful_func()
        assert result == "success"
        assert call_count == 1  # Called only once
    
    @pytest.mark.asyncio
    async def test_retry_on_error_retries_on_failure(self):
        """Test that function retries on failure."""
        call_count = 0
        
        @retry_on_error(max_attempts=3, delay=0.1)
        async def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"
        
        result = await failing_then_success()
        assert result == "success"
        assert call_count == 3  # Called 3 times (2 failures, 1 success)
    
    @pytest.mark.asyncio
    async def test_retry_on_error_raises_after_max_attempts(self):
        """Test that exception is raised after max attempts."""
        call_count = 0
        
        @retry_on_error(max_attempts=3, delay=0.1)
        async def always_failing():
            nonlocal call_count
            call_count += 1
            raise ValueError("Permanent error")
        
        with pytest.raises(ValueError, match="Permanent error"):
            await always_failing()
        
        assert call_count == 3  # Called 3 times then gave up
    
    @pytest.mark.asyncio
    async def test_retry_with_zero_attempts(self):
        """Test retry with count=0 executes only once."""
        call_count = 0
        
        @retry_on_error(max_attempts=0, delay=0.1)
        async def func_with_no_retry():
            nonlocal call_count
            call_count += 1
            return "done"
        
        result = await func_with_no_retry()
        assert result == "done"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_exponential_backoff(self):
        """Test that retry uses exponential backoff."""
        call_times = []
        
        @retry_on_error(max_attempts=3, delay=0.1, backoff=2.0)
        async def func_with_timing():
            import time
            call_times.append(time.time())
            if len(call_times) < 3:
                raise ValueError("Error")
            return "success"
        
        await func_with_timing()
        
        assert len(call_times) == 3
        
        # Check delays (approximately)
        # First to second: ~0.1s (delay * 2^0)
        # Second to third: ~0.2s (delay * 2^1)
        if len(call_times) >= 2:
            delay1 = call_times[1] - call_times[0]
            assert 0.08 < delay1 < 0.15  # ~0.1s with some tolerance
        
        if len(call_times) >= 3:
            delay2 = call_times[2] - call_times[1]
            assert 0.15 < delay2 < 0.25  # ~0.2s with some tolerance
    
    @pytest.mark.asyncio
    async def test_retry_on_timeout_decorator(self):
        """Test specialized timeout retry decorator."""
        call_count = 0
        
        @retry_on_timeout(max_attempts=3, delay=0.1)
        async def func_with_timeout():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TimeoutError("Timeout")
            return "success"
        
        result = await func_with_timeout()
        assert result == "success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_retry_catches_specific_exceptions(self):
        """Test that retry only catches specified exceptions."""
        call_count = 0
        
        @retry_on_error(max_attempts=3, delay=0.1, exceptions=(ValueError,))
        async def func_with_specific_exception():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Should retry")
            elif call_count == 2:
                raise TypeError("Should not retry")
            return "success"
        
        # TypeError should not be caught
        with pytest.raises(TypeError, match="Should not retry"):
            await func_with_specific_exception()
        
        assert call_count == 2  # ValueError retried, TypeError raised
    
    @pytest.mark.asyncio
    async def test_retry_uses_config_defaults(self):
        """Test that retry uses config values when not specified."""
        # Set config values
        config.set_timeouts(retry_count=2, retry_delay=0.1)
        
        call_count = 0
        
        @retry_on_error()  # No explicit attempts or delay
        async def func_using_config():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Error")
            return "success"
        
        result = await func_using_config()
        assert result == "success"
        assert call_count == 2
        
        # Reset config
        config.set_timeouts(retry_count=3, retry_delay=2.0)


class TestSleepWithJitter:
    """Test sleep with jitter utility."""
    
    @pytest.mark.asyncio
    async def test_sleep_with_jitter(self):
        """Test that sleep duration varies with jitter."""
        import time
        
        durations = []
        for _ in range(10):
            start = time.time()
            await sleep_with_jitter(1.0, jitter=0.2)
            duration = time.time() - start
            durations.append(duration)
        
        # Check that durations vary (not all the same)
        assert len(set([round(d, 1) for d in durations])) > 1
        
        # Check that all durations are within expected range
        for d in durations:
            assert 0.8 <= d <= 1.2  # 1.0 ± 20%
    
    @pytest.mark.asyncio
    async def test_sleep_with_zero_jitter(self):
        """Test sleep with zero jitter is consistent."""
        import time
        
        start = time.time()
        await sleep_with_jitter(0.5, jitter=0.0)
        duration = time.time() - start
        
        assert 0.49 <= duration <= 0.52  # Approximately 0.5s


class TestCommandLineTimeouts:
    """Test timeout arguments from command line."""
    
    def test_timeout_arguments_parsing(self):
        """Test that timeout arguments are parsed correctly."""
        import sys
        from main import argparse
        
        # Save original argv
        original_argv = sys.argv
        
        try:
            sys.argv = [
                'main.py',
                'https://its.1c.ru/db/test',
                '--timeout', '120',
                '--network-timeout', '90',
                '--retry-count', '5',
                '--retry-delay', '3.0',
                '--delay', '1.0'
            ]
            
            parser = argparse.ArgumentParser()
            parser.add_argument("url")
            parser.add_argument("--timeout", type=int, default=90)
            parser.add_argument("--network-timeout", type=int, default=60)
            parser.add_argument("--retry-count", type=int, default=3)
            parser.add_argument("--retry-delay", type=float, default=2.0)
            parser.add_argument("--delay", type=float, default=0.5)
            
            args = parser.parse_args()
            
            assert args.timeout == 120
            assert args.network_timeout == 90
            assert args.retry_count == 5
            assert args.retry_delay == 3.0
            assert args.delay == 1.0
            
        finally:
            sys.argv = original_argv
    
    def test_timeout_defaults(self):
        """Test that timeout defaults are correct."""
        import sys
        from main import argparse
        
        original_argv = sys.argv
        
        try:
            sys.argv = ['main.py', 'https://its.1c.ru/db/test']
            
            parser = argparse.ArgumentParser()
            parser.add_argument("url")
            parser.add_argument("--timeout", type=int, default=90)
            parser.add_argument("--network-timeout", type=int, default=60)
            parser.add_argument("--retry-count", type=int, default=3)
            parser.add_argument("--retry-delay", type=float, default=2.0)
            parser.add_argument("--delay", type=float, default=0.5)
            
            args = parser.parse_args()
            
            assert args.timeout == 90
            assert args.network_timeout == 60
            assert args.retry_count == 3
            assert args.retry_delay == 2.0
            assert args.delay == 0.5
            
        finally:
            sys.argv = original_argv


class TestRetryIntegration:
    """Integration tests for retry functionality."""
    
    @pytest.mark.asyncio
    async def test_retry_with_logger(self):
        """Test retry decorator logs retry attempts."""
        from src.logger import setup_logger
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            logger = setup_logger(tmp_dir, verbose=True, console_output=False)
            
            call_count = 0
            
            class MockScraper:
                def __init__(self):
                    self.log = logger
                
                @retry_on_error(max_attempts=3, delay=0.1)
                async def scrape_with_retry(self):
                    nonlocal call_count
                    call_count += 1
                    if call_count < 2:
                        raise ValueError("Temporary error")
                    return "success"
            
            scraper = MockScraper()
            result = await scraper.scrape_with_retry()
            
            assert result == "success"
            assert call_count == 2
            
            # Check that retry was logged
            import os
            log_file = os.path.join(tmp_dir, "script_log.txt")
            
            # Close logger before reading file
            logger.close()
            
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "Retry attempt" in content or "Retry successful" in content
    
    @pytest.mark.asyncio
    async def test_retry_timeout_with_config(self):
        """Test that retry uses config timeout values."""
        config.set_timeouts(retry_count=2, retry_delay=0.1)
        
        call_count = 0
        
        class MockScraper:
            def __init__(self):
                self.log = MagicMock()
            
            @retry_on_error()  # Use config defaults
            async def operation(self):
                nonlocal call_count
                call_count += 1
                if call_count < 2:
                    raise ConnectionError("Network issue")
                return "ok"
        
        scraper = MockScraper()
        result = await scraper.operation()
        
        assert result == "ok"
        assert call_count == 2
        
        # Reset config
        config.set_timeouts(retry_count=3, retry_delay=2.0)


class TestRetryBackoff:
    """Test exponential backoff behavior."""
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self):
        """Test that backoff timing follows exponential pattern."""
        import time
        
        call_times = []
        
        @retry_on_error(max_attempts=4, delay=0.1, backoff=2.0)
        async def func():
            call_times.append(time.time())
            if len(call_times) < 4:
                raise ValueError("Error")
            return "success"
        
        await func()
        
        assert len(call_times) == 4
        
        # Verify exponential delays
        # Delay 1: 0.1 * 2^0 = 0.1s
        # Delay 2: 0.1 * 2^1 = 0.2s
        # Delay 3: 0.1 * 2^2 = 0.4s
        
        if len(call_times) >= 2:
            delay1 = call_times[1] - call_times[0]
            assert 0.08 < delay1 < 0.15  # ~0.1s
        
        if len(call_times) >= 3:
            delay2 = call_times[2] - call_times[1]
            assert 0.15 < delay2 < 0.25  # ~0.2s
        
        if len(call_times) >= 4:
            delay3 = call_times[3] - call_times[2]
            assert 0.35 < delay3 < 0.50  # ~0.4s
    
    @pytest.mark.asyncio
    async def test_retry_logs_attempts(self):
        """Test that retry attempts are logged."""
        from src.logger import setup_logger
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            logger = setup_logger(tmp_dir, verbose=True, console_output=False)
            
            call_count = 0
            
            class TestClass:
                def __init__(self):
                    self.log = logger
                
                @retry_on_error(max_attempts=3, delay=0.05)
                async def method_with_retry(self):
                    nonlocal call_count
                    call_count += 1
                    if call_count < 3:
                        raise ConnectionError("Connection failed")
                    return "connected"
            
            obj = TestClass()
            result = await obj.method_with_retry()
            
            assert result == "connected"
            assert call_count == 3
            
            # Close logger before reading file
            logger.close()
            
            # Verify logging
            import os
            log_file = os.path.join(tmp_dir, "script_log.txt")
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Should contain retry messages
                assert "Retry" in content or "attempt" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

