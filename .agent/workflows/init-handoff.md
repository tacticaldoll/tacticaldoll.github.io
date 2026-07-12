---
name: init-handoff
description: 讀取草稿報告並透過 NLP 萃取元數據，初始化發佈交接檔 (Initialize Publishing Handoff via NLP)
argument-hint: "[session_id]"
user-invokable: true
schema: ["../schemas/handoff.posts.schema.yaml", "../schemas/handoff.terms.schema.yaml", "../schemas/init-handoff.task.schema.yaml"]
spec: "../reference/agent-operating-guideline.md"
---

# 初始化交接檔 (Init-Handoff)

本工作流為發佈管線的**「純粹認知與萃取層」**。它負責閱讀非結構化的草稿報告，運用 NLP 能力進行重構，並產出兩份符合 Schema 的 JSON 交接檔，供人類審查與後續管線使用。

> [!IMPORTANT]
> **AI 執行約束 (Bootstrapping)**：在開始執行本工作流前，你必須先讀取 [init-handoff.task.schema.yaml](../schemas/init-handoff.task.schema.yaml) 內的 `template` 區塊，並將其完整內容複製到你當前會話的 `task.md` 工件中。在後續執行過程中，你必須嚴格打勾追蹤進度，絕對禁止任何步驟跳躍或遺漏。

## 0. 第零階段：Handoff 初始化與萃取 (Stage 0: NLP Handoff Initialization)

請依據 `task.md` 中的 10 個步驟進行宏觀與微觀解析。特別注意以下 NLP 核心職責：

### 0-A. NLP 標題重塑 (Series Styling)
若存在 `guide.md`，你**嚴禁**照抄搬運來的空泛標題（如「XX 系列」）。你必須發揮敘事能力，產出具備高度反思性的風格標題，並寫入 `handoff.posts.json` 的 `metadata.series` 中。
**強制風格格式**：`[核心主題]：[自由發揮的敘事化副標題]`

### 0-B. 時序與來源資訊（腳本自動處理，AI 無需手填）
- **時間基準**：各篇 `date` 由 `prepare_handoff.py` 自動產出 —— 以該報告頭部 `**Date**:`（格式如 `2026-03-28T17:45`）的「年月日時分」為基準，並把 session 內的排序序號寫入秒數槽（如 `:01`, `:02`，用以打破同分鐘並列、鎖定發佈排序），補上 `+08:00` 成完整 ISO 8601（如 `2026-03-28T17:45:03+08:00`）。AI **嚴禁**自行虛構或填寫 `date`。
- **來源資訊**：`ai_info.generation`（`scope` / `model` / `agent`，分別對應報告頭部 `**Structure**:` / `**Model**:` / `**Agent**:`）同樣由 `prepare_handoff.py` 以 regex 萃取並寫入（會覆蓋 AI 內容），AI 無需手動掃描填寫。

### 0-C. 術語提取與描述補全 (Automated Term Extraction & NLP Description)
自動掃描是主來源，但它只認 `中文(EN)` 雙語括號與 `**粗體**` 兩種標記；對沒有這類標記的報告（常見於外部模型產出的草稿）會抓不到任何詞。腳本已用兩道補強縮小盲區，但**最終守門人仍是你的 NLP 判讀**。請依序執行：
1. **執行掃描與收割**：在終端機執行 `python3 .agent/scripts/workflows/generate-article/prepare_handoff.py <session_id>`。腳本會 (a) 掃描雙語/粗體詞彙，並 (b) 收割 `series-map*.md` / `guide*.md` 之 `## Metadata` TOML `tags` 作為高信心候選（`[METADATA HARVEST]`），funnel 進 `discovered`。
2. **執行精煉**：接著執行 `python3 .agent/scripts/workflows/generate-article/refine_handoff.py <session_id>` 將候選移入 `locked` 陣列。
   > [!WARNING]
   > **零術語守門 (Term-Starvation Gate)**：若終端機印出 `[WARNING] 0 locked terms`，代表報告既無雙語/粗體標記、又無 series-map/guide 可收割。具實質內容的報告幾乎不可能零術語——你**必須**親自閱讀報告，將核心術語以 `zh / en / description` 寫入 `handoff.terms.json` 的 `declared` 陣列後重跑精煉，嚴禁直接零術語交接。
3. **NLP 補寫 en + 描述與純化**：新術語會被腳本標記為 `PENDING_REFINEMENT`（並中斷精煉），且**收割自 metadata tags 的詞其 `en` 為空字串**。你必須讀取 `handoff.terms.json`，為所有 `locked` 內描述為 `PENDING_REFINEMENT` 的術語補上**正規化的 `en`（Title Case）與 `description`**。
   > [!IMPORTANT]
   > **純化與離手原則**：確保寫入的術語為「純淨名詞」（無過渡贅字）。若自動提取出的術語包含贅字（如「這是選擇性注意力」、「在強一致性」），你必須在 `handoff.terms.json` 中將其縮減為純淨名詞（如「選擇性注意力」、「強一致性」），且**絕對嚴禁在此階段修改原始的 `.md` 報告檔案**。只要純化後的名詞仍為原始文本的子字串，後續審計即可通過。
4. **確認通關**：再次執行 `refine_handoff.py <session_id>`，確認終端機不再印出 `PENDING terms need description` 或 `0 locked terms` 的警告。

> [!WARNING]
> **非對稱標籤與防禦性設計**：`metadata.posts[].domain_tag` (AI Tag) **嚴禁 AI 手動填寫**。為防止上下文滲透 (Context Bleed)，該欄位全權交由後續腳本掃描產生。

## 1. 第一階段：封裝交接 (Halt & Handoff)

當你完成 `handoff.posts.json` 的建立，並確保 `handoff.terms.json` 中的 `PENDING_REFINEMENT` 都已解決後，**工作流即刻終止**。
你必須輸出以下提示語，並停止所有後續動作（將主控權交還給人類）：

`✅ Handoff JSON 已初始化完畢。請人類檢閱 handoff.posts.json（特別是系列標題、時間排序與標籤）與 handoff.terms.json。確認無誤後，請手動執行 /publish-article 啟動發佈管線。`
