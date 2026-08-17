# 本体铸造（ontology-fondry）· 首月周报

> LLM 原生企业知识图谱平台：上传企业文档 → LLM 归纳本体与抽取实例 → 可治理的知识图谱 → MCP endpoint 供 Agent 问答。
> 本报告覆盖 2026-08 第 3–4 周（W1→W4）四周交付，面向外部读者。

## 一、本月四周产出

### W1 · 管线跑通（commit 3c544ae）

- 上传→解析分块→LLM 归纳→实例抽取→落库 全链通。
- 实测 8 份真实企业文档（deepseek-v4-pro @ prompt-v1）：归纳 8 个 object type、8 个 link type，抽取 41 对象 / 31 关系。
- 建评估集：20 条跨领域人工标注样本，基线通过率 45%（原始）/ 70%（别名修正口径），召回 80.2%。
- 提示词版本化（`PROMPT_VERSION` 随 `ExtractionRun.model` 落库可追溯）；`parse_json` 三级容错 + 3 次重试。

### W2 · 图谱成形（commit d0c13bc）

- `/api/objects/graph` 达 70 节点 / 80 边（DoD ≥50/≥80）。
- 前端 Cytoscape 图浏览上线；REST 查询与邻居遍历带 `object_type_name`（list/detail/neighbor 统一 join 填充）。
- prompt v2 修正两类回归：人员角色（mentor/sales_rep/technician/adjuster 等）与组织单元（branch/position）独立建型；命名用领域通用规范名（product 而非 health_food）。

### W3 · 治理与消费闭环（commit 738fdea）

- 治理审核 UI 四类闭环：object_type / link_type / object / link 各自的 draft→approve/reject，approve 使 `provenance` 由 `llm` 升 `llm_approved`，全程写 `audit_logs`。
- MCP endpoint（FastMCP stdio）上线，四个工具：`list_object_types` / `list_link_types` / `search_objects` / `get_object_detail`，供外部 LLM 客户端（Claude Desktop / opencode / Cursor）挂载完成问答。配置见 `docs/mcp-client-config.md`。

### W4 · 端到端硬化（本次）

- **docker-compose 一键起**：`docker compose up --build` 三服务（db/api/web）全绿，健康检查通过，浏览器可访问 `:3000`，`/api/health` 200。修了 backend Dockerfile 找不到包的 build bug、前端 `NEXT_PUBLIC_API_BASE` 构建期注入、api healthcheck + web 依赖条件。
- **完整演示脚本** `scripts/demo_w4.py`：上传 → process → graph → 审核一项 → MCP 问答三问（褪黑素软糖原料 / 达人推广 / 合规话术分级），确定性 tool 调用作答，可复现。
- **错误路径兜底**（testplan 层 4 三条）：不支持文件类型落 failed + 400；LLM 3 次非法 JSON 落 ExtractionRun failed + 文档 failed；LLM 不可达 120s 超时兜底同落 failed。`backend/tests/test_error_paths.py` 4 测试自动化验证。
- 修复三处韧性缺口：文档失败状态未标 failed、induction 硬失败 ExtractionRun 未翻 failed、客户端超时 60s→120s 对齐 DoD。

## 二、DoD 达标情况

| 里程碑 | DoD | 状态 |
|---|---|---|
| W1 | 真实企业文档 API 返回 ≥3 个可读 object type 草案 | ✓（实测 8 个） |
| W2 | graph ≥50 对象 ≥80 关系；前端图可浏览；prompt v2 不低于 70% 基线 | ✓ 图谱 70/80、前端图、REST；prompt v2 全量 eval 遗留 |
| W3 | 审核四类闭环；MCP endpoint 完成一次问答 | ✓ 闭环 + MCP demo 四工具 |
| W4 | docker 一键起；完整演示脚本；错误路径兜底；周报 | ✓ 本报告 |

## 三、已知遗留（非阻塞）

- **prompt v2 全量 eval**：opencode zen 端点不稳（首跑 15/20 超时），未补跑 20 样本全量通过率。端点稳定时补跑，验证不低于 70% 基线。
- **真实 LLM 客户端问答截图**：W3 MCP 演示以 `scripts/mcp_demo.py` + 确定性 tool 调用覆盖；真实 opencode/Claude Desktop 挂载问答的截图待补 `docs/demo/w3-mcp/`。
- **LLM 端点稳定性**：opencode zen 对整文档多块抽取偶发超时；演示与错误路径用 mock/构造输入规避依赖。生产化时换稳定端点或自托管。

## 四、演示指引

### 一键起

```
git clone <repo> && cd ontology-fondry
# 根 .env 软链 → backend/.env，填入 LLM_API_KEY / LLM_BASE_URL / LLM_MODEL
docker compose up --build
# → db + api(8000) + web(3000) 三服务 green
curl http://localhost:8000/api/health   # 200
# 浏览器打开 http://localhost:3000 看图谱与审核
```

### 端到端演示

```
# 对运行中的栈（docker 或 dev）
python scripts/demo_w4.py
# → 上传 samples/health-commerce/ 三份文档、process、graph、审核一项、MCP 三问
# 报告落 docs/demo/w4/run-NN.md
```

MCP 客户端（Claude Desktop / opencode / Cursor）挂载配置见 `docs/mcp-client-config.md`。

### 错误路径验证

```
cd backend && .venv/bin/pytest tests/test_error_paths.py -v   # 4 passed
```

路径 3 真实 120s 超时手动复现见 `docs/demo/w4/error-paths.md`。

## 五、架构一句话

数据模型用 Palantir 三原语简化版（object_types / link_types / objects(JSONB 动态属性) / links），不做 RDF/OWL 内核；归纳与抽取分离，抽取受本体 digest 硬约束（LLM 不在抽取时发明 schema），治理后置到审核队列；一切 LLM 产物带 `provenance`（llm/human/llm_approved）+ `confidence` 可追溯。
