"""FEAT-001 层 4 错误路径：三条兜底，验证 db 落 failed + 错误串。

- 路径1：不支持的文件类型 → 文档 status=failed + error，process 返回 400
- 路径2：LLM 连续 3 次非法 JSON → induction ExtractionRun=failed、document=failed、错误串落库
- 路径3：LLM 不可达（网络） → document=failed + 错误串；另核对客户端 timeout=120s 兜底
"""
from sqlalchemy import select

from app.db import SessionLocal
from app.models import Document, ExtractionRun
from app.modules.services import llm as llm_mod


# --- 伪造 OpenAI 客户端，驱动 complete_json 真实的 3 次重试循环 ---

class _Msg:
    def __init__(self, content): self.content = content

class _Choice:
    def __init__(self, content): self.message = _Msg(content)

class _Resp:
    def __init__(self, content): self.choices = [_Choice(content)]


class _FakeClient:
    timeout = 120.0

    class chat:
        class completions:
            @staticmethod
            def create(**kw): return _Resp("这不是合法 JSON：{{{ 坏掉")  # 永远非法 JSON


class _RaisingClient:
    timeout = 120.0

    class chat:
        class completions:
            @staticmethod
            def create(**kw): raise Exception("connection refused (模拟 LLM 不可达)")


def _doc_by_filename(client, filename):
    with SessionLocal() as db:
        return db.scalar(select(Document).where(Document.filename == filename))


# --- 路径1：不支持的文件类型 ---

def test_unsupported_file_type_lands_failed(client):
    resp = client.post(
        "/api/documents",
        files={"file": ("bad.xlsx", b"\x50\x4b\x03\x04", "application/vnd.ms-excel")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "failed"
    assert "不支持的文件类型" in body["error"]

    doc = _doc_by_filename(client, "bad.xlsx")
    assert doc.status == "failed"
    assert doc.error
    assert doc.raw_text in (None, "")

    # process 据 not raw_text 返回 400
    proc = client.post(f"/api/documents/{doc.id}/process")
    assert proc.status_code == 400


# --- 路径2：LLM 连续 3 次非法 JSON ---

def test_three_illegal_json_lands_failed(client, monkeypatch):
    monkeypatch.setattr(llm_mod, "OpenAI", lambda **kw: _FakeClient())

    up = client.post(
        "/api/documents",
        files={"file": ("ok.md", "褪黑素软糖由达人推广。".encode(), "text/markdown")},
    )
    doc_id = up.json()["id"]
    proc = client.post(f"/api/documents/{doc_id}/process")
    assert proc.status_code == 200  # 后台任务同步等待完成（TestClient 同步执行 BackgroundTasks）

    with SessionLocal() as db:
        doc = db.get(Document, doc_id)
        assert doc.status == "failed"
        assert "JSON" in doc.error or "json" in doc.error.lower()
        runs = db.scalars(select(ExtractionRun).where(ExtractionRun.document_id == doc_id)).all()
        induction = next(r for r in runs if r.stage == "induction")
        assert induction.status == "failed"


# --- 路径3：LLM 不可达 ---

def test_llm_unreachable_lands_failed(client, monkeypatch):
    monkeypatch.setattr(llm_mod, "OpenAI", lambda **kw: _RaisingClient())
    monkeypatch.setattr(llm_mod.time, "sleep", lambda _s: None)  # 跳过退避等待

    up = client.post(
        "/api/documents",
        files={"file": ("ok2.md", "合规话术分三级。".encode(), "text/markdown")},
    )
    doc_id = up.json()["id"]
    client.post(f"/api/documents/{doc_id}/process")

    with SessionLocal() as db:
        doc = db.get(Document, doc_id)
        assert doc.status == "failed"
        assert "LLM" in doc.error or "connection" in doc.error.lower()


def test_client_timeout_is_120s():
    """DoD：客户端 120s 超时兜底（防 SDK 默认 600s × 重试叠加）。"""
    inst = llm_mod.LLM()
    assert inst.client.timeout == 120.0
