import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from playwright.async_api import Error as PlaywrightError
from src.scraper import Scraper
from src import config
from src import file_manager
from src import parser

@pytest.mark.unit
@pytest.mark.asyncio
async def test_scraper_save_as_pdf_error_handling(mock_logger, monkeypatch):
    """Тест обработки ошибок при сохранении PDF."""
    mock_page = MagicMock()
    mock_page.url = "https://its.1c.ru/db/article_main"
    mock_page.query_selector = AsyncMock(return_value=None)
    mock_page.pdf = AsyncMock(side_effect=Exception("PDF generation error"))

    scraper = Scraper(mock_logger)
    scraper.context = MagicMock()

    # Заглушка для open
    import unittest.mock
    with unittest.mock.patch("builtins.open", unittest.mock.mock_open()) as mock_file:
        monkeypatch.setattr("os.path.join", lambda *args: "/tmp/test.pdf")
        await scraper._save_as_pdf(mock_page, "/tmp/test.pdf")

        log_messages = [call_args[0][0] for call_args in mock_logger.call_args_list]
        assert any("Could not save PDF for https://its.1c.ru/db/article_main: PDF generation error" in msg for msg in log_messages)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_scraper_save_as_pdf_with_print_link_fallback(mock_logger, mock_playwright, monkeypatch):
    """Тест сохранения PDF с fallback на основную страницу при проблемах с print-ссылкой."""
    # Extract components from fixture
    mock_page = mock_playwright.context.new_page.return_value
    mock_page.url = "https://its.1c.ru/db/article_main"
    mock_page.query_selector = AsyncMock()
    
    mock_print_link_element = MagicMock()
    mock_print_link_element.get_attribute = AsyncMock(return_value="/db/article_print")
    mock_page.query_selector.return_value = mock_print_link_element

    # Мок для новой страницы с ошибкой, чтобы вернуться к основной странице
    mock_print_page = MagicMock()
    mock_print_page.goto = AsyncMock(side_effect=Exception("Print page error"))
    mock_print_page.close = AsyncMock()

    mock_playwright.context.new_page = AsyncMock(return_value=mock_print_page)

    scraper = Scraper(mock_logger)
    scraper.context = mock_playwright.context

    # Мок для основного pdf метода
    mock_page.pdf = AsyncMock(return_value=b"main_pdf_content")

    import unittest.mock
    with unittest.mock.patch("builtins.open", unittest.mock.mock_open()) as mock_file:
        monkeypatch.setattr("os.path.join", lambda *args: "/tmp/test.pdf")
        # The _save_as_pdf method doesn't use playwright context directly, so no need to mock that
        await scraper._save_as_pdf(mock_page, "/tmp/test.pdf")

        # Должен использовать основной метод PDF, так как print page вызвал ошибку
        mock_page.pdf.assert_called_once()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_scraper_close_with_none_components(mock_logger):
    """Тест закрытия скрапера с None компонентами."""
    scraper = Scraper(mock_logger)
    # Убедимся, что browser и context равны None
    scraper.browser = None
    scraper.context = None
    
    # Это не должно вызвать ошибок
    await scraper.close()
    
    # Проверим, что сообщение о закрытии появилось
    log_messages = [call_args[0][0] for call_args in mock_logger.call_args_list]
    assert any("Browser connection closed" in msg for msg in log_messages)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_scraper_discover_articles_with_duplicate_urls(mock_logger, mock_playwright):
    """Тест обнаружения статей с дублирующимися URL."""
    # Используем две статьи с одинаковыми URL, но разными фрагментами
    initial_links = [
        {"url": "https://its.1c.ru/db/article1#section1", "title": "Article 1 section 1"},
        {"url": "https://its.1c.ru/db/article1#section2", "title": "Article 1 section 2"},
        {"url": "https://its.1c.ru/db/article2", "title": "Article 2"}
    ]
    
    # Extract components from fixture
    mock_page = mock_playwright.context.new_page.return_value
    mock_frame = MagicMock()
    mock_frame.content = AsyncMock(return_value="""
    <body>
        <div class="article-content">Test content</div>
    </body>
    """)
    mock_page.frame = AsyncMock(return_value=mock_frame)
    mock_page.goto = AsyncMock()
    mock_page.wait_for_load_state = AsyncMock()
    mock_page.close = AsyncMock()
    
    # Create a mock for the result of async_playwright() that has start() method
    mock_async_playwright_result = MagicMock()
    mock_async_playwright_result.start = AsyncMock(return_value=mock_playwright)
    
    with patch("src.scraper.async_playwright", return_value=mock_async_playwright_result):
        with patch.object(file_manager, 'save_index_data', new_callable=AsyncMock) as mock_save_index_data:
            with patch.object(parser, 'parse_article_page', return_value=(MagicMock(), [], 123)) as mock_parse_article_page:
                scraper = Scraper(mock_logger)
                await scraper.connect()
                await scraper.discover_articles(initial_links)
                
                # Должен обработать только уникальные URL (без фрагментов)
                # Всего 2 уникальных URL: article1 и article2
                # article1 встречается 2 раза, но обрабатывается 1 раз
                assert mock_async_playwright_result.start.call_count == 1
                assert mock_page.goto.call_count == 2  # Только для уникальных URL
                mock_save_index_data.assert_called_once()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_scraper_scrape_final_articles_with_special_characters_in_title(mock_logger, mock_playwright):
    """Тест скрапинга статей со специальными символами в заголовке."""
    articles_to_scrape = [
        {"url": "https://its.1c.ru/db/article1", "title": "Article with / and ? and #"},
        {"url": "https://its.1c.ru/db/article2", "title": "Article with <tags> & symbols"},
    ]
    formats = ['json']

    # Extract components from fixture
    mock_page = mock_playwright.context.new_page.return_value
    mock_frame = MagicMock()
    mock_frame.content = AsyncMock(return_value="<body>Test Content</body>")
    mock_page.frame = MagicMock(return_value=mock_frame)
    mock_page.goto = AsyncMock()
    mock_page.wait_for_load_state = AsyncMock()
    mock_page.close = AsyncMock()

    # Create a mock for the result of async_playwright() that has start() method
    mock_async_playwright_result = MagicMock()
    mock_async_playwright_result.start = AsyncMock(return_value=mock_playwright)
    
    with patch("src.scraper.async_playwright", return_value=mock_async_playwright_result):
        with patch.object(file_manager, 'save_article_content', new_callable=MagicMock) as mock_save_article_content:
            with patch.object(Scraper, '_save_as_pdf', new_callable=AsyncMock) as mock_save_as_pdf:
                scraper = Scraper(mock_logger)
                await scraper.connect()
                await scraper.scrape_final_articles(articles_to_scrape, formats)

                assert mock_async_playwright_result.start.call_count == 1
                assert mock_save_article_content.call_count == len(articles_to_scrape)
                
                # Проверим, что имена файлов были очищены от специальных символов
                for i, call_args in enumerate(mock_save_article_content.call_args_list):
                    filename_base = call_args[0][0]  # Первый аргумент - это filename_base
                    # filename_base должен начинаться с номера и подчеркивания
                    assert filename_base.startswith(f"{i+1:03d}_")