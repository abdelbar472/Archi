"""Archi — Code Architecture Tool"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from scanner import TemporyScanner
from generate_obsidian import generate_obsidian_markdown


def main():
    parser = argparse.ArgumentParser(description="Archi — Code Architecture Tool")
    parser.add_argument("project_path", help="Path to the project directory")
    parser.add_argument("--focus", type=str, default=None, help="Focus scan on a subdirectory")
    parser.add_argument("--output", type=str, default="output", help="Base output directory")
    parser.add_argument("--top-gods", type=int, default=12, help="Number of top god nodes")
    parser.add_argument("--search", type=str, default=None, help="Run semantic search after scan")
    parser.add_argument("--no-obsidian", action="store_true", help="Skip Obsidian vault generation")
    
    args = parser.parse_args()

    project_name = Path(args.project_path).name

    # Scan the project
    scanner = TemporyScanner(args.project_path)
    scanner.scan(args.focus)

    # Generate graph data
    graph_dict = scanner.graph.to_dict(top_gods=args.top_gods)

    # === Clean Project-Specific Output Structure ===
    base_output = Path(args.output)
    project_dir = base_output / project_name          # e.g., output/ui/
    project_dir.mkdir(parents=True, exist_ok=True)

    # JSON mapping file
    json_path = project_dir / f"{project_name}_mapping_v10.json"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(graph_dict, f, indent=2, ensure_ascii=False)

    print(f"\n🎉 Mapping complete → {json_path}")
    print(f"   Nodes: {graph_dict['metadata']['total_nodes']} | Edges: {graph_dict['metadata']['total_edges']}")

    # Summary
    print("\n🔥 Top Internal God Nodes:")
    for item in graph_dict['metadata']['god_nodes']['internal']:
        print(f"   • {item['node']} ({item['degree']} connections)")

    print("\n🌐 Top External God Nodes:")
    for item in graph_dict['metadata']['god_nodes']['external']:
        print(f"   • {item['node']} ({item['degree']} connections) [EXT]")

    # Semantic Search (optional)
    if args.search:
        print(f"\n🔍 Semantic Search: '{args.search}'")
        results = scanner.graph.search(args.search, limit=15)
        for node_id, score in results:
            node_type = scanner.graph.node_types.get(node_id, "unknown")
            print(f"   {score:2d} → {node_id} ({node_type})")

    # Obsidian Vault (inside project folder)
    if not args.no_obsidian:
        print("\n📖 Generating Obsidian Knowledge Base...")
        vault_dir = project_dir / "obsidian_vault"
        generate_obsidian_markdown(str(json_path), str(vault_dir))
        print(f"   Vault ready → {vault_dir}")

    print(f"\n✅ All done! Check: {project_dir}")


if __name__ == "__main__":
    main()