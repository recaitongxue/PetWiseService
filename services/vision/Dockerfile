FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

COPY pyproject.toml README.md ./
COPY app ./app

ARG GPU=0
RUN if [ "$GPU" = "1" ]; then \
        pip uninstall -y onnxruntime 2>/dev/null || true; \
        pip install -e ".[gpu]" ; \
    else \
        pip install -e . ; \
    fi

# 权重以挂载方式提供（cv/artifacts:/app/artifacts:ro），这里只建占位目录
RUN mkdir -p /app/artifacts

EXPOSE 8081

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081"]
