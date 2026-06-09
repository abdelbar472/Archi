"""Parser registry — maps file extensions to parser classes."""
from .python import PythonParser
from .javascript import JavaScriptParser
from .go import GoParser
from .dart import DartParser
from .rust import RustParser
from .java import JavaParser
from .swift import SwiftParser
from .ruby import RubyParser
from .cpp import CppParser
from .csharp import CSharpParser
from .proto import ProtoParser

PARSER_REGISTRY = {
    '.py':    PythonParser,
    '.js':    JavaScriptParser,
    '.ts':    JavaScriptParser,
    '.jsx':   JavaScriptParser,
    '.tsx':   JavaScriptParser,
    '.go':    GoParser,
    '.dart':  DartParser,
    '.rs':    RustParser,
    '.java':  JavaParser,
    '.kt':    JavaParser,      # Kotlin uses same parser as Java
    '.swift': SwiftParser,
    '.rb':    RubyParser,
    '.cpp':   CppParser,
    '.cc':    CppParser,
    '.h':     CppParser,
    '.hpp':   CppParser,
    '.cs':    CSharpParser,
    '.proto': ProtoParser,
}

# Quality metadata for honest reporting
PARSER_QUALITY = {
    '.py':    'ast',
    '.js':    'regex',
    '.ts':    'regex',
    '.jsx':   'regex',
    '.tsx':   'regex',
    '.go':    'regex',
    '.dart':  'regex',
    '.rs':    'regex',
    '.java':  'regex',
    '.kt':    'regex',
    '.swift': 'regex',
    '.rb':    'regex',
    '.cpp':   'regex',
    '.cc':    'regex',
    '.h':     'regex',
    '.hpp':   'regex',
    '.cs':    'regex',
    '.proto': 'regex',
}
