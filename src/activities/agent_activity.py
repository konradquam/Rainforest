from functools import lru_cache

from anthropic import AsyncAnthropic
from temporalio import activity

from core.activity_names import RUN_AGENT_ACTIVITY
from core.config import load_settings
from core.models import AgentResult, Task
from knowledge_grove.mcp_server import mcp_server


@lru_cache(maxsize=1)
def _get_client() -> AsyncAnthropic:
    return AsyncAnthropic(api_key=load_settings().anthropic_api_key)


@activity.defn(name=RUN_AGENT_ACTIVITY)
async def run_agent_activity(prompt: str, task: Task) -> AgentResult:
    settings = load_settings()
    client = _get_client()

    messages=[{"role": "user", "content": prompt}]
    tools = [t.model_dump(include={"name", "description", "input_schema"}) for t in await mcp_server.list_tools()]
    if tools:
        tools[-1]["cache_control"] = {"type": "ephemeral"}
    while True:
        response = await client.messages.create(
            model=settings.anthropic_model,
            max_tokens=4096,
            system=f"You are working on task '{task.id}': {task.description}",
            messages=messages,
            tools= tools
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != 'tool_use':
            break

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            result = await mcp_server.call_tool(block.name, block.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": [{"type": "text", "text": item.text} for item in result.content],
                "is_error": result.is_error,
            })
        messages.append({"role": "user", "content": tool_results})


    text = "".join(block.text for block in response.content if block.type == "text")
    return AgentResult(output=text, stop_reason=response.stop_reason)
