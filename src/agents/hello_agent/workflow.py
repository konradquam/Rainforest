from datetime import timedelta

from temporalio import workflow

from core.activity_names import RUN_AGENT_ACTIVITY
from core.models import AgentResult, Task


@workflow.defn
class HelloAgentWorkflow:
    @workflow.run
    async def run(self, prompt: str, task: Task) -> AgentResult:
        return await workflow.execute_activity(
            RUN_AGENT_ACTIVITY,
            args=[prompt, task],
            result_type=AgentResult,
            start_to_close_timeout=timedelta(minutes=2),
        )
