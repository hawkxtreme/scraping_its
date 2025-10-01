import os
import json
import re
import pytest
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from src import file_manager
from src import config

@pytest.mark.unit
def test_setup_output_directories(temp_dir, monkeypatch):
    """Тест создания структуры директорий."""
    # Подменяем пути на временные
    monkeypatch.setattr(config, "OUTPUT_DIR", str(temp_dir))
    monkeypatch.setattr(config, "BASE_ARTICLES_DIR", str(temp_dir / "articles"))
    monkeypatch.setattr(config, "JSON_DIR", str(temp_dir / "articles/json"))
    monkeypatch.setattr(config, "PDF_DIR", str(temp_dir / "articles/pdf"))
    monkeypatch.setattr(config, "TXT_DIR", str(temp_dir / "articles/txt"))
    monkeypatch.setattr(config, "MARKDOWN_DIR", str(temp_dir / "articles/markdown"))
    monkeypatch.setattr(config, "TMP_INDEX_DIR", str(temp_dir / "tmp_index"))

    # Вызываем функцию создания директорий
    file_manager.setup_output_directories()

    # Проверяем, что все директории созданы
    assert os.path.exists(temp_dir / "articles")
    assert os.path.exists(temp_dir / "articles/json")
    assert os.path.exists(temp_dir / "articles/pdf")
    assert os.path.exists(temp_dir / "articles/txt")
    assert os.path.exists(temp_dir / "articles/markdown")
    assert os.path.exists(temp_dir / "tmp_index")

@pytest.mark.unit
def test_cleanup_temp_files(temp_dir, monkeypatch):
    """Тест очистки временных файлов."""
    # Создаем временные файлы и директории
    tmp_dir = temp_dir / "tmp"
    tmp_dir.mkdir()
    (tmp_dir / "test.tmp").write_text("test")
    
    monkeypatch.setattr(config, "TMP_INDEX_DIR", str(tmp_dir))
    
    # Вызываем функцию очистки
    file_manager.cleanup_temp_files()
    
    # Проверяем, что временные файлы удалены
    assert not os.path.exists(tmp_dir)

@pytest.mark.unit
def test_save_index_data(temp_dir, monkeypatch):
    """Тест сохранения данных индекса."""
    # Подготавливаем тестовые данные
    test_data = [
        {"url": "http://test.com/1", "title": "Test 1"},
        {"url": "http://test.com/2", "title": "Test 2"}
    ]
    
    index_dir = temp_dir / "tmp_index"
    monkeypatch.setattr(config, "TMP_INDEX_DIR", str(index_dir))
    
    # Сохраняем данные
    file_manager.save_index_data(test_data)
    
    # Проверяем, что данные сохранились корректно
    index_file = index_dir / "index.json"
    assert index_file.exists()
    saved_data = json.loads(index_file.read_text())
    assert saved_data == test_data

@pytest.mark.unit
def test_load_index_data(temp_dir, monkeypatch):
    """Тест загрузки данных индекса."""
    # Подготавливаем тестовые данные
    test_data = [
        {"url": "http://test.com/1", "title": "Test 1"},
        {"url": "http://test.com/2", "title": "Test 2"}
    ]
    
    index_dir = temp_dir / "tmp_index"
    index_dir.mkdir()
    index_file = index_dir / "index.json"
    index_file.write_text(json.dumps(test_data))
    
    monkeypatch.setattr(config, "TMP_INDEX_DIR", str(index_dir))
    
    # Загружаем данные
    loaded_data = file_manager.load_index_data()
    
    # Проверяем, что данные загрузились корректно
    assert loaded_data == test_data

@pytest.mark.unit
def test_load_index_data_empty(temp_dir, monkeypatch):
    """Тест загрузки данных индекса, когда файл индекса отсутствует."""
    index_dir = temp_dir / "tmp_index"
    monkeypatch.setattr(config, "TMP_INDEX_DIR", str(index_dir))
    loaded_data = file_manager.load_index_data()
    assert loaded_data == []

@pytest.mark.unit
def test_get_index_path(temp_dir, monkeypatch):
    """Тест получения пути к временной директории индекса."""
    expected_path = str(temp_dir / "tmp_index")
    monkeypatch.setattr(config, "TMP_INDEX_DIR", expected_path)
    assert file_manager.get_index_path() == expected_path

