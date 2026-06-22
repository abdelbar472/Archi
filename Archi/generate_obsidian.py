"""Obsidian Generator — Classic (full) + Smart (Context-Rich & Rewired)"""
import json
import sys
import shutil
import time
from pathlib import Path
from collections import defaultdict
import re
import hashlib


def sanitize_filename(name: str) -> str:
    name = str(name).replace('\\', '/')
    cleaned = re.sub(r'[\\/:*?"<>|]', '_', name)
    cleaned = cleaned.replace('::', '__')
    cleaned = cleaned.replace('(', '_').replace(')', '_')
    cleaned = re.sub(r'[\n\r\t]', '_', cleaned)
    cleaned = re.sub(r'_+', '_', cleaned).strip('_')
    if len(cleaned) > 140:
        digest = hashlib.sha1(name.encode("utf-8")).hexdigest()[:10]
        cleaned = f"{cleaned[:120]}__{digest}"
    return cleaned or "unnamed_node"


def wikilink(node_id: str) -> str:
    return f"[[{sanitize_filename(node_id)}]]"


def safe_rmtree(path: Path):
    if path.exists():
        for _ in range(5):
            try:
                shutil.rmtree(path, ignore_errors=False)
                return
            except PermissionError:
                time.sleep(0.5)
        print(f" ⚠️ Could not fully remove {path}")


def generate_obsidian_markdown(mapping_path: str, vault_dir: str = None, mode: str = "classic"):
    mapping_path = Path(mapping_path)
    data = json.loads(mapping_path.read_text(encoding="utf-8"))

    metadata = data.get("metadata", {})
    project = metadata.get("project", mapping_path.stem.replace("_mapping_v10", "")
                          .replace("_mapping_classic", "").replace("_mapping_smart", ""))

    if vault_dir is None:
        vault_dir = Path(f"output/{project}/obsidian_vault_{mode}")
    else:
        vault_dir = Path(vault_dir)

    print(f"📖 Generating Obsidian vault — Mode: {mode.upper()}")

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

    # Group by community for "Related" section
    communities_map = defaultdict(list)
    for nid, node in nodes.items():
        comm = node.get("community", -1)
        if comm != -1:
            communities_map[comm].append(nid)

    # INDEX
    index = [f"# {project} Architecture ({mode.title()} Mode)", ""]
    index.append(f"Nodes: {len(nodes):,} | Generated: {metadata.get('scan_date', 'N/A')}")

    index.append("\n## 🔥 Top God Nodes")
    for item in metadata.get("god_nodes", {}).get("internal", [])[:30]:
        index.append(f"- {wikilink(item['node'])} ({item['degree']} connections)")

    (vault_dir / "INDEX.md").write_text("\n".join(index), encoding="utf-8")

    created = 0

    for nid, node in nodes.items():
        if node.get("external", False):
            continue

        node_type = node.get("type", "unknown")
        
        # In Smart mode, we 100% trust graph.py's rewired JSON. No double-filtering.
        if mode == "classic":
            if '::' in nid:
                symbol = nid.split('::', 1)[1]
                if len(symbol) < 2 or symbol.startswith('_'):
                    continue

        # Build page
        lines = [f"# {nid}", ""]
        
        # Tags for Obsidian graph visualization
        lines.append(f"type:: {node_type.replace(' ', '_')}")
        if node.get("community") is not None and node.get("community") != -1:
            lines.append(f"community:: {node['community']}")
        lines.append("")

        out_edges = outgoing.get(nid, [])
        if out_edges:
            by_type = defaultdict(list)
            for e in out_edges:
                by_type[e.get("type", "related")].append(e.get("target"))
            lines.append("## → Outgoing")
            for etype, targets in sorted(by_type.items()):
                lines.append(f"**{etype.capitalize()}:**")
                for t in sorted(set(targets))[:25]:
                    lines.append(f"- {wikilink(t)}")
            lines.append("")

        inc_edges = [e for e in incoming.get(nid, []) if not nodes.get(e.get("source"), {}).get("external")]
        if inc_edges:
            by_type_in = defaultdict(list)
            for e in inc_edges:
                by_type_in[e.get("type", "related")].append(e.get("source"))
            lines.append("## ← Incoming")
            for etype, sources in sorted(by_type_in.items()):
                lines.append(f"**{etype.capitalize()}:**")
                for s in sorted(set(sources))[:25]:
                    lines.append(f"- {wikilink(s)}")
            lines.append("")

        # 🧠 SMART FEATURE: Show peers in the same community module
        comm = node.get("community", -1)
        if comm != -1 and mode == "smart":
            peers = [p for p in communities_map.get(comm, []) if p != nid and not nodes.get(p, {}).get("external")]
            if peers:
                lines.append("## 🏘️ Same Module (Community)")
                for p in sorted(peers)[:15]:
                    lines.append(f"- {wikilink(p)}")
                lines.append("")

        safe_name = sanitize_filename(nid)
        try:
            (vault_dir / f"{safe_name}.md").write_text("\n".join(lines), encoding="utf-8")
            created += 1
        except:
            pass

    print(f"✅ Done! Mode: {mode.upper()} → {created:,} pages created")
    print(f"   Vault: {vault_dir}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_obsidian.py <mapping.json> [vault_dir] [mode]")
        sys.exit(1)
    
    mode = sys.argv[3] if len(sys.argv) > 3 else "classic"
    generate_obsidian_markdown(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None, mode)