"""业务错误模型。

错误码分段与契约《1.4 错误码》严格对应，前端按 code 分支处理，
因此这里的所有 code 都是硬约定，改动需要同步 packages/contracts 与前端 api/request.js。
"""

from __future__ import annotations

from typing import Any, ClassVar


class ErrorCode:
    """业务错误码常量。"""

    OK = 0

    # 4xxxx → 400 Bad Request
    BAD_REQUEST = 10001
    VALIDATION_FAILED = 10002

    # 2xxxx → 401 / 403
    UNAUTHORIZED = 20001
    TOKEN_EXPIRED = 20002
    TOKEN_INVALID = 20003
    FORBIDDEN = 20004

    # 3xxxx → 404 / 409
    NOT_FOUND = 30001
    CONFLICT = 30002

    # 4xxxx → 429
    RATE_LIMITED = 40001

    # 41xxx → 429（AI 额度）
    AI_QUOTA_EXHAUSTED = 41001

    # 42xxx → 422（状态机非法）
    CONSULT_STATE_INVALID = 42001

    # 5xxxx → 500
    INTERNAL_ERROR = 50000

    # 6xxxx → 503（下游不可用，本仓库自定义的扩展段）
    DOWNSTREAM_UNAVAILABLE = 60001
    DOWNSTREAM_TIMEOUT = 60002

    _HTTP_STATUS: ClassVar[dict[int, int]] = {
        OK: 200,
        BAD_REQUEST: 400,
        VALIDATION_FAILED: 400,
        UNAUTHORIZED: 401,
        TOKEN_EXPIRED: 401,
        TOKEN_INVALID: 401,
        FORBIDDEN: 403,
        NOT_FOUND: 404,
        CONFLICT: 409,
        RATE_LIMITED: 429,
        AI_QUOTA_EXHAUSTED: 429,
        CONSULT_STATE_INVALID: 422,
        INTERNAL_ERROR: 500,
        DOWNSTREAM_UNAVAILABLE: 503,
        DOWNSTREAM_TIMEOUT: 503,
    }

    @classmethod
    def http_status(cls, code: int) -> int:
        """按 code 段位推导 HTTP 状态码：万位段即 HTTP 段。"""
        return cls._HTTP_STATUS.get(code, cls._HTTP_STATUS[code // 10000 * 10000])


class AppError(Exception):
    """所有对外业务异常的基类。

    约定：message 里禁止出现堆栈、SQL、内网地址（契约 1.6.5）。
    """

    def __init__(
        self,
        code: int = ErrorCode.INTERNAL_ERROR,
        message: str = "服务繁忙，请稍后再试",
        *,
        status: int | None = None,
        data: Any = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status or ErrorCode.http_status(code)
        self.data = data

    def __repr__(self) -> str:  # pragma: no cover - 仅调试用
        return f"AppError(code={self.code}, message={self.message!r}, status={self.status})"

    # ── 常用构造糖 ────────────────────────────────────────────
    @classmethod
    def bad_request(cls, message: str = "请求参数错误") -> "AppError":
        return cls(ErrorCode.BAD_REQUEST, message)

    @classmethod
    def validation_failed(cls, details: list[dict[str, str]]) -> "AppError":
        """参数校验失败，details 形如 [{field: 'phone', issue: '格式不正确'}]。"""
        return cls(
            ErrorCode.VALIDATION_FAILED,
            "参数校验失败",
            data={"details": details},
        )

    @classmethod
    def unauthorized(cls, message: str = "请先登录") -> "AppError":
        return cls(ErrorCode.UNAUTHORIZED, message)

    @classmethod
    def token_expired(cls) -> "AppError":
        return cls(ErrorCode.TOKEN_EXPIRED, "登录已过期")

    @classmethod
    def forbidden(cls, message: str = "无权限访问") -> "AppError":
        return cls(ErrorCode.FORBIDDEN, message)

    @classmethod
    def not_found(cls, resource: str = "资源") -> "AppError":
        return cls(ErrorCode.NOT_FOUND, f"{resource}不存在")

    @classmethod
    def conflict(cls, message: str = "资源冲突") -> "AppError":
        return cls(ErrorCode.CONFLICT, message)

    @classmethod
    def ai_quota_exhausted(cls) -> "AppError":
        return cls(ErrorCode.AI_QUOTA_EXHAUSTED, "今日 AI 问诊额度已用尽，建议转诊真人医生")

    @classmethod
    def consult_state(cls, message: str = "当前问诊单状态不允许该操作") -> "AppError":
        return cls(ErrorCode.CONSULT_STATE_INVALID, message)

    @classmethod
    def downstream_unavailable(cls, service: str) -> "AppError":
        return cls(ErrorCode.DOWNSTREAM_UNAVAILABLE, f"{service} 服务暂不可用")

    @classmethod
    def downstream_timeout(cls, service: str) -> "AppError":
        return cls(ErrorCode.DOWNSTREAM_TIMEOUT, f"{service} 响应超时")
