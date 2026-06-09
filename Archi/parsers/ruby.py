"""Ruby parser — regex-based, medium confidence."""
import re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from base import BaseParser


class RubyParser(BaseParser):
    METHOD = "regex"

    CLASS_PATTERN = re.compile(r'^\s*class\s+(\w+)', re.MULTILINE)
    MODULE_PATTERN = re.compile(r'^\s*module\s+(\w+)', re.MULTILINE)
    FUNC_PATTERN = re.compile(r'^\s*def\s+(?:self\.)?(\w+)', re.MULTILINE)
    REQUIRE_PATTERN = re.compile(r"require\s+[\x27\"](.+?)[\x27\"]")
    INCLUDE_PATTERN = re.compile(r'^\s*include\s+(\w+)', re.MULTILINE)

    def parse(self, file_path: Path, file_id: str):
        content = self._safe_read(file_path)

        for match in self.CLASS_PATTERN.finditer(content):
            self._add_def(file_id, match.group(1), "class")

        for match in self.MODULE_PATTERN.finditer(content):
            self._add_def(file_id, match.group(1), "module")

        for match in self.FUNC_PATTERN.finditer(content):
            self._add_def(file_id, match.group(1), "method")

        for match in self.REQUIRE_PATTERN.finditer(content):
            req = match.group(1)
            self.graph.add_node(req, "module", external=True)
            self._add_import(file_id, req)

        for match in self.INCLUDE_PATTERN.finditer(content):
            mod = match.group(1)
            self.graph.add_edge(file_id, mod, "includes")