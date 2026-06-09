"""JavaScript/TypeScript parser — regex-based, medium confidence."""
import re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from base import BaseParser


class JavaScriptParser(BaseParser):
    METHOD = "regex"

    FUNC_PATTERN = re.compile(
        r'(?:export\s+)?(?:async\s+)?(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>))'
    )
    CLASS_PATTERN = re.compile(r'(?:export\s+)?class\s+(\w+)')
    IMPORT_PATTERN = re.compile(r"import\s+.*?\s+from\s+[\x27\"](.+?)[\x27\"]")
    REQUIRE_PATTERN = re.compile(r"require\([\x27\"](.+?)[\x27\"]\)")

    def parse(self, file_path: Path, file_id: str):
        content = self._safe_read(file_path)

        for match in self.FUNC_PATTERN.finditer(content):
            name = match.group(1) or match.group(2)
            if name:
                self._add_def(file_id, name, "function")

        for match in self.CLASS_PATTERN.finditer(content):
            class_id = self._add_def(file_id, match.group(1), "class")

        for match in self.IMPORT_PATTERN.finditer(content):
            target = match.group(1)
            if target.startswith('.'):
                target_path = (file_path.parent / target).resolve()
                target_id = str(target_path.relative_to(Path.cwd()))
                self._add_import(file_id, target_id)
            else:
                pkg = target.split('/')[0]
                self.graph.add_node(pkg, "module", external=True)
                self._add_import(file_id, pkg)

        for match in self.REQUIRE_PATTERN.finditer(content):
            target = match.group(1)
            pkg = target.split('/')[0]
            self.graph.add_node(pkg, "module", external=True)
            self._add_import(file_id, pkg)