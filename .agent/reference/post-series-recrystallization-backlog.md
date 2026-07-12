# 已發布知識再結晶 Backlog

本文件是已發布貼文重新歸納為母系列的草案。它不是既有分類的權威來源，而是後續執行 `recrystallize-post-series` 時的工作入口。

每個母系列應獨立使用一個 session 處理。處理時讀取候選貼文全文，暫時忽略既有 `tags` 與 `series` 的權威性，再從正文反推核心問題、因果鏈與系列角色。

---

## 啟動範例 (Session Kickoff Example)

以下範例可作為每次啟動單一母系列再結晶 session 的起始指令。執行時替換 `Backlog 系列 1`、日期尾碼與目的地。

```text
讀取 .agent/reference/post-series-recrystallization-backlog.md，處理 Backlog 系列 1。

目的地使用：
.agent-scratch/recrystal-<今天日期>-a

輸出規則：
- 這是已發布貼文系列再結晶，不修改 content/，不產生 handoff，不發布。
- session 第一層目錄必須用 recrystal- prefix。
- series-map.md 放在 session 根目錄，作為本次再結晶地圖。
- 若最後判斷只需要一篇主報告，就不需要 guide.zh-TW.md。

若只需要一篇主報告，結構應類似：

.agent-scratch/recrystal-<今天日期>-a/
  series-map.md
  <report-slug>/
    report.zh-TW.md

請先讀候選貼文全文，忽略既有 tags/series 的權威性，從正文反推核心問題、因果鏈、文章角色、合併/移出/保留決策，再輸出 series-map.md 與 slug 隔離的 report.zh-TW.md。
```

---

## Taxonomy 去污染規則

建議移出 tags 的項目以 `recrystallize-post-series` 工作流 §6b（Tags）為唯一權威，本檔不再複述以免漂移；執行去污染時請對齊該清單。

建議保留或重新萃取的主題 tags：

```text
AI 治理
規格驅動開發
棕地專案
知識管理
知識萃取
權威漂移
語意污染
上下文污染
反向指引
因果斷裂
信任邊界
確定性邊界
模型漂移
幻覺
驗證瓶頸
外部裁決
單一事實來源
決定性管線
結構約束
錯誤表面
技術債
領域驅動設計
人機協作
觀念化能力
團隊擴散
Linux 權限
Sandbox
最小權限
術語管理
可逆投影
```

---

## 基礎補齊規則

每個系列再結晶時，不只重寫候選貼文，也要檢查是否缺少「基礎貼文」。基礎貼文的用途是補足系列的前提、定義、因果骨架或反例邊界，使系列不依賴讀者已經知道作者過去的脈絡。

判斷規則：

- 若候選貼文都在討論進階治理，卻沒有說明基本問題，應補一篇基礎導論。
- 若**同一系列內**多篇文章共用同一個前提，應考慮抽成一篇系列內基礎模型文，而不是在各篇重複鋪陳。**跨系列**共用的前提則不抽成中央報告供他人引用，只在用到它的各系列就地自含重述（見「共用前提一致性參考」）。
- 若系列內有大量術語，但沒有定義其差異與邊界，應補一篇概念地圖。
- 若系列主張容易被誤用，應補一篇反例與不適用邊界。
- 若 Mermaid 圖或 example code 能讓核心模型更穩，基礎貼文應優先承載這些結構化表達。

### 展開方向盤點表 (Expansion Inventory — 必填)

為避免基礎補齊與密度展開被當成「有空再做」而略過，每個系列的 `series-map.md` **必須**填寫下表，四個展開類型一個都不能省。每格狀態只能是固定值之一，不允許留空：

| 展開類型 | 狀態 | 歸屬報告 / 去向 |
| :--- | :--- | :--- |
| 共用前提（就地自含） | `本次就地承載` / `不涉及` / `移入後續 backlog` | … |
| 概念地圖 / 詞彙表 | `已承載` / `本次補寫` / `不需要` / `移入後續 backlog` | … |
| 反例與不適用邊界 | `已承載` / `本次補寫` / `不需要` / `移入後續 backlog` | … |
| 結構化資產（Mermaid / example code） | `已承載` / `本次補寫` / `不需要` / `移入後續 backlog` | … |

