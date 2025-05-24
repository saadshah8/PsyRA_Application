import os
import numpy as np
from tqdm import tqdm
from typing import List
import tiktoken
from tenacity import retry, stop_after_attempt, wait_exponential
from langchain_community.embeddings import JinaEmbeddings

# Load from env
EMBEDDINGS_MODEL = os.getenv('EMBEDDINGS_MODEL', 'jina-embeddings-v3')
JINA_API_KEY = os.getenv("JINA_API_KEY")

# Tokenizer (cl100k_base is used for OpenAI/Jina-compatible models)
tokenizer = tiktoken.get_encoding("cl100k_base")

def clip_text_to_tokens(text: str, max_tokens: int = 2048) -> str:
    tokens = tokenizer.encode(text)
    return tokenizer.decode(tokens[:max_tokens])

class JinaEmbeddingWrapper:
    """
    Wrapper for Jina Embeddings v3 via LangChain with:
    - Batch processing
    - Token-safe truncation (2048 tokens max)
    - Retry logic
    """

    def __init__(self, api_key: str = None, batch_size: int = 500):
        self.api_key = api_key or JINA_API_KEY
        self.batch_size = min(batch_size, 2048)  # Hard limit
        self.model = JinaEmbeddings(
            jina_api_key=self.api_key,
            model_name=EMBEDDINGS_MODEL,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def embed_documents(self, texts: List[str]) -> np.ndarray:
        """Embed a list of documents safely in batches"""
        embeddings = []
        for i in tqdm(range(0, len(texts), self.batch_size), desc="Embedding"):
            batch = texts[i:i + self.batch_size]
            batch_clipped = [clip_text_to_tokens(t) for t in batch]
            batch_embeddings = self.model.embed_documents(batch_clipped)
            embeddings.extend(batch_embeddings)
        return np.array(embeddings)

    def embed_query(self, query: str) -> List[float]:
        return self.model.embed_query(clip_text_to_tokens(query))
