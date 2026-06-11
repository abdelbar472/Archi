# Archi — Code Architecture Mapper

**Local, fast, offline codebase visualization & architecture intelligence tool.**

No LLM dependency. No cloud. Runs instantly on your machine.

![Archi Screenshot](https://github.com/abdelbar472/Archi/raw/main/docs/screenshot.png)

## Features

- **Multi-language support**: Python (AST), JavaScript/TypeScript, Go, Proto, and more
- **Rich architecture graph**: files, classes, methods, calls, imports, inheritance, database tables
- **Framework awareness**: Deep detection for FastAPI, Django, React, gRPC, etc.
- **God Nodes & Communities**: Automatically highlights critical parts of your codebase
- **Beautiful Obsidian export**: Generates a full knowledge base with rich connections
- **Semantic search**: Find components by natural language

## Quick Start

```bash
# 1. Clone & install
git clone https://github.com/abdelbar472/Archi.git
cd Archi
pip install -e .

# 2. Scan any project
archi /path/to/your/project

# 3. With semantic search
archi /path/to/your/project --search "user authentication"