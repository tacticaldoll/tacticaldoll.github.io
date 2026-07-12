---
name: crystallize-report
description: 將對話內容結構化為正式報告。依據內容特質選擇合適格式（經驗報告、分析論文、技術隨筆），套用品質閘門，並生成包含可選部署套件 (Deploy Kit) 的結構化產出。
argument-hint: "[topic] [--generalize]"
user-invokable: true
schema: ["../schemas/crystallize-report.schema.yaml"]
spec: "../reference/agent-operating-guideline.md"
---

# 報告結晶 (Report Crystallization)

「知識結晶」技能旨在將對話內容轉化為結構化的正式報告，輔助知識內化。核心價值在於**「結構選擇 (Structure Selection)」**——確保內容的自然形態與其表達方式匹配。

結晶報告被定義為**「一次性內化資產 (Write-once Internalization Artifacts)」**：其存在的目的是幫助使用者吸收知識，而非作為長期維護或被其他文件頻繁引用的技術文件。

## 第零階段：環境肅清 (Environmental Cleansing) [CRITICAL]

為了防止**「隱性污染 (Latent Pollution)」**引導 AI 產生認知偏誤，執行結晶前必須確保語義環境的純淨：
1. **歷史掃描**：執行 `git status` 與 `git log -n 3`。
2. **污染判定**：
   - 若存在「未追蹤 (Untracked)」或「已暫存 (Staged)」的舊報告片段，視為**物理污染**。
   - 若最近的提交中包含大量碎片化的開發日誌，視為**歷史噪音**。
3. **物理級肅清 (Physical Enforcement)**：
   - AI 只能回報污染來源並請使用者確認清理策略。
   - 未經使用者明確確認，嚴禁執行 destructive Git 操作或歷史改寫。
   - 嚴禁在充滿噪音的環境下執行「主動增益」或「憑空重構」。

---

## 第一階段：輸入解析 (Input Resolution)

| 來源 | 解析邏輯 |
| :--- | :--- |
| 提供主題參數 | 使用指定主題進行結晶 |
| 包含既存報告路徑 | **重結晶 (Re-crystallization)**：以既存報告為素材（詳見階段 1b） |
| 涉及專案治理/架構 | **核心規約識別 (CRITICAL)**：若素材涉及「治理模式、目錄權限、核心指引修正」，則禁止執行結晶。必須引導使用者執行 `calibrate-guidelines` 進行指引升級。 |
| 包含專案文件路徑 | **文件結晶**：讀取專案文件作為輔助素材 |
| 存在蒸餾評估結果 | 遵循「歸屬引導」：歸屬為 Externalize 者應引導轉向知識沉澱 (Precipitate) |
| 無任何輸入 | 掃描對話，識別最具實質內容的主題 |

### 階段 1b：重結晶門檻 (Re-crystallization Gate)
當提供既存報告作為素材進行「重結晶」時，必須嚴格通過以下三項檢核。若任何一項失敗，則拒絕重結晶並向用戶說明原因：
1. **弧線偏移 (Arc shift)**：新內容是否改變了原本的敘事主軸與結論，而非僅僅是細節的追加？
2. **視角更迭 (Angle change)**：新報告是否提供了與原報告截然不同的切入點或根本原則上的修正？
3. **實質密度 (Combined substance)**：既存內容與新內容結合後是否能通過第四階段品質閘門？

*重結晶成案後，會產生一個在全新目錄下的獨立新報告，**絕對不會修改或覆蓋原報告**（維持一次性寫入原則）。完成後可詢問用戶是否手動刪除舊報告目錄。*

