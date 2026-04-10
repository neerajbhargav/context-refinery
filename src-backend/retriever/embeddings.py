"""
ContextRefinery — Custom ChromaDB Embedding Functions
Wraps LangChain embedding providers to work directly with ChromaDB's
EmbeddingFunction interface.
"""

from typing import cast, List
import logging
from chromadb.api.types import Documents, Embeddings as ChromaEmbeddings, EmbeddingFunction
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_ollama import OllamaEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings

from config import settings

logger = logging.getLogger(__name__)

class LangChainEmbeddingWrapper(EmbeddingFunction):
    """
    Wraps a LangChain Embeddings class as a ChromaDB EmbeddingFunction.
    """
    def __init__(self, langchain_embeddings):
        self._lc_embeddings = langchain_embeddings

    def __call__(self, input: Documents) -> ChromaEmbeddings:
        """Embed the input documents using the wrapped LangChain provider."""
        # LangChain's embed_documents returns List[List[float]]
        # ChromaDB expects the same structure
        return cast(ChromaEmbeddings, self._lc_embeddings.embed_documents(input))


def get_embedding_function() -> EmbeddingFunction:
    """
    Factory function to create the appropriate embedding function 
    based on the application settings.
    """
    provider = settings.EMBEDDING_PROVIDER
    
    try:
        if provider == "google":
            if not settings.GOOGLE_API_KEY:
                logger.warning("GOOGLE_API_KEY not set. Falling back to local embeddings.")
                return get_local_embedding_function()
            
            logger.info(f"Using Google Embeddings: {settings.GOOGLE_EMBEDDING_MODEL}")
            lc_embeddings = GoogleGenerativeAIEmbeddings(
                model=settings.GOOGLE_EMBEDDING_MODEL,
                google_api_key=settings.GOOGLE_API_KEY,
            )
            return LangChainEmbeddingWrapper(lc_embeddings)
            
        elif provider == "ollama":
            logger.info(f"Using Ollama Embeddings: {settings.OLLAMA_EMBEDDING_MODEL}")
            lc_embeddings = OllamaEmbeddings(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.OLLAMA_EMBEDDING_MODEL,
            )
            return LangChainEmbeddingWrapper(lc_embeddings)
            
        else: # sentence-transformers or fallback
            return get_local_embedding_function()
            
    except Exception as e:
        logger.error(f"Failed to initialize '{provider}' embeddings: {e}. Falling back to local.")
        return get_local_embedding_function()


def get_local_embedding_function() -> EmbeddingFunction:
    """Create a local sentence-transformers embedding function."""
    logger.info(f"Using Local Embeddings: {settings.LOCAL_EMBEDDING_MODEL}")
    lc_embeddings = HuggingFaceEmbeddings(
        model_name=settings.LOCAL_EMBEDDING_MODEL,
        cache_folder=str(settings.DATA_DIR / "models"),
    )
    return LangChainEmbeddingWrapper(lc_embeddings)
