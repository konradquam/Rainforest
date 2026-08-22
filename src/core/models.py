from dataclasses import dataclass, field
from typing import Any


@dataclass
class Task:
    id: str
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    output: str
    stop_reason: str | None = None
