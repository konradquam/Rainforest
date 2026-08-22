# Code Map

A file-by-file map of the codebase. Start here to find where something lives.

## `pyproject.toml`

Declares dependencies (`temporalio`, `anthropic`, `python-dotenv`) and maps `src/` so `core`, `agents`, `activities`, `tools` install as top-level packages via `pip install -e .`.

## `.env` / `.env.example`

Local configuration: `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `TEMPORAL_ADDRESS`, `TEMPORAL_NAMESPACE`, `TEMPORAL_TASK_QUEUE`. Read by `core/config.py`.

## `src/core/` — shared platform code

| File | Purpose |
|---|---|
| `config.py` | `Settings` dataclass + `load_settings()`, which reads `.env` (via `python-dotenv`) and caches the result. Raises if `ANTHROPIC_API_KEY` is unset. |
| `models.py` | Shared domain dataclasses: `Task` (id, description, metadata) and `AgentResult` (output, stop_reason). Passed as Temporal activity/workflow inputs and outputs, so kept plain and JSON-serializable. |
| `activity_names.py` | String constants for activity names (e.g. `RUN_AGENT_ACTIVITY`). Imported by both the activity's `@activity.defn(name=...)` and by workflow files that call `workflow.execute_activity(...)` — keeps the two in sync without hardcoding the string twice. Deliberately dependency-free so workflow files can import it without pulling `anthropic`/`dotenv` into Temporal's workflow sandbox. |
| `agent_registry.py` | `AGENT_WORKFLOWS` — the single map from an agent's short name (e.g. `"hello_agent"`) to its workflow class. Both `worker.py` (which workflows to register) and `scripts/run_workflow.py` (which one to start, and validating the CLI's `agent` argument) read from this one place. Add a new agent here once, and both pick it up. |
| `worker.py` | The worker entrypoint. Connects to the Temporal server and runs a `Worker` registered with every activity and every workflow in `AGENT_WORKFLOWS`. Restart this process after any change to activity/workflow code. |

## `src/activities/` — Temporal activities shared across agents

| File | Purpose |
|---|---|
| `agent_activity.py` | `run_agent_activity(prompt, task)` — the core LLM-calling activity. Builds a cached `AsyncAnthropic` client, sends the prompt with the task folded into the system prompt, and returns an `AgentResult`. Registered under the name `RUN_AGENT_ACTIVITY` from `core/activity_names.py`. |

## `src/agents/` — one directory per agent

Each agent is its own package: a workflow, an `__init__.py` re-exporting it (and eventually holding that agent's own setup — MCP connections, tool wiring, etc.), and its own `README.md`.

| Agent | Purpose |
|---|---|
| `hello_agent/` | The first agent — a minimal wiring check (`HelloAgentWorkflow`) that calls `run_agent_activity`. See its own `README.md` for details. |

## `src/tools/`

Empty so far — reserved for agent tools (Temporal-activity-wrapped or plain) shared across more than one agent.

## `scripts/` — local dev CLI entry points

| File | Purpose |
|---|---|
| `run_workflow.py` | Starts a registered agent's workflow against the running Temporal server/worker, from the terminal: `run_workflow.py <agent> <prompt>` plus optional `--task-id`/`--task-description`. The agent name is looked up in `core/agent_registry.py`. |
| `smoke_test_activity.py` | Runs `run_agent_activity` directly through Temporal's `ActivityEnvironment` test harness — exercises the Anthropic wiring with no Temporal server involved at all. |

## How a request flows

```
scripts/run_workflow.py <agent> <prompt>
  -> looks up <agent> in core/agent_registry.AGENT_WORKFLOWS
  -> Client.execute_workflow(<agent's workflow>.run, ...)   [connects to Temporal server]
  -> Temporal server schedules the workflow task on the task queue
  -> core/worker.py's Worker picks it up
  -> HelloAgentWorkflow.run(prompt, task)
       -> workflow.execute_activity(RUN_AGENT_ACTIVITY, ...)
       -> activities/agent_activity.py: run_agent_activity(prompt, task)
            -> Anthropic Messages API
       -> AgentResult returned back up through the workflow to the client
```
