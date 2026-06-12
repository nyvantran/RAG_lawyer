# 🤖 PROJECT CONTEXT: RAG_lawyer

## 🎯 Tổng quan dự án

Dự án phát triển một RAG_lawyer Agent tự trị (Autonomous Agent) có khả năng: .
Hệ thống được thiết kế theo hướng module hóa cao (Modular Architecture) để dễ dàng "plug-and-play" các LLM Providers
khác nhau và mở rộng bộ công cụ (Tools).

## 🛠 Tech Stack

- **Ngôn ngữ:** Python 3.11+
- **Core Framework:** LangChain, Deep Agent.
- **LLM Abstraction:** `BaseChatModel` của LangChain.
- **Data & Validation:** Pydantic v2 (Bắt buộc dùng cho cấu trúc Schema của Tools).
- **Environment:** Quản lý bằng `.env` (API Keys) và biến môi trường.
- **UI:** sử dụng thư viện Rich để tạo giao diện chat

## 🏗 Kiến trúc & Nguyên tắc mở rộng (BẮT BUỘC)

### 1. Multi-Provider Support (Tính đa nền tảng)

- **Tách biệt Logic Model:** KHÔNG BAO GIỜ khởi tạo trực tiếp `ChatOpenAI`, `ChatAnthropic` hay `ChatGoogleGenerativeAI`
  trong code của Agent.
- **Sử dụng Factory Pattern:** Mọi LLM phải được khởi tạo qua một `LLMFactory`. Đầu vào chỉ là tên Provider (lấy từ
  config), đầu ra là một instance chuẩn hóa kế thừa từ `BaseChatModel`.
- Nhờ vậy, Agent chỉ giao tiếp với interface chung, không phụ thuộc vào nhà cung cấp.

### 2. Chia các chức năng thành các service, các service áp dụng singleton

- **ChatService**: Quản lý việc tạo hội thoại chat với agent của ConfigService, xử lý các ngắt human_in_the_loop của
  agent, xử lý stream luồng suy nghĩ của agent thông qua phương thức stream của agent 
- **ConfigService**: Quản lý việc thay đổi api key, provider, model. Quản lý agent

### 3. Giao diện CLI (UI CLI)

- **Software Architecture**: UI được tổ chức theo mô hình MVC
- **Feature**:
    1. khi stream luồng suy nghĩ của agent thì mỗi loại message sẽ có màu riêng
    2. mỗi khi có Humman_in_the_loop thì hiển thị cách chọn approve hay reject
    3. các message tool call thì phải hiển thì tool nào được gọi và một số thuộc tính của nó
    4. có thể ngắt luồng suy nghĩ bằng ctrl+c

### 4. Tổ chức thư mục (Folder Structure)

- `app/core/agent/`: Chứa khởi tạo Deep agents.
- `app/core/llm/`: Chứa `LLMFactory` và các file setup cho từng Provider.
- `app/core/checkpoint`: Chứa `CheckpointFactory` quản lý khởi tạo các checkpoint
- `app/service`: Chứa các service
- `ui/controllers`: Chứa `ChatController` Đóng vai trò điều phối thông tin giữa Model (trạng thái hệ thống) và View (
  giao diện Rich).
- `ui/models`: Chứa `ChatModel` Chịu trách nhiệm lưu trữ và quản lý trạng thái của ứng dụng UI
- `ui/views`: Chứa `ChatView` Chịu trách nhiệm hiển thị (render) giao diện người dùng ra Terminal bằng thư viện Rich.
- `config`: Chứa các cấu hình system prompt của agent chính và cấu hình cho các sub agent

## 🧠 Nguyên tắc Coding dành cho AI Assistant (AI Instructions)

1. **Hướng đối tượng**: các thành phần đều được tổ chức theo các class, có thể áp dụng design pattern để tối ứng hệ
   thống
2. **Clean Code**: ưu tiên code rõ ràng, dễ bảo trì
3. **Chống lỗi**: khi giao tiếp vs các thành phần có ảnh hưởng từ bên ngoài (như: LLM, agent) thì dùng try expect để đảm
   bảo hệ thống luôn hoạt động ngay cả khi provider xảy ra lỗi
4. **Thêm một chức năng vào UI**: thì bắt buộc thêm phải đọc file `service.json` để nắm được cách sử dụng phương thức
   của service

## Nguyên tắc làm việc:

- Mặc định trả lời bằng tiếng việt 