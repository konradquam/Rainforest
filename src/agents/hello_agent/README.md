# Hello Agent

The first agent in the project — a minimal wiring check for the Temporal + Anthropic setup, meant as a template for later agents rather than a real one.

## What it does

`HelloAgentWorkflow.run(prompt, task)` takes a prompt string and a `Task` (`core/models.py`), and executes the shared `run_agent_activity` activity to get a response from Claude — the task's `id`/`description` are folded into the system prompt. Returns an `AgentResult(output, stop_reason)`.

## Files

- `workflow.py` — the `HelloAgentWorkflow` definition
- `__init__.py` — re-exports `HelloAgentWorkflow`; this is also where this agent's own setup (MCP connections, tool wiring, etc.) will live once it needs any

## Running it

Requires the Temporal dev server and the worker to be running (see the top-level README). Then, from the project root:

```bash
source .venv/bin/activate
PYTHONPATH=src python scripts/run_workflow.py hello_agent "Say hello in one short sentence."
```

Optional flags: `--task-id <id>`, `--task-description "..."`.
