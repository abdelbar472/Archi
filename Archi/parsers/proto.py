"""Protobuf parser — extracts services/messages, links to generated stubs."""
import re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from base import BaseParser


class ProtoParser(BaseParser):
    METHOD = "regex"

    SERVICE_PATTERN = re.compile(r'^service\s+(\w+)\s*\{', re.MULTILINE)
    MESSAGE_PATTERN = re.compile(r'^message\s+(\w+)\s*\{', re.MULTILINE)
    RPC_PATTERN = re.compile(r'^\s*rpc\s+(\w+)\s*\(', re.MULTILINE)
    IMPORT_PATTERN = re.compile(r'^import\s+"(.+?)";', re.MULTILINE)

    def parse(self, file_path: Path, file_id: str):
        content = self._safe_read(file_path)
        proto_name = file_path.stem

        for match in self.SERVICE_PATTERN.finditer(content):
            svc_id = self._add_def(file_id, match.group(1), "service")
            py_stub = f"{proto_name}_pb2_grpc.py"
            if self.graph.is_known(py_stub):
                self.graph.add_edge(svc_id, py_stub, "generates")
            go_stub = f"{proto_name}.pb.go"
            if self.graph.is_known(go_stub):
                self.graph.add_edge(svc_id, go_stub, "generates")

        for match in self.MESSAGE_PATTERN.finditer(content):
            self._add_def(file_id, match.group(1), "message")

        for match in self.RPC_PATTERN.finditer(content):
            self._add_def(file_id, match.group(1), "rpc")

        for match in self.IMPORT_PATTERN.finditer(content):
            imported = match.group(1)
            self.graph.add_node(imported, "proto", external=True)
            self._add_import(file_id, imported)