import os
import shutil
import json
import markdownify

import config

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

def save_article_content(filename_base, formats, soup_content, article_info):
    """Saves the article content in the specified formats (excluding PDF)."""
    content_div = soup_content.find('body')
    if not content_div:
        return # Or raise an error

    if 'json' in formats or 'txt' in formats or 'markdown' in formats:
        article_text = content_div.get_text(separator='\n', strip=True)
        
        if 'json' in formats:
            path = os.path.join(config.JSON_DIR, f"{filename_base}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"title": article_info['title'], "url": article_info['url'], "content": article_text}, f, ensure_ascii=False, indent=4)
        
        if 'txt' in formats:
            path = os.path.join(config.TXT_DIR, f"{filename_base}.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(article_text)
                
        if 'markdown' in formats:
            path = os.path.join(config.MARKDOWN_DIR, f"{filename_base}.md")
            # Convert only the content_div to markdown
            md_content = markdownify.markdownify(str(content_div), heading_style="ATX")
            with open(path, "w", encoding="utf-8") as f:
                f.write(md_content)

def save_index_data(article_info):
    """Saves temporary index data for an article."""
    index_data = {
        "title": article_info["title"],
        "url": article_info["url"],
        "original_order": article_info.get("original_order", 9999)
    }
    # Use a hash of the URL for a unique, filesystem-safe filename
    index_filename = f"{hash(article_info['url'])}.json"
    path = os.path.join(config.TMP_INDEX_DIR, index_filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(index_data, f)

def load_and_sort_index():
    """Loads all temporary index files and returns a sorted list of articles."""
    final_articles_list = []
    for filename in os.listdir(config.TMP_INDEX_DIR):
        if filename.endswith('.json'):
            path = os.path.join(config.TMP_INDEX_DIR, filename)
            with open(path, "r", encoding="utf-8") as f:
                final_articles_list.append(json.load(f))
    
    # Sort by original order (from TOC), then by title as a fallback
    final_articles_list.sort(key=lambda x: (x.get('original_order', 9999), x['title']))
    return final_articles_list

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
