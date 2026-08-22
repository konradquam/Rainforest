from core.models import AgentResult, Task


def test_task_defaults_metadata_to_empty_dict():
    task = Task(id="t1", description="desc")
    assert task.metadata == {}


def test_task_metadata_is_independent_per_instance():
    a = Task(id="a", description="a")
    b = Task(id="b", description="b")
    a.metadata["k"] = "v"
    assert b.metadata == {}


def test_agent_result_stop_reason_defaults_to_none():
    result = AgentResult(output="hi")
    assert result.stop_reason is None
