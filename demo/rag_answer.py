from __future__ import annotations

import os
from typing import Any, Dict, List

import chromadb
from dotenv import load_dotenv
from openai import OpenAI

from index import CHROMA_DB_DIR, COLLECTION_NAME, get_embedding

load_dotenv()

TOP_K_SEARCH = 10
TOP_K_SELECT = 3
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")


def retrieve_dense(query: str, top_k: int = TOP_K_SEARCH) -> List[Dict[str, Any]]:
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
    collection = client.get_collection(COLLECTION_NAME)

    query_embedding = get_embedding(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    formatted_results: List[Dict[str, Any]] = []
    if results.get("documents"):
        for i in range(len(results["documents"][0])):
            score = 1 - results["distances"][0][i]
            metadata = results["metadatas"][0][i] or {}
            if results.get("ids"):
                metadata = {**metadata, "id": results["ids"][0][i]}
            formatted_results.append({
                "text": results["documents"][0][i],
                "metadata": metadata,
                "score": score,
            })

    return formatted_results


def retrieve_sparse(query: str, top_k: int = TOP_K_SEARCH) -> List[Dict[str, Any]]:
    from rank_bm25 import BM25Okapi

    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
    collection = client.get_collection(COLLECTION_NAME)

    payload = collection.get(include=["documents", "metadatas"])
    all_ids = payload["ids"]
    all_docs = payload["documents"]
    all_metas = payload["metadatas"]

    corpus = [doc or "" for doc in all_docs]
    tokenized_corpus = [doc.lower().split() for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)

    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

    results: List[Dict[str, Any]] = []
    for idx in top_indices:
        metadata = all_metas[idx] or {}
        metadata = {**metadata, "id": all_ids[idx]}
        results.append({
            "text": all_docs[idx],
            "metadata": metadata,
            "score": scores[idx],
        })
    return results


def retrieve_hybrid(query: str, top_k: int = TOP_K_SEARCH,
                    dense_weight: float = 0.6, sparse_weight: float = 0.4) -> List[Dict[str, Any]]:
    dense_results = retrieve_dense(query, top_k=top_k * 2)
    sparse_results = retrieve_sparse(query, top_k=top_k * 2)

    dense_ranks = {res["metadata"].get("id", f"dense_{rank}"): rank for rank, res in enumerate(dense_results, 1)}
    sparse_ranks = {res["metadata"].get("id", f"sparse_{rank}"): rank for rank, res in enumerate(sparse_results, 1)}

    all_doc_ids = set(dense_ranks.keys()) | set(sparse_ranks.keys())
    rrf_scores: Dict[str, float] = {}
    for doc_id in all_doc_ids:
        dense_rank = dense_ranks.get(doc_id, float("inf"))
        sparse_rank = sparse_ranks.get(doc_id, float("inf"))
        rrf = dense_weight * (1 / (60 + dense_rank)) + sparse_weight * (1 / (60 + sparse_rank))
        rrf_scores[doc_id] = rrf

    sorted_doc_ids = sorted(all_doc_ids, key=lambda x: rrf_scores[x], reverse=True)
    top_doc_ids = sorted_doc_ids[:top_k]

    top_chunks: List[Dict[str, Any]] = []
    for doc_id in top_doc_ids:
        if doc_id in dense_ranks:
            chunk = next(res for res in dense_results if res["metadata"].get("id") == doc_id)
        else:
            chunk = next(res for res in sparse_results if res["metadata"].get("id") == doc_id)
        top_chunks.append(chunk)
    return top_chunks


def build_context_block(chunks: List[Dict[str, Any]]) -> str:
    context_parts: List[str] = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata", {}) or {}
        source = meta.get("source", "unknown")
        section = meta.get("section", "")
        score = chunk.get("score", 0)
        text = chunk.get("text", "")

        header = f"[{i}] {source}"
        if section:
            header += f" | {section}"
        if score and score > 0:
            header += f" | score={score:.2f}"

        context_parts.append(f"{header}\n{text}")

    return "\n\n".join(context_parts)


def build_grounded_prompt(query: str, context_block: str) -> str:
    return f"""Answer only from the retrieved context below.
If the context is insufficient to answer the question, say you do not know and do not make up information.
Cite the source field (in brackets like [1]) when possible.
Keep your answer short, clear, and factual.
Respond in the same language as the question.

Question: {query}

Context:
{context_block}

Answer:"""


def call_llm(prompt: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Thiếu OPENAI_API_KEY trong file .env")

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "Bạn là trợ lý học tập hỗ trợ sinh viên. Luôn trả lời trung thực dựa trên tài liệu được cung cấp."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_tokens=512,
    )
    return response.choices[0].message.content.strip()


def rag_answer(query: str,
               retrieval_mode: str = "dense",
               top_k_search: int = TOP_K_SEARCH,
               top_k_select: int = TOP_K_SELECT,
               use_rerank: bool = False,
               verbose: bool = False) -> Dict[str, Any]:
    config = {
        "retrieval_mode": retrieval_mode,
        "top_k_search": top_k_search,
        "top_k_select": top_k_select,
        "use_rerank": use_rerank,
    }

    if retrieval_mode == "dense":
        candidates = retrieve_dense(query, top_k=top_k_search)
    elif retrieval_mode == "sparse":
        candidates = retrieve_sparse(query, top_k=top_k_search)
    elif retrieval_mode == "hybrid":
        candidates = retrieve_hybrid(query, top_k=top_k_search)
    else:
        candidates = retrieve_dense(query, top_k=top_k_search)

    selected_chunks = candidates[:top_k_select]
    context_block = build_context_block(selected_chunks)
    prompt = build_grounded_prompt(query, context_block)

    if verbose:
        print(f"\n[RAG DEBUG] Query: {query}")
        print(f"[RAG DEBUG] Sources found: {[c['metadata'].get('source') for c in selected_chunks]}")

    answer = call_llm(prompt)
    sources = list({c["metadata"].get("source", "unknown") for c in selected_chunks})

    return {
        "query": query,
        "answer": answer,
        "sources": sources,
        "chunks_used": selected_chunks,
        "config": config,
    }
