"""Go parser — regex-based, medium confidence."""
import re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from base import BaseParser


class GoParser(BaseParser):
    METHOD = "regex"

    FUNC_PATTERN = re.compile(r'^func\s+(?:\([^)]+\)\s+)?(\w+)\s*\(', re.MULTILINE)
    STRUCT_PATTERN = re.compile(r'^type\s+(\w+)\s+struct', re.MULTILINE)
    INTERFACE_PATTERN = re.compile(r'^type\s+(\w+)\s+interface', re.MULTILINE)
    IMPORT_PATTERN = re.compile(r'"([^"]+)"')

    def parse(self, file_path: Path, file_id: str):
        content = self._safe_read(file_path)

        for match in self.FUNC_PATTERN.finditer(content):
            self._add_def(file_id, match.group(1), "function")

        for match in self.STRUCT_PATTERN.finditer(content):
            self._add_def(file_id, match.group(1), "struct")

        for match in self.INTERFACE_PATTERN.finditer(content):
            self._add_def(file_id, match.group(1), "interface")

        for match in self.IMPORT_PATTERN.finditer(content):
            pkg = match.group(1)
            if not pkg.startswith("."):
                pkg_name = pkg.split("/")[-1]
                self.graph.add_node(pkg_name, "module", external=True)
                self._add_import(file_id, pkg_name)