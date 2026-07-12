+++
title = "規格導入不必是瀑布陷阱"
date = "2026-03-12T16:00:02+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "分析將規格驅動開發引入棕地專案時的規格債概念，剖析差量開發流程的五大迷思，並闡述規格稀疏期的按需校對與增量形式化運作模式。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "AI 代理人", # term:AiAgent
    "規格驅動開發", # term:SpecDrivenDevelopment
    "規格債", # term:SpecDebt
    "增量形式化", # term:IncrementalFormalization
    "差量流程", # term:DeltaFlow
    "技術債", # term:TechnicalDebt
    "棕地專案", # term:BrownfieldProject
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

把規格引入既有專案時，最常見的恐懼是：「這是不是要我們先寫完所有規格，再動手改程式？」這個恐懼有歷史根據——**瀑布模型**（Waterfall Model） <!-- term:WaterfallModel -->正是這樣運作的。但**規格驅動開發**（Spec-Driven Development） <!-- term:SpecDrivenDevelopment -->和瀑布是不同的東西。瀑布要求階段完整性：規格寫完才能設計，設計完才能編碼。規格驅動開發 <!-- term:SpecDrivenDevelopment -->只要求一件事：當規格存在時，程式碼必須與之對齊。

> [!IMPORTANT]
> **瀑布模型** <!-- term:WaterfallModel --> (Waterfall Model): 要求在進入下一開發階段前必須完全完成前一階段（如先寫完所有規格）的傳統軟體開發生命週期模型。 <!-- anchor:WaterfallModel -->
> **規格驅動開發** <!-- term:SpecDrivenDevelopment --> (Spec-Driven Development): 以規格文件為基準約束程式碼行為，確保實作與規格始終對齊的開發方法。 <!-- anchor:SpecDrivenDevelopment -->


這個區別看似微小，實際上決定了導入策略是否可行。本文從「**規格債**（Spec Debt） <!-- term:SpecDebt -->」的概念出發，拆解五個常見的**差量**（Delta） <!-- term:Delta -->開發迷思，描述**規格稀疏期**（Spec-Sparse Period） <!-- term:SpecSparsePeriod -->的正確運作方式，並探討從「建立規格」到「管理規格變更」的轉換時機。

> [!IMPORTANT]
> **規格債** <!-- term:SpecDebt --> (Spec Debt): 系統中已實作但尚未被明確規格文件定義或記錄的行為所累積的驗證風險。 <!-- anchor:SpecDebt -->
> **差量** <!-- term:Delta --> (Delta): 相對於已存在規格基線的具體變化與修改項目。 <!-- anchor:Delta -->
> **規格稀疏期** <!-- term:SpecSparsePeriod --> (Spec-Sparse Period): 專案初期或規格導入早期，此時規格覆蓋率低，多數行為以程式碼為真相來源的過渡階段。 <!-- anchor:SpecSparsePeriod -->


## 分析

### 規格債：未被書寫的行為

**技術債**（Technical Debt） <!-- term:TechnicalDebt -->是廣為接受的概念——程式碼中存在已知但未修復的品質問題。規格債 <!-- term:SpecDebt -->是同一思維的延伸：系統中存在已實作但未被明確規格描述的行為。

> [!IMPORTANT]
> **技術債** <!-- term:TechnicalDebt --> (Technical Debt): 程式碼中為求快速交付而妥協、待重構與修復的設計或品質缺陷。 <!-- anchor:TechnicalDebt -->


規格債 <!-- term:SpecDebt -->不代表系統有錯。它代表系統的正確性無法被驗證——因為「正確」的定義不存在。當一個功能只存在於程式碼中，沒有對應的規格描述時，任何人（包括 AI）對該功能的修改都只能憑「讀懂現有程式碼」來判斷是否破壞了**預期行為**（Expected Behavior） <!-- term:ExpectedBehavior -->。這和技術債 <!-- term:TechnicalDebt -->的風險結構相同：債務不會立即造成問題，但隨著修改次數增加，破壞未記錄行為的機率持續累積。