狀態使用規則：

- 選 `不需要`、`不涉及` 或 `移入後續 backlog` 時，「去向」欄必須寫明理由，否則視為未完成。
- 每個系列既有的「可順勢補齊的基礎方向」是本表的輸入，必須逐項落入上表某一格，不得懸空。
- `series-map.md` 另需列出：本次形成的報告、順勢新增的基礎報告、後續展開方向；不得提及候選貼文、來源 slug 或「吸收／重寫自」這類再生成關係。

---

## Backlog

本 backlog 的順序是再結晶執行順序，而不是主題盤點順序。排序依據是因果鏈：

```text
Agent 本質限制
→ 語意污染
→ 信任與驗證問題
→ 治理與知識架構
→ 驅動模型與決策權威演化
→ 規格與契約
→ 架構與決定性管線
→ 術語治理
→ 人機協作擴散
→ Linux / Sandbox 技術支線
```

### 共用前提一致性參考 (Shared-premise Consistency Reference)

有些前提會被多個母系列用到。在自包含原則下（報告不得要求讀者外部閱讀），這些前提**必須在用到它的每個系列就地自含重述**——複製、不連結，不抽成中央報告供他人引用。本節**僅為撰寫輔助**，不是交付物，報告與 `series-map.md` 都不得引用本節或彼此。

它的唯一用途是：當下列前提出現在某系列時，照此處措辭保持**定義一致**，避免同一概念在不同系列各說各話。

| 共用前提 | 出現於 |
| :--- | :--- |
| `自洽 ≠ 正確 ≠ 可信` | 系列 1、3、7 |
| `Agent 推理最小模型：無狀態生成 → 因果斷裂` | 系列 1，系列 2、6 隱性依賴 |
| `主體 / 客體 / 能力 / 邊界 的最小詞彙` | 系列 4、6、9 |
| `污染傳播路徑：輸入材料 → 模型注意力 → 輸出決策` | 系列 2、7 |
| `確定性邊界 vs 統計執行層` | 系列 3、5、6 |
| `可逆投影：穩定鍵 / 顯示值 / 錨點 / 重貼` | 系列 7，系列 4 隱性依賴 |

使用規則：

- 用到某前提的系列，在其報告中就地給出自含的定義與最小模型（可用 Mermaid 或 example code），措辭與本表一致。
- 不得把任一前提抽成獨立報告再要求其他系列引用；跨系列「重複」這些前提是自包含的必要條件，不是污染。

### 1. Agent 認知限制與錯誤表面

目的：重整因果斷裂、接龍狀態機、局部完備性、錯誤表面與結構約束相關文章。

候選貼文：

- `gen-2026-03-09-a-01--model-enumeration`
- `gen-2026-03-09-a-02--code-driven-limits`
- `gen-2026-03-09-a-03--evolution-dynamics`
- `gen-2026-03-11-a-01--agent-sequence-machine`
- `gen-2026-03-11-a-02--code-cleanliness-risks`
- `gen-2026-03-11-a-03--local-completeness-response`
- `gen-2026-03-24-a-01--causal-chain-break`
- `gen-2026-03-24-a-05--token-namespace-collision`
- `gen-2026-03-27-a-02--structural-constraint-agent-safety`

預期重整問題：

- Agent 的推理限制如何在工程中變成錯誤表面。
- 局部完備性與結構約束如何降低錯誤擴散。
- 命名與 token namespace 如何影響協作。

可順勢補齊的基礎方向：

- Agent 推理限制的最小模型：從無狀態生成到因果斷裂。
- Error surface 的工程化定義：錯誤如何從模型行為進入系統邊界。
- 局部完備性與結構約束的對照圖。
- 可用 example code 展示「開放式自由修改」與「受約束 extension point」的差異。

### 2. 語意污染與反向治理

目的：重整歷史噪音、Git log 污染、命名污染、反向指引與上下文污染相關文章。

候選貼文：

- `gen-2026-03-10-a-01--phantom-reconstruction`
- `gen-2026-03-10-a-02--pollution-landscape`
- `gen-2026-03-10-a-03--reverse-guidelines`
- `gen-2026-06-10-b-03--agent-context-pollution`

