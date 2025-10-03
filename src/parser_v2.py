from bs4 import BeautifulSoup
from . import config

def extract_toc_links(html_content):
    """
    Parses the initial Table of Contents HTML to extract a hierarchical structure of article links for the new format.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    nav_tree_div = soup.find('div', id='w_metadata_navtree')
    if not nav_tree_div:
        raise ValueError("Could not find the nav tree div with id 'w_metadata_navtree'.")

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

    top_ul = nav_tree_div.find('ul')
    if not top_ul:
        return []
        
    return parse_ul(top_ul)

def parse_article_page(html_content):
    """
    Parses the HTML of an article's content to find the main text and nested links.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    content_div = soup.find('div', id='w_content')
    if not content_div:
        raise ValueError("Could not find content div with id 'w_content'.")

    # Calculate content hash
    article_text = content_div.get_text(separator='\n', strip=True)
    content_hash = hash(article_text)

    # Discover nested links
    nested_links = []
    # We assume that the links are in the main content area
    for link in content_div.find_all('a'):
        href = link.get('href')
        text = link.get_text(strip=True)
        if href and text:
            # We need to filter out links that are not articles
            if href.startswith('/db/'):
                full_url = f"{config.BASE_URL}{href}"
                nested_links.append({"title": text, "url": full_url})
    
    return soup, nested_links, content_hash
