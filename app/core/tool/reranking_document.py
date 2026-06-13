import os
import sys
from typing import List, Tuple, Optional, Any, Type
import asyncio
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain_core.documents import Document


class RerankerModelManager:
    """
    Singleton Manager quản lý việc tải và lưu trữ instance của CrossEncoder.
    Tránh việc tải lại mô hình nhiều lần gây tốn tài nguyên và thời gian.
    """
    _instance = None
    _model = None
    _current_model_name = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(RerankerModelManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def get_model(self, model_name: str = "keepitreal/vietnamese-sbert"):
        """
        Lấy hoặc khởi tạo mô hình CrossEncoder (luôn trả về cùng một đối tượng nếu model_name không đổi).
        """
        # Nếu model chưa được load hoặc đổi model khác, tiến hành tải mới
        if self._model is None or self._current_model_name != model_name:
            try:
                from sentence_transformers import CrossEncoder
                print(f"Đang tải mô hình Re-ranker: {model_name}...", file=sys.stderr)
                self._model = CrossEncoder(model_name)
                self._current_model_name = model_name
                print(f"Tải mô hình Re-ranker '{model_name}' thành công.", file=sys.stderr)
            except ImportError as e:
                print(
                    f"Lỗi: Không thể import 'sentence_transformers'. Vui lòng cài đặt thư viện này. "
                    f"Chi tiết: {str(e)}",
                    file=sys.stderr
                )
                raise e
            except Exception as e:
                print(f"Lỗi tải mô hình Re-ranker '{model_name}': {str(e)}", file=sys.stderr)
                raise e
        return self._model


class RerankingDocumentInput(BaseModel):
    """
    Schema định nghĩa tham số đầu vào cho RerankingDocument Tool.
    Sử dụng Pydantic v2 theo chuẩn cấu trúc của dự án.
    """
    query: str = Field(
        ...,
        description="Câu truy vấn dùng để tính điểm mức độ liên quan với các tài liệu."
    )
    documents: List[Any] = Field(
        ...,
        description="Danh sách các tài liệu cần xếp hạng lại (có thể là đối tượng Document, dictionary hoặc string)."
    )
    model_name: Optional[str] = Field(
        default=None,
        description="Tên model CrossEncoder được sử dụng để rerank."
    )


class RerankingDocumentCore:
    """
    Lớp chịu trách nhiệm triển khai logic xếp hạng lại tài liệu (Core Logic).
    Tách biệt logic nghiệp vụ khỏi adapter LangChain.
    """

    def rerank(
            self,
            query: str,
            documents: List[Any],
            model_name: Optional[str] = None
    ) -> List[Tuple[Document, float]]:
        """
        Thực hiện xếp hạng lại danh sách tài liệu dựa trên mức độ liên quan với câu truy vấn.

        Sử dụng try-except chống lỗi tải mô hình hoặc xử lý để bảo vệ luồng chính.
        """
        if not documents:
            return []

        try:
            # 1. Chuẩn hóa documents đầu vào thành List[Document] và List[str] để đưa vào CrossEncoder
            normalized_docs: List[Document] = []
            text_contents: List[str] = []

            for doc in documents:
                if isinstance(doc, Document):
                    normalized_docs.append(doc)
                    text_ct = RerankingDocumentCore.metadata2str(doc.metadata) + doc.page_content
                    text_contents.append(
                        text_ct
                    )
                elif isinstance(doc, dict):
                    page_content = doc.get("page_content", doc.get("text", ""))
                    metadata = doc.get("metadata", {})
                    new_doc = Document(page_content=page_content, metadata=metadata)
                    text_ct = RerankingDocumentCore.metadata2str(new_doc.metadata) + new_doc.page_content
                    normalized_docs.append(new_doc)
                    text_contents.append(text_ct)
                elif isinstance(doc, str):
                    new_doc = Document(page_content=doc, metadata={})
                    normalized_docs.append(new_doc)
                    text_contents.append(doc)
                else:
                    # Tránh lỗi kiểu dữ liệu lạ: ép kiểu về string
                    str_content = str(doc)
                    new_doc = Document(page_content=str_content, metadata={})
                    normalized_docs.append(new_doc)
                    text_contents.append(str_content)

            # 2. Xác định model name (ưu tiên model_name truyền vào, kế đến .env, cuối cùng là mặc định)
            resolved_model_name = (
                    model_name
                    or os.getenv("DEFAULT_RERANK_MODEL")
                    or os.getenv("DEFAULT_EMB_MODEL")
                    or "keepitreal/vietnamese-sbert"
            )

            # 3. Lấy instance model qua Singleton Manager
            model_manager = RerankerModelManager()
            model = model_manager.get_model(resolved_model_name)

            # 4. Thực hiện chấm điểm
            scores = model.rank(
                query=query,
                documents=text_contents,
            )

            # 5. Khớp kết quả trả về với danh sách Document ban đầu và gán điểm số vào metadata
            results = []
            for item in scores:
                idx = item["corpus_id"]
                score = float(item["score"])
                orig_doc = normalized_docs[idx]

                # Cập nhật điểm số vào metadata của Document để dễ truy cập sau này
                if orig_doc.metadata is None:
                    orig_doc.metadata = {}
                orig_doc.metadata["score"] = score

                results.append((orig_doc, score))

            # Sắp xếp lại danh sách kết quả giảm dần theo score (CrossEncoder.rank thường đã tự sắp xếp)
            results.sort(key=lambda x: x[1], reverse=True)
            return results

        except Exception as e:
            # Chống lỗi: ghi nhận lỗi chi tiết ra stderr và fallback trả về tài liệu gốc kèm score = 0.0
            print(f"Error during document reranking: {str(e)}", file=sys.stderr)
            fallback_results = []
            for doc in documents:
                if isinstance(doc, Document):
                    fallback_results.append((doc, 0.0))
                elif isinstance(doc, dict):
                    page_content = doc.get("page_content", doc.get("text", ""))
                    metadata = doc.get("metadata", {})
                    fallback_results.append((Document(page_content=page_content, metadata=metadata), 0.0))
                else:
                    fallback_results.append((Document(page_content=str(doc), metadata={}), 0.0))
            return fallback_results

    @staticmethod
    def metadata2str(
            metadata: dict[str, Any],
    ) -> str:
        data = metadata.copy()
        data.pop('_id')
        data.pop('_collection_name')
        return ". ".join(map(str, data.values())) + '\n'


class RerankingDocument(BaseTool):
    """
    Adapter kết nối RerankingDocumentCore với hệ thống LangChain.
    Kế thừa BaseTool và tích hợp schema đầu vào RerankingDocumentInput.
    """
    name: str = "reranking_document"
    description: str = (
        "Hữu ích khi cần xếp hạng lại (rerank) danh sách tài liệu dựa trên mức độ "
        "liên quan ngữ nghĩa với câu hỏi truy vấn của người dùng."
    )
    args_schema: Type[BaseModel] = RerankingDocumentInput

    def _run(
            self,
            query: str,
            documents: List[Any],
            model_name: Optional[str] = None,
            **kwargs: Any
    ) -> List[Tuple[Document, float]]:
        """
        Thực hiện xếp hạng lại tài liệu đồng bộ.
        """
        core = RerankingDocumentCore()
        return core.rerank(
            query=query,
            documents=documents,
            model_name=model_name
        )

    async def _arun(
            self,
            query: str,
            documents: List[Any],
            model_name: Optional[str] = None,
            **kwargs: Any
    ) -> List[Tuple[Document, float]]:
        """
        Thực hiện xếp hạng lại tài liệu bất đồng bộ.
        Sử dụng run_in_executor để tránh block event loop của FastAPI khi chạy mô hình deep learning local.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._run,
            query,
            documents,
            model_name
        )


# Định nghĩa alias để giữ tính đồng bộ với cấu trúc của dự án (như VectorSearchTool)
RerankingDocumentTool = RerankingDocument()
