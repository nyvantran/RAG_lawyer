from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.error_code import ErrorCode

class AppException(Exception):
    """
    AppException là ngoại lệ tùy chỉnh cho toàn bộ ứng dụng,
    chứa status_code (HTTP status), error_code (mã chi tiết) và message mô tả.
    """
    def __init__(self, status_code: int, error_code: ErrorCode, message: str = None):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        super().__init__(message)


def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handler xử lý AppException toàn cục cho FastAPI,
    trả về đúng cấu trúc JSON error response được quy định.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_code": exc.error_code.value if hasattr(exc.error_code, "value") else str(exc.error_code),
            "message": exc.message
        }
    )
