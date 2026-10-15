"""应用配置。

所有敏感项走环境变量（前缀 PW_），本地用 .env，容器用 compose 注入。
禁止把任何默认值写成真实密钥。
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PW_",
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── 应用 ──────────────────────────────────────────────
    APP_NAME: str = "petwise-api"
    ENV: str = Field(default="dev", description="dev | staging | prod")
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = False

    # ── 数据库 / 缓存 ────────────────────────────────────
    DATABASE_URL: str = "mysql+pymysql://root:123456@127.0.0.1:3306/petwise"
    DB_POOL_SIZE: int = 10
    DB_ECHO: bool = False
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── 鉴权 ──────────────────────────────────────────────
    JWT_SECRET: str = Field(default="change-me-in-production", min_length=8)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_TTL: int = 7200
    REFRESH_TOKEN_TTL: int = 30 * 24 * 3600

    # ── 内部服务调用 ──────────────────────────────────────
    VISION_BASE_URL: str = "http://localhost:8081"
    AGENT_BASE_URL: str = "http://localhost:8082"
    INTERNAL_TOKEN: str = "internal-token-change-me"

    # AI 链路给的时间预算：超过即降级，绝不拖垮主链路
    VISION_TIMEOUT: float = 3.0
    AGENT_TIMEOUT: float = 30.0
    AGENT_STREAM_TIMEOUT: float = 90.0

    # ── 对象存储 ──────────────────────────────────────────
    STORAGE_ENDPOINT: str = "localhost:9000"
    STORAGE_ACCESS_KEY: str = "petwise"
    STORAGE_SECRET_KEY: str = "petwise123"
    STORAGE_BUCKET: str = "petwise"
    STORAGE_SECURE: bool = False
    STORAGE_PUBLIC_BASE: str = "http://localhost:9000/petwise"

    # ── AI 配额 ───────────────────────────────────────────
    AI_DAILY_TRIAGE_QUOTA: int = 5

    # ── 本地演示 ──────────────────────────────────────────
    # 开启后短信验证码登录允许使用固定调试码（见 auth 路由），生产必须关闭
    SMS_DEBUG: bool = False

    # ── CORS ──────────────────────────────────────────────
    CORS_ORIGINS: str = "*"

    @property
    def is_prod(self) -> bool:
        return self.ENV.lower() == "prod"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
