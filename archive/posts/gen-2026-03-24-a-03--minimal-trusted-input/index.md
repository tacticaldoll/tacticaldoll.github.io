+++
title = "最小可信輸入：LLM 驅動分析的證據收斂法"
date = "2026-03-24T23:30:03+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "提出在 legacy 程式碼考古中應用最小可信輸入原則，分析時效性、完整性與精確性衰減之風險，並利用史學的「源泉批判」與最佳證據規則實現證據收斂。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "AI 代理人", # term:AiAgent
    "最小可信輸入", # term:MinimalTrustedInput
    "時效性衰減", # term:TemporalDecay
    "完整性衰減", # term:CompletenessDecay
    "精確性衰減", # term:PrecisionDecay
    "最大化信噪比", # term:MaximizeSignalToNoiseRatio
    "最佳證據規則", # term:BestEvidenceRule
  ]
series = ["人機知識協作：無狀態代理人的因果鏈保存與治理挑戰"]
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

專案裡有一個精心維護的知識庫，記錄了架構概覽、路由映射、模組依賴關係。當需要 LLM 分析 legacy code 時，直覺的做法是把知識庫作為輸入 — 省去重新探索的時間，讓 LLM「站在前人的肩膀上」。

但在一次 legacy code 考古 skill 的設計過程中，使用者提出了一個根本性的質疑：「是否不使用這些知識庫文件？因不確定輸入來源是否遭受污染。」

這個問題看似保守，實則指向一個重要的方法論問題：**LLM 的 attention mechanism 無法區分可靠來源和不可靠來源。** 所有 token 在 attention 計算中一視同仁。如果一份過時的知識庫文件和一份正確的原始碼同時存在於 attention window 裡，LLM 沒有內建的機制來偏好後者。

這篇文章從這個觀察出發，論證「**最小可信輸入**（Minimal Trusted Input） <!-- term:MinimalTrustedInput -->」原則 — 為什麼 LLM 驅動的分析應該收斂到最小的、可驗證的輸入集合。

> [!IMPORTANT]
> **最小可信輸入** <!-- term:MinimalTrustedInput --> (Minimal Trusted Input): AI 驅動分析中，將輸入上下文收斂至最小且可直接驗證的資訊集合，以最大化信噪比並防止過時文件引入幻覺。 <!-- anchor:MinimalTrustedInput -->


## 分析

### 證據的距離衰減

不同來源的可信度不同。可以用「離 ground truth 的距離」來衡量：

| 距離 | 定義 | 範例 | 可信度 |
|------|------|------|--------|
| 0 | 事物本身 | Source code（`.c` / `.h`） | 最高 — 它就是 ground truth |
| 1 | 事物的直接衍生物 | Compiler 的 AST dump、`objdump` 輸出 | 高 — 機械式轉換，無人為判斷 |
| 2 | 人對事物的整理 | 知識庫文件、架構文件 | 中 — 受限於整理者的理解和時效性 |
| 3 | 人對整理的引用 | 會議紀錄引用知識庫、報告引用報告 | 低 — 二次傳遞，失真累積 |

每多一層距離，可信度指數衰減。這不是因為整理者不認真，而是因為：
- **時效性衰減**（Temporal Decay） <!-- term:TemporalDecay --> — code 改了但文件沒更新
- **完整性衰減**（Completeness Decay） <!-- term:CompletenessDecay --> — 只記錄了「值得記錄」的部分，遺漏了看似不重要但實際關鍵的細節
- **精確性衰減**（Precision Decay） <!-- term:PrecisionDecay --> — 自然語言描述不可避免地簡化了 code 的精確行為

> [!IMPORTANT]
> **時效性衰減** <!-- term:TemporalDecay --> (Temporal Decay): 資訊隨時間推移與系統演進，而導致內容與系統現狀產生不一致或過時的退化現象。 <!-- anchor:TemporalDecay -->
> **完整性衰減** <!-- term:CompletenessDecay --> (Completeness Decay): 人為整理文件時僅記錄當前認為重要的部分，進而遺漏其他看似無關但實則關鍵之技術細節的流失現象。 <!-- anchor:CompletenessDecay -->
> **精確性衰減** <!-- term:PrecisionDecay --> (Precision Decay): 使用自然語言對精確的程式碼行為進行摘要與轉譯時，無可避免地簡化並流失其精確語意與邊界條件的退化現象。 <!-- anchor:PrecisionDecay -->


### 為什麼 LLM 特別需要這個原則

