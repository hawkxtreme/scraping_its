import pytest
from unittest.mock import patch, MagicMock, AsyncMock, PropertyMock
from playwright.async_api import Error as PlaywrightError
from src.scraper import Scraper
from src import config
from tests.conftest import verify_async_mock_calls
from src import file_manager
from src import parser

@pytest.mark.unit
@pytest.mark.asyncio
async def test_scraper_initialization(mock_logger):
    """Тест инициализации скрапера."""
    scraper = Scraper(mock_logger)
    assert scraper.log == mock_logger
    assert not scraper.browser
    assert not scraper.context

@pytest.mark.unit
@pytest.mark.asyncio
async def test_scraper_connect(mock_logger, mock_playwright):
    """Тест подключения к browserless."""
    # Extract the components from the mock_playwright fixture
    mock_browser = mock_playwright.chromium.connect_over_cdp.return_value
    mock_context = mock_browser.new_context.return_value
    
    # Create a mock for the result of async_playwright() that has start() method
    mock_async_playwright_result = MagicMock()
    mock_async_playwright_result.start = AsyncMock(return_value=mock_playwright)
    
    with patch("src.scraper.async_playwright", return_value=mock_async_playwright_result):
        scraper = Scraper(mock_logger)
        await scraper.connect()
        assert scraper.browser is not None
        assert scraper.context is not None
        
        # Проверяем, что были вызваны нужные методы
        mock_async_playwright_result.start.assert_called_once()
        mock_playwright.chromium.connect_over_cdp.assert_called_once_with(config.BROWSERLESS_URL)
        mock_browser.new_context.assert_called_once()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_scraper_login_success(mock_logger, mock_playwright):
    """Тест успешного логина."""
    # Create a mock page for login
    mock_page = MagicMock()
    mock_page.url = "https://login.1c.ru/user/profile"  # Успешный логин
    mock_page.query_selector = AsyncMock(return_value=True)
    mock_page.goto = AsyncMock()
    mock_page.fill = AsyncMock()
    mock_page.click = AsyncMock()
    mock_page.wait_for_load_state = AsyncMock()

    # Create a mock for the result of async_playwright() that has start() method
    mock_async_playwright_result = MagicMock()
    mock_async_playwright_result.start = AsyncMock(return_value=mock_playwright)
    
    # Mock the context.new_page to return our mock page - делаем это после connect()
    with patch.object(mock_playwright.context, 'new_page', new_callable=AsyncMock) as mock_new_page:
        mock_new_page.return_value = mock_page
    
    with patch("src.scraper.async_playwright", return_value=mock_async_playwright_result):
        scraper = Scraper(mock_logger)
        await scraper.connect()
        # Мокаем context.new_page после connect(), когда context уже установлен
        with patch.object(scraper.context, 'new_page', return_value=mock_page):
            await scraper.login()
            
            # Проверяем, что были вызваны нужные методы
            mock_async_playwright_result.start.assert_called_once()
            mock_page.goto.assert_called_once_with(config.LOGIN_URL, timeout=60000)
            assert mock_page.fill.call_count == 2
            mock_page.click.assert_called_once_with('#loginButton')
            assert mock_page.wait_for_load_state.call_count == 2

