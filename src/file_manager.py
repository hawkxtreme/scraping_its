import os
import shutil
import json
import re
from urllib.parse import urlparse
import markdownify

from . import config

def setup_output_directories(formats):
    """Cleans and creates the necessary output directories based on specified formats."""
    # Create base output directory if it doesn't exist
    os.makedirs(config.get_output_dir(), exist_ok=True)

    # Clean and create directories for specified formats
    format_map = {
        'json': config.get_json_dir(),
        'pdf': config.get_pdf_dir(),
        'txt': config.get_txt_dir(),
        'markdown': config.get_markdown_dir(),
    }

    for fmt in formats:
        dir_path = format_map.get(fmt)
        if dir_path and os.path.exists(dir_path):
            shutil.rmtree(dir_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

    # Ensure tmp_index directory exists
    os.makedirs(config.get_tmp_index_dir(), exist_ok=True)

def save_article_json(article_data):
    """Save article in JSON format."""
    json_dir = config.get_json_dir()
    if not os.path.exists(json_dir):
        os.makedirs(json_dir)

    # Get just the path component of the URL for the filename
    url_path = urlparse(article_data['url']).path
    safe_filename = re.sub(r'[^\w\-_.]', '_', url_path.strip('/'))
    
    json_file = os.path.join(json_dir, f"{safe_filename}.json")
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
    txt_dir = config.get_txt_dir()
    if not os.path.exists(txt_dir):
        os.makedirs(txt_dir)
    
    # Get just the path component of the URL for the filename
    url_path = urlparse(article_info['url']).path
    safe_filename = re.sub(r'[^\w\-_.]', '_', url_path.strip('/'))
    
    txt_file = os.path.join(txt_dir, f"{safe_filename}.txt")
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
        json_file = os.path.join(config.get_json_dir(), f"{filename_base}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(article_data, f, ensure_ascii=False, indent=2)

    # TXT
    if 'txt' in formats:
        txt_file = os.path.join(config.get_txt_dir(), f"{filename_base}.txt")
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"Title: {article_info['title']}\n")
            f.write(f"URL: {article_info['url']}\n\n")
            f.write(text_content)

    # Markdown
    if 'markdown' in formats:
        md_file = os.path.join(config.get_markdown_dir(), f"{filename_base}.md")
        md_content = markdownify.markdownify(str(soup), heading_style="ATX")
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)

    # PDF сохраняется отдельно через scraper._save_as_pdf

def save_hierarchical_index(toc_tree):
    """Saves the hierarchical TOC tree to a JSON file."""
    index_file = os.path.join(config.get_tmp_index_dir(), "_toc_tree.json")
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(toc_tree, f, ensure_ascii=False, indent=2)

def create_toc_and_meta(articles, formats):
    """Creates the _toc.md and _meta.json files."""
    # We need the original toc_tree to generate the markdown toc
    index_file = os.path.join(config.get_tmp_index_dir(), "_toc_tree.json")
    if not os.path.exists(index_file):
        return
    with open(index_file, "r", encoding="utf-8") as f:
        toc_tree = json.load(f)

    create_markdown_toc(toc_tree, articles, formats)
    create_meta_json(articles, formats)


def create_markdown_toc(toc_tree, articles, formats):
    """Generates the _toc.md file."""
    url_to_filename = {article["url"]: article["filename_base"] for article in articles if "filename_base" in article}

    with open(os.path.join(config.get_output_dir(), "_toc.md"), "w", encoding="utf-8") as f:
        f.write("# Оглавление\n\n")
        
        def write_nodes(nodes, indent_level=0):
            for node in nodes:
                filename_base = url_to_filename.get(node["url"])
                
                if filename_base:
                    f.write("    " * indent_level + f"*   **{node['title']}**\n")
                    for format in formats:
                        # Correct relative path for the new structure
                        f.write("    " * (indent_level + 1) + f"*   [{format.upper()}](./{format}/{filename_base}.{format})\n")
                else:
                    f.write("    " * indent_level + f"*   **{node['title']}**\n")

                if node["children"]:
                    write_nodes(node["children"], indent_level + 1)

        write_nodes(toc_tree)

def create_meta_json(articles, formats):
    """Generates the _meta.json file."""
    with open(os.path.join(config.get_output_dir(), "_meta.json"), "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)

def load_index_data():
    """Loads the hierarchical index, flattens it, and returns a list of articles to scrape."""
    index_file = os.path.join(config.get_tmp_index_dir(), "_toc_tree.json")
    if not os.path.exists(index_file):
        return []
        
    with open(index_file, "r", encoding="utf-8") as f:
        toc_tree = json.load(f)

    flat_list = []
    # Helper to sanitize titles for use in filenames
    def sanitize_title(title):
        # Remove invalid characters for filenames
        sanitized = re.sub(r'[<>:"/\\|?*]', '', title)
        # Replace long sequences of whitespace with a single underscore
        sanitized = re.sub(r'\s+', '_', sanitized)
        # Truncate to a reasonable length
        return sanitized[:100]

    def traverse(nodes, breadcrumbs, counter):
        for node in nodes:
            # Only process nodes that have a URL (i.e., are articles)
            if "url" in node and node["url"]:
                # Format index with zero padding
                index_str = str(counter).zfill(4) # e.g., 0001, 0002
                sanitized_title = sanitize_title(node["title"])
                filename_base = f"{index_str}_{sanitized_title}"

                article_data = {
                    "index": counter,
                    "filename_base": filename_base,
                    "title": node["title"],
                    "url": node["url"],
                    "breadcrumb": breadcrumbs + [node["title"]],
                }
                flat_list.append(article_data)
                counter += 1
            
            # Recursively process children, carrying the counter forward
            if "children" in node and node["children"]:
                counter = traverse(node["children"], breadcrumbs + [node["title"]], counter)
        return counter

    traverse(toc_tree, [], 1) # Start indexing from 1
    return flat_list

def get_index_path():
    """Returns the path to the temporary index directory."""
    return config.get_tmp_index_dir()

def cleanup_temp_files():
    """Removes temporary directories."""
    tmp_index_dir = config.get_tmp_index_dir()
    if os.path.exists(tmp_index_dir):
        shutil.rmtree(tmp_index_dir)
