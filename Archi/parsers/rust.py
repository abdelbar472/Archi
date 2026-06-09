"""Rust parser — regex-based, medium confidence."""
import re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from base import BaseParser


class RustParser(BaseParser):
    METHOD = "regex"

    FUNC_PATTERN = re.compile(r'^\s*(?:pub\s+)?fn\s+(\w+)', re.MULTILINE)
    STRUCT_PATTERN = re.compile(r'^\s*(?:pub\s+)?struct\s+(\w+)', re.MULTILINE)
    ENUM_PATTERN = re.compile(r'^\s*(?:pub\s+)?enum\s+(\w+)', re.MULTILINE)
    TRAIT_PATTERN = re.compile(r'^\s*(?:pub\s+)?trait\s+(\w+)', re.MULTILINE)
    IMPL_PATTERN = re.compile(r'^\s*impl\s+(?:<<[^>]+>\s+)?(\w+)', re.MULTILINE)
    USE_PATTERN = re.compile(r'^\s*use\s+([^;]+);', re.MULTILINE)

    def parse(self, file_path: Path, file_id: str):
        content = self._safe_read(file_path)

        for match in self.FUNC_PATTERN.finditer(content):
            self._add_def(file_id, match.group(1), "function")

        for match in self.STRUCT_PATTERN.finditer(content):
            self._add_def(file_id, match.group(1), "struct")

        for match in self.ENUM_PATTERN.finditer(content):
            self._add_def(file_id, match.group(1), "enum")

        for match in self.TRAIT_PATTERN.finditer(content):
            self._add_def(file_id, match.group(1), "trait")

        for match in self.IMPL_PATTERN.finditer(content):
            self.graph.add_edge(file_id, match.group(1), "implements")

        for match in self.USE_PATTERN.finditer(content):
            use_path = match.group(1).strip()
            parts = use_path.split("::")
            if parts:
                root = parts[0]
                if root not in ("self", "super", "crate"):
                    self.graph.add_node(root, "module", external=True)
                    self._add_import(file_id, root)