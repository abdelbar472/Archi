"""Parser Registry — Central hub for all language parsers."""
from .python import PythonParser
# Import other parsers only when they are ready (to avoid import errors)
# from .javascript import JavaScriptParser
# from .go import GoParser
# ... etc.

PARSER_REGISTRY = {
    '.py':    PythonParser,
    # '.js':    JavaScriptParser,
    # '.ts':    JavaScriptParser,
    # '.jsx':   JavaScriptParser,
    # '.tsx':   JavaScriptParser,
    # '.go':    GoParser,
    # '.dart':  DartParser,
    # '.rs':    RustParser,
    # '.java':  JavaParser,
    # '.kt':    JavaParser,
    # '.swift': SwiftParser,
    # '.rb':    RubyParser,
    # '.cpp':   CppParser,
    # '.cs':    CSharpParser,
    # '.proto': ProtoParser,
}

# Quality levels for reporting
PARSER_QUALITY = {
    '.py':    'ast-high',
    # '.js':    'regex-medium',
    # '.go':    'regex-medium',
    # Add others as implemented
}


def register_parser(ext: str, parser_class, quality: str = "medium"):
    """Allow dynamic registration of new parsers."""
    PARSER_REGISTRY[ext] = parser_class
    PARSER_QUALITY[ext] = quality


def get_parser(ext: str):
    """Safe getter."""
    return PARSER_REGISTRY.get(ext.lower())