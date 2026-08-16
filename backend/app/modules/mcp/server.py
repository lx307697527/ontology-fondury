"""MCP server：把知识图谱暴露为 LLM 工具，供外部客户端（Claude Desktop / opencode / Cursor）挂载。

工具（4 个）：
- list_object_types()：本体目录（LLM 先调此了解有哪些实体类型）
- list_link_types()：关系类型目录（了解有哪些关系可遍历）
- search_objects(q, type_name?, limit?)：按标题 ILIKE 搜索 + 可选类型过滤
- get_object_detail(object_id)：对象详情 + 邻居遍历（出/入方向，带 link_type_name）

复用 app.db.SessionLocal（手动开 session，不走 FastAPI Depends）。查询逻辑与
app.modules.api.objects / search 对齐。入口：python -m app.mcp_main（stdio 传输）。
"""

from sqlalchemy import or_, select

from app.db import SessionLocal
from app.models import Link, LinkType, Object, ObjectType
from fastmcp import FastMCP

mcp = FastMCP("ontology-fondry")


@mcp.tool
def list_object_types() -> list[dict]:
    """列出全部 object type（本体目录）。返回每项含 name/display_name/description/
    properties/status/provenance。LLM 回答问题前先调此工具，了解图谱中有哪些实体类型。"""
    with SessionLocal() as db:
        rows = db.scalars(select(ObjectType).order_by(ObjectType.name)).all()
        return [
            {
                "id": t.id,
                "name": t.name,
                "display_name": t.display_name,
                "description": t.description,
                "properties": t.properties,
                "status": t.status,
                "provenance": t.provenance,
            }
            for t in rows
        ]


@mcp.tool
def list_link_types() -> list[dict]:
    """列出全部 link type（关系类型目录）。返回每项含 name/display_name/description/
    source_object_type_id/target_object_type_id/cardinality/status/provenance。
    LLM 调此了解图谱中有哪些关系可遍历（如"推广""含原料""合规分级"）。"""
    with SessionLocal() as db:
        rows = db.scalars(select(LinkType).order_by(LinkType.name)).all()
        return [
            {
                "id": t.id,
                "name": t.name,
                "display_name": t.display_name,
                "description": t.description,
                "source_object_type_id": t.source_object_type_id,
                "target_object_type_id": t.target_object_type_id,
                "cardinality": t.cardinality,
                "status": t.status,
                "provenance": t.provenance,
            }
            for t in rows
        ]


@mcp.tool
def search_objects(q: str, type_name: str = "", limit: int = 20) -> list[dict]:
    """按标题全文（ILIKE）搜索对象，可按 object type 的 name 过滤。返回 [{id, title,
    object_type_name, properties, provenance, confidence}]。用于回答"有哪些 X"类问题，
    如"有哪些达人推广褪黑素软糖""有哪些原料"。q 为空时按置信度返回顶部对象。"""
    with SessionLocal() as db:
        query = select(Object).order_by(Object.confidence.desc())
        if type_name:
            query = query.join(ObjectType).where(ObjectType.name == type_name)
        if q:
            query = query.where(Object.title.ilike(f"%{q}%"))
        rows = db.scalars(query.limit(min(limit, 100))).all()
        type_names = {t.id: t.name for t in db.scalars(select(ObjectType)).all()}
        return [
            {
                "id": o.id,
                "title": o.title,
                "object_type_name": type_names.get(o.object_type_id, ""),
                "properties": o.properties,
                "provenance": o.provenance,
                "confidence": o.confidence,
            }
            for o in rows
        ]


@mcp.tool
def get_object_detail(object_id: str) -> dict:
    """取对象详情 + 邻居遍历。返回 {object: {...}, neighbors: [{link_type_name,
    direction, object: {id, title, object_type_name, provenance}}]}。direction 为
    out（该对象为源）/ in（该对象为目标）。用于回答关系型问题，如"褪黑素软糖用了哪些原料"
    "有哪些达人推广它""合规话术分级"。"""
    with SessionLocal() as db:
        obj = db.get(Object, object_id)
        if obj is None:
            return {"error": f"object {object_id} not found"}
        type_names = {t.id: t.name for t in db.scalars(select(ObjectType)).all()}
        rows = db.execute(
            select(Link, LinkType, Object)
            .join(LinkType, Link.link_type_id == LinkType.id)
            .join(Object, or_(Link.source_object_id == Object.id, Link.target_object_id == Object.id))
            .where(or_(Link.source_object_id == object_id, Link.target_object_id == object_id))
            .where(Object.id != object_id)
            .limit(200)
        ).all()
        neighbors = [
            {
                "link_type_name": link_type.name,
                "direction": "out" if link.source_object_id == object_id else "in",
                "object": {
                    "id": other.id,
                    "title": other.title,
                    "object_type_name": type_names.get(other.object_type_id, ""),
                    "provenance": other.provenance,
                },
            }
            for link, link_type, other in rows
        ]
        return {
            "object": {
                "id": obj.id,
                "title": obj.title,
                "object_type_name": type_names.get(obj.object_type_id, ""),
                "properties": obj.properties,
                "provenance": obj.provenance,
                "confidence": obj.confidence,
            },
            "neighbors": neighbors,
        }
