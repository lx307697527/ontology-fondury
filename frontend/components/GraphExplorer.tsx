"use client";

import { useEffect, useRef } from "react";
import cytoscape from "cytoscape";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export default function GraphExplorer() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cy: cytoscape.Core | null = null;
    fetch(`${API_BASE}/api/objects/graph`)
      .then((r) => r.json())
      .then((graph: { nodes: any[]; edges: any[] }) => {
        if (!ref.current) return;
        cy = cytoscape({
          container: ref.current,
          elements: [
            ...graph.nodes.map((n) => ({ data: { id: n.id, label: n.title, type: n.object_type_name } })),
            ...graph.edges.map((e) => ({ data: { id: e.id, source: e.source, target: e.target, label: e.link_type_name } })),
          ],
          style: [
            { selector: "node", style: { label: "data(label)", "font-size": 10, color: "#aeb7cc", "background-color": "#3b6ef6", width: 18, height: 18 } },
            { selector: "edge", style: { width: 1, "line-color": "#3a4358", "target-arrow-color": "#3a4358", "target-arrow-shape": "triangle", "curve-style": "bezier" } },
          ],
          layout: { name: "cose", animate: false },
        });
      });
    return () => cy?.destroy();
  }, []);

  return <div id="graph" ref={ref} />;
}
