# Sử dụng Python 3.12-slim làm base image để tối ưu dung lượng
FROM python:3.12-slim

# Thiết lập các biến môi trường cần thiết
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/workspace/.cache/huggingface

# Sao chép trình quản lý thư viện UV từ image chính thức của Astral
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Cài đặt các thư viện hệ thống cần thiết (như git để cài đặt các gói git, build-essential cho C++ extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Sao chép pyproject.toml từ thư mục gốc vào container
COPY pyproject.toml .

# Khai báo build-arg DEVICE (mặc định là cpu, có thể truyền cuda)
ARG DEVICE=cpu

# Cài đặt trước phiên bản PyTorch phù hợp với thiết bị đích sử dụng UV
# Sử dụng tùy chọn --system của uv để cài đặt thẳng vào môi trường Python hệ thống của container
RUN if [ "$DEVICE" = "cuda" ] ; then \
        uv pip install --system --no-cache torch --extra-index-url https://download.pytorch.org/whl/cu121 ; \
    else \
        uv pip install --system --no-cache torch --extra-index-url https://download.pytorch.org/whl/cpu ; \
    fi

# Cài đặt các thư viện còn lại khai báo trong pyproject.toml bằng UV
# Lệnh này sẽ bỏ qua cài đặt lại torch vì phiên bản phù hợp đã được cài đặt ở bước trên
RUN uv pip install --system --no-cache -r pyproject.toml

# Sao chép toàn bộ mã nguồn backend vào container
COPY . .

# Expose port của backend (FastAPI mặc định chạy trên port 8000)
EXPOSE 8000

# Lệnh khởi chạy ứng dụng FastAPI bằng uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
