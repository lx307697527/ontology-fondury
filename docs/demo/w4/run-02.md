## W4 端到端演示 · 2026-08-17 09:27:00
API: http://localhost:8000

### 1. 上传文档
  上传 konuo-influencer-script-ledger.md → id=744e06b1 status=parsed
  上传 konuo-product-compliance-handbook.md → id=db78641d status=parsed
  上传 konuo-quality-batch-traceability.md → id=418a58c9 status=parsed

### 2. process（live LLM 抽取一份）
  process 触发 id=db78641d，轮询中（至多 360s）…
  完成：status=parsed（361.8s）
  ⚠ 未在限期内 processed（LLM 端点不稳？），后续沿用既有图谱继续演示

### 3. 图谱快照
  graph：84 节点 / 93 边（DoD ≥70/≥80）✓

### 4. 治理审核
  审核 object_type「资质证书」provenance llm → llm_approved，status=approved，audit 已写

### 5. MCP Agent 问答三问
  Q1 褪黑素软糖用了哪些原料？ → 命中 6，首对象邻居 18 条
  Q2 有哪些达人推广？ → 命中 4 位
  Q3 合规话术分级？ → 命中 11 条话术，分级值 ['allowed', 'grayline', 'prohibited', 'prohibited', 'prohibited', 'grayline', 'allowed', 'allowed']

### 结果汇总
```json
{
  "uploaded": 3,
  "process": {
    "status": "parsed",
    "elapsed": 361.8
  },
  "graph": {
    "nodes": 84,
    "edges": 93
  },
  "review": {
    "id": "5a9ce1e57bcf4f3885beb14566c4952c",
    "before": "llm",
    "after": {
      "id": "5a9ce1e57bcf4f3885beb14566c4952c",
      "status": "approved",
      "provenance": "llm_approved"
    },
    "name": "资质证书"
  },
  "mcp_answers": [
    {
      "question": "褪黑素软糖用了哪些原料？",
      "matches": 6,
      "answer": [
        {
          "object": "褪黑素软糖（60 粒装）",
          "type": "product",
          "neighbors": [
            {
              "title": "康诺（湖州）生物科技有限公司",
              "type": "factory",
              "link": "manufactures",
              "dir": "in"
            },
            {
              "title": "明胶",
              "type": "ingredient",
              "link": "contains_ingredient",
              "dir": "out"
            },
            {
              "title": "柠檬酸",
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
          "object": "褪黑素软糖（60粒装）",
          "type": "product",
          "neighbors": [
            {
              "title": "康诺（湖州）生物科技有限公司",
              "type": "factory",
              "link": "manufactures",
              "dir": "in"
            },
            {
              "title": "浅眠科技（深圳）有限公司",
              "type": "client",
              "link": "commissions",
              "dir": "in"
            },
            {
              "title": "国食健注 G20240188",
              "type": "certificate",
              "link": "certified_by",
              "dir": "out"
            },
            {
              "title": "FDA注册（NDC 72812-003）",
              "type": "certificate",
              "link": "certified_by",
              "dir": "out"
            }
          ]
        }
      ]
    },
    {
      "question": "有哪些达人推广？",
      "matches": 4,
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
        }
      ]
    },
    {
      "question": "合规话术分级？",
      "matches": 11,
      "answer": [
        {
          "title": "有助于改善睡眠",
          "type": "compliance_script",
          "label": "合规话术脚本",
          "grade": "allowed",
          "review": "需产品有对应注册功能"
        },
        {
          "title": "比药物更安全",
          "type": "compliance_script",
          "label": "合规话术脚本",
          "grade": "grayline",
          "review": "需法务逐条审批后由指定达人使用"
        },
        {
          "title": "褪黑素软糖（抖音·老周）",
          "type": "compliance_script",
          "label": "合规话术脚本",
          "grade": "",
          "review": "家人们，这款软糖含有 2.8 毫克褪黑素，有助于改善睡眠，一天最多两粒，随餐或睡前食用……注意，本品不能代替药物，未成年人、孕妇不建议食用。"
        },
        {
          "title": "治疗失眠",
          "type": "compliance_script",
          "label": "合规话术脚本",
          "grade": "prohibited",
          "review": "任何情况下不得出现"
        },
        {
          "title": "根治高血脂",
          "type": "compliance_script",
          "label": "合规话术脚本",
          "grade": "prohibited",
          "review": "任何情况下不得出现"
        },
        {
          "title": "停药替代",
          "type": "compliance_script",
          "label": "合规话术脚本",
          "grade": "prohibited",
          "review": "任何情况下不得出现"
        },
        {
          "title": "SC-MEL-DY-03",
          "type": "script",
          "label": "话术脚本",
          "grade": "grayline",
          "review": "通过（限指定达人）"
        },
        {
          "title": "SC-MEL-DY-01",
          "type": "script",
          "label": "话术脚本",
          "grade": "allowed",
          "review": "通过"
        },
        {
          "title": "SC-MEL-TT-02",
          "type": "script",
          "label": "话术脚本",
          "grade": "allowed",
          "review": "通过（structure/function claim）"
        },
        {
          "title": "SC-OM3-DY-01",
          "type": "script",
          "label": "话术脚本",
          "grade": "allowed",
          "review": "通过"
        },
        {
          "title": "SC-PRO-KS-01",
          "type": "script",
          "label": "话术脚本",
          "grade": "allowed",
          "review": "通过"
        }
      ]
    }
  ]
}
```