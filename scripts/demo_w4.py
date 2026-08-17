"""W4 端到端演示：企业文档 → 图谱 → 治理审核 → Agent 问答。

对运行中的栈（dev 或 docker，默认 http://localhost:8000）串起完整链：
  1. 上传 samples/health-commerce/ 三份文档（解析落库）
  2. 对其中一份触发 process（live LLM 抽取，轮询至 processed）
  3. GET /api/objects/graph 打印节点/边（W2 DoD ≥70/≥80）
  4. /api/review 审核一项 object_type（provenance 升 llm_approved + audit_logs）
  5. MCP 三问（fastmcp Client stdio 调 app.mcp_main，确定性 tool 调用作答，不依赖外部 LLM）：
       - 褪黑素软糖用了哪些原料？
       - 有哪些达人推广？
       - 合规话术分级？

输出落 docs/demo/w4/run-<n>.md。复用 scripts/mcp_demo.py 的 fastmcp Client 模式。

用法：python scripts/demo_w4.py [--api http://localhost:8000]
前置：db+api 在跑（docker compose up 或 dev uvicorn）；backend/.venv 装好 -e .
"""
import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

import requests
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
SAMPLES = ROOT / "samples" / "health-commerce"
OUT_DIR = ROOT / "docs" / "demo" / "w4"
VENV_PY = str(BACKEND / ".venv" / "bin" / "python")

QUESTIONS = [
    "褪黑素软糖用了哪些原料？",
    "有哪些达人推广？",
    "合规话术分级？",
]


def _log(buf: list[str], msg: str) -> None:
    print(msg)
    buf.append(msg)


def upload_documents(api: str, buf: list[str]) -> list[dict]:
    docs = []
    for path in sorted(SAMPLES.iterdir()):
        if path.suffix not in (".md", ".txt", ".pdf", ".docx"):
            continue
        with open(path, "rb") as f:
            r = requests.post(
                f"{api}/api/documents",
                files={"file": (path.name, f, "application/octet-stream")},
                timeout=30,
            )
        r.raise_for_status()
        body = r.json()
        docs.append(body)
        _log(buf, f"  上传 {path.name} → id={body['id'][:8]} status={body['status']}")
    return docs


def process_one(api: str, doc_id: str, buf: list[str], deadline_s: int = 360) -> dict:
    r = requests.post(f"{api}/api/documents/{doc_id}/process", timeout=30)
    r.raise_for_status()
    _log(buf, f"  process 触发 id={doc_id[:8]}，轮询中（至多 {deadline_s}s）…")
    t0 = time.time()
    status = "processing"
    while time.time() - t0 < deadline_s:
        body = requests.get(f"{api}/api/documents/{doc_id}", timeout=10).json()
        status = body.get("status", "?")
        if status in ("processed", "failed"):
            break
        time.sleep(4)
    _log(buf, f"  完成：status={status}（{round(time.time()-t0,1)}s）")
    if status != "processed":
        _log(buf, f"  ⚠ 未在限期内 processed（LLM 端点不稳？），后续沿用既有图谱继续演示")
    return {"status": status, "elapsed": round(time.time() - t0, 1)}


def fetch_graph(api: str, buf: list[str]) -> dict:
    g = requests.get(f"{api}/api/objects/graph", timeout=20).json()
    n, e = len(g.get("nodes", [])), len(g.get("edges", []))
    _log(buf, f"  graph：{n} 节点 / {e} 边（DoD ≥70/≥80）{'✓' if n>=70 and e>=80 else '✗'}")
    return {"nodes": n, "edges": e}


def review_one(api: str, buf: list[str]) -> dict:
    q = requests.get(f"{api}/api/review/queue", timeout=15).json()
    ots = [t for t in q.get("object_types", []) if t.get("status") == "draft"]
    if not ots:
        _log(buf, "  审核队列无 draft object_type（已审完或队列空）")
        return {"skipped": True}
    target = ots[0]
    tid = target["id"]
    before = target.get("provenance")
    r = requests.post(
        f"{api}/api/review/object_type/{tid}/approve",
        json={"actor": "demo-w4", "comment": "W4 演示审核"},
        timeout=15,
    )
    r.raise_for_status()
    after = r.json()
    _log(buf, f"  审核 object_type「{target.get('display_name') or target.get('id')[:8]}」"
             f"provenance {before} → {after.get('provenance')}，status={after.get('status')}，audit 已写")
    return {"id": tid, "before": before, "after": after, "name": target.get("display_name")}


# --- MCP 三问：确定性 tool 调用作答 ---

def _parse(res):
    data = getattr(res, "data", None)
    if data is not None:
        return data
    if res.content:
        try:
            return json.loads(res.content[0].text)
        except Exception:
            return res.content[0].text
    return None


