from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(
        self,
        query: str,
        metadata_filter: dict | None = None,
        top_k: int = 3,
    ) -> str:
        if self.store.get_collection_size() == 0:
            return "Không tìm thấy thông tin trong cơ sở dữ liệu."

        if metadata_filter:
            results = self.store.search_with_filter(query, metadata_filter=metadata_filter, top_k=top_k)
        else:
            results = self.store.search(query, top_k=top_k)
        if not results:
            return "Không tìm thấy thông tin trong cơ sở dữ liệu."

        context_parts = []
        for index, result in enumerate(results, start=1):
            metadata = result.get("metadata", {})
            source = metadata.get("source_url", metadata.get("doc_id", result.get("id", "unknown")))
            context_parts.append(f"[{index}] Source: {source}\n{result['content']}")
        context = "\n\n".join(context_parts)
        prompt = (
            "Answer the question using only the provided context. "
            "Do not invent or infer information outside the context. "
            "Cite the relevant context number(s), such as [1] or [2], in your answer.\n\n"
            f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"
        )
        return self.llm_fn(prompt)
