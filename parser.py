from bs4 import BeautifulSoup
import config

def extract_toc_links(html_content):
    """
    Parses the initial Table of Contents HTML to extract article links.

    Args:
        html_content (str): The HTML content of the TOC page.

    Returns:
        list: A list of dictionaries, where each dictionary represents an article 
              with 'title', 'url', and 'original_order'.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    toc_div = soup.find('div', id='w_metadata_toc')
    if not toc_div:
        raise ValueError("Could not find the table of contents div with id 'w_metadata_toc'.")

    toc_links = []
    for i, link in enumerate(toc_div.select('ul li a')):
        href = link.get('href')
        text = link.get_text(strip=True)
        if href and text:
            full_url = f"{config.BASE_URL}{href}"
            toc_links.append({"title": text, "url": full_url, "original_order": i})
    return toc_links

def parse_article_page(iframe_html):
    """
    Parses the HTML of an article's iframe to find content and nested links.

    Args:
        iframe_html (str): The HTML content from within the article's iframe.

    Returns:
        tuple: A tuple containing:
            - BeautifulSoup object of the parsed HTML.
            - A list of new article dictionaries found in a nested index.
            - The hash of the main text content.
    """
    soup = BeautifulSoup(iframe_html, 'html.parser')
    content_div = soup.find('body')
    if not content_div:
        raise ValueError("Could not find body content in the iframe.")

    # Calculate content hash
    article_text = content_div.get_text(separator='\n', strip=True)
    content_hash = hash(article_text)

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
