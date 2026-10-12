"""推理服务配置。

与主后端的区别：这里关心<｜hy_place▁holder▁no▁813｜>与否可用即可，因此依赖非常轻（onnxruntime + numpy + pillow），
不含 torch —— 训练侧的依赖不应出现在生产镜像里。
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PW_VISION_",
        env_file=(".env", ".env.local"),
        extra="ignore",
    )

    APP_NAME: str = "petwise-vision"
    ENV: str = "dev"
    HOST: str = "0.0.0.0"
    PORT: int = 8081
    LOG_LEVEL: str = "INFO"

    # 服务间鉴权：与主后端共享同一个 INTERNAL_TOKEN
    INTERNAL_TOKEN: str = "please-change-internal-token"

    # 权重与标签所在目录，容器里通常挂载 cv/artifacts（只读）
    # parents: [0]=app  [1]=vision  → services/vision/artifacts
    ARTIFACTS_DIR: Path = Field(default=Path(__file__).resolve().parents[1] / "artifacts")

    # 模型注册表文件：描述有哪些模型、对应哪个 kind、版本号
    MANIFEST_FILE: str = "manifest.json"

    # 推理参数
    IMAGE_SIZE: int = 224
    TOP_K: int = 3
    MAX_IMAGE_MB: int = 10

    # 置信度分级阈值：低于 low 视为无法确认品种
    CONF_HIGH: float = 0.85
    CONF_LOW: float = 0.45

    # 拒识阈值：top-1 置信度低于此值直接返回「未识别到犬种」，而非强行给某个狗种。
    # 本模型只训练了犬种（无猫/其它宠物的负样本），低置信多为拍到非犬、角度/光线差或模糊图，
    # 强行输出狗种会损害「宠物识别」的可信度。0.5 为经验起点，可按验证集分布微调。
    REJECT_THRESHOLD: float = 0.5

    # 执行后端：CUDA 可用时自动优先
    PROVIDERS: str = "auto"  # auto | cpu | cuda

    @property
    def max_image_bytes(self) -> int:
        return self.MAX_IMAGE_MB * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
