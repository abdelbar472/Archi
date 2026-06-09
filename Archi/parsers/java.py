"""Java/Kotlin parser — regex-based, medium confidence."""
import re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from base import BaseParser


class JavaParser(BaseParser):
    METHOD = "regex"

    CLASS_PATTERN = re.compile(
        r'(?:public|private|protected|internal|abstract|final|open|data|sealed)?\s*'
        r'(?:class|interface|enum|object)\s+(\w+)',
        re.MULTILINE
    )
    FUNC_PATTERN = re.compile(
        r'(?:public|private|protected|internal|static|final|override|suspend)?\s*'
        r'(?:fun|def)?\s*(\w+)\s*\([^)]*\)\s*(?::\s*\w+)?\s*(?:\{|=)',
        re.MULTILINE
    )
    IMPORT_PATTERN = re.compile(r'^import\s+([\w.]+)', re.MULTILINE)

    def parse(self, file_path: Path, file_id: str):
        content = self._safe_read(file_path)

        for match in self.CLASS_PATTERN.finditer(content):
            self._add_def(file_id, match.group(1), "class")

        for match in self.FUNC_PATTERN.finditer(content):
            name = match.group(1)
            if name not in ('if', 'for', 'while', 'switch', 'catch', 'when'):
                self._add_def(file_id, name, "method")

        for match in self.IMPORT_PATTERN.finditer(content):
            pkg = match.group(1).split('.')[0]
            self.graph.add_node(pkg, "module", external=True)
            self._add_import(file_id, pkg)