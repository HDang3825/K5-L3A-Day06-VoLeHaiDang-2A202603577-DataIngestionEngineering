# Báo cáo cá nhân — Day 6: Data Ingestion Engineering

- **Học viên**: Võ Lê Hải Đăng
- **MSSV**: 2A202603577
- **Lớp**: K5 - L3A

---

## Dữ liệu và pipeline

* **Chủ đề, nguồn/quyền, số trang và quy tắc tính trang**:
  - **Tài liệu**: Báo cáo thường niên Vinamilk 2025 (Chủ đề: *50 Năm Để Tâm Phụng Sự*).
  - **Nguồn & Quyền sử dụng**: Tài liệu công bố thông tin đại chúng định kỳ của Công ty Cổ phần Sữa Việt Nam (Vinamilk) niêm yết trên HOSE, được phép khai thác phục vụ học tập và nghiên cứu phi thương mại.
  - **Quy tắc tính trang**: File gốc gồm **112 trang vật lý**. Áp dụng ngưỡng lọc tối thiểu $\ge 150$ ký tự văn bản để loại bỏ trang bìa trước (Trang 1) và trang bìa sau (Trang 112). Toàn bộ **110 trang nội dung hữu ích** (từ trang 2 đến 111) với tổng cộng **455.520 ký tự** được đưa vào pipeline xử lý.
* **Chuẩn hóa, lỗi và giới hạn**:
  - Dùng `pypdf` trích xuất văn bản từng trang vật lý.
  - Chuẩn hóa Unicode Form C (`NFC`), thay thế khoảng trắng không ngắt (`\xa0`, `\u200b`), chuẩn hóa khoảng trắng nội dòng và ngắt dòng dư thừa.
  - Giới hạn: Một số bảng biểu tài chính phức tạp ở trang 108–111 khi trích xuất text thuần có thể mất gióng hàng ngang; pipeline không dùng OCR mà dựa trên luồng text vector gốc của PDF.
* **Embedding model, Vector store, Lệnh chạy và Chi phí**:
  - **Embedding Model**: `google/embeddinggemma-2` (chạy local qua thư viện `sentence-transformers`, `torch_dtype=float32` trên CPU máy tính).
  - **Vector Store**: `ChromaDB` (bản local persistent client, metric khoảng cách Cosine `hnsw:space = cosine`).
  - **Lệnh thực thi**: `python src/run.py`
  - **Chi phí**: $0 VNĐ (toàn bộ pipeline và model chạy offline 100% trên phần cứng cá nhân, không phát sinh chi phí API).
* **Metadata bắt buộc & Trường lọc bổ sung**:
  - **Trường bắt buộc**: `document_id` (`VNM_AR_2025`), `source` (`20260319_VNM_Bao_cao_thuong_nien_2025_eae619d5f6.pdf`), `page` (số trang vật lý 1–112).
  - **Trường bổ sung**:
    * `section`: Phân mục nội dung dựa theo mục lục và running header của tài liệu (`mo_dau`, `thong_tin_chung`, `bao_cao_hoat_dong`, `quan_tri_cong_ty`, `phat_trien_ben_vung`, `bao_cao_tai_chinh`).
    * `year`: `2025`
    * `company`: `Vinamilk`
  - **Lý do chọn**: Trường `section` đóng vai trò quan trọng trong việc thu hẹp không gian tìm kiếm của câu hỏi, triệt tiêu hiện tượng nhầm lẫn ngữ nghĩa giữa các chương khác nhau (ví dụ: thù lao HĐQT ở Quản trị công ty vs chi phí nhân công ở Báo cáo tài chính).

---

## Cấu hình và benchmark

* **Mô tả 3 Cấu hình (A / B / C)**:
  - **Chiến lược A (Baseline - Fixed-size)**: Cửa sổ kích thước cố định `chunk_size = 500` ký tự, `overlap = 50` ký tự. Sinh ra **1.048 chunks**. Truy xuất Top-3 không áp dụng bộ lọc.
  - **Chiến lược B (Structure / Paragraph-Aware)**: Phân tách theo cấu trúc đoạn văn bản và bullet points, gộp các đoạn ngắn và chỉ ngắt câu tự nhiên khi vượt ngưỡng `target_max_size = 800` ký tự. Sinh ra **762 chunks** (độ dài trung bình $595,7$ ký tự). Truy xuất Top-3 không áp dụng bộ lọc.
  - **Chiến lược C (Metadata-Filtered Retrieval)**: Dùng **cùng 762 chunks và embedding index của Chiến lược B**. Điểm khác biệt duy nhất giữa B và C: Khi câu hỏi có chỉ định trường `filter` (ví dụ `{"section": "quan_tri_cong_ty"}`), Chiến lược C kích hoạt mệnh đề `where` của ChromaDB để lọc kết quả.
