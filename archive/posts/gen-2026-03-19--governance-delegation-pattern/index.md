+++
title = "不要複製權威 — 治理文件的預設委託模式"
date = "2026-03-19T23:50:01+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "分析治理文件設計的「預設委託模式」，探討在外部權威來源（如 ESLint 預設）存在時，如何避免低效的知識複製。藉由對比「教科書模型」與「政策聲明模型」，說明該模式如何大幅降低專案維護負擔與 AI Agent 的 Context Token 消耗。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "AI 代理人", # term:AiAgent
    "AI 治理", # term:AIGovernance
    "預設委託模式", # term:DefaultDelegationPattern
    "教科書模型", # term:TextbookModel
    "政策聲明模型", # term:PolicyDeclarationModel
    "架構層", # term:Architecture
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

## 背景

一天的工作從機械性的 `var` → `const`/`let` 轉換開始。289 處宣告，15 個檔案，每一個變數都需要判斷是否被重新賦值。完成後順手修了冒號間距，然後是逗號間距，然後是運算子間距。每修完一類，下一類就浮現出來 — 像打地鼠一樣，格式化問題此起彼落。

這個「打地鼠」現象觸發了一個根本性的問題：我們的格式化規則文件到底覆蓋了多少？於是對照 `@stylistic/eslint-plugin` 的 33 條規則做了一次系統性審計。結果令人不安：11 條有覆蓋，22 條完全缺漏。更不安的是，把 22 條補齊的直覺反應 — 逐條列舉每一條規則 — 會讓 formatting.md 從已經臃腫的 206 行繼續膨脹，而且 ESLint 未來新增的規則仍然會造成漂移。

這篇報告記錄的不是格式化修正本身，而是修正過程中浮現的治理設計問題：當一個公認的權威來源已經存在時，治理文件應該扮演什麼角色？

## 分析

### 逐條列舉的誘惑與代價

最初的 formatting.md 採用逐條列舉模式 — 每一條 ESLint 規則都用 markdown 重新描述一次，附帶正確和錯誤的程式碼範例。這種做法的吸引力顯而易見：文件本身就是完整的參考手冊，讀者不需要查閱外部資源。

但在實踐中，這種完整性是虛假的。ESLint 有 33 條格式化規則，我們只覆蓋了 11 條，遺漏率達 67%。補齊的話，文件會膨脹到約 400 行，而每一行都在做 ESLint 文件已經做過的事。這不是知識創造，而是知識複製。

複製帶來的問題不只是冗餘。在 AI agent 的語境中，每一行規則文件都消耗 context window 的 token 預算。206 行的 formatting.md 約佔 3000 tokens — 這是從實際任務推理空間中借來的。治理文件的 token 消耗有機會成本：你花在重複 ESLint 文件上的 context，就是你無法用於理解業務邏輯的 context。

> [!NOTE]
> **Decision Point**: 全覆蓋 33 條 vs 只補重要的
> — Alternatives: (1) 補齊 22 條缺漏至完整列舉 (2) 只補有實際違規的幾條 (3) 換一種治理模式
> — Outcome: 在考慮 context 成本後，選項 1 和 2 都被否決 — 它們是同一種思維的不同程度，差別只在複製多少

### 「反轉」的發現

轉折點來自一個簡單的觀察：逐條列舉是在回答「我們遵守什麼」，但更有效率的問題是「我們偏離什麼」。

當一個公認的權威來源存在時（如 ESLint 預設），治理文件不需要重述權威的全部內容。它只需要做兩件事：(1) 聲明遵循哪個權威 列出偏離該權威的具體項目。這就是「預設委託 + 偏離列舉」模式。

這個反轉在軟體工程中並不新鮮。Ruby on Rails 的「Convention over Configuration」是同一個原則的框架級應用 — 你不需要配置每一個細節，只需要配置偏離慣例的部分。從設計原則的角度，這也呼應了 Open-Closed Principle 的精神：對擴展開放（ESLint 新增規則自動被繼承），對修改封閉（文件本身不需要更新）。

在 formatting.md 的案例中，這個反轉的效果是戲劇性的：

| 維度 | 逐條列舉 | 預設委託 + 偏離 |
|------|---------|---------------|
| 覆蓋率 | 11/33 (33%) | 33/33 (100%) |
| 文件行數 | 206 行 | 46 行 |
| Context 消耗 | ~3000 tokens | ~700 tokens |
| ESLint 新增規則 | 需手動同步 | 自動繼承 |
| 維護負擔 | 每次 ESLint 更新 | 幾乎為零 |

更少的文字達成了更完整的覆蓋。這不是刪減，而是**架構層**（Architecture） <!-- term:Architecture -->級的改善。

> [!IMPORTANT]
> **架構層** <!-- term:Architecture --> (Architecture): 規格文件中用以客觀記錄系統「實際在做什麼」的事實陳述層。 <!-- anchor:Architecture -->


### Accessor 辯論作為微型案例

member-ordering 規則的 accessor 定位經歷了三次修訂，完美示範了為什麼手動鏡像權威來源是脆弱的。

第一版將 getter/setter 視為 field 的附屬品，與 `#field` 綁定。這看起來直覺 — 讀到 field 就看到 accessor，理解單一屬性很快。但當使用者指出 accessor 可以被子類覆寫時，field 附屬的定位就站不住腳了。於是第二版將 accessor 獨立為一個層級，放在 constructor 後、methods 前。接著查閱了 ESLint 的實際預設，發現 ESLint 確實把 accessor 視為獨立分類而非 method 的子集 — 第三版據此調整。

三次修訂，每一次都是手動推理然後對照 ESLint 修正。如果一開始就聲明「遵循 ESLint 預設」，這三次迭代根本不需要發生。手動鏡像的問題不只是初始成本，還有每一個設計決策都需要獨立推導，而推導過程容易偏離權威 — 即使偏離是無意的。

> [!NOTE]
> **Decision Point**: 引入 ESLint 工具 vs 純 markdown 規則
> — Alternatives: (1) 安裝 ESLint 作為專案工具 (2) 在 markdown 中聲明預設委託，不引入工具
> — Outcome: 選擇 (2)。工具引入有其獨立的考量（build pipeline、npm 依賴、團隊協作），不應與治理文件設計綁定。**預設委託模式**（Default Delegation Pattern） <!-- term:DefaultDelegationPattern -->在有無工具的情況下都成立

> [!IMPORTANT]
> **預設委託模式** <!-- term:DefaultDelegationPattern --> (Default Delegation Pattern): 一種治理文件設計模式。指治理文件不重述已有的權威來源（如 ESLint 預設），而是直接聲明遵循該權威，並僅列出具體的偏離項目，以降低維護成本與 AI Agent 的 Context 消耗。 <!-- anchor:DefaultDelegationPattern -->


### 基線建立作為遷移策略

宣告「遵循 ESLint 預設」很容易，但如果 codebase 本身不合規，這個宣告就只是願景。需要一個遷移策略，將 codebase 從當前狀態推進到合規狀態。

「基線建立 + 繼承」是這個遷移的實施模式：一次性掃描全部 33 條規則，修正所有違規，確認 codebase 合規。之後治理文件的預設委託聲明就有了實質基礎 — 它不再是願景，而是已驗證的現狀描述。

> [!NOTE]
> **Decision Point**: 一次性腳本 vs 可重複 skill
> — Alternatives: (1) 寫成 skill 以便日後重複執行 (2) 一次性腳本，跑完即棄
> — Outcome: 選擇 (2)。基線建立本質上是一次性的。如果未來需要驗證合規性，那時引入 ESLint 工具比維護一個手工的 grep-based skill 更合理

### 權威範圍的邊界

預設委託模式 <!-- term:DefaultDelegationPattern -->有一個必須明確的邊界：ESLint 的權威僅限於格式化規則。

在建立 Authority 段落時，最初的版本沒有足夠的邊界限制。Agent 可能會將「ESLint 優先」泛化到行為規則 — 看到 `==` 就自動改成 `===`（`eqeqeq`），看到未使用的參數就刪除（`no-unused-vars`）。這些都是語意變更，不是格式化。`==` 在 legacy code 中是刻意的型別強制轉換；未使用的參數可能是 API 契約的一部分。

因此最終的 formatting.md 明確劃定了兩個區域：ESLint 格式化預設管轄的領域（spacing、punctuation、layout），以及必須由專案決策的行為規則（附帶具體的排除清單和風險說明）。這個邊界不是多餘的防護 — 它是預設委託模式 <!-- term:DefaultDelegationPattern -->能安全運作的必要條件。

## 省思

### 治理文件的角色定位

這次經驗揭示了治理文件的兩種截然不同的角色模型：

**教科書模型**（Textbook Model） <!-- term:TextbookModel -->：文件本身是完整的知識來源。讀者不需要查閱外部資源就能獲得所有規則。優點是自包含，缺點是需要與權威來源保持同步 — 而同步必然滯後。

> [!IMPORTANT]
> **教科書模型** <!-- term:TextbookModel --> (Textbook Model): 治理文件設計的角色模型之一。文件本身作為完整且獨立的知識來源，讀者無需查閱外部資源，但代價是需要手動與權威來源同步，容易導致內容滯後與冗餘。 <!-- anchor:TextbookModel -->


