# Archi — Code Architecture Mapper

**Local, fast, offline codebase architecture tool.**

No LLM. No cloud. Runs instantly on your machine.

## Features

- Scans Python, TypeScript, gRPC, and more
- Builds rich graph (files, classes, methods, calls, database tables)
- Detects services, routers, God Nodes, and communities
- Generates clean **Obsidian** knowledge base automatically
- Semantic search support

## Quick Start

```bash
# Install
cd /d/codes/Archi
pip install -e .

# Scan a project + generate Obsidian vault
archi /path/to/your/project

# With search
archi /path/to/your/project --search "user authentication"