---
name: publish-article
description: 執行發佈管線腳本，將交接檔轉換為 Hugo 貼文 (Execute publishing pipeline scripts)
argument-hint: "[session_id]"
user-invokable: true
schema: ["../schemas/handoff.posts.schema.yaml", "../schemas/handoff.terms.schema.yaml"]
spec: "../reference/agent-operating-guideline.md"
---

# 發佈技能：執行發佈管線 (Publish Pipeline)

// turbo-all

本工作流位於 `/init-handoff` 之後，負責自動化執行所有 Python 發佈管線。

> [!NOTE]
> 本 Workflow 為純粹的操作執行層。操作意圖與跨工作流邊界請參閱 [agent-operating-guideline.md](../reference/agent-operating-guideline.md)。

> [!IMPORTANT]
> **AI 執行約束 (Bootstrapping)**：在開始執行本工作流前，你必須先讀取 [publish-article.task.schema.yaml](../schemas/publish-article.task.schema.yaml) 內的 `template` 區塊，並將其完整內容複製到你當前會話的 `task.md` 工件中。在後續執行過程中，你必須嚴格打勾追蹤進度，絕對禁止任何步驟跳躍或遺漏。

> [!IMPORTANT]
> **執行前置條件**：在執行本工作流前，必須確保 `.agent-scratch/<session_id>/` 目錄下已經由 `/init-handoff` 建立了 `handoff.posts.json` 與 `handoff.terms.json`，經由人類審查無誤，且 `handoff.posts.json` 的 `status` 已為 `refined`。本工作流不涉及任何 NLP 內容創作 or 萃取。

## 1. 執行管線 (Production Pipeline)

執行「終極 Turbo 流水線」，自動處理基準生成、裝配、術語錨定與審計：

```bash
python3 .agent/scripts/workflows/generate-article/pipeline.py <session_id> --mode ultimate
```

**漸進式模式**（Debug 或 Audit 失敗重試時使用）：

- `--mode baseline`：僅重新從報告產生草稿。
- `--mode finish`：跳過 baseline，直接對現有草稿執行裝配、術語錨定與 Audit。

> [!IMPORTANT]
> **Audit 失敗後，請優先使用 `--mode finish` 重試**，切勿直接重跑 `--mode ultimate` 覆蓋已完成的 baseline 狀態。

## 2. Terminal Gate：全域術語晉升 (Terminology Promotion)

> [!IMPORTANT]
> **全域術語晉升是本 Workflow 唯一且強制之「終端出口閘門」**。不論本次 Session 有無新術語，此步驟皆**必須無條件執行**，以杜絕任何隱性殘留的術語草稿。

```bash
python3 .agent/scripts/domain/terminology/manage.py --promote
```

若有新晉升術語，確認 `.agent/lexicon-core/databases/terminology.json` 已寫入後，將異動提交至 Git，正式完成整個發佈週期。

## 3. 附錄：核心規範提醒 (Reminders)

1. **NLP 不越界**：Handoff 產出後，AI 代理人不再介入內容精煉，一切交由流水線腳本處理。
2. **填充即法律**：禁止合併或刪除物理段落。
3. **治理委派**：所有關於 JSON 元數據、標籤協議與去雙語化標題規範，請參閱 [handoff.posts.schema.yaml](../schemas/handoff.posts.schema.yaml)。
