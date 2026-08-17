## W4 端到端演示 · 2026-08-17 09:21:43
API: http://localhost:8000

### 1. 上传文档
  上传 konuo-influencer-script-ledger.md → id=a9059dc4 status=parsed
  上传 konuo-product-compliance-handbook.md → id=4b1ac766 status=parsed
  上传 konuo-quality-batch-traceability.md → id=42ea58bb status=parsed

### 2. process（live LLM 抽取一份）
  process 触发 id=4b1ac766，轮询中（至多 240s）…
  完成：status=parsed（241.1s）
  ⚠ 未在限期内 processed（LLM 端点不稳？），后续沿用既有图谱继续演示

### 3. 图谱快照
  graph：70 节点 / 80 边（DoD ≥70/≥80）✓

### 4. 治理审核
  审核 object_type「生产工厂」provenance llm → llm_approved，status=approved，audit 已写

### 5. MCP Agent 问答三问
  Q1 褪黑素软糖用了哪些原料？ → 命中 5，首对象邻居 18 条
  Q2 有哪些达人推广？ → 命中 5 位
  Q3 合规话术分级？ → 命中 0，首对象属性 []

### 结果汇总
```json
{
  "uploaded": 3,
  "process": {
    "status": "parsed",
    "elapsed": 241.1
  },
  "graph": {
    "nodes": 70,
    "edges": 80
  },
  "review": {
    "id": "2729805ecae14d598b79090d3aa23be0",
    "before": "llm",
    "after": {
      "id": "2729805ecae14d598b79090d3aa23be0",
      "status": "approved",
      "provenance": "llm_approved"
    },
    "name": "生产工厂"
  },
  "mcp_answers": [
    {
      "question": "褪黑素软糖用了哪些原料？",
      "matches": 5,
      "answer": [
        {
          "object": "褪黑素软糖（60 粒装）",
          "type": "product",
          "neighbors": [
            {
              "title": "柠檬酸",
              "type": "ingredient",
              "link": "contains_ingredient",
              "dir": "out"
            },
            {
              "title": "明胶",
              "type": "ingredient",
              "link": "contains_ingredient",
              "dir": "out"
            },
            {
              "title": "草莓浓缩汁",
              "type": "ingredient",
              "link": "contains_ingredient",
              "dir": "out"
            },
            {
              "title": "浅眠科技（深圳）有限公司",
              "type": "client",
              "link": "commissions",
              "dir": "in"
            },
            {
              "title": "康诺（湖州）生物科技有限公司",
              "type": "factory",
              "link": "manufactures",
              "dir": "in"
            },
            {
              "title": "阿美 Nutrition",
              "type": "influencer",
              "link": "promotes_product",
              "dir": "in"
            },
            {
              "title": "褪黑素",
              "type": "ingredient",
              "link": "contains_ingredient",
              "dir": "out"
            },
            {
              "title": "CV-2026-06",
              "type": "compliance_violation",
              "link": "has_compliance_violation",
              "dir": "out"
            },
            {
              "title": "ANC-2026-025",
              "type": "cooperation",
              "link": "covers_product",
              "dir": "in"
            },
            {
              "title": "SC-MEL-DY-03",
              "type": "script",
              "link": "applies_to",
              "dir": "in"
            },
            {
              "title": "SC-MEL-DY-01",
              "type": "script",
              "link": "applies_to",
              "dir": "in"
            },
            {
              "title": "ANC-2026-021",
              "type": "cooperation",
              "link": "covers_product",
              "dir": "in"
            },
            {
              "title": "SC-MEL-TT-02",
              "type": "script",
              "link": "applies_to",
              "dir": "in"
            },
            {
              "title": "LS-2026-0425",
              "type": "live_session",
              "link": "promotes",
              "dir": "in"
            },
            {
              "title": "睡眠研究所·老周",
              "type": "influencer",
              "link": "promotes_product",
              "dir": "in"
            },
            {
              "title": "LS-2026-0418",
              "type": "live_session",
              "link": "promotes",
              "dir": "in"
            },
            {
              "title": "HZ-20260312-A2",
              "type": "production_batch",
              "link": "belongs_to_product",
              "dir": "in"
            },
            {
              "title": "HZ-20260418-B1",
              "type": "production_batch",
              "link": "belongs_to_product",
              "dir": "in"
            }
          ]
        },
        {
          "object": "褪黑素",
          "type": "ingredient",
          "neighbors": [
            {
              "title": "褪黑素软糖（60 粒装）",
              "type": "product",
              "link": "contains_ingredient",
              "dir": "in"
            },
            {
              "title": "褪黑素软糖",
              "type": "product",
              "link": "contains_ingredient",
              "dir": "in"
            },
            {
              "title": "褪黑素软糖（美版）",
              "type": "product",
              "link": "contains_ingredient",
              "dir": "in"
            }
          ]
        },
        {
          "object": "褪黑素软糖",
          "type": "product",
          "neighbors": [
            {
              "title": "褪黑素软糖（抖音·老周）",
              "type": "compliance_script",
              "link": "has_compliance_script",
              "dir": "out"
            },
            {
              "title": "褪黑素",
              "type": "ingredient",
              "link": "contains_ingredient",
              "dir": "out"
            },
            {
              "title": "睡眠研究所·老周",
              "type": "influencer",
              "link": "promotes_product",
              "dir": "in"
            }
          ]
        }
      ]
    },
    {
      "question": "有哪些达人推广？",
      "matches": 5,
      "answer": [
        {
          "title": "阿美 Nutrition",
          "type": "influencer"
        },
        {
          "title": "LS-2026-0425",
          "type": "live_session"
        },
        {
          "title": "睡眠研究所·老周",
          "type": "influencer"
        },
        {
          "title": "LS-2026-0418",
          "type": "live_session"
        },
        {
          "title": "睡眠研究所·老周",
          "type": "influencer"
        }
      ]
    },
    {
      "question": "合规话术分级？",
      "matches": 0,
      "answer": []
    }
  ]
}
```