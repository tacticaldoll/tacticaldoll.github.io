+++
title = "在規格稀疏期中存活：觀察性 Schema 與債務清創指南"
date = "2026-03-14T16:50:02+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "提出在缺乏完整規範的階段，利用帶有標記的觀察性綱要 (Descriptive Schema) 收集現狀，並轉化技術債務的方法論。"
tags = [
    "技術筆記", # term:TechnicalNote
    "AI 代理人", # term:AiAgent
    "規格稀疏期", # term:SpecSparsePeriod
    "技術債", # term:TechnicalDebt
    "規格驅動開發", # term:SpecDrivenDevelopment
    "約束性規格", # term:Spec
  ]
series = ["規格驅動開發的治理邊界：戳破集體幻覺與實踐分層防護的倖存者指南"]
[ai_info]
    [ai_info.generation]
        model = "Gemini 3 Flash"
        agent = "Antigravity IDE 1.19.6.0"
    [ai_info.refinement]
        model = "Gemini 3.5 Flash"
        agent = "Antigravity IDE 2.0.4"
+++

<!--more-->

## 背景

在缺乏「**單一事實來源**（Single Source of Truth） <!-- term:SingleSourceOfTruth -->」的專案早期，或者在面對錯綜複雜的遺留系統 時，開發團隊經常陷入「**規格稀疏期**（Spec-Sparse Period） <!-- term:SpecSparsePeriod -->」。在這個階段，系統架構充滿了隨意增建的模組，並且沒有一份完整、**約束性規格**（Spec） <!-- term:Spec --> 來指引新的開發項目。

> [!IMPORTANT]
> **單一事實來源** <!-- term:SingleSourceOfTruth --> (Single Source of Truth): 指在特定工作執行緒中唯一被視為絕對真實與合法的結構化資料來源，所有操作皆以其為單向基準。 <!-- anchor:SingleSourceOfTruth -->
> **規格稀疏期** <!-- term:SpecSparsePeriod --> (Spec-Sparse Period): 專案初期或規格導入早期，此時規格覆蓋率低，多數行為以程式碼為真相來源的過渡階段。 <!-- anchor:SpecSparsePeriod -->
> **約束性規格** <!-- term:Spec --> (Spec): 以結構化或機器可讀格式定義的系統或 API 合約規範。 <!-- anchor:Spec -->


傳統的開發流程如果強硬地要求在此階段導入**規格驅動開發**（Spec-Driven Development） <!-- term:SpecDrivenDevelopment -->，往往會遭遇兩種死胡同：
1.  **無政府狀態**：工程師各自為政，有人看舊程式碼通靈，有人發明自己的介面型別。系統快速孳生出無數微小且互不相容的名詞定義，最終導致龐大的語意坍縮 (**語意坍塌**（Semantic Collapse） <!-- term:SemanticCollapse -->)。
2.  **官僚主義癱瘓**：團隊被要求停下所有的功能開發，陷入無止盡的規格會議。為了決定一個時間戳記應該是字串還是整數，可以耗費數週。這導致了嚴重的**分析癱瘓**（Analysis Paralysis） <!-- term:AnalysisParalysis -->，專案動能歸零。

> [!IMPORTANT]
> **規格驅動開發** <!-- term:SpecDrivenDevelopment --> (Spec-Driven Development): 以規格文件為基準約束程式碼行為，確保實作與規格始終對齊的開發方法。 <!-- anchor:SpecDrivenDevelopment -->
> **語意坍塌** <!-- term:SemanticCollapse --> (Semantic Collapse): 大型語言模型在推理時，其認知機制因為指令與資料邊界模糊而導致對架構與內容產出失焦的現象。 <!-- anchor:SemanticCollapse -->
> **分析癱瘓** <!-- term:AnalysisParalysis --> (Analysis Paralysis): 因過度追求完美規格或陷入無止盡討論，導致開發動能喪失、無法實際推進的停滯狀態。 <!-- anchor:AnalysisParalysis -->


問題的核心在於：如果我們不依賴一份完美的規格來推動開發，我們如何確保系統在這段陣痛期中不會崩潰，且能穩步收斂知識與架構？

## 發現

