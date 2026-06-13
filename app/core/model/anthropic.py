import os
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.embeddings import Embeddings

def get_llm(model_name: str, **kwargs) -> BaseChatModel:
    """
    Khởi tạo ChatAnthropic model.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is not set in environment variables.")
    
    temperature = kwargs.pop("temperature", 0.0)
    
    return ChatAnthropic(
        model=model_name,
        anthropic_api_key=api_key,
        temperature=temperature,
        **kwargs
    )

def get_emb(model_name: str, **kwargs) -> Embeddings:
    """
    Anthropic không cung cấp embedding API trực tiếp.
    """
    raise NotImplementedError(
        "Anthropic does not provide an embedding model API directly. "
        "Please use OpenAI, Google GenAI, or HuggingFace embeddings."
    )