邊界候選：

- `gen-2026-06-08-a-01--pollution-not-fate`

預期重整問題：

- 污染如何從歷史、命名與上下文進入 Agent 推理。
- 反向指引如何把負面經驗轉為治理防線。
- 哪些污染應交給術語治理系列處理。

可順勢補齊的基礎方向：

- 語意污染的分類法：歷史污染、命名污染、上下文污染、管道污染。
- 污染傳播路徑圖：從輸入材料到模型注意力，再到輸出決策。
- 反向指引的適用邊界：何時應寫成禁止規則，何時應轉為正向結構。
- 污染清理與污染隔離的差異。

### 3. 信任邊界與驗證瓶頸

目的：重整模型漂移、幻覺、驗證容量、AI code review 與外部裁決相關文章。

候選貼文：

- `gen-2026-05-31-c-01--model-version-migration`
- `gen-2026-05-31-c-02--skill-illusion`
- `gen-2026-05-31-c-03--speed-trap`
- `gen-2026-05-31-c-04--topology-compensation`
- `gen-2026-05-31--silent-semantic-deviation`
- `gen-2026-06-10-b-01--knowledge-recovery-roi`
- `gen-2026-06-10-b-02--conversation-distillation-trust`
- `gen-2026-06-10-b-04--ai-code-review-boundary`
- `gen-2026-06-10-b-05--external-arbitration-workflow`

預期重整問題：

- 自洽輸出為何不等於可信。
- 驗證瓶頸如何成為 AI 協作的核心限制。
- 外部裁決與確定性邊界如何介入。

可順勢補齊的基礎方向：

- 自洽、正確、可信三者的差異。
- 驗證容量模型：生成速度、審查頻寬與風險累積。
- 外部裁決的最小架構：哪些判斷必須移出 LLM 閉環。
- 可用 Mermaid 呈現信任邊界與決策流。

### 4. AI 協作治理與知識架構

目的：重整遺留專案治理、知識分層、權威文件、AGENTS.md 與治理委託相關文章。

候選貼文：

- `gen-2026-03-05-a-01--governance-framework`
- `gen-2026-03-05-a-02--knowledge-extraction-tools`
- `gen-2026-03-05-a-03--authoritative-document-drift`
- `gen-2026-03-12--knowledge-layering`
- `gen-2026-03-18--ai-agent-governance`
- `gen-2026-03-19--governance-delegation-pattern`
- `gen-2026-03-23--aaif-governance`

預期重整問題：

- 權威文件如何避免漂移。
- 治理知識應如何分層。
- Agent 協作中的入口、委派與知識路由如何設計。

可順勢補齊的基礎方向：

- 知識層級模型：對話記憶、報告、規則、流程、程式碼之間的分工。
- 權威來源與委派鏈：何時集中，何時引用，何時拒絕複製。
- 多 Agent 協作的入口網關與路由圖。
- 治理文件的反例：看似完整但會造成權威漂移的文件形狀。

### 5. 規格驅動開發與棕地治理

目的：重整 OpenSpec、SDD、棕地專案、規格稀疏期與確定性契約相關文章。

候選貼文：

- `gen-2026-03-09-b-01--openspec-introduction`
- `gen-2026-03-09-b-02--scaffolding-identification`
- `gen-2026-03-09-b-03--selective-adoption`
- `gen-2026-03-09-b-04--brownfield-dual-layer`
- `gen-2026-03-12--spec-adoption-trap`
- `gen-2026-03-14-a-01--sdd-myths-and-naming`
- `gen-2026-03-14-a-02--descriptive-schema-and-debt`
- `gen-2026-03-14-a-03--layered-governance-and-vision`
- `gen-2026-05-31-b-01--deterministic-trust-boundary`
- `gen-2026-05-31-b-02--coupled-system-conflict-archive`
- `gen-2026-05-31-b-03--governance-feedback-loop`

預期重整問題：

- 規格如何在棕地環境中避免變成瀑布。
- 確定性契約與統計執行層如何分工。
- 規格債與觀察性 schema 如何治理。

可順勢補齊的基礎方向：

