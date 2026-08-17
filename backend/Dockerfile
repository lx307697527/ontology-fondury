FROM python:3.12-slim
WORKDIR /app
# pyproject 用 setuptools.packages.find(include=["app*"])，装包时 app/ 源必须在场
# （历史 bug：仅拷 pyproject 就 pip install . → 找不到 app 包，build 失败）
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir .
# 运行期无需reload；建表/迁移在 main.py startup create_all + run_legacy_migrations 完成
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
