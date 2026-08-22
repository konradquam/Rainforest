import argparse
import asyncio
import json
import uuid

from temporalio.client import Client

from core.config import load_settings


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Start any registered workflow by name",
        epilog='Example: run_workflow.py HelloAgentWorkflow '
        '--arg \'"Say hello in one short sentence."\' '
        '--arg \'{"id": "demo-1", "description": "Ad-hoc task"}\'',
    )
    parser.add_argument("workflow", help="Registered workflow type name, e.g. HelloAgentWorkflow")
    parser.add_argument(
        "--arg",
        dest="args",
        action="append",
        default=[],
        help="A single workflow argument, JSON-encoded. Repeat in order for multiple positional args.",
    )
    parser.add_argument("--id", dest="workflow_id", default=None)
    parser.add_argument("--task-queue", dest="task_queue", default=None)
    args = parser.parse_args()

    settings = load_settings()
    client = await Client.connect(settings.temporal_address, namespace=settings.temporal_namespace)

    workflow_args = [json.loads(a) for a in args.args]
    workflow_id = args.workflow_id or f"{args.workflow}-{uuid.uuid4()}"
    task_queue = args.task_queue or settings.task_queue

    result = await client.execute_workflow(
        args.workflow,
        args=workflow_args,
        id=workflow_id,
        task_queue=task_queue,
    )

    print(result)


if __name__ == "__main__":
    asyncio.run(main())
