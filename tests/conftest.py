import os
import tempfile
from pathlib import Path


os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("DRY_RUN", "true")
os.environ.setdefault("POLYMARKET_DB_PATH", str(Path(tempfile.gettempdir()) / "polymarket_pipeline_pytest.db"))
