"""Archi — Code Architecture Tool (Dual Mode: Classic + Smart)."""
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
    parser.add_argument("--no-obsidian", action="store_true", help="Skip Obsidian vault generation")
    parser.add_argument("--top-gods", type=int, default=15, help="Number of top god nodes")

    args = parser.parse_args()

    project_name = Path(args.project_path).name
    output_base = Path("output") / project_name
    output_base.mkdir(parents=True, exist_ok=True)

    print("🚀 Starting Archi Dual-Mode Scan...\n")

    # Scan once
    scanner = TemporyScanner(args.project_path)
    scanner.scan(args.focus)

    graph = scanner.graph

    # === Generate TWO JSON versions — now genuinely different ===
    def save_json(mode: str):
        data = graph.to_dict(top_gods=args.top_gods, mode=mode)
        path = output_base / f"{project_name}_mapping_{mode}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ {mode.title()} JSON saved → {path}  "
              f"({data['metadata']['total_nodes']:,} nodes, {data['metadata']['total_edges']:,} edges)")
        return path

    classic_json = save_json("classic")
    smart_json = save_json("smart")

    # Summary
    print(f"\n🔥 Top Internal God Nodes:")
    for item in graph.get_god_nodes(15)["internal"]:
        print(f"   • {item[0]} ({item[1]} connections)")

    if not args.no_obsidian:
        print("\n📖 Generating Obsidian Vaults...")

        print("   → Classic Vault (Detailed)")
        generate_obsidian_markdown(str(classic_json), str(output_base / "obsidian_vault_classic"), mode="classic")

        print("   → Smart Vault (Focused)")
        generate_obsidian_markdown(str(smart_json), str(output_base / "obsidian_vault_smart"), mode="smart")

    print(f"\n🎉 All done! Check folder: {output_base}")


if __name__ == "__main__":
    main()