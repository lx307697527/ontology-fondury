# W4 错误路径兜底（FEAT-001 testplan 层 4）

三条错误路径均已落地并自动化验证：`backend/tests/test_error_paths.py`（4 测试全绿）。
本文档记录机制与路径 3 真实 120s 超时的手动复现步骤（不脚本化，避免 120s×3 等待）。

## 机制（代码定位）

| 路径 | 触发 | 落库 | 代码 |
|---|---|---|---|
| 1 不支持的文件类型 | `parsing.extract_text` 抛 `ValueError` | `Document.status=failed` + `error`；`process` 据 `not raw_text` 返回 400 | `app/modules/api/documents.py`（upload except 分支）、`app/modules/services/parsing.py:extract_text` |
| 2 LLM 连续 3 次非法 JSON | `complete_json` 3 次重试后抛 `ValueError` | induction `ExtractionRun.status=failed`、`Document.status=failed`、错误串落 `doc.error` | `app/modules/services/llm.py:complete_json`、`app/modules/services/pipeline.py`（induction try 硬失败分支显式落 failed 再抛；外层 catch 兜底转 document failed） |
| 3 LLM 不可达 | OpenAI 客户端 `timeout=120s` + `max_retries=1` + `complete_json` 3 次循环 | `Document.status=failed` + 错误串 | `app/modules/services/llm.py`（`LLM.__init__` 客户端构造） |

## 自动化验证

```
cd backend && .venv/bin/pytest tests/test_error_paths.py -v
```

- `test_unsupported_file_type_lands_failed`：上传 `.xlsx` → 断言 `status==failed` + `error` 含"不支持的文件类型" + `POST /process` 返回 400。
- `test_three_illegal_json_lands_failed`：伪造 OpenAI 客户端恒返回非法 JSON → 断言 induction `ExtractionRun.status==failed` + `Document.status==failed` + `doc.error` 含 JSON。
- `test_llm_unreachable_lands_failed`：伪造客户端 `create` 抛连接异常 → 断言 `Document.status==failed` + `doc.error` 落串。
- `test_client_timeout_is_120s`：断言 `LLM().client.timeout == 120.0`（核对 DoD 的 120s 兜底数值）。

测试用独立 `fondry_test` 库隔离（`tests/conftest.py` 建库 + `drop_all/create_all`），不污染 dev 数据。

## 路径 3 真实 120s 超时 · 手动复现

自动化测试用伪造客户端即时模拟，不等待真实超时。如下手动复现可观察真实的 120s 超时兜底（约 120s×3≈6min，因 `complete_json` 3 次循环）：

1. db + api 在跑（`docker compose up` 或 dev uvicorn）。
2. 把 `backend/.env` 的 `LLM_BASE_URL` 指向一个**黑洞地址**（非 connection-refused，而是接受 TCP 但永不回包，触发超时而非即时失败），例如：
   ```
   LLM_BASE_URL=http://10.255.255.1:80/v1
   ```
   （`10.255.255.1` 是不可路由的占位 IP，TCP 连接挂起至超时。）
3. 上传一份 md：`curl -F file=@samples/health-commerce/konuo-product-compliance-handbook.md http://localhost:8000/api/documents`，取返回 `id`。
4. 触发 process：`curl -X POST http://localhost:8000/api/documents/<id>/process`。
5. 约 6 分钟后（3×120s + 退避）轮询 `GET /api/documents/<id>` → `status=failed`，`error` 含 `LLM 调用失败`/`timeout`。
6. 复现后把 `LLM_BASE_URL` 改回真实端点（`https://opencode.ai/zen/go/v1`）。

> 注：`max_retries=1` 使每次 attempt 最多 2 个请求（120s×2），3 次 attempt 最坏约 720s。这是有界的（防 SDK 默认 600s 无限叠加），演示与日常用 mock/构造输入规避此等待。
