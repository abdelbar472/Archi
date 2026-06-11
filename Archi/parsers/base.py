"""Base parser interface — shared helpers for all language parsers."""
from pathlib import Path


class BaseParser:
    METHOD = "unknown"

    def __init__(self, graph):
        self.graph = graph

    def parse(self, file_path: Path, file_id: str):
        raise NotImplementedError("Subclasses must implement parse()")

    def _safe_read(self, file_path: Path) -> str:
        try:
            return file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return file_path.read_text(encoding="latin-1", errors="ignore")
        except Exception:
            return ""

    def _add_def(self, parent_id: str, name: str, node_type: str) -> str:
        """Register a definition node and add a defines edge."""
        node_id = f"{parent_id}::{name}"
        self.graph.add_node(node_id, node_type)
        self.graph.add_edge(parent_id, node_id, "defines")
        return node_id

    def _add_type_edge(self, func_id: str, type_name: str, edge_type: str = "param_type"):
        """Add type annotation edge (param_type / return_type)"""
        if not type_name:
            return
        if hasattr(self.graph, 'BUILTIN_TYPES') and type_name in self.graph.BUILTIN_TYPES:
            return
        self.graph.add_edge(func_id, type_name, edge_type)