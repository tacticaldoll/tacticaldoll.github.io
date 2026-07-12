+++
title = "結構約束與 Agent Error Surface：為 AI 協作設計 Extension Point"
date = "2026-03-27T18:30:02+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "探討代碼結構約束如何系統性地窄化 AI 協作開發中的 Error Surface，分析術語漂移、引用完整性與語意預設偏差等失敗模式，並將 Agent Safety 提倡為 extension point 的關鍵設計維度。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "AI 代理人", # term:AiAgent
    "AI 治理", # term:AIGovernance
    "代理人安全", # term:AgentSafety
    "錯誤表面", # term:ErrorSurface
    "結構約束", # term:StructuralConstraint
    "擴充點", # term:ExtensionPoint
    "術語漂移", # term:TerminologyDrift
  ]
series = ["分類 Dispatch 與結構約束：從 Decorator Chain 到 Agent Error Surface 的演進啟示"]
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

在一次架構重構中，AI agent 協助將分散的分類函數集中為**宣告式**（Declarative） <!-- term:Declarative -->資料表。重構本身順利完成，但事後 review 揭露了五個 agent 引入的問題——不是邏輯錯誤，而是命名殘留、引用遺漏、**語意預設偏差**（Semantic Default Bias） <!-- term:SemanticDefaultBias -->。這些問題有一個共同特徵：它們都發生在 agent 有較多自由度的地方，而在結構受限的操作中沒有出現。

> [!IMPORTANT]
> **宣告式** <!-- term:Declarative --> (Declarative): 一種編程或治理正規，僅描述預期達成的狀態或目標，將具體執行與自癒細節委派給底層實體或系統。 <!-- anchor:Declarative -->
> **語意預設偏差** <!-- term:SemanticDefaultBias --> (Semantic Default Bias): AI 代理人預設程式碼執行快樂路徑（Happy Path）而忽略條件式限制或例外情況的認知偏差。 <!-- anchor:SemanticDefaultBias -->


這個觀察引出一個問題：程式碼結構的約束程度如何影響 AI agent 的出錯率？如果影響顯著，那麼在設計 extension point 時，「對 agent 友善」應該是一個設計維度。

## 發現

### 三種失敗模式

五個觀察可歸為三種失敗模式，每種反映 agent 的一個認知特性。

**術語漂移**（Terminology Drift） <!-- term:TerminologyDrift -->。 Agent 將新建的模組以剛被消解的概念命名。Agent 從對話 context 中繼承了該概念的高頻詞彙，沒有主動質疑它是否仍然精確——在舊概念被消解的場景下，沿用舊術語是 agent 的預設行為，因為 context window 中舊術語的出現頻率遠高於新術語。

> [!IMPORTANT]
> **術語漂移** <!-- term:TerminologyDrift --> (Terminology Drift): 在概念消解或變更的場景下，AI 代理人因對話上下文中舊術語高頻出現而沿用舊稱呼的預設行為。 <!-- anchor:TerminologyDrift -->


**引用完整性**（Referential Integrity） <!-- term:ReferentialIntegrity -->。 批量重命名一個型別後，一處 function pointer 型別簽名中的引用被遺漏。同樣，更新 governance 文件時，主要段落的術語被更新了，但其他段落的交叉引用未被發現。Agent 在批量操作中傾向處理「主要位置」——import 語句、型別定義、函數簽名——而遺漏出現在非典型位置的引用（fn pointer 型別標注、散文段落中的術語）。

> [!IMPORTANT]
> **引用完整性** <!-- term:ReferentialIntegrity --> (Referential Integrity): 批量變更或重命名時，系統中所有交叉引用（包括非典型位置的類型標記與文件段落）皆被同步更新的狀態。 <!-- anchor:ReferentialIntegrity -->


**語意預設偏差 <!-- term:SemanticDefaultBias -->。** 一個 builder 函數最初被實作為總是回傳成功構建的物件，而 spec 要求在**前置條件**（Prerequisite） <!-- term:Prerequisite -->不滿足時回傳空值（條件式構建）。Agent 預設了 happy path——build 函數就應該 build 出東西——忽略了條件式操作的語意。這個偏差在 verify 階段被攔截。

> [!IMPORTANT]
> **前置條件** <!-- term:Prerequisite --> (Prerequisite): 執行某項開發活動之前必須滿足的準備工作或狀態。 <!-- anchor:Prerequisite -->


### Error Surface 與結構約束

三種失敗模式指向一個共同原理：**agent 的 error surface 與 extension point 的**結構約束**（Structural Constraint） <!-- term:StructuralConstraint -->成反比**。

> [!IMPORTANT]
> **結構約束** <!-- term:StructuralConstraint --> (Structural Constraint): 限制開發自由度與變體形狀的程式碼結構設計，用以消除非法操作空間、收窄錯誤表面。 <!-- anchor:StructuralConstraint -->


```
error surface ∝ 1 / structural constraint
```

這個關係在同一系統的三段**架構演進**（Architecture Evolution） <!-- term:ArchitectureEvolution -->中清晰可見。Decorator chain 時期，新增一個 kind 需要理解 wrapping 拓撲、chain 順序、並從既有實作複製路徑解析邏輯——error surface 很大，agent 需要同時正確處理多個不受約束的決策點。分散分類函數時期，每個 kind 自己寫路徑解析——error surface 中等，其中一個 kind 實際上就漏掉了三種路徑形式中的兩種。數據 table 時期，新增 kind 只需加一行固定結構的表條目加上寫一個 build 函數——error surface 很小，因為表的結構本身約束了 agent 能做的事。

> [!IMPORTANT]
> **架構演進** <!-- term:ArchitectureEvolution --> (Architecture Evolution): 系統架構隨時間發展與改進的過程 <!-- anchor:ArchitectureEvolution -->


