# 貼文草稿格式規格書 (Post Draft Format Specification)

本文件定義由全域認知工具（如 `fornax-write-learning-report`）或人類撰寫、存放於 `.agent-scratch/` 下的 Markdown 草稿格式標準。下游發佈管線（`/init-handoff` 與 `/publish-article`）以此格式作為唯一合約輸入。

---

## 1. 檔案位置與命名慣例 (File Location & Naming)

- **路徑格式**：`.agent-scratch/<session_id>/<article-slug>/report.zh-TW.md`
  - `<session_id>`：標準格式為 `YYYY-MM-DD`（同日多會話則為 `YYYY-MM-DD-a`, `YYYY-MM-DD-b`）。
  - `<article-slug>`：該主題的英文語意目錄名（短橫線分隔，如 `governance-drift-mechanisms`）。
  - 檔案名稱一律為 `report.zh-TW.md`。
- **系列導讀 (可選)**：
  - 若該 session 包含多篇關聯文章，於會話根目錄提供 `guide.zh-TW.md`（或 `guide.md`）。單篇獨立文章則省略導讀檔。

---

## 2. 表頭元數據規範 (Provenance Header Block)

每份草稿報告的開頭**必須**包含標準的 Provenance 表頭區塊，以供 `prepare_handoff.py` 自動提取時間、體裁與生成資訊（發布管線會在生成 Hugo 貼文時自動剝離此表頭，不洩漏至讀者端）：

```markdown
# [文章標題 / Title]

**Structure**: [Experience Report | Analytical Essay | Technical Note]
**Date**: [YYYY-MM-DDTHH:MM]
**Source**: [conversation | notes | reconstruction]
**Model**: [平台或模型名稱，例如 Claude 3.7 Sonnet]
**Agent**: [代理工具名稱與版本，例如 Antigravity 2.0]

---
```

### 欄位要求：
1. **`# [文章標題]`**：頂層唯一的 H1，代表文章正標題。
2. **`**Structure**`**：體裁宣告，必須精確對應三大體裁之一：
   - `Experience Report`（經驗報告）
   - `Analytical Essay`（分析論述）
   - `Technical Note`（技術筆記）
   *(註：此宣告直接決定 Hugo 貼文的 `tags[0]` 體裁標籤)*
3. **`**Date**`**：ISO 時間字串（精確至分鐘），作為發布時序的排序基準。
4. **`**Model**`** 與 **`**Agent**`**：誠實宣告生成環境與版本號（需含版本數字，如 `2.0`）。

---

## 3. 三大體裁結構與標準章節 (Genres & Canonical Structures)

草稿內部的章節標題（H2）應符合以下標準體裁結構，並與 `.agent/lexicon-core/databases/taxonomy.json` 中的標準標頭（`header_normalization`）對齊：

### 體裁一：經驗報告 (Experience Report)
適用於記錄多階段工程實踐、試錯過程、權衡取捨與具體決策。
- `## 背景 (Background)`：前置狀態、觸發事件、問題情境。
- `## 發現 (Discovery)`：分階段的試錯、轉折與推進歷程。
- `## 決策總覽 (Decisions)`：關鍵決策點、被否決的替代方案與採納理由。
- `## 補充知識 (Supplementary)`：輔助理解決策的背景技術知識。
- `## 技術啟示 (Technical Insights)`：可遷移的工程原則與經驗總結。

### 體裁二：分析論述 (Analytical Essay)
適用於從客觀現象推導本質、建立概念框架、反思理論邊界。
- `## 導言 (Introduction)`：核心命題、問題意識、論述焦點。
- `## 分析 (Analysis)`：多維度拆解、機制推導、因果鏈條剖析。
- `## 反思 (Reflection)`：適用限制、張力、極端反例與反直覺警示。
- `## 實務對比 (Practical Contrastive Examples)`：橫向對照多種範式或實務實踐。
- `## 結論 (Conclusion)`：昇華後的通用原理與核心論點收束。

### 體裁三：技術筆記 (Technical Note)
適用於針對特定技術問題、實驗數據、漏洞排查或關鍵修復的深度解構。
- `## 問題 (Problem)`：具體故障現象、重現條件、錯誤表面。
- `## 調查 (Investigation)`：排查路徑、驗證實驗、假設排除。
- `## 發現 (Finding)`：根因分析、不變式破壞機制、關鍵技術洞察。
- `## 應用 (Application)`：防禦工程、修復方案、驗證代碼與後續防線。

---

## 4. 散文品質與格式慣例 (Prose & Formatting Standards)

1. **散文只寫一次 (Write-Once Prose)**：
   - 貼文正文即為草稿正文。發布管線只注入術語錨點與後設資料，**絕不改寫正文任何一句話**。因此論述嚴密性、文字流暢度必須在草稿階段完備。
2. **首次術語雙語標記**：
   - 核心專用術語在正文首次出現時，建議採用 **中文（English）** 雙語標記，以利 NLP 萃取與發布管線自動識別新詞。
3. **消除孤兒元件**：
   - 任何表格、Mermaid 流程圖或代碼區塊前後，必須有引言 prose 與後續解讀文字，杜絕未經說明的裸露圖表。
4. **禁止提前人工標記**：
   - 草稿散文中**嚴禁手動寫入** `<!-- term:/anchor: -->` 錨點標籤，亦不手動建立術語定義區塊；所有術語錨定與語意防線全權由 `/publish-article` 管線自動完成。