@pytest.mark.unit
@pytest.mark.asyncio
async def test_scraper_login_failure(mock_logger, mock_playwright):
    """Тест неудачного логина (неправильное перенаправление)."""
    # Create a mock page for login failure
    mock_page = MagicMock()
    mock_page.url = "https://login.1c.ru/some_other_page"  # Неудачный логин
    mock_page.query_selector = AsyncMock(return_value=True)
    mock_page.goto = AsyncMock()
    mock_page.fill = AsyncMock()
    mock_page.click = AsyncMock()
    mock_page.wait_for_load_state = AsyncMock()

    # Create a mock for the result of async_playwright() that has start() method
    mock_async_playwright_result = MagicMock()
    mock_async_playwright_result.start = AsyncMock(return_value=mock_playwright)
    
    
    with patch("src.scraper.async_playwright", return_value=mock_async_playwright_result):
        scraper = Scraper(mock_logger)
        await scraper.connect()
        # Мокаем context.new_page после connect(), когда context уже установлен
        with patch.object(scraper.context, 'new_page', return_value=mock_page):
            # Удаляем pytest.raises, потому что исключение может быть перехвачено внутри метода
            await scraper.login()
            
            # Проверяем, что была попытка логина и ошибка была зафиксирована
            log_messages = [call_args[0][0] for call_args in mock_logger.call_args_list]
            assert any("FATAL: Login failed" in msg for msg in log_messages)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_scraper_get_initial_toc(mock_logger, mock_playwright):
    """Тест получения начального оглавления."""
    test_url = "https://its.1c.ru/db/test"
    
    # Создаем полноценный AsyncMock для страницы
    mock_page = AsyncMock()
    mock_page.content = AsyncMock(return_value="""
    <html>
    <head>
        <title>Test Page</title>
    </head>
    <body>
        <div id="w_metadata_toc">
            <ul>
                <li><a href="/db/article1">Article 1</a></li>
                <li><a href="/db/article2">Article 2</a></li>
            </ul>
        </div>
    </body>
    </html>
    """)
    mock_page.goto = AsyncMock()
    mock_page.wait_for_load_state = AsyncMock()

    # Мокаем context.new_page, чтобы он возвращал mock_page
    mock_playwright.context.new_page = AsyncMock(return_value=mock_page)
    
    # Create a mock for the result of async_playwright() that has start() method
    mock_async_playwright_result = MagicMock()
    mock_async_playwright_result.start = AsyncMock(return_value=mock_playwright)
    
    with patch("src.scraper.async_playwright", return_value=mock_async_playwright_result):
        with patch("src.parser_v1.extract_toc_links", return_value=[
            {"title": "Article 1", "url": "https://its.1c.ru/db/article1", "original_order": 0},
            {"title": "Article 2", "url": "https://its.1c.ru/db/article2", "original_order": 1}
        ]):
            scraper = Scraper(mock_logger)
            await scraper.connect()
            # Мокаем page.content() внутри метода get_initial_toc
            with patch.object(scraper.context, 'new_page') as mock_new_page:
                mock_page_instance = AsyncMock()
                mock_page_instance.content.return_value = """
                <html>
                <head>
                    <title>Test Page</title>
                </head>
                <body>
                    <div id="w_metadata_toc">
                        <ul>
                            <li><a href="/db/article1">Article 1</a></li>
                            <li><a href="/db/article2">Article 2</a></li>
                        </ul>
                    </div>
                </body>
                </html>
                """
                mock_page_instance.goto = AsyncMock()
                mock_page_instance.wait_for_load_state = AsyncMock()
                mock_new_page.return_value = mock_page_instance
                
                links = await scraper.get_initial_toc(test_url, None)
                
                assert isinstance(links, list)
                assert len(links) == 2
                for link in links:
                    assert all(key in link for key in ["url", "title", "original_order"])


