# ⚖️ RAG Lawyer AI Agent

Hệ thống **RAG Lawyer** là một AI Agent tự trị (Autonomous Agent) hỗ trợ tư vấn Luật Lao Động tại Việt Nam. Hệ thống có khả năng phân tích câu hỏi của người dùng, tự động lập kế hoạch, tìm kiếm điều luật liên quan trong cơ sở dữ liệu Vector Qdrant, thực hiện reranking (tái xếp hạng tài liệu) và sử dụng LLM để đưa ra câu trả lời tư vấn pháp lý chính xác, có dẫn nguồn rõ ràng.

Dự án được thiết kế theo kiến trúc module hóa cao (Modular Architecture), sử dụng **Factory Pattern** cho LLM và Embedding nhằm dễ dàng thay thế các nhà cung cấp dịch vụ AI (OpenAI, Google Gemini, Anthropic Claude) và chạy hoàn toàn trên môi trường Docker.

---

## 🛠️ Tech Stack

* **Backend:** Python 3.12, FastAPI (Async), LangChain, LangGraph, DeepAgent.
* **Frontend:** Next.js (App Router), React, CSS Modules.
* **Vector Database:** Qdrant (Lưu trữ và tìm kiếm vector ngữ nghĩa).
* **Database:** MongoDB (Quản lý thông tin người dùng, lịch sử chat và các trạng thái checkpoint của Agent).
* **Package Manager:** [uv](https://github.com/astral-sh/uv) (Astral) & `pyproject.toml`.

---

## 📂 Cấu trúc thư mục chính

```text
├── app/                  # Mã nguồn Backend (FastAPI)
│   ├── api/              # Các router API (Auth, Chat,...)
│   ├── core/             # Logic cốt lõi (Agent, LLM/EMB Factory, Tools...)
│   │   ├── tool/         # Các công cụ của Agent (Vector Search, Reranking...)
│   │   └── model/        # Cấu hình các nhà cung cấp LLM
│   ├── schemas/          # Pydantic Models để validate dữ liệu
│   ├── service/          # Các dịch vụ xử lý logic (User, Chat, Agent Service)
│   └── storage/          # Kết nối Database (MongoDB, Qdrant)
├── frontend/             # Mã nguồn Frontend (Next.js)
├── notebook/             # Thư mục chứa các file Jupyter Notebook nghiên cứu
├── data/                 # Thư mục chứa dữ liệu Luật Lao Động dạng JSON
├── scripts/              # Các script bổ trợ (như script chuẩn bị dữ liệu Qdrant)
├── Makefile              # File tự động hóa các tác vụ bằng công cụ Make
├── docker-compose.yml    # Cấu hình Docker Compose (mặc định CPU)
├── docker-compose.gpu.yml# Cấu hình đè Docker Compose dành cho GPU (CUDA)
└── pyproject.toml        # File quản lý thư viện dự án bằng UV
```

---

## ⚙️ Yêu cầu hệ thống

Trước khi bắt đầu, hãy đảm bảo máy tính của bạn đã cài đặt các công cụ sau:
1. **Docker** & **Docker Compose** (phiên bản mới nhất).
2. Công cụ **`make`** (đã được cài đặt sẵn trên Linux/macOS. Trên Windows, bạn có thể cài đặt thông qua *Chocolatey*, *Scoop*, hoặc sử dụng *Git Bash* / *MSYS2*).
3. **NVIDIA Driver** & **NVIDIA Container Toolkit** (chỉ yêu cầu nếu bạn muốn chạy hệ thống bằng card đồ họa GPU/CUDA).

---

## 🚀 Hướng dẫn khởi chạy bằng công cụ `make`

### Bước 1: Thiết lập biến môi trường
Sao chép file `.env.example` thành `.env` ở thư mục gốc:
```bash
cp .env.example .env
```

Mở file `.env` vừa tạo và cập nhật các cấu hình API Key cũng như thông tin dịch vụ tương ứng:

#### 🔑 Các API Key cần cấu hình:
1. **LLM Providers (Dành cho Agent xử lý & trả lời):**
   * `GOOGLE_API_KEY`: API Key của Google Gemini (mặc định là `models/gemma-4-31b-it`).
   * `OPENAI_API_KEY`: API Key của OpenAI (nếu cấu hình sử dụng GPT).
   * `ANTHROPIC_API_KEY`: API Key của Anthropic Claude (nếu cấu hình sử dụng Claude).

2. **Reranking Providers (Dành cho việc tái xếp hạng tài liệu):**
   * Hệ thống hỗ trợ 2 nhà cung cấp rerank qua biến `DEFAULT_RERANK_PROVIDER`:
     * `huggingface` (Mặc định): Chạy mô hình cục bộ (ví dụ: `namdp-ptit/ViRanker`). **Không yêu cầu API Key**.
     * `cohere`: Sử dụng dịch vụ API của Cohere. **Yêu cầu cấu hình thêm**:
       * `DEFAULT_RERANK_PROVIDER=cohere`
       * `COHERE_API_KEY`: API Key của dịch vụ Cohere.
       * `COHERE_RERANK_MODEL`: Tên mô hình sử dụng (mặc định là `rerank-v4.0-pro`).

### Bước 2: Khởi chạy các container Docker
Tùy thuộc vào cấu hình phần cứng máy tính của bạn, chọn một trong hai lệnh sau:

* **Chạy trên máy KHÔNG có card đồ họa (Sử dụng CPU):**
  ```bash
  make up
  ```

* **Chạy trên máy CÓ card đồ họa NVIDIA (Sử dụng GPU/CUDA):**
  ```bash
  make up-gpu
  ```

*Lệnh này sẽ tải và khởi dựng 4 container: `rag_lawyer_mongodb`, `rag_lawyer_qdrant`, `rag_lawyer_backend`, và `rag_lawyer_frontend` ở chế độ chạy ngầm (background).*

### Bước 3: Chuẩn bị dữ liệu Vector Store cho Qdrant
Sau khi các container đã khởi chạy thành công, bạn cần nạp dữ liệu luật lao động từ thư mục `data/` vào Qdrant. 

* **Nạp dữ liệu (tự động tạo collection mới nếu chưa có):**
  ```bash
  make prepare-qdrant
  ```

* **Xóa sạch dữ liệu cũ và nạp lại từ đầu (Khuyên dùng trong lần chạy đầu tiên):**
  ```bash
  make prepare-qdrant-clean
  ```

*(Lưu ý: Lệnh này sẽ thực thi script Python trực tiếp bên trong môi trường container `backend` nên bạn không cần cài đặt Python hay thư viện nào ở máy host).*

---

## 📊 Địa chỉ truy cập dịch vụ

Sau khi hoàn tất các bước trên, bạn có thể truy cập các địa chỉ sau trên trình duyệt:

| Dịch vụ | URL truy cập | Mô tả |
| :--- | :--- | :--- |
| **Frontend** | `http://localhost:3000` | Giao diện Chat tư vấn Luật của RAG Lawyer |
| **Backend API** | `http://localhost:8000/docs` | Swagger UI để kiểm tra và test các API của Backend |
| **Qdrant Dashboard** | `http://localhost:6333/dashboard` | Trang quản trị trực quan của cơ sở dữ liệu Vector Qdrant |

---

## 🛠️ Các lệnh quản trị khác trong `Makefile`

Bạn có thể sử dụng các lệnh sau để quản lý hệ thống thuận tiện hơn:

* **Xem log của tất cả các container:**
  ```bash
  make logs
  ```
* **Xem log riêng của Backend:**
  ```bash
  make logs-backend
  ```
* **Xem log riêng của Frontend:**
  ```bash
  make logs-frontend
  ```
* **Dừng và giải phóng toàn bộ tài nguyên container:**
  ```bash
  make down
  ```
* **Build lại toàn bộ Docker images (CPU):**
  ```bash
  make build
  ```
* **Build lại toàn bộ Docker images (GPU):**
  ```bash
  make build-gpu
  ```
* **Khởi động lại toàn bộ hệ thống (CPU):**
  ```bash
  make restart
  ```
* **Khởi động lại toàn bộ hệ thống (GPU):**
  ```bash
  make restart-gpu
  ```

Để xem lại danh sách các lệnh bất cứ lúc nào, bạn chỉ cần gõ:
```bash
make help
```