- 棕地規格化的最小起點：先描述現況，還是先宣告意圖。
- 規格債、技術債、觀察債務的差異。
- 確定性契約與統計執行層的責任邊界圖。
- 可用 schema 或 pseudo-code 展示約束性規格與觀察性 schema 的差異。

### 6. 架構約束與決定性管線

目的：重整 SSOT、DDD、分類 dispatch、決定性管線、隱式依賴與重構治理相關文章。

候選貼文：

- `gen-2026-03-27-a-01--classification-dispatch-evolution`
- `gen-2026-03-28--data-governance-isolation`
- `gen-2026-03-28--defensive-agent-architecture`
- `gen-2026-03-28--ssot-deterministic-pipeline`
- `gen-2026-03-29--ddd-ai-agent`
- `gen-2026-06-07--eliminating-implicit-dependencies`
- `gen-2026-06-13-a-01--falling-into-the-gravity-well`
- `gen-2026-06-13-a-02--reverse-decompression`
- `gen-2026-06-13-a-03--multi-dimensional-ssot`

預期重整問題：

- 結構約束如何降低 Agent 錯誤表面。
- 決定性管線如何抵抗語意漂移。
- 跨語言重寫與多維 SSOT 如何治理。

可順勢補齊的基礎方向：

- 決定性管線的基礎模型：輸入、驗證、轉換、輸出、審計。
- SSOT 的多維拆分：資料、語意、責任、時間與發布狀態。
- 架構約束與自由生成的對照案例。
- 可用 example code 展示 pipeline gate、schema validation 或 extension point。

### 7. 術語治理與可逆投影

目的：重整機器造詞、術語污染、可逆投影、shape/role 與 symmetric stripping 相關文章。

候選貼文：

- `gen-2026-06-08-a-01--pollution-not-fate`
- `gen-2026-06-08-a-02--precision-is-posterior`
- `gen-2026-06-08-a-03--reversible-projection`
- `gen-2026-06-08--shape-is-not-role`
- `gen-2026-06-08--symmetric-stripping`
- `gen-2026-06-12--frameworks-capture-knowledge-they-do-not-own`
- `gen-2026-06-12--protect-contract-before-expanding-capability`
- `gen-2026-06-12--separating-by-role-owner-and-time`

預期重整問題：

- 術語如何從機器造詞變成污染。
- 可逆投影如何讓延後策展安全。
- 契約、角色、歸屬與時機如何支撐術語治理。

可順勢補齊的基礎方向：

- 術語生命週期：候選、採納、錨定、降級、封存。
- 可逆投影的最小模型：穩定鍵、顯示值、錨點與重貼。
- 術語污染與語意污染的邊界。
- 可用 Mermaid 呈現術語治理管線。

### 8. 人機協作與能力培育

目的：重整介質失真、團隊擴散、觀念化能力、不該用 AI 與人才斷層相關文章。

候選貼文：

- `gen-2026-05-31-a-01--medium-distortion`
- `gen-2026-05-31-a-02--collaboration-externalization`
- `gen-2026-05-31-a-03--implicit-adaptation`
- `gen-2026-05-31--team-scaling-ai-collaboration`
- `gen-2026-06-01--when-not-to-use-ai`
- `gen-2026-06-13--engineering-talent-gap-ai-era`
- `gen-2026-06-13--probabilistic-models-manual-coding`

預期重整問題：

- AI 協作如何改變團隊能力分布。
- 何時不該使用 AI。
- 人才培育與手寫代碼價值如何重新定位。

可順勢補齊的基礎方向：

- AI 協作能力模型：技術技能、觀念化能力、人際技能與驗證能力。
- 何時不用 AI 的判斷矩陣。
- 團隊擴散的成熟度階梯：個人技巧、配對模式、團隊制度、治理文化。
- 手寫代碼在 AI 時代的不可替代角色。

### 9. Linux 權限與 Sandbox 模型

目的：重整 Linux credentials、檔案與 socket、permission denied、最小權限、Unix socket daemon 與 container 權限模型。

候選貼文：

