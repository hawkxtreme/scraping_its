import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock, AsyncMock
from src import file_manager

def test_cleanup_temp_files(temp_dir):
    """Тест очистки временных файлов."""
    # Создаем временную директорию для теста
    tmp_index_dir = os.path.join(str(temp_dir), "tmp_index")
    os.makedirs(tmp_index_dir, exist_ok=True)
    
    # Создаем тестовый файл внутри временной директории
    test_file = os.path.join(tmp_index_dir, "test.txt")
    with open(test_file, 'w') as f:
        f.write("test")
    
    # Проверяем, что файл существует
    assert os.path.exists(test_file)
    
    # Имитируем config.TMP_INDEX_DIR для теста
    with patch('src.file_manager.config.TMP_INDEX_DIR', tmp_index_dir):
        file_manager.cleanup_temp_files()
        
        # Проверяем, что временная директория удалена
        assert not os.path.exists(tmp_index_dir)

def test_get_index_path():
    """Тест получения пути к индексу."""
    from src import config
    index_path = file_manager.get_index_path()
    assert index_path == config.TMP_INDEX_DIR

def test_save_article_json_sanitized_filename_edge_cases(temp_dir, monkeypatch):
    """Тест сохранения статьи в формате JSON с граничными случаями очистки имен файлов."""
    import re
    from urllib.parse import urlparse
    
    article_data = {
        'url': "http://example.com/path/with?query=param&special#fragment",
        'title': "Test Title",
        'content': "Some content."
    }
    
    json_output_dir = temp_dir / "json_output"
    monkeypatch.setattr('src.config.JSON_DIR', str(json_output_dir))
    os.makedirs(json_output_dir, exist_ok=True)

    file_manager.save_article_json(article_data)

    # Рассчитываем ожидаемое имя файла вручную
    url_path = urlparse(article_data['url']).path
    safe_filename = re.sub(r'[^\w\-_.]', '_', url_path.strip('/'))  # path/with -> path_with
    expected_filename = f"{safe_filename}.json"
    
    json_path = json_output_dir / expected_filename
    assert json_path.exists()

def test_save_article_content_txt_only(temp_dir, monkeypatch):
    """Тест сохранения статьи только в формате txt."""
    from bs4 import BeautifulSoup
    import re
    from urllib.parse import urlparse
    
    filename_base = "test_article"
    formats = ['txt']
    soup = BeautifulSoup("<p>Test content</p>", 'html.parser')
    article_info = {
        'url': "https://its.1c.ru/db/test_article",
        'title': "Test Article"
    }
    
    txt_output_dir = temp_dir / "txt_output"
    monkeypatch.setattr('src.config.TXT_DIR', str(txt_output_dir))
    os.makedirs(txt_output_dir, exist_ok=True)

    file_manager.save_article_content(filename_base, formats, soup, article_info)

    txt_path = txt_output_dir / f"{filename_base}.txt"
    assert txt_path.exists()
    
    # Проверяем содержимое
    with open(txt_path, 'r', encoding='utf-8') as f:
        content = f.read()
        assert "Test Article" in content
        assert "https://its.1c.ru/db/test_article" in content
        assert "Test content" in content

def test_save_article_content_json_only(temp_dir, monkeypatch):
    """Тест сохранения статьи только в формате json."""
    from bs4 import BeautifulSoup
    import json
    
    filename_base = "test_article"
    formats = ['json']
    soup = BeautifulSoup("<p>Test content</p>", 'html.parser')
    article_info = {
        'url': "https://its.1c.ru/db/test_article",
        'title': "Test Article"
    }
    
    json_output_dir = temp_dir / "json_output"
    monkeypatch.setattr('src.config.JSON_DIR', str(json_output_dir))
    os.makedirs(json_output_dir, exist_ok=True)

    file_manager.save_article_content(filename_base, formats, soup, article_info)

    json_path = json_output_dir / f"{filename_base}.json"
    assert json_path.exists()
    
    # Проверяем содержимое
    with open(json_path, 'r', encoding='utf-8') as f:
        content = json.load(f)
        assert content['title'] == "Test Article"
        assert content['url'] == "https://its.1c.ru/db/test_article"
        assert "Test content" in content['content']

def test_save_article_content_markdown_only(temp_dir, monkeypatch):
    """Тест сохранения статьи только в формате markdown."""
    from bs4 import BeautifulSoup
    import re
    from urllib.parse import urlparse
    
    filename_base = "test_article"
    formats = ['markdown']
    soup = BeautifulSoup("<h1>Test Header</h1><p>Test content</p>", 'html.parser')
    article_info = {
        'url': "https://its.1c.ru/db/test_article",
        'title': "Test Article"
    }
    
    md_output_dir = temp_dir / "markdown_output"
    monkeypatch.setattr('src.config.MARKDOWN_DIR', str(md_output_dir))
    os.makedirs(md_output_dir, exist_ok=True)

    file_manager.save_article_content(filename_base, formats, soup, article_info)

    md_path = md_output_dir / f"{filename_base}.md"
    assert md_path.exists()
    
    # Проверяем содержимое
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
        assert "# Test Header" in content or "Test Header" in content  # markdownify может по-разному обрабатывать заголовки
        assert "Test content" in content

def test_load_index_data_empty():
    """Тест загрузки пустого индекса."""
    with patch('src.file_manager.config.TMP_INDEX_DIR', "/nonexistent"):
        result = file_manager.load_index_data()
        assert result == []

def test_load_and_sort_index_empty():
    """Тест загрузки и сортировки пустого индекса."""
    with patch('src.file_manager.config.TMP_INDEX_DIR', "/nonexistent"):
        result = file_manager.load_and_sort_index()
        assert result == []