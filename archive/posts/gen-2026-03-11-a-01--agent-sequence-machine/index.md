+++
title = "接龍狀態機的因果斷裂：Agent 推理的本質限制"
date = "2026-03-11T22:30:01+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "軟體工程中，我們習慣將 AI agent 視為「會推理但有時推錯」的開發者。這個心智模型決定了我們如何設計代碼、如何組織知識、如何建立治理機制。但如果這個心智模型從根本上就是錯的呢？"
tags = [
    "分析論述", # term:AnalyticalEssay
    "AI 代理人", # term:AiAgent
    "條件機率序列生成器", # term:ConditionalProbabilitySequenceGenerator
    "接龍狀態機", # term:SequenceCompletionMachine
    "大型語言模型", # term:LargeLanguageModel
    "跨模組因果", # term:CrossModuleCausality
    "因果連續性", # term:CausalContinuity
  ]
series = ["接龍狀態機的因果斷裂：Agent 推理的本質限制"]
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

軟體工程中，我們習慣將 AI agent 視為「會推理但有時推錯」的開發者。這個心智模型決定了我們如何設計代碼、如何組織知識、如何建立治理機制。但如果這個心智模型從根本上就是錯的呢？

本文從 agent 的運算本質出發，論證一個基礎命題：agent 不是推理機器，而是**接龍狀態機**（Sequence Completion Machine） <!-- term:SequenceCompletionMachine -->。這個本質差異導致了一個被廣泛忽視的風險——**因果斷裂**（Causal Breakpoint） <!-- term:CausalBreakpoint -->。理解這個風險是後續討論代碼設計約束和治理防線的前提。

> [!IMPORTANT]
> **接龍狀態機** <!-- term:SequenceCompletionMachine --> (Sequence Completion Machine): 基於條件機率生成下一個 Token 的狀態機本質，其輸出取決於前文 Token 的統計分佈而非邏輯推理 <!-- anchor:SequenceCompletionMachine -->
> **因果斷裂** <!-- term:CausalBreakpoint --> (Causal Breakpoint): AI Agent 運算中由於上下文視窗或靜態程式碼中關鍵因果資訊缺失，導致無法正確推演系統狀態的現象 <!-- anchor:CausalBreakpoint -->


## 分析：接龍狀態機的本質

### 「存在 = token 中可見」命題

**大型語言模型**（Large Language Model） <!-- term:LargeLanguageModel -->是**條件機率序列生成器**（Conditional Probability Sequence Generator） <!-- term:ConditionalProbabilitySequenceGenerator -->——下一個 token 的選擇基於前文 token 的統計分佈。看起來像推理的輸出，本質上是「訓練語料中類似上下文之後通常接什麼」。

> [!IMPORTANT]
> **大型語言模型** <!-- term:LargeLanguageModel --> (Large Language Model): 基於海量文本數據訓練的深層神經網路模型，用於處理、生成和理解自然語言 <!-- anchor:LargeLanguageModel -->
> **條件機率序列生成器** <!-- term:ConditionalProbabilitySequenceGenerator --> (Conditional Probability Sequence Generator): 根據前文已生成的 Token 序列，計算並生成下一個機率最高 Token 的數學運算模型 <!-- anchor:ConditionalProbabilitySequenceGenerator -->


這個本質帶來三個後果，每一個都與人類開發者形成對比：

| 人類開發者 | Agent |
|---|---|
| 從規則推導出未見過的結論 | 從見過的模式中**匹配**最接近的輸出 |
| 能處理語料中從未出現的新組合 | 新組合只能靠已見模式的**插值**，品質取決於組成片段的相似度 |
| 遇到矛盾會停下來質疑 | 遇到矛盾選上下文中統計權重更高的那個，不會意識到矛盾存在 |

由此可以推導出一個基礎命題：**對接龍狀態機 <!-- term:SequenceCompletionMachine -->而言，存在 = 在前文中有對應 token**。不在 context window 裡的資訊，對 agent 而言等於不存在。不是「看到了但理解錯」，而是**根本不在輸入中**。

這個命題解釋了一個常見的困惑：為什麼 agent 有時能寫出複雜的代碼，卻在看似簡單的判斷上犯錯？答案是：它的「能力」取決於 context window 中 token 的品質和完整性，而非某種內在的「理解力」。Token 完整時表現優異，token 缺失時盲目行動——而且無法區分這兩種狀態。

### 二次摘要機制：封裝為何對 agent 格外危險

人類封裝代碼時，會刪除「有經驗的人能推導出來的」上下文，保留結構、命名和介面。這是第一次摘要——**人工摘要**（Human Summary） <!-- term:HumanSummary -->。

