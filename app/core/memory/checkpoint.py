import os
from typing import Optional
from dotenv import load_dotenv
from langgraph.checkpoint.memory import BaseCheckpointSaver

from app.storage.mongodb import MongoDBManager

load_dotenv()

# Khởi tạo các import checkpoint saver linh hoạt
try:
    from langgraph.checkpoint.memory import MemorySaver
except ImportError:
    MemorySaver = None

try:
    from langgraph.checkpoint.mongodb import MongoDBSaver

except ImportError:
    MongoDBSaver = None


class CheckpointFactory:
    """
    CheckpointFactory quản lý việc khởi tạo các bộ lưu trữ checkpoint (Checkpointer)
    cho các LangGraph Agent dựa trên cấu hình môi trường.
    """

    @staticmethod
    def get_checkpoint(provider: Optional[str] = None, **kwargs) -> BaseCheckpointSaver:
        """
        Khởi tạo và trả về một instance Checkpointer phù hợp.
        
        Args:
            provider: Tên provider ('mongodb', 'memory'). Nếu None sẽ lấy từ biến môi trường CHECKPOINT_PROVIDER.
            **kwargs: Các tham số truyền thêm tùy theo từng provider (db_name, collection_name, ...).
            
        Returns:
            Đối tượng checkpointer kế thừa từ BaseCheckpointSaver.
        """
        if not provider:
            provider = os.getenv("CHECKPOINT_PROVIDER", "memory").lower()

        if provider == "mongodb":
            try:
                mongodb_manager = MongoDBManager()
                return mongodb_manager.get_checkpointer(
                    db_name=kwargs.get("db_name"),
                    checkpoint_collection_name=kwargs.get("checkpoint_collection_name", "checkpoints"),
                    writes_collection_name=kwargs.get("writes_collection_name", "checkpoint_writes")
                )
            except Exception as e:
                # Chống lỗi: fallback về MemorySaver nếu khởi tạo MongoDB thất bại để đảm bảo app luôn chạy được
                print(f"Warning: Failed to load MongoDB Checkpointer ({e}). Falling back to MemorySaver.")
                if MemorySaver is not None:
                    return MemorySaver()
                raise RuntimeError(
                    f"Failed to initialize MongoDB checkpoint and MemorySaver is not available: {str(e)}"
                ) from e

        elif provider == "memory":
            if MemorySaver is None:
                raise ImportError(
                    "Could not import MemorySaver. Please install `langgraph` package."
                )
            return MemorySaver()

        else:
            raise ValueError(f"Unsupported checkpoint provider: '{provider}'")
