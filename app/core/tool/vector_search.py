from typing import Type, Optional, List, Tuple, Any
import asyncio
import sys
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain_core.documents import Document
from app.storage.vector_store import QdrantVectorStoreManager


class VectorSearchInput(BaseModel):
    """
    Schema định nghĩa tham số đầu vào cho VectorSearch Tool.
    Sử dụng Pydantic v2 theo chuẩn cấu trúc của dự án.
    """
    query: str = Field(
        ...,
        description="Câu truy vấn hoặc cụm từ khóa để tìm kiếm văn bản pháp luật liên quan."
    )
    collection_name: str = Field(
        default="RAG_lawer",
        description="Tên collection trong vector database cần thực hiện tìm kiếm."
    )
    k: int = Field(
        default=5,
        description="Số lượng tài liệu phù hợp nhất cần trả về."
    )
    score_threshold: Optional[float] = Field(
        default=None,
        description="Điểm tương đồng tối thiểu của tài liệu để giữ lại kết quả (từ 0.0 đến 1.0)."
    )


class VectorSearchCore:
    """
    Lớp chịu trách nhiệm triển khai logic tìm kiếm và định dạng dữ liệu (Core Logic).
    Tách biệt logic nghiệp vụ khỏi adapter LangChain.
    """

    def __init__(self):
        # Lấy instance Singleton của QdrantVectorStoreManager
        self.vector_store_manager = QdrantVectorStoreManager()

    def search(
            self,
            query: str,
            collection_name: str = "RAG_lawyer",
            k: int = 5,
            score_threshold: Optional[float] = None,
            filter: Optional[Any] = None
    ) -> List[Tuple[Document, float]]:
        """
        Thực hiện tìm kiếm ngữ nghĩa trong Vector Store.
        
        Sử dụng try-except chống lỗi kết nối hoặc truy vấn Vector DB để không làm sập luồng chính.
        """
        try:
            results = self.vector_store_manager.semantic_search(
                query=query,
                collection_name=collection_name,
                k=k,
                score_threshold=score_threshold,
                filter=filter
            )
            return results
        except Exception as e:
            # Chống lỗi: log lỗi ra stderr và trả về danh sách rỗng để agent xử lý tiếp
            print(f"Error during semantic search in collection '{collection_name}': {str(e)}", file=sys.stderr)
            return []

    # def format_results(self, results: List[Tuple[Document, float]]) -> str:
    #     """
    #     Định dạng dữ liệu trả về từ Vector Store thành chuỗi văn bản thân thiện với LLM.
    #     """
    #     if not results:
    #         return "Không tìm thấy tài liệu pháp lý nào phù hợp với yêu cầu tìm kiếm."
    #
    #     formatted_docs = []
    #     for index, (doc, score) in enumerate(results, 1):
    #         metadata = doc.metadata or {}
    #         source = metadata.get("document", "Không rõ nguồn")
    #         title = metadata.get("title", "")
    #
    #         header = f"--- Tài liệu {index} (Độ khớp: {score:.4f}) ---"
    #         source_info = f"Nguồn: {source}"
    #         if title:
    #             source_info += f" | Tiêu đề: {title}"
    #
    #         content = doc.page_content.strip()
    #
    #         formatted_doc = f"{header}\n{source_info}\nNội dung:\n{content}"
    #         formatted_docs.append(formatted_doc)
    #
    #     return "\n\n".join(formatted_docs)


class VectorSearch(BaseTool):
    """
    Adapter kết nối VectorSearchCore với hệ thống LangChain.
    Kế thừa BaseTool và tích hợp schema đầu vào VectorSearchInput.
    """
    name: str = "vector_search"
    description: str = (
        "Hữu ích khi cần tìm kiếm các quy định pháp luật, điều khoản luật, "
        "hoặc tài liệu pháp lý liên quan đến câu hỏi của người dùng."
    )
    args_schema: Type[BaseModel] = VectorSearchInput

    def _run(
            self,
            query: str,
            collection_name: str = "RAG_lawyer",
            k: int = 10,
            score_threshold: Optional[float] = None,
            **kwargs: Any
    ) -> list[Document]:
        """
        Thực hiện tìm kiếm đồng bộ.
        """
        core = VectorSearchCore()
        return core.search(
            query=query,
            collection_name=collection_name,
            k=k,
            score_threshold=score_threshold
        )

    async def _arun(
            self,
            query: str,
            collection_name: str = "RAG_lawyer",
            k: int = 5,
            score_threshold: Optional[float] = None,
            **kwargs: Any
    ) -> list[Document]:
        """
        Thực hiện tìm kiếm bất đồng bộ.
        Sử dụng run_in_executor để tránh block event loop của FastAPI khi gọi các hàm Qdrant Client đồng bộ.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._run,
            query,
            collection_name,
            k,
            score_threshold
        )


# Định nghĩa thêm alias để giữ tính tương thích ngược với các thành phần cũ
VectorSearchTool = VectorSearch()
