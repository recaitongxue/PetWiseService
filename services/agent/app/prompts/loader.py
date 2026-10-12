"""提示词版本化管理。

为什么不用硬编码字符串：
1. 提示词是**会持续调整的资产**，散落在业务代码里无法做版本对比与回滚；
2. 评测时需要固定"哪一版提示词 + 哪一版知识库"，必须可寻址；
3. 把 variables 显式声明出来，能避免不小心把未清洗的用户输入拼进 system 指令。

模板使用 Jinja2；如未安装该依赖，退化为简单的 str.format 替换，
保证最小化环境下服务仍能启动。
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

_PROMPT_ROOT = Path(__file__).parent


def available_versions() -> list[str]:
    return sorted(p.name for p in _PROMPT_ROOT.iterdir() if p.is_dir() and p.name.startswith("v"))


def _render(template: str, variables: dict[str, object]) -> str:
    try:
        from jinja2 import Template  # 惰性导入
    except ImportError:
        # 降级：仅替换 {{ var }}，不支持循环/条件
        rendered = template
        for key, value in variables.items():
            rendered = rendered.replace("{{ " + key + " }}", str(value))
        rendered = rendered.replace("{% raw %}", "").replace("{% endraw %}", "")
        return rendered

    return Template(template).render(**variables)


@lru_cache(maxsize=64)
def _read(version: str, name: str) -> str:
    path = _PROMPT_ROOT / version / f"{name}.j2"
    if not path.is_file():
        raise FileNotFoundError(f"提示词文件不存在: {path}")
    return path.read_text(encoding="utf-8")


def load(name: str, *, version: str = "v1") -> str:
    """读取原始模板。"""
    return _read(version, name)


def render(name: str, variables: dict[str, object], *, version: str = "v1") -> str:
    """渲染指定提示词。"""
    return _render(load(name, version=version), variables)
