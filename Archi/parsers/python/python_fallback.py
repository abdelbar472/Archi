"""Python Regex Fallback Parser"""
import re
from pathlib import Path
from ..base import BaseParser


class PythonFallback(BaseParser):
    METHOD = "python-fallback"

    def parse(self, file_path: Path, file_id: str):
        content = self._safe_read(file_path)
        if not content:
            return

        # Simple but useful patterns
        # Classes
        for match in re.finditer(r'class\s+(\w+)', content):
            name = match.group(1)
            if name[0].isupper():
                self.graph.add_node(f"{file_id}::{name}", "class", external=False)
                self.graph.add_edge(file_id, f"{file_id}::{name}", "defines")

        # Functions
        for match in re.finditer(r'def\s+(\w+)', content):
            name = match.group(1)
            if not name.startswith('_'):
                ntype = "celery_task" if 'task' in name.lower() else "function"
                self.graph.add_node(f"{file_id}::{name}", ntype, external=False)
                self.graph.add_edge(file_id, f"{file_id}::{name}", "defines")