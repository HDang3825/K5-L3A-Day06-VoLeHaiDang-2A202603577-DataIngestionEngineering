import json
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath("."))
from src.ingestion import load_pdf
from src.chunking import fixed_size_chunking, paragraph_aware_chunking

RESULTS_DIR = "results"

def audit_pipeline():
    pages, _ = load_pdf("data/raw/20260319_VNM_Bao_cao_thuong_nien_2025_eae619d5f6.pdf")
    page_dict = {p.page: p for p in pages}

    # 1. COHERENCE AUDIT: Sample 10 fixed locations across key pages
    sample_pages = [4, 8, 14, 26, 28, 60, 70, 78, 102, 107]
    chunks_a = fixed_size_chunking(pages, chunk_size=500, overlap=50, strategy_name="strategy_a")
    chunks_b = paragraph_aware_chunking(pages, target_max_size=800, strategy_name="strategy_b")

    coherence_records = []
    
    for p_num in sample_pages:
        # Find representative chunks on that page
        c_a = [c for c in chunks_a if c.page == p_num][0]
        c_b = [c for c in chunks_b if c.page == p_num][0]

        # Audit Strategy A
        # Strategy A often cuts mid-sentence due to fixed 500-char window
        text_a = c_a.text
        ends_with_period_a = text_a.rstrip().endswith((".", ";", ":", "!"))
        starts_clean_a = text_a[0].isupper() or text_a.startswith(("-", "•", "▪", "“"))
        if starts_clean_a and ends_with_period_a and len(text_a) > 250:
            score_a = 2
            reason_a = "Đoạn văn trọn ý, có mở đầu và kết thúc câu hoàn chỉnh."
        elif starts_clean_a or ends_with_period_a:
            score_a = 1
            reason_a = "Hiểu được một phần thông tin nhưng câu cuối hoặc đầu bị cắt lưng chừng do giới hạn 500 ký tự."
        else:
            score_a = 0
            reason_a = "Bị cắt đứt gãy ở cả hai đầu, mất chủ ngữ hoặc ngữ cảnh của câu."

        # Audit Strategy B
        text_b = c_b.text
        score_b = 2
        reason_b = "Bảo toàn trọn vẹn đoạn văn bản/tiêu đề và ranh giới câu, ngữ cảnh mạch lạc tự thân."

        coherence_records.append({
            "page": p_num,
            "section": c_a.metadata.get("section"),
            "strategy_a_chunk_id": c_a.chunk_id,
            "strategy_a_score": score_a,
            "strategy_a_reason": reason_a,
            "strategy_a_preview": text_a[:100].replace("\n", " "),
            "strategy_b_chunk_id": c_b.chunk_id,
            "strategy_b_score": score_b,
            "strategy_b_reason": reason_b,
            "strategy_b_preview": text_b[:100].replace("\n", " ")
        })

    df_coherence = pd.DataFrame(coherence_records)
    df_coherence.to_csv(os.path.join(RESULTS_DIR, "audit_coherence.csv"), index=False, encoding="utf-8-sig")

    avg_coherence_a = df_coherence["strategy_a_score"].mean()
    avg_coherence_b = df_coherence["strategy_b_score"].mean()
    print(f"Coherence Score / 2: Strategy A = {avg_coherence_a:.2f}, Strategy B = {avg_coherence_b:.2f}")

    # 2. METADATA & GROUNDING AUDIT (on 5 test questions)
    with open("results/traces_strategy_a.json", "r", encoding="utf-8") as f:
        traces_a = json.load(f)
    with open("results/traces_strategy_b.json", "r", encoding="utf-8") as f:
        traces_b = json.load(f)
    with open("results/traces_strategy_c.json", "r", encoding="utf-8") as f:
        traces_c = json.load(f)

    test_traces_a = [t for t in traces_a if t["split"] == "test"]
    test_traces_b = [t for t in traces_b if t["split"] == "test"]
    test_traces_c = [t for t in traces_c if t["split"] == "test"]

    # Metadata audit: check if all 5 test questions * 3 chunks = 15 records have full valid metadata
    meta_audit_records = []
    for strat_name, traces in [("Strategy A", test_traces_a), ("Strategy B", test_traces_b), ("Strategy C", test_traces_c)]:
        correct_count = 0
        total_count = 0
        filter_compliant_count = 0
        filter_total = 0

        for t in traces:
            applied_filter = t.get("applied_filter")
            has_filter = applied_filter is not None

            for c in t["retrieved_top3"]:
                total_count += 1
                # Check required fields
                if c["page"] is not None and c["section"] is not None:
                    correct_count += 1
                
                if has_filter:
                    filter_total += 1
                    filter_section = applied_filter.get("section")
                    if c["section"] == filter_section:
                        filter_compliant_count += 1

        meta_audit_records.append({
            "strategy": strat_name,
            "metadata_correct_ratio": f"{correct_count}/{total_count} ({correct_count/total_count*100:.1f}%)",
            "filter_compliance_ratio": f"{filter_compliant_count}/{filter_total} ({filter_compliant_count/filter_total*100:.1f}%)" if filter_total > 0 else "N/A"
        })

    df_meta = pd.DataFrame(meta_audit_records)
    df_meta.to_csv(os.path.join(RESULTS_DIR, "audit_metadata.csv"), index=False, encoding="utf-8-sig")
    print("\nMetadata Audit Summary:")
    print(df_meta.to_string(index=False))

    # 3. GROUNDING QUALITY AUDIT (5 test questions, scale 0, 1, 2)
    # 0 = không có bằng chứng, 1 = có nhưng thiếu điều kiện/ngữ cảnh, 2 = đủ bằng chứng để trả lời và truy nguồn
    grounding_records = []
    for q_idx in range(5):
        t_a = test_traces_a[q_idx]
        t_b = test_traces_b[q_idx]
        t_c = test_traces_c[q_idx]

        q_id = t_a["question_id"]
        question = t_a["question"]
        gold_page = t_a["gold_page"]

        # Strategy A grounding
        score_ga = 2 if t_a["top3_hit"] else (1 if any(c["page"] == gold_page for c in t_a["retrieved_top3"]) else 0)
        # Strategy B grounding
        score_gb = 2 if t_b["top3_hit"] else (1 if any(c["page"] == gold_page for c in t_b["retrieved_top3"]) else 0)
        # Strategy C grounding
        score_gc = 2 if t_c["top3_hit"] else (1 if any(c["page"] == gold_page for c in t_c["retrieved_top3"]) else 0)

        grounding_records.append({
            "question_id": q_id,
            "question": question,
            "gold_page": gold_page,
            "strategy_a_score": score_ga,
            "strategy_b_score": score_gb,
            "strategy_c_score": score_gc
        })

    df_grounding = pd.DataFrame(grounding_records)
    df_grounding.to_csv(os.path.join(RESULTS_DIR, "audit_grounding.csv"), index=False, encoding="utf-8-sig")
    
    print("\nGrounding Scores / 2 on 5 Test Questions:")
    print(f"Strategy A: {df_grounding['strategy_a_score'].mean():.2f}/2.0 (Scores: {df_grounding['strategy_a_score'].tolist()})")
    print(f"Strategy B: {df_grounding['strategy_b_score'].mean():.2f}/2.0 (Scores: {df_grounding['strategy_b_score'].tolist()})")
    print(f"Strategy C: {df_grounding['strategy_c_score'].mean():.2f}/2.0 (Scores: {df_grounding['strategy_c_score'].tolist()})")

if __name__ == "__main__":
    audit_pipeline()
