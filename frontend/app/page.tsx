"use client";

import { useCallback, useEffect, useState } from "react";
import GraphExplorer from "@/components/GraphExplorer";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

type Doc = { id: string; filename: string; status: string };
type ObjectType = { id: string; name: string; display_name: string; status: string; provenance: string };

export default function Home() {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [types, setTypes] = useState<ObjectType[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState("");

  const refresh = useCallback(async () => {
    const [docsResp, typesResp] = await Promise.all([
      fetch(`${API_BASE}/api/documents`).then((r) => r.json()).catch(() => []),
      fetch(`${API_BASE}/api/ontology/object-types`).then((r) => r.json()).catch(() => []),
    ]);
    setDocs(docsResp);
    setTypes(typesResp);
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function upload(file: File) {
    setBusy("upload");
    setMessage("");
    const form = new FormData();
    form.append("file", file);
    const created = await fetch(`${API_BASE}/api/documents`, { method: "POST", body: form }).then((r) => r.json());
    await fetch(`${API_BASE}/api/documents/${created.id}/process`, { method: "POST" });
    setBusy(null);
    setMessage(`已上传「${file.name}」，后台处理中（LLM 归纳+抽取需要几分钟），稍后刷新查看。`);
    refresh();
  }

  async function approve(typeId: string) {
    setBusy(typeId);
    await fetch(`${API_BASE}/api/review/object_type/${typeId}/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ actor: "web-ui" }),
    });
    setBusy(null);
    refresh();
  }

  return (
    <main>
      <h1>ontology-fondry</h1>
      <p className="subtitle">上传企业文档 → LLM 自动建本体和图谱 → 审核 → API / AI 应用消费</p>

      <div className="panel">
        <h2>文档接入</h2>
        <div className="row">
          <input
            type="file"
            accept=".txt,.md,.pdf,.docx"
            onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])}
            disabled={busy === "upload"}
          />
          {busy === "upload" && <span className="status">上传中…</span>}
          <button onClick={refresh}>刷新</button>
        </div>
        {message && <p className="status">{message}</p>}
        {docs.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>文件</th>
                <th>状态</th>
              </tr>
            </thead>
            <tbody>
              {docs.map((d) => (
                <tr key={d.id}>
                  <td>{d.filename}</td>
                  <td>{d.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="panel">
        <h2>本体（object types）</h2>
        {types.length === 0 && <p className="status">还没有本体，上传第一份文档开始。</p>}
        {types.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>标识</th>
                <th>名称</th>
                <th>状态</th>
                <th>来源</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {types.map((t) => (
                <tr key={t.id}>
                  <td>{t.name}</td>
                  <td>{t.display_name}</td>
                  <td>{t.status}</td>
                  <td>
                    <span className={`badge ${t.provenance}`}>{t.provenance}</span>
                  </td>
                  <td>
                    {t.status === "draft" && (
                      <button disabled={busy === t.id} onClick={() => approve(t.id)}>
                        审核通过
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="panel">
        <h2>知识图谱</h2>
        <GraphExplorer />
      </div>
    </main>
  );
}
