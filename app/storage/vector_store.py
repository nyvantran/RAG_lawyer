import os
from typing import List, Optional, Any, Tuple
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from app.core.model import EMBFactory
from dotenv import load_dotenv

load_dotenv()

# Khởi tạo exception linh hoạt
try:
    from qdrant_client import QdrantClient
except ImportError as e:
    raise ImportError(
        "Could not import qdrant-client. Please install it using `pip install qdrant-client`."
    ) from e

try:
    # langchain-qdrant là thư viện chính thức từ langchain >= 0.3.0
    from langchain_qdrant import QdrantVectorStore
except ImportError:
    try:
        from langchain_community.vectorstores import Qdrant as QdrantVectorStore
    except ImportError as e:
        raise ImportError(
            "Could not import Qdrant from langchain. "
            "Please install `langchain-qdrant` or `langchain-community`."
        ) from e


class QdrantVectorStoreManager:
    """
    QdrantVectorStoreManager quản lý việc kết nối và tương tác với Qdrant Vector Database.
    Áp dụng Singleton Pattern cho client và Multiton Pattern cho các instance Vector Store theo collection.
    """
    _instance = None
    _client = None
    _vector_stores = {}

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(QdrantVectorStoreManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        # Đảm bảo quá trình khởi tạo client chỉ chạy một lần duy nhất
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._init_client()
            self.vector_name = os.getenv("VECTOR_SEARCH")

    def _init_client(self):
        """
        Khởi tạo QdrantClient dựa trên biến môi trường.
        Hỗ trợ cả chế độ lưu trữ Local Path (dev) và Qdrant Server/Cloud (production).
        """
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        vector_store_path = os.getenv("VECTOR_STORE_PATH", "./data/vector_store")

        try:
            if qdrant_url:
                # Chế độ kết nối Server (Docker / Cloud)
                self._client = QdrantClient(
                    url=qdrant_url,
                    api_key=qdrant_api_key,
                )
            else:
                # Chế độ lưu trữ local trên ổ đĩa
                if vector_store_path and not vector_store_path.startswith(":memory:"):
                    os.makedirs(vector_store_path, exist_ok=True)

                self._client = QdrantClient(path=vector_store_path)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Qdrant Client: {str(e)}") from e

    def get_client(self) -> QdrantClient:
        """
        Trả về đối tượng QdrantClient gốc để thực hiện các thao tác nâng cao.
        """
        return self._client

    def get_vector_store(
            self,
            collection_name: str,
            embeddings: Optional[Embeddings] = None
    ) -> QdrantVectorStore:
        """
        Lấy hoặc khởi tạo đối tượng QdrantVectorStore từ LangChain tương ứng với collection_name.
        """
        if collection_name in self._vector_stores:
            return self._vector_stores[collection_name]

        # Tự động lấy default embedding model từ EMBFactory nếu không truyền vào
        if embeddings is None:
            embeddings = EMBFactory.get_emb()

        try:
            # Thử khởi tạo với tham số `embedding` (chuẩn langchain_qdrant)
            try:
                vector_store = QdrantVectorStore(
                    client=self._client,
                    collection_name=collection_name,
                    embedding=embeddings,
                    vector_name=self.vector_name
                )
            except TypeError:
                # Fallback sang tham số `embeddings` (chuẩn langchain_community)
                vector_store = QdrantVectorStore(
                    client=self._client,
                    collection_name=collection_name,
                    embeddings=embeddings,
                )

            self._vector_stores[collection_name] = vector_store
            return vector_store
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize QdrantVectorStore for collection '{collection_name}': {str(e)}"
            ) from e

    def semantic_search(
            self,
            query: str,
            collection_name: str,
            k: int = 5,
            score_threshold: Optional[float] = None,
            filter: Optional[Any] = None,
            embeddings: Optional[Embeddings] = None,
            **kwargs
    ) -> List[Tuple[Document, float]]:
        """
        Tìm kiếm ngữ nghĩa (Semantic Search) trên collection được chỉ định.
        
        Args:
            query: Nội dung câu truy vấn cần tìm kiếm.
            collection_name: Tên collection cần tìm.
            k: Số lượng tài liệu phù hợp nhất muốn trả về.
            score_threshold: Điểm tương đồng tối thiểu để giữ lại kết quả.
            filter: Bộ lọc metadata của Qdrant.
            embeddings: Embedding model custom (tùy chọn).
            
        Returns:
            Danh sách Tuple (Document, score) chứa tài liệu tìm thấy và độ tương đồng tương ứng.
        """
        try:
            vector_store = self.get_vector_store(collection_name, embeddings=embeddings)

            # Tìm kiếm độ tương đồng kèm điểm số
            results = vector_store.similarity_search_with_score(
                query=query,
                k=k,
                filter=filter,
                **kwargs
            )

            # Lọc kết quả dựa trên score_threshold nếu được thiết lập
            if score_threshold is not None:
                results = [(doc, score) for doc, score in results if score >= score_threshold]

            return results
        except Exception as e:
            # Chống lỗi: Ghi nhận và ném ngoại lệ khi có lỗi kết nối hoặc truy vấn Vector DB
            raise RuntimeError(
                f"Failed during semantic search in collection '{collection_name}': {str(e)}"
            ) from e

    def add_documents(
            self,
            documents: List[Document],
            collection_name: str,
            embeddings: Optional[Embeddings] = None,
            **kwargs
    ) -> List[str]:
        """
        Thêm danh sách đối tượng Document vào Vector Store.
        """
        try:
            vector_store = self.get_vector_store(collection_name, embeddings=embeddings)
            return vector_store.add_documents(documents, **kwargs)
        except Exception as e:
            raise RuntimeError(
                f"Failed to add documents to collection '{collection_name}': {str(e)}"
            ) from e

    # def add_texts(
    #         self,
    #         texts: List[str],
    #         metadatas: Optional[List[dict]] = None,
    #         collection_name: str = "",
    #         embeddings: Optional[Embeddings] = None,
    #         **kwargs
    # ) -> List[str]:
    #     """
    #     Thêm danh sách văn bản thuần (texts) cùng metadata vào Vector Store.
    #     """
    #     try:
    #         vector_store = self.get_vector_store(collection_name, embeddings=embeddings)
    #         return vector_store.add_texts(texts, metadatas=metadatas, **kwargs)
    #     except Exception as e:
    #         raise RuntimeError(
    #             f"Failed to add texts to collection '{collection_name}': {str(e)}"
    #         ) from e

    def delete_collection(self, collection_name: str) -> bool:
        """
        Xóa hoàn toàn một collection trong Qdrant.
        """
        try:
            self._client.delete_collection(collection_name)
            if collection_name in self._vector_stores:
                del self._vector_stores[collection_name]
            return True
        except Exception as e:
            # Ghi nhận lỗi nhưng không làm sập luồng xử lý chính nếu collection không tồn tại
            return False
