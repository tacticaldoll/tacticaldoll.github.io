+++
title = "提及即引導，沉默即邊界 — AI Agent 注意力與多人協作的資訊架構"
date = "2026-03-18T22:30:03+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "在一次治理重構的規劃中，設計者寫了一段看似無害的文字："
tags = [
    "分析論述", # term:AnalyticalEssay
    "AI 代理人", # term:AiAgent
    "選擇性注意力", # term:SelectiveAttention
    "硬邊界", # term:WorkspaceBoundary
    "認知容量閾值", # term:CognitiveCapacityThreshold
    "行為偶然化", # term:BehavioralAccidentalization
    "預期行為", # term:ExpectedBehavior
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

## 背景

在一次治理重構的規劃中，設計者寫了一段看似無害的文字：

```
## Out of Scope
- module-a/ 的 CLAUDE.md 和 skills
- module-b/ 的 .claude/rules/
- module-c/ 的任何檔案
```

這段文字的意圖是保護——告訴 AI agent「這些不在工作範圍內，不要碰」。但它的實際效果恰好相反：它向 agent 注入了三個具體路徑，每一個都成為 agent 可能去探索的目標。

這個觀察引出了一個更廣泛的問題：在為 AI agent 設計資訊架構時，資訊的存在本身就具有指令效果。負面清單（列出「不要做什麼」）和正面範圍（列出「要做什麼」）不是等價的修辭選擇——它們對 agent 行為的影響在結構上不同。

## 分析

### Context Window 是扁平的

理解這個問題需要先理解 AI agent 處理資訊的方式與人類的根本差異。

人類的注意力是分層的。當一個人讀到「本專案不涉及模組 A、B、C」時，大腦會將 A、B、C 標記為「已知但不相關」，在後續思考中主動抑制它們。這是**選擇性注意力**（Selective Attention） <!-- term:SelectiveAttention -->的正常運作——人類擅長忽略被明確標記為不相關的資訊。

> [!IMPORTANT]
> **選擇性注意力** <!-- term:SelectiveAttention --> (Selective Attention): 在大腦或系統面對大量資訊輸入時，主動聚焦於特定相關訊息並抑制無關干擾的認知聚焦機制。 <!-- anchor:SelectiveAttention -->


AI agent 的 context window 沒有這種分層機制。它是一個扁平的文本序列。當「module-b/.claude/rules/」出現在 context 中時，它與任何其他文本片段具有同等的存在感。agent 在後續推理中可能基於任何理由引用它——確認一致性、滿足完整性、或純粹因為它是一個可操作的路徑。

這不是 agent 的缺陷。這是 transformer 架構的**注意力機制**（Attention Mechanism） <!-- term:AttentionMechanism -->的自然特性。context window 中的每個 token 都參與注意力計算，沒有「被標記為不相關因此跳過」的機制。所謂的「忽略」只能靠其他更強的訊號壓過，而非靠標記實現。

> [!IMPORTANT]
> **注意力機制** <!-- term:AttentionMechanism --> (Attention Mechanism): Transformer 架構中用於計算輸入序列不同位置之間關聯權重的核心機制。 <!-- anchor:AttentionMechanism -->


### 提及即注入

這個特性意味著：**在 agent 的 context 中出現一個實體名稱，等價於告訴 agent 這個實體存在且可能與當前任務相關。**

考慮這兩段指引的差異：

**指引 A**（負面清單）：
```
修改範圍：CLAUDE.md、openspec/config.yaml。
不修改：module-a/、module-b/、module-c/、module-d/。
```

**指引 B**（正面範圍）：
```
修改範圍：CLAUDE.md、openspec/config.yaml。
```

指引 A 注入了 6 個路徑，其中 4 個是「不要碰」的。指引 B 注入了 2 個路徑，全部是「要碰的」。

從 agent 的行為預測來看：讀到指引 A 的 agent 知道 `module-b/.claude/rules/` 的存在。在修改 CLAUDE.md 的 Engineering Disciplines 段落時，它可能會推理：「module-b 有 .claude/rules/，我應該確認新的 CLAUDE.md 內容與它不衝突。」——然後去讀那個檔案。讀了之後，它可能發現差異，嘗試「修正一致性」，最終越界。

讀到指引 B 的 agent 不知道 `module-b/.claude/rules/` 存在。它只知道要修改 CLAUDE.md 和 config.yaml。它不會去尋找不知道存在的東西。

這個差異不是機率性的（「可能會」vs「可能不會」），而是結構性的：指引 A 在 agent 的可操作空間中增加了 4 個實體，指引 B 沒有。可操作空間越大，非**預期行為**（Expected Behavior） <!-- term:ExpectedBehavior -->的可能性越高。

> [!IMPORTANT]
> **預期行為** <!-- term:ExpectedBehavior --> (Expected Behavior): 系統或模組在特定輸入或情境下被要求達到的正確輸出與副作用狀態 <!-- anchor:ExpectedBehavior -->


### 認知科學的平行：框架效應

語言學家 George Lakoff 提出過一個著名的例子：「Don't think of an elephant」（別想大象）。這句話的效果恰好相反——它讓你立刻想到大象。否定指令（「不要想 X」）必然先激活 X 的表徵，然後試圖抑制它。抑制有時成功，有時失敗。

AI agent 的情況比人類更極端。人類至少有抑制機制（雖然不完美）。agent 的 context window 沒有抑制——一旦 X 進入 context，它就以全強度參與後續的注意力計算，直到 session 結束。

這意味著：在為 AI agent 寫指引時，**「不要做 X」比不說 X 更危險。** 不說 X，agent 不知道 X 存在。說「不要做 X」，agent 知道 X 存在，知道 X 的具體路徑，知道有人認為 X 與當前任務有關（否則為什麼要提到它？）——唯一的約束是一個否定詞。

### 推廣：四類隱式指令

這個原理不限於路徑名稱。context 中出現的各種資訊都有隱式的指令效果：

**被否決的方案**。設計文件中寫「我們考慮了方案 A 但因為 X 原因否決」。agent 讀到後，方案 A 的完整描述進入 context。在後續推理中，如果 agent 遇到 X 不成立的特殊情況，它可能復活方案 A。這有時是好事（靈活性），有時是壞事（方案 A 被否決的原因比 X 更深，但只有 X 被記錄了）。

**錯誤示例**。文件中寫「不要寫成 `if err != nil { return nil }`，應該寫成 `if err != nil { return fmt.Errorf(...) }`」。agent 同時看到了正確和錯誤的模式。在程式碼生成時，兩個模式都在注意力範圍內。如果正確模式的描述不夠強，錯誤模式可能在生成中「洩漏」。

**條件性例外**。文件中寫「安全規則 X 在測試環境可以放寬」。agent 知道了放寬的可能性。在非測試環境中，如果 agent 遇到 X 的限制，它可能推理「也許這裡也可以放寬」——因為放寬的先例已在 context 中。

**過時的狀態描述**。文件中寫「目前模組 A 使用舊版 API，計畫遷移到新版」。如果遷移已完成但文件未更新，agent 可能仍然認為舊版 API 在使用中，在推理中引入不存在的約束。

### 多人協作的額外維度

在單一作者的專案中，以上問題可以通過謹慎寫作來緩解——一個人控制 context 中出現的所有資訊。但在多人協作中，每位開發者都在向 agent 的 context 貢獻資訊（透過 CLAUDE.md、config files、程式碼註釋、commit messages 等），且彼此不一定知道對方寫了什麼。

這創造了一個資訊架構問題：**多位作者獨立寫入的資訊，在 agent 的 context window 中組合時，可能產生任何單一作者都未預期的隱式指令。**

例如，開發者 A 在 CLAUDE.md 中寫了 **硬邊界**（Workspace Boundary） <!-- term:WorkspaceBoundary -->。開發者 B 在 config.yaml 的 context 段中寫了完整的子模組列表（出於描述完整性）。agent 同時讀到兩者。CLAUDE.md 說「只碰這些」，config.yaml 說「這些子模組存在」。後者的存在削弱了前者的邊界效果。

> [!IMPORTANT]
> **硬邊界** <!-- term:WorkspaceBoundary --> (Workspace Boundary): 在專案或系統治理中，用於約束 AI Agent 操作權限或限制其可訪問目錄的強制性範圍界限。 <!-- anchor:WorkspaceBoundary -->


這不是任何人的錯誤——A 和 B 各自的寫作都合理。問題在於 context window 是全局的，而作者的視角是局部的。

### Session 作為硬邊界

上述所有問題都受限於一個 session 的 context window。不同 session 之間，context 是乾淨的——新 session 只載入持久化的指引文件，不載入前一個 session 的對話歷史。

這個特性讓 session 邊界成為注意力管理的最強工具。一個探索性 session 中積累的所有被否決方案、中間推理、修正歷程，在新 session 中完全消失。新 session 的 agent 只讀到最終的 artifacts——乾淨的 proposal、design、tasks，沒有被否決的草案。

由此衍生出一個實踐原則：**探索與實作應分屬不同 session。** 探索 session 的產出是持久化的 artifacts（寫入文件）。實作 session 只讀 artifacts，不繼承探索過程。這不是工程美學，而是 context window 特性的直接推論——agent 沒有選擇性遺忘的能力，唯一的「遺忘」機制是新開一個 session。

## 省思

### 正面範圍的邊界條件

正面範圍設計不是萬能的。有些情境必須使用負面表述：

安全規則是最明顯的例外。「不得將密碼以明文儲存」必須直接寫出。安全規則被注意到的收益（防止漏洞）遠大於被注意到的成本（agent 可能過度關注安全問題）。在安全領域，過度警覺好過不警覺。

建置指令也是例外。`make module-a` 必須出現在建置文件中，即使你不希望 agent 去讀 module-a/ 的原始碼。操作手冊的完整性優先於注意力最小化。

這些例外的共通點是：**被注意到的收益 > 被注意到的成本。** 正面範圍設計的適用條件是反過來的情況——被注意到的成本 > 被注意到的收益，即那些「agent 知道了反而會出事」的資訊。

### 資訊密度與注意力稀釋

即使全部使用正面範圍，context 中的資訊密度也會影響 agent 的表現。一份 300 行的 CLAUDE.md 中，每條規則獲得的注意力權重低於一份 30 行的 CLAUDE.md 中的同一條規則。

這暗示了一個設計張力：CLAUDE.md 作為治理根需要涵蓋足夠多的規則（完整性），但每增加一條規則都稀釋了其他規則的注意力權重（有效性）。

沒有完美的解法。實踐上的緩解措施包括：將規則按重要性排序（高優先在前）、使用格式化（表格、粗體）來增加關鍵規則的視覺權重、定期審計規則的必要性（移除過時的規則以減少密度）。

### 這不只是 AI 的問題

雖然本文以 AI agent 為分析對象，但「提及即引導」的原理在人類協作中也成立，只是程度較弱。

一份 code review checklist 如果列出「不要做的 10 件事」，reviewer 的注意力會被這 10 件事占據，可能忽略 checklist 沒提到的第 11 件事。一份 onboarding 文件如果列出「已廢棄的系統」，新人會好奇那些系統是什麼、為什麼被廢棄，投入不必要的時間。

差異在於人類有更強的抑制能力——大部分人讀到「已廢棄」後能有效忽略。但在注意力有限的情境（趕工期、認知負荷高）下，人類也會被負面清單引導到錯誤的方向。

## 結論

為 AI agent 設計資訊架構時，三個原則值得內化：

1. **Context 中的資訊是隱式指令。** 出現 = 存在 = 可操作 = 可能被操作。設計者對 context 內容的控制，就是對 agent 行為的控制。

2. **正面範圍優於負面清單。** 定義「agent 做什麼」，不定義「agent 不做什麼」。不被提及的事物，對 agent 不存在。這是比任何否定指令都更可靠的邊界。

3. **Session 是最強的注意力邊界。** agent 沒有選擇性遺忘能力。被否決的方案、中間推理、錯誤嘗試——這些在同一 session 中永遠存在。唯一的清除方式是新 session。探索與實作分離到不同 session，不是偏好，是 context window 特性的直接推論。