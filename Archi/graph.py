"""Graph module — Smarter filtering with PageRank & Edge Rewiring."""
import networkx as nx
from datetime import datetime
from collections import defaultdict
import re

class Graph:
    BUILTIN_TYPES = {'int', 'str', 'bool', 'float', 'bytes', 'list', 'dict', 'set', 'tuple', 'None'}

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
        self.communities = []

        self.semantic_index = defaultdict(list)
        self._file_suffix_index = defaultdict(list)
        self.module_to_file = {}

    def _normalize(self, node_id: str) -> str:
        return node_id.replace('\\', '/')

    def register_file_id(self, file_id: str):
        file_id = self._normalize(file_id)
        parts = file_id.split('/')
        for i in range(len(parts)):
            suffix = '/'.join(parts[i:])
            self._file_suffix_index[suffix].append(file_id)

    def resolve_path_alias(self, alias: str, file_id: str = None):
        alias = self._normalize(alias)
        candidates = [
            alias, alias + '.ts', alias + '.tsx', alias + '.js', alias + '.jsx',
            alias + '/index.ts', alias + '/index.tsx', alias + '/index.js'
        ]
        for cand in candidates:
            hits = self._file_suffix_index.get(cand)
            if not hits:
                continue
            if len(hits) == 1 or not file_id:
                return hits[0]
            file_parts = file_id.split('/')
            def shared_prefix_len(hit):
                hit_parts = hit.split('/')
                n = 0
                for a, b in zip(file_parts, hit_parts):
                    if a != b: break
                    n += 1
                return n
            return max(hits, key=shared_prefix_len)
        return None

    def add_node(self, node_id: str, node_type: str, external: bool = False, description: str = ""):
        node_id = self._normalize(node_id)
        if node_id not in self.node_types:
            self.nodes.append(node_id)
            self.node_types[node_id] = node_type
            self.node_external[node_id] = external
            self.graph.add_node(node_id, type=node_type, external=external, community=-1)
            self._index_keywords(node_id, node_type)
        elif external and not self.node_external[node_id]:
            if self.node_types[node_id] == "unresolved":
                self.node_external[node_id] = True
                self.graph.nodes[node_id]['external'] = True

    def _index_keywords(self, node_id: str, node_type: str):
        keywords = set(re.findall(r'\w+', node_id.lower()))
        keywords.add(node_type.lower())
        for word in keywords:
            if len(word) > 2:
                self.semantic_index[word].append(node_id)

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
            self.add_node(target, "unresolved", external=True)
        return len(dangling)

    def build_communities(self):
        try:
            undirected = self.graph.to_undirected()
            skip = {'unresolved', 'folder'}
            undirected.remove_nodes_from(
                [n for n in undirected.nodes if self.node_types.get(n) in skip]
            )
            self.communities = list(nx.community.louvain_communities(undirected, seed=42))
            for i, comm in enumerate(self.communities):
                for node in comm:
                    if node in self.graph.nodes:
                        self.graph.nodes[node]['community'] = i
                        self.node_community[node] = i
        except Exception as e:
            print(f"   ⚠️ Community detection failed: {e}")
            self.communities = []

    def get_god_nodes(self, top: int = 10):
        all_degrees = [(n, d) for n, d in self.graph.degree() if self.node_types.get(n) != 'folder']
        internal = [(n, d) for n, d in all_degrees if not self.node_external.get(n, False)]
        external = [(n, d) for n, d in all_degrees if self.node_external.get(n, False)]
        return {
            "internal": sorted(internal, key=lambda x: x[1], reverse=True)[:top],
            "external": sorted(external, key=lambda x: x[1], reverse=True)[:top]
        }

    # ── SMART MODE 2.0 ──────────────────────────────────────────────────

    IMPORTANT_TYPES = {
        "file", "component", "router", "service", "model", "main",
        "react_component", "react_hook", "nestjs_controller", "nestjs_service",
        "nestjs_module", "nestjs_endpoint", "class", "function", "interface",
        "type_alias", "enum", "django_model", "django_view", "fastapi_endpoint",
        "fastapi_schema",
    }

    NOISE_SYMBOLS = {'len', 'fmt', 'log', 'err', 'req', 'res', 'ctx', 'val', 'key', 'obj', 'arr', 'str', 'int', 'map', 'set'}

    def _is_smart_keep(self, node_id: str, node_type: str, ranks: dict) -> bool:
        # 1. Type-based filtering for files/folders
        if '::' not in node_id:
            return node_type in self.IMPORTANT_TYPES or node_type == "folder"

        # 2. Symbol-based filtering
        symbol = node_id.split('::', 1)[1]
        if len(symbol) < 3 or symbol.startswith('_') or symbol.lower().startswith('test'):
            return False
        if symbol.lower() in self.NOISE_SYMBOLS:
            return False

        # 3. Importance-based filtering (PageRank Centrality)
        rank = ranks.get(node_id, 0)
        if node_type in self.IMPORTANT_TYPES:
            return rank > 0.000001  # Keep almost any important typed node
        elif node_type == "function":
            return rank > 0.00005   # Only keep highly-connected functions
        
        return rank > 0.00001

    def to_dict(self, top_gods: int = 10, mode: str = "classic") -> dict:
        god_nodes = self.get_god_nodes(top_gods)

        if mode == "smart":
            # Calculate PageRank to determine true architectural importance
            try:
                ranks = nx.pagerank(self.graph, alpha=0.85)
            except Exception:
                ranks = {n: 1.0 for n in self.nodes}

            keep_ids = {
                nid for nid in self.nodes
                if not self.node_external.get(nid) and self._is_smart_keep(nid, self.node_types.get(nid, "unknown"), ranks)
            }
            
            # 🧠 SMART REWIRING: Prevent orphan nodes when intermediate drops out
            # If A -> B -> C, but B is dropped, rewire to A -> C so the flow survives
            smart_edges = []
            seen_smart_edges = set()
            
            for e in self.edges:
                src, tgt = e['source'], e['target']
                src_in = src in keep_ids
                tgt_in = tgt in keep_ids

                if src_in and tgt_in:
                    key = (src, tgt, e['type'])
                    if key not in seen_smart_edges:
                        smart_edges.append(e)
                        seen_smart_edges.add(key)
                elif src_in and not tgt_in:
                    # Target dropped: look for kept descendants of the dropped target
                    for successor in self.graph.successors(tgt):
                        if successor in keep_ids:
                            key = (src, successor, e['type'])
                            if key not in seen_smart_edges:
                                smart_edges.append({"source": src, "target": successor, "type": e['type']})
                                seen_smart_edges.add(key)
                elif not src_in and tgt_in:
                    # Source dropped: look for kept ancestors
                    for predecessor in self.graph.predecessors(src):
                        if predecessor in keep_ids:
                            key = (predecessor, tgt, e['type'])
                            if key not in seen_smart_edges:
                                smart_edges.append({"source": predecessor, "target": tgt, "type": e['type']})
                                seen_smart_edges.add(key)

            node_list = [nid for nid in self.nodes if nid in keep_ids]
            edge_list = smart_edges
        else:
            node_list = self.nodes
            edge_list = self.edges

        return {
            "nodes": [
                {
                    "id": nid,
                    "type": self.node_types.get(nid, "unknown"),
                    "community": self.node_community.get(nid, -1),
                    "external": self.node_external.get(nid, False)
                }
                for nid in node_list
            ],
            "edges": edge_list,
            "metadata": {
                "project": self.project_name,
                "mode": mode,
                "total_nodes": len(node_list),
                "total_edges": len(edge_list),
                "generated_by": "Archi Mapper v1.1",
                "scan_date": datetime.now().isoformat(),
                "communities_count": len(self.communities),
                "god_nodes": {
                    "internal": [{"node": n, "degree": d} for n, d in god_nodes["internal"]],
                    "external": [{"node": n, "degree": d} for n, d in god_nodes["external"]]
                },
                "parser_info": dict(self.parser_stats)
            }
        }