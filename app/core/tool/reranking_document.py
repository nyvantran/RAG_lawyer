import os
import sys
from typing import List, Tuple, Optional, Any, Type
import asyncio

import torch
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
                device = "cuda" if torch.cuda.is_available() else "cpu"
                self._model = CrossEncoder(model_name, device=device)
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
    documents: List[Document] = Field(
        ...,
        description="Danh sách các tài liệu cần xếp hạng lại dưới dạng danh sách các đối tượng Document."
    )
    model_name: Optional[str] = Field(
        default=None,
        description="Tên model được sử dụng để rerank (ví dụ: 'namdp-ptit/ViRanker' cho huggingface hoặc 'rerank-v4.0-pro' cho cohere)."
    )
    provider: Optional[str] = Field(
        default=None,
        description="Nhà cung cấp dịch vụ rerank. Hỗ trợ 'huggingface' hoặc 'cohere'."
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
            model_name: Optional[str] = None,
            provider: Optional[str] = None
    ) -> List[Tuple[Document, float]]:
        """
        Thực hiện xếp hạng lại danh sách tài liệu dựa trên mức độ liên quan với câu truy vấn.

        Sử dụng try-except chống lỗi tải mô hình hoặc xử lý để bảo vệ luồng chính.
        """
        if not documents:
            return []
        if isinstance(documents[0], tuple):
            documents = self.format_list_document(documents)

        try:
            # 1. Chuẩn hóa documents đầu vào thành List[Document] và List[str] để đưa vào Reranker
            normalized_docs: List[Document] = []
            text_contents: List[str] = []

            for doc in documents:
                if isinstance(doc, Document):
                    normalized_docs.append(doc)
                    text_ct = RerankingDocumentCore.metadata2str(doc.metadata) + doc.page_content
                    text_contents.append(text_ct)
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

            # 2. Xác định provider (ưu tiên provider truyền vào, kế đến .env, mặc định là huggingface)
            resolved_provider = (
                provider
                or os.getenv("DEFAULT_RERANK_PROVIDER")
                or "huggingface"
            ).lower()

            results = []

            if resolved_provider == "cohere":
                # Nhánh Cohere
                resolved_model_name = (
                    model_name
                    or os.getenv("DEFAULT_RERANK_MODEL")
                    or os.getenv("DEFAULT_EMB_MODEL")
                    or "rerank-v4.0-pro"
                )
                
                cohere_results = self._rerank_cohere(
                    query=query,
                    text_contents=text_contents,
                    model_name=resolved_model_name
                )
                
                for item in cohere_results:
                    idx = item["index"]
                    score = float(item["relevance_score"])
                    orig_doc = normalized_docs[idx]

                    if orig_doc.metadata is None:
                        orig_doc.metadata = {}
                    orig_doc.metadata["score"] = score

                    results.append((orig_doc, score))
            else:
                # Nhánh Hugging Face (mặc định)
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
                    show_progress_bar=True,
                    batch_size=2,
                )

                # 5. Khớp kết quả trả về với danh sách Document ban đầu và gán điểm số vào metadata
                for item in scores:
                    idx = item["corpus_id"]
                    score = float(item["score"])
                    orig_doc = normalized_docs[idx]

                    if orig_doc.metadata is None:
                        orig_doc.metadata = {}
                    orig_doc.metadata["score"] = score

                    results.append((orig_doc, score))

            # Sắp xếp lại danh sách kết quả giảm dần theo score
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

    def _rerank_cohere(
            self,
            query: str,
            text_contents: List[str],
            model_name: str
    ) -> List[dict]:
        """
        Gọi API Cohere để xếp hạng lại tài liệu.
        Hỗ trợ sử dụng SDK cohere nếu có sẵn, ngược lại tự động fallback sang HTTP Request.
        """
        cohere_api_key = os.getenv("COHERE_API_KEY")
        if not cohere_api_key:
            raise ValueError("COHERE_API_KEY chưa được cấu hình trong biến môi trường.")

        try:
            import cohere
            client = cohere.ClientV2(api_key=cohere_api_key)
            response = client.rerank(
                model=model_name,
                query=query,
                documents=text_contents,
            )
            results = []
            for res in response.results:
                results.append({
                    "index": res.index,
                    "relevance_score": res.relevance_score
                })
            return results
        except ImportError:
            # Fallback sang gọi HTTP API trực tiếp bằng requests
            import requests
            headers = {
                "Authorization": f"Bearer {cohere_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model_name,
                "query": query,
                "documents": text_contents
            }
            response = requests.post("https://api.cohere.com/v2/rerank", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])

    @staticmethod
    def metadata2str(
            metadata: dict[str, Any],
    ) -> str:
        data = metadata.copy()
        data.pop('_id', None)
        data.pop('_collection_name', None)
        return ". ".join(map(str, data.values())) + '\n'

    @staticmethod
    def format_list_document(list_document: List[Tuple[Document, float | int]]) -> list[Document]:
        return [doc[0] for doc in list_document]


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
            documents: List[Document],
            model_name: Optional[str] = None,
            provider: Optional[str] = None,
            # **kwargs: Any
    ) -> List[Tuple[Document, float]]:
        """
        Thực hiện xếp hạng lại tài liệu đồng bộ.
        """
        core = RerankingDocumentCore()
        return core.rerank(
            query=query,
            documents=documents,
            model_name=model_name,
            provider=provider
        )

    async def _arun(
            self,
            query: str,
            documents: List[Document],
            model_name: Optional[str] = None,
            provider: Optional[str] = None,
            # **kwargs: Any
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
            model_name,
            provider
        )


# Định nghĩa alias để giữ tính đồng bộ với cấu trúc của dự án (như VectorSearchTool)
RerankingDocumentTool = RerankingDocument()
