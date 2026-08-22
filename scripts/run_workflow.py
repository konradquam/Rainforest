import argparse
import asyncio
import uuid

from temporalio.client import Client

from agents.hello_agent import HelloAgentWorkflow
from core.config import load_settings
from core.models import Task


async def main() -> None:
    parser = argparse.ArgumentParser(description="Start a HelloAgentWorkflow run")
    parser.add_argument("prompt", help="Prompt to send the agent")
    parser.add_argument("--task-id", default=str(uuid.uuid4()))
    parser.add_argument("--task-description", default="Ad-hoc task started from the terminal")
    args = parser.parse_args()

    settings = load_settings()
    client = await Client.connect(settings.temporal_address, namespace=settings.temporal_namespace)

    task = Task(id=args.task_id, description=args.task_description)
    result = await client.execute_workflow(
        HelloAgentWorkflow.run,
        args=[args.prompt, task],
        id=f"hello-agent-{task.id}",
        task_queue=settings.task_queue,
    )

    print("output:", result.output)
    print("stop_reason:", result.stop_reason)


if __name__ == "__main__":
    asyncio.run(main())
