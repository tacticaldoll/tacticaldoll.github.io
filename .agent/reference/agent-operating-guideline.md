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

- 系列名稱格式依 `init-handoff.task.schema.yaml` 的 `[核心主題]：[敘事化副標題]`；`taxonomy.json` 治理標籤與領域分類，不定義系列前綴，`taxonomy.md` 僅能作為 read-only view。
- 系列宣告資格由 `guide*.md` 的實體存在單一決定；單篇報告 session 為 Standalone，不得在 `series-map.md` 宣告 `series`。
- 禁止建立、手動修復或操作 `terminology.md` 類型的術語投影；術語變更必須對準 `terminology.json` 與 promote 流程。
- Agent 操作意圖只能有一個 active reference：`.agent/reference/agent-operating-guideline.md`，並必須由 `GUIDE.md` 明確引用。
- 領域分類由 `taxonomy.json` 的分類順序決定，依序取首個命中者。此為定案而非產物：較具體的讀法應勝過較寬泛的讀法，即使只命中一個詞。歧義以 `classify_domain_evidence` 的旗標曝光，不得改為加權或最低證據門檻——那會反轉此定案當初為之而立的貼文。
- 引擎宣告的契約由引擎保證，不由呼叫點各自記得。呼叫點不得取消引擎已決定的政策。
- 可驗證規則必須下沉到 schema、script 或 audit；本檔只保留意圖與邊界。

## 7. Audit Commitments

`audit_kb.py` 必須攔截以下漂移：
- 單元套件（`*_tester.py`）必須全部通過。此前沒有任何機制執行它們——本稽核沒有、CI 沒有、工作流沒有、`GUIDE.md` 未曾提及——因此 `lexicon_tester.py` 長期失敗而無人可能發現。套件以 glob 發現而非寫死清單，新套件落地當天即納入覆蓋。
- 單元套件不得寫入儲存庫。光是執行就讓 §10.1 的「草稿零殘留」失效，這正是 `lexicon_tester.py` 每次失敗都把 `TestTerm` 留在草稿裡的原因；hermeticity 以執行前後的工作區狀態比對驗證。

- `reference/` 不得放置 JSON database entity。
- 指引不得引用舊式上一層資料庫相對路徑；資料庫路徑必須指向 `.agent/lexicon-core/databases/`。
- `terminology.md` 不得作為現行操作目標。
- `/publish-article` 任務清單不得重新初始化 Handoff。
- `/publish-article` 任務清單不得要求 AI 填寫 `domain_tag`。
- Markdown 標頭處理不得使用 broad `\s*`。
- 活躍 `handoff.terms.json` 的 `locked.description` 不得含 placeholder。
- `.agent-scratch/` 報告 Markdown 的散文不得含術語錨定（`<!-- term:/anchor: -->`）；錨定是 `publish-article` 對 Hugo 貼文的專屬職責，語法示例須置於程式碼區塊。
- `series-map.md` 不得在無 `guide*.md` 的 session 中宣告 `series`，TOML 與散文兩種形狀皆然；`is_series` 的唯一判準是導讀檔的實體存在。沒有腳本解析 series-map 的 `series`（權威欄位是 handoff 的 `metadata.series`），因此無資格的宣告只會製造內部地圖與已發布貼文的分歧。
- `classify_domain` 不得接收未剝除 provenance 表頭的報告全文；表頭記載的模型與工具名本身就是偵測詞（`**Model**: Claude` 命中大型語言模型，`**Agent**: Antigravity` 命中 AI 代理人），且同一 session 的每份報告值相同，會讓生成後設資料替全部報告決定領域。剝除以 `infra.utils.strip_report_provenance` 為單一定義。
- `GUIDE.md` 不得為系列名稱指定 `taxonomy.json` 的領域前綴；系列命名的 SSOT 是 `init-handoff.task.schema.yaml`，`taxonomy.json` 治理標籤與領域分類。
- 腳本不得以 list 常量作為 `categories` 的預設值；AI 分類清單與其順序（`classify_domain` 依序取首個命中）的 SSOT 是 `taxonomy.json`，程式內的副本會自由漂移。散文提及個別分類不受此限。
- 呼叫點不得把 `classify_domain` 的 `None` 強制成分類（Asymmetric Tagging）。`AI` 本身即為 `taxonomy.json` 的分類值，以它作為缺欄位預設會使 `not in ai_categories` 守衛恆假並整段跳過分類。
- 任何呼叫點不得窗口化分類輸入。權威路徑 `prepare_handoff` 分類完整報告，呼叫點的截斷會讓同一篇文章依到達者不同而得到不同領域。
- 分類不得改為加權或門檻決勝：優先序較低但命中較多的分類仍須落敗。
- `classify_domain` 與 `classify_domain_evidence` 必須是同一個決定，且歧義旗標不得為死碼。兩套並行實作會漂移，使歧義回報描述一個貼文並不具備的領域。
- 組裝時因 `TAG_SCAN_LIMIT` 或 `TAG_CAP` 被丟棄的候選標籤必須逐筆命名。去重（與 genre／領域標籤重複）不在此限。
- 標籤候選的去留不得由字串長度決定。GUIDE §3.2 將 Level 1 定為優先標籤，依長度排序會讓 Level 1 術語在 `TAG_CAP` 處輸給較長的 Level 2 術語。
- Level 3（IGNORE_LIST）術語不得進入標籤候選，也不得出現在丟棄報告中。`anchor_by_display` 依政策拒絕它們，那不是損失；報進損失通道只會淹掉真正的損失，與去重同屬豁免。
- `.antigravityignore` 與 `GUIDE.md` 的 `目錄保護絕對規則` 必須指名同一組受保護目錄。忽略清單多出未經宣告的路徑，或宣告了絕對保護卻未列入忽略清單，兩者皆為漂移；後者使宣告看似已被強制，而 GUIDE 所委派的機制並未涵蓋該路徑。
- `GUIDE.md` 的知識漏斗必須指名 `distill-knowledge` 且排在 `crystallize-report` 之前。評估是結晶的前置條件；漏斗漏掉評估級，會讓結晶跑在未經評估的素材上。
- `GUIDE.md` §10.2 不得對 `crystallize-report` 拒絕結晶的素材要求結晶報告。該工作流第一階段禁止結晶治理素材並導向 `calibrate-guidelines`；兩條規約對同一次變更指向相反流程時，實際結果取決於執行者先讀到哪一條。
