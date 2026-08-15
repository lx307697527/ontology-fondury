"""本体归纳质量评估：对 eval/samples.jsonl 逐条跑 induction，按人工标注的期望 object types 算通过率。

用法（backend 目录下）：
    python eval/run_eval.py            # 全量 20 条
    python eval/run_eval.py 3          # 只跑前 3 条（调试）
报告落盘 eval/reports/report-<时间戳>.json，含逐条命中明细，供每周对比。
"""

import json
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.modules.services.llm import LLM, PROMPT_VERSION  # noqa: E402

EVAL_DIR = Path(__file__).resolve().parent


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9_]", "", str(name).strip().lower().replace("-", "_"))


def load_samples() -> list[dict]:
    samples = []
    with open(EVAL_DIR / "samples.jsonl", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                samples.append(json.loads(line))
    return samples


def match_expected(proposed_names: set[str], expected: list[dict]) -> tuple[list[str], list[str]]:
    """返回（命中的期望类型, 漏掉的期望类型）"""
    hit, miss = [], []
    for exp in expected:
        keys = {_slug(exp["name"]), *(_slug(a) for a in exp.get("aliases", []))}
        # 允许单复数差异（product/products）
        keys |= {f"{k}s" for k in list(keys)}
        keys |= {k[:-1] for k in list(keys) if k.endswith("s") and len(k) > 3}
        if keys & proposed_names:
            hit.append(exp["name"])
        else:
            miss.append(exp["name"])
    return hit, miss


def main() -> None:
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    samples = load_samples()
    if limit:
        samples = samples[:limit]

    llm = LLM()
    results, passed = [], 0
    for s in samples:
        expected = s["expected_object_types"]
        try:
            proposal = llm.induce_schema([s["text"]])
            proposed = {_slug(t.get("name", "")) for t in proposal.get("object_types", [])} - {""}
            hit, miss = match_expected(proposed, expected)
            recall = len(hit) / len(expected) if expected else 0.0
            ok = not miss
            results.append({
                "id": s["id"], "ok": ok, "recall": round(recall, 3),
                "hit": hit, "miss": miss,
                "proposed": sorted(proposed),
                "extra": sorted(proposed - {k for e in expected for k in [e["name"], *e.get("aliases", [])]}),
            })
        except Exception as e:  # noqa: BLE001 - 单条失败不中断整轮评估
            results.append({"id": s["id"], "ok": False, "recall": 0.0, "error": f"{e}\n{traceback.format_exc()[-500:]}"})
        r = results[-1]
        print(f"[{'PASS' if r['ok'] else 'FAIL'}] {s['id']}: recall={r['recall']} miss={r.get('miss')}")

    total = len(results)
    mean_recall = sum(r["recall"] for r in results) / total if total else 0.0
    passed = sum(1 for r in results if r["ok"])
    report = {
        "ran_at": datetime.now().isoformat(timespec="seconds"),
        "model": llm.model_label,
        "prompt_version": PROMPT_VERSION,
        "pass_rate": round(passed / total, 3) if total else 0,
        "mean_recall": round(mean_recall, 3),
        "results": results,
    }
    out_dir = EVAL_DIR / "reports"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n通过率 {passed}/{total} = {report['pass_rate']:.0%} · 平均召回 {report['mean_recall']:.1%} · 报告 {out}")


if __name__ == "__main__":
    main()
