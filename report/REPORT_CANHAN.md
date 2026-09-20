# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Phạm Quốc Đạt
**Nhóm:** Nova
**Ngày:** 20/09/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao phản ánh góc giữa hai vector embedding tiến về 0 độ, nghĩa là hai vector cùng hướng và văn bản có sự đồng nhất cao về mặt ngữ nghĩa, độc lập với độ dài hoặc từ vựng bề mặt.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Người mua có thể yêu cầu trả hàng nếu kiện hàng bị biến dạng lúc vận chuyển."
- Câu B: "Khách hàng được quyền hoàn trả khi bưu phẩm gặp sự cố móp méo trong quá trình giao nhận."
- Tại sao tương đồng: Hai câu dùng từ ngữ khác nhau nhưng cùng diễn đạt quyền trả hàng của người mua khi kiện hàng bị hư hỏng hoặc biến dạng trong quá trình vận chuyển.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Thời hạn bảo hành thiết bị điện tử chính hãng là 12 tháng kể từ ngày kích hoạt."
- Câu B: "Chính sách chiết khấu voucher áp dụng tối đa 50.000 đồng cho đơn từ 200.000 đồng."
- Tại sao khác: Hai câu nói về hai chủ đề không liên quan, một câu về thời hạn bảo hành thiết bị điện tử và một câu về điều kiện chiết khấu voucher.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid đo khoảng cách hình học theo độ dài vector nên có thể bị ảnh hưởng khi so sánh các văn bản có độ dài khác nhau. Cosine similarity chuẩn hóa độ dài vector và chỉ đo góc định hướng ngữ nghĩa, phù hợp với text embedding; khi các vector đã được chuẩn hóa ($||v|| = 1$), dot product bằng đúng cosine similarity.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Áp dụng công thức:
> ceil((độ_dài - overlap) / (chunk_size - overlap)) = ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = 23 chunks
>
> Đã kiểm chứng trực tiếp bằng code `len(FixedSizeChunker(chunk_size=500, overlap=50).chunk('a'*10000))`, kết quả là **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi `overlap=100`, số chunk là $\left\lceil(10000 - 100) / (500 - 100)\right\rceil = \left\lceil9900 / 400\right\rceil = 25$, tăng thêm 2 chunk. Đôi khi cần overlap lớn hơn dù tốn thêm chunk vì nó tạo vùng đệm ngữ cảnh, ngăn câu văn hoặc điều khoản bảo hành bị cắt giữa chừng và giúp embedding/LLM giữ được liên kết ngữ nghĩa giữa hai chunk kế tiếp.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi dùng regex `(?<=[.!?])(?: |\n)+` để tách văn bản tại khoảng trắng hoặc xuống dòng đứng sau các dấu kết thúc câu `.`, `!`, `?`. Mỗi câu được `strip()` để loại bỏ khoảng trắng thừa, bỏ qua câu rỗng, sau đó gom tối đa `max_sentences_per_chunk` câu vào một chunk và nối chúng bằng một khoảng trắng. Với văn bản rỗng, hàm trả về danh sách rỗng; nếu tham số số câu nhỏ hơn 1 thì được chuẩn hóa thành 1 để tránh tạo chunk không hợp lệ.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán ưu tiên lần lượt các dấu phân cách `\n\n`, `\n`, `. `, dấu cách và cuối cùng là chuỗi rỗng; văn bản được tách theo dấu phân cách hiện tại rồi đệ quy xử lý các phần nhỏ hơn với các dấu phân cách còn lại. Base case là khi phần văn bản không vượt quá `chunk_size`, khi đó trả về ngay một chunk sau khi loại bỏ khoảng trắng đầu/cuối; nếu không còn dấu phân cách, hàm cắt trực tiếp theo kích thước cố định. Sau khi tách, các mảnh liên tiếp vẫn được ghép lại nếu tổng độ dài (kể cả dấu phân cách) không vượt quá `chunk_size`, nhờ đó hạn chế tạo ra các chunk quá ngắn.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Tôi lưu mỗi `Document` thành một record trong danh sách trong bộ nhớ, gồm `id`, nội dung, bản sao metadata và embedding được tạo từ nội dung bằng hàm embedding đã truyền vào (mặc định là mock embedder). Khi tìm kiếm, hệ thống tạo embedding cho query, tính tích vô hướng giữa query embedding và embedding của từng record, sắp xếp điểm giảm dần và trả về tối đa `top_k` kết quả. Hàm `compute_similarity` riêng dùng cosine similarity cho bài toán đo độ tương tự, còn đường tìm kiếm hiện tại dùng dot product để xếp hạng.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` lọc trước: chỉ giữ các record có toàn bộ cặp khóa-giá trị khớp với `metadata_filter`, rồi mới embedding query và xếp hạng các ứng viên còn lại; nếu không có bộ lọc thì tìm trên toàn bộ store. `delete_document` xóa tất cả chunk có metadata `doc_id` bằng `doc_id` được yêu cầu, trả về `True` nếu có record bị xóa và `False` nếu không tìm thấy tài liệu tương ứng. Vì một tài liệu có thể gồm nhiều chunk, cách xóa theo metadata giúp loại bỏ toàn bộ các chunk của tài liệu đó.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Agent trước hết kiểm tra store có dữ liệu, sau đó truy xuất tối đa `top_k` chunk bằng `search` hoặc `search_with_filter` nếu có metadata filter. Mỗi chunk được đưa vào context kèm số thứ tự và nguồn lấy từ `source_url`, `doc_id` hoặc `id`; prompt yêu cầu mô hình chỉ dùng context, không tự suy diễn và trích dẫn số context như `[1]` hoặc `[2]`. Cuối prompt, agent đặt câu hỏi và phần `Answer:` rồi truyền toàn bộ prompt cho `llm_fn`; nếu không có dữ liệu hoặc không có kết quả truy xuất thì trả về thông báo không tìm thấy thông tin.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
# Dán kết quả (output) của: pytest tests/ -v
```
![alt text](image.png)
**Số lượng bài test vượt qua (pass):** 42/42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Người mua có thể yêu cầu trả hàng nếu kiện hàng bị biến dạng lúc vận chuyển. | Khách hàng được quyền hoàn trả khi bưu phẩm gặp sự cố móp méo trong quá trình giao nhận. | Cao | -0.078313 | Không |
| 2 | Sản phẩm còn thời hạn bảo hành và có tem bảo hành hợp lệ. | Thiết bị còn thời hạn bảo hành và vẫn giữ phiếu bảo hành. | Cao | 0.003204 | Không |
| 3 | Shopee đưa ra hướng giải quyết tranh chấp trong vòng 07 ngày làm việc. | Vụ việc được xử lý trong thời hạn bảy ngày làm việc kể từ khi nhận đủ tài liệu. | Cao | 0.017354 | Không |
| 4 | Người bán phải điền nguồn gốc và chế độ bảo hành của sản phẩm. | Hôm nay trời có mưa nhẹ ở khu vực miền Bắc. | Thấp | 0.090404 | Không |
| 5 | Người mua có thể yêu cầu hoàn tiền khi hàng bị lỗi. | Chính sách voucher áp dụng giảm tối đa 50.000 đồng cho đơn từ 200.000 đồng. | Thấp | 0.074338 | Không |