**政策聲明模型**（Policy Declaration Model） <!-- term:PolicyDeclarationModel -->：文件宣告遵循哪個權威，只記錄偏離項。知識存在於權威來源（ESLint 文件），治理文件只是一個指針加上一組差異。優點是永不過時（權威更新自動繼承），缺點是讀者需要查閱外部資源。

> [!IMPORTANT]
> **政策聲明模型** <!-- term:PolicyDeclarationModel --> (Policy Declaration Model): 治理文件設計的角色模型之一。文件僅宣告遵循外部權威並記錄偏離項目。該模型能讓 AI Agent 直接呼叫其預訓練知識，從而大幅減少 Context Token 的消耗。 <!-- anchor:PolicyDeclarationModel -->


對 AI agent 來說，政策聲明模型 <!-- term:PolicyDeclarationModel -->有一個額外的結構性優勢：agent 已經「知道」ESLint 預設（作為訓練知識的一部分）。一句「follow ESLint defaults」喚起的是 agent 已有的知識，而不是用 3000 tokens 重新傳達它已經知道的東西。這讓政策聲明模型 <!-- term:PolicyDeclarationModel -->在 agent 語境中的效率優勢更加顯著。

### 跨生態的印證

預設委託模式 <!-- term:DefaultDelegationPattern -->並非 JavaScript 生態獨有的發現。在不同的語言和工具鏈中，同樣的模式反覆出現 — 也反覆被忽視。

Python 社群有 PEP 8，一份被廣泛接受的風格指南。然而許多團隊仍然在內部 wiki 中用 50 頁重述 PEP 8 的每條規則，只因為「我們需要自己的 style guide」。更有效的做法是一行聲明：「follow PEP 8, except: max line length = 120」。偏離項清晰，其餘自動繼承。

Go 語言則展示了預設委託的極端形態。`gofmt` 沒有配置選項 — 格式由工具強制定義，不存在「偏離」的可能性。連委託聲明都不需要，因為沒有可以偏離的空間。這說明當權威來源同時也是執行工具時，治理文件本身的必要性可以被完全消除。

Java 生態的 Checkstyle 介於兩者之間。團隊可以選擇重寫整份 Google Java Style Guide 為內部文件，也可以在 `.checkstyle.xml` 中引用 `google_checks.xml` 然後只覆蓋 3 條規則。後者不僅更短，而且當 Google 更新 style guide 時，團隊自動獲得更新 — 前者則永遠滯後。

Kubernetes 的 Helm chart 提供了配置管理領域的類比。`values.yaml` 可以逐一列出每個預設值並加註解，也可以只寫需要 override 的項目，其餘繼承 chart default。後者正是 Helm 設計者預期的使用方式。

這些例子排列起來，勾勒出一個從弱到強的委託光譜：

| 階段 | 形態 | 文件角色 | 範例 |
|------|------|---------|------|
| 0 | 無權威來源 | 文件即權威 | 公司內部的自訂命名慣例 |
| 1 | 有權威，逐條複製 | 教科書 | 團隊 wiki 重述 PEP 8 |
| 2 | 有權威，聲明 + 偏離 | 政策聲明 | formatting.md、Checkstyle config |
| 3 | 有權威 + 執行工具 | 工具配置 | ESLint `.eslintrc`、Helm values |
| 4 | 權威即工具，無偏離空間 | 不需要文件 | `gofmt`、`rustfmt` |

大多數專案停留在階段 1，而階段 2 已經是巨大的改善。能否推進到階段 3 或 4，取決於工具鏈的成熟度和團隊的接受程度。

### 適用邊界

預設委託模式 <!-- term:DefaultDelegationPattern -->有明確的適用條件：必須存在一個公認的、穩定的、被 agent 訓練資料覆蓋的權威來源。ESLint 格式化規則完美符合這三個條件。但如果權威來源不穩定（如某個小眾 linter 的實驗性規則），或不被 agent 認識（如公司內部的自訂標準），那麼逐條列舉可能仍是必要的 — 這就是委託光譜中階段 0 的情境。

同樣，行為規則之所以不能委託給 ESLint，不是因為 ESLint 的建議不好，而是因為行為變更需要對 codebase 語意的深入理解 — 這是超出格式化權威範圍的專案層級決策。

## 結論

當一個公認的權威來源存在時，治理文件的最佳策略不是複製權威的內容，而是聲明對權威的委託，只記錄偏離項。這個原則可以壓縮為一句話：

**不要複製權威，委託權威。**

具體實施時，這意味著：一次性建立基線（驗證 codebase 合規），然後用一份薄文件聲明預設 + 列舉偏離。文件從「教科書」變成「政策聲明」— 更薄、更完整、更不容易過時，且對 AI agent 的 context 消耗最低。