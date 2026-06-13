# 🤖 PROJECT CONTEXT: RAG_lawyer

## 🎯 Tổng quan dự án

Dự án phát triển một RAG_lawyer Agent tự trị (Autonomous Agent) có khả năng: phân tích vấn đề, lên kế hoạch để giải
quyết, tìm kiếm tài liệu luật liên quan trong vectore_store, sử dụng tài liệu kiếm được để giải quyết vấn đề.
Hệ thống được thiết kế theo hướng module hóa cao (Modular Architecture) để dễ dàng "plug-and-play" các LLM Providers
khác nhau và mở rộng bộ công cụ (Tools).

## 🛠 Tech Stack

- **Ngôn ngữ:** Python 3.12
- **LLM Framework:** LangChain, Deep Agent.
- **Web Framework:** FastAPI (Asynchronous).
- **LLM Abstraction:** `BaseChatModel` của LangChain.
- **Data & Validation:** Pydantic v2 (Bắt buộc dùng cho cấu trúc Schema của Tools).
- **Vector Store:** Qdrant
- **Environment:** Quản lý bằng `.env` (API Keys) và biến môi trường.
- **UI:** NEXT js

## 🏗 Kiến trúc & Nguyên tắc mở rộng (BẮT BUỘC)

### 1. Multi-Provider Support (Tính đa nền tảng)

- **Tách biệt Logic Model:** KHÔNG BAO GIỜ khởi tạo trực tiếp `ChatOpenAI`, `ChatAnthropic` hay `ChatGoogleGenerativeAI`
  trong code của Agent.
- **Sử dụng Factory Pattern:** Mọi LLM phải được khởi tạo qua một `LLMFactory`. Đầu vào chỉ là tên Provider (lấy từ
  config), đầu ra là một instance chuẩn hóa kế thừa từ `BaseChatModel`. Nhờ vậy, Agent chỉ giao tiếp với interface
  chung, không phụ thuộc vào nhà cung cấp.
- **Tool:** được tổ chức vào các file riêng và được triển khai theo adapter design pattern

### 2. Chia các chức năng thành các service, các service áp dụng singleton

### 3. Tổ chức thư mục (Folder Structure)

- `app/api/`: Chứa các router FastAPI.
- `app/core/agent/`: Chứa khởi tạo Deep agents.
- `app/core/model/`: Chứa `LLMFactory` và `EMBFactory` và các file setup cho từng Provider.
- `app/core/memory`: Chứa `CheckpointFactory` quản lý khởi tạo các checkpoint.
- `app/core/tool`: Chứa các tool được viết vào các file riêng
- `app/schemas/`: Định nghĩa Pydantic models.
- `app/storage`: Chứa các cấu hình kết nối các database
- `app/service`: Chứa các service.
- `app/config`: Chứa các cấu hình system prompt của agent chính và cấu hình cho các sub agent.

## 🧠 Nguyên tắc Coding dành cho AI Assistant (AI Instructions)

1. **Hướng đối tượng**: các thành phần đều được tổ chức theo các class, có thể áp dụng design pattern để tối ứng hệ
   thống
2. **Clean Code**: ưu tiên code rõ ràng, dễ bảo trì
3. **Chống lỗi**: khi giao tiếp vs các thành phần có ảnh hưởng từ bên ngoài (như: LLM, agent) thì dùng try expect để đảm
   bảo hệ thống luôn hoạt động ngay cả khi provider xảy ra lỗi
4. **API:** tuân thủ quy tắc restful api

## Nguyên tắc làm việc:

- Mặc định trả lời bằng tiếng việt 