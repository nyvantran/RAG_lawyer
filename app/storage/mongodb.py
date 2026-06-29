import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Khởi tạo exception linh hoạt
try:
    from pymongo import MongoClient
except ImportError as e:
    raise ImportError(
        "Could not import pymongo. Please install it using `pip install pymongo`."
    ) from e

try:
    from langgraph.checkpoint.mongodb import MongoDBSaver
except ImportError:
    MongoDBSaver = None


class MongoDBManager:
    """
    MongoDBManager quản lý kết nối đến cơ sở dữ liệu MongoDB và khởi tạo 
    thành phần lưu checkpoint (Checkpointer) cho LangGraph.
    Áp dụng Singleton Pattern cho client.
    """
    _instance = None
    _client = None
    _checkpointer = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(MongoDBManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        # Đảm bảo quá trình khởi tạo client chỉ chạy một lần duy nhất
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._init_client()

    def _init_client(self):
        """
        Khởi tạo MongoClient dựa trên biến môi trường.
        """
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://admin:secret_password@localhost:27017/")
        try:
            self._client = MongoClient(mongodb_url)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize MongoDB Client: {str(e)}") from e

    def get_client(self) -> MongoClient:
        """
        Trả về đối tượng MongoClient gốc để thực hiện các thao tác nâng cao.
        """
        return self._client

    def get_checkpointer(
        self,
        db_name: Optional[str] = None,
        checkpoint_collection_name: str = "checkpoints",
        writes_collection_name: str = "checkpoint_writes"
    ) -> MongoDBSaver:
        """
        Lấy hoặc khởi tạo đối tượng MongoDBSaver dùng cho LangGraph checkpointing.
        
        Args:
            db_name: Tên database để lưu checkpoint.
            checkpoint_collection_name: Tên collection lưu các checkpoint.
            writes_collection_name: Tên collection lưu lịch sử ghi của checkpoint.
            
        Returns:
            Một instance MongoDBSaver cho LangGraph.
        """
        if MongoDBSaver is None:
            raise ImportError(
                "langgraph-checkpoint-mongodb is not installed. "
                "Please install it using `pip install langgraph-checkpoint-mongodb`."
            )

        if not self._checkpointer:
            if db_name is None:
                db_name = os.getenv("MONGODB_DB_NAME", "rag_lawyer")
            
            try:
                # Khởi tạo MongoDBSaver
                self._checkpointer = MongoDBSaver(
                    client=self._client,
                    db_name=db_name,
                    checkpoint_collection_name=checkpoint_collection_name,
                    writes_collection_name=writes_collection_name
                )
            except Exception as e:
                # Chống lỗi: ném ngoại lệ mô tả chi tiết lỗi kết nối/khởi tạo
                raise RuntimeError(
                    f"Failed to initialize MongoDBSaver checkpointer: {str(e)}"
                ) from e
        
        return self._checkpointer