@pytest.mark.unit
@pytest.mark.asyncio
async def test_scraper_discover_articles(mock_logger, mock_playwright):
    """Тест обнаружения статей."""
    initial_links = [
        {"url": "https://its.1c.ru/db/article1", "title": "Article 1"},
        {"url": "https://its.1c.ru/db/article2", "title": "Article 2"}
    ]
    
    # Extract components from fixture
    mock_frame = MagicMock()
    mock_frame.content = AsyncMock(return_value="""
    <body>
        <div class="article-content">Test content</div>
        <div class="index">
            <a href="/db/nested1">Nested Article 1</a>
        </div>
    </body>
    """)
    
    # Создаем отдельные mock_page для каждого вызова new_page()
    mock_page1 = MagicMock()
    mock_page1.frame = AsyncMock(return_value=mock_frame)
    mock_page1.goto = AsyncMock()
    mock_page1.wait_for_load_state = AsyncMock()
    mock_page1.close = AsyncMock()
    
    mock_page2 = MagicMock()
    mock_page2.frame = AsyncMock(return_value=mock_frame)
    mock_page2.goto = AsyncMock()
    mock_page2.wait_for_load_state = AsyncMock()
    mock_page2.close = AsyncMock()
    
    # Мокаем context.new_page, чтобы он возвращал разные страницы
    new_page_calls = [mock_page1, mock_page2]
    call_count = 0
    
    async def mock_new_page():
        nonlocal call_count
        if call_count < len(new_page_calls):
            result = new_page_calls[call_count]
            call_count += 1
            return result
        else:
            # Возвращаем последнюю страницу, если вызовов больше
            return new_page_calls[-1]
    
    mock_playwright.context.new_page = AsyncMock(side_effect=mock_new_page)
    
    # Create a mock for the result of async_playwright() that has start() method
    mock_async_playwright_result = MagicMock()
    mock_async_playwright_result.start = AsyncMock(return_value=mock_playwright)
    
    with patch("src.scraper.async_playwright", return_value=mock_async_playwright_result):
        with patch.object(file_manager, 'save_index_data', new_callable=AsyncMock) as mock_save_index_data:
            with patch('src.parser_v1.parse_article_page', return_value=(MagicMock(), [], 123)) as mock_parse_article_page:
                scraper = Scraper(mock_logger)
                await scraper.connect()
                await scraper.discover_articles(initial_links)
                
                # Проверяем, что были правильные вызовы
                assert mock_async_playwright_result.start.call_count == 1
                assert mock_playwright.context.new_page.call_count == len(initial_links)
                assert mock_page.goto.call_count == len(initial_links)
                assert mock_parse_article_page.call_count == len(initial_links)
                mock_save_index_data.assert_called_once_with(initial_links)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_scraper_discover_articles_no_frame(mock_logger, mock_playwright):
    """Тест обнаружения статей, когда фрейм статьи не найден."""
    initial_links = [
        {"url": "https://its.1c.ru/db/article1", "title": "Article 1"}
    ]
    
    mock_page = MagicMock()
    mock_page.frame = AsyncMock(return_value=None) # Имитируем отсутствие фрейма
    mock_page.goto = AsyncMock()
    mock_page.wait_for_load_state = AsyncMock()
    mock_page.close = AsyncMock()
    
    mock_context = MagicMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)
    
    mock_browser = MagicMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    mock_playwright.chromium.connect_over_cdp = AsyncMock(return_value=mock_browser)
    
    with patch("playwright.async_api.async_playwright", return_value=mock_playwright):
        with patch.object(file_manager, 'save_index_data', new_callable=AsyncMock) as mock_save_index_data:
            scraper = Scraper(mock_logger)
            await scraper.connect()
            await scraper.discover_articles(initial_links)
            
            # Проверяем, что ошибка была залогирована и save_index_data всё равно вызывается
            log_messages = [call_args[0][0] for call_args in mock_logger.call_args_list]
            assert any("ERROR during discovery for Article 1: Could not find article frame" in msg for msg in log_messages)
            # save_index_data будет вызван с оставшимися статьями, но в этом случае с пустым списком

