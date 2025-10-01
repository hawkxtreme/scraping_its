import os
import shutil
import json
import re
from urllib.parse import urlparse
import markdownify

from . import config

def setup_output_directories():
    """Cleans and creates the necessary output directories."""
    if os.path.exists(config.BASE_ARTICLES_DIR):
        shutil.rmtree(config.BASE_ARTICLES_DIR)
    if os.path.exists(config.TMP_INDEX_DIR):
        shutil.rmtree(config.TMP_INDEX_DIR)
    
    os.makedirs(config.JSON_DIR, exist_ok=True)
    os.makedirs(config.PDF_DIR, exist_ok=True)
    os.makedirs(config.TXT_DIR, exist_ok=True)
    os.makedirs(config.MARKDOWN_DIR, exist_ok=True)
    os.makedirs(config.TMP_INDEX_DIR, exist_ok=True)

def save_article_json(article_data):
    """Save article in JSON format."""
    if not os.path.exists(config.JSON_DIR):
        os.makedirs(config.JSON_DIR)

    # Get just the path component of the URL for the filename
    url_path = urlparse(article_data['url']).path
    safe_filename = re.sub(r'[^\w\-_.]', '_', url_path.strip('/'))
    
    json_file = os.path.join(config.JSON_DIR, f"{safe_filename}.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(article_data, f, ensure_ascii=False, indent=2)

def _save_article_json_and_txt_legacy(content, article_info):
    """Save article content in both JSON and TXT formats."""
    article_data = {
        'url': article_info['url'],
        'title': article_info['title'],
        'content': content
    }
    save_article_json(article_data)

    # TXT format
    if not os.path.exists(config.TXT_DIR):
        os.makedirs(config.TXT_DIR)
    
    # Get just the path component of the URL for the filename
    url_path = urlparse(article_info['url']).path
    safe_filename = re.sub(r'[^\w\-_.]', '_', url_path.strip('/'))
    
    txt_file = os.path.join(config.TXT_DIR, f"{safe_filename}.txt")
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(f"Title: {article_info['title']}\n")
        f.write(f"URL: {article_info['url']}\n\n")
        f.write(content)
def save_article_content(filename_base, formats, soup, article_info):
    """
    Сохраняет статью в указанных форматах (txt, json, markdown, pdf) по имени файла.
    - filename_base: базовое имя файла (без расширения)
    - formats: список форматов (например, ['txt', 'json', 'markdown'])
    - soup: BeautifulSoup-объект с содержимым статьи
    - article_info: словарь с метаданными статьи
    """
    text_content = soup.get_text(separator='\n', strip=True)
    article_data = {
        'url': article_info['url'],
        'title': article_info['title'],
        'content': text_content
    }

    # JSON
    if 'json' in formats:
        json_file = os.path.join(config.JSON_DIR, f"{filename_base}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(article_data, f, ensure_ascii=False, indent=2)

    # TXT
    if 'txt' in formats:
        txt_file = os.path.join(config.TXT_DIR, f"{filename_base}.txt")
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"Title: {article_info['title']}\n")
            f.write(f"URL: {article_info['url']}\n\n")
            f.write(text_content)

    # Markdown
    if 'markdown' in formats:
        md_file = os.path.join(config.MARKDOWN_DIR, f"{filename_base}.md")
        md_content = markdownify.markdownify(str(soup), heading_style="ATX")
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)

    # PDF сохраняется отдельно через scraper._save_as_pdf

def save_index_data(articles_list):
    """Saves temporary index data for articles."""
    os.makedirs(config.TMP_INDEX_DIR, exist_ok=True)
    index_file = os.path.join(config.TMP_INDEX_DIR, "index.json")
    
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(articles_list, f, ensure_ascii=False, indent=2)

def load_and_sort_index():
    """Loads the index file and returns the list of articles."""
    index_file = os.path.join(config.TMP_INDEX_DIR, "index.json")
    if not os.path.exists(index_file):
        return []
        
    with open(index_file, "r", encoding="utf-8") as f:
        return json.load(f)

def cleanup_temp_files():
    """Removes temporary directories."""
    if os.path.exists(config.TMP_INDEX_DIR):
        shutil.rmtree(config.TMP_INDEX_DIR)

def get_index_path():
    """Returns the path to the temporary index directory."""
    return config.TMP_INDEX_DIR

def load_index_data():
    """Loads and sorts the index data."""
    return load_and_sort_index()
