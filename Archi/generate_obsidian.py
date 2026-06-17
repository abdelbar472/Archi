"""Obsidian Markdown Generator — creates rich, well-connected knowledge base."""
import json
import sys
import shutil
from pathlib import Path
from collections import defaultdict
import re


def sanitize_filename(name: str) -> str:
    """Safe filename for Windows + Obsidian — aggressive cleaning."""
    name = str(name)
    name = re.sub(r'[\\/:*?"<>|]', '_', name)
    name = name.replace('::', '__')
    name = name.replace('(', '_').replace(')', '_')
    name = name.replace('\n', '_').replace('\r', '_')
    name = re.sub(r'_+', '_', name).strip('_')
    if len(name) > 140:
        name = name[:140]
    return name


def wikilink(node_id: str) -> str:
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

    if vault_dir.exists():
        shutil.rmtree(vault_dir)
    vault_dir.mkdir(parents=True, exist_ok=True)
    (vault_dir / ".obsidian").mkdir(exist_ok=True)

    nodes = {n["id"]: n for n in data["nodes"]}
    edges = data["edges"]

    outgoing = defaultdict(list)
    incoming = defaultdict(list)
    for e in edges:
        outgoing[e["source"]].append(e)
        incoming[e["target"]].append(e)

    # ==================== INDEX.md ====================
    index = [
        f"# {project} Architecture",
        "",
        f"Generated on {metadata.get('scan_date', 'N/A')}",
        f"Nodes: {metadata.get('total_nodes', 0)} | Edges: {metadata.get('total_edges', 0)}",
        ""
    ]

    index.append("## 🔥 Top God Nodes")
    for item in metadata.get("god_nodes", {}).get("internal", [])[:20]:
        index.append(f"- {wikilink(item['node'])} ({item['degree']} connections)")

    index.append("\n## Key Folders / Aliases")
    folders = {nid.split('/')[0] for nid in nodes if '/' in nid and not nid.startswith('.')}
    for s in sorted(list(folders)[:30]):
        index.append(f"- [[{s}]]")

    (vault_dir / "INDEX.md").write_text("\n".join(index), encoding="utf-8")

    # ==================== Per-Node Pages ====================
    # Create pages for files + important symbols
    for nid, node in nodes.items():
        if node.get("external", False):
            continue

        # Skip very noisy low-level symbols to reduce orphans
        if '::' in nid and len(nid.split('::')[1]) < 3:
            continue

        lines = [f"# {nid}", ""]
        lines.append(f"**Type:** {node.get('type', 'unknown')}")
        if node.get("community", -1) >= 0:
            lines.append(f"**Community:** {node['community']}")

        out_edges = outgoing.get(nid, [])
        if out_edges:
            by_type = defaultdict(list)
            for e in out_edges:
                by_type[e["type"]].append(e["target"])
            lines.append("\n## Outgoing Connections")
            for etype, targets in sorted(by_type.items()):
                lines.append(f"\n### {etype.capitalize()}")
                for t in sorted(set(targets))[:30]:   # limit to avoid huge pages
                    lines.append(f"- {wikilink(t)}")

        # Add incoming connections section
        inc_edges = incoming.get(nid, [])
        internal_inc = [e for e in inc_edges if not nodes.get(e["source"], {}).get("external")]
        if internal_inc:
            by_type_in = defaultdict(list)
            for e in internal_inc:
                by_type_in[e["type"]].append(e["source"])
            lines.append("\n## Incoming Connections")
            for etype, sources in sorted(by_type_in.items()):
                lines.append(f"\n### {etype.capitalize()}")
                for s in sorted(set(sources))[:30]:
                    lines.append(f"- {wikilink(s)}")

        safe_name = sanitize_filename(nid)
        try:
            (vault_dir / f"{safe_name}.md").write_text("\n".join(lines), encoding="utf-8")
        except Exception as e:
            print(f"   ⚠️ Could not write {safe_name}: {e}")
    print(f"   Project: {project} | Nodes: {len(nodes)}")
    print(f"   Orphans fixed: nodes now have both outgoing + incoming wikilinks")
    print(f"   Pages created: {sum(1 for n in nodes.values() if not n.get('external', False))}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_obsidian.py <mapping.json> [vault_dir]")
        sys.exit(1)
    generate_obsidian_markdown(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)