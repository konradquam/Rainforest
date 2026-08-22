import pytest

from core.config import load_settings


@pytest.fixture(autouse=True)
def clear_settings_cache():
    load_settings.cache_clear()
    yield
    load_settings.cache_clear()


def test_load_settings_requires_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(RuntimeError):
        load_settings()


def test_load_settings_defaults(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    for var in ("ANTHROPIC_MODEL", "TEMPORAL_ADDRESS", "TEMPORAL_NAMESPACE", "TEMPORAL_TASK_QUEUE"):
        monkeypatch.delenv(var, raising=False)

    settings = load_settings()

    assert settings.anthropic_api_key == "test-key"
    assert settings.anthropic_model == "claude-sonnet-5"
    assert settings.temporal_address == "localhost:7233"
    assert settings.temporal_namespace == "default"
    assert settings.task_queue == "agent-task-queue"


def test_load_settings_reads_overrides(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-opus-5")
    monkeypatch.setenv("TEMPORAL_ADDRESS", "example.com:7233")
    monkeypatch.setenv("TEMPORAL_NAMESPACE", "custom-ns")
    monkeypatch.setenv("TEMPORAL_TASK_QUEUE", "custom-queue")

    settings = load_settings()

    assert settings.anthropic_model == "claude-opus-5"
    assert settings.temporal_address == "example.com:7233"
    assert settings.temporal_namespace == "custom-ns"
    assert settings.task_queue == "custom-queue"
