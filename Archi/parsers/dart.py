"""Dart/Flutter parser — regex-based, medium confidence."""
import re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from base import BaseParser


class DartParser(BaseParser):
    METHOD = "regex"

    CLASS_PATTERN = re.compile(r'^class\s+(\w+)', re.MULTILINE)
    FUNC_PATTERN = re.compile(r'^(?:\w+\s+)?(\w+)\s*\([^)]*\)\s*\{', re.MULTILINE)
    WIDGET_PATTERN = re.compile(r'^class\s+(\w+)\s+extends\s+(?:StatelessWidget|StatefulWidget|Widget)', re.MULTILINE)
    IMPORT_PATTERN = re.compile(r"import\s+[\x27\"](.+?)[\x27\"]")

    def parse(self, file_path: Path, file_id: str):
        content = self._safe_read(file_path)

        for match in self.WIDGET_PATTERN.finditer(content):
            self._add_def(file_id, match.group(1), "widget")

        for match in self.CLASS_PATTERN.finditer(content):
            class_name = match.group(1)
            if not self.graph.is_known(f"{file_id}::{class_name}"):
                self._add_def(file_id, class_name, "class")

        for match in self.FUNC_PATTERN.finditer(content):
            name = match.group(1)
            if name not in ('if', 'for', 'while', 'switch', 'catch'):
                func_id = f"{file_id}::{name}"
                if not self.graph.is_known(func_id):
                    self.graph.add_node(func_id, "function")
                    self.graph.add_edge(file_id, func_id, "defines")

        for match in self.IMPORT_PATTERN.finditer(content):
            target = match.group(1)
            if target.startswith("package:"):
                pkg = target.split(":")[1].split("/")[0]
                self.graph.add_node(pkg, "module", external=True)
                self._add_import(file_id, pkg)
            elif target.startswith("dart:"):
                self.graph.add_node(target, "module", external=True)
                self._add_import(file_id, target)