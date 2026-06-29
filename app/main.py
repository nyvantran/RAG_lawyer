import os
from fastapi import FastAPI
from dotenv import load_dotenv

from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router
from app.core.exceptions import AppException, app_exception_handler

# Load biến môi trường
load_dotenv()

app = FastAPI(
    title="RAG Lawyer API",
    description="API hỗ trợ đăng nhập, đăng ký và dịch vụ RAG Lawyer Agent.",
    version="1.0.0"
)

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả các nguồn kết nối khi phát triển
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký custom exception handler để chuẩn hóa phản hồi lỗi
app.add_exception_handler(AppException, app_exception_handler)

# Đăng ký các router với prefix /api
app.include_router(api_router, prefix="/api")


@app.get("/")
def read_root():
    """
    Endpoint kiểm tra trạng thái hoạt động của server.
    """
    return {
        "success": True,
        "data": {
            "app": "RAG Lawyer API Server",
            "version": "1.0.0",
            "status": "healthy"
        },
        "message": "RAG Lawyer API Server đang hoạt động bình thường"
    }


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8000"))
    # Load và chạy uvicorn server
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