@pytest.mark.unit
def test_save_article_content_all_formats(temp_dir, monkeypatch):
    """Тест сохранения содержимого статьи во всех поддерживаемых форматах."""
    # Подготавливаем тестовые данные
    filename_base = "test_article"
    formats = ['json', 'txt', 'markdown']
    article_info = {
        "url": "http://test.com/article",
        "title": "Test Article",
    }
    html_content = "<h1>Test Article</h1><p>Test content</p>"
    soup = BeautifulSoup(html_content, 'html.parser')

    # Подменяем пути на временные
    monkeypatch.setattr(config, "JSON_DIR", str(temp_dir / "json"))
    monkeypatch.setattr(config, "TXT_DIR", str(temp_dir / "txt"))
    monkeypatch.setattr(config, "MARKDOWN_DIR", str(temp_dir / "markdown"))
    
    # Создаём директории
    os.makedirs(temp_dir / "json")
    os.makedirs(temp_dir / "txt")
    os.makedirs(temp_dir / "markdown")

    # Сохраняем в разных форматах
    file_manager.save_article_content(filename_base, formats, soup, article_info)

    # Проверяем JSON
    json_file = temp_dir / "json" / f"{filename_base}.json"
    assert json_file.exists()
    saved_json = json.loads(json_file.read_text())
    assert saved_json['title'] == article_info['title']
    assert saved_json['url'] == article_info['url']
    assert "Test content" in saved_json['content']
    
    # Проверяем TXT
    txt_file = temp_dir / "txt" / f"{filename_base}.txt"
    assert txt_file.exists()
    saved_txt = txt_file.read_text()
    assert f"Title: {article_info['title']}" in saved_txt
    assert f"URL: {article_info['url']}" in saved_txt
    assert "Test content" in saved_txt

    # Проверяем Markdown
    md_file = temp_dir / "markdown" / f"{filename_base}.md"
    assert md_file.exists()
    saved_md = md_file.read_text()
    assert "# Test Article" in saved_md
    assert "Test content" in saved_md

@pytest.mark.unit
def test_save_article_json(temp_dir, monkeypatch):
    """Тест сохранения статьи в формате JSON."""
    article_data = {
        'url': "http://example.com/test",
        'title': "Test Title",
        'content': "Some content."
    }
    monkeypatch.setattr(config, "JSON_DIR", str(temp_dir / "json_output"))
    os.makedirs(temp_dir / "json_output")

    file_manager.save_article_json(article_data)

    expected_filename = "test.json"
    json_path = temp_dir / "json_output" / expected_filename
    assert json_path.exists()
    with open(json_path, 'r', encoding='utf-8') as f:
        loaded_data = json.load(f)
    assert loaded_data == article_data

@pytest.mark.unit
def test_save_article_json_sanitized_filename(temp_dir, monkeypatch):
    """Тест сохранения статьи в формате JSON с очищенным именем файла."""
    article_data = {
        'url': "http://example.com/path/with/!@#$special%^&*chars.html",
        'title': "Test Title",
        'content': "Some content."
    }
    
    # Создаем подкаталог для JSON файлов
    json_output_dir = temp_dir / "json_output"
    monkeypatch.setattr(config, "JSON_DIR", str(json_output_dir))
    os.makedirs(json_output_dir, exist_ok=True)

    file_manager.save_article_json(article_data)

    # Рассчитываем ожидаемое имя файла вручную так же, как это делает функция
    url_path = urlparse(article_data['url']).path  # /path/with/!@#$special%^&*chars.html
    safe_filename = re.sub(r'[^\w\-_.]', '_', url_path.strip('/'))  # path_with____special____chars_html
    expected_filename = f"{safe_filename}.json"  # path_with____special____chars_html.json
    
    json_path = json_output_dir / expected_filename
    assert json_path.exists()

@pytest.mark.unit
def test_save_article_json_no_dir(temp_dir, monkeypatch):
    """Тест сохранения статьи в формате JSON, когда директория не существует."""
    article_data = {
        'url': "http://example.com/test",
        'title': "Test Title",
        'content': "Some content."
    }
    monkeypatch.setattr(config, "JSON_DIR", str(temp_dir / "json_output"))

    file_manager.save_article_json(article_data)

    json_path = temp_dir / "json_output" / "test.json"
    assert json_path.exists()
