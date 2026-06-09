"""C# parser — regex-based, medium confidence."""
import re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from base import BaseParser


class CSharpParser(BaseParser):
    METHOD = "regex"

    CLASS_PATTERN = re.compile(
        r'(?:public|private|protected|internal|abstract|sealed|static|partial)?\s*'
        r'(?:class|struct|interface|enum|record)\s+(\w+)',
        re.MULTILINE
    )
    FUNC_PATTERN = re.compile(
        r'(?:public|private|protected|internal|static|async|override|virtual|abstract)?\s*'
        r'(?:\w+\s+)?(\w+)\s*\([^)]*\)\s*(?:=>|\{)',
        re.MULTILINE
    )
    USING_PATTERN = re.compile(r'^using\s+([\w.]+);', re.MULTILINE)
    NAMESPACE_PATTERN = re.compile(r'^namespace\s+([\w.]+)', re.MULTILINE)

    def parse(self, file_path: Path, file_id: str):
        content = self._safe_read(file_path)

        for match in self.CLASS_PATTERN.finditer(content):
            self._add_def(file_id, match.group(1), "class")

        for match in self.FUNC_PATTERN.finditer(content):
            name = match.group(1)
            if name not in ('if', 'for', 'while', 'switch', 'catch', 'using', 'lock', 'checked', 'unchecked'):
                self._add_def(file_id, name, "method")

        for match in self.USING_PATTERN.finditer(content):
            ns = match.group(1).split('.')[0]
            self.graph.add_node(ns, "namespace", external=True)
            self._add_import(file_id, ns)

        for match in self.NAMESPACE_PATTERN.finditer(content):
            self._add_def(file_id, match.group(1), "namespace")