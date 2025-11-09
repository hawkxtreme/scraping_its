from . import parser_v1
from . import parser_v3

def get_parser_for_url(url):
    """
    Factory function to get the correct parser module for a given URL.
    Автоматически определяет подходящий парсер на основе URL.
    
    Parser V1: Classic TOC structure (w_metadata_toc) - БСП, v8std
    Parser V3: Universal tree-based navigation - v8327doc, metod8dev, metod81
    """
    url_lower = url.lower()
    
    # Parser V3: Universal tree-based parser
    # Для v8327doc, method_dev, metod8dev, metod81 и других с .tree навигацией
    if ('/db/v8327' in url_lower or 
        '/section/dev/' in url_lower or
        '/db/metod8' in url_lower or
        '/db/metod81' in url_lower):
        return parser_v3
    
    # Parser V1: для БСП, v8std и других с классической структурой w_metadata_toc
    else:
        return parser_v1