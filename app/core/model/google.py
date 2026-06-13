import os
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.embeddings import Embeddings

def get_llm(model_name: str, **kwargs) -> BaseChatModel:
    """
    Khởi tạo ChatGoogleGenerativeAI model.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is not set in environment variables.")
    
    temperature = kwargs.pop("temperature", 0.0)
    
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=temperature,
        **kwargs
    )

def get_emb(model_name: str, **kwargs) -> Embeddings:
    """
    Khởi tạo GoogleGenAIEmbeddings model.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is not set in environment variables.")
    
    return GoogleGenerativeAIEmbeddings(
        model=model_name,
        **kwargs
    )

