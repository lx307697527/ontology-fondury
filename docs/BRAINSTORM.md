# 垂直行业头脑风暴：金融 · 零售带货 · 制造业

> 2026-08-15 · 基于 Palantir 官方博客/案例研究 + 项目已有定位（LLM 原生 KG 平台）

## 一、Palantir 的行业打法解码（对我们最重要的三条情报）

1. **平台不分行业，打法分行业**。Palantir 卖的永远是同一个 Ontology 平台，但用「前向部署工程师现场建本体」进入行业；跑通后再把行业打法固化成产品包（Warp Speed = 制造业包，Foundry for AML = 金融合规包）。**我们用「行业本体模板 + LLM 现场适配」替代他们的前向部署工程师——行业进入成本从几百万人天压到一次下载。**

2. **叙事是 decision-centric，不是 data-centric**。官方架构博客（Akshay Krishnaswamy, Chief Architect）的核心框架：每个决策 = Data（信息）+ Logic（评估）+ Action（执行）。Titan Industries 虚构案例演示了完整闭环：供应商断供 → 图谱导航到全部受影响订单 → 模拟在 scenario 沙箱暂存 → AI copilot 提议方案 → 人审 → 写回 ERP/WMS/生产系统 → decision lineage 沉淀为训练素材。**我们的骨架目前只有 Data，Logic（规则检查）和 Action（写回）是 Phase 2 的两张王牌。**

3. **Ursa Major 案例里藏着我们的直接同构验证**：他们的 Assembly & Testing Assistant「直接从工程图纸和 PDF 自动生成 digital workflows，省去数周人工配置」——这就是"LLM 从文档生成本体结构"在制造业的付费实证，年省 10,000-15,000 工程小时。我们做的事在 Palantir 生态里已被验证有价值，只是他们做成重服务，我们做成产品。

## 二、三大垂直逐一拆解

### 金融（银行/券商/消金）

| 维度 | 内容 |
|---|---|
| 典型本体 | Customer、Account、Transaction、Counterparty、FinancialProduct、Institution、Alert/Case、SanctionEntity、Device |
| 杀手场景 | ① AML 调查辅助：一笔可疑交易在图谱上展开 3-5 层资金链路（Palantir 实证：调查时间减半、真阳性率 40x、成本降 90%）② KYC/客户 360 ③ 投研知识层：研报/公告/监管文件 → KG → 多跳问答 ④ 信贷审查材料核验 |
| 付费方与周期 | 预算最足但销售周期 6-12 个月，POC 门槛高，普遍要求私有化部署 |
| 数据 | 交易流水（表格）、客户材料（文档）、研报公告（文档）、制裁名单（表格）——表格占比高 |
| 我们的契合点 | 监管要求可解释可审计 = provenance 徽章的天然市场；"这句话/这条结论来自哪份文件第几段"正是我们已有的 source_chunk 追溯 |
| 风险 | 无真实数据难做 demo；信任门槛最高；**不适合第一个滩头，适合有案例后进场的第二曲线** |

### 互联网零售带货（中国特色，Palantir 空白区）

| 维度 | 内容 |
|---|---|
| 典型本体 | Product/SKU、Brand、Category、Anchor(主播)、LiveRoom、Script(话术)、Violation(违规项)、Complaint(投诉)、Supplier、Ingredient(成分)、Certification(资质) |
| 杀手场景 | ① **直播合规审查**：话术脚本 vs 广告法/平台规则（绝对化用语、功效宣称、特殊品类限制）——广告法罚款 20-100 万，MCN 的真实出血点 ② 选品风控：商品 ↔ 成分 ↔ 曝光黑历史 ↔ 资质缺失关联过滤 ③ 商品知识图谱：搜索/推荐/智能客服的语义层 ④ 主播-商品匹配 |
| 付费方 | MCN 机构、品牌方电商团队、直播代运营、电商 SaaS 平台（嵌入） |
| 数据 | 商品详情页、成分表、直播脚本、平台规则文档——**几乎全公开，demo 数据当天可得** |
| 我们的契合点 | 中文生态壁垒（海外竞品不做）；数据全是文档型，LLM 管线零改造直接对口；合规结论必须可追溯（哪句话违反哪条规则）= provenance 模型的完美应用 |
| 风险 | 客单价偏低（SMB 为主），MCN 付费意愿需要验证——适合低价 SaaS/按次审查的产品形态 |

### 制造业

