import asyncio

from temporalio.testing import ActivityEnvironment

from activities.agent_activity import run_agent_activity
from core.models import Task


async def main() -> None:
    env = ActivityEnvironment()
    task = Task(id="smoke-test", description="Say hello in one short sentence.")
    result = await env.run(run_agent_activity, "Hello, who are you?", task)
    print("output:", result.output)
    print("stop_reason:", result.stop_reason)


if __name__ == "__main__":
    asyncio.run(main())