| 架構 | Extension 需要的決策 | **錯誤表面**（Error Surface） <!-- term:ErrorSurface --> |
|------|---------------------|:---:|
| Decorator chain | wrapping 拓撲 + 順序 + 邏輯複製 | 大 |
| 分散分類函數 | 邏輯複製 + 順序位置 | 中 |
| 數據 table | 加一行表 + 寫 build 函數 | 小 |

> [!IMPORTANT]
> **錯誤表面** <!-- term:ErrorSurface --> (Error Surface): 系統中 AI 代理人或開發者可能引入錯誤或偏離設計意圖的自由度與決策空間範圍。 <!-- anchor:ErrorSurface -->


### 同一原理家族

「結構約束 <!-- term:StructuralConstraint -->窄化 error surface」不是新發現——它是一個已知原理家族的特定實例。

Type theory 中的 "make illegal states unrepresentable" 透過型別系統消除非法狀態：如果型別不允許某種組合，程式碼就不可能寫出那種組合。Parse-don't-validate 透過解析步驟將未驗證的字串轉為帶型別的值：一旦進入型別化領域，後續程式碼不可能操作未驗證的資料。兩者的共同機制都是透過結構約束 <!-- term:StructuralConstraint -->消除整個錯誤類別，而非逐一檢查每個錯誤實例。

數據 table 的 extension point 做了類似的事：表的結構定義了「一行 = pattern + build function pointer」，agent 在這個結構內只能填入符合型別的值。相比之下，不受約束的分類函數是一個任意函數體——agent 可以在裡面做任何事，包括錯誤地複製路徑解析邏輯。

## 結論

### 收斂性任務 vs 發散性任務

結構約束 <!-- term:StructuralConstraint -->並非在所有場景下都有利。區分在於任務的收斂性。

**收斂性任務**（Convergent Task） <!-- term:ConvergentTask -->的答案**形狀**（Data Shape） <!-- term:DataShape -->已知，工作是填入內容。新增一個資源類型、填寫一個 guard 條件、實作一個 build 函數——這些都是收斂性任務 <!-- term:ConvergentTask -->。約束在此幫助 agent：窄化搜索空間，減少需要做的決策數量。

> [!IMPORTANT]
> **收斂性任務** <!-- term:ConvergentTask --> (Convergent Task): 答案形狀已知、主要工作為在既定結構內填入內容的開發任務，適合以強結構約束降低出錯率。 <!-- anchor:ConvergentTask -->
> **形狀** <!-- term:DataShape --> (Data Shape): 資料結構或物件所包含的屬性與型別定義，通常由型別系統來描述 <!-- anchor:DataShape -->


**發散性任務**（Divergent Task） <!-- term:DivergentTask -->的答案形狀 <!-- term:DataShape -->未知，工作是探索結構。同一次重構的設計探索階段就是典型：agent 自由探索了共用 helper + 分散 guard、集中式宣告表、自註冊、代數資料型別 dispatch 等六種方案，經過多輪挑戰和修正才收斂到最終設計。如果一開始就約束在「只能加 helper」的框架中，不會發現集中式宣告表的方向。

> [!IMPORTANT]
> **發散性任務** <!-- term:DivergentTask --> (Divergent Task): 答案形狀未知、需要廣泛探索設計方案的任務，此類任務需要較高的自由度而不宜過度約束。 <!-- anchor:DivergentTask -->


關鍵限定詞：**extension point 本質上是收斂性任務** <!-- term:ConvergentTask -->。Extension 的定義就是在既有結構中加入新的變體——形狀 <!-- term:DataShape -->已知（由結構定義），差異已知（由需求定義），工作是填入兩者的交集。因此，為 extension point 選擇受限結構不是犧牲彈性——是匹配任務的收斂本質。

### 設計維度的擴展

傳統的 extension point 設計考量包括擴充成本、型別安全、可測試性。本文的觀察建議增加一個維度：**agent error surface**。當團隊使用 AI agent 協作開發時，extension point 的結構約束 <!-- term:StructuralConstraint -->程度直接影響 agent 引入錯誤的機率。

這不是要為 agent 降低標準——verify 階段應該攔截所有偏差。但攔截的成本與偏差的數量成正比。如果 extension point 的設計本身就能減少偏差，verify 的負擔就更輕，整體開發效率更高。

## 結論

**結構約束 <!-- term:StructuralConstraint -->窄化 agent error surface——在收斂性任務 <!-- term:ConvergentTask -->中。** 這是 "make illegal states unrepresentable" 原理在 AI 協作場景中的延伸：不是透過型別消除非法狀態，而是透過 extension point 的結構設計消除 agent 的非法操作空間。

**Extension point 天然是收斂性任務 <!-- term:ConvergentTask -->。** 形狀 <!-- term:DataShape -->由結構定義，差異由需求定義，agent 的工作是填入交集。為收斂性任務 <!-- term:ConvergentTask -->選擇受限結構不是限制，是對齊。

**三種 agent 失敗模式可被結構約束 <!-- term:StructuralConstraint -->緩解：** 術語漂移 <!-- term:TerminologyDrift -->——受限結構減少需要命名的自由度；引用完整性 <!-- term:ReferentialIntegrity -->——集中化減少散落引用的數量；語意預設偏差 <!-- term:SemanticDefaultBias -->——固定結構的表條目沒有空間容納 happy path 假設。

**Agent safety 是 extension point 的設計維度。** 與型別安全、擴充成本並列。當 AI 協作成為常態，結構約束 <!-- term:StructuralConstraint -->不只服務於人類的可維護性，也服務於 agent 的正確性。