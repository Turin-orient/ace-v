# So Sánh Chi Tiết: Playbook Cũ vs Playbook Mới

## Tổng Quan
- **Playbook Cũ**: 14 bullets (từ demo ban đầu với 5 samples)
- **Playbook Mới**: 19 bullets (sau khi chạy verification với 3 samples mới)
- **Tăng thêm**: +5 bullets mới

---

## 1. Bullets Mới Được Thêm Vào

### 🆕 [err-00002] - Xử Lý Negation (Phủ Định) → Zero
**Nội dung**: Quy tắc chuyển đổi các cụm từ phủ định ("no shares", "none available") thành giá trị số 0.

**Ví dụ cụ thể**:
- "no shares remain available under the 2014 Long Term Incentive Plan" → `ShareBasedCompensationArrangementByShareBasedPaymentAwardNumberOfSharesAvailableForGrant = 0`
- "There are no amounts available under the credit facility" → `LineOfCreditFacilityRemainingBorrowingCapacity = 0`

**Tác động**: 
- ✅ **Tích cực**: Giải quyết edge case quan trọng (negation handling)
- ✅ Tránh lỗi khi model bỏ qua các giá trị "zero" ngầm định
- ✅ Cải thiện độ chính xác cho các báo cáo tài chính có giá trị 0

---

### 🆕 [err-00004] - Interest Expense Mapping (Chi Phí Lãi Vay)
**Nội dung**: Quy tắc map các khoản lãi vay vào tag cụ thể theo instrument (Seller Notes, Term Loan, v.v.) thay vì dùng tag chung.

**Ví dụ cụ thể**:
- "$179,507 of interest charges associated with the Seller Notes" → `InterestExpenseDebt` (linked to Seller Notes)
- "No interest expense was recorded on the Term Loan" → `InterestExpenseDebt = 0` (Term Loan)

**Tác động**:
- ✅ **Tích cực**: Tăng độ chi tiết (granularity) của dữ liệu
- ✅ Link được chi phí lãi với từng khoản nợ cụ thể
- ✅ Hỗ trợ phân tích tài chính chi tiết hơn

---

### 🆕 [ctx-00001] - Equity/Plan Lexical Rules (Quy Tắc Cổ Phiếu/Kế Hoạch)
**Nội dung**: Bộ quy tắc lexical chi tiết cho:
1. Par value per share → `CommonStockParOrStatedValuePerShare`
2. Shares outstanding → `CommonStockSharesOutstanding`
3. Plan-specific shares (available/authorized) → Plan-specific tags

**Ví dụ cụ thể**:
- "$0.001 par value per share" → `CommonStockParOrStatedValuePerShare = 0.001`
- "28,026,713 shares outstanding" → `CommonStockSharesOutstanding = 28,026,713`
- "no shares remain available under the 2014 Long Term Incentive Plan" → `ShareBasedCompensationArrangementByShareBasedPaymentAwardNumberOfSharesAvailableForGrant = 0`

**Tác động**:
- ✅ **Rất tích cực**: Giải quyết nhiều trường hợp phức tạp về equity
- ✅ Phân biệt rõ giữa par value, outstanding shares, và plan shares
- ✅ Tránh nhầm lẫn giữa các loại shares khác nhau

---

### 🆕 [ctx-00003] - LIBOR Plus Spread Mapping
**Nội dung**: Quy tắc map "LIBOR plus X%" vào `DebtInstrumentBasisSpreadOnVariableRate1` (spread tag) thay vì absolute interest rate.

**Ví dụ cụ thể**:
- "LIBOR plus 4.15%" → `DebtInstrumentBasisSpreadOnVariableRate1 = 4.15%`
- "margin ranges from 1.00% to 2.00% in the case of LIBOR loans" → Both = `DebtInstrumentBasisSpreadOnVariableRate1`

**Tác động**:
- ✅ **Tích cực**: Tránh nhầm lẫn giữa spread (biên độ) và absolute rate (lãi suất tuyệt đối)
- ✅ Xử lý đúng các khoản vay có lãi suất thả nổi (variable rate)

---

