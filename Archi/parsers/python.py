"""Python parser — AST-based with deep FastAPI + Django detection and cross-file resolution."""
import ast
from pathlib import Path
from collections import defaultdict

from .base import BaseParser


class PythonParser(BaseParser):
    METHOD = "ast"

    # Framework signatures
    FASTAPI_DECORATORS = {'get', 'post', 'put', 'delete', 'patch', 'options', 'head', 'trace'}
    DJANGO_VIEW_BASES = {'APIView', 'ViewSet', 'ModelViewSet', 'GenericAPIView', 
                        'CreateAPIView', 'ListAPIView', 'RetrieveAPIView',
                        'UpdateAPIView', 'DestroyAPIView', 'ListCreateAPIView'}
    DJANGO_MODEL_BASES = {'Model', 'AbstractUser', 'AbstractBaseUser'}
    DJANGO_SERIALIZER_BASES = {'ModelSerializer', 'Serializer', 'HyperlinkedModelSerializer'}
    CALL_NOISE = {'int', 'str', 'bool', 'list', 'dict', 'len', 'print', 'range', 'super'}

    def __init__(self, graph):
        super().__init__(graph)
        self._file_imports = defaultdict(dict)  # file_id -> {alias: target}

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

        # Pass 1: Classes
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

        # Pass 2: Top-level functions
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_type = self._detect_function_type(node)
                func_id = self._add_def(file_id, node.name, func_type)
                self._extract_annotations(node, func_id)
                func_nodes.append((func_id, node))

        # Pass 3: Imports (build map for cross-file resolution)
        self._parse_imports(tree, file_id)

        # Pass 4: Intra-file + Cross-file calls
        self._resolve_calls(func_nodes, file_id)

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
        elif any('APIRouter' in self._expr_to_str(b) for b in node.bases):
            node_type = "fastapi_router"
        else:
            node_type = self._detect_type(file_id)

        return self._add_def(file_id, node.name, node_type)

    def _detect_function_type(self, node):
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call):
                name = self._expr_to_str(dec.func)
                if any(d in name for d in self.FASTAPI_DECORATORS):
                    return "fastapi_endpoint"
                if 'receiver' in name:
                    return "django_signal"
        return "function"

    def _expr_to_str(self, expr):
        try:
            return ast.unparse(expr) if hasattr(ast, 'unparse') else str(expr)
        except:
            return str(expr)

    def _extract_database_mapping(self, node, class_id, file_id):
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and isinstance(item.value, ast.Constant):
                        if target.id == "__tablename__":
                            table = f"table:{item.value.value}"
                            self.graph.add_node(table, "table")
                            self.graph.add_edge(class_id, table, "maps_to")
                            return
                        if target.id in ("__collection__", "collection"):
                            coll = f"collection:{item.value.value}"
                            self.graph.add_node(coll, "collection")
                            self.graph.add_edge(class_id, coll, "maps_to")
                            return

    def _extract_inheritance(self, node, class_id):
        for base in node.bases:
            try:
                base_name = self._expr_to_str(base)
                if base_name and base_name not in ('object', ''):
                    self.graph.add_edge(class_id, base_name, "inherits")
            except:
                pass

    def _extract_annotations(self, func_node, func_id: str):
        for arg in func_node.args.args:
            type_name = self._resolve_annotation(arg.annotation)
            if type_name:
                self._add_type_edge(func_id, type_name, "param_type")

        if func_node.returns:
            type_name = self._resolve_annotation(func_node.returns)
            if type_name:
                self._add_type_edge(func_id, type_name, "return_type")

    def _resolve_annotation(self, annotation):
        if not annotation:
            return None
        if isinstance(annotation, ast.Name):
            return annotation.id
        if isinstance(annotation, ast.Attribute):
            return annotation.attr
        if isinstance(annotation, ast.Subscript):
            return self._subscript_base(annotation)
        return None

    def _subscript_base(self, node):
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Subscript):
            return self._subscript_base(node.value)
        if isinstance(node, ast.Attribute):
            return node.attr
        return None

    def _parse_imports(self, tree, file_id: str):
        """Build import map for cross-file resolution"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                target = f"{node.module.replace('.', '/')}.py"
                for alias in node.names:
                    self._file_imports[file_id][alias.asname or alias.name] = target
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    target = f"{alias.name.split('.')[0]}.py"
                    self._file_imports[file_id][alias.asname or alias.name] = target

    def _resolve_calls(self, func_nodes, file_id: str):
        """Intra-file + Cross-file call resolution"""
        imports = self._file_imports.get(file_id, {})

        for func_id, func_node in func_nodes:
            for child in ast.walk(func_node):
                if not isinstance(child, ast.Call):
                    continue
                if not isinstance(child.func, (ast.Name, ast.Attribute)):
                    continue

                callee = self._call_to_str(child.func)
                if not callee or callee in self.CALL_NOISE:
                    continue

                # Intra-file call
                if '.' not in callee:
                    target_id = f"{file_id}::{callee}"
                    if self.graph.is_known(target_id):
                        self.graph.add_edge(func_id, target_id, "calls")
                    continue

                # Cross-file call resolution
                root = callee.split('.')[0]
                if root in imports:
                    base_target = imports[root]
                    resolved = f"{base_target.rsplit('.py', 1)[0]}::{callee.split('.', 1)[1]}"
                    if self.graph.is_known(resolved):
                        self.graph.add_edge(func_id, resolved, "calls")

    def _call_to_str(self, func):
        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):
            try:
                return f"{self._call_to_str(func.value)}.{func.attr}"
            except:
                return None
        return None

    def _detect_type(self, filename: str) -> str:
        lower = filename.lower()
        if any(x in lower for x in ['router', 'route']): return "router"
        if 'service' in lower: return "service"
        if any(x in lower for x in ['model', 'schema']): return "model"
        if any(x in lower for x in ['main', 'app', 'index']): return "main"
        if 'grpc' in lower: return "grpc"
        return "file"