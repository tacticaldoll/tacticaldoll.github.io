+++
title = "概念採納：外部框架整合時的權威衝突與選擇性吸收"
date = "2026-03-09T22:00:03+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "一個遺留專案在引入 OpenSpec 時面臨與既有治理框架的權威衝突。本文記錄了如何透過鷹架辨識、概念與工具解耦，最終採納概念並實現四步過渡的實踐歷程。"
tags = [
    "經驗報告", # term:ExperienceReport
    "AI 代理人", # term:AiAgent
    "選擇性吸收", # term:SelectiveAbsorption
    "單一事實來源", # term:SingleSourceOfTruth
    "專案指令檔", # term:ProjectInstructions
    "外部規格", # term:Specifications
  ]
series = ["規格驅動開發：遺留專案在棕地環境下的治理演進與選擇性採納"]
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

一個遺留專案正處於從逆向工程知識過渡到**規格驅動開發**（Spec-Driven Development） <!-- term:SpecDrivenDevelopment -->的階段。治理框架已經就位——規則約束編碼品質，技能處理工作流程，知識庫被定義為過渡性債務。缺少的是一個承載行為規格的結構。**OpenSpec** 作為候選框架被評估，它提供了完整的工具鏈：目錄結構（`specs/` + `changes/` + `archive/`）、規格格式（Requirement + Scenario + RFC 2119）、CLI 命令列工具（`openspec init/propose/accept`）、以及基於 JSON **結構合約**（Schema） <!-- term:Schema --> 的驗證引擎。

> [!IMPORTANT]
> **規格驅動開發** <!-- term:SpecDrivenDevelopment --> (Spec-Driven Development): 以規格文件為基準約束程式碼行為，確保實作與規格始終對齊的開發方法。 <!-- anchor:SpecDrivenDevelopment -->
> **結構合約** <!-- term:Schema --> (Schema): 定義資料欄位、型別與排版限制的強型別規格定義，用於強制約束模型產出的格式。 <!-- anchor:Schema -->


評估的起始假設是「整合 OpenSpec」——將它作為一個完整的框架導入。但分析過程揭示了一個深層矛盾：OpenSpec 和專案既有的治理框架對「誰是行為的最終權威」這個問題有不相容的回答。本文記錄了從發現矛盾到選擇性採納的決策歷程。

## 發現

### 階段一：權威衝突的浮現

初始評估聚焦在相容性問題上。OpenSpec 的核心假設是：`specs/` 是行為的單一真相來源，所有其他文件——規則、知識、程式碼註釋——都是次要的。與此同時，專案的元規則（既有治理框架的核心機制，作為權威衝突的另一方）定義了一套四層文件階層：Level 0 元規則具有絕對權威，Level 1 **準則**（Guidelines） <!-- term:Guidelines -->次之，Level 2 規格再次，Level 3 知識最低。

> [!IMPORTANT]
> **準則** <!-- term:Guidelines --> (Guidelines): 強制性的專案準則，指導如何正確地做事 <!-- anchor:Guidelines -->


衝突的結構是這樣的：OpenSpec 假設 `specs/` 是最高權威；元規則假設 Level 0 是最高權威，而規格只是 Level 2。兩個系統不是在不同的領域各自運作——它們對同一個問題（「什麼文件具有最高行為權威」）給出了互斥的答案。

> [!NOTE]
> **Decision Point**: 權威衝突是否可以透過層級調整來化解
> — Alternatives: 將 OpenSpec 的 `specs/` 映射為 Level 2，讓元規則繼續治理它（維持現狀，最小變動）；將 `specs/` 提升為 Level 0 同級（改造元規則）；承認兩者不相容，選擇其一
> — Outcome: 選擇第三項。映射方案違反 OpenSpec 的設計意圖——它假設規格是最高權威，被降為 Level 2 等於閹割其核心價值。提升方案引入兩個 Level 0——衝突解決機制本身需要一個更高的仲裁者，造成無限回歸。不相容是結構性的，不是配置性的

