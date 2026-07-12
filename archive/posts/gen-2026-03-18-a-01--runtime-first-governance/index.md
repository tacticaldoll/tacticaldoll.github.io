+++
title = "Runtime 優先，共存為先 — 多作者 AI 專案的治理妥協學"
date = "2026-03-18T22:30:01+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "一個多人維護的 Rust 專案，在導入結構化工作流約兩週後，面臨一個非技術問題：規則散落在三處，沒有人知道衝突時聽誰的。"
tags = [
    "經驗報告", # term:ExperienceReport
    "AI 代理人", # term:AiAgent
    "硬邊界", # term:WorkspaceBoundary
    "規格稀疏期", # term:SpecSparsePeriod
    "可見性", # term:Visibility
    "準則", # term:Guidelines
  ]
series = ["規範治理：多作者協作與 AI Agent 注意力邊界的熵增與消解"]
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

一個多人維護的 Rust 專案，在導入結構化工作流約兩週後，面臨一個非技術問題：規則散落在三處，沒有人知道衝突時聽誰的。

專案有三個指引來源。CLAUDE.md 是 Claude Code 的專案設定檔，每次 AI agent session 啟動時自動載入，記錄了專案概覽、建置指令、語言規範。**OpenSpec** 的 config.yaml 是工作流工具的設定檔，在執行 `/opsx:propose` 等指令時才載入，記錄了架構決策、編碼紀律、文件格式規則。context/ 是一個手動維護的知識庫目錄，包含 37 個設計文件、歷史教訓、排程規劃。

三者各自演化，各自記錄規則，沒有一份文件宣告它們之間的層級關係。對 AI agent 而言，這意味著每次 session 開始時，它知道「用正體中文寫規格」（CLAUDE.md 說的），但不知道「不得相容舊版 API」（config.yaml 說的，但此刻沒載入）。

同時，專案由多位開發者維護。有人習慣在 context/tech/ 寫設計筆記，有人用 OpenSpec 的 change 流程，有人兩者都不用。任何治理重構都需要在這些習慣之間找到共存空間。

## Discovery

### 第一階段：盤點與分工嘗試

起點是一個直覺的問題：context/ 目錄和 openspec/ 的 specs/ 有內容重疊，應該怎麼分工？

盤點後發現，9 個 openspec specs 覆蓋了 2 個 Epic（E01 路徑模型、E02 目錄瀏覽），但專案共有 13 個 Epic。剩餘 11 個 Epic 的設計知識只存在於 context/tech/ 的 14 個檔案中。簡單地說，openspec 才長出兩成，context/ 還不能拆。

更深的問題浮現：context/tech/ 的設計文件混合了「需求」（系統該做什麼）和「設計原理」（為什麼這樣設計）。前者應該是 specs 的職責，後者是設計文件的職責，但在 context/ 裡它們糾纏在同一個檔案中。逐段拆分是可能的，但工作量巨大且當下沒有收益——specs 還沒長到那裡。

此階段的結論是：context/ 的消解必須跟 specs 的填充同步，不能先於它。

### 第二階段：工具中心化的誘惑

既然 context/ 不能馬上消解，下一個問題是：規則應該集中到哪裡？

OpenSpec 有完整的 schema/rules 機制。config.yaml 的 rules 段可以按 artifact 類型（proposal、specs、design、tasks）定義約束，每次建立 artifact 時自動注入。這看起來是理想的規則中心——結構化、可執行、有模板。

於是第一版方案是：把 context/ 裡的架構決策和工程紀律都搬進 config.yaml rules。搬完之後，CLAUDE.md 只保留專案概覽和建置指令，config.yaml 成為實質上的治理中心。

> [!NOTE]
> **Decision Point**: 以 OpenSpec config.yaml 為治理中心
> — Alternatives: 以 CLAUDE.md 為治理中心（當時被認為「太弱」——沒有結構化 rules 機制）
> — Outcome: 方案被否決。原因見下一階段。

### 第三階段：可見性問題

一個簡單的問題推翻了整個方案：**「config.yaml 的 rules 什麼時候載入？」**

答案是：只在 openspec 工作流指令執行時。`/opsx:propose`、`/opsx:apply` 等指令會調用 `openspec instructions`，此時 rules 注入 agent 的 context。但在其他情境——修 bug、回答問題、做 code review、寫單元測試——rules 不存在。

這意味著「不得相容舊版 API」這條架構決策，只在 agent 建立 openspec artifact 時生效。如果使用者直接要求 agent「加一個向後相容的 adapter」，agent 的 context 中沒有任何東西阻止它執行。

問題不在 config.yaml 的結構化程度，而在它的**可見性**（Visibility） <!-- term:Visibility -->是條件性的。相比之下，CLAUDE.md 在每次 session 啟動時就載入，在整個 session 期間存在，不管 agent 在做什麼。

