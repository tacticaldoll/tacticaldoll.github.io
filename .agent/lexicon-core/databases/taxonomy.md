# 分類與結構規範 (Taxonomy & Structure)

## 1. 文章結構標準化 (Header Normalization) [SSOT]

為確保全站技術文獻一致性，精煉階段必須將來源報告的「變體標題」強制對位至以下標準詞彙。

### A. 全域通用標題 (Generic Headers)
| 來源變體 (Variation) | 標準標題 (Standardized Header) | 說明 |
| :--- | :--- | :--- |
| `引言` / `前言` / `背景` / `Motivation` | **背景** | 描述問題起源與必要性 |
| `我的發現` / `實踐結果` / `觀察` / `Findings` | **發現** | 技術嘗試後的具體觀測結論 |
| `決策紀錄` / `決策摘要` / `最終方案` / `決定` / `Decisions` | **決議** | 權衡後的技術選擇與路徑 |
| `關鍵教訓` / `避坑指南` / `總結` / `Lessons` | **技術啟示** | 具備普適移植價值的技術點 |
| `後記` / `反思` / `展望` / `結語` / `Conclusion` | **結論** | 最終狀態與未來方向 |

### B. 結構性排除 (Scope Exclusions)
- **技術名詞標題**：若標題本身即為「核心技術術語」（如：`MCP 協議的斷路器機制`），則 **嚴禁標準化**，必須 100% 物理保留。

## 2. 系列命名與註冊 (Series Registry)

### A. 命名格式
- **強制前綴**：`領域：系列名稱` (如 `人機協作：物理填充實踐`)。
- **領域定義**：必須從 `人機協作`, `規範治理`, `專案演化`, `技術思辨`, `工程實踐` 中選擇。

### B. 命名精煉與隔離原則 (Naming Refinement & Isolation)
- **合規前提**：僅有符合系列定義的貼文（即結晶目錄下存在 `guide*.md`）才允許賦予系列名稱。
- **動態精煉**：系列名稱的後半段必須根據當次 Session 的核心技術議題**嚴格精煉**而成，嚴禁使用無意義的泛用詞彙。
- **Session 隔離 (Session Isolation)**：為確保語義邊界的清晰，**嚴禁不同 Session 共用相同的系列名稱**。每一組獨立的 Session 若構成系列，都必須擁有獨一無二的專屬系列命名（例如依據具體實踐目標命名，如 `人機協作：術語引擎重構與語意錨定`），以防檢索時發生語義混淆。

---

## 3. 術語首見與語意擴充 (First-seen & Semantic Expansion)

### A. 首見錨定策略 (First-seen Anchoring)
- **雙語鎖定**：核心技術名詞首次出現，必須執行 `中文 (English)`。
- **跨領域對位**：若術語屬於特定領域（如「人機協作」下的 `物理填充`），首見時應優先引用 `taxonomy.md` 或 `terminology.json` 中的標準語境進行 1-2 句的背景代入，嚴禁 AI 自行發明語境。

### B. 擴充權重原則 (Expansion Weights)
- **加法邊界**：允許針對報告中的「技術斷層」進行補白（例如：原始報告沒寫某工具的背景，AI 可補上）。
- **密度守恆**：擴充內容長度嚴禁超過原始事實段落的 **30%**，以維持技術報告的硬核解析度。

---

## 4. 標籤分類法 (Tagging Reference) [EN-PRIORITY]

為防止語意漂移，標籤應遵循「中英雙語」原則，優先對應術語庫的 `中文 (English)` 格式。

### A. 標籤選取原則 (Tag Selection Principles)
- **首見即引**：文章標籤必須在正文中至少出現一次，且該術語被視為該篇的核心討論對象。
- **雙語對位**：標籤名稱須與 `terminology.json` 中的雙語格式完全一致。
- **密度控制**：單篇文章建議標籤數量為 3-8 個，避免標籤稀釋。

### A. 治理與演化軸 (Governance & Evolution)
- `project-evolution`: 專案演化
- `driving-model`: 驅動模型
- `governance`: 規範治理
- `layered-coexistence`: 層疊共存
- `semantic-isolation`: 語意隔離

### B. 失敗模式與風險 (Failure Modes & Risks)
- `behavioral-accidentalization`: 行為偶然化
- `knowledge-decay`: 知識衰減
- `semantic-resonance`: 語意共振
- `latent-pollution`: 隱性污染
- `conversation-echo`: 對話殘響

### C. 工程實踐與規格 (Engineering & Spec)
- `spec-driven`: 規格驅動
- `code-driven`: 程式碼驅動
- `test-driven`: 測試驅動
- `causal-continuity`: 因果連續性
- `cognitive-capacity-threshold`: 認知容量閾值

### D. 文體與性質 (Genre & Nature)
- `analytical-essay`: 分析論文
- `experience-report`: 經驗報告
- `technical-note`: 技術隨筆
