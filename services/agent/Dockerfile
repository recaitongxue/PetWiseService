FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

COPY pyproject.toml README.md ./
COPY app ./app

# 默认只装 CPU 依赖；需要本地 embedding 时用 build-arg 打开
ARG EXTRAS=""
RUN if [ -z "$EXTRAS" ]; then \
        pip install -e . ; \
    else \
        pip install -e ".[$EXTRAS]" ; \
    fi

# 语料随镜像分发，保证任何时候都能一键重建知识库
COPY knowledge_base ./knowledge_base

EXPOSE 8082

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8082"]
