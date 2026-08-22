# Rainforest

A personal agentic ecosystem built on [Temporal](https://temporal.io) workflows, with agents calling Claude through the Anthropic API.

## Requirements

- Python 3.11 (the `temporalio` SDK can lag behind newer Python releases, so the venv is pinned to 3.11)
- [Temporal CLI](https://docs.temporal.io/cli) for the local dev server (`temporal server start-dev`)
- An Anthropic API key from [console.anthropic.com](https://console.anthropic.com) — a claude.ai subscription alone does not provide one

## Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env   # then fill in ANTHROPIC_API_KEY
```

`pip install -e .` installs `core`, `agents`, `activities`, and `tools` as top-level importable packages (see `pyproject.toml`).

## Running locally

Three terminals:

1. **Temporal dev server**
   ```bash
   temporal server start-dev
   ```
   Web UI at `localhost:8233`, gRPC frontend at `localhost:7233`.

2. **Worker** — polls the task queue and hosts every registered activity/workflow
   ```bash
   source .venv/bin/activate
   PYTHONPATH=src python src/core/worker.py
   ```
   Restart this any time you change activity/workflow code or `worker.py`'s registration list — there's no hot reload.

3. **Start a workflow run** — pass which agent to run, then the prompt
   ```bash
   source .venv/bin/activate
   PYTHONPATH=src python scripts/run_workflow.py hello_agent "Say hello in one short sentence."
   ```
   The agent name must be one registered in `core/agent_registry.py`; passing anything else lists the valid options.

To sanity-check the Anthropic wiring in isolation, with no Temporal server involved at all:
```bash
PYTHONPATH=src python scripts/smoke_test_activity.py
```

## Project layout

```
src/
  core/         shared platform code — settings, domain models, activity-name constants, the worker entrypoint
  agents/       one directory per agent — each owns its workflow(s) and eventually its own setup (MCP, tool wiring, etc.)
  activities/   Temporal activities shared across agents (e.g. the LLM call)
  tools/        agent tools shared across more than one agent
scripts/        small CLI entry points for local dev
docs/           architecture notes and a file-by-file code map
```

See [`docs/code-map.md`](docs/code-map.md) for the full map, and [`src/agents/hello_agent/README.md`](src/agents/hello_agent/README.md) for the first agent.

## Configuration

Set in `.env` (see `.env.example` for defaults):

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | required — Anthropic API key |
| `ANTHROPIC_MODEL` | model id used by `run_agent_activity` |
| `TEMPORAL_ADDRESS` | Temporal server gRPC address |
| `TEMPORAL_NAMESPACE` | Temporal namespace |
| `TEMPORAL_TASK_QUEUE` | task queue the worker polls and clients submit to |