> [!IMPORTANT]
> **可見性** <!-- term:Visibility --> (Visibility): 知識在開發團隊或 AI 代理人之間的公開與可存取程度。 <!-- anchor:Visibility -->


這揭示了一個判斷**準則**（Guidelines） <!-- term:Guidelines -->：**一條規則的治理能力，不取決於它的結構化程度，而取決於它在需要生效時是否可見。**

> [!IMPORTANT]
> **準則** <!-- term:Guidelines --> (Guidelines): 強制性的專案準則，指導如何正確地做事 <!-- anchor:Guidelines -->


> [!NOTE]
> **Decision Point**: 治理根從 OpenSpec config.yaml 改為 CLAUDE.md
> — Alternatives: 保持 config.yaml 為中心（結構化更好）；雙寫（兩邊都放，維護成本高）
> — Outcome: 採用。CLAUDE.md 永遠載入的特性使它成為唯一能覆蓋所有情境的治理來源。這個修正衍生出三層治理模型。

### 第四階段：三層模型的形成

承認 CLAUDE.md 為治理根之後，config.yaml 和 codebase 的角色自然展開為三層：

- **Layer 0 — CLAUDE.md**：永遠載入。放「寫任何程式碼都要遵守」的規則。
- **Layer 1 — openspec/**：條件載入。放「寫 artifact 才要遵守」的格式規則。
- **Layer 2 — Codebase**：讀寫時可見。實作事實，最終權威。

歸屬判斷只需一個問題：「這條規則是寫任何程式碼都要遵守的嗎？」是 → Layer 0。否 → Layer 1。

Override 規則：Layer 2 > Layer 1 > Layer 0。程式碼是最終事實。如果程式碼和規格不一致，那是 bug，但此刻程式碼是現實。

### 第五階段：與開發者習慣的碰撞

三層模型解決了 AI agent 的治理問題，但專案不只有 AI。多位開發者各有工作習慣，治理重構不能只考慮 agent。

第一個碰撞出現在 context/ 消解策略上。邏輯上，既然 specs 會逐步取代 tech/ 的設計文件，就應該在 tech/ 目錄放一個 README 說明「此目錄正在消解，新知識請寫到 openspec/specs/ 或程式碼 doc comments」，甚至在 CI 中加檢查阻止新檔案寫入。

但部分開發者明確表示：不希望改變現有工作方式。他們習慣在 context/tech/ 寫設計筆記，不想被強制使用 OpenSpec 工作流。

> [!NOTE]
> **Decision Point**: 不攔截 context/ 的新寫入
> — Alternatives: 放 README 攔截 + CI 檢查（技術上可行）；通知作者並要求遷移（流程可行）
> — Outcome: 採用。不放 README、不加 CI 檢查、不通知作者。改為設計循環消解機制——寫入不管，但每次 openspec change 歸檔後執行一輪清理。

這個妥協不是退讓，而是辨認出一個事實：**CLAUDE.md 治理的對象是 AI agent，不是人類開發者。** 對 agent，CLAUDE.md 是強制性指引。對人類，它只是可選參考。兩者的治理力度本來就不對稱，設計時應該接受這個不對稱，而非試圖統一。

第二個碰撞出現在子模組邊界上。專案有多個 git submodule，其中只有一個核心服務模組由本專案治理，其餘各自獨立。最初的方案是在任務文件中列出「Out of Scope」負面清單，明確寫出不碰哪些子模組。

但這引發了另一個問題：agent 讀到負面清單時，會知道那些子模組的存在，進而可能去探索它們。這與注意力工程有關（另一份報告詳述），但背後同樣是妥協的考量——提及子模組名稱不僅影響 agent，也暗示了「這些子模組需要被考慮」，增加了未來開發者的認知負擔。

最終採用正面範圍定義：只列出 root 擁有的目錄和唯一的實作目標子模組，其餘不提及。CLAUDE.md 的子模組表格也被刪除。

### 第六階段：治理層級的自我宣告

三層模型設計完成後，最後一個問題是：治理層級本身要不要寫入 CLAUDE.md？

如果不寫，治理層級只存在於設計者的腦中（以及這次對話的 artifacts 裡）。未來的 agent 或開發者不會知道為什麼規則分散在 CLAUDE.md 和 config.yaml 兩處，也不會知道衝突時聽誰的。

決定將治理層級表格寫入 CLAUDE.md 的 §OpenSpec Integration 段落，包含 Layer 定義、override 規則、歸屬判斷準則 <!-- term:Guidelines -->。這讓治理架構成為自描述的——讀 CLAUDE.md 就能理解整個治理設計。

## 決議

| # | 決策 | 選項 | 採用理由 |
|---|------|------|---------|
| 1 | 治理根 = CLAUDE.md | config.yaml / CLAUDE.md / 雙寫 | 永遠載入 = 所有情境生效 |
| 2 | config.yaml 只留 artifact 格式規則 | 混合 / 分離 | 行為約束在非工作流情境失效 |
| 3 | 不攔截 context/ 新寫入 | 攔截 / 不攔截 | 部分開發者要求不改變工作方式 |
| 4 | 正面範圍取代負面清單 | Out of Scope 列表 / 正面範圍 | 提及即引導 agent 注意 |
| 5 | 循環消解而非一次搬完 | 一次性 / 循環 | **規格稀疏期**（Spec-Sparse Period） <!-- term:SpecSparsePeriod -->不可跳過 |
| 6 | 治理層級寫入 CLAUDE.md | 寫入 / 不寫入 | 治理架構須自描述 |

> [!IMPORTANT]
> **規格稀疏期** <!-- term:SpecSparsePeriod --> (Spec-Sparse Period): 專案初期或規格導入早期，此時規格覆蓋率低，多數行為以程式碼為真相來源的過渡階段。 <!-- anchor:SpecSparsePeriod -->


## Supplementary Knowledge

### 不對稱治理：機器嚴格，人類寬鬆

本次經驗的一個核心洞察是：AI agent 和人類開發者不應該被同一套治理機制管理。

對 AI agent，CLAUDE.md 是硬約束。agent 的行為完全由 context 中的指引決定——它沒有「我知道規則但我選擇不遵守」的能力。任何出現在 CLAUDE.md 中的規則，agent 都會盡力執行。

對人類開發者，CLAUDE.md 是軟參考。開發者可以讀它，也可以不讀。可以遵守，也可以用自己的判斷覆蓋。這不是缺陷，而是人類工作的本質——經驗豐富的開發者有時需要違反通用規則來處理特殊情況。

這個不對稱性在本次治理設計中反覆出現：

- 規則嚴格寫入 CLAUDE.md，但不強制人類開發者讀
- context/ 消解是 agent 的義務（消解循環），但不阻止人類繼續寫入
- 子模組邊界對 agent 是**硬邊界**（Workspace Boundary） <!-- term:WorkspaceBoundary -->，對人類是慣例

> [!IMPORTANT]
> **硬邊界** <!-- term:WorkspaceBoundary --> (Workspace Boundary): 在專案或系統治理中，用於約束 AI Agent 操作權限或限制其可訪問目錄的強制性範圍界限。 <!-- anchor:WorkspaceBoundary -->


接受這個不對稱，而非試圖統一，是本次治理設計最大的妥協——也是最正確的一個。

### 工具-治理反轉

當團隊引入新工具時，特別是有完整 schema/rules 機制的工具，容易將工具的設定中心誤認為專案的治理中心。這種反轉在以下條件下特別容易發生：新工具結構化程度高（看起來「像」治理系統）、團隊對新工具投入了大量設計精力（**沉沒成本**（Sunk Cost） <!-- term:SunkCost -->偏誤）、舊體系確實有問題（急於替換的衝動）。

> [!IMPORTANT]
> **沉沒成本** <!-- term:SunkCost --> (Sunk Cost): 指已經付出且無法收回的成本（如時間、精力或 token 費用）。在決策中，人們常因不願浪費已投入的資源而繼續追加投入，導致非理性决策。 <!-- anchor:SunkCost -->


辨別方式是問：「如果明天移除這個工具，哪些規則會消失？」如果消失的包括架構決策級別的規則，那就是工具-治理反轉。治理根應該是工具移除後仍然存在的設定。

### 規格稀疏期是常態

任何導入結構化工作流的專案都會經歷規格稀疏期 <!-- term:SpecSparsePeriod -->。這不是例外，而是默認狀態。新體系不可能在一夜之間覆蓋所有功能。設計治理架構時必須容納這個階段，而非假設規格已經完整。

本專案的 9/39+ specs 覆蓋率（約 23%）在導入兩週後是合理的。設計消解策略時，接受「tech/ 還有 77% 的內容不可替代」這個事實，比急於清理更重要。

## Key Lessons

1. **治理根 = runtime 可見性 <!-- term:Visibility -->最高的持久設定。** 不是結構化程度最高的，不是功能最豐富的，而是永遠在場的那一個。

2. **歸屬判斷只需一個問題：「寫任何程式碼都要遵守嗎？」** 是 → 永遠載入的設定（Layer 0）。否 → 條件載入的設定（Layer 1）。

3. **治理的對象決定治理的力度。** AI agent 接受硬約束，人類開發者接受軟引導。在同一個專案中，兩者的治理機制可以且應該不同。

4. **工具是租戶，不是房東。** 引入工具時，確保工具的設定不綁架專案的治理。治理根必須獨立於任何單一工具。

5. **妥協不是退讓，是辨認誰的需求更真實。** 「不攔截 context/ 寫入」不是對治理的放棄，而是承認人類開發者的工作慣性是現實約束，治理設計必須容納它。

6. **治理奠基不依賴工具完整度。** CLAUDE.md 可以隨時修改。不需要等 openspec 的規格體系完善，不需要等 context/ 消解完成。先建好治理根，其餘跟著開發節奏走。