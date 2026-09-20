# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [Tên nhóm]
**Thành viên:** [Họ tên từng thành viên]
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Chính sách bảo hành, đổi trả và khiếu nại sàn Shopee (Lớp K4-L3B).

**Tại sao nhóm chọn chủ đề này?**
> Bộ dữ liệu này bao gồm các chính sách công khai về quyền lợi người mua, nghĩa vụ người bán và quy định xử lý khiếu nại, đổi trả, bảo hành trên sàn Shopee. Chúng ta chọn chủ đề này vì nó mang tính thực tiễn cao, có cấu trúc metadata rõ ràng và phù hợp để xây dựng hệ thống retrieval, lọc theo audience và đánh giá chất lượng truy xuất văn bản.

### Danh sách tài liệu (Data Inventory)

| STT | Doc ID | Tiêu đề | Đối tượng | Nguồn URL | Phiên bản |
|-----|--------|---------|-----------|-----------|-----------|
| 1 | shopee-brand-warranty-coverage | Chinh sach bao hanh chinh hang Shopee Mall | buyer | https://help.shopee.vn/portal/4/article/190242 | not-stated |
| 2 | shopee-prohibited-items-policy | Chinh sach hang hoa cam va han che | seller | https://help.shopee.vn/portal/4/article/77246 | not-stated |
| 3 | shopee-return-refund-rights-buyer | Chinh sach tra hang va bao ve nguoi mua | buyer | https://help.shopee.vn/portal/4/article/77262 | not-stated |
| 4 | shopee-seller-dispute-and-penalty | Quy dinh ve tranh chap va xu phat Shop | seller | https://help.shopee.vn/portal/4/article/77265 | not-stated |
| 5 | shopee-seller-return-warranty-fulfillment | Nghia vu tiep nhan va xu ly bao hanh cua nguoi ban | seller | https://help.shopee.vn/portal/4/article/79314 | not-stated |
| 6 | shopee-terms-service-warranty-general | Dieu khoan dich vu va quy dinh chung | buyer | https://help.shopee.vn/portal/4/article/77245 | not-stated |
| 7 | shopee-warranty-electronic-service | Quy dinh bao hanh dien tu va sua chua | buyer | https://help.shopee.vn/portal/4/article/188931 | not-stated |

**Tổng quan corpus (Corpus Summary):**
- Chủ đề: Chính sách bảo hành và khiếu nại sàn Shopee (Lớp K4-L3B).
- Tổng số tài liệu: 7 file Markdown (.md).
- Phân bố audience: 4 buyer, 3 seller.
- Trạng thái kiểm thử CP2: 7/7 file đạt chuẩn, khớp 1-1 với `sources.csv`.

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.
- [x] Mỗi `doc_id` đồng bộ với tên file `.md` và khớp với `sources.csv`.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `shopee-return-refund-rights-buyer` | Mã định danh duy nhất, dùng để khóa tài liệu, kiểm tra tương ứng 1-1 với file `.md` và lọc dữ liệu chính xác. |
| `title` | string | `Chinh sach tra hang va bao ve nguoi mua` | Tiêu đề chính thức giúp nhận diện nội dung chính và hỗ trợ truy vấn theo tên chính sách. |
| `source_url` | string | `https://help.shopee.vn/portal/4/article/77262` | Link nguồn gốc giúp xác minh tính hợp lệ, truy nguồn và kiểm tra chất lượng dữ liệu thu thập. |
| `retrieved_at` | string / ISO timestamp | `2026-09-20` | Thời điểm thu thập cho phép theo dõi phiên bản dữ liệu và kiểm soát tính cập nhật của corpus. |
| `document_version` | string | `not-stated` | Biểu thị mức độ rõ ràng về phiên bản văn bản; ở đây được chuẩn hóa là `not-stated` do nguồn không công bố. |
| `audience` | string | `buyer` hoặc `seller` | Trường quan trọng cho filtering metadata, cho phép tách corpus theo nhóm người dùng và cải thiện độ chính xác khi trả lời câu hỏi theo đối tượng. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| | FixedSizeChunker (`fixed_size`) | | | |
| | SentenceChunker (`by_sentences`) | | | |
| | RecursiveChunker (`recursive`) | | | |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — [Tên]**
- **Loại chiến lược:** [FixedSize / Sentence / Recursive / custom]
- **Mô tả & lý do chọn cho chủ đề này:** *(2-3 câu)*
- **Code snippet (nếu custom):**
```python
# Dán mã nguồn (implementation) vào đây
```

**Thành viên 2 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

**Thành viên 3 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| | | | | |
| | | | | |
| | | | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *Viết 2-3 câu — đây là phần được đánh giá cao nhất (khả năng suy nghĩ & giải thích):*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> *Viết 2-3 câu:*

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> *Liệt kê 2-3 ý:*

**Bài học rút ra khi so sánh trong nhóm:**
> *Viết 2-3 câu — cùng tài liệu nhưng chiến lược khác nhau dẫn tới khác biệt gì?*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |
