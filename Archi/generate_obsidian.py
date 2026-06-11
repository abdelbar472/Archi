"""Obsidian Markdown Generator — creates rich, well-connected knowledge base."""
import json
import sys
import shutil
from pathlib import Path
from collections import defaultdict
import re


def sanitize_filename(name: str) -> str:
    """Safe filename for Windows + Obsidian"""
    name = re.sub(r'[\\/:*?"<>|]', '_', name)
    name = name.replace('::', '__')
    name = re.sub(r'_+', '_', name).strip('_')
    return name[:180]


def wikilink(node_id: str) -> str:
    """Create safe wikilink"""
    safe = sanitize_filename(node_id)
    return f"[[{safe}]]"


def generate_obsidian_markdown(mapping_path: str, vault_dir: str = None):
    mapping_path = Path(mapping_path)
    data = json.loads(mapping_path.read_text(encoding="utf-8"))

    metadata = data.get("metadata", {})
    project = metadata.get("project", Path(mapping_path).stem.replace("_mapping_v10", ""))

    if vault_dir is None:
        vault_dir = Path(f"obsidian_vault_{project}")
    else:
        vault_dir = Path(vault_dir)

    # Fresh vault
    if vault_dir.exists():
        shutil.rmtree(vault_dir)
    vault_dir.mkdir(parents=True, exist_ok=True)
    (vault_dir / ".obsidian").mkdir(exist_ok=True)

    nodes = {n["id"]: n for n in data["nodes"]}
    edges = data["edges"]

    outgoing = defaultdict(list)
    for e in edges:
        outgoing[e["source"]].append(e)

    # ==================== INDEX.md ====================
    index = [
        f"# {project} Architecture",
        "",
        f"Generated on {metadata.get('scan_date', 'N/A')}",
        f"Nodes: {metadata.get('total_nodes', 0)} | Edges: {metadata.get('total_edges', 0)}",
        ""
    ]

    index.append("## 🔥 Top God Nodes")
    for item in metadata.get("god_nodes", {}).get("internal", [])[:15]:
        index.append(f"- {wikilink(item['node'])} ({item['degree']} connections)")

    index.append("\n## Services")
    services = {nid.split('/')[0] for nid in nodes if '/' in nid}
    for s in sorted(services):
        index.append(f"- [[{s}]]")

    (vault_dir / "INDEX.md").write_text("\n".join(index), encoding="utf-8")

    # ==================== Per-Node Pages ====================
    for nid, node in nodes.items():
        if node.get("external", False):
            continue

        lines = [f"# {nid}", ""]
        lines.append(f"**Type:** {node['type']}")
        if node.get("community", -1) >= 0:
            lines.append(f"**Community:** {node['community']}")

        # Outgoing connections
        out_edges = outgoing.get(nid, [])
        if out_edges:
            by_type = defaultdict(list)
            for e in out_edges:
                by_type[e["type"]].append(e["target"])
            lines.append("\n## Outgoing Connections")
            for etype, targets in sorted(by_type.items()):
                lines.append(f"\n### {etype.capitalize()}")
                for t in sorted(set(targets)):
                    lines.append(f"- {wikilink(t)}")

        safe_name = sanitize_filename(nid)
        (vault_dir / f"{safe_name}.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"✅ Obsidian vault generated: {vault_dir}")
    print(f"   Project: {project} | Nodes: {len(nodes)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_obsidian.py <mapping.json> [vault_dir]")
        sys.exit(1)
    mapping = sys.argv[1]
    vault = sys.argv[2] if len(sys.argv) > 2 else None
    generate_obsidian_markdown(mapping, vault)