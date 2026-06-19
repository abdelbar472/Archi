"""Obsidian Markdown Generator — Fixed for large projects like js_9"""
import json
import sys
import shutil
import time
from pathlib import Path
from collections import defaultdict
import re


import hashlib

def sanitize_filename(name: str) -> str:
    """Ultra-safe filename for Windows. Collision-proof for long monorepo paths."""
    name = str(name)
    cleaned = re.sub(r'[\\/:*?"<>|]', '_', name)
    cleaned = cleaned.replace('::', '__')
    cleaned = cleaned.replace('(', '_').replace(')', '_')
    cleaned = re.sub(r'[\n\r\t]', '_', cleaned)
    cleaned = re.sub(r'_+', '_', cleaned).strip('_')

    if len(cleaned) > 140:
        # Keep a short hash of the FULL original id so distinct long paths
        # never collapse onto the same filename after truncation.
        digest = hashlib.sha1(name.encode("utf-8")).hexdigest()[:10]
        cleaned = f"{cleaned[:120]}__{digest}"

    return cleaned or "unnamed_node"


def wikilink(node_id: str) -> str:
    return f"[[{sanitize_filename(node_id)}]]"


def safe_rmtree(path: Path):
    """Robust cleanup for Windows."""
    if path.exists():
        try:
            shutil.rmtree(path, ignore_errors=True)
            time.sleep(0.8)
        except Exception as e:
            print(f"   ⚠️ Cleanup warning: {e}")


def generate_obsidian_markdown(mapping_path: str, vault_dir: str = None):
    mapping_path = Path(mapping_path)
    data = json.loads(mapping_path.read_text(encoding="utf-8"))

    metadata = data.get("metadata", {})
    project = metadata.get("project", mapping_path.stem.replace("_mapping_v10", ""))

    if vault_dir is None:
        vault_dir = Path(f"output/{project}/obsidian_vault")
    else:
        vault_dir = Path(vault_dir)

    print(f"   Generating Obsidian vault for {project}...")

    safe_rmtree(vault_dir)
    vault_dir.mkdir(parents=True, exist_ok=True)
    (vault_dir / ".obsidian").mkdir(exist_ok=True)

    nodes = {n["id"]: n for n in data.get("nodes", [])}
    edges = data.get("edges", [])

    outgoing = defaultdict(list)
    incoming = defaultdict(list)
    for e in edges:
        outgoing[e.get("source")].append(e)
        incoming[e.get("target")].append(e)

    # INDEX.md
    index = [
        f"# {project} Architecture",
        f"Generated: {metadata.get('scan_date', 'N/A')}",
        f"Nodes: {len(nodes):,} | Edges: {len(edges):,}",
        ""
    ]

    index.append("## 🔥 Top Internal God Nodes")
    for item in metadata.get("god_nodes", {}).get("internal", [])[:20]:
        index.append(f"- {wikilink(item['node'])} ({item['degree']} connections)")

    (vault_dir / "INDEX.md").write_text("\n".join(index), encoding="utf-8")

    # Create pages — less aggressive filtering for js_9
    created = 0
    for nid, node in nodes.items():
        if node.get("external", False):
            continue

        # Only skip extremely noisy tiny symbols
        if '::' in nid:
            symbol = nid.split('::', 1)[1]
            if len(symbol) < 2 or symbol.startswith('_'):
                continue

        lines = [f"# {nid}", ""]
        lines.append(f"**Type:** {node.get('type', 'unknown')}")

        if node.get("community") is not None:
            lines.append(f"**Community:** {node['community']}")

        # Outgoing connections
        out_edges = outgoing.get(nid, [])
        if out_edges:
            by_type = defaultdict(list)
            for e in out_edges:
                by_type[e.get("type", "related")].append(e.get("target"))
            lines.append("\n## → Outgoing")
            for etype, targets in sorted(by_type.items()):
                lines.append(f"\n### {etype.capitalize()}")
                for t in sorted(set(targets))[:35]:
                    lines.append(f"- {wikilink(t)}")

        # Incoming (internal only)
        inc_edges = [e for e in incoming.get(nid, []) if not nodes.get(e.get("source"), {}).get("external")]
        if inc_edges:
            by_type_in = defaultdict(list)
            for e in inc_edges:
                by_type_in[e.get("type", "related")].append(e.get("source"))
            lines.append("\n## ← Incoming")
            for etype, sources in sorted(by_type_in.items()):
                lines.append(f"\n### {etype.capitalize()}")
                for s in sorted(set(sources))[:35]:
                    lines.append(f"- {wikilink(s)}")

        safe_name = sanitize_filename(nid)
        try:
            (vault_dir / f"{safe_name}.md").write_text("\n".join(lines), encoding="utf-8")
            created += 1
        except Exception as e:
            print(f"   ⚠️ Write failed for {safe_name}: {e}")

    print(f"✅ Obsidian vault generated → {vault_dir}")
    print(f"   Pages created: {created:,}")
    print(f"   Open this folder in Obsidian to view the knowledge base.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_obsidian.py <mapping.json> [vault_dir]")
        sys.exit(1)
    generate_obsidian_markdown(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)