這個發現改變了評估的方向——從「如何整合」轉向「如何選擇」。

### 階段二：鷹架假說的驗證

權威衝突暴露後，自然的問題是：既然兩者不相容，應該保留哪一個？

直覺上，元規則是精心設計的治理基礎設施，放棄它意味著放棄整個層級系統。但進一步追溯元規則每一條定義的建立理由後，一個不同的圖景浮現：元規則的四個層級定義不是針對系統的本質需求，而是針對 `context/`（過渡性知識庫，作為**鷹架**（Scaffolding） <!-- term:Scaffolding -->驗證中「被治理對象消失」的實例）過渡期的特定問題。

> [!IMPORTANT]
> **鷹架** <!-- term:Scaffolding --> (Scaffolding): 專案在過渡或重構階段所建立的臨時性治理機制，其生命週期與特定過渡性問題綁定，問題解決後即應予以拆除。 <!-- anchor:Scaffolding -->


Level 3 定義用於治理 `context/` 知識庫——但 `context/` 正在被遷移。Level 2 定義用於銜接**外部規格**（Specifications） <!-- term:Specifications -->輸入——但 `specs/` 將取代這個銜接機制。Level 0 和 Level 1 的存在是為了讓 Level 2 和 Level 3 有衝突解決框架——但如果 Level 2 和 Level 3 失去被治理對象，衝突解決框架也就失去了用途。

> [!IMPORTANT]
> **外部規格** <!-- term:Specifications --> (Specifications): 由外部團隊提供的權威性系統規格文件 <!-- anchor:Specifications -->


依賴鏈的每一個節點都指向過渡性問題而非持久性需求。這意味著元規則是鷹架 <!-- term:Scaffolding -->，不是基礎設施。

> [!NOTE]
> **Decision Point**: 元規則的定位——基礎設施還是鷹架 <!-- term:Scaffolding -->
> — Alternatives: 基礎設施 vs. 鷹架 <!-- term:Scaffolding -->
> — Outcome: 鷹架 <!-- term:Scaffolding -->。三項驗證全部通過：被治理對象正在消失（`context/` 遷移中）、**依賴圖**（Dependency Graph） <!-- term:DependencyGraph -->指向過渡任務、移除後系統功能不退化（規則和技能獨立運作）。嘗試保留並演化元規則等於為一個不再需要的機制尋找新的存在理由——那是投機設計

> [!IMPORTANT]
> **依賴圖** <!-- term:DependencyGraph --> (Dependency Graph): 追溯各項治理規則與機制之建立緣由所構成的依賴網絡，用以評估該機制的存續價值與拆除時機。 <!-- anchor:DependencyGraph -->


### 階段三：概念與工具的解耦

確認了「選擇 OpenSpec、退役元規則」的方向後，下一個問題是採納的範圍。OpenSpec 是一個完整的框架，包含概念層面（目錄結構、規格格式、**差量**（Delta） <!-- term:Delta -->變更模型）和工具層面（CLI 命令、JSON 結構合約 <!-- term:Schema --> 驗證）。

> [!IMPORTANT]
> **差量** <!-- term:Delta --> (Delta): 相對於已存在規格基線的具體變化與修改項目。 <!-- anchor:Delta -->


專案已經有一套成熟的操作機制（以下兩個技能作為「既有工具鏈足以覆蓋」的論證依據）。規格對齊技能在實作前比對規格與程式碼，知識沉澱技能在工作結束後將**知識路由**（Attribution Routing） <!-- term:AttributionRouting -->到正確的位置。兩者都是 AI 代理環境的原生技能，與技能生態系深度整合。

> [!IMPORTANT]
> **知識路由** <!-- term:AttributionRouting --> (Attribution Routing): 將系統的非結構化知識或遺留債務，精準指派並分流至合適的追蹤與管理工具之機制。 <!-- anchor:AttributionRouting -->


