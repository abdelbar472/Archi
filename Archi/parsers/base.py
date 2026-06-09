"""Base parser interface."""
from pathlib import Path


class BaseParser:
    METHOD = "unknown"
    SUPPORTED_EXTENSIONS = set()

    def __init__(self, graph):
        self.graph = graph

    def parse(self, file_path: Path, file_id: str):
        raise NotImplementedError