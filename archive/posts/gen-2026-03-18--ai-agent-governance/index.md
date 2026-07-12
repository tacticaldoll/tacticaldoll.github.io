+++
title = "AI Agent 協作的治理架構 — 從三層模型到知識消解"
date = "2026-03-18T21:00:01+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "本文探討跨子模組產品專案面臨的治理困境，提出由三層模型至知識消解的演化路徑。透過採用 AI 框架原生的規則分域與路徑限定載入機制，實現入口索引與具體規則分離的乾淨架構，並建立每次歸檔後觸發的四步消解循環。"
tags = [
    "經驗報告", # term:ExperienceReport
    "AI 代理人", # term:AiAgent
    "知識衰減", # term:KnowledgeDecay
    "查找順序", # term:DiscoveryRule
    "絞殺者模式", # term:StranglerPattern
    "知識路由", # term:AttributionRouting
  ]
[ai_info]
    [ai_info.generation]
        model = "Claude Opus 4.6"
        agent = "Claude Code VSCode Extension 2.1.72"
    [ai_info.refinement]
        model = "Gemini 3.5 Flash"
        agent = "Antigravity IDE 2.0.4"
+++

<!--more-->

## Background

一個跨子模組的產品專案面臨治理困境：工程規則散落在三個位置 — 專案描述檔、工作流設定檔、知識庫目錄 — 卻沒有定義優先序。AI agent 每次 session 都載入專案描述檔，但架構決策和編碼紀律不在裡面。工作流設定檔裡混合了行為約束和模板格式規則，而行為約束只在特定工作流中注入，日常寫程式碼時不生效。知識庫中有 37 個檔案，部分已被規格文件覆蓋卻沒人清理。

這不是一個「文件不夠多」的問題。恰恰相反 — 文件太多、太散，而且沒有機制讓過時的知識退場。

觸發這次重構的直接原因是：團隊引入了結構化的變更管理系統後，規則和知識的來源從兩個變成三個，混亂程度不減反增。

## Discovery

### 第一幕：集中化 — 把規則塞進永遠載入的檔案

第一個直覺是建立層級：專案描述檔是 Layer 0（永遠載入），工作流設定是 Layer 1（工作流中載入），程式碼是 Layer 2（實作事實）。所有「寫任何程式碼都要遵守」的規則應該在 Layer 0，「只在寫 artifact 時需要」的規則留在 Layer 1。

這個分層邏輯清晰，執行也直接 — 從架構願景文件中提煉 7 條 binding constraints 寫入專案描述檔，建立 6 條工程紀律，精簡工作流設定檔只留模板格式規則。

集中化解決了「去哪裡找規則」的問題，但製造了新的張力：專案描述檔從 120 行膨脹到 280 行，其中混合了兩種截然不同的內容 — 專案概覽（建置指令、打包流程、服務生命週期）和治理規則（架構決策、編碼紀律、日誌規範）。更麻煩的是，Rust 專屬的範例（如 `Resource` 型別、`SafetyPoint` 檢查點）在編輯 shell script 時也被載入，浪費了 agent 的注意力。

### 第二幕：知識開始流動 — 消解優於翻譯

集中化之後，下一個問題浮現：知識庫中有大量中文寫成的知識檔案，按照 AI-readable 文件應為英文的規範，這些檔案語言不對。

最初的想法是翻譯。但在實際操作中發現，翻譯保留了檔案的結構卻沒有保留它的價值 — 一個記錄 Legacy 缺陷的考古筆記，翻譯成英文後仍然是一份考古筆記，它的價值（對新設計的約束）並沒有被安置到正確的位置。

> [!NOTE]
> **Decision Point**: 消解優於翻譯 — 不翻譯原檔案，而是萃取可行動的知識到正確的治理層級，然後刪除來源
> — Alternatives: 原地翻譯（保留結構但不安置價值）；搬移到新目錄（換地方但本質不變）
> — Outcome: 4 個考古檔案被消解為 2 個英文結構化參考表 + 架構決策吸收；過渡期知識庫從 37 個檔案縮減，並建立了每次歸檔後的消解循環機制

這個轉折點確立了一個原則：知識不是搬家，是提煉。每一筆知識都應該流向它最自然的永久位置 — 如果是約束，就進入治理規則；如果是參考資料，就進入結構化參考；如果是規格行為，就進入規格文件。來源檔案不是被搬走，而是被吸收殆盡後消失。

