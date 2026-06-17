"""Parser Registry — Central hub for all language parsers."""
from .python import PythonParser

# Smart JS/TS Parser with fallback
try:
    from .javascript_treesitter import JavaScriptParser
    JS_METHOD = "tree-sitter"
except ImportError:
    from .javascript_regex import JavaScriptParser
    JS_METHOD = "regex"

PARSER_REGISTRY = {
    '.py':    PythonParser,
    '.js':    JavaScriptParser,
    '.ts':    JavaScriptParser,
    '.jsx':   JavaScriptParser,
    '.tsx':   JavaScriptParser,
    # Add more languages here
}

PARSER_QUALITY = {
    '.py':    'ast-high',
    '.js':    JS_METHOD,
    '.ts':    JS_METHOD,
    '.jsx':   JS_METHOD,
    '.tsx':   JS_METHOD,
}


def get_parser(ext: str):
    return PARSER_REGISTRY.get(ext.lower())