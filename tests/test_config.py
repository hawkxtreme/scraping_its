import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from src import config
from tests.conftest import verify_async_mock_calls

@pytest.mark.unit
@pytest.mark.asyncio
async def test_check_dependencies_with_missing_credentials(mock_logger, monkeypatch):
    """Тест проверки зависимостей при отсутствии учетных данных."""
    monkeypatch.setattr(config, "LOGIN_1C_USER", "")
    monkeypatch.setattr(config, "LOGIN_1C_PASSWORD", "")
    monkeypatch.setattr(config, "BROWSERLESS_URL", "http://localhost:3000")

    result = await config.check_dependencies(mock_logger)
    assert not result
    log_messages = [call_args[0][0] for call_args in mock_logger.call_args_list]
    assert any("  - [FAIL] Credentials not found or are default in .env file." in msg for msg in log_messages)
    assert any("Result: Failed - Credentials not set." in msg for msg in log_messages)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_check_dependencies_with_valid_credentials(mock_logger, mock_playwright):
    """Тест проверки зависимостей с валидными учетными данными."""
    with patch.dict(os.environ, {
        "LOGIN_1C_USER": "test_user",
        "LOGIN_1C_PASSWORD": "test_pass",
        "BROWSERLESS_URL": "http://localhost:3000"
    }):
        with patch("playwright.async_api.async_playwright", return_value=mock_playwright):
            result = await config.check_dependencies(mock_logger)
            assert result
            log_messages = [call_args[0][0] for call_args in mock_logger.call_args_list]
            assert "All dependency checks passed." in log_messages
            assert "  - [OK] Credentials found." in log_messages

@pytest.mark.unit
@pytest.mark.asyncio
async def test_check_dependencies_with_browserless_error(mock_logger, monkeypatch):
    """Тест проверки зависимостей при недоступности browserless."""
    monkeypatch.setattr(config, "LOGIN_1C_USER", "test_user")
    monkeypatch.setattr(config, "LOGIN_1C_PASSWORD", "test_pass")
    monkeypatch.setattr(config, "BROWSERLESS_URL", "http://invalid:3000")

    mock_playwright_instance = MagicMock()
    mock_playwright_instance.chromium.connect_over_cdp = AsyncMock(side_effect=Exception("Connection failed"))
    mock_playwright_instance.stop = AsyncMock()

    with patch("playwright.async_api.async_playwright", return_value=mock_playwright_instance):
        result = await config.check_dependencies(mock_logger)
        assert not result
        log_messages = [call_args[0][0] for call_args in mock_logger.call_args_list]
        assert any("Result: Failed - Browserless service not available" in msg for msg in log_messages)

@pytest.mark.unit
def test_config_constants():
    """Тест констант конфигурации."""
    assert config.BASE_URL == "https://its.1c.ru"
    assert config.LOGIN_URL == "https://login.1c.ru/login"
    assert os.path.exists(config.PROJECT_ROOT)
    assert os.path.exists(config.SCRIPT_DIR)
    assert "out" in config.OUTPUT_DIR
    assert "json" in config.JSON_DIR.lower()
    assert "pdf" in config.PDF_DIR.lower()
    assert "txt" in config.TXT_DIR.lower()
    assert "markdown" in config.MARKDOWN_DIR.lower()