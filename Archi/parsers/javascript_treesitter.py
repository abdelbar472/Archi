"""JavaScript/TypeScript Tree-sitter Parser — PRODUCTION-READY v4 (Large Monorepos + NestJS)"""
import re
from pathlib import Path
from typing import Optional, List

try:
    from tree_sitter import Language, Parser
    import tree_sitter_javascript
    import tree_sitter_typescript
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False

from .base import BaseParser


NESTJS_CLASS_DECORATORS = {
    'Controller': 'nestjs_controller',
    'Injectable': 'nestjs_service',
    'Service': 'nestjs_service',
    'Module': 'nestjs_module',
    'Guard': 'nestjs_guard',
    'Interceptor': 'nestjs_interceptor',
    'Pipe': 'nestjs_pipe',
    'Resolver': 'nestjs_resolver',
    'Middleware': 'nestjs_middleware',
    'Catch': 'nestjs_filter',
    'WebSocketGateway': 'nestjs_gateway',
}

NESTJS_METHOD_DECORATORS = {'Get', 'Post', 'Put', 'Delete', 'Patch', 'Options', 'Head', 'All',
                           'MessagePattern', 'EventPattern', 'Query', 'Mutation', 'Subscription'}

JS_NOISE = {'console', 'process', 'require', 'module', 'exports', 'window', 'document'}