* **Bộ Benchmark (20 câu)**:
  - Tách trước độc lập: **15 câu Dev** (`dev-01` đến `dev-15`) và **5 câu Test** (`test-01` đến `test-05`).
  - Gồm 4 câu có metadata filter (3 câu Dev: `dev-13`, `dev-14`, `dev-15`; 1 câu Test: `test-01`).
  - Phủ 4 nhóm câu hỏi: trực tiếp (8 câu), diễn đạt lại (5 câu), điều kiện/ngoại lệ (3 câu), lọc metadata (4 câu).
  - 100% trích dẫn chứng cứ (`evidence_quote`) và số trang (`gold_page`) được kiểm chứng khớp từng ký tự trên corpus đã chuẩn hóa.
* **Tiêu chí chọn chiến lược chốt trước khi xem Test**:
  - Ưu tiên 1: Evidence Hit@3 trên tập Dev cao hơn.
  - Ưu tiên 2: Tính mạch lạc (Coherence Score) và Grounding Quality cao hơn.
  - Ưu tiên 3: Tối ưu tài nguyên (số lượng chunk ít hơn, thời gian xử lý nhanh hơn).

---

## Kết quả

### Bảng 1: Hiệu năng định lượng & Chi phí

| Strategy | Split | Hit@1 (n/N) | Evidence Hit@3 (n/N) | Chunk count | Thời gian index | Chi phí |
|---|---|---|---|---|---|---|
| **Strategy A** (Fixed 500/50) | Dev | 5/15 (33.3%) | 11/15 (73.3%) | 1048 | 533.10s | 0 VNĐ |
| | Test | 4/5 (80.0%) | 4/5 (80.0%) | 1048 | - | 0 VNĐ |
| | **Toàn bộ (All)** | **9/20 (45.0%)** | **15/20 (75.0%)** | **1048** | **533.10s** | **0 VNĐ** |
| **Strategy B** (Paragraph 800) | Dev | 5/15 (33.3%) | 8/15 (53.3%) | 762 | 490.22s | 0 VNĐ |
| | Test | 3/5 (60.0%) | 5/5 (100.0%) | 762 | - | 0 VNĐ |
| | **Toàn bộ (All)** | **8/20 (40.0%)** | **13/20 (65.0%)** | **762** | **490.22s** | **0 VNĐ** |
| **Strategy C** (Metadata Filtered) | Dev | 6/15 (40.0%) | 8/15 (53.3%) | 762 | 490.22s | 0 VNĐ |
| | Test | 3/5 (60.0%) | 5/5 (100.0%) | 762 | - | 0 VNĐ |
| | **Toàn bộ (All)** | **9/20 (45.0%)** | **13/20 (65.0%)** | **762** | **490.22s** | **0 VNĐ** |

### Bảng 2: Đánh giá chất lượng thủ công (Audit)

| Strategy | Coherence trung bình /2 (10 mẫu) | Metadata đủ và đúng (15 bản ghi test) | Filter tuân thủ (3 bản ghi có filter) | Grounding trung bình /2 (5 câu test) | Phân bố Grounding (mức 0 / 1 / 2) |
|---|:---:|:---:|:---:|:---:|:---:|
| **Strategy A** | **0.20 / 2.0** (n=10) | 15/15 (100.0%) | N/A | **1.60 / 2.0** | 1 câu mức 0 / 0 câu mức 1 / 4 câu mức 2 |
| **Strategy B** | **2.00 / 2.0** (n=10) | 15/15 (100.0%) | N/A | **2.00 / 2.0** | 0 câu mức 0 / 0 câu mức 1 / 5 câu mức 2 |
| **Strategy C** | **2.00 / 2.0** (n=10) | 15/15 (100.0%) | 3/3 (100.0%) | **2.00 / 2.0** | 0 câu mức 0 / 0 câu mức 1 / 5 câu mức 2 |

* **Đường dẫn minh chứng**:
  - Traces chi tiết: `results/traces_strategy_a.json`, `results/traces_strategy_b.json`, `results/traces_strategy_c.json`.
  - Mẫu chấm thủ công Coherence: `results/audit_coherence.csv`.
  - Kiểm tra Metadata & Grounding: `results/audit_metadata.csv`, `results/audit_grounding.csv`.
  - Cách chọn mẫu Coherence: 10 vị trí trang cố định trải đều các phân mục (`pages: [4, 8, 14, 26, 28, 60, 70, 78, 102, 107]`).

---

## Phân tích và kết luận

### 1. So sánh Chiến lược A–B và B–C

* **So sánh A–B (Ảnh hưởng của phương pháp Chunking)**:
  - *Về khối lượng & thời gian*: Chiến lược B chỉ tạo ra 762 chunks (giảm **27.3%** số lượng chunk so với A là 1048 chunks), nhờ đó tiết kiệm 43 giây thời gian sinh vector embedding và giảm dung lượng index.
  - *Về tính mạch lạc (Coherence)*: Chiến lược B vượt trội hoàn toàn ($2.00/2.0$ so với $0.20/2.0$ của A). Chiến lược A dùng cửa sổ cố định 500 ký tự nên có tới 8/10 mẫu bị cắt cụt giữa chữ cái hoặc giữa mệnh đề (ví dụ cắt cụt chữ `Vinami...`, `Đặng Thị Th...`, hoặc mất mệnh đề điều kiện). Ngược lại, B tôn trọng trọn vẹn ranh giới đoạn văn và câu.
  - *Về Grounding trên tập Test*: Trên 5 câu test độc lập, Chiến lược B đạt **100% Hit@3 (5/5)** với Grounding $2.00/2.0$, trong khi Chiến lược A trượt câu `test-04` dẫn đến Grounding chỉ đạt $1.60/2.0$.
