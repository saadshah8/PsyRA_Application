import os
import pandas as pd
from langchain_community.embeddings import JinaEmbeddings
from langchain.retrievers import EnsembleRetriever, ContextualCompressionRetriever
from langchain.schema import Document
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_cohere import CohereRerank

# Load environment
load_dotenv()

# Load paths from .env
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "faiss_index")
CHUNKS_CSV_PATH = os.getenv("CHUNKS_CSV_PATH", "dsm_chunks.csv")
JINA_API_KEY = os.getenv("JINA_API_KEY")

def filter_and_sort_documents(documents, score_key="relevance_score", threshold=0.01, top_k=3):
    """Filter by score, sort descending, return top_k."""
    filtered = [
        doc for doc in documents
        if score_key in doc.metadata and doc.metadata[score_key] >= threshold
    ]
    sorted_docs = sorted(filtered, key=lambda d: d.metadata[score_key], reverse=True)
    return sorted_docs[:top_k]

# Load metadata and create LangChain-compatible docs
script_dir = os.path.dirname(os.path.abspath(__file__))
# Move up to App directory and then to utils
app_dir = os.path.dirname(os.path.dirname(script_dir))  # Up to App from code_files
csv_path = os.path.join(app_dir, CHUNKS_CSV_PATH)
# print(f"Attempting to load CSV from: {csv_path}")  # Debug print
df = pd.read_csv(csv_path)
if "text" not in df.columns:
    raise ValueError("CSV file missing 'text' column. Load correct chunk file.")

docs = [
    Document(
        page_content=row["text"],
        metadata={
            "chunk_id": row.get("chunk_id"),
            "section_title": row.get("section_title"),
            "topic": row.get("topic"),
            "book_name": row.get("book_name", ""),
            "book_type": row.get("book_type", ""),
            "page_number": row.get("page_number", None),
        }
    )
    for _, row in df.iterrows()
]

# === Load FAISS vector index ===
embedding_model = JinaEmbeddings(
    model_name="jina-embeddings-v3",
    jina_api_key=JINA_API_KEY
)
faiss_store = FAISS.load_local(
    folder_path=os.path.join(app_dir, os.path.splitext(FAISS_INDEX_PATH)[0]),  # Adjust path to App/utils/faiss_index
    embeddings=embedding_model,
    index_name="index",
    allow_dangerous_deserialization=True
)

# === Setup BM25 Retriever (metadata-based) ===
bm25 = BM25Retriever.from_documents(docs)
bm25.k = 5

# === Setup Hybrid Retriever ===
hybrid_retriever = EnsembleRetriever(
    retrievers=[faiss_store.as_retriever(search_kwargs={"k": 5}), bm25],
    weights=[0.7, 0.3]
)

# === Metadata Filtering (example) ===
def get_filtered_retriever(topic=None, section_title=None):
    filters = {}
    if topic:
        filters["topic"] = topic
    if section_title:
        filters["section_title"] = section_title
    return faiss_store.as_retriever(
        search_kwargs={"k": 5, "filter": filters}
    )

# === Optional Re-ranking with Cohere ===
cohere_key = os.getenv("COHERE_API_KEY")
if cohere_key:
    reranker = CohereRerank(top_n=5, cohere_api_key=cohere_key, model="rerank-english-v3.0")
    retriever_with_rerank = ContextualCompressionRetriever(
        base_compressor=reranker,
        base_retriever=hybrid_retriever
    )
else:
    retriever_with_rerank = hybrid_retriever

# === Final Retriever for RAG ===
rag_retriever = retriever_with_rerank

# === Example Usage ===
if __name__ == "__main__":
    query = "What is the CBT technique for panic disorder?"
    results = rag_retriever.invoke(query)
    top_results = filter_and_sort_documents(results)
    for i, doc in enumerate(top_results):
        print(f"\n--- Top Document {i+1} ---")
        print(doc.page_content[:500])
        print("Metadata:", doc.metadata)
    print(f"\nRetrieved {len(results)} documents, showing top {len(top_results)} after filtering.")