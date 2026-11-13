# Day 06 · Data Ingestion Engineering

**Lab cá nhân** · **4 giờ** · **Dữ liệu tự chọn**

Biến tài liệu thành kho tri thức có thể truy xuất cho AI agent, rồi đo xem cách chuẩn bị dữ liệu nào hiệu quả nhất.

| 📄 Dữ liệu | 🧩 Chiến lược | 🎯 Benchmark |
|---|---|---|
| Tối thiểu **30 trang nội dung** | Tối thiểu **3 cấu hình** | Tối thiểu **20 câu hỏi** |

---

## Báo cáo & Kết quả bài nộp của học viên

- **Học viên**: Võ Lê Hải Đăng (MSSV: 2A202603577) — Lớp K5-L3A
- **Corpus**: Báo cáo thường niên Vinamilk 2025 (`data/raw/20260319_VNM_Bao_cao_thuong_nien_2025_eae619d5f6.pdf`, 110 trang hữu ích)
- **Embedding Model**: `google/embeddinggemma-2` (chạy local trên CPU qua `sentence-transformers`)
- **Vector Store**: `ChromaDB` (local persistent store, khoảng cách Cosine)
- **Báo cáo cá nhân chi tiết**: [report/individual/2A202603577_VoLeHaiDang.md](report/individual/2A202603577_VoLeHaiDang.md)
- **Nhật ký thí nghiệm**: [artifacts/experiment_log.csv](artifacts/experiment_log.csv)
- **Bộ benchmark 20 câu (15 dev / 5 test)**: [benchmark/benchmark.json](benchmark/benchmark.json) | [benchmark/benchmark.csv](benchmark/benchmark.csv)
- **Kết quả & Traces**: Thư mục [results/](results/)

---

## Hướng dẫn cài đặt & Chạy Pipeline

### 1. Cài đặt môi trường

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Chạy toàn bộ pipeline thử nghiệm (Chiến lược A, B, C)

```powershell
python src/run.py
```

Lệnh trên sẽ tự động:
1. Đọc và chuẩn hóa 110 trang PDF từ `data/raw/`.
2. Tạo 1.048 chunks cho Chiến lược A (Fixed 500) và 762 chunks cho Chiến lược B/C (Paragraph 800).
3. Nạp model `google/embeddinggemma-2` và tính vector embedding.
4. Lưu trữ vào ChromaDB tại `data/chroma_db/`.
5. Chạy benchmark 20 câu hỏi (15 dev / 5 test) cho cả 3 chiến lược.
6. Xuất toàn bộ kết quả, chỉ số Hit@1/Hit@3 và traces vào thư mục `results/`.

### 3. Chạy phân tích & Audit chất lượng thủ công

```powershell
python scripts/audit_evaluation.py
```

---

## Cấu trúc thư mục bài nộp

```text
├── STUDENT.md                              # Thông tin học viên
├── requirements.txt                        # Thư viện phụ thuộc
├── data/
│   ├── raw/                                # PDF Báo cáo thường niên Vinamilk 2025
│   ├── manifest.json                       # Manifest bản quyền, nguồn, quy tắc tính trang
│   └── page_analysis.json                  # Thống kê chi tiết 110 trang hữu ích
├── benchmark/
│   ├── benchmark.json                      # 20 câu hỏi (15 dev / 5 test) kèm gold evidence
│   └── benchmark.csv                       # Phiên bản CSV của bộ benchmark
├── src/
│   ├── models.py                           # Cấu trúc DocumentPage và Chunk
│   ├── ingestion.py                        # Trích xuất và chuẩn hóa PDF, gán section metadata
│   ├── chunking.py                         # 2 thuật toán chunking (Fixed-size & Paragraph-aware)
│   ├── embeddings.py                       # Nạp google/embeddinggemma-2 qua SentenceTransformer
│   ├── store.py                            # ChromaDB Vector Store & Metadata Filter
│   ├── evaluation.py                       # Tính Hit@1, Hit@3 và xuất trace
│   └── run.py                              # Script chạy toàn bộ pipeline
├── artifacts/
│   └── experiment_log.csv                  # Nhật ký cấu hình A/B/C và giả thuyết
├── results/
│   ├── metrics_summary.json                # Thống kê Hit@1/Hit@3 cho Dev/Test/All
│   ├── traces_strategy_a.json              # Trace truy xuất Top-3 của Chiến lược A
│   ├── traces_strategy_b.json              # Trace truy xuất Top-3 của Chiến lược B
│   ├── traces_strategy_c.json              # Trace truy xuất Top-3 của Chiến lược C
│   ├── audit_coherence.csv                 # Bảng chấm thủ công Coherence (10 mẫu)
│   ├── audit_metadata.csv                  # Bảng kiểm tra tính đúng đắn của Metadata
│   └── audit_grounding.csv                 # Bảng chấm thủ công Grounding (5 câu test)
├── report/
│   └── individual/
│       └── 2A202603577_VoLeHaiDang.md      # Báo cáo cá nhân hoàn chỉnh theo mẫu
└── scripts/
    ├── analyze_corpus.py                   # Script phân tích số trang & ký tự PDF
    ├── build_benchmark.py                  # Script xây dựng & đối soát evidence câu hỏi
    └── audit_evaluation.py                 # Script đối soát audit Coherence/Metadata/Grounding
```