### 🆕 [ctx-00005] - Borrowing Base Mapping
**Nội dung**: Quy tắc map "borrowing base" (hạn mức vay hiện tại) vào `LineOfCreditFacilityRemainingBorrowingCapacity`.

**Ví dụ cụ thể**:
- "The borrowing base under the credit facility is $425.0 million" → `LineOfCreditFacilityRemainingBorrowingCapacity = $425.0M`

**Tác động**:
- ✅ **Rất tích cực**: Đây là quy tắc được học từ Sample 3 trong verification run
- ✅ Giải quyết chính xác case "borrowing base" mà playbook cũ không có
- ✅ **Bằng chứng trực tiếp** của khả năng học: Model đã tự động viết quy tắc này sau khi gặp lỗi trong Sample 3

---

## 2. Phân Tích Tác Động Tổng Thể

### ✅ Điểm Tích Cực

1. **Học từ Lỗi Thực Tế**:
   - `ctx-00005` (borrowing base) được tạo ra **trực tiếp** từ lỗi trong Sample 3
   - Reflector phát hiện lỗi → Curator viết quy tắc mới → Generator áp dụng thành công

2. **Tăng Coverage (Phạm Vi Bao Phủ)**:
   - Từ 14 → 19 bullets (+36% tăng trưởng)
   - Bổ sung các edge cases quan trọng (negation, borrowing base, LIBOR spread)

3. **Tăng Độ Chính Xác**:
   - Các quy tắc mới giải quyết các ambiguity (mơ hồ) cụ thể
   - Ví dụ: Phân biệt rõ "LIBOR plus 4%" (spread) vs "4% per annum" (absolute rate)

4. **Tự Động Hóa Hoàn Toàn**:
   - Không cần human intervention
   - Model tự phát hiện gap → tự viết quy tắc → tự validate

### 📊 Kết Quả Cụ Thể

**Sample 3 (Verification Run)**:
- **Lần 1**: ❌ Sai (không có quy tắc "borrowing base")
- **Reflector**: Phát hiện lỗi và đề xuất thêm quy tắc
- **Curator**: Viết `ctx-00005` (borrowing base rule)
- **Lần 2**: ✅ Đúng (áp dụng quy tắc mới)

**Bằng chứng từ log**:
```json
{
  "reasoning": "Applied playbook lexical rules: (1) 'borrowing base' exact-cue maps currency nearest to cue to LineOfCreditFacilityRemainingBorrowingCapacity (ctx-00005 / ctx-00009)...",
  "bullet_ids": ["ctx-00005", "ctx-00009", "ctx-00003", "ctx-00008", "ctx-00011"],
  "final_answer": "LineOfCreditFacilityRemainingBorrowingCapacity,DebtInstrumentBasisSpreadOnVariableRate1,..."
}
```

---

## 3. Kết Luận

### ✅ **Kết Quả: RẤT TÍCH CỰC**

1. **Playbook đã tiến hóa đúng hướng**: Các quy tắc mới giải quyết các lỗi thực tế gặp phải
2. **Chất lượng quy tắc cao**: Các bullets mới có cấu trúc rõ ràng, có ví dụ cụ thể, và có unit tests
3. **Tự động học từ lỗi**: Hệ thống đã chứng minh khả năng self-improvement
4. **Scalability tốt**: Với 3 samples mới đã học được 5 quy tắc → tỷ lệ học tốt

### 🎯 Điểm Nổi Bật

- **`ctx-00005` (borrowing base)**: Quy tắc này là **bằng chứng trực tiếp nhất** của learning loop
  - Sample 3 ban đầu sai vì thiếu quy tắc này
  - Curator tự động viết quy tắc
  - Generator áp dụng ngay và trả lời đúng

### 📈 Tiềm Năng Mở Rộng

Nếu chạy với 50-100 samples:
- Dự kiến playbook sẽ tăng lên ~50-80 bullets
- Độ chính xác sẽ cải thiện đáng kể khi gặp nhiều edge cases hơn
- Các quy tắc sẽ được refine (tinh chỉnh) qua helpful/harmful counters
