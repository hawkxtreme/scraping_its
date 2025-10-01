import pytest
import asyncio
from bs4 import BeautifulSoup

@pytest.fixture
def async_mock():
    """Создает mock для асинхронных функций."""
    class AsyncMock:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
            self.calls = []

        async def __call__(self, *args, **kwargs):
            self.calls.append((args, kwargs))
            return self

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    return AsyncMock

@pytest.fixture
def mock_page(async_mock):
    """Mock для страницы Playwright."""
    class MockPage:
        def __init__(self):
            self.goto = async_mock()
            self.wait_for_load_state = async_mock()
            self.frame = lambda name: MockFrame() if name == "w_metadata_doc_frame" else None
            self.query_selector = async_mock()
            self.pdf = async_mock()
            self.close = async_mock()

    return MockPage()

class MockFrame:
    async def content(self):
        return """
        <div class="index">
            <a href="/db/article1">Article 1</a>
            <a href="/db/article2">Article 2</a>
        </div>
        """

@pytest.fixture
def mock_browser(async_mock):
    """Mock для браузера Playwright."""
    class MockBrowser:
        def __init__(self):
            self.new_context = async_mock()
            self.close = async_mock()

    return MockBrowser()

@pytest.fixture
def mock_playwright():
    """Mock для Playwright."""
    class MockPlaywright:
        def __init__(self):
            self.chromium = MockChromium()

    class MockChromium:
        async def connect_over_cdp(self, *args, **kwargs):
            return MockBrowser()

    return MockPlaywright()

@pytest.fixture
def sample_article_data():
    """Тестовые данные статьи."""
    return {
        "url": "https://its.1c.ru/db/article1",
        "title": "Test Article",
        "content": "Article content for testing"
    }

@pytest.fixture
def mock_logger():
    """Mock для логгера."""
    class MockLogger:
        def __init__(self):
            self.logs = []

        def __call__(self, message):
            self.logs.append(message)

    return MockLogger()