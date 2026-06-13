import os
from typing import Optional
from langchain_core.embeddings import Embeddings
from dotenv import load_dotenv

# Tải biến môi trường
load_dotenv()

class EMBFactory:
    """
    EMBFactory quản lý khởi tạo các đối tượng Embedding Model dựa trên Provider và Model Name.
    Áp dụng Factory Pattern để chuẩn hóa việc tạo đối tượng kế thừa từ Embeddings.
    """
    
    @classmethod
    def get_emb(
        cls, 
        provider: Optional[str] = None, 
        model_name: Optional[str] = None, 
        **kwargs
    ) -> Embeddings:
        """
        Khởi tạo và trả về instance của Embedding Model.
        
        Args:
            provider: Tên nhà cung cấp (openai, google, huggingface, anthropic). 
                      Nếu không truyền, lấy mặc định từ DEFAULT_EMB_PROVIDER.
            model_name: Tên model cụ thể (ví dụ: text-embedding-3-small, keepitreal/vietnamese-sbert).
                        Nếu không truyền, lấy mặc định từ DEFAULT_EMB_MODEL.
            **kwargs: Các tham số bổ sung khác.
            
        Returns:
            Một đối tượng kế thừa từ Embeddings.
        """
        # Load lại env để đảm bảo cập nhật các biến môi trường mới nhất
        load_dotenv()
        
        # Lấy giá trị mặc định từ config nếu không được truyền vào
        resolved_provider = provider or os.getenv("DEFAULT_EMB_PROVIDER")
        resolved_model = model_name or os.getenv("DEFAULT_EMB_MODEL")
        
        if not resolved_provider:
            raise ValueError("Embedding provider is not defined. Set DEFAULT_EMB_PROVIDER in .env or pass it explicitly.")
        if not resolved_model:
            raise ValueError("Embedding model name is not defined. Set DEFAULT_EMB_MODEL in .env or pass it explicitly.")
            
        provider_lower = resolved_provider.lower().strip()
        
        try:
            if provider_lower == "openai":
                from app.core.model.openai import get_emb as get_openai_emb
                return get_openai_emb(resolved_model, **kwargs)
                
            elif provider_lower == "google":
                from app.core.model.google import get_emb as get_google_emb
                return get_google_emb(resolved_model, **kwargs)
                
            elif provider_lower == "anthropic":
                from app.core.model.anthropic import get_emb as get_anthropic_emb
                return get_anthropic_emb(resolved_model, **kwargs)
                
            elif provider_lower == "huggingface":
                from app.core.model.huggingface import get_emb as get_huggingface_emb
                return get_huggingface_emb(resolved_model, **kwargs)
                
            else:
                raise ValueError(f"Unsupported Embedding provider: {resolved_provider}")
                
        except Exception as e:
            # Chống lỗi: Ghi nhận lỗi chi tiết khi giao tiếp với Embedding Provider bên ngoài
            raise RuntimeError(
                f"Failed to initialize Embedding for provider '{resolved_provider}' and model '{resolved_model}': {str(e)}"
            ) from e