為了讓這個流動機制持續運作，建立了四步消解循環：規格覆蓋掃描 → 標記或刪除已覆蓋段落 → 新**知識路由**（Attribution Routing） <!-- term:AttributionRouting -->到正確位置 → 評估模組消解程度。這個循環在每次變更歸檔後觸發，確保知識庫不會重新累積。

> [!IMPORTANT]
> **知識路由** <!-- term:AttributionRouting --> (Attribution Routing): 將系統的非結構化知識或遺留債務，精準指派並分流至合適的追蹤與管理工具之機制。 <!-- anchor:AttributionRouting -->


### 第三幕：尋找規則的家 — 三次轉向

專案描述檔太臃腫了。規則需要一個獨立的家，但放在哪裡？

第一次嘗試是建立 `governance/` 目錄。結構清晰，每個主題一個檔案。但這是在 AI 框架之外發明一個新目錄 — agent 不會自動讀取它，必須在專案描述檔中寫指標告訴 agent 去讀。這等於是用一層間接引用解決膨脹問題，並沒有根本性的改善。

第二次嘗試是回到原點：既然專案描述檔是唯一保證永遠載入的檔案，也許膨脹是可以接受的代價。但 280 行只是起點 — 隨著其他子模組加入各自的編碼規範（C/C++、前端），膨脹只會加劇。

> [!NOTE]
> **Decision Point**: 採用 AI 框架原生的 `.claude/rules/` 機制，放棄自訂目錄
> — Alternatives: 自訂 `governance/` 目錄（需要手動引導 agent 讀取）；全部留在專案描述檔（膨脹且無法分域）
> — Outcome: `.claude/rules/` 下的所有 `.md` 檔案自動載入，支援 `paths:` frontmatter 限定載入範圍。跨專案規則放 `common/`（永遠載入），子模組規則放 `<submodule>/`（進入該目錄時載入）。不需要發明任何新機制

第三次轉向才找到正確答案。原則很簡單：在發明新機制之前，先確認框架是否已經提供了。AI 框架的 `.claude/rules/` 不僅自動載入，還支援路徑限定 — Rust 規範只在操作對應子模組的檔案時載入，不會在編輯 shell script 時出現。

這個機制同時解決了另一個問題：子模組的治理歸屬。以子模組名稱作為目錄映射（如 `.claude/rules/<submodule>/`），建立了清晰的治理層級 — 根專案的跨專案規則、根專案對子模組的規則、子模組自己的規則，三層各有歸屬。

### 危機：子模組邊界

設計完成後進入實作，立刻撞上 git submodule 的現實約束。

原本的計畫是在提取規則到 `.claude/rules/` 的同時，清理子模組的專案描述檔中重複的段落 — 兩邊保持一致，沒有重複。但子模組是獨立的 git repository，修改它需要一個獨立的 commit，然後根專案更新子模組指標再做一個 commit。兩個 commit 無法原子化 — 如果只合併其中一個，系統處於不一致狀態。

實作了一半後回退，重新評估。

> [!NOTE]
> **Decision Point**: 接受暫時重複作為合理的過渡狀態
> — Alternatives: 同時修改根 repo 和子模組（commit 耦合，無法原子化）；等子模組準備好再開始（延遲根專案治理建立）
> — Outcome: 根 repo 的 `.claude/rules/` 是 authoritative source，子模組中的重複內容標記為 transitional。清理延後到子模組獨立 commit 時處理。重複是有意的設計，不是錯誤

這是整個過程中最重要的教訓之一：追求乾淨架構和尊重現實邊界之間的張力，解法往往不是強行一步到位，而是接受過渡狀態並確保過渡方向明確。

### 終局：治理模型成形

經過三個變更、四次設計轉折，最終模型是：

```mermaid
graph TB
    subgraph "Layer 0 — Always loaded"
        CMD["CLAUDE.md<br/>Governance index"]
        RC["`.claude/rules/common/`<br/>Cross-project rules"]
        RS["`.claude/rules/&lt;submodule&gt;/`<br/>Scoped rules (paths:)"]
    end

    subgraph "Layer 1 — During workflow"
        OS["openspec/<br/>Change lifecycle"]
    end

    subgraph "Layer 2 — When coding"
        CB["Codebase<br/>Implementation facts"]
    end

    CMD --> RC
    CMD --> RS
    RS -->|"paths: scoping"| CB
    OS -->|"specs inform"| CB

    style CMD fill:#e8f5e9,stroke:#2e7d32
    style RC fill:#e8f5e9,stroke:#2e7d32
    style RS fill:#e8f5e9,stroke:#2e7d32
```