> Điểm được tính bằng `compute_similarity(MockEmbedder()(A), MockEmbedder()(B))`. Vì không có ngưỡng tuyệt đối để gọi một điểm là cao hay thấp, trong bảng này tôi quy ước hai điểm lớn nhất trong 5 cặp là “cao” và ba điểm còn lại là “thấp”; kết quả được làm tròn đến 6 chữ số thập phân. Theo quy ước đó, cặp 4 và 5 có điểm cao nhất, còn cặp 1, 2 và 3 có điểm thấp hơn.

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là cặp 1 và cặp 3 đều là các câu gần nghĩa nhưng lần lượt chỉ đạt -0.078313 và 0.017354, trong khi cặp 4 gồm hai câu không liên quan lại đạt 0.090404, cao nhất trong năm cặp. Nguyên nhân là `MockEmbedder` chỉ băm MD5 để tạo vector giả ổn định, không học ngữ nghĩa; vì vậy điểm cosine trong thí nghiệm này không thể hiện mức độ tương đồng ngôn ngữ và không nên được dùng để kết luận về chất lượng embedding thực tế. Với một embedding model được huấn luyện cho văn bản tiếng Việt, dự đoán các cặp 1-3 có điểm cao sẽ hợp lý hơn.

---

## 5. Kết quả Benchmark & Đánh giá — FixedSizeChunker (10 điểm)