- `gen-2026-06-10-a-01--process-credentials`
- `gen-2026-06-10-a-02--filesystem-socket-objects`
- `gen-2026-06-10-a-03--permission-debug-guide`
- `gen-2026-06-10-a-04--least-privilege-boundaries`
- `gen-2026-06-10-a-05--unix-socket-daemon-authorization`
- `gen-2026-06-10-a-06--container-permission-model`

預期重整問題：

- 權限檢查如何從主體連到客體。
- Sandbox 邊界與最小權限如何建立。
- Linux 權限模型如何支撐 Agent 執行安全。

可順勢補齊的基礎方向：

- 主體、客體、能力、命名空間的最小詞彙表。
- Linux 權限檢查的基本流程圖。
- Sandbox 不是權限開關，而是邊界組合。
- 可用 shell / pseudo-code 展示 process credential、file permission 與 socket authorization 的差異。

### 10. 驅動模型與決策權威演化

目的：重整「驅動模型」後設框架——專案在不同成熟度階段由哪種文件類型持有決策權威，以及這些模型之間的演化、層疊與遷移失敗。本系列與系列 5（規格驅動）正交：系列 5 深入五範式中的「規格驅動」一支，本系列處理五範式的分類、空間與演化動力學；與系列 4（治理知識架構）也不同，後者談知識住在哪一層，本系列談此刻由哪種模型當家。概念位置上，它先於「規格與契約」，因為五範式的演化終點才是規格驅動。

候選貼文：

- `gen-2026-03-09-a-01--model-enumeration`
- `gen-2026-03-09-a-02--code-driven-limits`（與系列 1 共用；系列 1 取其「程式碼文本落差／錯誤表面」切面，本系列取其「程式碼驅動模型的能力邊界」切面）
- `gen-2026-03-09-a-03--evolution-dynamics`

邊界候選：

- `gen-2026-03-12--spec-adoption-trap`（本體歸系列 5；本系列僅引為「儀式化採納」反模式的具體案例）

預期重整問題：

- 如何辨識專案當前的驅動模型（行為對錯有分歧時，團隊去查閱什麼）。
- 五種模型各自的保證、無法保證與失敗邊界為何，「無法保證」如何成為下一模型的問題。
- 測試驅動為何與流程成熟度正交，不應被排入演化序列。
- 演化為何是層疊加法而非替換，遷移時機如何由維護成本交叉決定。
- 三種遷移反模式（跳層、儀式化採納、全域強制）的共同根因。

可順勢補齊的基礎方向：

- 驅動模型的概念地圖：決策權威、能力邊界、語義缺口、正交性、層疊共存、遷移觸發、反模式。
- 統一洞見就地自含：每個模型的失敗 = 把自身權威邊界過度延伸到能力邊界之外。
- 結構化資產可重用既有素材：五範式特徵矩陣、驅動模型空間 quadrantChart、層疊 graph BT。

驅動模型與實踐範例（本系列特有的展開維度）：

本系列素材偏抽象，需以實踐範例把框架釘穩。下列範例屬再結晶範圍內的結構化資產，用來錨定模型，不是操作手冊：

- 辨識診斷走查：以一個模組為例，演示「行為對錯有分歧 → 查閱什麼 → 判定當前驅動模型」。
- 同一功能的範式對照：用 example code / pseudo-code 呈現同一 feature 在程式碼驅動、測試驅動、規格驅動下「真相來源」與「完成判準」的差異。
- 混合狀態範例：核心業務規格驅動、邊緣工具程式碼驅動，落實「矩陣盲點」反思。
- 遷移反模式具體案例：跳層（規格淪為裝飾物）、儀式化採納（spec-adoption-trap）、全域強制（低風險模組被過度工程）。

移入後續 backlog（屬操作層，非本次概念再結晶主體）：

- 驅動模型稽核清單與成熟度評估範本。
- 特定技術棧的遷移 playbook 與真實專案案例研究。

報告數量建議：單篇主報告。三篇候選構成一條緊密因果鏈（定義 → 枚舉 → 演化），實踐範例以結構化資產段落承載即可；拆成多篇會使分類、演化與反模式變成孤立技巧。若實踐範例段落過大，可降級為「概念主報告 + 實踐／診斷導讀」雙篇並加 `guide.zh-TW.md`。
