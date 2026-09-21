import pytest
from mcp_types import Tool
from temporalio.testing import ActivityEnvironment

from activities import agent_activity
from core.activity_names import RUN_AGENT_ACTIVITY
from core.config import Settings
from core.models import Task


class _FakeTextBlock:
    type = "text"

    def __init__(self, text):
        self.text = text


class _FakeToolUseBlock:
    type = "tool_use"

    def __init__(self, id, name, input):
        self.id = id
        self.name = name
        self.input = input


class _FakeResponse:
    def __init__(self, content, stop_reason):
        self.content = content
        self.stop_reason = stop_reason


class _FakeMessages:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    async def create(self, **kwargs):
        # snapshot messages: run_agent_activity mutates the same list object
        # across loop iterations, so capturing a reference would show every
        # call's messages as of the *final* state, not as of that call.
        kwargs = {**kwargs, "messages": list(kwargs["messages"])}
        self.calls.append(kwargs)
        return self._responses.pop(0)


class _FakeClient:
    def __init__(self, responses):
        self.messages = _FakeMessages(responses)


class _FakeCallToolResult:
    def __init__(self, text, is_error=False):
        self.content = [_FakeTextBlock(text)]
        self.is_error = is_error


class _FakeMcpServer:
    def __init__(self, tools, call_tool_result=None):
        self._tools = tools
        self._call_tool_result = call_tool_result
        self.call_tool_calls = []

    async def list_tools(self):
        return self._tools

    async def call_tool(self, name, arguments):
        self.call_tool_calls.append((name, arguments))
        return self._call_tool_result


_FAKE_SETTINGS = Settings(
    anthropic_api_key="test-key",
    anthropic_model="claude-test",
    temporal_address="localhost:7233",
    temporal_namespace="default",
    task_queue="agent-task-queue",
)


def _patch(monkeypatch, client, mcp_server):
    monkeypatch.setattr(agent_activity, "_get_client", lambda: client)
    monkeypatch.setattr(agent_activity, "load_settings", lambda: _FAKE_SETTINGS)
    monkeypatch.setattr(agent_activity, "mcp_server", mcp_server)


def test_activity_registered_under_shared_constant():
    assert agent_activity.run_agent_activity.__temporal_activity_definition.name == RUN_AGENT_ACTIVITY


async def test_run_agent_activity_returns_text_and_stop_reason(monkeypatch):
    response = _FakeResponse([_FakeTextBlock("hello there")], "end_turn")
    fake_client = _FakeClient([response])
    fake_mcp_server = _FakeMcpServer(tools=[])
    _patch(monkeypatch, fake_client, fake_mcp_server)

    env = ActivityEnvironment()
    task = Task(id="t1", description="say hi")
    result = await env.run(agent_activity.run_agent_activity, "hello", task)

    assert result.output == "hello there"
    assert result.stop_reason == "end_turn"
    assert fake_client.messages.calls[0]["model"] == "claude-test"
    assert "t1" in fake_client.messages.calls[0]["system"]
    assert len(fake_client.messages.calls) == 1


async def test_run_agent_activity_translates_mcp_tools_for_anthropic(monkeypatch):
    tool = Tool(name="gather_context", description="search", inputSchema={"type": "object", "properties": {}})
    response = _FakeResponse([_FakeTextBlock("no tools needed")], "end_turn")
    fake_client = _FakeClient([response])
    fake_mcp_server = _FakeMcpServer(tools=[tool])
    _patch(monkeypatch, fake_client, fake_mcp_server)

    env = ActivityEnvironment()
    task = Task(id="t1", description="say hi")
    await env.run(agent_activity.run_agent_activity, "hello", task)

    sent_tools = fake_client.messages.calls[0]["tools"]
    assert sent_tools == [
        {
            "name": "gather_context",
            "description": "search",
            "input_schema": {"type": "object", "properties": {}},
            "cache_control": {"type": "ephemeral"},
        }
    ]


async def test_run_agent_activity_executes_tool_and_continues_loop(monkeypatch):
    tool_use = _FakeToolUseBlock(id="call_1", name="gather_context", input={"query_text": "x", "pattern": "x"})
    first_response = _FakeResponse([tool_use], "tool_use")
    second_response = _FakeResponse([_FakeTextBlock("final answer")], "end_turn")
    fake_client = _FakeClient([first_response, second_response])
    fake_mcp_server = _FakeMcpServer(
        tools=[],
        call_tool_result=_FakeCallToolResult("search result text"),
    )
    _patch(monkeypatch, fake_client, fake_mcp_server)

    env = ActivityEnvironment()
    task = Task(id="t1", description="look something up")
    result = await env.run(agent_activity.run_agent_activity, "hello", task)

    assert result.output == "final answer"
    assert result.stop_reason == "end_turn"
    assert len(fake_client.messages.calls) == 2
    assert fake_mcp_server.call_tool_calls == [("gather_context", {"query_text": "x", "pattern": "x"})]

    second_call_messages = fake_client.messages.calls[1]["messages"]
    tool_result_message = second_call_messages[-1]
    assert tool_result_message["role"] == "user"
    assert tool_result_message["content"] == [
        {
            "type": "tool_result",
            "tool_use_id": "call_1",
            "content": [{"type": "text", "text": "search result text"}],
            "is_error": False,
        }
    ]


async def test_run_agent_activity_propagates_tool_error(monkeypatch):
    tool_use = _FakeToolUseBlock(id="call_1", name="gather_context", input={})
    first_response = _FakeResponse([tool_use], "tool_use")
    second_response = _FakeResponse([_FakeTextBlock("recovered")], "end_turn")
    fake_client = _FakeClient([first_response, second_response])
    fake_mcp_server = _FakeMcpServer(
        tools=[],
        call_tool_result=_FakeCallToolResult("boom", is_error=True),
    )
    _patch(monkeypatch, fake_client, fake_mcp_server)

    env = ActivityEnvironment()
    task = Task(id="t1", description="look something up")
    await env.run(agent_activity.run_agent_activity, "hello", task)

    tool_result_message = fake_client.messages.calls[1]["messages"][-1]
    assert tool_result_message["content"][0]["is_error"] is True
