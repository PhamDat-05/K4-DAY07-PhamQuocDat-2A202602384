from __future__ import annotations

import sys
from contextlib import redirect_stdout
from pathlib import Path

from src.chunking import FixedSizeChunker
from src.models import Document
from src.store import EmbeddingStore


DATA_DIR = Path(__file__).parent / "data" / "shopee-policies"
OUTPUT_PATH = Path(__file__).parent / "ket_qua_benchmark.txt"

QUERIES = [
    "Đối với đơn hàng do Người bán tự vận chuyển, nếu Người mua không bấm \"Đã nhận được hàng\", thời hạn tối đa để gửi yêu cầu Trả hàng/Hoàn tiền là bao lâu kể từ lúc đơn hàng được cập nhật \"Lấy hàng thành công\"?",
    "Ba điều kiện bảo hành cơ bản mà Shopee khuyến cáo Người Mua cần đáp ứng là gì?",
    "Khi đăng bán sản phẩm trên Shopee, Người Bán phải điền những thông tin nào liên quan đến nguồn gốc và bảo hành?",
    "Với tranh chấp không phải khiếu nại Trả hàng/Hoàn tiền, Shopee đưa ra hướng giải quyết trong bao lâu sau khi nhận đủ thông tin/tài liệu?",
    "Khi phát sinh nhu cầu bảo hành sản phẩm trên Shopee thì cần làm gì?",
]

GOLD_CRITERIA = [
    {
        "docs": {"shopee-terms-service-warranty-general", "shopee-return-refund-rights-buyer"},
        "keywords": ["20 ngày", "lấy hàng thành công"],
    },
    {
        "docs": {"shopee-warranty-electronic-service", "shopee-brand-warranty-coverage"},
        "keywords": ["thời hạn bảo hành", "tem/phiếu", "lỗi kỹ thuật"],
    },
    {
        "docs": {"shopee-seller-dispute-and-penalty", "shopee-prohibited-items-policy"},
        "keywords": ["nguồn gốc", "chế độ bảo hành"],
    },
    {
        "docs": {"shopee-seller-dispute-and-penalty"},
        "keywords": ["07 ngày", "ngày làm việc"],
    },
    {
        "docs": {"shopee-seller-return-warranty-fulfillment"},
        "keywords": ["tiếp nhận bảo hành", "chính sách bảo hành"],
    },
]


def parse_markdown(path: Path) -> tuple[dict[str, str], str]:
    """Read YAML-like frontmatter and body from one Markdown policy file."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text.strip()

    parts = text.split("---", 2)
    if len(parts) != 3:
        return {}, text.strip()

    metadata: dict[str, str] = {}
    for line in parts[1].splitlines():
        key, separator, value = line.partition(":")
        if separator:
            metadata[key.strip()] = value.strip().strip("'\"")
    return metadata, parts[2].strip()


def load_documents() -> list[Document]:
    chunker = FixedSizeChunker(chunk_size=500, overlap=50)
    documents: list[Document] = []

    for path in sorted(DATA_DIR.glob("*.md")):
        frontmatter, body = parse_markdown(path)
        for index, chunk in enumerate(chunker.chunk(body)):
            documents.append(
                Document(
                    id=f"{path.stem}#{index}",
                    content=chunk,
                    metadata={**frontmatter, "doc_id": path.stem},
                )
            )
    return documents


def print_results(query_number: int, query: str, results: list[dict], filter_value: dict | None) -> None:
    print(f"\n=== Query {query_number} ===")
    print(query)
    print(f"Filter: {filter_value}" if filter_value else "Filter: none")
    if not results:
        print("No results.")
        return

    for rank, result in enumerate(results, start=1):
        metadata = result.get("metadata", {})
        doc_id = metadata.get("doc_id", result.get("id", "unknown"))
        preview = " ".join(result.get("content", "").split())[:150]
        print(f"{rank}. score={result['score']:.6f} doc_id={doc_id} content={preview}")


def score_results(results: list[dict], criteria: dict) -> int:
    """Award 2/1/0 points based on ranked gold document and keyword hits."""
    for rank, result in enumerate(results[:3], start=1):
        metadata = result.get("metadata", {})
        doc_id = metadata.get("doc_id", result.get("id", ""))
        content = result.get("content", "").casefold()
        if doc_id in criteria["docs"] and any(keyword.casefold() in content for keyword in criteria["keywords"]):
            return 2 if rank == 1 else 1
    return 0


class Tee:
    def __init__(self, *streams) -> None:
        self.streams = streams

    def write(self, text: str) -> int:
        for stream in self.streams:
            stream.write(text)
            stream.flush()
        return len(text)

    def flush(self) -> None:
        for stream in self.streams:
            stream.flush()


def run_benchmark() -> None:
    documents = load_documents()
    store = EmbeddingStore()
    store.add_documents(documents)
    print(f"Tong so chunk da nap vao store: {store.get_collection_size()}")
    backend = getattr(store._embedding_fn, "_backend_name", store._embedding_fn.__class__.__name__)
    print(f"Embedding backend: {backend}")

    scores: list[int] = []

    for query_number, query in enumerate(QUERIES, start=1):
        if query_number == 5:
            filtered_results = store.search_with_filter(
                query,
                metadata_filter={"audience": "seller"},
                top_k=3,
            )
            print_results(query_number, query, filtered_results, {"audience": "seller"})
            filtered_score = score_results(filtered_results, GOLD_CRITERIA[query_number - 1])
            scores.append(filtered_score)
            print(f"Q5 Filtered score: {filtered_score}/2")

            unfiltered_results = store.search_with_filter(query, metadata_filter=None, top_k=3)
            print(f"\n=== Query 5 A/B comparison: unfiltered ===")
            print_results(query_number, query, unfiltered_results, None)
            unfiltered_score = score_results(unfiltered_results, GOLD_CRITERIA[query_number - 1])
            print(f"Q5 Unfiltered score: {unfiltered_score}/2")
        else:
            results = store.search(query, top_k=3)
            print_results(query_number, query, results, None)
            score = score_results(results, GOLD_CRITERIA[query_number - 1])
            scores.append(score)
            print(f"Q{query_number} score: {score}/2")

    print("\n=== CP6 Summary ===")
    print(f"FixedSizeChunker retrieval score: {sum(scores)}/10")
    print(f"Embedding backend status: {backend}")


def main() -> None:
    with OUTPUT_PATH.open("w", encoding="utf-8") as output_file:
        with redirect_stdout(Tee(sys.stdout, output_file)):
            run_benchmark()
    print(f"\nBenchmark output saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
