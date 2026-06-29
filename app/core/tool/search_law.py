from typing import Type, Optional, List, Any
import asyncio
import sys
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain_core.documents import Document

from app.core.tool.vector_search import VectorSearchCore
from app.core.tool.reranking_document import RerankingDocumentCore


class SearchLawInput(BaseModel):
    """
    Schema định nghĩa tham số đầu vào cho SearchLaw Tool.
    Sử dụng Pydantic v2 theo chuẩn cấu trúc của dự án.
    """
    query: str = Field(
        ...,
        description="Câu truy vấn hoặc cụm từ khóa để tìm kiếm các quy định pháp luật liên quan."
    )
    search_k: int = Field(
        default=10,
        description="Số lượng tài liệu thô tối đa cần tìm kiếm từ Vector Store trước khi xếp hạng lại."
    )
    rerank_k: int = Field(
        default=5,
        description="Số lượng tài liệu phù hợp nhất cần trả về sau khi đã xếp hạng lại (rerank)."
    )
    collection_name: str = Field(
        default="RAG_lawyer",
        description="Tên collection trong vector database cần thực hiện tìm kiếm."
    )


class SearchLawCore:
    """
    Lớp chịu trách nhiệm kết hợp VectorSearchCore và RerankingDocumentCore
    để tìm kiếm và xếp hạng tài liệu pháp luật (Core Logic).
    """

    def __init__(self):
        self.vector_search_core = VectorSearchCore()
        self.reranking_core = RerankingDocumentCore()

    def search_and_rerank(
            self,
            query: str,
            search_k: int = 10,
            rerank_k: int = 3,
            collection_name: str = "RAG_lawyer"
    ) -> List[Document]:
        """
        Thực hiện tìm kiếm tài liệu qua VectorSearchCore, sau đó xếp hạng lại qua RerankingDocumentCore
        và trả về danh sách rerank_k tài liệu phù hợp nhất.
        
        Sử dụng try-except chống lỗi để đảm bảo hệ thống luôn hoạt động ngay cả khi xảy ra lỗi ngoài ý muốn.
        """
        try:
            # 1. Tìm kiếm tài liệu từ vector database
            raw_docs = self.vector_search_core.search(
                query=query,
                collection_name=collection_name,
                k=search_k
            )
            
            if not raw_docs:
                return []

            # 2. Xếp hạng lại tài liệu bằng reranker
            reranked_results = self.reranking_core.rerank(
                query=query,
                documents=raw_docs
            )

            # 3. Trích xuất danh sách Document và giới hạn số lượng trả về (rerank_k)
            sorted_docs = RerankingDocumentCore.format_list_document(reranked_results)
            
            return sorted_docs[:rerank_k]

        except Exception as e:
            # Chống lỗi: ghi nhận lỗi chi tiết ra stderr và trả về danh sách rỗng để không ảnh hưởng luồng chính
            print(f"Error during search_and_rerank: {str(e)}", file=sys.stderr)
            return []


class SearchLaw(BaseTool):
    """
    Adapter kết nối SearchLawCore với hệ thống LangChain.
    Kế thừa BaseTool và tích hợp schema đầu vào SearchLawInput.
    """
    name: str = "search_law"
    description: str = (
        "Hữu ích khi cần tìm kiếm các quy định pháp luật liên quan đến câu hỏi của người dùng. "
        "Công cụ này tự động thực hiện tìm kiếm ngữ nghĩa và xếp hạng lại các tài liệu tìm được "
        "để cung cấp các kết quả chính xác nhất."
    )
    args_schema: Type[BaseModel] = SearchLawInput

    def _run(
            self,
            query: str,
            search_k: int = 10,
            rerank_k: int = 3,
            collection_name: str = "RAG_lawyer",
            **kwargs: Any
    ) -> List[Document]:
        """
        Thực hiện tìm kiếm và xếp hạng đồng bộ.
        """
        core = SearchLawCore()
        return core.search_and_rerank(
            query=query,
            search_k=search_k,
            rerank_k=rerank_k,
            collection_name=collection_name
        )

    async def _arun(
            self,
            query: str,
            search_k: int = 10,
            rerank_k: int = 3,
            collection_name: str = "RAG_lawyer",
            **kwargs: Any
    ) -> List[Document]:
        """
        Thực hiện tìm kiếm và xếp hạng bất đồng bộ.
        Sử dụng run_in_executor để tránh block event loop của FastAPI khi chạy mô hình deep learning.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._run,
            query,
            search_k,
            rerank_k,
            collection_name
        )


# Định nghĩa instance Tool sẵn để sử dụng trong hệ thống
SearchLawTool = SearchLaw()