async def mcp_three_questions(buf: list[str]) -> list[dict]:
    if not os.path.exists(VENV_PY):
        _log(buf, f"  ⚠ 找不到 {VENV_PY}，跳过 MCP 三问（先 cd backend && .venv/bin/pip install -e .）")
        return []
    transport = StdioTransport(command=VENV_PY, args=["-m", "app.mcp_main"], cwd=str(BACKEND))
    answers = []
    async with Client(transport) as client:
        ots = _parse(await client.call_tool("list_object_types", {}))
        type_names = {t["name"]: t for t in (ots or [])}

        # Q1 褪黑素软糖用了哪些原料 → 搜"褪黑素"，取 detail 邻居里关系含原料/含成分的方向
        objs = _parse(await client.call_tool("search_objects", {"q": "褪黑素", "limit": 10})) or []
        q1 = {"question": QUESTIONS[0], "matches": len(objs), "answer": []}
        for o in objs[:3]:
            det = _parse(await client.call_tool("get_object_detail", {"object_id": o["id"]})) or {}
            neighbors = det.get("neighbors", [])
            related = [
                {"title": nb["object"]["title"], "type": nb["object"]["object_type_name"],
                 "link": nb["link_type_name"], "dir": nb["direction"]}
                for nb in neighbors
            ]
            q1["answer"].append({"object": o["title"], "type": o["object_type_name"],
                                 "neighbors": related})
        _log(buf, f"  Q1 {QUESTIONS[0]} → 命中 {len(objs)}，首对象邻居 {len(q1['answer'][0]['neighbors']) if q1['answer'] else 0} 条")

        # Q2 有哪些达人推广 → 搜"达人"/type 含 influencer/mentor，或经推广 link 邻居
        q2_objs = (_parse(await client.call_tool("search_objects", {"q": "达人", "limit": 20})) or [])
        if not q2_objs:
            # 退一步：从 Q1 的产品对象邻居里找 direction=in 且 link 含推广/promote 的
            for o in objs[:3]:
                det = _parse(await client.call_tool("get_object_detail", {"object_id": o["id"]})) or {}
                for nb in det.get("neighbors", []):
                    if "推广" in nb["link_type_name"] or "promote" in nb["link_type_name"]:
                        q2_objs.append(nb["object"])
        q2 = {"question": QUESTIONS[1], "matches": len(q2_objs),
              "answer": [{"title": o.get("title"), "type": o.get("object_type_name")} for o in q2_objs]}
        _log(buf, f"  Q2 {QUESTIONS[1]} → 命中 {len(q2_objs)} 位")

        # Q3 合规话术分级 → 按 type_name 查 compliance_script(risk_level)与 script(compliance_grade)
        q3_answer = []
        for tn, grade_key, label in [
            ("compliance_script", "risk_level", "合规话术脚本"),
            ("script", "compliance_grade", "话术脚本"),
        ]:
            rows = _parse(await client.call_tool(
                "search_objects", {"q": "", "type_name": tn, "limit": 20})) or []
            for o in rows:
                props = o.get("properties") or {}
                q3_answer.append({
                    "title": o.get("title"), "type": tn, "label": label,
                    "grade": props.get(grade_key, ""),
                    "review": props.get("review_conclusion") or props.get("content_summary") or "",
                })
        q3 = {"question": QUESTIONS[2], "matches": len(q3_answer), "answer": q3_answer}
        grades = [a["grade"] for a in q3_answer if a["grade"]]
        _log(buf, f"  Q3 {QUESTIONS[2]} → 命中 {len(q3_answer)} 条话术，分级值 {grades[:8]}")

        answers = [q1, q2, q3]
    return answers


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default=os.environ.get("API_BASE", "http://localhost:8000"))
    args = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    buf: list[str] = []
    _log(buf, f"## W4 端到端演示 · {time.strftime('%Y-%m-%d %H:%M:%S')}")
    _log(buf, f"API: {args.api}")
    _log(buf, "")

    _log(buf, "### 1. 上传文档")
    docs = upload_documents(args.api, buf)

    _log(buf, "\n### 2. process（live LLM 抽取一份）")
    proc = {}
    if docs:
        # 选产品合规手册（最贴三问）
        target = next((d for d in docs if "compliance" in d["filename"]), docs[0])
        proc = process_one(args.api, target["id"], buf)

    _log(buf, "\n### 3. 图谱快照")
    graph = fetch_graph(args.api, buf)

    _log(buf, "\n### 4. 治理审核")
    review = review_one(args.api, buf)

    _log(buf, "\n### 5. MCP Agent 问答三问")
    answers = asyncio.run(mcp_three_questions(buf))

    _log(buf, "\n### 结果汇总")
    summary = {"uploaded": len(docs), "process": proc, "graph": graph,
               "review": review, "mcp_answers": answers}
    _log(buf, "```json")
    _log(buf, json.dumps(summary, ensure_ascii=False, indent=2))
    _log(buf, "```")

    n = len(list(OUT_DIR.glob("run-*.md"))) + 1
    out = OUT_DIR / f"run-{n:02d}.md"
    out.write_text("\n".join(buf), encoding="utf-8")
    print(f"\n→ 报告已落 {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
