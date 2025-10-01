import os
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, AsyncMock

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

# Fixtures for testing
@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for testing file operations."""
    return tmp_path

@pytest.fixture
def mock_env(monkeypatch):
    """Setup mock environment variables for testing."""
    monkeypatch.setenv("LOGIN_1C_USER", "test_user")
    monkeypatch.setenv("LOGIN_1C_PASSWORD", "test_pass")
    monkeypatch.setenv("BROWSERLESS_URL", "http://localhost:3000")

async def verify_async_mock_calls(mock: MagicMock, calls: list[dict]) -> None:
    """
    Верифицирует, что асинхронный мок был вызван с ожидаемыми параметрами.

    Args:
        mock (MagicMock): Мок для проверки
        calls (list[dict]): Список вызовов для проверки, каждый вызов - словарь с параметрами
    """
    assert mock.await_count == len(calls), f"Expected {len(calls)} calls, got {mock.await_count}"
    for i, call in enumerate(calls):
        args = call.get("args", [])
        kwargs = call.get("kwargs", {})
        assert mock.await_args_list[i] == ((tuple(args), kwargs)), \
            f"Call {i} mismatch. Expected {args}, {kwargs}, got {mock.await_args_list[i]}"

@pytest.fixture
def mock_logger():
    """Фикстура для мока логгера."""
    logger = Mock()
    logger.logs = []
    def log_func(message):
        logger.logs.append(message)
    logger.__call__ = log_func
    return logger

@pytest.fixture
def mock_playwright():
    """Фикстура для мока Playwright."""
    # Main playwright object that has start() method
    playwright = MagicMock()
    playwright.start = AsyncMock()
    playwright.stop = AsyncMock()
    
    # Mock chromium
    playwright.chromium = MagicMock()
    playwright.chromium.connect_over_cdp = AsyncMock()
    
    # Mock browser
    browser = MagicMock()
    browser.new_context = AsyncMock()
    browser.close = AsyncMock()
    playwright.chromium.connect_over_cdp.return_value = browser
    
    # Mock context
    context = MagicMock()
    context.new_page = AsyncMock()
    context.close = AsyncMock()
    browser.new_context.return_value = context
    
    # Mock page
    page = MagicMock()
    page.goto = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.fill = AsyncMock()
    page.click = AsyncMock()
    page.content = AsyncMock()
    page.frame = MagicMock()
    page.close = AsyncMock()
    page.pdf = AsyncMock()
    page.query_selector = AsyncMock()
    context.new_page.return_value = page
    
    # Set the playwright object as the return value for the start method
    playwright.start.return_value = playwright
    
    return playwright

@pytest.fixture
def sample_html():
    """Return sample HTML content for testing parsers."""
    return """
    <html>
        <body>
            <div id="w_metadata_toc">
                <ul>
                    <li><a href="/db/article1">Article 1</a></li>
                    <li><a href="/db/article2">Article 2</a></li>
                </ul>
            </div>
            <div class="article-content">
                <h1>Test Article</h1>
                <p>Test content</p>
            </div>
        </body>
    </html>
    """