### Tổng hợp thực nghiệm CP6

- **Corpus:** `data/shopee-warranty` (8 tài liệu).
- **Tổng số chunk nạp vào store:** 41 chunks.
- **Chunker:** `FixedSizeChunker(chunk_size=500, overlap=50)`.
- **Embedding backend:** Mock embeddings fallback (MD5 hashing).
- **Điểm retrieval:** **1/10**.
- Q1 đạt 1/2 nhờ metadata filter đưa đúng tài liệu seller vào top-3; Q2-Q5 đạt 0/2. MockEmbedder tạo vector ổn định nhưng không mã hóa ngữ nghĩa, nên điểm similarity vẫn mang tính ngẫu nhiên và gây nhiễu.

### Chi tiết Top-3 theo 5 benchmark queries

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 (Filtered) | Quyền và trách nhiệm khi bảo hành trên sàn | `seller-listing-policy` (0.1448 / 0.0697); `seller-warranty-policy` (0.0483) | 1/2 | Có, hạng 3 | Filter `audience=seller` đưa đủ 3 marker vào top-3. |
| 1 (Unfiltered) | Quyền và trách nhiệm khi bảo hành trên sàn | `shopee-mall-terms` (0.2481); `dispute-process` (0.2133); `return-refund-process` (0.1943) | 0/2 | Không | Không có tài liệu gold trong top-3. |
| 2 | Thời hạn Trả hàng/Hoàn tiền khi Người bán tự vận chuyển | `shopee-mall-terms` (0.3653 / 0.1999); `return-refund-policy` (0.1585) | 0/2 | Không | Không truy xuất được chunk chứa “20 ngày” và “Lấy hàng thành công”. |
| 3 | Điều kiện cơ bản để được bảo hành | `return-refund-policy` (0.2806); `seller-warranty-policy` (0.2332); `return-refund-process` (0.1943) | 0/2 | Không | Không chứa đủ các marker về thời hạn, tem/phiếu và lỗi kỹ thuật. |
| 4 | Thời hạn giải quyết tranh chấp ngoài Trả hàng/Hoàn tiền | `shopee-mall-terms` (0.2119); `seller-listing-policy` (0.2038); `return-refund-policy` (0.1706) | 0/2 | Không | Không truy xuất được marker “07 ngày làm việc”. |
| 5 | Các lý do được phép Trả hàng/Hoàn tiền | `shopee-mall-terms` (0.3569); `return-refund-process` (0.2706); `shopee-guarantee` (0.1878) | 0/2 | Không | Không chứa đủ 8 marker của câu hỏi. |

**Tổng điểm retrieval:** **1 / 10**.

### Đánh giá chiến lược FixedSizeChunker

- **Ưu điểm:** Tốc độ chunking đồng nhất, sản sinh 41 chunk với kích thước 500 ký tự và overlap 50 ký tự; dễ kiểm soát chi phí và kích thước context.
- **Hạn chế:** Cắt cứng cơ học nên một số câu, heading và bảng biểu chính sách bị đứt đoạn giữa hai chunk, làm mất liên kết ngữ nghĩa khi truy xuất.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5/ 5 |
| Hướng tiếp cận của tôi (My Approach) | 10/ 10 |
| Hoàn thiện code (Core Implementation — tests) | 30/ 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5/ 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10/ 10 |
| **Tổng phần cá nhân** | **60/ 60** |