人類分析師面對多個來源時，有能力主動質疑可信度：「這份文件是什麼時候寫的？誰寫的？跟 code 核對過嗎？」LLM 則不同 — attention mechanism 對 window 裡所有 token 一視同仁。

如果一份知識庫文件說「某個操作接受 `path` 參數」，而原始碼顯示它接受 `target` + `name` 兩個參數，LLM 的 attention 會同時考慮兩個說法。結果可能是一個混合了兩者的不精確輸出 — 不完全錯，但也不完全對。

用訊號處理的術語：每增加一個不完全可靠的輸入來源，等於在訊號裡混入噪聲。收斂到最小可信輸入 <!-- term:MinimalTrustedInput --> = **最大化信噪比**（Maximize Signal-To-Noise Ratio） <!-- term:MaximizeSignalToNoiseRatio -->。

> [!IMPORTANT]
> **最大化信噪比** <!-- term:MaximizeSignalToNoiseRatio --> (Maximize Signal-To-Noise Ratio): 藉由排除不可靠、過時或冗餘的輸入，最大化輸入上下文中 ground truth 比例以提高 AI 分析推論精確度的實踐。 <!-- anchor:MaximizeSignalToNoiseRatio -->


### 收斂的實踐：層層剝離

在實際設計中，最小可信輸入 <!-- term:MinimalTrustedInput -->不是一次性決策，而是逐步收斂的過程。以 legacy code 考古 skill 的演化為例：

第一輪，所有可用的文件都在可信集合裡 — source code、知識庫文件、參考文件。使用者質疑知識庫文件的可靠性後，第二輪移除了知識庫目錄。但參考文件（功能目錄、routing 映射表）看起來仍然有用，暫時保留。

進一步審視後發現：routing 映射表本質上是某個 dispatcher 原始碼裡 `strcmp(func, "...")` 分支的**人工摘要**（Human Summary） <!-- term:HumanSummary -->。既然可以直接 grep 原始碼得到精確結果，為什麼要用一份可能過時的摘要？第三輪移除了所有非 code 文件。

> [!IMPORTANT]
> **人工摘要** <!-- term:HumanSummary --> (Human Summary): 人類工程師在封裝程式碼時，主動隱去具體實作細節，僅保留命名、介面與結構的抽象過程 <!-- anchor:HumanSummary -->


最後一步最微妙：排除清單本身（「不讀 A、不讀 B、不讀 C」）把被排除的路徑名注入了 attention space，造成了另一種形式的干擾。第四輪改為**正面描述**（Positive Description） <!-- term:PositiveDescription -->：「只讀 `src/*.c` 和 `include/*.h`」。

> [!IMPORTANT]
> **正面描述** <!-- term:PositiveDescription --> (Positive Description): 在引導 AI 時採用正面列舉允許集合的描述方式，避免使用排除清單將被排除項目的 Token 意外引入注意力空間。 <!-- anchor:PositiveDescription -->


| 迭代 | 可信集合 | 收斂觸發 |
|------|---------|---------|
| 0 | `.c` + `.h` + 知識庫 + 參考文件 | 初始狀態 |
| 1 | `.c` + `.h` + 參考文件 | 知識庫可能過時 |
| 2 | `.c` + `.h` | 參考文件也是 secondary source |
| 3 | `.c` + `.h`（正面描述 <!-- term:PositiveDescription -->） | 排除清單注入碰撞詞 |

收斂的停止條件是：**再移除一個來源會導致分析無法完成。** Source code 不能移除 — 沒有它就無法考古。使用者的指定（function name）不能移除 — 沒有它就不知道考古什麼。其他一切都是可選的，而可選的都應該被質疑。

### 類比框架

這個原則在多個領域有精確對應。

**史學的**源泉批判**（Source Criticism） <!-- term:SourceCriticism -->。** 19 世紀德國歷史學派建立的方法論，要求區分 primary source（事件本身的直接產物）、secondary source（基於 primary 的分析）、tertiary source（彙編多個 secondary）。嚴謹的歷史研究必須回到 primary source — 不把 secondary source 當作事實，而是當作「某人對事實的解讀」。

> [!IMPORTANT]
> **源泉批判** <!-- term:SourceCriticism --> (Source Criticism): 史學研究中評估史料來源可信度、真實性與離歷史事件核心距離的方法論，在 AI 協作中用以評估輸入資訊的信任等級。 <!-- anchor:SourceCriticism -->