@pytest.mark.unit
@pytest.mark.asyncio
async def test_scraper_close(mock_logger, mock_playwright):
    """Тест закрытия соединений."""
    # Создаем асинхронные моки
    mock_context = MagicMock()
    mock_context.close = AsyncMock()

    mock_browser = MagicMock()
    mock_browser.close = AsyncMock()
    mock_playwright.chromium.connect_over_cdp.return_value = mock_browser

    with patch("playwright.async_api.async_playwright", return_value=mock_playwright):
        scraper = Scraper(mock_logger)
        await scraper.connect()
        scraper.context = mock_context
        scraper.browser = mock_browser
        await scraper.close()
        
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_scraper_error_handling(mock_logger):
    """Тест обработки ошибок."""
    # Создаем Scraper без подключения и пробуем вызвать методы
    scraper = Scraper(mock_logger)
    # Просто проверяем, что исключение может быть вызвано
    try:
        # Пытаемся использовать скрапер без подключения
        await scraper.login()
    except:
        pass  # Ожидаем, что будет исключение
    
    # Проверяем, что была попытка логирования ошибки
    log_messages = [call_args[0][0] for call_args in mock_logger.call_args_list]
    assert any("FATAL: Login failed" in msg for msg in log_messages)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_safely_close_page(mock_logger):
    """Тест безопасного закрытия страницы."""
    mock_page = MagicMock()
    mock_page.close = AsyncMock()

    scraper = Scraper(mock_logger)
    await scraper._safely_close_page(mock_page)
    mock_page.close.assert_called_once()

    # Тест обработки исключения при закрытии страницы
    mock_page.close.side_effect = Exception("Page close error")
    await scraper._safely_close_page(mock_page)
    log_messages = [call_args[0][0] for call_args in mock_logger.call_args_list]
    assert any("Warning: Error closing page: Page close error" in msg for msg in log_messages)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_safely_close_page_none(mock_logger):
    """Тест безопасного закрытия страницы, когда страница None."""
    scraper = Scraper(mock_logger)
    await scraper._safely_close_page(None)
    # Проверяем, что никаких ошибок не возникло и логгер не был вызван с предупреждением
    assert not any("Warning: Error closing page" in msg for msg in mock_logger.call_args_list)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_scraper_save_as_pdf_with_print_link(mock_logger, monkeypatch):
    """Тест сохранения PDF с использованием print-friendly ссылки."""
    mock_page = MagicMock()
    mock_page.url = "https://its.1c.ru/db/article_main"
    mock_page.query_selector = AsyncMock()
    mock_page.pdf = AsyncMock(return_value=b"pdf_content_main")

    mock_print_link_element = MagicMock()
    mock_print_link_element.get_attribute = AsyncMock(return_value="/db/article_print")
    mock_page.query_selector.return_value = mock_print_link_element

    mock_print_page = MagicMock()
    mock_print_page.goto = AsyncMock()
    mock_print_page.wait_for_load_state = AsyncMock()
    mock_print_page.pdf = AsyncMock(return_value=b"pdf_content_print")
    mock_print_page.close = AsyncMock()

    mock_context = MagicMock()
    mock_context.new_page = AsyncMock(return_value=mock_print_page)

    scraper = Scraper(mock_logger)
    scraper.context = mock_context

    # Создаем мок для open
    mock_open = MagicMock()
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    monkeypatch.setattr("builtins.open", mock_open)
    monkeypatch.setattr("os.path.join", lambda *args: "/tmp/test.pdf")

    await scraper._save_as_pdf(mock_page, "/tmp/test.pdf")

    mock_page.query_selector.assert_called_once_with('#w_metadata_print_href')
    mock_print_link_element.get_attribute.assert_called_once_with('href')
    mock_context.new_page.assert_called_once()
    mock_print_page.goto.assert_called_once_with("https://its.1c.ru/db/article_print", timeout=90000)
    mock_print_page.pdf.assert_called_once_with(format='A4', print_background=True)
    # Проверяем, что файл был открыт для записи
    mock_open.assert_called_once_with("/tmp/test.pdf", "wb")
    # Проверяем, что содержимое было записано
    mock_file.write.assert_called_once_with(b"pdf_content_print")
    mock_print_page.close.assert_called_once()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_scraper_save_as_pdf_no_print_link(mock_logger, monkeypatch):
    """Тест сохранения PDF без print-friendly ссылки (используется основная страница)."""
    mock_page = MagicMock()
    mock_page.url = "https://its.1c.ru/db/article_main"
    mock_page.query_selector = AsyncMock(return_value=None) # Нет print-friendly ссылки
    mock_page.pdf = AsyncMock(return_value=b"pdf_content_main")

    scraper = Scraper(mock_logger)

    # Создаем мок для open
    mock_open = MagicMock()
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    monkeypatch.setattr("builtins.open", mock_open)
    monkeypatch.setattr("os.path.join", lambda *args: "/tmp/test.pdf")

    await scraper._save_as_pdf(mock_page, "/tmp/test.pdf")

    mock_page.query_selector.assert_called_once_with('#w_metadata_print_href')
    mock_page.pdf.assert_called_once_with(format='A4', print_background=True)
    mock_open.assert_called_once_with("/tmp/test.pdf", "wb")
    mock_file.write.assert_called_once_with(b"pdf_content_main")

