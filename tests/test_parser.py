import pytest
from bs4 import BeautifulSoup
from src.parser_v1 import (
    extract_toc_links,
    parse_article_page
)

@pytest.mark.unit
def test_extract_toc_links():
    """Тест извлечения ссылок из оглавления."""
    html = """
    <div id="w_metadata_toc">
        <ul>
            <li><a href="/db/article1">Article 1</a></li>
            <li><a href="/db/article2">Article 2</a></li>
            <li><a href="/db/subarticle1">Sub Article 1</a></li>
        </ul>
    </div>
    """
    links = extract_toc_links(html)
    
    assert len(links) == 3
    assert all(isinstance(link, dict) for link in links)
    assert all(set(link.keys()) == {"title", "url", "original_order"} for link in links)
    assert links[0]["title"] == "Article 1"
    assert links[1]["title"] == "Article 2"
    assert links[2]["title"] == "Sub Article 1"

@pytest.mark.unit
def test_parse_article_page():
    """Тест парсинга содержимого статьи."""
    html = """
    <html>
    <body>
        <h1>Test Article</h1>
        <p>Test paragraph</p>
        <div class="index">
            <a href="/db/nested1">Nested Article 1</a>
            <a href="/db/nested2">Nested Article 2</a>
        </div>
    </body>
    </html>
    """
    soup, nested_links, content_hash = parse_article_page(html)
    
    # Проверяем основной контент
    assert soup.find('h1').text == "Test Article"
    assert soup.find('p').text == "Test paragraph"
    
    # Проверяем вложенные ссылки
    assert len(nested_links) == 2
    assert {"title": "Nested Article 1", "url": "https://its.1c.ru/db/nested1"} in nested_links
    assert {"title": "Nested Article 2", "url": "https://its.1c.ru/db/nested2"} in nested_links
    
    # Проверяем хеш контента
    assert isinstance(content_hash, int)

@pytest.mark.unit
def test_parse_article_page_no_nested_links():
    """Тест парсинга статьи без вложенных ссылок."""
    html = """
    <html>
    <body>
        <h1>Test Article</h1>
        <p>Simple content</p>
    </body>
    </html>
    """
    soup, nested_links, content_hash = parse_article_page(html)
    
    assert len(nested_links) == 0
    assert isinstance(content_hash, int)
    assert soup.find('h1').text == "Test Article"

@pytest.mark.unit
def test_parse_article_page_empty():
    """Тест парсинга пустой статьи."""
    html = "<html><head></head></html>"
    with pytest.raises(ValueError, match="Could not find body content in the iframe."):
        parse_article_page(html)

@pytest.mark.unit
def test_extract_toc_links_invalid():
    """Тест извлечения ссылок из некорректного оглавления."""
    html = "<div>No table of contents here</div>"
    with pytest.raises(ValueError, match="Could not find the table of contents div with id 'w_metadata_toc'."):
        extract_toc_links(html)