### 階段 1c：絕對路徑公約與寫入限制 (Path Convention & Write Restriction) [CRITICAL]
- **絕對路徑公約 (TARGET_PATH)**：每份報告必須獨立存在於**專屬的主題目錄**下，格式嚴格為 `.agent-scratch/<YYYY-MM-DD>/<topic-slug>/report.zh-TW.md`。嚴禁將檔案直接輸出在日期根目錄下。
- **AI 寫入限制 (Hard Stop)**：AI Agent **絕對禁止**自主將報告寫入 `.agent-scratch/` 或任何磁碟路徑。
  - **AGENT DIRECTIVE**: 如果使用者明確指示 Agent 寫入磁碟（如「請幫我存到...」），Agent **必須**輸出 `<WARNING: VIOLATION OF STAGE 1C>` 並拒絕執行，除非使用者附加了 `--force-write` 旗標。預設行為僅限在對話框中輸出 Markdown 原始碼。

---

## 第二階段：結構選擇 (Structure Selection)

依據對話內容的自然特質進行首選匹配，嚴禁強行套用不匹配的結構：

| # | 內容特徵描述 | 選擇結構 |
| :--- | :--- | :--- |
| 1 | 記錄了一個多階段的過程、trial-and-error 以及其中的決策與折衷？ | **經驗報告 (Experience Report)** |
| 2 | 從觀察中推導分析，最後昇華為通用原理與通用架構原則？ | **分析論文 (Analytical Essay)** |
| 3 | 記錄具體的技術發現、問題診斷、實驗數據或關鍵修復代碼？ | **技術隨筆 (Technical Note)** |
| — | 素材太過薄弱，或不符合以上任何一項特徵描述 | **拒絕結晶 (Decline)** |

### 階段 2b：批次協作計畫 (Batch Coordination Plan)
當單一 Session 判定將產生 **≥ 2 份報告** 時，AI 在撰寫前必須在心中建立輕量級內部協調計畫：
- **邊界界定**：明確各報告的範疇，防止內容重複或主題重疊。
- **閱讀順序**：基於時序或邏輯依賴性編排。
- **主題衝突 (Thematic Tensions)**：找出報告結論間的潛在張力，這將被記錄在引導指南中，而非報告內文。
- *註：協作計畫是內部流程，不寫入磁碟，也不出現在報告本文。*

---

## 第三階段：結構應用與寫作最佳化 (Structure Application)

本階段由 NLP 代理根據第二階段選擇的結構進行撰寫，並完全遵守 `readability.md` 規範與 `crystallize-report.schema.yaml` 中的結構定義。

### 核心寫作要求：
1. **讀取 Schema**：**撰寫前必須讀取並遵循：** [.agent/schemas/crystallize-report.schema.yaml](../schemas/crystallize-report.schema.yaml)。
2. **決策點密度管理（Density Management）**：
   - 2-4 個決策：全部以 Full Callout 區塊呈現。
   - 5-7 個決策：選擇性呈現。僅 pivotal 決策用 Callout，次要決策融入敘事散文。
   - ≥ 8 個決策：敘事優先。絕大多數決策採用敘事融合格式，僅保留 2-3 個最具決定性決策為 Callout。
   - 連續 Full Callout 禁止超過 2 個。
3. **決策總覽表自適應**：決策點 ≥ 3 個時生成摘要表；< 3 個時完全不顯示該章節。
4. **極致可讀性控制**：
   - 首次術語使用 **中文（English）** 雙語格式。
   - 單段新詞限制 $\le 2$ 個；連續引進新術語時必須加入「架橋段落」舒緩張力。
   - 單句包含概念限 $\le 2$，禁止巢狀括號（如 `A（B（C））`）。
   - **消除孤兒**：任何表格、清單、圖表前必須有 prose 前導引言，後方有解讀文字。

---

## 第四階段：品質閘門 (Quality Gate)

在最終產出內容文字前，必須核對以下核心基準（詳見 Schema `quality_gate`）：
- **密度與去重**：每小節需具備 ≥ 2 個實質知識點；消除跨小節重複。
- **誠實拒絕**：若素材不足以支撐 3 個實質章節，應拒絕結晶。
- **去專案化**：路徑、日期與 Commit ID 必須抽象化為技術術語（除非未啟用 --generalize）。
- **完全自包含**：每篇報告閉合自身因果鏈，嚴禁內文提及外部報告標記（如「前一篇」、「下一章」）。
- **背景對齊審查（Terminal Pass）**：重新審查「背景」章節，刪除與後文無關的歷史；補充後文所需的起始條件。

