"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import cytoscape, { Core, NodeSingular } from "cytoscape";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

// 类型 → 稳定色板（暗色主题下可读）。新增类型自动落到回退色。
const TYPE_PALETTE: Record<string, string> = {
  product: "#3b6ef6",
  ingredient: "#2aa198",
  factory: "#b58900",
  certificate: "#6c71c4",
  client: "#cb4b16",
  influencer: "#d33682",
  compliance_script: "#859900",
  compliance_violation: "#dc322f",
  batch: "#268bd2",
  quality_report: "#b58900",
  raw_material: "#2aa198",
  customer_complaint: "#cb4b16",
  live_session: "#d33682",
  cooperation_contract: "#6c71c4",
  script_review: "#859900",
};
const FALLBACK_COLOR = "#5b6478";

type GraphNode = { id: string; title: string; object_type_name: string };
type GraphEdge = { id: string; source: string; target: string; link_type_name: string };
type Graph = { nodes: GraphNode[]; edges: GraphEdge[] };

type Neighbor = {
  link_type_name: string;
  direction: "out" | "in";
  object: { id: string; title: string; object_type_name: string; provenance: string; confidence: number };
};
type ObjectDetail = {
  id: string;
  title: string;
  object_type_name: string;
  properties: Record<string, string>;
  provenance: string;
  confidence: number;
  neighbors: Neighbor[];
};

function colorFor(type: string) {
  return TYPE_PALETTE[type] || FALLBACK_COLOR;
}

export default function GraphExplorer() {
  const ref = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<ObjectDetail | null>(null);
  const [detailBusy, setDetailBusy] = useState(false);
  const [types, setTypes] = useState<Record<string, string>>({});

  const loadDetail = useCallback(async (nodeId: string, fallbackType: string) => {
    setDetailBusy(true);
    try {
      const resp = await fetch(`${API_BASE}/api/objects/${nodeId}`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const detail: ObjectDetail = await resp.json();
      // 后端旧版本可能不返回 object_type_name，用图里已知的回退
      if (!detail.object_type_name) detail.object_type_name = fallbackType;
      setSelected(detail);
    } catch (e) {
      setError(`加载节点详情失败：${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setDetailBusy(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    fetch(`${API_BASE}/api/objects/graph`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((graph: Graph) => {
        if (cancelled || !ref.current) return;
        const typeMap: Record<string, string> = {};
        graph.nodes.forEach((n) => {
          if (n.object_type_name) typeMap[n.object_type_name] = colorFor(n.object_type_name);
        });
        setTypes(typeMap);
        const cy = cytoscape({
          container: ref.current,
          elements: [
            ...graph.nodes.map((n) => ({
              data: { id: n.id, label: n.title, type: n.object_type_name, color: colorFor(n.object_type_name) },
            })),
            ...graph.edges.map((e) => ({
              data: { id: e.id, source: e.source, target: e.target, label: e.link_type_name },
            })),
          ],
          style: [
            {
              selector: "node",
              style: {
                label: "data(label)",
                "font-size": 10,
                color: "#aeb7cc",
                "background-color": "data(color)",
                width: 22,
                height: 22,
                "border-width": 0,
                "text-valign": "bottom",
                "text-margin-y": 4,
              },
            },
            {
              selector: "node:selected",
              style: { "border-width": 3, "border-color": "#e6e8ee" },
            },
            {
              selector: "edge",
              style: {
                width: 1,
                "line-color": "#3a4358",
                "target-arrow-color": "#3a4358",
                "target-arrow-shape": "triangle",
                "curve-style": "bezier",
                label: "data(label)",
                "font-size": 8,
                color: "#5b6478",
                "text-rotation": "autorotate",
              },
            },
          ],
          layout: { name: "cose", animate: false, padding: 24, idealEdgeLength: 80 },
        });
        cyRef.current = cy;
        cy.on("tap", "node", (evt: { target: NodeSingular }) => {
          const node = evt.target;
          loadDetail(node.id(), node.data("type"));
        });
        setLoading(false);
      })
      .catch((e) => {
        if (cancelled) return;
        setError(`加载图谱失败：${e instanceof Error ? e.message : String(e)}`);
        setLoading(false);
      });
    return () => {
      cancelled = true;
      cyRef.current?.destroy();
      cyRef.current = null;
    };
  }, [loadDetail]);

  const legendTypes = Object.keys(types);

  return (
    <div className="graph-wrap">
      <div className="graph-canvas-wrap">
        {loading && <p className="status">加载图谱中…</p>}
        {error && <p className="status" style={{ color: "#dc322f" }}>{error}</p>}
        <div id="graph" ref={ref} />
      </div>
      <div className="graph-side">
        <div className="legend">
          <h3>类型图例</h3>
          {legendTypes.length === 0 && <p className="status">无节点</p>}
          <ul>
            {legendTypes.map((t) => (
              <li key={t}>
                <span className="dot" style={{ background: types[t] }} />
                {t}
              </li>
            ))}
          </ul>
        </div>
        <div className="detail">
          <h3>节点详情</h3>
          {!selected && <p className="status">点击节点查看详情与邻居</p>}
          {selected && (
            <>
              {detailBusy && <p className="status">加载中…</p>}
              <p className="detail-title">{selected.title}</p>
              <p className="status">
                类型：<strong>{selected.object_type_name || "—"}</strong> · 来源：
                <span className={`badge ${selected.provenance}`}>{selected.provenance}</span> · 置信 {selected.confidence.toFixed(2)}
              </p>
              {Object.keys(selected.properties).length > 0 && (
                <table>
                  <tbody>
                    {Object.entries(selected.properties).map(([k, v]) => (
                      <tr key={k}>
                        <th>{k}</th>
                        <td>{String(v)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
              <h4>邻居（{selected.neighbors.length}）</h4>
              <ul className="neighbors">
                {selected.neighbors.map((n, i) => (
                  <li key={i}>
                    <span className="dir">{n.direction === "out" ? "→" : "←"}</span>
                    <span className="lt">{n.link_type_name}</span>
                    <span className="nt">{n.object.title}</span>
                    <span className="status"> {n.object.object_type_name || ""}</span>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
