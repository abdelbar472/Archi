"""Python AST Parser — Primary parser for Python files"""
import ast
from pathlib import Path
from typing import Optional
from collections import defaultdict

from ..base import BaseParser


class PythonASTParser(BaseParser):
    METHOD = "python-ast"

    def parse(self, file_path: Path, file_id: str):
        content = self._safe_read(file_path)
        if not content:
            return

        try:
            tree = ast.parse(content)
            visitor = _PythonVisitor(self.graph, content, file_id)
            visitor.visit(tree)
        except SyntaxError:
            # Fallback to regex if AST fails
            self._regex_fallback(file_path, file_id)
        except Exception as e:
            print(f"   ⚠️ Python AST error in {file_path.name}: {e}")
            self._regex_fallback(file_path, file_id)

    def _regex_fallback(self, file_path: Path, file_id: str):
        try:
            from .python_fallback import PythonFallback
            PythonFallback(self.graph).parse(file_path, file_id)
        except Exception:
            pass


class _PythonVisitor(ast.NodeVisitor):
    def __init__(self, graph, content: str, file_id: str):
        self.graph = graph
        self.content = content
        self.file_id = file_id

    def visit_ClassDef(self, node):
        name = node.name
        ntype = self._classify_class(node)
        self._add_def(name, ntype)

        self.generic_visit(node)  # visit methods inside

    def visit_FunctionDef(self, node):
        name = node.name
        ntype = self._classify_function(node)
        self._add_def(name, ntype)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        name = node.name
        self._add_def(name, "async_function")
        self.generic_visit(node)

    def _classify_class(self, node) -> str:
        # Django Model
        if any(base.id == 'models.Model' for base in node.bases if hasattr(base, 'id')):
            return "django_model"
        # Pydantic / FastAPI
        if any(getattr(base, 'id', '') in ('BaseModel', 'BaseSettings') for base in node.bases):
            return "pydantic_model"
        return "class"

    def _classify_function(self, node) -> str:
        name = node.name.lower()
        if 'task' in name or any(d.id == 'task' for d in node.decorator_list if hasattr(d, 'id')):
            return "celery_task"
        if any(hasattr(d, 'attr') and d.attr in ('get', 'post', 'put', 'delete') for d in node.decorator_list):
            return "fastapi_endpoint"
        if name.startswith('test_'):
            return "test"
        return "function"

    def _add_def(self, name: str, node_type: str):
        node_id = f"{self.file_id}::{name}"
        self.graph.add_node(node_id, node_type, external=False)
        self.graph.add_edge(self.file_id, node_id, "defines")