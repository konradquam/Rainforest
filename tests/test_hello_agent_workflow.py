from temporalio import activity
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from agents.hello_agent import HelloAgentWorkflow
from core.activity_names import RUN_AGENT_ACTIVITY
from core.models import AgentResult, Task


@activity.defn(name=RUN_AGENT_ACTIVITY)
async def fake_run_agent_activity(prompt: str, task: Task) -> AgentResult:
    return AgentResult(output=f"echo:{prompt}:{task.id}", stop_reason="end_turn")


async def test_hello_agent_workflow_calls_agent_activity():
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[HelloAgentWorkflow],
            activities=[fake_run_agent_activity],
        ):
            task = Task(id="t1", description="say hi")
            result = await env.client.execute_workflow(
                HelloAgentWorkflow.run,
                args=["hello", task],
                id="test-hello-agent",
                task_queue="test-queue",
            )

    assert result.output == "echo:hello:t1"
    assert result.stop_reason == "end_turn"