> [!IMPORTANT]
> **預期行為** <!-- term:ExpectedBehavior --> (Expected Behavior): 系統或模組在特定輸入或情境下被要求達到的正確輸出與副作用狀態 <!-- anchor:ExpectedBehavior -->


關鍵差異在於還債方式。技術債 <!-- term:TechnicalDebt -->需要專門的重構工期。規格債 <!-- term:SpecDebt -->可以在功能開發過程中順帶清償——每次觸及一個功能時，把觀察到的行為記錄為規格的**架構層**（Architecture） <!-- term:Architecture -->，把確認的意圖記錄為**需求層**（Requirements） <!-- term:Requirements -->。這就是**增量形式化**（Incremental Formalization） <!-- term:IncrementalFormalization -->的基礎，後文會展開討論。

> [!IMPORTANT]
> **架構層** <!-- term:Architecture --> (Architecture): 規格文件中用以客觀記錄系統「實際在做什麼」的事實陳述層。 <!-- anchor:Architecture -->
> **需求層** <!-- term:Requirements --> (Requirements): 規格文件中用以定義系統「應該做什麼」的行為契約與設計意圖層。 <!-- anchor:Requirements -->
> **增量形式化** <!-- term:IncrementalFormalization --> (Incremental Formalization): 在功能開發過程中，將理解的系統行為與意圖漸進式寫入規格文件的清償規格債機制。 <!-- anchor:IncrementalFormalization -->


### 五個差量開發迷思

**差量流程**（Delta Flow） <!-- term:DeltaFlow -->是規格變更管理的核心機制：提出**變更提案**（Proposal） <!-- term:Proposal -->，描述新增、修改、刪除的規格項目，審查後合併到基線規格中。這個流程本身很簡單，但圍繞它產生了五個常見迷思。

> [!IMPORTANT]
> **差量流程** <!-- term:DeltaFlow --> (Delta Flow): 通過提案描述規格之新增、修改與刪除，以管理規格基線變更的機制。 <!-- anchor:DeltaFlow -->
> **變更提案** <!-- term:Proposal --> (Proposal): 在差量流程中提交的變更申請，用以詳細描述規格的修改內容與動機。 <!-- anchor:Proposal -->


**迷思一：差量 <!-- term:Delta -->需要完整基線。** 差量 <!-- term:Delta -->的定義是「相對於基線的變化」，所以必須先有完整的基線規格？錯。差量 <!-- term:Delta -->只需要相對於「已存在的規格」的變化。如果一個領域只有三條需求被明確記錄，那麼針對這三條的修改就是有效的差量 <!-- term:Delta -->。基線的完整性和差量 <!-- term:Delta -->的有效性是獨立的維度。

**迷思二：稀疏期不能使用差量 <!-- term:Delta -->。** 既然規格還很稀疏，用差量流程 <!-- term:DeltaFlow -->不是過度工程嗎？要看修改對象。如果你要修改的行為恰好已經有規格描述，差量流程 <!-- term:DeltaFlow -->就是正確的工具——不管整體規格覆蓋率多低。如果你要修改的行為沒有規格，那確實不需要差量 <!-- term:Delta -->，因為沒有基線可以參照。判斷標準是「被修改的特定行為是否有規格」，不是「整體覆蓋率」。

**迷思三：改程式前必須先快照規格。** 這是瀑布思維的殘留。**規格快照**（Snapshot） <!-- term:Snapshot -->在頻繁變動期有意義，例如版本發布前凍結規格。在稀疏期，規格本身就是片段的，快照片段沒有額外價值。規格的快照策略應該是功能開發的副產品（byproduct），不是**前置條件**（Prerequisite） <!-- term:Prerequisite -->。

> [!IMPORTANT]
> **規格快照** <!-- term:Snapshot --> (Snapshot): 對特定時間點的規格進行凍結與備份，常用於版本發布前。 <!-- anchor:Snapshot -->
> **前置條件** <!-- term:Prerequisite --> (Prerequisite): 執行某項開發活動之前必須滿足的準備工作或狀態。 <!-- anchor:Prerequisite -->


