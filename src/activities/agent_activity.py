from functools import lru_cache

from anthropic import AsyncAnthropic
from temporalio import activity

from core.activity_names import RUN_AGENT_ACTIVITY
from core.config import load_settings
from core.models import AgentResult, Task


@lru_cache(maxsize=1)
def _get_client() -> AsyncAnthropic:
    return AsyncAnthropic(api_key=load_settings().anthropic_api_key)


@activity.defn(name=RUN_AGENT_ACTIVITY)
async def run_agent_activity(prompt: str, task: Task) -> AgentResult:
    settings = load_settings()
    client = _get_client()

    response = await client.messages.create(
        model=settings.anthropic_model,
        max_tokens=4096,
        system=f"You are working on task '{task.id}': {task.description}",
        messages=[{"role": "user", "content": prompt}],
    )

    text = "".join(block.text for block in response.content if block.type == "text")
    return AgentResult(output=text, stop_reason=response.stop_reason)
