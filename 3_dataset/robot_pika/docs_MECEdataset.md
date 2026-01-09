### File 1: **memories.xlsx** - Event Types Benchmark

**Tổng số test cases: 30** (6 loại Event Types × 5 test cases)

| Event Type     | Trigger Condition     | Số Test Cases |
| -------------- | --------------------- | -------------- |
| ADD            | New Fact              | 5              |
| UPDATE         | Refinement            | 5              |
| UPDATE         | Correction            | 5              |
| DELETE         | Negation              | 5              |
| NOOP           | Redundancy            | 5              |
| UPDATE_PARTIAL | Partial Contradiction | 5              |

**Đặc điểm:**

* ✅ **6 loại Event Types** (đầy đủ MECE)
* ✅ **30 test cases** (mỗi loại 5 cases)
* ✅ **5-10 turns** hội thoại mỗi case
* ✅ Cột `messages` là **JSON array** (chuẩn API)

### 🔍 File 2: **search.xlsx** - Search Memory Benchmark

**Tổng số test cases: 168** (4 × 2 × 7 × 3 = 168)

| Chiều                           | Số Loại | Chi Tiết                                                                                           |
| -------------------------------- | --------- | --------------------------------------------------------------------------------------------------- |
| **Query Intent**           | 4         | Fact Retrieval, Reasoning, Comparison, Summarization                                                |
| **Query Specificity**      | 2         | Specific, Ambiguous                                                                                 |
| **Data Complexity**        | 7         | Simple Fact, List of Facts, Conflicting Facts, Multi-hop, Summarized Info, Empty Results, Inference |
| **Test Cases/Giao điểm** | 3         | Mỗi giao điểm MECE có 3 test cases                                                              |

**Phân bố:**

* ✅  **Fact Retrieval** : 42 test cases (4 × 2 × 7 × 3 / 4)
* ✅  **Reasoning** : 42 test cases
* ✅  **Comparison** : 42 test cases
* ✅  **Summarization** : 42 test cases
* ✅  **Specific** : 84 test cases
* ✅  **Ambiguous** : 84 test cases
* ✅  **Mỗi Data Complexity** : 24 test cases

**Đặc điểm:**

* ✅ **168 test cases** (4 × 2 × 7 × 3)
* ✅ **5-10 turns** hội thoại mỗi case
* ✅ Cột `messages` là **JSON array** (chuẩn API)
* ✅ **Đầy đủ MECE** - không trùng lặp, bao phủ toàn diện

### ✅ Tổng Kết

| Tiêu Chí                   | Kết Quả                          |
| ---------------------------- | ---------------------------------- |
| **Tổng test cases**   | 30 + 168 =**198 test cases** |
| **MECE Event Types**   | 6 loại × 5 cases = 30 ✅         |
| **MECE Search Memory** | 4 × 2 × 7 × 3 = 168 ✅          |
| **Format messages**    | JSON array (chuẩn API) ✅         |
| **Số turns**          | 5-10 turns/case ✅                 |
| **Ngôn ngữ**         | Trẻ em giao tiếp với Pika ✅    |

Cả 2 file Excel đã được đính kèm và sẵn sàng sử dụng!