為了找出解答，檢視了多種處理知識與規格矛盾的方法。發現最關鍵的突破口在於改變規格的「防護層級」與「對齊視角」。

如果我們承認，在真實專案的「規格稀疏期 <!-- term:SpecSparsePeriod -->」，強求一份完美的規格是不切實際的幻想，那我們究竟該如何進行日常編碼與**代理人**（AI Agent） <!-- term:AiAgent --> 協作？

> [!IMPORTANT]
> **AI 代理人** <!-- term:AiAgent --> (AI Agent): 具備自主理解、推論與程式碼生成能力，能在給定規則下執行特定任務的 AI 協作者。 <!-- anchor:AiAgent -->


答案是：**擁抱混沌，但用結構化的方式收容它。** 我們不僅需要最終的強制規格，我們還迫切需要一種「容許缺陷、衝突與爭議存在」的代理規格。將其定義為「**觀察性綱要**（Descriptive Schema） <!-- term:DescriptiveSchema -->」。

> [!IMPORTANT]
> **觀察性綱要** <!-- term:DescriptiveSchema --> (Descriptive Schema): 在規格不明確的混沌階段中，用以收集並記錄現行系統狀態、缺陷與爭議的過渡性資料綱要。 <!-- anchor:DescriptiveSchema -->


這份綱要的目的，並不是對專案下達「必須怎麼做」的強硬法律，而是作為一份「現況健檢報告」。更重要的是，當我們配置多個 代理人 <!-- term:AiAgent --> 在背景進行**反向工程**（Reverse Engineering） <!-- term:ReverseEngineering -->或掃描遺留程式碼時，必須賦予牠們一個明確的「**探索邊界**（Exploration Boundary） <!-- term:ExplorationBoundary -->」。我們指示 Agent去爬梳舊有腳本，當發現任何未記載的介面屬性時，全數寫入這份觀察性綱要 <!-- term:DescriptiveSchema -->中，並針對與預期不符之處加上衝突標籤 (`x-conflict`) 供日後決議。

> [!IMPORTANT]
> **反向工程** <!-- term:ReverseEngineering --> (Reverse Engineering): 透過分析現行系統的原始碼或運作行為，推導並重建出系統架構與規格的工程手段。 <!-- anchor:ReverseEngineering -->
> **探索邊界** <!-- term:ExplorationBoundary --> (Exploration Boundary): 指示自動化代理人在進行程式碼反向工程或掃描時的目標約束範疇。 <!-- anchor:ExplorationBoundary -->


## 技術啟示

調查結果顯示，有效削減知識債並平穩過渡至規格驅動的關鍵，在於執行精準的**「**知識路由**（Attribution Routing） <!-- term:AttributionRouting -->」**與清創手術。以下是三個具體的債務轉化行動框架：

> [!IMPORTANT]
> **知識路由** <!-- term:AttributionRouting --> (Attribution Routing): 將系統的非結構化知識或遺留債務，精準指派並分流至合適的追蹤與管理工具之機制。 <!-- anchor:AttributionRouting -->


### 行動一：將「願景」轉化為「觀察性 Schema」

專案初期常遇見將**未來的期望**（What Should Be） <!-- term:WhatShouldBe -->記錄於文件中的狀況。若將這段「計畫中」的設計，當作「已實現」的規格寫入正式的描述檔中，將誘發**前瞻性規格**（Forward-Looking Spec） <!-- term:ForwardLookingSpec -->漂移 (Forward-looking **規格漂移**（Spec Drift） <!-- term:SpecDrift -->)。正確的清創作法，是將其寫入綱要，但強制標記為「未實作的願景」。

> [!IMPORTANT]
> **未來的期望** <!-- term:WhatShouldBe --> (What Should Be): 計畫在後續階段實作，但目前在系統中尚未真實落地的設計願景。 <!-- anchor:WhatShouldBe -->
> **前瞻性規格** <!-- term:ForwardLookingSpec --> (Forward-Looking Spec): 將計畫中但尚未實作的行為描述為已實現的規格 <!-- anchor:ForwardLookingSpec -->
> **規格漂移** <!-- term:SpecDrift --> (Spec Drift): 系統行為規格文件與真實程式碼實作之間，隨著時間演化產生的語意偏離現象。 <!-- anchor:SpecDrift -->


