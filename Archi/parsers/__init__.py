"""Parser package initialization."""
from .registry import PARSER_REGISTRY, PARSER_QUALITY, get_parser

__all__ = ['PARSER_REGISTRY', 'PARSER_QUALITY', 'get_parser', 'register_parser']

def register_parser(ext: str, parser_class, quality: str = "medium"):
    """Allow dynamic registration of new parsers."""
    PARSER_REGISTRY[ext] = parser_class
    PARSER_QUALITY[ext] = quality