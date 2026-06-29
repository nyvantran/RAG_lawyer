import os
from typing import Dict, Any
from app.core.agent.agent_factory import AgentFactory

class AgentService:
    """
    AgentService quản lý các thực thể Agent của người dùng.
    Mỗi người dùng sẽ sở hữu duy nhất một instance Agent trong bộ nhớ (Singleton per User).
    """
    _instance = None
    _agents: Dict[str, Any] = {}

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AgentService, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._initialized = True

    def get_agent_for_user(self, user_id: str) -> Any:
        """
        Lấy thực thể Agent của người dùng. Nếu chưa tồn tại, tiến hành khởi tạo mới qua AgentFactory.
        """
        if user_id not in self._agents:
            try:
                factory = AgentFactory()
                # Khởi tạo agent mặc định 'lawyer_agent'
                agent = factory.create_agent("lawyer_agent")
                self._agents[user_id] = agent
            except Exception as e:
                raise RuntimeError(f"Không thể khởi tạo Agent cho người dùng {user_id}: {str(e)}") from e
        return self._agents[user_id]

    def clear_agent_for_user(self, user_id: str):
        """
        Giải phóng thực thể Agent của người dùng khỏi bộ nhớ (ví dụ: khi người dùng đăng xuất).
        """
        if user_id in self._agents:
            del self._agents[user_id]
