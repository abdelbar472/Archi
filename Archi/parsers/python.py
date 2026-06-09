"""Python AST Parser — Passes: structure, inheritance, imports, cross-file calls."""
import ast
from pathlib import Path
from collections import defaultdict
from parsers.base import BaseParser


class PythonParser(BaseParser):
    METHOD = "ast"
    SUPPORTED_EXTENSIONS = {".py"}

    def __init__(self, graph):
        super().__init__(graph)
        # Import map: local name -> (source_module, imported_name, is_from_import)
        # Built during Pass 2, used by Pass 3
        self._file_imports = {}  # file_id -> {local_name: (resolved_node_id, is_external)}

    def parse(self, file_path: Path, file_id: str):
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except Exception:
            return

        # Pass 1: Structure (classes, functions, methods, calls intra-file)
        self._pass1_structure(tree, file_id)

        # Pass 2: Import resolution
        self._pass2_imports(tree, file_id)

        # Pass 3: Cross-file calls (uses import map from Pass 2)
        self._pass3_crossfile_calls(tree, file_id)

    # ─────────────────────────────────────────────────────────────────────────
    # PASS 1 — Structure
    # ─────────────────────────────────────────────────────────────────────────
    def _pass1_structure(self, tree: ast.AST, file_id: str):
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_id = f"{file_id}::{node.name}"
                self.graph.add_node(class_id, "class")
                self.graph.add_edge(file_id, class_id, "contains")

                # Inheritance edges (base classes)
                for base in node.bases:
                    base_name = self._expr_to_str(base)
                    if base_name:
                        # Will be resolved in Pass 2 if it's an import
                        # For now, add a tentative edge — Pass 2 may upgrade it
                        self.graph.add_edge(class_id, base_name, "inherits")

                # Methods
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_id = f"{class_id}::{item.name}"
                        self.graph.add_node(method_id, "method")
                        self.graph.add_edge(class_id, method_id, "contains")
                        self._extract_calls(item, file_id, method_id)

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Top-level function
                func_id = f"{file_id}::{node.name}"
                self.graph.add_node(func_id, "function")
                self.graph.add_edge(file_id, func_id, "contains")
                self._extract_calls(node, file_id, func_id)

    def _extract_calls(self, node: ast.AST, file_id: str, caller_id: str):
        """Extract function calls within a function/method body."""
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                callee = self._call_to_str(child.func)
                if callee:
                    # Intra-file call (tentative — Pass 3 may upgrade to cross-file)
                    self.graph.add_edge(caller_id, callee, "calls")

    def _expr_to_str(self, expr) -> str:
        """Convert an AST expression to a dotted name string."""
        if isinstance(expr, ast.Name):
            return expr.id
        elif isinstance(expr, ast.Attribute):
            val = self._expr_to_str(expr.value)
            return f"{val}.{expr.attr}" if val else expr.attr
        return ""

    def _call_to_str(self, expr) -> str:
        """Convert a call expression to a dotted name."""
        return self._expr_to_str(expr)

    # ─────────────────────────────────────────────────────────────────────────
    # PASS 2 — Import Resolution
    # ─────────────────────────────────────────────────────────────────────────
    def _pass2_imports(self, tree: ast.AST, file_id: str):
        """Build import map for this file. Maps local names to resolved node IDs."""
        imports = {}
        file_dir = Path(file_id).parent if "/" in file_id else ""

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    local = alias.asname if alias.asname else alias.name
                    # Try to resolve to a file in the project
                    resolved = self._resolve_module(alias.name, file_dir)
                    if resolved:
                        imports[local] = (resolved, False)  # (node_id, is_external)
                    else:
                        # Might be external — mark as tentative
                        imports[local] = (alias.name, True)

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    local = alias.asname if alias.asname else alias.name
                    # from auth.services import authenticate_user
                    # -> module="auth.services", name="authenticate_user"
                    resolved = self._resolve_import_from(module, alias.name, file_dir)
                    if resolved:
                        imports[local] = (resolved, False)
                    else:
                        imports[local] = (f"{module}.{alias.name}" if module else alias.name, True)

        self._file_imports[file_id] = imports

    def _resolve_module(self, module_name: str, file_dir: str) -> str:
        """Try to resolve 'auth.services' to a file node like 'auth/services.py'."""
        parts = module_name.split(".")
        # Try progressively: auth/services.py, auth/services/__init__.py
        for i in range(len(parts), 0, -1):
            prefix = "/".join(parts[:i])
            candidate = f"{prefix}.py"
            if self.graph.is_known(candidate):
                return candidate
            candidate_init = f"{prefix}/__init__.py"
            if self.graph.is_known(candidate_init):
                return candidate_init
        return None

    def _resolve_import_from(self, module: str, name: str, file_dir: str) -> str:
        """Resolve 'from auth.services import authenticate_user' to a node ID."""
        # First, try to find the module file
        module_file = self._resolve_module(module, file_dir)
        if not module_file:
            return None

        # Then try to find the specific name inside that file
        candidates = [
            f"{module_file}::{name}",           # function or class
            f"{module_file}::{name}.{name}",    # nested (less common)
        ]
        for c in candidates:
            if self.graph.is_known(c):
                return c

        # If the name is a module itself (from auth import services)
        sub_module = f"{module}.{name}".replace(".", "/")
        sub_candidate = f"{sub_module}.py"
        if self.graph.is_known(sub_candidate):
            return sub_candidate

        return None

    # ─────────────────────────────────────────────────────────────────────────
    # PASS 3 — Cross-File Calls
    # ─────────────────────────────────────────────────────────────────────────
    def _pass3_crossfile_calls(self, tree: ast.AST, file_id: str):
        """Resolve intra-file 'calls' edges to cross-file targets using import map."""
        imports = self._file_imports.get(file_id, {})
        if not imports:
            return

        # Collect all call sites in this file
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                caller_id = f"{file_id}::{node.name}"
                if not self.graph.is_known(caller_id):
                    continue

                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        callee_str = self._call_to_str(child.func)
                        if not callee_str:
                            continue

                        # Try to resolve via import map
                        resolved = self._resolve_call(callee_str, imports)
                        if resolved and resolved != callee_str:
                            # Add a proper cross-file call edge
                            self.graph.add_edge(caller_id, resolved, "calls")

    def _resolve_call(self, callee_str: str, imports: dict) -> str:
        """Resolve a call like 'authenticate_user()' or 'AuthService.login()' using imports."""
        parts = callee_str.split(".")
        if not parts:
            return callee_str

        head = parts[0]
        if head in imports:
            resolved, is_external = imports[head]
            if is_external:
                return resolved  # External type, keep as-is

            if len(parts) == 1:
                # Direct import: authenticate_user -> auth/services.py::authenticate_user
                return resolved
            else:
                # Attribute access: AuthService.login -> auth/services.py::AuthService.login
                # But resolved might be a file, so we need to construct the full path
                tail = ".".join(parts[1:])
                # If resolved is a file node, append ::tail
                if resolved.endswith(".py"):
                    return f"{resolved}::{tail}"
                return f"{resolved}.{tail}"

        return callee_str