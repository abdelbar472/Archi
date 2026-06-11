"""Python parser — AST-based with rich framework detection (FastAPI + Django)."""
import ast
from pathlib import Path

from .base import BaseParser


class PythonParser(BaseParser):
    METHOD = "ast"

    # Framework detection helpers
    FASTAPI_DECORATORS = {'get', 'post', 'put', 'delete', 'patch', 'options', 'head', 'trace'}
    DJANGO_VIEW_BASES = {'APIView', 'ViewSet', 'ModelViewSet', 'GenericAPIView', 
                        'CreateAPIView', 'ListAPIView', 'RetrieveAPIView',
                        'UpdateAPIView', 'DestroyAPIView', 'ListCreateAPIView'}
    DJANGO_MODEL_BASES = {'Model', 'AbstractUser', 'AbstractBaseUser'}
    DJANGO_SERIALIZER_BASES = {'ModelSerializer', 'Serializer', 'HyperlinkedModelSerializer'}

    def parse(self, file_path: Path, file_id: str):
        try:
            content = self._safe_read(file_path)
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError:
            return

        # Semantic indexing
        words = {w.lower() for w in content.split() if len(w) > 3}
        for w in list(words)[:30]:
            self.graph.semantic_index[w].append(file_id)

        func_nodes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_id = self._register_class(node, file_id)
                self._extract_database_mapping(node, class_id, file_id)
                self._extract_inheritance(node, class_id)

                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_id = self._add_def(class_id, item.name, "method")
                        self._extract_annotations(item, method_id)
                        func_nodes.append((method_id, item))

        # Top-level functions
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_id = self._add_def(file_id, node.name, "function")
                self._extract_annotations(node, func_id)
                func_nodes.append((func_id, node))

        # Intra-file calls
        for func_id, func_node in func_nodes:
            for child in ast.walk(func_node):
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                    target_id = f"{file_id}::{child.func.id}"
                    if self.graph.is_known(target_id) and target_id != func_id:
                        self.graph.add_edge(func_id, target_id, "calls")

        # Imports
        self._parse_imports(tree, file_id)

    def _register_class(self, node: ast.ClassDef, file_id: str) -> str:
        base_names = {self._expr_to_str(b) for b in node.bases}

        if base_names & self.DJANGO_MODEL_BASES:
            node_type = "django_model"
        elif base_names & self.DJANGO_VIEW_BASES:
            node_type = "django_view"
        elif base_names & self.DJANGO_SERIALIZER_BASES:
            node_type = "django_serializer"
        elif any('AppConfig' in b for b in base_names):
            node_type = "django_app"
        elif any('BaseModel' in b for b in base_names):
            node_type = "fastapi_schema"
        else:
            node_type = self._detect_type(file_id)

        return self._add_def(file_id, node.name, node_type)

    def _expr_to_str(self, expr):
        try:
            return ast.unparse(expr) if hasattr(ast, 'unparse') else str(expr)
        except:
            return str(expr)

    def _extract_database_mapping(self, node: ast.ClassDef, class_id: str, file_id: str):
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and isinstance(item.value, ast.Constant):
                        if target.id == "__tablename__":
                            table_name = f"table:{item.value.value}"
                            self.graph.add_node(table_name, "table")
                            self.graph.add_edge(class_id, table_name, "maps_to")
                            return
                        if target.id in ("__collection__", "collection"):
                            coll_name = f"collection:{item.value.value}"
                            self.graph.add_node(coll_name, "collection")
                            self.graph.add_edge(class_id, coll_name, "maps_to")
                            return

    def _extract_inheritance(self, node: ast.ClassDef, class_id: str):
        for base in node.bases:
            try:
                base_name = self._expr_to_str(base)
                if base_name and base_name not in ('object', ''):
                    self.graph.add_edge(class_id, base_name, "inherits")
            except:
                pass

    def _extract_annotations(self, func_node, func_id: str):
        """Extract param and return type annotations"""
        for arg in func_node.args.args:
            type_name = self._resolve_annotation(arg.annotation)
            if type_name:
                self._add_type_edge(func_id, type_name, "param_type")

        if func_node.returns:
            type_name = self._resolve_annotation(func_node.returns)
            if type_name:
                self._add_type_edge(func_id, type_name, "return_type")

    def _resolve_annotation(self, annotation) -> str | None:
        if annotation is None:
            return None
        if isinstance(annotation, ast.Name):
            return annotation.id
        if isinstance(annotation, ast.Subscript):
            return self._subscript_base(annotation)
        if isinstance(annotation, ast.Attribute):
            return annotation.attr
        if isinstance(annotation, ast.Constant) and isinstance(annotation.value, str):
            return annotation.value
        return None

    def _subscript_base(self, node) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Subscript):
            return self._subscript_base(node.value)
        if isinstance(node, ast.Attribute):
            return node.attr
        return None

    def _parse_imports(self, tree, file_id: str):
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                target = f"{node.module.replace('.', '/')}.py"
                if self.graph.is_known(target):
                    self.graph.add_edge(file_id, target, "imports")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    target = f"{alias.name.split('.')[0]}.py"
                    if self.graph.is_known(target):
                        self.graph.add_edge(file_id, target, "imports")

    def _detect_type(self, filename: str) -> str:
        lower = filename.lower()
        if any(x in lower for x in ['router', 'route']): return "router"
        if 'service' in lower: return "service"
        if any(x in lower for x in ['model', 'schema']): return "model"
        if any(x in lower for x in ['main', 'app', 'index']): return "main"
        if 'grpc' in lower: return "grpc"
        return "file"