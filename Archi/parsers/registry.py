"""Parser Registry — Smart dispatcher with backward compatibility"""
from pathlib import Path
from typing import Optional, Type

from .base import BaseParser


PARSER_REGISTRY = {}
PARSER_QUALITY = {}


def register_parser(ext: str, parser_class: Type[BaseParser], priority: int = 1, quality: str = "medium"):
    PARSER_REGISTRY[ext.lower()] = (parser_class, priority)
    PARSER_QUALITY[ext.lower()] = quality


def get_parser(ext: str):
    ext = ext.lower()
    entry = PARSER_REGISTRY.get(ext)
    if entry:
        parser_cls, _ = entry
        return parser_cls
    return None


def get_parser_for_file(file_path: Path, graph) -> Optional[BaseParser]:
    ext = file_path.suffix.lower()
    parser_cls = get_parser(ext)
    if parser_cls:
        return parser_cls(graph)
    return None


# ==================== Registration ====================

# JavaScript / TypeScript (subfolder)
try:
    from .javascript.javascript_treesitter import JavaScriptParser
    for e in ['.js', '.jsx', '.ts', '.tsx']:
        register_parser(e, JavaScriptParser, priority=10, quality="tree-sitter")
    print("✅ JavaScript Tree-sitter parser loaded successfully")
except ImportError as e:
    print(f"⚠️ Tree-sitter JS parser failed: {e}")
    try:
        from .javascript.javascript_regex import JavaScriptParser
        for e in ['.js', '.jsx', '.ts', '.tsx']:
            register_parser(e, JavaScriptParser, priority=5, quality="regex")
        print("✅ JavaScript Regex fallback loaded")
    except ImportError:
        print("❌ No JavaScript parser available")

# Python
try:
    from .python.python_ast import PythonASTParser
    register_parser('.py', PythonASTParser, priority=10, quality="ast-high")
    print("✅ Python AST parser loaded")
except ImportError as e:
    print(f"⚠️ Python parser failed: {e}")


if __name__ == "__main__":
    print("Registered extensions:", list(PARSER_REGISTRY.keys()))