引入 OpenSpec CLI 意味著在每個操作節點上存在兩條平行路徑：技能驅動的路徑（AI 自動執行）和 CLI 驅動的路徑（人工執行命令）。兩條路徑操作相同的規格目錄，但它們不共享狀態——技能不知道 CLI 做了什麼，CLI 不知道技能做了什麼。

> [!NOTE]
> **Decision Point**: 整體採納還是概念級採納（concept-level adoption）
> — Alternatives: 整體採納（安裝 npm 套件、使用 CLI、配置 schema）vs. 概念級採納（只取目錄結構和格式，用既有技能操作）
> — Outcome: 概念級採納。OpenSpec 的核心價值在於它的思維模型（規格真相來源、差量 <!-- term:Delta -->變更、結構即語意），不在於它的 CLI。CLI 的功能——初始化目錄、產生提案模板、執行接受/歸檔——全部可以由既有技能承擔。引入 CLI 增加的是操作路徑的分裂，不是能力的擴充

### 階段四：執行——四步過渡

決策完成後，過渡分四步執行。

第一步建立 OpenSpec 目錄結構，將先前累積的 10 個規格請求轉換為 OpenSpec 格式，按領域組織為四個子目錄（作為「概念級採納」的具體執行軌跡）。

第二步退役元規則。在刪除前提取兩個可遷移的知識片段——機制選擇測試和準則 <!-- term:Guidelines -->格式規範——寫入**專案指令檔**（Project Instructions） <!-- term:ProjectInstructions -->，然後刪除元規則檔案。同步更新相關規則，將過渡性知識庫的引用替換為規格目錄。

> [!IMPORTANT]
> **專案指令檔** <!-- term:ProjectInstructions --> (Project Instructions): 遺留專案中用以承載所有開發慣例、工程標準與累積知識的單體文字檔案。 <!-- anchor:ProjectInstructions -->


第三步遷移過渡性知識庫的全部 8 個跨切面知識檔案至規格目錄。每個 spec 檔案採用雙層結構：**架構層**（Architecture） <!-- term:Architecture --> 段落承載已確認的行為，規範性需求 段落承載待確認的設計意圖（使用 RFC 2119 + Given/When/Then）。遷移完成後刪除過渡性知識庫。

> [!IMPORTANT]
> **架構層** <!-- term:Architecture --> (Architecture): 規格文件中用以客觀記錄系統「實際在做什麼」的事實陳述層。 <!-- anchor:Architecture -->


第四步更新工作流程連接。規格對齊技能改為從規格目錄讀取，知識沉澱技能的輸出路由改為規格目錄或共置 README。最後執行第一個完整的變更週期驗證——建立提案、完成後歸檔——確認流程端對端可行。

## 補充知識

### 選擇性吸收的一般模式

外部框架的採納存在一個頻譜，從完全不採納到完全採納之間有多個有意義的位置。

| 層級 | 描述 | 適用場景 |
|------|------|---------|
| 概念啟發 | 理解框架的思維模型，不採用任何具體機制 | 框架解決的問題與當前需求不匹配 |
| 概念採納 | 採用框架的思維模型和結構，不採用工具鏈 | 既有工具鏈已能實現框架的操作需求 |
| 工具整合 | 採用框架的工具鏈，與既有系統並行運作 | 框架工具提供了既有系統缺乏的能力 |
| 完全導入 | 以框架取代既有系統 | 既有系統不存在或全面劣於框架 |

每個層級都是正當的選擇——關鍵不在於採納了多少，而在於選擇的理由是否清晰。概念級採納不是「半吊子」的整合，而是在分析了工具層面的增量價值後做出的精確取捨。

### 權威互斥作為設計約束