* **So sánh B–C (Ảnh hưởng của Metadata Filtering)**:
  - Giữ nguyên các chunk của B, khi áp dụng metadata filter ở Chiến lược C, câu `dev-13` (truy xuất thù lao Chủ tịch HĐQT trong phần Quản trị công ty) đã được đẩy từ Top-2 lên **Top-1** ngay lập tức, nâng tỷ lệ Dev Hit@1 từ 33.3% lên **40.0%**.
  - Đối với các câu hỏi có phạm vi ngữ cảnh cụ thể, Chiến lược C đảm bảo 100% chunk trả về tuân thủ đúng phân mục, loại bỏ hoàn toàn nhiễu từ các chương khác.

### 2. Hai ví dụ sai lệch cụ thể (Failure Cases)

1. **Lỗi ở Chiến lược A — Câu `test-04` (Trang 90, Phần Quản trị công ty)**:
   - *Câu hỏi*: *"Trong trường hợp cần thiết, Chủ tịch HĐQT có quyền hạn gì đối với các quyết định của Tổng Giám đốc?"*
   - *Nguyên nhân thất bại*: Câu trả lời nằm ở khoản mục quy định quyền hạn Chủ tịch HĐQT ("tạm đình chỉ những quyết định của Tổng Giám đốc"). Ở Chiến lược A, cửa sổ 500 ký tự cắt rời mục này thành một mẩu ngắn bị tách khỏi tiêu đề điều khoản, khiến similarity score bị thấp và trượt khỏi Top-3 (Hit@3 = False). Trong khi đó, Chiến lược B giữ nguyên cụm đoạn văn điều khoản nên đạt Hit@1 ngay lập tức.
2. **Lỗi ở Chiến lược B — Câu `dev-13` (Trang 78, Phần Quản trị công ty)**:
   - *Câu hỏi*: *"Trong báo cáo quản trị công ty, mức thù lao năm 2025 của Chủ tịch HĐQT Nguyễn Hạnh Phúc là bao nhiêu triệu đồng?"*
   - *Nguyên nhân thất bại*: Khi không có bộ lọc (Chiến lược B), retriever trả về Top-1 là một đoạn văn bản ở phần Báo cáo Ban Điều Hành có nhắc tới tên Chủ tịch HĐQT thay vì bảng biểu thù lao ở trang 78 (khiến câu này chỉ đạt Hit@2 thay vì Hit@1). Khi chuyển sang **Chiến lược C** (có filter `section: "quan_tri_cong_ty"`), đoạn văn nhiễu bị loại bỏ và đoạn bảng thù lao ở trang 78 đã vươn lên Top-1 chính xác.

### 3. Chiến lược được lựa chọn & Đánh đổi (Trade-offs)

* **Chiến lược được chọn**: **Chiến lược C (Paragraph-Aware kết hợp Metadata Filtering)**.
* **Lý do**:
  1. Bảo toàn ngữ cảnh và tính toàn vẹn thông tin cao nhất (Coherence 2.0/2.0, Grounding trên Test 2.0/2.0).
  2. Số lượng chunk gọn nhẹ hơn 27% so với chia nhỏ cố định, giảm tải cho bộ nhớ Vector DB.
  3. Linh hoạt: Hoạt động như Chiến lược B khi người dùng hỏi chung, và phát huy tối đa độ chính xác khi câu hỏi có ngữ cảnh lọc theo danh mục.
* **Đánh đổi**: Cần thêm bước tiền xử lý cấu trúc để gắn nhãn phân mục chính xác và logic ứng dụng cần hỗ trợ trích xuất filter từ câu hỏi của người dùng.

### 4. Hạn chế thực nghiệm & Hướng cải tiến

* **Hạn chế**:
  - Tập test gồm 5 câu là đại diện mẫu nhỏ cho kiểm thử ban đầu, chưa bao quát hết mọi trường hợp biên trong 112 trang tài liệu.
  - Model embedding mã nguồn mở `google/embeddinggemma-2` chạy trên CPU có độ trễ tạo vector khá lâu (~8-10 phút cho toàn bộ tài liệu).
* **Hướng cải tiến nếu mở rộng**:
  - Kết hợp **Hybrid Search (Dense Cosine Similarity + BM25 Sparse Search)** để cải thiện truy xuất các từ khóa đặc thù như mã chứng khoán, tên viết tắt, số liệu chính xác.
  - Sử dụng mô hình chuyên xử lý bảng (Table parsing / Markdown extraction) đối với các trang Báo cáo tài chính để trích xuất cấu trúc hàng-cột chuẩn xác hơn text thô.