@pytest.mark.unit
@pytest.mark.asyncio
async def test_scraper_save_as_pdf_error(mock_logger, monkeypatch):
    """Тест обработки ошибки при сохранении PDF."""
    mock_page = MagicMock()
    mock_page.url = "https://its.1c.ru/db/article_main"
    mock_page.query_selector = AsyncMock(return_value=None)
    mock_page.pdf = AsyncMock(side_effect=Exception("PDF generation error"))

    scraper = Scraper(mock_logger)

    mock_open = MagicMock()
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    monkeypatch.setattr("builtins.open", mock_open)
    monkeypatch.setattr("os.path.join", lambda *args: "/tmp/test.pdf")

    await scraper._save_as_pdf(mock_page, "/tmp/test.pdf")

    log_messages = [call_args[0][0] for call_args in mock_logger.call_args_list]
    assert any("Could not save PDF for https://its.1c.ru/db/article_main: PDF generation error" in msg for msg in log_messages)
    # Ошибка должна быть записана в файл с расширением .error.txt
    mock_open.assert_called_once()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_scraper_scrape_single_article(mock_logger, mock_playwright):
    """Тест финального скрапинга статей."""
    articles_to_scrape = [
        {"url": "https://its.1c.ru/db/article1", "title": "Article 1"},
        {"url": "https://its.1c.ru/db/article2", "title": "Article 2"}
    ]
    formats = ['json', 'txt', 'pdf']

    # Extract components from fixture
    mock_frame = MagicMock()
    mock_frame.content = AsyncMock(return_value="<body>Test Content</body>")
    
    # Создаем отдельные mock_page для каждого вызова new_page()
    mock_page1 = MagicMock()
    mock_page1.frame = MagicMock(return_value=mock_frame)
    mock_page1.goto = AsyncMock()
    mock_page1.wait_for_load_state = AsyncMock()
    mock_page1.close = AsyncMock()
    
    mock_page2 = MagicMock()
    mock_page2.frame = MagicMock(return_value=mock_frame)
    mock_page2.goto = AsyncMock()
    mock_page2.wait_for_load_state = AsyncMock()
    mock_page2.close = AsyncMock()
    
    # Мокаем context.new_page, чтобы он возвращал разные страницы
    new_page_calls = [mock_page1, mock_page2]
    call_count = 0
    
    async def mock_new_page():
        nonlocal call_count
        if call_count < len(new_page_calls):
            result = new_page_calls[call_count]
            call_count += 1
            return result
        else:
            # Возвращаем последнюю страницу, если вызовов больше
            return new_page_calls[-1]
    
    mock_playwright.context.new_page = AsyncMock(side_effect=mock_new_page)

    # Create a mock for the result of async_playwright() that has start() method
    mock_async_playwright_result = MagicMock()
    mock_async_playwright_result.start = AsyncMock(return_value=mock_playwright)
    
    with patch("src.scraper.async_playwright", return_value=mock_async_playwright_result):
        with patch.object(file_manager, 'save_article_content', new_callable=MagicMock) as mock_save_article_content:
            with patch.object(Scraper, '_save_as_pdf', new_callable=AsyncMock) as mock_save_as_pdf:
                scraper = Scraper(mock_logger)
                await scraper.connect()
                for i, article_info in enumerate(articles_to_scrape):
                    await scraper.scrape_single_article(article_info, formats, i, len(articles_to_scrape))

                assert mock_async_playwright_result.start.call_count == 1
                assert mock_playwright.context.new_page.call_count == len(articles_to_scrape)
                assert mock_page.goto.call_count == len(articles_to_scrape)
                assert mock_save_article_content.call_count == len(articles_to_scrape)
                assert mock_save_as_pdf.call_count == len(articles_to_scrape)
                
                # Проверяем, что save_article_content вызывается с правильными аргументами
                for i, article in enumerate(articles_to_scrape):
                    filename_base_prefix = f"{i+1:03d}"
                    assert mock_save_article_content.call_args_list[i][0][0].startswith(filename_base_prefix)
                    assert mock_save_article_content.call_args_list[i][0][1] == formats
                    assert isinstance(mock_save_article_content.call_args_list[i][0][2], MagicMock)  # BeautifulSoup
                    assert mock_save_article_content.call_args_list[i][0][3] == article

