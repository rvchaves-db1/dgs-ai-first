import os
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")
COLLECTION_NAME = "novatech"
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


def _doc_family(source: str) -> str:
    """'PROC-042-v2-frete-especial-revisado.md' → 'PROC-042'"""
    name = source.replace(".md", "")
    parts = name.split("-")
    return f"{parts[0]}-{parts[1]}" if len(parts) >= 2 else name


def _deduplicate_versions(chunks: list[dict]) -> list[dict]:
    """When multiple chunks from the same doc family appear, keep only the most recent."""
    best: dict[str, dict] = {}
    for chunk in chunks:
        source = chunk["metadata"].get("source", "")
        family = _doc_family(source)
        date = chunk["metadata"].get("doc_date", "0000-00-00")
        if family not in best or date > best[family]["metadata"].get("doc_date", "0000-00-00"):
            best[family] = chunk

    result = list(best.values())
    result.sort(key=lambda x: x["similarity_score"], reverse=True)
    return result


def search(
    query: str,
    collection_name: str = COLLECTION_NAME,
    n_results: int = 5,
    deduplicate_versions: bool = True,
) -> list[dict]:
    """
    Returns up to n_results chunks ordered by cosine similarity (descending).
    Each item: {'text': str, 'metadata': dict, 'similarity_score': float}
    """
    ef = SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(name=collection_name, embedding_function=ef)

    fetch_n = min(n_results * 3 if deduplicate_versions else n_results, collection.count())

    raw = collection.query(
        query_texts=[query],
        n_results=fetch_n,
        include=["documents", "metadatas", "distances"],
    )

    chunks = [
        {
            "text": doc,
            "metadata": meta,
            # cosine space: distance = 1 - similarity → similarity = 1 - distance
            "similarity_score": round(1.0 - dist, 4),
        }
        for doc, meta, dist in zip(
            raw["documents"][0],
            raw["metadatas"][0],
            raw["distances"][0],
        )
    ]

    if deduplicate_versions:
        chunks = _deduplicate_versions(chunks)

    return chunks[:n_results]


if __name__ == "__main__":
    import sys

    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Qual o prazo de devolução?"
    print(f"Query: {query}\n")
    for i, r in enumerate(search(query), 1):
        print(f"[{i}] score={r['similarity_score']:.4f} | {r['metadata']['source']} — {r['metadata']['section']}")
        print(f"     {r['text'][:200]}\n")
