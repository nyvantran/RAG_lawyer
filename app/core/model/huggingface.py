import torch
from langchain_core.embeddings import Embeddings


def get_emb(model_name: str, **kwargs) -> Embeddings:
    """
    Khởi tạo HuggingFaceEmbeddings model.
    """
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError:
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
        except ImportError as e:
            raise ImportError(
                "Could not import HuggingFaceEmbeddings. "
                "Please install langchain-huggingface or sentence-transformers to use HuggingFace embeddings."
            ) from e

    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=
        {
            "device": "cuda" if torch.cuda.is_available() else "cpu",
        },
        **kwargs
    )
