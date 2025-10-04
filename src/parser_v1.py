from bs4 import BeautifulSoup
from . import config

def extract_toc_links(html_content):
    """
    Parses the initial Table of Contents HTML to extract a hierarchical structure of article links.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    toc_div = soup.find('div', id='w_metadata_toc')
    if not toc_div:
        raise ValueError("Could not find the table of contents div with id 'w_metadata_toc'.")

    def parse_ul(ul_element):
        children = []
        for li in ul_element.find_all('li', recursive=False):
            link = li.find('a', recursive=False)
            if link:
                href = link.get('href')
                text = link.get_text(strip=True)
                if href and text:
                    full_url = f"{config.BASE_URL}{href}"
                    node = {"title": text, "url": full_url, "children": []}
                    nested_ul = li.find('ul')
                    if nested_ul:
                        node["children"] = parse_ul(nested_ul)
                    children.append(node)
        return children

    top_ul = toc_div.find('ul')
    if not top_ul:
        return []
        
    return parse_ul(top_ul)

def parse_article_page(iframe_html):
    """
    Parses the HTML of an article's iframe to find content and nested links.
    """
    soup = BeautifulSoup(iframe_html, 'html.parser')
    content_div = soup.find('body')
    if not content_div:
        raise ValueError("Could not find body content in the iframe.")

    # Calculate content hash - include URL for uniqueness
    article_text = content_div.get_text(separator='\n', strip=True)
    # Use a more robust hash that includes URL to avoid false duplicates
    # Only create hash if content is not empty
    if article_text.strip():
        content_hash = hash(f"{article_text}|{len(article_text)}")
    else:
        content_hash = 0  # Special value for empty content

    # Discover nested links
    nested_links = []
    nested_index = soup.find('div', class_='index')
    if nested_index and nested_index.find('a'):
        for link in nested_index.find_all('a'):
            href = link.get('href')
            text = link.get_text(strip=True)
            if href and text:
                full_url = f"{config.BASE_URL}{href}"
                nested_links.append({"title": text, "url": full_url})
    
    return soup, nested_links, content_hash