> [!IMPORTANT]
> **人工摘要** <!-- term:HumanSummary --> (Human Summary): 人類工程師在封裝程式碼時，主動隱去具體實作細節，僅保留命名、介面與結構的抽象過程 <!-- anchor:HumanSummary -->


Agent 讀取代碼時，將文本轉為 context window 中的 token 序列。這是第二次摘要——**機器摘要**（Machine Summary） <!-- term:MachineSummary -->。兩次摘要各自有不同的丟棄標準：

> [!IMPORTANT]
> **機器摘要** <!-- term:MachineSummary --> (Machine Summary): AI Agent 將程式碼文本載入 Context Window 時，丟棄非字面 Token 而僅保留前文特徵的過程 <!-- anchor:MachineSummary -->


| 摘要階段 | 丟棄標準 | 保留的內容 | 假設的讀者 |
|---|---|---|---|
| 人類封裝（第一次） | 「有經驗的人能推導出來的」 | 結構、命名、介面 | 有領域直覺的人類 |
| Agent 讀取（第二次） | 「token 序列中未出現的」 | 前文中的字面 token | 只有 token 序列的狀態機 |

關鍵在於：兩次損失不是相加，而是**相乘**。人類封裝精準地丟棄了「可推導的上下文」——但 agent 無法推導。第一次摘要刪掉的，恰好是第二次摘要的救命資訊。換句話說：**人類認為「冗餘的」那部分，恰好是 agent 最需要的**。

用一個對比來說明這種疊加效應：

```javascript
// 封裝前（人類覺得囉唆，但 agent 能完整推斷因果）
function processOrder(order) {
    // 只有 pending 且未出貨的訂單可取消——
    // shipped 訂單走退貨流程（見 returnOrder），不走這裡
    if (order.status === "pending" && !order.shipped) {
        cancelOrder(order);
    }
}

// 封裝後（人類覺得整潔，但 agent 看不到 why-not）
function processOrder(order) {
    if (order.isCancellable()) {
        cancelOrder(order);
    }
}
```

封裝後的版本對人類更整潔——`isCancellable()` 自解釋。但 agent 看不到「shipped 走退貨流程」這個**排除邏輯**（Why-Not Comment） <!-- term:WhyNotComment -->。如果 agent 需要修改取消條件，它無法判斷改動是否會與退貨流程衝突，因為那段因果鏈已經在第一次摘要中被刪除。

> [!IMPORTANT]
> **排除邏輯** <!-- term:WhyNotComment --> (Why-Not Comment): 在程式碼中記錄「為何不採用某種方案」的說明，用以補全 Agent 無法從程式碼推導的因果鏈 <!-- anchor:WhyNotComment -->


這就是「高度封裝的整潔代碼本身就是人工摘要 <!-- term:HumanSummary -->，導入 agent 會變成二次摘要」的具體含義。對 agent 而言最理想的代碼，是人類覺得「囉唆」的代碼——局部上下文完整、意圖顯式、有適度重複。這種代碼經過 agent 的 context window 摘要後，仍然保留足夠的決策依據。而高度封裝的整潔代碼經過二次摘要後，剩下的只有骨架，沒有血肉。

### 因果斷裂光譜

基於「存在 = token 中可見」的命題，因果斷裂 <!-- term:CausalBreakpoint -->可以分為三種類型。每種類型在 agent 的 token 序列中呈現不同的缺陷模式，危害程度遞增：

| 類型 | 機制 | 範例 | 危害 |
|---|---|---|---|
| **刪除** | 原本存在的上下文被封裝刪除 | DRY 消除重複後，局部上下文消失；抽象層把實作細節藏到跳轉鏈深處 | 留有線索（函數名、介面簽名），agent 可嘗試跳轉追蹤 |
| **從未存在** | 關鍵資訊從未以 token 形式出現在代碼文本中 | 非同步操作的中間狀態變更；runtime 事件綁定的訂閱者清單 | 完全無線索，agent 不知道自己遺漏了什麼 |
| **錯誤存在** | Token 序列中存在資訊，但內容與事實不符 | 過時的集中知識庫描述；被污染後回寫的 spec 條目 | 最危險——agent 把錯誤當事實，且無法自檢 |

「刪除」型是封裝和 DRY 的產物。「從未存在」型是 runtime 綁定和非同步的產物。「錯誤存在」型是知識庫維護失敗的產物。三者在後續的風險分析和回應方案中各自需要不同的處理策略。

## 反思：因果連續性作為獨立約束

### 因果連續性 vs 語意邊界