專案描述檔從「全文」轉變為「治理入口」— 它描述模型、定義**查找順序**（Discovery Rule） <!-- term:DiscoveryRule -->、說明知識歸位規則，但不再包含具體的工程規則內容。規則住在 `.claude/rules/` 裡，按跨專案和子模組分域管理。知識庫通過消解循環逐步收斂，新知識按性質路由到正確的永久位置。

> [!IMPORTANT]
> **查找順序** <!-- term:DiscoveryRule --> (Discovery Rule): 決定知識或文件查找順序的規則 <!-- anchor:DiscoveryRule -->


## 決議

| # | Decision | Trigger | Outcome |
|---|----------|---------|---------|
| 1 | 建立三層治理架構（Layer 0/1/2） | 規則散落三處無優先序 | 明確的載入時機和覆蓋規則 |
| 2 | 語言邊界：人類審閱 → 正體中文，AI 查詢 → English | openspec/ 子目錄無語言分類 | 可測試的判斷**準則**（Guidelines） <!-- term:Guidelines --> |
| 3 | 消解優於翻譯 | 翻譯不安置價值 | 知識流向永久層，來源消失 |
| 4 | 四步消解循環 | 知識庫持續累積無退場機制 | 每次歸檔後觸發消解 |
| 5 | 採用 `.claude/rules/` 原生機制 | 自訂目錄需手動引導 | 自動載入 + 路徑限定 |
| 6 | 子模組名稱映射治理目錄 | 需要 scoped governance | 清晰歸屬 + 自治路徑 |
| 7 | 接受暫時重複（submodule 邊界） | git 無法原子化跨 repo commit | 過渡狀態明確，方向明確 |

> [!IMPORTANT]
> **準則** <!-- term:Guidelines --> (Guidelines): 強制性的專案準則，指導如何正確地做事 <!-- anchor:Guidelines -->


## Supplementary Knowledge

### 為什麼 `.claude/rules/` 的 `paths:` 限定重要

在多子模組專案中，不同子模組可能使用完全不同的技術棧 — 一個用 Rust，一個用 C，一個用 TypeScript。如果所有規則永遠載入，agent 在編輯 C 程式碼時會看到 Rust 的 `unsafe` boundary rule，這不僅浪費 context window，還可能產生混淆（agent 嘗試套用不適用的規則）。

`paths:` frontmatter 讓規則只在操作匹配的檔案時載入。這不是權限控制 — 任何人都能讀任何規則檔案。這是 **attention management** — 確保 agent 在特定情境下只看到相關的規則。

### 母專案治理子模組：非典型但合理

傳統 git submodule 模式中，母專案只負責 pin 版本，子模組完全自治。但這個專案的子模組都是同一個產品的組件，不存在被其他專案引用的場景。子模組的存在是歷史原因（不同團隊、不同語言），不是因為需要獨立複用。

在這種情境下，母專案作為治理中樞是合理的 — 跨專案的架構決策和編碼紀律自然住在產品層級，不是組件層級。但設計必須保留自治路徑：當某個子模組確實需要獨立運作時，只要把規則檔案從母專案搬到子模組自己的 `.claude/rules/` 即可，不需要改結構。

## Key Lessons

1. **框架原生機制優先** — 在發明自訂目錄、自訂格式、自訂載入機制之前，先確認所用的 AI 框架是否已經提供了等效功能。`.claude/rules/` 比 `governance/` 更好，不是因為功能更強，而是因為它不需要任何額外的引導就能運作。

2. **消解優於翻譯** — 當知識需要從一個位置遷移到另一個位置時，不要原封不動地搬。提煉出可行動的內容，安置到它最自然的永久位置，然後讓來源消失。翻譯保留結構但不保留價值；消解提取價值但不保留結構。

3. **過渡狀態是設計，不是妥協** — 當現實約束（如 submodule commit 邊界）阻止一步到位時，明確的過渡狀態比強行的原子性更好。關鍵是：方向明確（authoritative source 在哪裡）、退場條件明確（什麼時候清理重複）、過渡是有意的（不是忘記做了）。

4. **治理入口與治理內容分離** — 永遠載入的檔案應該是索引（描述模型、定義查找順序 <!-- term:DiscoveryRule -->），不是全文（包含所有規則）。這讓入口保持精簡，同時允許內容按需載入和獨立演化。

5. **以消費者劃分語言邊界** — 「人類審閱 → 本地語言，AI 查詢 → English」是一個可測試、可持續的判斷準則 <!-- term:Guidelines -->，比逐目錄定義語言規範更穩定。當新目錄出現時，問一句「誰是消費者」就能決定語言。