class JavaScriptParser(BaseParser):
    METHOD = "tree-sitter"

    def __init__(self, graph):
        super().__init__(graph)
        self.parser = None
        self.js_language = None
        self.ts_language = None
        if TREE_SITTER_AVAILABLE:
            self._init_tree_sitter()

    def _init_tree_sitter(self):
        try:
            self.js_language = Language(tree_sitter_javascript.language())
            self.ts_language = Language(tree_sitter_typescript.language_typescript())
            try:
                self.parser = Parser(self.ts_language)
            except TypeError:
                self.parser = Parser()
                self.parser.set_language(self.ts_language)
            print("   🌳 Tree-sitter JS/TS initialized (Large Monorepo mode)")
        except Exception as e:
            print(f"   ⚠️ Tree-sitter init failed: {e}")
            self.parser = None

    def parse(self, file_path: Path, file_id: str):
        content = self._safe_read(file_path)
        if not content:
            return

        if TREE_SITTER_AVAILABLE and self.parser:
            try:
                is_ts = file_path.suffix.lower() in ('.ts', '.tsx', '.d.ts')
                lang = self.ts_language if is_ts else self.js_language
                if hasattr(self.parser, 'set_language'):
                    self.parser.set_language(lang)

                tree = self.parser.parse(bytes(content, "utf8"))
                visitor = _ASTVisitor(self.graph, content, file_id)
                visitor.visit(tree.root_node)
            except Exception as e:
                print(f"   ⚠️ Tree-sitter error in {file_path.name}: {e}")
                self._regex_fallback(file_path, file_id)
        else:
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
                                "variable_declaration", "interface_declaration"):
                declaration = child

        if declaration:
            self.current_decorators = decorators
            self.visit(declaration)
            self.current_decorators = []
        else:
            self._visit_default(node)

    def _visit_class_declaration(self, node):
        name = self._child_text(node, "identifier")
        if name:
            ntype = self._classify_class(name, self.current_decorators, node.start_byte)
            self._add_def(name, ntype)

            for child in node.children:
                if child.type == "class_body":
                    self._extract_class_methods(child, name)

    def _extract_class_methods(self, body_node, class_name: str):
        for child in body_node.children:
            if child.type == "method_definition":
                mname = self._child_text(child, "property_identifier") or self._child_text(child, "identifier")
                if mname and mname not in JS_NOISE:
                    mtype = self._classify_method(mname, child.start_byte)
                    self._add_def(mname, mtype, parent=class_name)

    def _visit_function_declaration(self, node):
        name = self._child_text(node, "identifier")
        if name and name not in JS_NOISE:
            ntype = self._classify_function(name, node.start_byte)
            self._add_def(name, ntype)

    def _visit_lexical_declaration(self, node):
        for child in node.children:
            if child.type == "variable_declarator":
                name = self._child_text(child, "identifier")
                if name and name not in JS_NOISE:
                    for sub in child.children:
                        if sub.type in ("arrow_function", "function"):
                            ntype = self._classify_function(name, child.start_byte)
                            self._add_def(name, ntype)

    def _visit_interface_declaration(self, node):
        name = self._child_text(node, "identifier")
        if name:
            self._add_def(name, "interface")

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
                return NESTJS_CLASS_DECORATORS[dec]
        snippet = self.content[max(0, pos - 1800):pos + 1000]
        for dec, ntype in NESTJS_CLASS_DECORATORS.items():
            if f'@{dec}' in snippet or f'@{dec}(' in snippet:
                return ntype
        if name[0].isupper() and re.search(r'return\s*[<(]', snippet):
            return "react_component"
        return "class"

    def _classify_method(self, name: str, pos: int) -> str:
        snippet = self.content[max(0, pos - 600):pos + 400]
        for dec in NESTJS_METHOD_DECORATORS:
            if f'@{dec}' in snippet or f'@{dec}(' in snippet:
                return "nestjs_endpoint"
        return "constructor" if name == "constructor" else "method"

    def _classify_function(self, name: str, pos: int) -> str:
        if name.startswith('use') and len(name) > 3 and name[3].isupper():
            return "react_hook"
        if name in {'getServerSideProps', 'getStaticProps', 'getStaticPaths', 'generateMetadata', 'generateStaticParams'}:
            return "nextjs_data_fn"
        snippet = self.content[pos:pos + 900]
        if name[0].isupper() and re.search(r'return\s*[<(]', snippet):
            return "react_component"
        return "function"

    def _extract_decorator_name(self, node) -> Optional[str]:
        for child in node.children:
            if child.type == "identifier":
                return self.content[child.start_byte:child.end_byte]
            if child.type == "call_expression":
                for sub in child.children:
                    if sub.type == "identifier":
                        return self.content[sub.start_byte:sub.end_byte]
        return None

    def _child_text(self, node, child_type: str) -> Optional[str]:
        for child in node.children:
            if child.type == child_type:
                return self.content[child.start_byte:child.end_byte]
        return None

    def _add_def(self, name: str, node_type: str, parent: Optional[str] = None):
        if parent:
            node_id = f"{self.file_id}::{name}"
            parent_id = f"{self.file_id}::{parent}" if '::' not in str(parent) else parent
        else:
            node_id = f"{self.file_id}::{name}"
            parent_id = self.file_id
        self.graph.add_node(node_id, node_type, external=False)
        self.graph.add_edge(parent_id, node_id, "defines")

    def _handle_import(self, import_path: str):
        if not import_path or import_path in JS_NOISE:
            return
        # Monorepo alias handling (@/, ~/, src/, packages/)
        if import_path.startswith(('@/', '~/', 'src/', './', '../', 'packages/')):
            alias_path = import_path.replace('src/', '', 1).lstrip('./')
            for cand in (alias_path, f"{alias_path}.ts", f"{alias_path}.tsx", f"{alias_path}/index.ts", f"{alias_path}/index.tsx"):
                if self.graph.is_known(cand):
                    self.graph.add_edge(self.file_id, cand, "imports")
                    return
            self.graph.add_node(alias_path, "alias", external=False)
            self.graph.add_edge(self.file_id, alias_path, "imports")
            return
        # External packages
        if import_path.startswith('@'):
            pkg = '/'.join(import_path.split('/')[:2])
        else:
            pkg = import_path.split('/')[0]
        if pkg:
            self.graph.add_node(pkg, "npm_package", external=True)
            self.graph.add_edge(self.file_id, pkg, "imports")