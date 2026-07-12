+++
title = "隱性污染源（二）：從命名感應到對話殘響的全景剖析"
date = "2026-03-10T13:40:02+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "在解決了「Git Log 污染」的具體技術問題後，我們意識到 AI 的「憑空重構」行為並非單一來源的偶發產物，而是多種隱性污染源相互共振的結果。本報告旨在剖析那些除了 Git 歷史之外，同樣能誘導 AI 偏離事實、觸發重構幻覺的深度污染路徑。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "AI 代理人", # term:AiAgent
    "AI 治理", # term:AIGovernance
    "歷史噪音", # term:HistoryNoise
    "對話殘響", # term:ConversationEcho
    "潛在污染地圖", # term:PotentialPollutionMap
    "上下文視窗", # term:ContextWindow
    "路徑即指令", # term:NamingInducedResonance
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

## 導言

在解決了「**版本控制歷史**（Git Log） <!-- term:GitLog --> 污染」的具體技術問題後，我們意識到 AI 的「**憑空重構**（Phantom Reconstruction） <!-- term:PhantomReconstruction -->」行為並非單一來源的偶發產物，而是多種隱性污染源相互共振的結果。深入剖析那些除了 Git 歷史之外，同樣能誘導 AI 偏離事實、觸發重構**幻覺**（Hallucination） <!-- term:Hallucination -->的深度污染路徑。

> [!IMPORTANT]
> **版本控制歷史** <!-- term:GitLog --> (Git Log): Git 等版本控制系統所記錄的完整提交與異動軌跡。 <!-- anchor:GitLog -->
> **憑空重構** <!-- term:PhantomReconstruction --> (Phantom Reconstruction): AI Agent 在缺乏當前對話素材及明確指令的情況下，自主生成格式錯誤、內容受污染檔案之異常行為。 <!-- anchor:PhantomReconstruction -->
> **幻覺** <!-- term:Hallucination --> (Hallucination): 大型語言模型在面對不實或矛盾資訊時，生成不符合客觀現實或超出脈絡之回應的錯誤現象。 <!-- anchor:Hallucination -->


## 分析

### 1. 命名感應：路徑即指令
檔案與目錄的命名本身就是強大的語意錨點。
- 路徑作為意圖訊號：當 AI 讀取到特定的目錄結構時，名稱本身會提供強烈的指令色彩。
- **殭屍指令**（Zombie Instructions） <!-- term:ZombieInstructions -->：即使目錄內檔案已被清空，目錄的名稱仍會像「殭屍」一樣對 AI 下達隱性指令，促使其根據目錄名稱的字面意思來填充內容。

> [!IMPORTANT]
> **殭屍指令** <!-- term:ZombieInstructions --> (Zombie Instructions): 已清空內容的目錄或檔案因名稱殘留，仍持續對 AI Agent 產生引導效應的隱性指令。 <!-- anchor:ZombieInstructions -->


### 2. 歷史噪音 的放大效應
「**歷史噪音**（History Noise） <!-- term:HistoryNoise -->」是指那些已在邏輯上被廢棄，但在物理紀錄中依然存在的資訊碎片。
- 語意共振：當當前語境缺乏足夠資訊時，AI 會與物理殘骸產生「語意共振」，誤以為噪音就是失落的指令。
- **虛假確定性**：噪音中包含的具體路徑與格式，會賦予 AI 一種「虛假的確定性」，誘導其產出結構完整但事實錯誤的內容。

> [!IMPORTANT]
> **歷史噪音** <!-- term:HistoryNoise --> (History Noise): 已在邏輯上廢棄但物理上仍殘留在版本控制歷史中的資訊碎片。 <!-- anchor:HistoryNoise -->


### 3. 潛在污染地圖
- **知識遺骸**（Knowledge Debris） <!-- term:KnowledgeDebris -->：儲存在教訓資料庫中的過時術語或規則。AI 傾向於優先信任這些「已**結晶**（Crystallize） <!-- term:Crystallize -->」的資產。
- **範例陷阱**（Template Trap） <!-- term:TemplateTrap -->：工作流 檔案中包含的舊版格式「示範代碼」。
- **對話殘響**（Conversation Echo） <!-- term:ConversationEcho -->：最難防禦來源。即使檔案重設，**當前對話歷史** 仍保留了先前失敗紀錄，導致 AI 出於「自我修正」本能再次嘗試無意義的重構。

> [!IMPORTANT]
> **知識遺骸** <!-- term:KnowledgeDebris --> (Knowledge Debris): 歷史對話或教訓資料庫中殘留的過時術語、規則或已失效資訊。 <!-- anchor:KnowledgeDebris -->
> **結晶** <!-- term:Crystallize --> (Crystallize): 將蒸餾後的關鍵知識沉澱並結構化為正式報告或規格的過程。 <!-- anchor:Crystallize -->
> **範例陷阱** <!-- term:TemplateTrap --> (Template Trap): 工作流或指引檔案中供示範用的範例程式碼被 AI 誤當作當前實作指令的現象。 <!-- anchor:TemplateTrap -->
> **對話殘響** <!-- term:ConversationEcho --> (Conversation Echo): 檔案已重設但當前對話歷史（上下文視窗）中仍殘留先前對話資訊，持續干擾 AI 的現象。 <!-- anchor:ConversationEcho -->


## 反思

隱性污染的本質是 AI 對「環境一致性」的極度渴求。當真實素材缺失時，任何環境殘骸（命名、歷史、舊範例）都會被 AI 視為補完語意的救生圈。

## 結論

治理 AI 的「憑空重構 <!-- term:PhantomReconstruction -->」不能僅處理點狀的污染，必須建立一套完整的「環境免疫機制」：
- **物理性肅清**：徹底銷毀污染路徑與紀錄。
- 語意脫鉤：在重設任務時，必須明確清空對話聯想，防止「對話殘響 <!-- term:ConversationEcho -->」的干擾。