**迷思四：所有變更都需要正式提案。** 差量流程 <!-- term:DeltaFlow -->的正式程度應該匹配變更的影響範圍。修正一個架構層 <!-- term:Architecture -->的事實性錯誤——直接修改就好，不需要提案。新增或修改需求層 <!-- term:Requirements -->的行為契約——提案流程提供了變更的可追溯性。**比例原則**（Proportionality） <!-- term:Proportionality -->是關鍵：治理的重量應該匹配風險的重量。

> [!IMPORTANT]
> **比例原則** <!-- term:Proportionality --> (Proportionality): 治理流程的繁簡程度應與變更影響範圍及風險大小相匹配的設計原則。 <!-- anchor:Proportionality -->


**迷思五：差量流程 <!-- term:DeltaFlow -->是重量級的。** 這通常源於對流程的過度想像。一個最小差量 <!-- term:Delta -->提案只需要三個元素：變更的規格檔路徑、ADDED/MODIFIED/REMOVED 標記、以及變更的具體內容。這比大多數 pull request 描述還短。流程的目的不是增加儀式，而是讓「為什麼改」和「改了什麼」同時被記錄。

### 規格稀疏期的運作模式

理解了上述迷思後，規格稀疏期 <!-- term:SpecSparsePeriod -->的運作模式就很清楚了。核心原則是三條：

第一，**按需校對，不按計畫校對。** 規格-**程式碼校對**（Spec-Code Reconciliation） <!-- term:SpecCodeReconciliation -->只在規格存在時才有意義。當你要修改一個功能，先查規格是否覆蓋這個功能。有規格就校對，確認程式碼與規格一致；沒有規格就跳過，以程式碼為真相來源。不要為了執行校對流程而先補寫規格。

> [!IMPORTANT]
> **程式碼校對** <!-- term:SpecCodeReconciliation --> (Spec-Code Reconciliation): 比對並調和程式碼實作與規格文件，確保兩者一致的驗證過程。 <!-- anchor:SpecCodeReconciliation -->


第二，**副產品驅動的規格成長。** 每次功能開發都是觀察系統行為的機會。開發者在理解現有程式碼的過程中，自然會釐清「系統實際上在做什麼」和「系統應該做什麼」。把這些理解記錄下來——前者成為架構層 <!-- term:Architecture -->，後者成為需求層 <!-- term:Requirements -->——規格就在功能開發的副產品中逐步成長。這和「先寫規格再寫程式」是截然不同的模式。

第三，**穿透到程式碼。** 當規格不存在時，知識探索的順序自然穿透到下一層：先查規格、再查**共置文件**（Co-Located Readme） <!-- term:CoLocatedReadme -->、最後搜尋程式碼。稀疏期只是意味著穿透到程式碼的頻率更高。這不是失敗——這是設計中預期的退化路徑（graceful degradation）。

> [!IMPORTANT]
> **共置文件** <!-- term:CoLocatedReadme --> (Co-Located Readme): 與程式碼放在相同倉庫目錄下的說明文件，利於隨時查閱。 <!-- anchor:CoLocatedReadme -->


### 從建立到管理：轉換時機

一個領域什麼時候從「建立規格」階段進入「管理規格變更」階段？答案是：當該領域的規格密度足以約束實作決策時。

這個閾值是**逐領域**（Per-Domain） <!-- term:PerDomain -->的，不是全域的。前端 UI 規格可能已經足夠密集，可以使用差量流程 <!-- term:DeltaFlow -->管理變更；同時後端服務規格可能仍然很稀疏，每次觸及都還是在「建立」模式。硬要統一全專案的規格管理階段，就是把組織層級的一致性置於實際生產力之上——這正是瀑布模型 <!-- term:WaterfallModel -->的核心錯誤。

> [!IMPORTANT]
> **逐領域** <!-- term:PerDomain --> (Per-Domain): 以特定業務或技術領域為單位進行治理或轉換，而非一刀切的全域做法。 <!-- anchor:PerDomain -->