| 维度 | 内容 |
|---|---|
| 典型本体 | Equipment、WorkOrder、BOM、Part、ProcessRoute(工艺路线)、Supplier、QualityEvent、Defect、FaultCode、Manual(设备手册) |
| 杀手场景 | ① **设备维修知识库**：手册 PDF + 历史维修工单 → KG → 维修助手问答（= Ursa Major 的 Assembly & Testing Assistant 同构，已验证付费）② 质量追溯：缺陷 ↔ 批次 ↔ 供应商 ↔ 工艺参数的多跳下钻 ③ 供应链风险：Titan 案例的断供影响面分析 |
| 付费方 | 中型制造企业、集团多工厂；国内制造业数字化转型有政策与预算红利 |
| 数据 | 设备手册（PDF）、维修记录（Excel）、ERP 导出（表格）——文档+表格混合 |
| 我们的契合点 | 痛点极真实（老师傅退休、知识流失）；国内竞品（海致星图、明略）卖重型项目制，我们卖轻量 SaaS 是错位竞争 |
| 风险 | 表格数据导入必须做好；行业know-how深，单厂实施仍偏项目制 |

## 三、战略结论：一个内核 + 三个行业包

平台内核（已搭骨架）不随行业变化。行业差异全部落在四类**可复用资产**上：

1. **行业本体模板**：预置 object/link types YAML，LLM 在模板上适配扩展，而非每家从零归纳 → 平台需新增「模板加载器」（1-2 天工作量）
2. **行业提示词包**：垂直词汇表（如金融的对手方类型、带货的违禁词体系）注入归纳/抽取提示词
3. **行业评估集**：每行业 20 条人工金标准，度量抽取质量
4. **演示数据包**：公开数据组装的 end-to-end demo

行业共同要求的平台能力缺口（按优先级）：

- **P0 CSV/Excel 导入 + 列映射**：金融交易、维修工单、商品清单全是表格——目前只支持文档，这是三行业共同的硬缺口
- **P0 MCP endpoint**：滩头场景①（AI 应用知识层）的消费钩子
- **P1 合规规则检查器**：在图上跑规则（违禁词匹配、资质缺失告警）并输出带出处的报告——带货合规场景的核心交付物
- **P1 审计报告导出**：审查结论 + 溯源 + 时间戳的 PDF/JSON——金融与合规场景的交付物形态
- **P2 Action Types 写回**（Palantir 案例的"动词"，Phase 2 主菜）

## 四、推荐排序与 1 个月计划的衔接

**推荐：零售带货合规做第一旗舰 demo，制造业第二，金融第三（次年）。**

理由：数据可得性（当天能做出真 demo）× 中文壁垒（无海外竞品）× 痛点货币化明确（罚款金额摆着）× 与现有文档管线零改造。制造业等 CSV 导入做好即可切入（W3-W4 顺手做）；金融需要案例背书后进场。

**不推翻 1 个月计划**：行业包只是 W4 演示的「皮肤」。最小行业包 = 带货合规的 1 份本体模板 YAML + 20 条评估样本 + 1 套演示文档（话术脚本 + 平台规则 + 商品详情）。CSV 导入插入 W3（D 的任务扩展），合规规则检查器若 W4 来不及就用提示词实现 v0。

## 五、待决策

1. 三个行业中，团队是否有相关人脉/潜在客户？（比所有分析更值钱的滩头信号）
2. 带货合规的客户形态：直接卖 MCN（低价 SaaS）还是嵌入电商 SaaS 平台（分成）？
3. 制造业是否要并行准备一份 demo（维修助手），还是严格串行？

## 六、本体工程原则（来自 Palantir 社区 "Ontology and Pipeline Design Principles"，直接约束我们的模板与 API 设计）

1. **决策倒推设计**：先写"用户要做决策 X"，再检查/起草所需 objects——不是先建数据后找用途。"Ontology 是组织的 API，不是 datastore"。
2. **命名硬规则**（我们的行业模板直接采纳）：object 用自然语言业务概念命名；禁止版本化命名（`Message_v3`）和 `[tag]` 前缀；FK 统一 `{type}_id` 格式；`id` 必须是内在唯一的 string，不依赖运行时生成。
3. **成熟度状态**：每个 object type 配 Experimental/Active/Deprecated 状态 + 具名负责人——我们已有 status + 审核流，补一个 owner 字段即可对齐。
4. **图形态检查**：孤立 object 是坏设计信号，但也要避免"蛛网"——抽取管线的评估指标里应加这两条。
5. **项目分层**：数据源层 → 整合层 → 本体层 → 应用层 → 沙箱，权限按层收口——多租户（Phase 2+）的权限模型照此设计。

## 参考来源

- Palantir Blog: Connecting AI to Decisions with the Palantir Ontology（Chief Architect，Titan Industries 案例）
- Ursa Major × Palantir Warp Speed 制造案例
- Palantir Foundry for AML / Financial Services 方案页
- Palantir Foundry for Retail（缺货率 3 个月降 20%+ 案例）、Consumer Goods 方案页
- Palantir Docs: Ontology Overview / Ontology Architecture / AIP Tools
