from fastapi import APIRouter, Depends, status, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.service.chat import ChatService
from app.api.user import get_current_user
from app.schemas.user import UserResponse
from app.core.exceptions import AppException
from app.core.error_code import ErrorCode

router = APIRouter(prefix="/chat", tags=["chat"])

def get_chat_service() -> ChatService:
    """
    Dependency cung cấp instance Singleton của ChatService.
    """
    return ChatService()

# Schema dữ liệu đầu vào cho API
class SessionCreateRequest(BaseModel):
    title: Optional[str] = "Cuộc hội thoại mới"

class MessageSendRequest(BaseModel):
    content: str

@router.get("/sessions")
async def get_sessions(
    current_user: UserResponse = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service)
):
    """
    Lấy danh sách các phòng chat của người dùng hiện tại.
    """
    try:
        sessions = await service.get_sessions(current_user.id)
        return {
            "success": True,
            "data": sessions,
            "message": "Lấy danh sách phòng chat thành công"
        }
    except Exception as e:
        raise AppException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            message=f"Lỗi tải danh sách phòng chat: {str(e)}"
        )

@router.post("/sessions")
async def create_session(
    request: SessionCreateRequest,
    current_user: UserResponse = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service)
):
    """
    Tạo phòng chat mới cho người dùng hiện tại.
    """
    try:
        session = await service.create_session(current_user.id, request.title)
        return {
            "success": True,
            "data": session,
            "message": "Tạo phòng chat thành công"
        }
    except Exception as e:
        raise AppException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            message=f"Lỗi tạo phòng chat mới: {str(e)}"
        )

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service)
):
    """
    Xóa phòng chat của người dùng hiện tại.
    """
    try:
        deleted = await service.delete_session(current_user.id, session_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy phòng chat hoặc bạn không có quyền xóa"
            )
        return {
            "success": True,
            "data": None,
            "message": "Xóa phòng chat thành công"
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise AppException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            message=f"Lỗi xóa phòng chat: {str(e)}"
        )

@router.get("/sessions/{session_id}/messages")
async def get_messages(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service)
):
    """
    Lấy danh sách toàn bộ tin nhắn của một phòng chat cụ thể.
    """
    try:
        messages = await service.get_messages(current_user.id, session_id)
        return {
            "success": True,
            "data": messages,
            "message": "Tải tin nhắn thành công"
        }
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve)
        )
    except Exception as e:
        raise AppException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            message=f"Lỗi tải tin nhắn: {str(e)}"
        )

from fastapi.responses import StreamingResponse

@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: str,
    request: MessageSendRequest,
    current_user: UserResponse = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service)
):
    """
    Gửi tin nhắn mới của người dùng và stream phản hồi từ AI Agent (bao gồm suy nghĩ và câu trả lời).
    """
    if not request.content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nội dung tin nhắn không được để trống"
        )
        
    try:
        generator = service.send_message_stream(current_user.id, session_id, request.content)
        return StreamingResponse(generator, media_type="text/event-stream")
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve)
        )
    except Exception as e:
        raise AppException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            message=f"Lỗi xử lý gửi tin nhắn: {str(e)}"
        )