判斷訊號包括：同一領域的規格被第二個人引用（表示規格開始有讀者，不只有作者）、規格校對開始發現「程式碼不符合規格」而非「規格不存在」（表示規格的覆蓋已經開始約束實作）、以及修改一條需求時需要考慮對其他需求的影響（表示需求之間已經形成結構）。

### 增量形式化：從隱性到顯性

增量形式化 <!-- term:IncrementalFormalization -->是規格債 <!-- term:SpecDebt -->的自然清償機制。核心概念很簡單：每次功能開發中，開發者對系統行為產生的理解，有一部分可以被轉換為明確的規格描述。這個轉換不需要額外的「文件撰寫」工期——它是理解過程的副產品。

這和傳統的文件撰寫（documentation sprint）有根本區別。文件撰寫是一個獨立活動，目標是「把已知的東西寫下來」。增量形式化 <!-- term:IncrementalFormalization -->是功能開發的附帶效果，目標是「把剛理解的東西在理解最深的時候記錄下來」。時機上的差異導致品質上的差異——開發當下記錄的規格，比事後回憶撰寫的文件更準確。

增量形式化 <!-- term:IncrementalFormalization -->也有其邊界。不是所有理解都值得形式化。判斷標準回到規格的雙層結構：如果理解的是系統「實際在做什麼」（事實），放入架構層 <!-- term:Architecture -->，成本極低；如果理解的是系統「應該做什麼」（意圖），需要產品確認後才能放入需求層 <!-- term:Requirements -->。架構層 <!-- term:Architecture -->可以單方面形式化，需求層 <!-- term:Requirements -->需要跨角色確認——這個區別防止了開發者把個人對系統的理解錯誤地提升為行為契約。

## 結論

這些觀察背後有一個共同的張力：規格管理的理想狀態（完整覆蓋、全面校對、正式差量流程 <!-- term:DeltaFlow -->）和當前狀態（稀疏覆蓋、選擇性校對、混合模式）之間的落差。瀑布思維的陷阱在於，它要求先彌合這個落差才能開始工作。增量思維的解法是，讓工作本身成為彌合落差的手段。

這也解釋了為什麼「先寫完規格」的建議在**棕地專案**（Brownfield Project） <!-- term:BrownfieldProject -->中幾乎必然失敗。棕地專案 <!-- term:BrownfieldProject -->的行為已經被程式碼定義了——回頭為現有行為寫規格，要嘛變成抄寫程式碼的自然語言版本（無價值），要嘛變成對程式碼的重新詮釋（高風險）。正確的姿態是承認規格債 <!-- term:SpecDebt -->的存在，然後在每次碰觸系統的機會中漸進式清償。

> [!IMPORTANT]
> **棕地專案** <!-- term:BrownfieldProject --> (Brownfield Project): 已有大量既有程式碼與運作中行為、非從零開始的現存軟體專案。 <!-- anchor:BrownfieldProject -->


另一個值得注意的點是比例原則 <!-- term:Proportionality -->對團隊採納的影響。如果差量流程 <!-- term:DeltaFlow -->讓人感覺是額外負擔，團隊會繞過它。如果差量流程 <!-- term:DeltaFlow -->比 pull request 描述更輕量，團隊會自然使用它。流程設計的成功標準不是「夠嚴謹」，而是「阻力夠低以至於不使用它反而更麻煩」。

## 結論

規格導入的可行路徑有四個支撐點。第一，認識規格債 <!-- term:SpecDebt -->——它和技術債 <!-- term:TechnicalDebt -->一樣是可管理的累積風險，不是必須立即清零的缺陷。第二，差量流程 <!-- term:DeltaFlow -->的門檻是「被修改的行為有規格」，不是「整體覆蓋率足夠」。第三，規格的成長來自功能開發的副產品，不是獨立的文件撰寫工期。第四，從建立到管理的轉換是逐領域 <!-- term:PerDomain -->的，以該領域的規格密度為判斷基準。

這四個支撐點的共同特徵是：它們都把規格管理嵌入現有工作流程，而不是在工作流程上方疊加新的階段。這正是它和瀑布的根本區別——不是階段的串聯，而是實踐的融入。