**法律的**最佳證據規則**（Best Evidence Rule） <!-- term:BestEvidenceRule -->。** 英美法系的 Federal Rules of Evidence Rule 1002：要證明文件的內容，必須出示原件。副本或摘要只在原件不可得時才被接受。知識庫文件是原始碼的「摘要」。原件可得（source code 就在 repo 裡），所以不應該用摘要。

> [!IMPORTANT]
> **最佳證據規則** <!-- term:BestEvidenceRule --> (Best Evidence Rule): 法律學上要求出示原始文件以證明內容的證據法規則，在此比喻 AI 分析時應以原始程式碼而非人工摘要或二次文件作為主要依據。 <!-- anchor:BestEvidenceRule -->


**零信任架構**（Zero Trust Architecture） <!-- term:ZeroTrustArchitecture -->。 網路安全的 Zero Trust 原則：不因為某個來源在「內網」就信任它，每次存取都需要驗證。LLM 分析的 Zero Trust 版本：不因為某個文件在「專案 repo 裡」就信任它 — 可信度取決於離 ground truth 的距離，不取決於存放位置。

> [!IMPORTANT]
> **零信任架構** <!-- term:ZeroTrustArchitecture --> (Zero Trust Architecture): 網路安全中不預設任何信任邊界的安全模型，在 AI 協作中指不因檔案存在於專案目錄中即盲目信任，每次存取皆需驗證其真實性。 <!-- anchor:ZeroTrustArchitecture -->


## 結論

### 正面描述 vs 排除清單

「不要想大象」之後你一定會想到大象。Wegner（1987）的 Ironic Process Theory 解釋了這個現象 — 壓制一個想法需要先監控它是否出現，而監控本身就保持了想法的活躍。

在 LLM 的 prompt 裡，這個效應更加直接：排除清單把被排除的對象作為 token 注入了 attention space。「不要讀知識庫目錄」這句話裡的目錄路徑 token 會吸引 attention，效果與「請讀知識庫目錄」裡的 token 在 attention 計算層面沒有本質差異。

因此，最小可信輸入 <!-- term:MinimalTrustedInput -->的描述方式也必須收斂：用正面列舉取代排除清單。一條「只讀 X」比 N 條「不讀 A、B、C...」更乾淨 — 更短，且不注入任何干擾 token。

### 便利性 vs 精確性的取捨

最小可信輸入 <!-- term:MinimalTrustedInput -->有成本。直接 grep 原始碼比讀一份整理好的映射表慢。Recon agent 讀完整 function 比讀一份摘要消耗更多 token。

但這個成本是值得的，因為**從錯誤的輸入得到的快速結果比沒有結果更糟**。一份基於過時知識庫的考古報告會包含看起來正確但實際錯誤的行為描述，而使用者很難發現這些錯誤 — 因為它們被正確的結果包圍著。

### 泛化的方法

這個原則不限於 code archaeology，適用於任何 LLM 驅動的分析任務。收斂的通用步驟：

1. 列出所有可能的輸入來源
2. 對每個來源問：「如果它是錯的，我能從其他來源驗證嗎？」
3. 如果能驗證 → 移除它，直接用可驗證的來源
4. 重複直到集合不能再縮小
5. 用正面描述 <!-- term:PositiveDescription -->寫出可信集合

## 結論

LLM 的 attention mechanism 不區分可靠來源和不可靠來源。這意味著每一個不完全可靠的輸入都會降低整體輸出的信噪比 — 而且這種降低是無聲的，不會報錯，只會默默偏移結果。

**最小可信輸入 <!-- term:MinimalTrustedInput -->原則**：LLM 驅動的分析應該收斂到最小的、可直接驗證的輸入集合。能從 primary source 得到的資訊，就不從 secondary source 取得。

**正面描述 <!-- term:PositiveDescription -->原則**：用「只允許 X」描述可信集合，不用「排除 A, B, C」。排除清單本身是一種輸入污染。

**收斂停止條件**（Convergence Stopping Condition） <!-- term:ConvergenceStoppingCondition -->：再移除一個來源會導致分析無法完成。這是收斂的下界 — 不是「最少到還能用」，而是「少到不能再少」。

> [!IMPORTANT]
> **收斂停止條件** <!-- term:ConvergenceStoppingCondition --> (Convergence Stopping Condition): 在逐步收斂輸入來源的過程中，判定無法再移除任何輸入來源否則分析即無法完成的下界閾值。 <!-- anchor:ConvergenceStoppingCondition -->