兩個系統對同一問題給出互斥答案，不一定是其中一個的設計缺陷。更常見的情況是它們各自在不同的設計語境中做出了一致的內部選擇。OpenSpec 在規格驅動語境中假設規格是最高權威；分層治理在治理語境中假設層級系統是最高權威。兩者在各自的語境中都是自洽的。

衝突不在於誰「錯了」，而在於一個系統不能同時有兩個「最高權威」——這是一個邏輯約束，不是品質判斷。辨識這一點比試圖調和更有價值：調和通常意味著一方假裝接受另一方的框架，但在實際運作中仍然按原有邏輯行事。

## 決議

| # | 決策 | 原因 |
|---|------|------|
| 1 | 權威衝突不可調和 | OpenSpec 視規格為最高權威；元規則視層級系統為最高權威。映射或提升都引入新矛盾 |
| 2 | 元規則是鷹架 <!-- term:Scaffolding -->，可退役 | 三項驗證：被治理對象消失、依賴圖 <!-- term:DependencyGraph -->指向過渡任務、移除無功能退化 |
| 3 | 概念級採納 OpenSpec | 核心價值在思維模型非 CLI；既有技能已覆蓋操作需求；CLI 引入路徑分裂 |
| 4 | 雙層 spec 結構 | 架構層 <!-- term:Architecture -->+ 規範性需求— 誠實區分已知行為與設計意圖 |
| 5 | 先提取再拆除 | 元規則中的機制選擇和格式規範被提取至專案指令檔 <!-- term:ProjectInstructions -->後再刪除 |

## 技術啟示

1. **框架的價值往往集中在思維模型而非工具鏈。** OpenSpec 最有價值的貢獻——規格即真相來源、差量 <!-- term:Delta -->變更、結構即語意——全部是概念層面的洞察。CLI 和 結構合約 <!-- term:Schema --> 是這些概念的一種實現方式，但不是唯一的實現方式。當既有環境已經有成熟的操作機制時，概念採納比工具整合更精確地捕捉框架的價值。

2. **權威互斥**（Authority Mutual Exclusion） <!-- term:AuthorityMutualExclusion -->是邏輯約束，不是品質判斷。 發現兩個系統的權威宣告互斥時，反應不應該是「哪個設計得更好」而是「一個系統不能有兩個最高權威」。這把問題從品質評估轉化為選擇問題——需要的不是改善其中一個，而是為當前情境選擇更合適的那一個。

> [!IMPORTANT]
> **權威互斥** <!-- term:AuthorityMutualExclusion --> (Authority Mutual Exclusion): 兩個治理系統或文件針對同一個問題（如最高權威歸屬）給出互斥答案的結構性衝突，通常不可透過簡單調和解決。 <!-- anchor:AuthorityMutualExclusion -->


3. **選擇性吸收**（Selective Absorption） <!-- term:SelectiveAbsorption -->需要清晰的分離面。 框架的概念層和工具層是可以分離的，但前提是能清楚地識別哪些是概念（可用不同工具實現），哪些是工具（與特定實現綁定）。如果框架的概念和工具深度耦合——某個概念只有透過框架的工具才能實現——那概念級採納就不可行。OpenSpec 的概念和 CLI 是鬆耦合的，這使得選擇性吸收 <!-- term:SelectiveAbsorption -->成為可能。

> [!IMPORTANT]
> **選擇性吸收** <!-- term:SelectiveAbsorption --> (Selective Absorption): 在引進外部框架時，不盲目全盤接受其工具鏈，而是精確過濾並僅採納其核心概念與思維模型的整合模式。 <!-- anchor:SelectiveAbsorption -->


4. **先提取再拆除，永遠不要邊拆邊找。** 退役一個機制時，先系統性地識別其中可遷移的知識片段並安置到新位置，然後再執行刪除。「邊拆邊找」的風險是遺漏——被刪除後才發現某個片段有價值，但此時已經需要從版本歷史中打撈。提取是預防性的，打撈是補救性的，兩者的成本差異遠大於直覺。