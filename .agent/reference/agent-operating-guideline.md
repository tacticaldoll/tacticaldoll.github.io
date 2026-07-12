# Agent Operating Guideline

本文件是 AI Agent 的單一活躍操作指引。它描述意圖、邊界與永久防線；具體欄位結構、任務清單、腳本行為與物理攔截分別由 `.agent/schemas/`、`.agent/workflows/`、`.agent/scripts/` 與 audit 工具承接。

## 1. Authority Model

Agent 冷啟動時以 `GUIDE.md` 為入口；`GUIDE.md` 再引用本檔作為 Agent 操作層 reference。

- `GUIDE.md`: 專案級最高入口，定義網站、內容、Git、受保護目錄與冷啟動導航。
- `.agent/reference/agent-operating-guideline.md`: Agent 操作意圖、跨工作流邊界與永久防線。
- `.agent/schemas/`: 欄位結構、所有權、mutation policy。
- `.agent/workflows/`: 可呼叫工作流入口與任務順序。
- `.agent/scripts/`: 確定性執行、檢查與資料庫操作。
- `.agent/lexicon-core/databases/`: 術語、分類、規則等 SSOT。

本檔為 non-executable reference。若本檔與 schema/script/audit 的具體規則衝突，先以可驗證層為準，並透過 `calibrate-guidelines` 回補本檔。

## 2. Physical Layer Boundaries

- `reference/`: 放置人類與 Agent 可讀的操作意圖、邊界與永久防線。
- `schemas/`: 放置 JSON/YAML/Markdown 產物的結構契約。欄位 ownership 必須在 schema 中明示。
- `lexicon-core/databases/`: 放置可被腳本讀寫的 SSOT。Agent 不得繞過 schema 或專屬腳本直接發明資料庫狀態。
- `scripts/`: 放置確定性操作。腳本只能消費 schema/database/reference 的契約，不得以啟發式猜測取代 Handoff 或術語庫。
- `.agent-scratch/`: 原始資料、結晶報告與 Handoff 會話狀態。Agent 只能在人類明確引導下寫入。

## 3. Workflow Boundaries

### distill-knowledge

- 職責：客觀評估對話中的可萃取知識價值。
- 輸出：只輸出評估表。
- 禁止：不得起草文章、不得建檔、不得建議下一步、不得引用專案資料夾或其他工作流。

### crystallize-report

- 職責：把對話或素材轉成內部知識報告。
- 語氣：嚴謹、客觀、高密度、自包含。
- 禁止：不得混入 `publish-article` 的口語寫作風格；不得把報告互相引用成系列文章正文；報告本文不得經術語錨定處理——散文中不得出現 `<!-- term:/anchor: -->` 錨點、`（English）` 雙語錨定或 `> [!IMPORTANT]` 術語定義框（術語錨定是 `publish-article` 對 Hugo 貼文的專屬職責）。說明用的語法示例必須置於程式碼區塊內。
- 例外：批次導讀 `guide.zh-TW.md` 可以記錄跨報告閱讀順序，但報告本文必須自包含。

### init-handoff

- 職責：將結晶報告萃取為 `handoff.posts.json` 與 `handoff.terms.json`。
- NLP 權責：標題、摘要、一般 tags、`rules.headers`、`rules.redactions`、`rules.sublimations`、`terms.declared`。
- Script 權責：`prepare_handoff.py` 掃描術語與禁語；`refine_handoff.py` 晉升 locked terms 並攔截 placeholder。
- 禁止：AI 不得填寫 `domain_tag`。
- 停機：Handoff 完成後必須停止，交還人類審查。

### publish-article

- 職責：消費已審核且已 refined 的 Handoff，產生 Hugo 貼文，執行術語錨定、審計、補庫與終端晉升。
- 權威輸入：`.agent-scratch/<session_id>/handoff.posts.json` 與 `handoff.terms.json`。
- 禁止：不得重新初始化 Handoff；不得重新執行 `/init-handoff` 的 NLP 補寫職責；不得直接修補輸出文章以掩蓋 pipeline bug。
- 終端閘門：必須執行 `python3 .agent/scripts/domain/terminology/manage.py --promote`。

