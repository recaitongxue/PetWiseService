"""问诊智能体服务配置。

LLM 相关的密钥一律走环境变量，禁止默认值写入真实凭据。
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PW_AGENT_",
        env_file=(".env", ".env.local"),
        extra="ignore",
    )

    APP_NAME: str = "petwise-agent"
    ENV: str = "dev"
    HOST: str = "0.0.0.0"
    PORT: int = 8082
    LOG_LEVEL: str = "INFO"

    # 服务间鉴权，与 api 服务共享
    INTERNAL_TOKEN: str = "please-change-internal-token"

    # ── 数据库（知识库与会话记忆） ─────────────────────────
    DATABASE_URL: str = "postgresql+psycopg://petwise:petwise@localhost:5432/petwise"
    REDIS_URL: str = "redis://localhost:6379/1"

    # pgvector 检索参数
    KB_SCHEMA: str = "public"
    EMBEDDING_DIM: int = 768
    RETRIEVAL_TOP_K: int = 6
    RETRIEVAL_CANDIDATES: int = 30     # 混合检索的粗召回数量
    SIMILARITY_THRESHOLD: float = 0.30  # 低于该分数的片段视为无关
    VECTOR_WEIGHT: float = 0.7          # 混合检索里向量的权重
    KEYWORD_WEIGHT: float = 0.3

    # 重排策略：heuristic（零依赖）| cross-encoder（需额外模型）
    RERANK_STRATEGY: str = "heuristic"
    # 同一篇文档最多返回几段，避免上下文被单篇文章占满
    MAX_CHUNKS_PER_DOC: int = 2

    # ── Embedding 提供者 ─────────────────────────────────────
    # hash    : 零依赖本地兜底（仅用于跑通链路，语义质量差，禁止用于论文评测）
    # local   : sentence-transformers 加载本地中文模型（推荐离线环境）
    # openai  : 任意 OpenAI 兼容的 embedding 端点
    EMBEDDING_PROVIDER: str = "hash"
    EMBEDDING_MODEL: str = "BAAI/bge-small-zh-v1.5"
    EMBEDDING_BASE_URL: str = "https://api.openai.com/v1"
    EMBEDDING_API_KEY: str = ""

    # ── 大语言模型 ──────────────────────────────────────────
    LLM_PROVIDER: str = "openai"        # openai | anthropic | ollama | mock
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_API_KEY: str = ""
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 1600
    LLM_TIMEOUT: float = 45.0

    # JSON 输出校验失败时的重试次数
    LLM_JSON_RETRIES: int = 2

    # ── 知识库语料 ──────────────────────────────────────────
    # parents: [0]=app  [1]=agent  → services/agent/knowledge_base
    KB_CORPUS_DIR: Path = Field(
        default=Path(__file__).resolve().parents[1] / "knowledge_base"
    )
    CHUNK_SIZE: int = 380
    CHUNK_OVERLAP: int = 60

    # ── 安全边界 ────────────────────────────────────────────
    # 出现这些词时不给出具体用药建议，直接导向线下就诊
    PRESCRIPTION_ENABLED: bool = False
    DISCLAIMER: str = "AI 建议仅供参考，不能替代执业兽医的面诊与处方。"

    @property
    def mock_mode(self) -> bool:
        """未配置密钥时进入 mock：链路可跑通，但输出来自规则而非 LLM。"""
        return self.LLM_PROVIDER == "mock" or not self.LLM_API_KEY


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
