"""W4 错误路径测试夹具：用独立 fondry_test 库隔离，避免污染 dev 数据。

psycopg + JSONB 只能跑在 postgres 上，不走 sqlite。conftest 在导入 app 之前
把 DATABASE_URL 指向 fondry_test 并建库；app.db.engine 随之绑定测试库。
"""
import os

import psycopg
import pytest

_TEST_DB = "fondry_test"
_TEST_DSN = f"postgresql+psycopg://fondry:fondry@localhost:5432/{_TEST_DB}"

# 必须在导入 app.* 之前设定，engine 在 import 期即读 get_settings()
os.environ["DATABASE_URL"] = _TEST_DSN
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("LLM_BASE_URL", "http://localhost:1")
os.environ.setdefault("LLM_MODEL", "test-model")


def _ensure_test_db() -> None:
    try:
        with psycopg.connect(
            f"host=localhost port=5432 dbname=postgres user=fondry password=fondry",
            autocommit=True,
        ) as conn:
            conn.execute(f"CREATE DATABASE {_TEST_DB}")
    except psycopg.errors.DuplicateDatabase:
        pass


_ensure_test_db()

from app.db import Base, engine, run_legacy_migrations  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _schema():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    run_legacy_migrations()
    yield
    # 测试结束不清库，便于人工核对；下次 drop_all 重建


@pytest.fixture()
def client():
    return TestClient(app)
