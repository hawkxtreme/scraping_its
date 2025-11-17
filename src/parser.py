from . import parser_v1
from . import parser_v2

def detect_parser_type(html_content):
    """
    Automatically detects which parser to use based on the HTML structure.
    
    Returns:
        str: 'v1' or 'v2' based on detected structure
    """
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Check for v2 indicators (newer format)
    if soup.find('div', id='w_metadata_navtree'):
        return 'v2'
    
    # Check for v1 indicators (older format)
    if soup.find('div', id='w_metadata_toc'):
        return 'v1'
    
    # Additional heuristics for v2 format
    if (soup.find('div', id='w_content') or 
        soup.find('iframe', id='w_metadata_doc_frame') or
        soup.find('div', class_='content-wrapper')):
        return 'v2'
    
    # Additional heuristics for v1 format
    if soup.find('div', class_='index'):
        return 'v1'
    
    # Default to v2 for unknown structures (more flexible)
    return 'v2'

def get_parser_for_url(url):
    """
    Factory function to get the correct parser module for a given URL.
    Uses automatic detection for unknown URL patterns.
    """
    # Known patterns - use direct mapping
    if "v8std" in url or "v8327doc" in url:
        return parser_v2
    
    # For unknown patterns, we'll need to detect from content
    # This will be handled in the scraper by calling detect_parser_type first
    return None  # Indicates need for content-based detection

def get_parser_by_type(parser_type):
    """
    Get parser module by type string.
    
    Args:
        parser_type (str): 'v1' or 'v2'
        
    Returns:
        Module: The appropriate parser module
    """
    if parser_type == 'v1':
        return parser_v1
    elif parser_type == 'v2':
        return parser_v2
    else:
        raise ValueError(f"Unknown parser type: {parser_type}")