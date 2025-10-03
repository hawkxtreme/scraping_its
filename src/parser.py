from . import parser_v1
from . import parser_v2

def get_parser_for_url(url):
    """
    Factory function to get the correct parser module for a given URL.
    """
    if "v8std" in url:
        return parser_v2
    else:
        return parser_v1