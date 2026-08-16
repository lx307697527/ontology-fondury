"use client";

import { useCallback, useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

type Ot = { id: string; name: string; display_name: string; status: string; provenance: string };
type Lt = { id: string; name: string; display_name: string; status: string; provenance: string };
type Ob = { id: string; title: string; object_type_name: string; status: string; provenance: string };
type Lk = {
  id: string;
  link_type_name: string;
  source_title: string;
  target_title: string;
  status: string;
  provenance: string;
};

type Queue = { object_types: Ot[]; link_types: Lt[]; objects: Ob[]; links: Lk[] };

const ENT_OT = "object_type";
const ENT_LT = "link_type";
const ENT_OB = "object";
const ENT_LK = "link";

export default function ReviewPage() {
  const [q, setQ] = useState<Queue>({ object_types: [], link_types: [], objects: [], links: [] });
  const [busy, setBusy] = useState<string | null>(null);
  const [comments, setComments] = useState<Record<string, string>>({});

  const refresh = useCallback(async () => {
    const r = await fetch(`${API_BASE}/api/review/queue`)
      .then((r) => r.json())
      .catch(() => null);
    if (r) setQ(r);
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function act(entity: string, id: string, action: "approve" | "reject") {
    const key = `${entity}:${id}`;
    setBusy(key);
    await fetch(`${API_BASE}/api/review/${entity}/${id}/${action}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ actor: "web-ui", comment: comments[key] || "" }),
    });
    setBusy(null);
    setComments((c) => {
      const n = { ...c };
      delete n[key];
      return n;
    });
    refresh();
  }

  const setComment = (key: string, v: string) => setComments((c) => ({ ...c, [key]: v }));

  function actions(entity: string, id: string, status: string) {
    const key = `${entity}:${id}`;
    if (status !== "draft") return <span className="status">{status}</span>;
    return (
      <div className="row">
        <input
          type="text"
          value={comments[key] || ""}
          onChange={(e) => setComment(key, e.target.value)}
          placeholder="备注"
        />
        <button disabled={busy === key} onClick={() => act(entity, id, "approve")}>
          通过
        </button>
        <button disabled={busy === key} onClick={() => act(entity, id, "reject")}>
          驳回
        </button>
      </div>
    );
  }

  function badge(p: string) {
    return <span className={`badge ${p}`}>{p}</span>;
  }

  const empty =
    q.object_types.length + q.link_types.length + q.objects.length + q.links.length === 0;

  return (
    <main>
      <h1>审核队列</h1>
      <p className="subtitle">
        审核 LLM 草案：approve 升级徽章（llm→llm_approved）并写审计日志；reject 归档。{" "}
        <a href="/">← 返回首页</a>
      </p>
      {empty && <p className="status">队列为空（无 draft 行）。</p>}

      {q.object_types.length > 0 && (
        <div className="panel">
          <h2>Object Types（{q.object_types.length}）</h2>
          <table>
            <thead>
              <tr>
                <th>标识</th>
                <th>名称</th>
                <th>来源</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {q.object_types.map((t) => (
                <tr key={t.id}>
                  <td>{t.name}</td>
                  <td>{t.display_name}</td>
                  <td>{badge(t.provenance)}</td>
                  <td>{actions(ENT_OT, t.id, t.status)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {q.link_types.length > 0 && (
        <div className="panel">
          <h2>Link Types（{q.link_types.length}）</h2>
          <table>
            <thead>
              <tr>
                <th>标识</th>
                <th>名称</th>
                <th>来源</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {q.link_types.map((t) => (
                <tr key={t.id}>
                  <td>{t.name}</td>
                  <td>{t.display_name}</td>
                  <td>{badge(t.provenance)}</td>
                  <td>{actions(ENT_LT, t.id, t.status)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {q.objects.length > 0 && (
        <div className="panel">
          <h2>Objects（{q.objects.length}）</h2>
          <table>
            <thead>
              <tr>
                <th>类型</th>
                <th>标题</th>
                <th>来源</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {q.objects.map((o) => (
                <tr key={o.id}>
                  <td>{o.object_type_name}</td>
                  <td>{o.title}</td>
                  <td>{badge(o.provenance)}</td>
                  <td>{actions(ENT_OB, o.id, o.status)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {q.links.length > 0 && (
        <div className="panel">
          <h2>Links（{q.links.length}）</h2>
          <table>
            <thead>
              <tr>
                <th>关系</th>
                <th>源 → 目标</th>
                <th>来源</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {q.links.map((l) => (
                <tr key={l.id}>
                  <td>{l.link_type_name}</td>
                  <td>
                    {l.source_title} → {l.target_title}
                  </td>
                  <td>{badge(l.provenance)}</td>
                  <td>{actions(ENT_LK, l.id, l.status)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
