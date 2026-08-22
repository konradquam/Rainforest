import pytest
from temporalio.testing import ActivityEnvironment

from activities import agent_activity
from core.activity_names import RUN_AGENT_ACTIVITY
from core.config import Settings
from core.models import Task


class _FakeTextBlock:
    type = "text"

    def __init__(self, text):
        self.text = text


class _FakeResponse:
    def __init__(self, text, stop_reason):
        self.content = [_FakeTextBlock(text)]
        self.stop_reason = stop_reason


class _FakeMessages:
    def __init__(self, response):
        self._response = response
        self.last_kwargs = None

    async def create(self, **kwargs):
        self.last_kwargs = kwargs
        return self._response


class _FakeClient:
    def __init__(self, response):
        self.messages = _FakeMessages(response)


def test_activity_registered_under_shared_constant():
    assert agent_activity.run_agent_activity.__temporal_activity_definition.name == RUN_AGENT_ACTIVITY


async def test_run_agent_activity_returns_text_and_stop_reason(monkeypatch):
    fake_client = _FakeClient(_FakeResponse("hello there", "end_turn"))
    fake_settings = Settings(
        anthropic_api_key="test-key",
        anthropic_model="claude-test",
        temporal_address="localhost:7233",
        temporal_namespace="default",
        task_queue="agent-task-queue",
    )
    monkeypatch.setattr(agent_activity, "_get_client", lambda: fake_client)
    monkeypatch.setattr(agent_activity, "load_settings", lambda: fake_settings)

    env = ActivityEnvironment()
    task = Task(id="t1", description="say hi")
    result = await env.run(agent_activity.run_agent_activity, "hello", task)

    assert result.output == "hello there"
    assert result.stop_reason == "end_turn"
    assert fake_client.messages.last_kwargs["model"] == "claude-test"
    assert "t1" in fake_client.messages.last_kwargs["system"]
