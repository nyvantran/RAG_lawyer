import os
from typing import Optional
from langchain_core.language_models.chat_models import BaseChatModel
from dotenv import load_dotenv

# Tải biến môi trường
load_dotenv()

class LLMFactory:
    """
    LLMFactory quản lý khởi tạo các đối tượng LLM dựa trên Provider và Model Name.
    Áp dụng Factory Pattern để chuẩn hóa việc tạo đối tượng kế thừa từ BaseChatModel.
    """
    
    @classmethod
    def get_llm(
        cls, 
        provider: Optional[str] = None, 
        model_name: Optional[str] = None, 
        **kwargs
    ) -> BaseChatModel:
        """
        Khởi tạo và trả về instance của LLM Model.
        
        Args:
            provider: Tên nhà cung cấp (openai, google, anthropic). 
                      Nếu không truyền, lấy mặc định từ DEFAULT_LLM_PROVIDER.
            model_name: Tên model cụ thể (ví dụ: gpt-4o, gemini-2.5-flash).
                        Nếu không truyền, lấy mặc định từ DEFAULT_LLM_MODEL.
            **kwargs: Các tham số bổ sung khác (ví dụ: temperature, max_tokens,...).
            
        Returns:
            Một đối tượng kế thừa từ BaseChatModel.
        """
        # Load lại env để đảm bảo cập nhật các biến môi trường mới nhất
        load_dotenv()
        
        # Lấy giá trị mặc định từ config nếu không được truyền vào
        resolved_provider = provider or os.getenv("DEFAULT_LLM_PROVIDER")
        resolved_model = model_name or os.getenv("DEFAULT_LLM_MODEL")
        
        if not resolved_provider:
            raise ValueError("LLM provider is not defined. Set DEFAULT_LLM_PROVIDER in .env or pass it explicitly.")
        if not resolved_model:
            raise ValueError("LLM model name is not defined. Set DEFAULT_LLM_MODEL in .env or pass it explicitly.")
            
        provider_lower = resolved_provider.lower().strip()
        
        try:
            if provider_lower == "openai":
                from app.core.model.openai import get_llm as get_openai_llm
                return get_openai_llm(resolved_model, **kwargs)
                
            elif provider_lower == "google":
                from app.core.model.google import get_llm as get_google_llm
                return get_google_llm(resolved_model, **kwargs)
                
            elif provider_lower == "anthropic":
                from app.core.model.anthropic import get_llm as get_anthropic_llm
                return get_anthropic_llm(resolved_model, **kwargs)
                
            else:
                raise ValueError(f"Unsupported LLM provider: {resolved_provider}")
                
        except Exception as e:
            # Chống lỗi: Ghi nhận lỗi chi tiết khi giao tiếp với LLM Provider bên ngoài
            raise RuntimeError(
                f"Failed to initialize LLM for provider '{resolved_provider}' and model '{resolved_model}': {str(e)}"
            ) from e