**因果連續性**（Causal Continuity） <!-- term:CausalContinuity -->與**語意邊界**（Semantic Boundary） <!-- term:SemanticBoundary -->是兩個常被混淆的概念。區分它們對於理解 agent 風險至關重要。

> [!IMPORTANT]
> **因果連續性** <!-- term:CausalContinuity --> (Causal Continuity): 系統中某項決策或邏輯的完整依據在 Token 序列中完全可見且未被中斷的狀態 <!-- anchor:CausalContinuity -->
> **語意邊界** <!-- term:SemanticBoundary --> (Semantic Boundary): 模組或類別在空間維度上定義其職責與封裝邊界的概念 <!-- anchor:SemanticBoundary -->


語意邊界 <!-- term:SemanticBoundary -->回答的是空間問題：「這個概念的責任到哪裡結束」。因果連續性 <!-- term:CausalContinuity -->回答的是時序問題：「這個決策的依據是否在 token 序列中可見」。兩者的交叉產生四種狀態：

| | 因果連續 | 因果斷裂 <!-- term:CausalBreakpoint --> |
|---|---|---|
| **語意邊界 <!-- term:SemanticBoundary -->清楚** | Agent 能正確操作 | Agent 知道在哪改，但改錯 |
| **語意邊界 <!-- term:SemanticBoundary -->模糊** | Agent 改對了，但改到不該改的地方 | 全面失控 |

語意邊界 <!-- term:SemanticBoundary -->是 DDD、模組化、封裝本來就在做的事。因果連續性 <!-- term:CausalContinuity -->是 agent 時代**額外需要的約束**——它要求關鍵資訊不僅存在於正確的模組中，還要以 token 形式出現在 agent 可讀取的範圍內。

### 因果鏈的承載形式

釐清因果連續性 <!-- term:CausalContinuity -->後，一個自然的問題是：agent 是否「不能走無註解風格」？答案需要精確化——agent 需要的不是「註解」，而是**因果鏈在 token 序列中連續**。

註解只是補因果鏈的其中一種手段。不同的手段承載不同維度的因果：

| 手段 | 承載的因果維度 |
|---|---|
| 註解 | 自然語言 token 補 why / why-not |
| 型別標注 | 結構化 token **型別標註**（Type Annotation） <!-- term:TypeAnnotation --> |
| 好命名 | 壓縮的因果 token（what，部分 why） |
| 意圖測試 | 可執行的因果 token（expected behavior） |

> [!IMPORTANT]
> **型別標註** <!-- term:TypeAnnotation --> (Type Annotation): 在程式碼中顯式宣告變數或函式參數之資料結構形狀，以降低靜態追蹤與跳轉成本 <!-- anchor:TypeAnnotation -->


無註解風格的假設是「命名足以承載因果」。對人類通常成立，因為人類會用直覺填補命名覆蓋不到的部分。對 agent，命名只能承載 **what**，承載不了 **why-not** 和**跨模組因果**（Cross-Module Causality） <!-- term:CrossModuleCausality -->。

> [!IMPORTANT]
> **跨模組因果** <!-- term:CrossModuleCausality --> (Cross-Module Causality): 一個模組的實作細節受限於另一個模組的隱含規則，且在靜態程式碼中不直接呈現的因果依賴 <!-- anchor:CrossModuleCausality -->


所以結論不是「一定要寫註解」，而是：**任何一種手段都行，只要因果鏈在 agent 可見的 token 中不斷裂。**

### 統一根因

回到開頭的命題，可以將前面所有討論統一到一張表中。每一類 agent 風險，都可以還原為同一個根因——關鍵資訊不在 token 序列中：

| 風險 | 根因還原 |
|---|---|
| DRY 刪掉局部上下文 | 刪掉的 token 不在前文中 → 不存在 |
| 知識庫過時 | 錯誤的 token 在前文中 → 被當作事實 |
| Runtime 綁定 | 綁定關係未出現在靜態文本中 → 不存在 |
| 非同步死區 | 中間狀態變更未寫在代碼中 → 不存在 |
| 設計模式間接層 | 跳轉目標超出 context window → 不存在 |

## 結論

Agent 不是「有時推錯的推理者」，而是「只能基於可見 token 做統計匹配的序列生成器」。這個本質差異衍生出因果連續性 <!-- term:CausalContinuity -->這個獨立於語意邊界 <!-- term:SemanticBoundary -->的新約束維度。在 agent 的 token 序列中，因果斷裂 <!-- term:CausalBreakpoint -->有三種形態（刪除、從未存在、錯誤存在），每種需要不同的預防策略。

核心原則是：**對接龍狀態機 <!-- term:SequenceCompletionMachine -->而言，不在 token 序列中的東西等於不存在。** 所有 agent 風險的根源都是這一個。