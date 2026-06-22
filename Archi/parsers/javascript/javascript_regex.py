"""JavaScript/TypeScript regex fallback parser — stable and dependency-free."""
import re
from pathlib import Path
from collections import defaultdict

from .base import BaseParser


JS_NOISE = {
    'console', 'process', 'require', 'module', 'exports', 'window', 'document',
    'Promise', 'setTimeout', 'setInterval', 'JSON', 'Math', 'Date', 'Object',
    'Array', 'String', 'Number', 'Boolean', 'Error', 'Map', 'Set', 'Symbol',
    'fetch', 'URL', 'req', 'res', 'props', 'children'
}

NESTJS_DECORATORS = {'Controller', 'Injectable', 'Module', 'Guard', 'Interceptor', 'Pipe', 'Resolver', 'Service'}
NESTJS_ROUTE_DECORATORS = {'Get', 'Post', 'Put', 'Delete', 'Patch', 'Options', 'Head', 'All'}


class JavaScriptParser(BaseParser):
    METHOD = "regex"

    CLASS_PATTERN = re.compile(r'(?:export\s+(?:default\s+)?)?(?:abstract\s+)?class\s+(\w+)', re.MULTILINE)
    INTERFACE_PATTERN = re.compile(r'(?:export\s+)?interface\s+([A-Z]\w+)', re.MULTILINE)
    TYPE_PATTERN = re.compile(r'(?:export\s+)?type\s+([A-Z]\w+)', re.MULTILINE)
    ENUM_PATTERN = re.compile(r'(?:export\s+)?(?:const\s+)?enum\s+([A-Z]\w+)', re.MULTILINE)

    FUNC_NAMED = re.compile(r'(?:export\s+(?:default\s+)?)?(?:async\s+)?function\s*\*?\s+(\w+)\s*\(', re.MULTILINE)
    FUNC_ARROW = re.compile(r'^(?:\s*export\s+)?(?:const|let|var)\s+(\w+)\s*(?::\s*[\w<>,.\s|]+)?\s*=\s*(?:async\s+)?\(?', re.MULTILINE)

    DECORATOR_PATTERN = re.compile(r'@(\w+)(?:\(|$)', re.MULTILINE)

    IMPORT_PATTERNS = [
        re.compile(r"import\s+(?:type\s+)?(?:\{[^}]*\}|[\w*]+|\*\s+as\s+\w+)\s+from\s+['\"]([^'\"]+)['\"]"),
        re.compile(r"import\s*\(\s*['\"]([^'\"]+)['\"]"),
        re.compile(r"require\s*\(\s*['\"]([^'\"]+)['\"]")
    ]

    def parse(self, file_path: Path, file_id: str):
        content = self._safe_read(file_path)
        if not content:
            return

        is_ts = file_path.suffix.lower() in ('.ts', '.tsx', '.d.ts')
        is_jsx = file_path.suffix.lower() in ('.jsx', '.tsx')

        self._parse_types(content, file_id)
        self._parse_classes(content, file_id)
        self._parse_functions(content, file_id, is_jsx)
        self._parse_imports(content, file_id, file_path)
        self._parse_decorators(content, file_id)

    def _parse_types(self, content: str, file_id: str):
        for pattern, ntype in [(self.INTERFACE_PATTERN, "interface"),
                               (self.TYPE_PATTERN, "type_alias"),
                               (self.ENUM_PATTERN, "enum")]:
            for m in pattern.finditer(content):
                self._add_def(file_id, m.group(1), ntype)

    def _parse_classes(self, content: str, file_id: str):
        for m in self.CLASS_PATTERN.finditer(content):
            name = m.group(1)
            node_type = self._classify_class(name, content, m.start())
            self._add_def(file_id, name, node_type)

    def _parse_functions(self, content: str, file_id: str, is_jsx: bool):
        seen = set()
        for pattern in (self.FUNC_NAMED, self.FUNC_ARROW):
            for m in pattern.finditer(content):
                name = m.group(1)
                if not name or name in seen or name.lower() in JS_NOISE:
                    continue
                seen.add(name)
                node_type = self._classify_function(name, content, m.start(), is_jsx)
                self._add_def(file_id, name, node_type)

    def _classify_class(self, name: str, content: str, pos: int) -> str:
        before = content[max(0, pos-400):pos+300]
        for dec in NESTJS_DECORATORS:
            if f'@{dec}' in before:
                return "nestjs_controller" if dec == 'Controller' else "nestjs_service"
        if name[0].isupper() and re.search(r'return\s*\(?\s*<', content[pos:pos+800]):
            return "react_component"
        return "class"

    def _classify_function(self, name: str, content: str, pos: int, is_jsx: bool) -> str:
        if name.startswith('use') and len(name) > 3 and name[3].isupper():
            return "react_hook"
        if is_jsx and name[0].isupper():
            return "react_component"
        if name in ('getServerSideProps', 'getStaticProps', 'getStaticPaths', 'generateMetadata'):
            return "nextjs_data_fn"
        return "function"

    def _parse_decorators(self, content: str, file_id: str):
        pass  # Can be extended

    def _parse_imports(self, content: str, file_id: str, file_path: Path):
        for pattern in self.IMPORT_PATTERNS:
            for m in pattern.finditer(content):
                raw = m.group(1).strip()
                if not raw or raw.lower() in JS_NOISE:
                    continue
                if raw.startswith('.'):
                    resolved = self._resolve_relative(raw, file_id, file_path)
                    if resolved:
                        self.graph.add_edge(file_id, resolved, "imports")
                else:
                    pkg = raw.split('/')[0]
                    if pkg:
                        self.graph.add_node(pkg, "npm_package", external=True)
                        self.graph.add_edge(file_id, pkg, "imports")

    def _resolve_relative(self, raw: str, file_id: str, file_path: Path):
        try:
            file_dir = '/'.join(file_id.split('/')[:-1]) or "."
            if raw.startswith('./'):
                return f"{file_dir}/{raw[2:]}".rstrip('.')
            elif raw.startswith('../'):
                parts = file_dir.split('/')
                levels = raw.count('../')
                resolved = '/'.join(parts[:-levels]) if levels <= len(parts) else ""
                rest = raw.replace('../', '', levels).lstrip('/')
                return f"{resolved}/{rest}".strip('/') if resolved else rest
            return raw
        except:
            return None