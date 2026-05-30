import os
import re
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")
COLLECTION_NAME = "novatech"
MAX_CHUNK_TOKENS = 500
OVERLAP_TOKENS = 50
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


def estimate_tokens(text: str) -> int:
    return len(text) // 4


def extract_metadata(content: str, filename: str) -> dict:
    version = "unknown"
    date = "unknown"

    version_match = re.search(r'\*\*Versão:\*\*\s*([\d.]+)', content)
    if version_match:
        version = version_match.group(1)

    date_match = re.search(
        r'\*\*(?:Última atualização|Data de emissão):\*\*\s*([\d/]+)', content
    )
    if date_match:
        parts = date_match.group(1).split("/")
        if len(parts) == 3:
            date = f"{parts[2]}-{parts[1]}-{parts[0]}"

    return {
        "source": filename,
        "doc_version": version,
        "doc_date": date,
        "source_quality": "native",
    }


def _is_table_line(line: str) -> bool:
    return bool(re.match(r'\s*\|', line))


def _split_section(title: str, content: str, base_meta: dict, idx_start: int) -> list[dict]:
    """Split one section into chunks, keeping table blocks intact."""
    chunks = []
    idx = idx_start
    lines = content.split("\n")
    current: list[str] = []
    table: list[str] = []
    in_table = False

    def flush_text(buf: list[str]) -> None:
        nonlocal idx
        text = "\n".join(buf).strip()
        if text:
            chunks.append({
                "text": text,
                "metadata": {**base_meta, "section": title, "chunk_index": idx},
            })
            idx += 1

    def flush_table(buf: list[str]) -> None:
        nonlocal idx
        text = "\n".join(buf).strip()
        if text:
            chunks.append({
                "text": text,
                "metadata": {**base_meta, "section": title, "chunk_index": idx},
            })
            idx += 1

    for line in lines:
        if _is_table_line(line):
            if not in_table:
                flush_text(current)
                current = []
                in_table = True
            table.append(line)
        else:
            if in_table:
                flush_table(table)
                table = []
                in_table = False
            current.append(line)
            if estimate_tokens("\n".join(current)) >= MAX_CHUNK_TOKENS:
                flush_text(current)
                # Carry overlap into next chunk
                overlap_chars = OVERLAP_TOKENS * 4
                joined = "\n".join(current)
                current = [joined[-overlap_chars:]] if len(joined) > overlap_chars else []

    if in_table:
        flush_table(table)
    else:
        flush_text(current)

    return chunks


def split_into_chunks(document: dict) -> list[dict]:
    """Divide a document into semantic chunks by Markdown section (## / ###)."""
    content = document["content"]
    base_meta = document["metadata"]

    header_re = re.compile(r'^#{2,3}\s+(.+)$', re.MULTILINE)
    sections: list[tuple[str, str]] = []
    last_end = 0
    current_title = "Introdução"

    for m in header_re.finditer(content):
        sec_content = content[last_end:m.start()].strip()
        if sec_content:
            sections.append((current_title, sec_content))
        current_title = m.group(1).strip()
        last_end = m.end()

    tail = content[last_end:].strip()
    if tail:
        sections.append((current_title, tail))

    all_chunks: list[dict] = []
    for title, sec_content in sections:
        new = _split_section(title, sec_content, base_meta, len(all_chunks))
        all_chunks.extend(new)

    return all_chunks


def load_documents(docs_dir: str) -> list[dict]:
    docs = []
    for filename in sorted(os.listdir(docs_dir)):
        if not filename.endswith(".md"):
            continue
        with open(os.path.join(docs_dir, filename), encoding="utf-8") as f:
            content = f.read()
        metadata = extract_metadata(content, filename)
        docs.append({"content": content, "metadata": metadata})
        print(f"  Carregado: {filename}  (v{metadata['doc_version']} | {metadata['doc_date']})")
    return docs


def ingest_to_chromadb(chunks: list[dict], collection_name: str = COLLECTION_NAME) -> None:
    ef = SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

    collection = client.create_collection(
        name=collection_name,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    ids = [f"chunk_{i}" for i in range(len(chunks))]
    texts = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        collection.add(
            ids=ids[i : i + batch_size],
            documents=texts[i : i + batch_size],
            metadatas=metadatas[i : i + batch_size],
        )
        print(f"  Lote {i // batch_size + 1}: {len(ids[i:i+batch_size])} chunks indexados")

    print(f"\nTotal: {len(chunks)} chunks na coleção '{collection_name}'")


if __name__ == "__main__":
    print("=== Ingestão NovaTech ===\n")

    print("1. Carregando documentos...")
    documents = load_documents(DOCS_DIR)
    print(f"   {len(documents)} documento(s) carregado(s).\n")

    print("2. Gerando chunks...")
    all_chunks: list[dict] = []
    for doc in documents:
        chunks = split_into_chunks(doc)
        all_chunks.extend(chunks)
        print(f"   {doc['metadata']['source']}: {len(chunks)} chunks")
    print(f"   Total: {len(all_chunks)} chunks\n")

    print("3. Indexando no ChromaDB...")
    ingest_to_chromadb(all_chunks)

    print("\nIngestão concluída.")
