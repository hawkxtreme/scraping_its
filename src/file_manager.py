import os
import shutil
import json
import re
from urllib.parse import urlparse
import markdownify

from . import config

def setup_output_directories():
    """Cleans and creates the necessary output directories."""
    if os.path.exists(config.OUTPUT_DIR):
        shutil.rmtree(config.OUTPUT_DIR)
    
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

def save_hierarchical_index(toc_tree):
    """Saves the hierarchical TOC tree to a JSON file."""
    index_file = os.path.join(config.TMP_INDEX_DIR, "_toc_tree.json")
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(toc_tree, f, ensure_ascii=False, indent=2)

def create_toc_and_meta(articles, formats):
    """Creates the _toc.md and _meta.json files."""
    # We need the original toc_tree to generate the markdown toc
    index_file = os.path.join(config.TMP_INDEX_DIR, "_toc_tree.json")
    if not os.path.exists(index_file):
        return
    with open(index_file, "r", encoding="utf-8") as f:
        toc_tree = json.load(f)

    create_markdown_toc(toc_tree, articles, formats)
    create_meta_json(articles, formats)

def create_markdown_toc(toc_tree, articles, formats):
    """Generates the _toc.md file."""
    url_to_filename = {article["url"]: article["filename_base"] for article in articles if "filename_base" in article}

    with open(os.path.join(config.OUTPUT_DIR, "_toc.md"), "w", encoding="utf-8") as f:
        f.write("# Оглавление\n\n")
        
        def write_nodes(nodes, indent_level=0):
            for node in nodes:
                filename_base = url_to_filename.get(node["url"])
                
                if filename_base:
                    f.write("    " * indent_level + f"*   **{node['title']}**\n")
                    for format in formats:
                        f.write("    " * (indent_level + 1) + f"*   [{format.upper()}](./{format}/{filename_base}.{format})\n")
                else:
                    f.write("    " * indent_level + f"*   **{node['title']}**\n")

                if node["children"]:
                    write_nodes(node["children"], indent_level + 1)

        write_nodes(toc_tree)

def create_meta_json(articles, formats):
    """Generates the _meta.json file."""
    with open(os.path.join(config.OUTPUT_DIR, "_meta.json"), "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)

def load_index_data():
    """Loads the hierarchical index, flattens it, and returns a list of articles to scrape."""
    index_file = os.path.join(config.TMP_INDEX_DIR, "_toc_tree.json")
    if not os.path.exists(index_file):
        return []
        
    with open(index_file, "r", encoding="utf-8") as f:
        toc_tree = json.load(f)

    flat_list = []
    def traverse(nodes, breadcrumbs):
        for node in nodes:
            article_data = {
                "title": node["title"],
                "url": node["url"],
                "breadcrumb": breadcrumbs + [node["title"]],
            }
            flat_list.append(article_data)
            if node["children"]:
                traverse(node["children"], breadcrumbs + [node["title"]])

    traverse(toc_tree, [])
    return flat_list

def get_index_path():
    """Returns the path to the temporary index directory."""
    return config.TMP_INDEX_DIR

def cleanup_temp_files():
    """Removes temporary directories."""
    if os.path.exists(config.TMP_INDEX_DIR):
        shutil.rmtree(config.TMP_INDEX_DIR)
