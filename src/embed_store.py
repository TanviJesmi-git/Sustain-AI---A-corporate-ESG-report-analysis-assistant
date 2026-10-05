from sentence_transformers import SentenceTransformer
import chromadb

import uuid

MODEL_NAME = "all-MiniLM-L6-v2"

_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model



def create_session_collection():
    """Creates a fresh, in-memory (non-persistent) ChromaDB collection with a unique name,
    so repeated calls (e.g. on session reset) never collide with a previous collection."""
    client = chromadb.Client()
    unique_name = f"session_esg_reports_{uuid.uuid4().hex}"
    collection = client.create_collection(name=unique_name)
    return collection

def add_chunks(chunks: list[dict], collection, model):
    texts = [c["content"] for c in chunks]
    ids = [c["chunk_id"] for c in chunks]
    metadatas = [
        {
            "company": c["company"],
            "year": c["year"],
            "page_number": c["page_number"],
            "chunk_type": c["chunk_type"],
        }
        for c in chunks
    ]
    embeddings = model.encode(texts, show_progress_bar=False).tolist()
    collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
    return len(chunks)


def get_known_companies(collection) -> list[str]:
    all_data = collection.get(include=["metadatas"])
    companies = {m["company"] for m in all_data["metadatas"]}
    return sorted(companies)