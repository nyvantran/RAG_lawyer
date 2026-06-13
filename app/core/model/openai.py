import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.embeddings import Embeddings

def get_llm(model_name: str, **kwargs) -> BaseChatModel:
    """
    Khởi tạo ChatOpenAI model.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set in environment variables.")
    
    temperature = kwargs.pop("temperature", 0.0)
    
    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        temperature=temperature,
        **kwargs
    )

def get_emb(model_name: str, **kwargs) -> Embeddings:
    """
    Khởi tạo OpenAIEmbeddings model.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set in environment variables.")
    
    return OpenAIEmbeddings(
        model=model_name,
        api_key=api_key,
        **kwargs
    )

