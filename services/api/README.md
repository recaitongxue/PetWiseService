# Petwise API

Petwise 业务后端（FastAPI）。对外唯一网关与业务数据持有者，vision / agent 不直接面对客户端。

## 技术栈

- FastAPI + Uvicorn
- SQLAlchemy 2.0（同步 ORM）+ PyMySQL（本地 MySQL 9.7）
- Pydantic / Pydantic Settings
- JWT 鉴权（python-jose）

## 本地运行

```bash
# 依赖安装（uv）
uv sync

# 建库建表 + 种子数据（首次）
uv run python -m app.scripts.seed

# 启动
uv run uvicorn app.main:app --reload --port 8080
```

接口前缀 `/api/v1`，文档 `/docs`。数据库 DSN 通过 `PW_DATABASE_URL` 配置，本地默认
`mysql+pymysql://root:123456@127.0.0.1:3306/petwise`。
