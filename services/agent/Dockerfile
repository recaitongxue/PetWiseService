FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /uvx /bin/

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_CACHE_DIR=/tmp/uv-cache

COPY pyproject.toml README.md ./
COPY app ./app

# 默认只装 CPU 依赖；需要本地 embedding 时用 build-arg 打开
ARG EXTRAS=""
RUN if [ -z "$EXTRAS" ]; then \
        uv pip install --system -e . ; \
    else \
        uv pip install --system -e ".[${EXTRAS}]" ; \
    fi

# 语料随镜像分发，保证任何时候都能一键重建知识库
COPY knowledge_base ./knowledge_base

EXPOSE 8082

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8082"]
