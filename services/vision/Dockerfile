FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /uvx /bin/

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_CACHE_DIR=/tmp/uv-cache

COPY pyproject.toml README.md ./
COPY app ./app

ARG GPU=0
RUN if [ "$GPU" = "1" ]; then \
        uv pip uninstall --system onnxruntime 2>/dev/null || true; \
        uv pip install --system -e ".[gpu]" ; \
    else \
        uv pip install --system -e . ; \
    fi

# 权重以挂载方式提供（cv/artifacts:/app/artifacts:ro），这里只建占位目录
RUN mkdir -p /app/artifacts

EXPOSE 8081

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081"]
