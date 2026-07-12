+++
title = "隱性污染源（一）：Git Log 誘導下的 AI 認知偏誤實錄"
date = "2026-03-10T13:40:01+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "在專案開發過程中，發現 AI Agent 出現了「憑空重構」的異常行為：在缺乏當前對話素材及明確指令的情況下，自主在臨時工作區生成了大量格式錯誤、內容受污染的治理報告。這種行為不僅違反了「AI 禁止自主寫入」的約束，更顯示出某種底層的認知偏誤。"
tags = [
    "技術筆記", # term:TechnicalNote
    "AI 代理人", # term:AiAgent
    "AI 治理", # term:AIGovernance
    "憑空重構", # term:PhantomReconstruction
    "物理級肅清", # term:PhysicalEnforcement
    "受污染的歷史片段", # term:PollutedHistorySnapshots
    "歷史紀錄分析", # term:GitLogAnalysis
    "全局重設操作", # term:GlobalResetOperation
  ]
series = ["隱性污染三部曲：從歷史殘骸到治理範式"]
[ai_info]
    [ai_info.generation]
        model = "Gemini 3 Flash"
        agent = "Antigravity IDE 1.19.6.0"
    [ai_info.refinement]
        model = "Gemini 3.5 Flash"
        agent = "Antigravity IDE 2.0.4"
+++

<!--more-->

## 問題

在專案開發過程中，發現 **代理人**（AI Agent） <!-- term:AiAgent --> 出現了**「**憑空重構**（Phantom Reconstruction） <!-- term:PhantomReconstruction -->」**的異常行為：在缺乏當前對話素材及明確指令的情況下，自主在**臨時工作區**（Ephemeral Scratchpad） <!-- term:EphemeralScratchpad --> 生成了大量格式錯誤、內容受污染的治理報告。這種行為不僅違反了「AI 禁止自主寫入」的約束，更顯示出某種底層的認知偏誤。

> [!IMPORTANT]
> **AI 代理人** <!-- term:AiAgent --> (AI Agent): 具備自主理解、推論與程式碼生成能力，能在給定規則下執行特定任務的 AI 協作者。 <!-- anchor:AiAgent -->
> **憑空重構** <!-- term:PhantomReconstruction --> (Phantom Reconstruction): AI Agent 在缺乏當前對話素材及明確指令的情況下，自主生成格式錯誤、內容受污染檔案之異常行為。 <!-- anchor:PhantomReconstruction -->
> **臨時工作區** <!-- term:EphemeralScratchpad --> (Ephemeral Scratchpad): AI Agent 執行任務時所使用的臨時工作目錄。 <!-- anchor:EphemeralScratchpad -->


## 調查

為了找出這些「**幻覺**（Hallucination） <!-- term:Hallucination -->指令」的來源，我們執行了深度的技術追蹤：

> [!IMPORTANT]
> **幻覺** <!-- term:Hallucination --> (Hallucination): 大型語言模型在面對不實或矛盾資訊時，生成不符合客觀現實或超出脈絡之回應的錯誤現象。 <!-- anchor:Hallucination -->


1. Git **狀態掃描**（Git Status） <!-- term:GitStatus -->：
    - 發現底層版本控制系統顯示部分被刪除的檔案仍處於「**未追蹤**（Untracked） <!-- term:Untracked -->」或「**已暫存**（Staged） <!-- term:Staged -->」的模糊狀態。
2. **歷史紀錄分析**（Git Log Analysis） <!-- term:GitLogAnalysis -->：
    - 發現**受污染的歷史片段**（Polluted History Snapshots） <!-- term:PollutedHistorySnapshots --> 包含了這些受污染的內容。
    - 發現**全局重設操作**（Global Reset Operation） <!-- term:GlobalResetOperation --> 雖已執行，但其後的碎片化提交留下了語意殘骸。

> [!IMPORTANT]
> **狀態掃描** <!-- term:GitStatus --> (Git Status): 讀取版本控制系統以確認當前檔案的追蹤與修改狀態。 <!-- anchor:GitStatus -->
> **未追蹤** <!-- term:Untracked --> (Untracked): 版本控制系統中尚未被納入追蹤管理的新檔案狀態。 <!-- anchor:Untracked -->
> **已暫存** <!-- term:Staged --> (Staged): 版本控制系統中已被標記為準備提交的修改檔案狀態。 <!-- anchor:Staged -->
> **歷史紀錄分析** <!-- term:GitLogAnalysis --> (Git Log Analysis): 對版本控制系統的歷史提交紀錄進行掃描與上下文關聯性解析。 <!-- anchor:GitLogAnalysis -->
> **受污染的歷史片段** <!-- term:PollutedHistorySnapshots --> (Polluted History Snapshots): 版本控制歷史中包含無效、錯誤或過時程式碼結構的提交紀錄。 <!-- anchor:PollutedHistorySnapshots -->
> **全局重設操作** <!-- term:GlobalResetOperation --> (Global Reset Operation): 強制將工作區與歷史紀錄重設至特定乾淨狀態的清除程序。 <!-- anchor:GlobalResetOperation -->


### 核心發現：非直覺污染源

調查結果顯示，污染源並非來自檔案系統，而是來自 **版本控制歷史**（Git Log） <!-- term:GitLog -->。當 代理人 <!-- term:AiAgent --> 啟動或執行「重構」任務時，其底層邏輯會掃描最近的歷史紀錄以獲取上下文。在重設操作之後所留下的歷史路徑，被 AI 誤解為「遺失的開發意圖」，進而觸發其「自動修補」本能。

> [!IMPORTANT]
> **版本控制歷史** <!-- term:GitLog --> (Git Log): Git 等版本控制系統所記錄的完整提交與異動軌跡。 <!-- anchor:GitLog -->


## 發現

### 1. 指令幻覺形成機制
代理人 <!-- term:AiAgent --> 在啟動時為了「建立一致性」，會將歷史紀錄中的提交視為有效的上下文一部分。當歷史中存在受污染的片段時，即使當前檔案已被刪除，AI 仍會嘗試根據這些片段進行「**內容重建**（Reconstruction） <!-- term:Reconstruction -->」。這是一種**「路徑依賴型認知偏誤」**。

> [!IMPORTANT]
> **內容重建** <!-- term:Reconstruction --> (Reconstruction): AI 嘗試根據不完整歷史或上下文片段，自主修補與重新生成檔案的過程。 <!-- anchor:Reconstruction -->


### 2. 解決方案：物理級肅清
簡單的檔案刪除僅能清理檔案系統，無法清理 AI 的「歷史視野」。有效的解決方案必須包含：
- **邏輯重設**：執行歷史抹除操作以消除碎片化紀錄。
- **物理肅清**：透過強制同步機制將污染紀錄從雲端與本地歷史中徹底移除。

## 關鍵教訓

- **歷史即指令**：對 AI 而言，版本控制歷史 <!-- term:GitLog -->不僅是紀錄，更是強大的指令源。
- **重設不等於消失**：未經過合併的混亂歷史是 AI 認知污染的溫床。
- **物理約束優於注意力**：防止 AI 幻覺 <!-- term:Hallucination -->最有效的方法是「物理性地讓污染素材從其視野中消失」。