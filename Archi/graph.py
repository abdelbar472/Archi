"""Graph module: shared graph state, community detection, god nodes + enhanced semantics."""
import networkx as nx
from datetime import datetime
from collections import defaultdict
from pathlib import Path
import re

class Graph:
    BUILTIN_TYPES = {
        'int', 'str', 'bool', 'float', 'bytes', 'list', 'dict', 'set', 'tuple',
        'None', 'Any', 'Optional', 'Dict', 'List', 'Set', 'Tuple', 'Type',
        'Union', 'Callable', 'Awaitable', 'Coroutine', 'AsyncIterable',
        'AsyncIterator', 'Iterable', 'Iterator', 'Generator', 'Sequence', 'Mapping',
        'Literal', 'Annotated', 'Final', 'ClassVar', 'Self', 'Never', 'NoReturn'
    }

    EXTERNAL_TYPES = {
        'AsyncSession', 'Session', 'Request', 'Response', 'FastAPI',
        'HTTPException', 'HTTPAuthorizationCredentials', 'Depends',
        'BackgroundTasks', 'WebSocket', 'UploadFile', 'Query', 'Path',
        'Body', 'Header', 'Cookie', 'File', 'BaseModel', 'Field',
        'validator', 'root_validator', 'SQLAlchemy', 'declarative_base',
        'Column', 'Integer', 'String', 'Boolean', 'DateTime', 'ForeignKey',
        'relationship', 'Index', 'Table', 'MetaData', 'create_engine',
        'select', 'insert', 'update', 'delete', 'join'
    }

    def __init__(self, project_name: str):
        self.project_name = project_name
        self.nodes = []
        self.node_types = {}
        self.node_external = {}
        self.node_community = {}
        self.edges = []
        self._edge_set = set()
        self.graph = nx.DiGraph()
        self.parser_stats = defaultdict(lambda: {"files": 0, "method": "unknown"})

        # Enhanced Semantic Capabilities
        self.semantic_index = defaultdict(list)      # word → list of node_ids
        self.node_keywords = {}                      # node_id → set of keywords
        self.node_descriptions = {}                  # node_id → description (if available)
        self.communities = []

    def _normalize(self, node_id: str) -> str:
        return node_id.replace('\\', '/')

    def add_node(self, node_id: str, node_type: str, external: bool = False, description: str = ""):
        node_id = self._normalize(node_id)
        # FIXED: Only mark true external types — don't override explicit external=False
        # for internal types that happen to have node_type "type" or "builtin"
        if not external and node_id in self.EXTERNAL_TYPES:
            external = True
        if node_id not in self.node_types:
            self.nodes.append(node_id)
            self.node_types[node_id] = node_type
            self.node_external[node_id] = external
            self.graph.add_node(node_id, type=node_type, external=external, community=-1)

            if description:
                self.node_descriptions[node_id] = description

            self._index_keywords(node_id, node_type, description)

    def _index_keywords(self, node_id: str, node_type: str, description: str = ""):
        """Extract rich keywords for semantic search"""
        keywords = set()

        # From node ID (split on common separators)
        parts = re.findall(r'\w+', node_id.lower())
        keywords.update(parts)

        # From node type
        keywords.add(node_type.lower())

        # From description / docstring if available
        if description:
            desc_words = re.findall(r'\w+', description.lower())
            keywords.update(w for w in desc_words if len(w) > 2)

        # Domain-specific boosts
        nid_lower = node_id.lower()
        if 'service' in nid_lower: keywords.add('service')
        if 'router' in nid_lower: keywords.add('router')
        if any(x in nid_lower for x in ['table', 'model', 'schema']): keywords.add('database')
        if 'grpc' in nid_lower: keywords.add('grpc')
        if 'rag' in nid_lower: keywords.add('rag')
        if 'auth' in nid_lower: keywords.add('auth')

        self.node_keywords[node_id] = keywords

        # Inverted index for fast search
        for word in keywords:
            if len(word) > 2:
                self.semantic_index[word].append(node_id)

    def search(self, query: str, limit: int = 15):
        """Semantic keyword search"""
        query_words = [w.lower() for w in re.findall(r'\w+', query) if len(w) > 1]
        if not query_words:
            return []

        scores = defaultdict(int)
        for word in query_words:
            if word in self.semantic_index:
                for node_id in self.semantic_index[word]:
                    scores[node_id] += 2  # base score

        # Boost exact matches and important nodes
        results = []
        for node_id, score in scores.items():
            boost = 0
            nid_lower = node_id.lower()
            if any(q in nid_lower for q in query_words):
                boost += 5
            if self.node_types.get(node_id) in ['service', 'router', 'model', 'table', 'collection']:
                boost += 3
            results.append((node_id, score + boost))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def is_known(self, node_id: str) -> bool:
        return self._normalize(node_id) in self.node_types

    def add_edge(self, source: str, target: str, edge_type: str):
        source = self._normalize(source)
        target = self._normalize(target)
        if not source or not target or source == target:
            return
        key = (source, target, edge_type)
        if key in self._edge_set:
            return
        self._edge_set.add(key)
        self.edges.append({"source": source, "target": target, "type": edge_type})
        self.graph.add_edge(source, target, type=edge_type)

    def resolve_dangling_edges(self):
        node_ids = set(self.nodes)
        dangling = {e['target'] for e in self.edges if e['target'] not in node_ids}
        for target in dangling:
            is_external = target in self.EXTERNAL_TYPES or target in self.BUILTIN_TYPES
            self.add_node(target, "type", external=is_external)
        return len(dangling)

    def build_communities(self):
        try:
            undirected = self.graph.to_undirected()
            type_nodes = [n for n in undirected.nodes if self.node_types.get(n) == 'type']
            undirected.remove_nodes_from(type_nodes)
            self.communities = list(nx.community.louvain_communities(undirected, seed=42))
            for i, comm in enumerate(self.communities):
                for node in comm:
                    if node in self.graph.nodes:
                        self.graph.nodes[node]['community'] = i
                        self.node_community[node] = i
        except Exception as e:
            print(f"   ⚠️ Community detection failed: {e}")

    def get_god_nodes(self, top: int = 10):
        NOISE = self.BUILTIN_TYPES | {'root', 'folder', 'file'}
        all_degrees = [(n, d) for n, d in self.graph.degree() 
                       if n not in NOISE and self.node_types.get(n) != 'folder']

        internal = [(n, d) for n, d in all_degrees if not self.node_external.get(n, False)]
        external = [(n, d) for n, d in all_degrees if self.node_external.get(n, False)]

        return {
            "internal": sorted(internal, key=lambda x: x[1], reverse=True)[:top],
            "external": sorted(external, key=lambda x: x[1], reverse=True)[:top]
        }

    def to_dict(self, top_gods: int = 10) -> dict:
        god_nodes = self.get_god_nodes(top_gods)
        return {
            "nodes": [
                {
                    "id": nid,
                    "type": self.node_types.get(nid, "unknown"),
                    "community": self.node_community.get(nid, -1),
                    "external": self.node_external.get(nid, False)
                }
                for nid in self.nodes
            ],
            "edges": self.edges,
            "metadata": {
                "project": self.project_name,
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "generated_by": "Tempory Mapper v1.0",
                "scan_date": datetime.now().isoformat(),
                "communities_count": len(self.communities),
                "god_nodes": {
                    "internal": [{"node": n, "degree": d} for n, d in god_nodes["internal"]],
                    "external": [{"node": n, "degree": d} for n, d in god_nodes["external"]]
                },
                "parser_info": dict(self.parser_stats),
                "dangling_edges_resolved": True,
                "call_graph_scope": "cross-file"
            }
        }