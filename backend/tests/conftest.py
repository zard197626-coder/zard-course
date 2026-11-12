from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app


@pytest.fixture
def client():
    # 不使用 pytest 的系统临时目录，确保在受限文件系统（如沙箱）中也能运行。
    base = Path(os.getenv("CAMPUS_TEST_DB_DIR", Path.cwd() / ".test-data"))
    base.mkdir(parents=True, exist_ok=True)
    database_path = base / f"test-{uuid.uuid4().hex}.db"
    application = create_app(database_path)
    with TestClient(application) as test_client:
        yield test_client
    for suffix in ("", "-wal", "-shm"):
        try:
            (base / f"{database_path.name}{suffix}").unlink(missing_ok=True)
        except OSError:
            pass
