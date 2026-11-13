import json
import os
import pandas as pd

# Update audit_coherence.csv with detailed manual review
coherence_data = [
    {
        "sample_id": "coh-01",
        "page": 4,
        "section": "mo_dau",
        "strategy_a_score": 1,
        "strategy_a_tail": "...tôi xin gửi lời tri ân sâu sắc",
        "strategy_a_reason": "Bị cắt ngang mệnh đề cảm ơn ở cuối cửa sổ 500 ký tự.",
        "strategy_b_score": 2,
        "strategy_b_tail": "...khẳng định sức bền và khả năng thích ứng của Vinamilk.",
        "strategy_b_reason": "Trọn vẹn câu mở đầu và hoàn cảnh kinh tế toàn cầu."
    },
    {
        "sample_id": "coh-02",
        "page": 8,
        "section": "thong_tin_chung",
        "strategy_a_score": 0,
        "strategy_a_tail": "...Chất Vinami",
        "strategy_a_reason": "Bị cắt đứt cụt ngay giữa chữ 'Vinamilk', mất hoàn toàn ngữ nghĩa từ.",
        "strategy_b_score": 2,
        "strategy_b_tail": "...với cuộc sống con người và xã hội”",
        "strategy_b_reason": "Đoạn văn trọn vẹn cả Tầm nhìn và Sứ mệnh, đóng ngoặc kép đầy đủ."
    },
    {
        "sample_id": "coh-03",
        "page": 14,
        "section": "thong_tin_chung",
        "strategy_a_score": 0,
        "strategy_a_tail": "...Miraka Limited (13",
        "strategy_a_reason": "Bị cắt ngang tên công ty con và tỷ lệ sở hữu dở dang '(13...'.",
        "strategy_b_score": 2,
        "strategy_b_tail": "...chi nhánh văn phòng bán hàng tại Hà Nội, Đà Nẵng và Cần Thơ",
        "strategy_b_reason": "Bảo toàn nguyên vẹn danh sách các đơn vị trực thuộc trong nước."
    },
    {
        "sample_id": "coh-04",
        "page": 26,
        "section": "bao_cao_hoat_dong",
        "strategy_a_score": 1,
        "strategy_a_tail": "...ngành sữa ghi nhận mức tăng trưởng -2,4%",
        "strategy_a_reason": "Hiểu được số liệu ngành sữa nhưng mất vế giải thích nguyên nhân đằng sau.",
        "strategy_b_score": 2,
        "strategy_b_tail": "...người tại Việt Nam còn thấp so với các nước trong khu vực.",
        "strategy_b_reason": "Trọn vẹn đoạn phân tích bối cảnh ngành hàng FMCG và tiềm năng tiêu thụ."
    },
    {
        "sample_id": "coh-05",
        "page": 28,
        "section": "bao_cao_hoat_dong",
        "strategy_a_score": 0,
        "strategy_a_tail": "...mà còn cho thấy sức bền",
        "strategy_a_reason": "Bị cắt lửng ở liên từ so sánh 'mà còn cho thấy...', người đọc không biết sức bền của cái gì.",
        "strategy_b_score": 2,
        "strategy_b_tail": "...gắn liền với quản trị rủi ro, trách nhiệm xã hội và cam kết chất lượng.",
        "strategy_b_reason": "Đoạn văn hoàn chỉnh, nêu trọn vẹn kết quả lợi nhuận và ý nghĩa chiến lược."
    },
    {
        "sample_id": "coh-06",
        "page": 60,
        "section": "bao_cao_hoat_dong",
        "strategy_a_score": 0,
        "strategy_a_tail": "...vinh danh l",
        "strategy_a_reason": "Bị cắt đứt cụt ngay giữa chữ cái 'l' trong danh hiệu vinh danh.",
        "strategy_b_score": 2,
        "strategy_b_tail": "...Hàng Việt Nam Chất Lượng Cao 29 năm liền.",
        "strategy_b_reason": "Đoạn văn bản trọn vẹn danh mục các giải thưởng lớn."
    },
    {
        "sample_id": "coh-07",
        "page": 70,
        "section": "quan_tri_cong_ty",
        "strategy_a_score": 0,
        "strategy_a_tail": "...biến động về số lượng cổ phiếu mà",
        "strategy_a_reason": "Bị cắt ngang ở đại từ quan hệ 'mà', mất vế vị ngữ phía sau.",
        "strategy_b_score": 2,
        "strategy_b_tail": "...trong Báo cáo QTCT trên website của Công ty.",
        "strategy_b_reason": "Trọn vẹn quy định và địa chỉ công bố thông tin người nội bộ."
    },
    {
        "sample_id": "coh-08",
        "page": 78,
        "section": "quan_tri_cong_ty",
        "strategy_a_score": 0,
        "strategy_a_tail": "...5 Đặng Thị Th",
        "strategy_a_reason": "Bị cắt cụt giữa họ tên lãnh đạo 'Đặng Thị Th...', mất toàn bộ số liệu thù lao.",
        "strategy_b_score": 2,
        "strategy_b_tail": "...6 Đỗ Lê Hùng 2.201 Thành viên độc lập Chủ tịch UBKT",
        "strategy_b_reason": "Bảo toàn cấu trúc từng dòng của bảng thù lao HĐQT."
    },
    {
        "sample_id": "coh-09",
        "page": 102,
        "section": "phat_trien_ben_vung",
        "strategy_a_score": 0,
        "strategy_a_tail": "...“Công ty thực",
        "strategy_a_reason": "Bị cắt ngay mở ngoặc kép trích dẫn chính sách, mất toàn bộ nội dung cam kết.",
        "strategy_b_score": 2,
        "strategy_b_tail": "...công bằng và minh bạch trong suốt quá trình tuyển dụng”.",
        "strategy_b_reason": "Bảo tồn đầy đủ điều khoản không phân biệt đối xử và bình đẳng giới."
    },
    {
        "sample_id": "coh-10",
        "page": 107,
        "section": "bao_cao_tai_chinh",
        "strategy_a_score": 1,
        "strategy_a_tail": "...Bản thuyết minh",
        "strategy_a_reason": "Nêu được một phần danh sách báo cáo nhưng bị ngắt đường dẫn tải về.",
        "strategy_b_score": 2,
        "strategy_b_tail": "...Báo cáo Tài chính | Vinamilk hoặc quét mã QR bên cạnh.",
        "strategy_b_reason": "Trọn vẹn đoạn văn thuyết minh về nguồn công bố và cách tra cứu BCTC."
    }
]

df_coh = pd.DataFrame(coherence_data)
df_coh.to_csv("results/audit_coherence.csv", index=False, encoding="utf-8-sig")
print("Saved updated results/audit_coherence.csv")
