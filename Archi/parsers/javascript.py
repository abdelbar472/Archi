"""JavaScript/TypeScript parser — regex-based, framework-aware."""
import re
from pathlib import Path

from .base import BaseParser


# Noise: JS builtins / common false positives
JS_NOISE = {
    'console', 'process', 'require', 'module', 'exports', 'window',
    'document', 'Promise', 'setTimeout', 'setInterval', 'clearTimeout',
    'JSON', 'Math', 'Date', 'Object', 'Array', 'String', 'Number',
    'Boolean', 'Error', 'Map', 'Set', 'Symbol', 'Proxy', 'Reflect',
    'parseInt', 'parseFloat', 'isNaN', 'isFinite', 'encodeURIComponent',
    'fetch', 'URL', 'URLSearchParams', 'FormData', 'Headers', 'Request',
    'Response', 'AbortController', 'ReadableStream', 'paths', 'id', 'below',
    'params', 'props', 'context', 'req', 'res', 'children'
}

# Framework signatures
NESTJS_CLASS_DECORATORS = {'Controller', 'Injectable', 'Module', 'Guard', 'Interceptor', 'Pipe', 'Resolver'}
NESTJS_METHOD_DECORATORS = {'Get', 'Post', 'Put', 'Delete', 'Patch', 'Options', 'Head', 'All', 'MessagePattern'}


class JavaScriptParser(BaseParser):
    METHOD = "regex"

    # Improved patterns with TS type annotation support
    FUNC_NAMED = re.compile(r'(?:export\s+(?:default\s+)?)?(?:async\s+)?function\s*\*?\s+(\w+)\s*\(')
    
    FUNC_ARROW = re.compile(
        r'^(?:\s*export\s+)?(?:const|let|var)\s+(\w+)\s*(?::\s*[\w<>,.\s|]+)?\s*=\s*(?:async\s+)?\(?',
        re.MULTILINE
    )

    TS_INTERFACE = re.compile(r'(?:export\s+)?interface\s+([A-Z]\w+)(?:\s+extends\s+[\w,\s<>]+)?\s*\{')
    TS_TYPE = re.compile(r'(?:export\s+)?type\s+([A-Z]\w+)\s*=')
    TS_ENUM = re.compile(r'(?:export\s+)?(?:const\s+)?enum\s+([A-Z]\w+)')

    DECORATOR = re.compile(r'@(\w+)(?:\(|$)', re.MULTILINE)

    IMPORT_FROM = re.compile(r"import\s+(?:type\s+)?(?:\{[^}]*\}|[\w*]+|\*\s+as\s+\w+)\s+from\s+['\"]([^'\"]+)['\"]")
    IMPORT_DYNAMIC = re.compile(r"import\s*\(\s*['\"]([^'\"]+)['\"]\s*\)")
    REQUIRE = re.compile(r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)")

    def parse(self, file_path: Path, file_id: str):
        content = self._safe_read(file_path)
        if not content:
            return

        is_ts = file_path.suffix.lower() in ('.ts', '.tsx', '.d.ts')
        is_jsx = file_path.suffix.lower() in ('.jsx', '.tsx')

        # TypeScript constructs
        for m in self.TS_INTERFACE.finditer(content):
            self._add_def(file_id, m.group(1), "interface")
        for m in self.TS_TYPE.finditer(content):
            self._add_def(file_id, m.group(1), "type_alias")
        for m in self.TS_ENUM.finditer(content):
            self._add_def(file_id, m.group(1), "enum")

        # Classes
        for m in re.finditer(r'(?:export\s+(?:default\s+)?)?(?:abstract\s+)?class\s+(\w+)', content):
            name = m.group(1)
            node_type = self._classify_class(name, content, m.start())
            self._add_def(file_id, name, node_type)

        # Functions / Components
        seen = set()
        for pattern in (self.FUNC_NAMED, self.FUNC_ARROW):
            for m in pattern.finditer(content):
                name = m.group(1)
                if not name or name in seen or name.lower() in JS_NOISE:
                    continue
                seen.add(name)
                node_type = self._classify_function(name, content, m.start(), is_jsx)
                self._add_def(file_id, name, node_type)

        # Imports
        self._parse_imports(content, file_id, file_path)

    def _classify_class(self, name: str, content: str, pos: int) -> str:
        before = content[max(0, pos-300):pos]
        if any(d in before for d in NESTJS_CLASS_DECORATORS):
            return "nestjs_controller" if 'Controller' in before else "nestjs_service"
        if name[0].isupper() and re.search(r'return\s*\(?\s*<', content[pos:pos+600]):
            return "react_component"
        return "class"

    def _classify_function(self, name: str, content: str, pos: int, is_jsx: bool) -> str:
        if name.startswith('use') and len(name) > 3 and name[3].isupper():
            return "react_hook"
        if is_jsx and name[0].isupper():
            return "react_component"
        if name in ('getServerSideProps', 'getStaticProps', 'getStaticPaths', 'generateMetadata', 'generateStaticParams'):
            return "nextjs_data_fn"
        return "function"

    def _parse_imports(self, content: str, file_id: str, file_path: Path):
        for pattern in (self.IMPORT_FROM, self.IMPORT_DYNAMIC, self.REQUIRE):
            for m in pattern.finditer(content):
                raw = m.group(1).strip()
                if not raw or raw.lower() in JS_NOISE:
                    continue

                if raw.startswith(('@/', '~/')):
                    alias_path = raw[2:]
                    if self.graph.is_known(alias_path) or self.graph.is_known(alias_path + '.ts'):
                        self.graph.add_edge(file_id, alias_path, "imports")
                    continue

                if raw.startswith('.'):
                    resolved = self._resolve_relative(raw, file_id, file_path)
                    if resolved and self.graph.is_known(resolved):
                        self.graph.add_edge(file_id, resolved, "imports")
                else:
                    pkg = raw.split('/')[0]
                    if pkg and not pkg.startswith('.'):
                        self.graph.add_node(pkg, "npm_package", external=True)
                        self.graph.add_edge(file_id, pkg, "imports")

    def _resolve_relative(self, raw: str, file_id: str, file_path: Path) -> str | None:
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