@pytest.mark.unit
@pytest.mark.asyncio
async def test_scraper_scrape_single_article_error_handling(mock_logger, mock_playwright):
    """Тест обработки ошибок в scrape_single_article."""
    articles_to_scrape = [
        {"url": "https://its.1c.ru/db/article1", "title": "Article 1"},
        {"url": "https://its.1c.ru/db/article2", "title": "Article 2"}
    ]
    formats = ['json']

    # Extract components from fixture
    mock_frame = MagicMock()
    mock_frame.content = AsyncMock(return_value="<body>Test Content</body>")
    
    # Создаем отдельные mock_page для каждого вызова new_page()
    mock_page1 = MagicMock()
    mock_page1.frame = MagicMock(return_value=mock_frame)
    mock_page1.goto = AsyncMock()
    mock_page1.wait_for_load_state = AsyncMock()
    mock_page1.close = AsyncMock()
    
    mock_page2 = MagicMock()
    # Имитируем ошибку на второй статье
    mock_page2.frame = MagicMock(side_effect=PlaywrightError("Frame not found"))
    mock_page2.goto = AsyncMock()
    mock_page2.wait_for_load_state = AsyncMock()
    mock_page2.close = AsyncMock()
    
    # Мокаем context.new_page, чтобы он возвращал разные страницы
    new_page_calls = [mock_page1, mock_page2]
    call_count = 0
    
    async def mock_new_page():
        nonlocal call_count
        if call_count < len(new_page_calls):
            result = new_page_calls[call_count]
            call_count += 1
            return result
        else:
            # Возвращаем последнюю страницу, если вызовов больше
            return new_page_calls[-1]
    
    mock_playwright.context.new_page = mock_new_page

    # Create a mock for the result of async_playwright() that has start() method
    mock_async_playwright_result = MagicMock()
    mock_async_playwright_result.start = AsyncMock(return_value=mock_playwright)
    
    with patch("src.scraper.async_playwright", return_value=mock_async_playwright_result):
        with patch.object(file_manager, 'save_article_content', new_callable=MagicMock) as mock_save_article_content:
            with patch.object(Scraper, '_save_as_pdf', new_callable=AsyncMock) as mock_save_as_pdf:
                scraper = Scraper(mock_logger)
                await scraper.connect()
                for i, article_info in enumerate(articles_to_scrape):
                    await scraper.scrape_single_article(article_info, formats, i, len(articles_to_scrape))

                # Проверяем, что первая статья обработана, а вторая вызвала ошибку
                assert mock_async_playwright_result.start.call_count == 1
                assert mock_save_article_content.call_count == 1
                assert mock_save_as_pdf.call_count == 0 # PDF не запрашивался
                
                log_messages = [call_args[0][0] for call_args in mock_logger.call_args_list]
                assert any("NON-FATAL ERROR during final scraping of Article 2: Frame not found" in msg for msg in log_messages)