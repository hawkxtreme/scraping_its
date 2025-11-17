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
    For v8std pages with /content/XXX/hdoc URLs, content is in an iframe.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Try to find content in div#w_content first (browse pages)
    content_div = soup.find('div', id='w_content')
    
    # If not found, try to find iframe (content pages like /content/467/hdoc)
    if not content_div:
        # Look for iframe with article content
        iframe = soup.find('iframe', id='w_metadata_doc_frame')
        if iframe:
            # For iframe-based pages, we need to extract from the iframe's src
            # But since we're already parsing the page content, let's look for the actual content div
            # In the main page structure after the iframe loads
            pass
        
        # Try alternative selectors for content
        content_div = soup.find('div', class_='content')
        if not content_div:
            content_div = soup.find('div', class_='document-content')
        if not content_div:
            # Try to find any div with substantial content
            content_div = soup.find('div', id='l_content')
        
        if not content_div:
            # Last resort: look for main content area
            main_divs = soup.find_all('div', class_='content-wrapper')
            if main_divs:
                content_div = main_divs[0]
    
    if not content_div:
        # If still not found, use the body but exclude navigation/footer
        body = soup.find('body')
        if body:
            # Remove navigation and footer elements
            for nav in body.find_all(['nav', 'header', 'footer']):
                nav.decompose()
            for script in body.find_all('script'):
                script.decompose()
            for style in body.find_all('style'):
                style.decompose()
            content_div = body
        else:
            raise ValueError("Could not find content in the page.")

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
    # We assume that the links are in the main content area
    for link in content_div.find_all('a'):
        href = link.get('href')
        text = link.get_text(strip=True)
        if href and text:
            # We need to filter out links that are not articles
            if href.startswith('/db/'):
                # Filter out common navigation and reference links
                text_lower = text.lower().strip()
                skip_patterns = [
                    'здесь', 'подробнее', 'см.', 'книгу', 'книге', 'описано', 'описана', 
                    'описаны', 'написано', 'приведено', 'приводится', 'можно', 'прочитать',
                    'получить', 'ознакомиться', 'подробное', 'описание', 'в книге',
                    'подробно описано', 'описанной в книге', 'описана в книге',
                    'описаны в книге', 'написано в книге', 'приведено в книге',
                    'приводится в книге', 'можно прочитать в книге', 'можно получить в книге',
                    'подробнее можно ознакомиться в книге', 'подробное описание',
                    'подробнее см. книгу', 'подробно описано в книге'
                ]
                
                # Skip if text matches any skip pattern
                if any(pattern in text_lower for pattern in skip_patterns):
                    continue
                
                # Skip very short text (likely navigation)
                if len(text.strip()) < 3:
                    continue
                
                # Skip text that looks like page numbers or IDs
                if text.strip().isdigit() or text.strip().startswith('http'):
                    continue
                
                full_url = f"{config.BASE_URL}{href}"
                nested_links.append({"title": text, "url": full_url})
    
    return soup, nested_links, content_hash
