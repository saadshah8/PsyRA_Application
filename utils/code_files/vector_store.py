import os
import faiss
import numpy as np
import pandas as pd
from langchain_community.embeddings import JinaEmbeddings
from langchain.vectorstores import FAISS
from dotenv import load_dotenv
import tiktoken
import JinaEmbeddingWrapper
from langchain.docstore.in_memory import InMemoryDocstore
from langchain.schema import Document

load_dotenv()

# Get Jina API details and file paths
JINA_API_KEY = os.getenv('JINA_API_KEY')
JINA_API_URL = os.getenv('JINA_API_URL')
CHUNKS_CSV_PATH = os.getenv('CHUNKS_CSV_PATH', 'dsm_chunks.csv')  # Path to chunked CSV from Part 1
FAISS_INDEX_PATH = os.getenv('FAISS_INDEX_PATH', 'faiss_index')  # Folder name only
METADATA_CSV_PATH = os.getenv('METADATA_CSV_PATH', 'faiss_metadata.csv')

# Jina model name (optional override)
EMBEDDINGS_MODEL = os.getenv('EMBEDDINGS_MODEL', 'jina-embeddings-v3')


def get_jina_embeddings(texts):
    embedder = JinaEmbeddingWrapper.JinaEmbeddingWrapper(api_key=JINA_API_KEY)
    return embedder.embed_documents(texts)


# === FAISS Index Creation ===
def create_faiss_index(embeddings, metadata, faiss_index_path, metadata_csv_path):
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)  #using flat L2 Indexing for simplicity and small chunks
    index.add(embeddings)

    docs = [
        Document(
            page_content=metadata[i].get("text", ""),
            metadata={k: v for k, v in metadata[i].items() if k != "text"}
        )
        for i in range(len(metadata))
    ]

    # Create FAISS store using LangChain
    faiss_store = FAISS.from_documents(docs, embedding=JinaEmbeddingWrapper.JinaEmbeddingWrapper(api_key=JINA_API_KEY))

    # Save FAISS index using save_local (writes .faiss and .pkl)
    faiss_store.save_local(faiss_index_path)

    metadata_df = pd.DataFrame(metadata)
    metadata_df.to_csv(metadata_csv_path, index=False)

    print(f"FAISS index saved to {faiss_index_path}")
    print(f"Metadata saved to {metadata_csv_path}")
    return faiss_store.index


# === Generate and Index ===
def generate_and_index_embeddings(chunks, faiss_index_path=FAISS_INDEX_PATH, metadata_csv_path=METADATA_CSV_PATH):
    texts = [chunk["text"] for chunk in chunks]
    metadata = [
        {
            "text": chunk["text"],  # Include text for saving
            "chunk_id": chunk["chunk_id"],
            "section_title": chunk["section_title"],
            "topic": chunk["topic"],
            "book_name": chunk.get("book_name", ""),
            "book_type": chunk.get("book_type", ""),
            "page_number": chunk.get("page_number", None),
        }
        for chunk in chunks
    ]

    print("Generating embeddings via Jina API...")
    embeddings = get_jina_embeddings(texts)

    print("Creating FAISS index...")
    index = create_faiss_index(embeddings, metadata, faiss_index_path, metadata_csv_path)
    return index


# === Load from CSV and Run ===
if __name__ == "__main__":
    print(f"Loading chunks from: {CHUNKS_CSV_PATH}")
    df = pd.read_csv(CHUNKS_CSV_PATH)

    # Ensure required columns exist
    required_columns = {"text", "chunk_id", "section_title", "topic"}
    if not required_columns.issubset(df.columns):
        raise ValueError(f"CSV is missing required columns: {required_columns - set(df.columns)}")

    # Convert to list of dicts
    chunks = df.to_dict(orient="records")

    # Generate and index
    generate_and_index_embeddings(chunks)