### calibrate-guidelines

- 職責：維持 `GUIDE.md`、reference、workflow、schema 與 scripts 的一致性。
- 原則：規則必須盡量物理化。能被 audit 檢查的規則不得只停留在敘事文字。
- 觸發：大規模規則修改、術語庫變更、目錄邊界調整或防線修復後。

### physical-enforcement

- 職責：處理嚴重污染、舊路徑殘留或本地 Git 狀態混亂。
- 限制：任何 destructive Git 行為都必須取得人類明確確認。

## 4. Ownership Matrix

| Surface | Owner | Consumer | Mutation Rule |
| :--- | :--- | :--- | :--- |
| `metadata.posts[].tags` | `/init-handoff` NLP | `pipeline.py` | AI 可在 Stage 0 填寫一般技術標籤。 |
| `metadata.posts[].domain_tag` | `TaxonomyEngine` | `pipeline.py` | AI 不得填寫。 |
| `metadata.posts[].rules` | `/init-handoff` NLP | `pipeline.py` | NLP 寫入語意脫敏與標頭規則；pipeline 只消費。 |
| `terms.declared` | `/init-handoff` NLP | `refine_handoff.py` | 享有 declaration immunity，但不得含敘事雜訊。 |
| `terms.discovered/existing/forbidden_found` | `prepare_handoff.py` | `refine_handoff.py` | Script-managed。 |
| `terms.locked` | `refine_handoff.py` + NLP description | `pipeline.py` | description 不得為空或含 placeholder。 |
| `terminology.json` | Lexicon scripts | 全域管線 | 只能透過 schema 與 promote 流程維護。 |
| `taxonomy.json` | Lexicon/database layer | Taxonomy scripts | 分類 SSOT。`taxonomy.md` 只能是 secondary/read-only view。 |

## 5. Production Intent

- Handoff 是文章生成的會話 SSOT。完成審查後，後續腳本不得回頭猜測文章屬性。
- NLP 負責非結構化理解；Python 負責確定性消費。兩者不得互相越權。
- Stage gate 必須 all-or-nothing；同一 Session 未全數通過術語與 linter 凍結，不得進入發布。
- Scoped lexicon 只在編譯時暫時融合新詞，成功後再透過草稿庫與 promote 晉升。
- Header 相關 regex 不得使用會吞垂直換行的 `\s*`；只能使用 `[ \t]*` 表示水平空白。

## 6. Permanent Gates

- 系列前綴必須依 `taxonomy.json` 的領域定義選擇；`taxonomy.md` 僅能作為 read-only view。
- 禁止建立、手動修復或操作 `terminology.md` 類型的術語投影；術語變更必須對準 `terminology.json` 與 promote 流程。
- Agent 操作意圖只能有一個 active reference：`.agent/reference/agent-operating-guideline.md`，並必須由 `GUIDE.md` 明確引用。
- 可驗證規則必須下沉到 schema、script 或 audit；本檔只保留意圖與邊界。

## 7. Audit Commitments

`audit_kb.py` 必須攔截以下漂移：

- `reference/` 不得放置 JSON database entity。
- 指引不得引用舊式上一層資料庫相對路徑；資料庫路徑必須指向 `.agent/lexicon-core/databases/`。
- `terminology.md` 不得作為現行操作目標。
- `/publish-article` 任務清單不得重新初始化 Handoff。
- `/publish-article` 任務清單不得要求 AI 填寫 `domain_tag`。
- Markdown 標頭處理不得使用 broad `\s*`。
- 活躍 `handoff.terms.json` 的 `locked.description` 不得含 placeholder。
- `.agent-scratch/` 報告 Markdown 的散文不得含術語錨定（`<!-- term:/anchor: -->`）；錨定是 `publish-article` 對 Hugo 貼文的專屬職責，語法示例須置於程式碼區塊。
