import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from activities.agent_activity import run_agent_activity
from agents.hello_agent import HelloAgentWorkflow
from core.config import load_settings


async def main() -> None:
    settings = load_settings()
    client = await Client.connect(settings.temporal_address, namespace=settings.temporal_namespace)
    worker = Worker(
        client,
        task_queue=settings.task_queue,
        activities=[run_agent_activity],
        workflows=[HelloAgentWorkflow],
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
