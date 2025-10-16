Local AI on Mac Pro 5,1 — with a Retro Macintosh SE/30 Frontend

English (Deutsch below: see README.de.md)

Overview
- Goal: Run a fully local, offline-first AI system on a Mac Pro 5,1 (2009), and use a Macintosh SE/30 as a charming retro front-end.
- Why: Keep full control of your data, avoid cloud dependencies, and showcase that modern AI can run locally on retro-capable hardware.
- How: A containerized stack (Docker/Compose) with FastAPI + LangGraph for agent orchestration, optional Open WebUI, and an evolving RAG pipeline and toolchain.

Highlights
- Fully local: No cloud keys or external services required for core functionality.
- Agent-first: LangGraph to orchestrate tools and steps.
- RAG prototype: Retrieval-Augmented Generation pipeline under active development.
- Tooling: Helper script ./a to simplify common dev and ops workflows.

Architecture & Stack
- OS baseline: Minimal NixOS host (or any Linux/macOS host capable of Docker) running containers.
- Core services:
  - FastAPI backend (agent-server)
  - LangGraph for agent orchestration
  - Optional Open WebUI for chat
  - Datastores (Postgres + pgvector, ClickHouse, MinIO), Redis, SearXNG (optional web search)
- Agents and Tools:
  - RAG agent prototypes
  - Internet Archive toolchain (early stage)
  - SQL agent (work-in-progress)

Hardware Context
- Macintosh SE/30: acts as the visible retro interface; network bridging in progress (wireless Ethernet planned). Disk and OS setup still pending.
- Mac Pro 5,1 (2009): the AI workhorse; upgraded GPU (flashed Radeon RX 6800) for modern compatibility.

Repository Layout (top-level)
- a — project helper script (see Commands below)
- compose.yml, compose.override.yml — docker compose setup
- src/agent-server — FastAPI backend, agents, graphs, tools, prompts
- libs/open-webui — vendored Open WebUI (optional)
- docker/*, config/* — container build and service configuration
- data/, test/ — data and tests

Prerequisites
- Docker and Docker Compose v2
- macOS users: GNU sed (gsed) for some helper toggles
  - Install via Homebrew: brew install gnu-sed
- Optional: jq, yq (some helper paths will run yq via docker if not installed)

Quick Start
1) Initialize local config files
   - ./a i
   - Creates .env and compose.override.yml if missing.
2) Start services
   - ./a s            # starts all services defined in compose
3) Open the UI (optional)
   - ./a o            # opens http://localhost:8080 in your default browser (macOS)
4) Check logs
   - ./a l            # all logs
   - ./a lf as        # follow logs of the agent-server service

Common Helper Commands (./a)
- ./a i                      Initialize local env files
- ./a s [SERVICE]            Start a specific service or all
- ./a d [SERVICE]            Stop a specific service or all
- ./a b SERVICE              Build a service
- ./a bma SERVICE            Build multi-arch (base images only; see labels)
- ./a e SERVICE CMD...       Exec into a running container and run a command
- ./a l [SERVICE]            Show logs (also tries init-* logs)
- ./a lf [SERVICE]           Follow logs
- ./a m [alembic args]       Run alembic in agent-server (defaults to upgrade head)
- ./a w [options] [SERVICE]  Compose watch for live rebuilds
- ./a td                     Toggle debug mode switch in .env
- ./a ti                     Toggle init containers in compose.override.yml
- ./a dpsw                   Watch docker compose service states
- ./a rc                     Restart all containers (down + up -d)
- ./a rd                     Reset services labeled resetableDb
- ./a o                      Open default UI URL

Notes
- On the first run, images will be built/pulled which can take time.
- The project aims to run fully offline once images and models are in place. Some optional tools (e.g., web search) need connectivity.

Development Notes
- FastAPI routers live in src/agent-server/routers
- Agents, prompts, tools, and graphs are under src/agent-server/ai
- Use alembic via ./a m for database migrations inside the agent-server container.
- Debug toggle: ./a td flips a switch in .env used by the dev stack.

Roadmap
- Finalize SE/30 network bridge and OS setup, enabling the retro front-end
- Harden RAG pipeline, add local knowledge base integration (vector DB)
- Expand toolchain for instruction extraction without pre-indexing
- Provide easy model management for fully offline operation

Contributing
This is an open, collaborative, and retro-friendly project. PRs are welcome! If the Star Trek “Hello, Computer” vision resonates with you, please join in.

License
TBD. Until a license is added, assume all rights reserved by the author(s).

Contact
If you’d like to collaborate or test on similar hardware, please open an issue or PR.