```yaml
# [正確/高解析度] 將願景顯性化為觀察目標
PaginationGraphLinks:
  description: "[PLANNED VISION] 未來支援關聯圖譜的願景結構。目前尚未實作，Agent 於推論時請勿假設其存在。"
  x-governance-level: "Level-3-Vision"
  properties: 
    # ...
```

*發現效益*：團隊有了一個具體、可討論結構的實體目標。而在編譯期或 Agent 的上下文中，這個物件被明確降級拒絕，徹底消弭了因未來規格引發**幻覺**（Hallucination） <!-- term:Hallucination -->的可能。

> [!IMPORTANT]
> **幻覺** <!-- term:Hallucination --> (Hallucination): 大型語言模型在面對不實或矛盾資訊時，生成不符合客觀現實或超出脈絡之回應的錯誤現象。 <!-- anchor:Hallucination -->


### 行動二：將「舊需求與衝突」化為排程工作

當反向掃描發現現行系統僅回傳一個簡陋的逗號分隔字串，而舊有需求文件卻聲稱會回傳一個完整的「明細陣列物件」時，衝突即刻浮現。切忌在綱要中進行投機設計 (Speculative Fix)，強行將其宣告為美好的陣列以迎合過期的文件。這是一個**事實錯誤**的**技術債**（Technical Debt） <!-- term:TechnicalDebt -->。正確的清創作法，是將這個「規格與現實的落差」從綱要的屬性中拔除，並轉換成具有生命週期的工作項目（如 Issue Tracker 中的 Ticket 或程式碼層級的 `TODO`），同時將綱要退回至真實殘酷的「字串描述」狀態。

> [!IMPORTANT]
> **技術債** <!-- term:TechnicalDebt --> (Technical Debt): 程式碼中為求快速交付而妥協、待重構與修復的設計或品質缺陷。 <!-- anchor:TechnicalDebt -->


*發現效益*：落差與債務不再隱藏於文件深處，而是進入了可追蹤的排程系統。它成為一項待處理的工程任務，而非長期誤導的系統謊言。

### 行動三：用 Agent 規則取代人類風格指南

許多專案維護著數十頁供人類閱讀的「開發風格指南」，記述著「變數命名禁止使用 Pinyin」、「禁止從儲存庫層直接拋出內部模型」等規矩。強迫人類或 Agent 閱讀並記憶這些「**規範性知識**（Prescriptive Knowledge） <!-- term:PrescriptiveKnowledge -->」，是徒勞無功的。

> [!IMPORTANT]
> **規範性知識** <!-- term:PrescriptiveKnowledge --> (Prescriptive Knowledge): 指引或規範系統應該如何被開發、命名或組織的規則與風格導向知識。 <!-- anchor:PrescriptiveKnowledge -->


正確的清創作法，是將這些**準則**（Guidelines） <!-- term:Guidelines -->全數翻譯成約束性工具的設定檔（例如靜態**檢查工具**（Linter） <!-- term:Linter --> 檢查工具 <!-- term:Linter --> 的規則集，或是內建於 Agent 工作流的驗證閘門防護腳本）。隨後，徹底銷毀那些純文字格式風格指南。

> [!IMPORTANT]
> **準則** <!-- term:Guidelines --> (Guidelines): 強制性的專案準則，指導如何正確地做事 <!-- anchor:Guidelines -->
> **檢查工具** <!-- term:Linter --> (Linter): 在開發期或持續整合管線中，用以靜態掃描程式碼並揪出風格或語法錯誤的工具。 <!-- anchor:Linter -->


*發現效益*：這徹底實踐了「防呆機制」。寫下來的原則 100% 透過機器被執行，完全封殺了規範性知識 <!-- term:PrescriptiveKnowledge -->漂移的空間，確保底層品質不再倒退。

完成這三個核心行動後，系統將不再被完美且不切實際的規格所綑綁。取而代之的，是誠實且精準標示了衝突的**觀察性綱要** <!-- term:DescriptiveSchema -->，以及在底層堅定防守系統不致崩塌的**自動化規則護欄**。這正是跨越規格稀疏期 <!-- term:SpecSparsePeriod -->，邁向系統穩態的唯一存活之道。

## 結論