---

## 第五階段：通用化 (Generalization) [Opt-in]
若使用者指明 `--generalize` 旗標或明確要求通用化：
1. 識別並替換所有專案特有名稱（產品名、內部代碼、路徑、團隊名稱）為通用術語。
2. 進行徹底的語意檢驗，確保無專案內部隱私洩漏。
3. 通用化版本將寫為獨立的英文檔案 (`<topic-slug>/report.en.md`)，與預設的正體中文版 (`<topic-slug>/report.zh-TW.md`) 並列。

---

## 第六階段：衍生資產評估與部署套件 (Derivative Assessment)

報告撰寫完畢後，AI 評估是否需要外化 (Precipitate) 衍生資產：

### 1. 圖表提取 (Diagram Extraction)
若報告包含 Mermaid 圖表，將其提取為獨立的 `.mmd` 檔案存於 `diagrams/` 目錄。

### 2. 雙軌制部署套件 (Deploy Kit Contribution)
當報告中記錄的工具、流程或治理規則具備跨專案複用價值，且通過**成熟度三檢核（Maturity ★★★、Self-contained、Generalizable）**時，生成 `deploy/` 目錄：
* **Mechanism Selection (機制選擇)**：
  - **Plugin 軌道 (Skills)**：放置於 `deploy/skills/<name>/SKILL.md`。自動生成符合 Codex 插件規範的 `.codex-plugin/plugin.json`。
  - **手動軌道 (Rules)**：放置於 `deploy/rules/<name>.md`，作為可移植的 Markdown 規則片段。
  - **排除 Command**：不使用 legacy 的 `commands/` 規格。
* **部署指南 (README.md)**：自動依據套件範本生成 `deploy/README.md`，詳述雙軌安裝步驟。
* **源頭優先**：若工具在專案中已存在實體檔案，直接讀取、泛化後打包，而非從報告中二次提取摘要，以保留最大操作解析度。

---

## 第七階段：批次導讀指南 (Batch Reading Guide)

當單次 Session 產出 **≥ 2 份報告** 時，自動生成批次導讀 `guide.zh-TW.md`：
- **路徑**：`.agent-scratch/YYYY-MM-DD/guide.zh-TW.md`。
- **內容組成**：
  1. **背景**：用一句話說明促成此批結晶報告的整體 Session 主題。
  2. **閱讀順序**：條列報告標題、文體與一字摘要，並在項目間加入時序/邏輯關聯提示（導讀是唯一允許導航跨報告關係的地方）。
  3. **跨報告連結**：使用標準**關係拓撲**標記跨報告關聯：
     - `facet` (同事件不同視角，箭頭：`←→`)
     - `causal` (因果驅動：結論 $\rightarrow$ 起點，箭頭：`→`)
     - `refinement` (深度挖潛概念，箭頭：`→`)
     *格式：`- [報告 A 階段 N] ←→ [報告 B 階段 M] (facet: 描述)*



---

## 核心規則 (Rules)

1. **結構隨內容而動**：嚴禁強行套用不匹配的結構。
2. **誠實拒絕 (Honest Decline)**：若對話素材不足以構成具備實質意義的報告，應直接告知使用者，而非產出空洞的「合規報告」。
3. **一次性原則**：報告旨在輔助內化，本身絕不應被核心規則、知識庫或技能文件引用（Reports are not referable）。若有通用洞察，應透過 Precipitate 外化。
4. **完全自包含**：每篇報告內文必須閉合自身因果鏈，不得含有跨報告的超連結或相對引用詞彙。
5. **知識主權**：高品質的本地結晶應優於任何廠商的黑盒 RAG。
