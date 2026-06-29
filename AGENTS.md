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
- **Database:** Mongodb
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

1. **Agent Service** nhiệm vụ quản lý các agent của các người dùng, mỗi người dùng sẽ có 1 agent duy nhất. ngoài ra còn
   hỗ trợ stream câu trả lời của agent của user
2. **User service** quản lý tạo user
3. **Chat service** quản lý tạo, xóa và chat với agent

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
- `frontend`: Chứa giao diện UI 

### 4. API

1. API response trong trường hợp trường hợp response success:

- Các API thường, không yêu cầu phân trang(pagination) dữ liệu:

```json
{
  "success": "type(boolean)",
  "data": "type(any)",
  "message": "type(string) | none"
}
```

2. API response cho trường hợp response error:

```json
{
  "success": "type(boolean)",
  "error_code": "type(string)",
  "message": "type(string) | none"
}
```

- error_code là một chuỗi string thể hiện chi tiết lỗi(http status response chỉ là gom nhóm lỗi trong phạm vi nào,
  error_code sẽ cho biết cụ thể lỗi là gì)
- Danh sách các error_code(và http status của nó) ở backend/app/core/error_code.py
- Trường hợp lười catch lỗi quá thì display message trả về cho client

3. xác thực API thông qua bearer token, với access token có hiệu lực 5p, refresh token có hiệu lực 1 ngày

## 🧠 Nguyên tắc Coding dành cho AI Assistant (AI Instructions)

1. **Hướng đối tượng**: các thành phần đều được tổ chức theo các class, có thể áp dụng design pattern để tối ứng hệ
   thống
2. **Clean Code**: ưu tiên code rõ ràng, dễ bảo trì
3. **Chống lỗi**: khi giao tiếp vs các thành phần có ảnh hưởng từ bên ngoài (như: LLM, agent) thì dùng try expect để đảm
   bảo hệ thống luôn hoạt động ngay cả khi provider xảy ra lỗi
4. **API:** tuân thủ quy tắc restful api

## Nguyên tắc làm việc:

- Mặc định trả lời bằng tiếng việt 