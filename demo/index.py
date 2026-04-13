from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

load_dotenv()

DEMO_ROOT = Path(__file__).parent
DOCS_DIR = DEMO_ROOT / "data"
CHROMA_DB_DIR = DEMO_ROOT / "chroma_db"
COLLECTION_NAME = "rag_lab_demo"

CHUNK_SIZE = 400
CHUNK_OVERLAP = 80


_st_model = None


def preprocess_document(raw_text: str, filepath: str) -> Dict[str, Any]:
    lines = raw_text.strip().split("\n")
    metadata = {
        "source": filepath,
        "section": "",
        "department": "unknown",
        "effective_date": "unknown",
        "access": "internal",
    }

    content_lines: List[str] = []
    header_done = False

    for line in lines:
        if not header_done:
            if line.startswith("Source:"):
                metadata["source"] = line.replace("Source:", "").strip()
            elif line.startswith("Department:"):
                metadata["department"] = line.replace("Department:", "").strip()
            elif line.startswith("Effective Date:"):
                metadata["effective_date"] = line.replace("Effective Date:", "").strip()
            elif line.startswith("Access:"):
                metadata["access"] = line.replace("Access:", "").strip()
            elif line.startswith("==="):
                header_done = True
                content_lines.append(line)
            elif line.strip() == "" or line.isupper():
                continue
            else:
                header_done = True
                content_lines.append(line)
        else:
            content_lines.append(line)

    cleaned_text = "\n".join(content_lines).strip()
    if not cleaned_text:
        cleaned_text = raw_text.strip()

    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)

    return {"text": cleaned_text, "metadata": metadata}


def _split_by_size(text: str, base_metadata: Dict[str, Any], section: str,
                   chunk_chars: int = CHUNK_SIZE * 4,
                   overlap_chars: int = CHUNK_OVERLAP * 4) -> List[Dict[str, Any]]:
    paragraphs = text.split("\n\n")
    chunks: List[Dict[str, Any]] = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= chunk_chars:
            current_chunk += para + "\n\n"
        else:
            if current_chunk.strip():
                chunks.append({
                    "text": current_chunk.strip(),
                    "metadata": {**base_metadata, "section": section},
                })
            current_chunk = current_chunk[-overlap_chars:] + para + "\n\n"

    if current_chunk.strip():
        chunks.append({
            "text": current_chunk.strip(),
            "metadata": {**base_metadata, "section": section},
        })

    return chunks


def chunk_document(doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    text = doc["text"]
    base_metadata = doc["metadata"].copy()
    chunks: List[Dict[str, Any]] = []

    sections = re.split(r"(===.*?===)", text)
    current_section = "General"
    current_section_text = ""

    for part in sections:
        if re.match(r"===.*?===", part):
            if current_section_text.strip():
                chunks.extend(_split_by_size(current_section_text.strip(), base_metadata, current_section))
            current_section = part.strip("= ").strip()
            current_section_text = ""
        else:
            current_section_text += part

    if current_section_text.strip():
        chunks.extend(_split_by_size(current_section_text.strip(), base_metadata, current_section))

    return chunks


def get_embedding(text: str) -> List[float]:
    provider = os.getenv("EMBEDDING_PROVIDER", "openai").lower()

    if provider == "local":
        global _st_model
        if _st_model is None:
            from sentence_transformers import SentenceTransformer
            model_name = os.getenv("LOCAL_EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
            _st_model = SentenceTransformer(model_name)
        return _st_model.encode(text).tolist()

    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.embeddings.create(input=text, model="text-embedding-3-small")
    return response.data[0].embedding


def build_index(docs_dir: Path = DOCS_DIR, db_dir: Path = CHROMA_DB_DIR, reset_collection: bool = True) -> None:
    import chromadb

    print(f"Đang build index từ: {docs_dir}")
    db_dir.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(db_dir))

    if reset_collection:
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"Đã xóa collection cũ: {COLLECTION_NAME}")
        except Exception:
            pass

    collection = client.get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})

    total_chunks = 0
    doc_files = sorted(docs_dir.glob("*.txt"))
    if not doc_files:
        print(f"Không tìm thấy file .txt trong {docs_dir}")
        return

    for filepath in doc_files:
        print(f"  Processing: {filepath.name}")
        raw_text = filepath.read_text(encoding="utf-8")
        doc = preprocess_document(raw_text, str(filepath))
        chunks = chunk_document(doc)

        for i, chunk in enumerate(chunks):
            chunk_id = f"{filepath.stem}_{i}"
            embedding = get_embedding(chunk["text"])
            collection.upsert(
                ids=[chunk_id],
                embeddings=[embedding],
                documents=[chunk["text"]],
                metadatas=[chunk["metadata"]],
            )
        total_chunks += len(chunks)

    print(f"\nHoàn thành! Tổng số chunks: {total_chunks}")


if __name__ == "__main__":
    build_index()
