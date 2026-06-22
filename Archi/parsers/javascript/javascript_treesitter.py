"""Universal JavaScript/TypeScript Tree-sitter Parser for Archi"""
import re
from pathlib import Path
from typing import Optional, List, Dict

try:
    from tree_sitter import Language, Parser
    import tree_sitter_javascript
    import tree_sitter_typescript
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False

from ..base import BaseParser


NESTJS_CLASS_DECORATORS = {
    'Controller', 'Injectable', 'Service', 'Module', 'Guard', 'Interceptor',
    'Pipe', 'Resolver', 'Middleware', 'Catch', 'WebSocketGateway'
}

NESTJS_METHOD_DECORATORS = {'Get', 'Post', 'Put', 'Delete', 'Patch', 'Options', 'Head', 'All',
                           'MessagePattern', 'EventPattern', 'Query', 'Mutation', 'Subscription'}

JS_NOISE = {'console', 'process', 'require', 'module', 'exports', 'window', 'document', 'global'}


class JavaScriptParser(BaseParser):
    METHOD = "tree-sitter-universal"

    def __init__(self, graph):
        super().__init__(graph)
        self.js_parser = None
        self.ts_parser = None
        if TREE_SITTER_AVAILABLE:
            self._init_tree_sitter()

    def _init_tree_sitter(self):
        try:
            js_language = Language(tree_sitter_javascript.language())
            ts_language = Language(tree_sitter_typescript.language_typescript())
            
            try:
                # Modern API (>=0.22)
                self.js_parser = Parser(js_language)
                self.ts_parser = Parser(ts_language)
            except TypeError:
                # Legacy API
                self.js_parser = Parser()
                self.js_parser.set_language(js_language)
                self.ts_parser = Parser()
                self.ts_parser.set_language(ts_language)
                
            print("   🌳 Tree-sitter JS/TS initialized — UNIVERSAL mode")
        except Exception as e:
            print(f"   ⚠️ Tree-sitter init failed: {e}")
            self.js_parser = self.ts_parser = None

    def parse(self, file_path: Path, file_id: str):
        content = self._safe_read(file_path)
        if not content:
            return

        if TREE_SITTER_AVAILABLE and self.ts_parser and self.js_parser:
            try:
                name = file_path.name.lower()
                is_ts = name.endswith('.ts') or name.endswith('.tsx') or name.endswith('.d.ts')
                parser = self.ts_parser if is_ts else self.js_parser

                tree = parser.parse(bytes(content, "utf8"))
                visitor = _ASTVisitor(self.graph, content, file_id)
                visitor.visit(tree.root_node)
                return
            except Exception as e:
                print(f"   ⚠️ Tree-sitter parse error {file_path.name}: {e}")

        self._regex_fallback(file_path, file_id)

    def _regex_fallback(self, file_path: Path, file_id: str):
        try:
            from .javascript_regex import JavaScriptParser as RegexParser
            RegexParser(self.graph).parse(file_path, file_id)
        except Exception:
            pass


