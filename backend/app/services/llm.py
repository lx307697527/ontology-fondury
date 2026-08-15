import json
from json import JSONDecodeError

from openai import OpenAI

from app.config import get_settings

_JSON_ONLY = "只输出一个合法的 JSON 对象，不要包含 markdown 代码块或任何其他文字。Output only one valid JSON object, no markdown fences, no prose."

# 提示词版本化：改提示词必须递增版本号，随 ExtractionRun.model 落库（如 gpt-4o-mini@prompt-v1）
PROMPT_VERSION = "v1"

INDUCTION_SYSTEM = f"""你是一位企业本体（ontology）架构师，风格参照 Palantir Foundry 的建模方法：以业务运营为中心，而不是照搬源系统的表结构。

任务：阅读企业文档片段，归纳出支撑业务运营所需的核心 object types（业务"名词"）和 link types（业务关系）。

要求：
- object type：name 用 snake_case 英文标识；display_name 和 description 用文档语言；每个类型最多 8 个属性（name/ display_name/ dtype/ description），dtype 取 string/number/date/boolean 之一；必须含一个能唯一定位实例的 title 属性语义。
- link type：name 用 snake_case 动词短语（如 works_for / belongs_to / supplies）；source/target 用上面定义的 object type 的 name；cardinality 取 one_to_one/one_to_many/many_to_many。
- 克制建模：只提出文档中反复出现、对业务运营有决策价值的概念，宁缺毋滥，总数控制在 3~10 个 object types。
- {_JSON_ONLY}

输出格式：
{{"object_types": [{{"name": str, "display_name": str, "description": str, "properties": [{{"name": str, "display_name": str, "dtype": str, "description": str}}]}}], "link_types": [{{"name": str, "display_name": str, "description": str, "source": str, "target": str, "cardinality": str}}]}}"""

EXTRACTION_SYSTEM = f"""你是知识图谱抽取引擎。给定已定义的本体（object types 与 link types）和一段文档，抽取实例。

硬性规则：
- 只允许使用给定本体中的类型和关系，禁止发明新类型；无法归入的内容直接丢弃。
- 每个对象给 title（用文档原文中的名称，保留原语言）与 properties（只填本类型已定义的属性，文档未提及的属性留空字符串）。
- link 的 source/target 用本批抽取出的对象 title 精确匹配；两个 title 必须都已出现在 objects 列表中。
- 严格忠于原文，不要推断文档没有的事实；每项给 0~1 的 confidence。
- {_JSON_ONLY}

输出格式：
{{"objects": [{{"type": str, "title": str, "properties": {{str: str}}, "confidence": float}}], "links": [{{"source_title": str, "link_type": str, "target_title": str, "confidence": float}}]}}"""


class LLM:
    def __init__(self) -> None:
        s = get_settings()
        self.model = s.llm_model
        self.model_label = f"{s.llm_model}@prompt-{PROMPT_VERSION}"
        # 显式超时：SDK 默认 600s × 内置重试叠加 complete_json 的 3 次重试会拖死管线
        self.client = OpenAI(base_url=s.llm_base_url, api_key=s.llm_api_key, timeout=120.0, max_retries=1)

    def complete_json(self, system: str, user: str) -> dict:
        # 推理型/小参数模型偶发包裹代码块或夹杂文字，解析失败时带错误信息重试
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        last_error = ""
        for _ in range(3):
            resp = self.client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                messages=messages,
            )
            content = resp.choices[0].message.content or ""
            try:
                return parse_json(content)
            except JSONDecodeError as e:
                last_error = f"{e}（原文开头：{content[:120]!r}）"
                messages.append({"role": "assistant", "content": content})
                messages.append(
                    {"role": "user", "content": f"上一条输出不是合法 JSON：{last_error}。请严格只输出一个合法的 JSON 对象。"}
                )
        raise ValueError(f"LLM 连续 3 次未能输出合法 JSON：{last_error}")

    def induce_schema(self, sample_chunks: list[str]) -> dict:
        samples = "\n\n---\n\n".join(f"【片段 {i + 1}】\n{c}" for i, c in enumerate(sample_chunks))
        return self.complete_json(INDUCTION_SYSTEM, f"以下是同一批企业文档的抽样片段：\n\n{samples}")

    def extract_instances(self, chunk: str, schema_digest: str) -> dict:
        return self.complete_json(
            EXTRACTION_SYSTEM,
            f"已定义本体：\n{schema_digest}\n\n待抽取的文档片段：\n{chunk}",
        )


def parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()
    try:
        return json.loads(text)
    except JSONDecodeError:
        # 兜底：截取首个配平的花括号块，容忍前后夹杂的说明文字
        start = text.find("{")
        if start == -1:
            raise
        depth, in_string, escaped = 0, False, False
        for i in range(start, len(text)):
            ch = text[i]
            if in_string:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_string = False
                continue
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(text[start : i + 1])
        raise
