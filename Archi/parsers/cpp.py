"""C/C++ parser — regex-based, medium confidence."""
import re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from base import BaseParser


class CppParser(BaseParser):
    METHOD = "regex"

    FUNC_PATTERN = re.compile(r'(?:\w+\s+)?(\w+)\s*\([^)]*\)\s*(?:const\s*)?\{', re.MULTILINE)
    CLASS_PATTERN = re.compile(r'(?:class|struct)\s+(\w+)', re.MULTILINE)
    INCLUDE_PATTERN = re.compile(r'#include\s+[<\"](.+?)[>\"]')
    NAMESPACE_PATTERN = re.compile(r'namespace\s+(\w+)')

    def parse(self, file_path: Path, file_id: str):
        content = self._safe_read(file_path)

        for match in self.CLASS_PATTERN.finditer(content):
            self._add_def(file_id, match.group(1), "class")

        for match in self.FUNC_PATTERN.finditer(content):
            name = match.group(1)
            if name not in ('if', 'for', 'while', 'switch', 'catch', 'main'):
                self._add_def(file_id, name, "function")

        for match in self.INCLUDE_PATTERN.finditer(content):
            header = match.group(1)
            self.graph.add_node(header, "header", external=True)
            self._add_import(file_id, header)

        for match in self.NAMESPACE_PATTERN.finditer(content):
            self._add_def(file_id, match.group(1), "namespace")