class _ASTVisitor:
    def __init__(self, graph, content: str, file_id: str):
        self.graph = graph
        self.content = content
        self.file_id = file_id
        self.current_decorators: List[str] = []

    def visit(self, node):
        node_type = node.type
        handler = getattr(self, f'_visit_{node_type}', self._visit_default)
        handler(node)

    def _visit_export_statement(self, node):
        decorators = []
        declaration = None
        for child in node.children:
            if child.type == "decorator":
                dec = self._extract_decorator_name(child)
                if dec:
                    decorators.append(dec)
            elif child.type in ("class_declaration", "function_declaration", "lexical_declaration",
                                "variable_declaration", "interface_declaration", "type_alias"):
                declaration = child

        if declaration:
            self.current_decorators = decorators
            self.visit(declaration)
            self.current_decorators = []
        else:
            self._visit_default(node)

    def _visit_class_declaration(self, node):
        name = self._child_text(node, ["identifier", "type_identifier"])
        if name:
            ntype = self._classify_class(name, self.current_decorators, node.start_byte)
            self._add_def(name, ntype)

            for child in node.children:
                if child.type == "class_body":
                    self._extract_class_members(child, name)

    def _extract_class_members(self, body_node, class_name: str):
        for child in body_node.children:
            if child.type == "method_definition":
                mname = self._child_text(child, ["property_identifier", "identifier"])
                if mname and mname not in JS_NOISE:
                    mtype = self._classify_method(mname, child.start_byte)
                    self._add_def(mname, mtype, parent=class_name)

    def _visit_function_declaration(self, node):
        name = self._child_text(node, ["identifier", "type_identifier"])
        if name and name not in JS_NOISE:
            ntype = self._classify_function(name, node.start_byte)
            self._add_def(name, ntype)

    def _visit_lexical_declaration(self, node):
        for decl in node.children:
            if decl.type == "variable_declarator":
                name = self._child_text(decl, ["identifier", "type_identifier"])
                if name and name not in JS_NOISE:
                    for sub in decl.children:
                        if sub.type in ("arrow_function", "function"):
                            ntype = self._classify_function(name, decl.start_byte)
                            self._add_def(name, ntype)

    def _visit_interface_declaration(self, node):
        name = self._child_text(node, ["identifier", "type_identifier"])
        if name:
            self._add_def(name, "interface")

    def _visit_type_alias(self, node):
        name = self._child_text(node, ["identifier", "type_identifier"])
        if name:
            self._add_def(name, "type_alias")

    def _visit_import_statement(self, node):
        for child in node.children:
            if child.type == "string":
                path = self.content[child.start_byte:child.end_byte].strip('"\'')
                self._handle_import(path)

    def _visit_default(self, node):
        for child in node.children:
            self.visit(child)

    def _classify_class(self, name: str, decorators: List[str], pos: int) -> str:
        for dec in decorators:
            if dec in NESTJS_CLASS_DECORATORS:
                return f"nestjs_{dec.lower()}"
        snippet = self.content[max(0, pos - 2000):pos + 1200]
        for dec in NESTJS_CLASS_DECORATORS:
            if f'@{dec}' in snippet:
                return f"nestjs_{dec.lower()}"

        if re.match(r'^[A-Z]', name) and re.search(r'return\s*\(\s*<', snippet):
            return "react_component"
        return "class"

    def _classify_method(self, name: str, pos: int) -> str:
        snippet = self.content[max(0, pos - 800):pos + 500]
        for dec in NESTJS_METHOD_DECORATORS:
            if f'@{dec}' in snippet:
                return "nestjs_endpoint"
        return "method"

    def _classify_function(self, name: str, pos: int) -> str:
        if name.startswith('use') and len(name) > 3 and name[3].isupper():
            return "react_hook"
        if name in {'getServerSideProps', 'getStaticProps', 'getStaticPaths', 'generateMetadata'}:
            return "nextjs_data_fn"
        snippet = self.content[pos:pos + 1200]
        if re.match(r'^[A-Z]', name) and re.search(r'return\s*\(\s*<', snippet):
            return "react_component"
        return "function"

    def _extract_decorator_name(self, node) -> Optional[str]:
        for child in node.children:
            if child.type == "identifier":
                return self.content[child.start_byte:child.end_byte]
            if child.type == "call_expression":
                for sub in child.children:
                    if sub.type in ("identifier", "member_expression"):
                        return self.content[sub.start_byte:sub.end_byte].split('.')[-1]
        return None

    def _child_text(self, node, child_types):
        if isinstance(child_types, str):
            child_types = [child_types]
        for child in node.children:
            if child.type in child_types:
                return self.content[child.start_byte:child.end_byte]
        return None

    def _add_def(self, name: str, node_type: str, parent: Optional[str] = None):
        node_id = f"{self.file_id}::{name}"
        parent_id = f"{self.file_id}::{parent}" if parent and '::' not in str(parent) else (parent or self.file_id)
        self.graph.add_node(node_id, node_type, external=False)
        self.graph.add_edge(parent_id, node_id, "defines")

    def _handle_import(self, import_path: str):
        if not import_path or import_path in JS_NOISE or import_path.startswith('node:'):
            return

        if import_path.startswith(('@/', '~/', 'src/', './', '../', 'packages/', '@')):
            cleaned = import_path.replace('@/', '').replace('~/', '').replace('src/', '')
            if cleaned.startswith('./') or cleaned.startswith('../'):
                # Relative paths are resolved via suffix index directly
                pass
            
            resolved = self.graph.resolve_path_alias(cleaned)
            if resolved:
                self.graph.add_edge(self.file_id, resolved, "imports")
                return

            self.graph.add_node(cleaned, "alias", external=False)
            self.graph.add_edge(self.file_id, cleaned, "imports")
            return

        # External package
        if import_path.startswith('@'):
            pkg = '/'.join(import_path.split('/')[:2])
        else:
            pkg = import_path.split('/')[0].split('@')[0] if '@' in import_path else import_path.split('/')[0]

        if pkg:
            self.graph.add_node(pkg, "npm_package", external=True)
            self.graph.add_edge(self.file_id, pkg, "imports")