import os

# knowledge_grove.mcp_server builds a SQLAlchemy engine at import time from
# this env var. Tests never hit the real database (mcp_server is monkeypatched
# wherever it matters), but importing agent_activity still requires a
# syntactically valid DSN to be present.
os.environ.setdefault("KNOWLEDGE_GROVE_DSN", "postgresql+psycopg://test:test@localhost/test")
