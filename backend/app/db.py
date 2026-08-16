from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 项目无 Alembic，create_all 不改既有表；此处幂等补历史迁移。
# 新增列时：先加 model 字段，再在此追加 IF NOT EXISTS ALTER。
_LEGACY_MIGRATIONS = [
    "ALTER TABLE links ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'draft'",
]


def run_legacy_migrations() -> None:
    """幂等补列。dev 安全；接入 Alembic 后此函数可移除。"""
    with engine.begin() as conn:
        for stmt in _LEGACY_MIGRATIONS:
            conn.execute(text(stmt))
