import os
import uuid
import anyio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from langchain_core.messages import HumanMessage

from app.storage.mongodb import MongoDBManager
from app.service.agent import AgentService

class ChatService:
    """
    ChatService quản lý các cuộc trò chuyện (sessions) và tin nhắn (messages) trong MongoDB.
    Đồng thời tích hợp và gọi AI Agent xử lý câu hỏi của người dùng.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ChatService, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._init_db()
            self.agent_service = AgentService()

    def _init_db(self):
        """
        Khởi tạo kết nối MongoDB và tạo chỉ mục tìm kiếm.
        """
        try:
            self.mongo_manager = MongoDBManager()
            self.client = self.mongo_manager.get_client()
            db_name = os.getenv("MONGODB_DB_NAME", "rag_lawyer")
            self.db = self.client[db_name]
            self.collection = self.db["chat_sessions"]
            
            # Tạo index để tối ưu tìm kiếm theo session id và user_id
            self.collection.create_index("id", unique=True)
            self.collection.create_index("user_id")
        except Exception as e:
            raise RuntimeError(f"ChatService failed to initialize MongoDB connection: {str(e)}") from e

    async def get_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Lấy danh sách tất cả các phiên hội thoại của người dùng (chỉ lấy metadata, không lấy mảng tin nhắn).
        """
        try:
            def _sync_find():
                cursor = self.collection.find(
                    {"user_id": user_id},
                    {"id": 1, "user_id": 1, "title": 1, "created_at": 1, "updated_at": 1}
                ).sort("updated_at", -1)
                return list(cursor)
                
            docs = await anyio.to_thread.run_sync(_sync_find)
            
            sessions = []
            for doc in docs:
                sessions.append({
                    "id": doc["id"],
                    "title": doc["title"],
                    "created_at": doc["created_at"].isoformat() if isinstance(doc["created_at"], datetime) else doc["created_at"],
                    "updated_at": doc["updated_at"].isoformat() if isinstance(doc["updated_at"], datetime) else doc["updated_at"]
                })
            return sessions
        except Exception as e:
            raise RuntimeError(f"Lỗi hệ thống khi lấy danh sách phòng chat: {str(e)}") from e

    async def create_session(self, user_id: str, title: str) -> Dict[str, Any]:
        """
        Tạo một phiên hội thoại mới.
        """
        try:
            session_id = uuid.uuid4().hex
            now = datetime.now(timezone.utc)
            new_session = {
                "id": session_id,
                "user_id": user_id,
                "title": title or "Cuộc hội thoại mới",
                "messages": [],
                "created_at": now,
                "updated_at": now
            }
            
            await anyio.to_thread.run_sync(self.collection.insert_one, new_session)
            
            return {
                "id": session_id,
                "title": new_session["title"],
                "created_at": now.isoformat(),
                "updated_at": now.isoformat()
            }
        except Exception as e:
            raise RuntimeError(f"Lỗi hệ thống khi tạo phòng chat mới: {str(e)}") from e

    async def delete_session(self, user_id: str, session_id: str) -> bool:
        """
        Xóa một phiên hội thoại.
        """
        try:
            def _sync_delete():
                result = self.collection.delete_one({"id": session_id, "user_id": user_id})
                return result.deleted_count > 0
                
            return await anyio.to_thread.run_sync(_sync_delete)
        except Exception as e:
            raise RuntimeError(f"Lỗi hệ thống khi xóa phòng chat: {str(e)}") from e

    async def get_messages(self, user_id: str, session_id: str) -> List[Dict[str, Any]]:
        """
        Lấy toàn bộ danh sách tin nhắn của một phiên hội thoại.
        """
        try:
            def _sync_find_one():
                return self.collection.find_one({"id": session_id, "user_id": user_id}, {"messages": 1})
                
            doc = await anyio.to_thread.run_sync(_sync_find_one)
            if not doc:
                raise ValueError("Không tìm thấy phiên hội thoại này hoặc bạn không có quyền truy cập.")
                
            messages = []
            for msg in doc.get("messages", []):
                messages.append({
                    "id": msg.get("id"),
                    "role": msg.get("role"),
                    "content": msg.get("content"),
                    "thinking": msg.get("thinking", ""),
                    "created_at": msg["created_at"].isoformat() if isinstance(msg.get("created_at"), datetime) else msg.get("created_at")
                })
            return messages
        except ValueError as e:
            raise e
        except Exception as e:
            raise RuntimeError(f"Lỗi hệ thống khi tải tin nhắn: {str(e)}") from e

    async def send_message(self, user_id: str, session_id: str, content: str) -> Dict[str, Any]:
        """
        Gửi tin nhắn mới từ người dùng, gọi AI Agent để nhận phản hồi và lưu lại.
        """
        try:
            # 1. Xác thực sự tồn tại của session
            def _sync_find_session():
                return self.collection.find_one({"id": session_id, "user_id": user_id})
                
            session = await anyio.to_thread.run_sync(_sync_find_session)
            if not session:
                raise ValueError("Không tìm thấy cuộc hội thoại này hoặc bạn không có quyền.")

            # 2. Tạo và lưu tin nhắn của User
            user_msg_id = uuid.uuid4().hex
            now = datetime.now(timezone.utc)
            user_message = {
                "id": user_msg_id,
                "role": "user",
                "content": content,
                "thinking": "",
                "created_at": now
            }
            
            def _sync_save_user_msg():
                self.collection.update_one(
                    {"id": session_id},
                    {
                        "$push": {"messages": user_message},
                        "$set": {"updated_at": now}
                    }
                )
            
            await anyio.to_thread.run_sync(_sync_save_user_msg)

            # 3. Gọi thực thể AI Agent
            text_response = ""
            thinking_response = ""
            
            try:
                agent = self.agent_service.get_agent_for_user(user_id)
                config_message = {"configurable": {"thread_id": session_id}}
                last_event = None
                
                # Gọi và chạy toàn bộ stream từ Agent bất đồng bộ để lấy kết quả hoàn chỉnh
                async for event in agent.astream(
                    {"messages": [HumanMessage(content=content)]},
                    config=config_message,
                    stream_mode="values"
                ):
                    last_event = event
                
                if last_event and "messages" in last_event and len(last_event["messages"]) > 0:
                    ai_message = last_event["messages"][-1]
                    raw_content = ai_message.content
                    text_response, thinking_response = self._parse_agent_response(raw_content)
                else:
                    text_response = "AI Agent không trả về phản hồi hợp lệ."
                    thinking_response = "Lỗi: Không nhận được sự kiện phản hồi."
            except Exception as agent_error:
                text_response = f"Xin lỗi, đã xảy ra lỗi trong quá trình xử lý câu hỏi của bạn: {str(agent_error)}"
                thinking_response = f"Lỗi hệ thống khi gọi AI Agent: {str(agent_error)}"

            # 4. Tạo và lưu tin nhắn của Assistant (AI)
            assistant_msg_id = uuid.uuid4().hex
            assistant_now = datetime.now(timezone.utc)
            assistant_message = {
                "id": assistant_msg_id,
                "role": "assistant",
                "content": text_response,
                "thinking": thinking_response,
                "created_at": assistant_now
            }
            
            def _sync_save_assistant_msg():
                self.collection.update_one(
                    {"id": session_id},
                    {
                        "$push": {"messages": assistant_message},
                        "$set": {"updated_at": assistant_now}
                    }
                )
                
            await anyio.to_thread.run_sync(_sync_save_assistant_msg)
            
            # Trả về tin nhắn của AI dạng JSON cho API response
            return {
                "id": assistant_msg_id,
                "role": "assistant",
                "content": text_response,
                "thinking": thinking_response,
                "created_at": assistant_now.isoformat()
            }
            
        except ValueError as e:
            raise e
        except Exception as e:
            raise RuntimeError(f"Lỗi hệ thống khi gửi tin nhắn: {str(e)}") from e

    async def send_message_stream(self, user_id: str, session_id: str, content: str):
        """
        Gửi tin nhắn mới từ người dùng dưới dạng Stream (Server-Sent Events),
        gọi AI Agent để nhận phản hồi và lưu lại sau khi hoàn thành.
        """
        import json
        try:
            # 1. Xác thực sự tồn tại của session
            def _sync_find_session():
                return self.collection.find_one({"id": session_id, "user_id": user_id})
                
            session = await anyio.to_thread.run_sync(_sync_find_session)
            if not session:
                raise ValueError("Không tìm thấy cuộc hội thoại này hoặc bạn không có quyền.")

            # 2. Tạo và lưu tin nhắn của User
            user_msg_id = uuid.uuid4().hex
            now = datetime.now(timezone.utc)
            user_message = {
                "id": user_msg_id,
                "role": "user",
                "content": content,
                "thinking": "",
                "created_at": now
            }
            
            def _sync_save_user_msg():
                self.collection.update_one(
                    {"id": session_id},
                    {
                        "$push": {"messages": user_message},
                        "$set": {"updated_at": now}
                    }
                )
            
            await anyio.to_thread.run_sync(_sync_save_user_msg)

            # 3. Khởi tạo Agent
            agent = self.agent_service.get_agent_for_user(user_id)
            config_message = {"configurable": {"thread_id": session_id}}
            
            full_text = ""
            full_thinking = ""
            assistant_msg_id = uuid.uuid4().hex
            
            try:
                # Gọi astream_events để stream các token
                async for event in agent.astream_events(
                    {"messages": [HumanMessage(content=content)]},
                    config=config_message,
                    version="v2"
                ):
                    event_type = event.get("event")
                    # Lọc các event stream của chat model chính
                    if event_type == "on_chat_model_stream":
                        chunk = event["data"]["chunk"]
                        chunk_content = chunk.content
                        
                        delta_text = ""
                        delta_thinking = ""
                        
                        if isinstance(chunk_content, list):
                            for block in chunk_content:
                                if isinstance(block, dict) and block.get("type") == "thinking":
                                    delta_thinking += block.get("thinking", "")
                                elif isinstance(block, dict) and block.get("type") == "text":
                                    delta_text += block.get("text", "")
                        elif isinstance(chunk_content, str):
                            delta_text = chunk_content
                            
                        if delta_thinking:
                            full_thinking += delta_thinking
                            yield f"data: {json.dumps({'type': 'thinking', 'delta': delta_thinking})}\n\n"
                        if delta_text:
                            full_text += delta_text
                            yield f"data: {json.dumps({'type': 'text', 'delta': delta_text})}\n\n"
                            
            except Exception as agent_error:
                error_msg = f"\n[Lỗi hệ thống trong quá trình xử lý: {str(agent_error)}]"
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
                full_text += error_msg
                full_thinking += f"\nLỗi: {str(agent_error)}"

            # 4. Tạo và lưu tin nhắn của Assistant (AI) sau khi hoàn thành
            assistant_now = datetime.now(timezone.utc)
            assistant_message = {
                "id": assistant_msg_id,
                "role": "assistant",
                "content": full_text,
                "thinking": full_thinking,
                "created_at": assistant_now
            }
            
            def _sync_save_assistant_msg():
                self.collection.update_one(
                    {"id": session_id},
                    {
                        "$push": {"messages": assistant_message},
                        "$set": {"updated_at": assistant_now}
                    }
                )
                
            await anyio.to_thread.run_sync(_sync_save_assistant_msg)
            
            # Gửi event done kèm theo thông tin đầy đủ của tin nhắn đã lưu
            yield f"data: {json.dumps({'type': 'done', 'id': assistant_msg_id, 'created_at': assistant_now.isoformat()})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    def _parse_agent_response(self, content: Any) -> tuple[str, str]:
        """
        Bóc tách phản hồi của Agent để lấy riêng phần suy nghĩ (thinking) và phần văn bản (text).
        Chống lỗi với mọi loại cấu trúc dữ liệu trả về từ LLM (List, Dict, JSON String, Plain Text).
        """
        thinking = ""
        text = ""
        
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "thinking":
                        thinking += block.get("thinking", "")
                    elif block.get("type") == "text":
                        text += block.get("text", "")
                elif hasattr(block, "get"):
                    if block.get("type") == "thinking":
                        thinking += block.get("thinking", "")
                    elif block.get("type") == "text":
                        text += block.get("text", "")
        elif isinstance(content, str):
            try:
                import json
                data = json.loads(content)
                if isinstance(data, list):
                    for block in data:
                        if isinstance(block, dict):
                            if block.get("type") == "thinking":
                                thinking += block.get("thinking", "")
                            elif block.get("type") == "text":
                                text += block.get("text", "")
                else:
                    text = content
            except Exception:
                text = content
        else:
            text = str(content)
            
        return text.strip(), thinking.strip()
