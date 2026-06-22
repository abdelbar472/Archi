"""Tempory Scanner — clean orchestrator, delegates to parser plugins."""
from pathlib import Path
import os
import sys

sys.path.insert(0, str(Path(__file__).parent))

from parsers.registry import PARSER_REGISTRY, PARSER_QUALITY
from parsers import get_parser
from graph import Graph


class TemporyScanner:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.graph = Graph(self.root_dir.name)
        self.ignored_dirs = {
            '.venv', '.git', '__pycache__', '.idea', 'build', 'dist',
            'graphify-out', '.pytest_cache', 'migrations', 'node_modules',
            '.dist-info', 'site-packages', '__mocks__', 'perf', 'release',
            '.claude', 'output', 'target', 'bin', 'obj', '.gradle',
            '.vscode', '.vs', 'Pods', '.build', 'DerivedData'
        }

    def should_ignore(self, path: Path) -> bool:
        try:
            rel_parts = set(path.relative_to(self.root_dir).parts)
        except ValueError:
            rel_parts = set(path.parts)
        return not rel_parts.isdisjoint(self.ignored_dirs)

    @staticmethod
    def _detect_file_type(filename: str) -> str:
        lower = filename.lower()
        if any(x in lower for x in ['component', 'screen', 'provider']): return "component"
        if any(x in lower for x in ['router', 'route']): return "router"
        if 'service' in lower: return "service"
        if any(x in lower for x in ['model', 'schema']): return "model"
        if 'test' in lower or 'spec' in lower: return "test"
        if 'index' in lower or 'main' in lower: return "main"
        if 'grpc' in lower: return "grpc"
        return "file"

    def scan(self, focus_dir: str = None):
        print(f"🔍 Archi Scanner v1.0 Scanning: {self.root_dir.name}")
        if focus_dir:
            print(f"   Focus: {focus_dir}")

        start_dir = self.root_dir / focus_dir if focus_dir else self.root_dir

        for dirpath, dirnames, filenames in os.walk(start_dir):
            current = Path(dirpath)
            if self.should_ignore(current):
                dirnames.clear()
                continue

            rel = current.relative_to(self.root_dir)
            folder_id = str(rel).replace('\\', '/') if str(rel) != "." else "root"
            self.graph.add_node(folder_id, "folder")

            if folder_id != "root":
                parent_id = str(rel.parent).replace('\\', '/') if str(rel.parent) != "." else "root"
                self.graph.add_edge(parent_id, folder_id, "contains")

            for filename in filenames:
                ext = Path(filename).suffix.lower()

                parser_cls = get_parser(ext)
                if parser_cls:
                    file_id = f"{folder_id}/{filename}" if folder_id != "root" else filename
                    
                    # Register for cross-file resolution
                    self.graph.register_file_id(file_id)
                    if ext == '.py':
                        dotted = file_id.replace('/', '.').rsplit('.py', 1)[0]
                        self.graph.module_to_file[dotted] = file_id

                    file_node_type = self._detect_file_type(filename)
                    self.graph.add_node(file_id, file_node_type)
                    self.graph.add_edge(folder_id, file_id, "contains")

                    parser = parser_cls(self.graph)
                    parser.parse(current / filename, file_id)

                    lang = ext.lstrip('.')
                    self.graph.parser_stats[lang]["files"] += 1
                    self.graph.parser_stats[lang]["method"] = getattr(parser, 'METHOD', 'unknown')

        resolved = self.graph.resolve_dangling_edges()
        if resolved:
            print(f"   🔧 Auto-registered {resolved} dangling type targets")

        self.graph.build_communities()

        print(f"✅ Scan complete: {len(self.graph.nodes)} nodes, {len(self.graph.edges)} edges")
        print(f"   Parsers used: {list(self.graph.parser_stats.keys())}")
        return self.graph.nodes, self.graph.edges