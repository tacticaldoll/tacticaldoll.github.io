+++
title = "局部完備性：Agent 開發的約束集與治理防線"
date = "2026-03-11T22:30:03+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "Agent 是接龍狀態機，代碼整潔度的多個面向會製造因果斷裂，而 DRY + 集中知識庫的疊加可以將風險升級為系統性崩潰。在這些前提下，問題變成：如何在不重寫既有代碼的前提下回應這些風險？"
tags = [
    "分析論述", # term:AnalyticalEssay
    "AI 代理人", # term:AiAgent
    "品質閘門", # term:QualityGate
    "局部完備性", # term:LocalCompleteness
    "知識路由規則", # term:KnowledgeRoutingRule
    "設置人為閘門", # term:HumanGate
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

Agent 是**接龍狀態機**（Sequence Completion Machine） <!-- term:SequenceCompletionMachine -->，代碼整潔度的多個面向會製造**因果斷裂**（Causal Breakpoint） <!-- term:CausalBreakpoint -->，而 DRY + 集中知識庫的疊加可以將風險升級為系統性崩潰。在這些前提下，問題變成：如何在不重寫既有代碼的前提下回應這些風險？

> [!IMPORTANT]
> **接龍狀態機** <!-- term:SequenceCompletionMachine --> (Sequence Completion Machine): 基於條件機率生成下一個 Token 的狀態機本質，其輸出取決於前文 Token 的統計分佈而非邏輯推理 <!-- anchor:SequenceCompletionMachine -->
> **因果斷裂** <!-- term:CausalBreakpoint --> (Causal Breakpoint): AI Agent 運算中由於上下文視窗或靜態程式碼中關鍵因果資訊缺失，導致無法正確推演系統狀態的現象 <!-- anchor:CausalBreakpoint -->


回應分兩個層面。代碼層面需要一組附加約束，確保 agent 在單個 session 內能做出正確決策。治理層面需要額外防線，防止跨 session 的累積污染侵蝕 spec-driven 框架的根基。

本文先盤點現有消減手段的能力與邊界，再提出代碼層的約束集和治理層的防護機制。

## 分析：消減手段的能力與邊界

### 型別標注

型別標注對 agent 的真正價值不是正確性保證，而是**減少跳轉**。有型別標注的函數，agent 不需要追蹤到實作就能知道輸入/輸出的**形狀**（Data Shape） <!-- term:DataShape -->。每少一次跳轉，推斷鏈斷裂的機率就降低一次。

> [!IMPORTANT]
> **形狀** <!-- term:DataShape --> (Data Shape): 資料結構或物件所包含的屬性與型別定義，通常由型別系統來描述 <!-- anchor:DataShape -->


但型別有明確的消減邊界。以下按「能否消減」分類：

| 風險類型 | 型別能否消減 | 原因 |
|---|---|---|
| `*args, **kwargs` 透傳 | **是** | `TypedDict` / `Protocol` 讓參數形狀 <!-- term:DataShape -->顯式化 |
| Decorator 改變簽名 | **是** | `ParamSpec` + `Concatenate` 保留原始簽名 |
| Mixin MRO 衝突 | **部分** | `Protocol` 定義預期介面，但 MRO 解析順序仍是 runtime 行為 |
| `@property` 副作用 | **否** | 型別只描述回傳值的形狀 <!-- term:DataShape -->，不描述「讀取時是否觸發 I/O」 |
| `__getattr__` 動態屬性 | **否** | 動態生成的部分仍是盲區 |
| Metaclass | **否** | 型別描述實例的形狀 <!-- term:DataShape -->，不描述「類別建構過程被如何改寫」 |
| Monkey Patching | **否** | 型別是宣告時的契約，runtime 替換後型別檢查器不會重新驗證 |

型別回答「這個值長什麼形狀 <!-- term:DataShape -->」，不回答「這個值怎麼來的」和「存取它會發生什麼」。這是它的根本邊界。

### Code as doc（好命名）

好命名降低了「讀懂一個函數」的風險，但沒有降低「理解一個決策」的風險。具體而言，code as doc 的盲區是：

| 缺口 | 說明 |
|---|---|
| **Why-not** | 代碼中不存在的路徑，agent 無法區分「故意省略」和「遺漏」 |
| **邊界條件的意圖** | `if (x > 0)` —— 0 是被排除的合法值，還是不可能出現的值？代碼表達不出來 |
| **跨文件因果** | A 文件的寫法是因為 B 文件的約束，代碼本身無法表達這個依賴方向 |

無註解風格的假設是「命名足以承載因果」。對人類通常成立，因為人類會用直覺填補命名覆蓋不到的部分。對 agent，命名只能承載 **what**，承載不了 **why-not** 和**跨模組因果**（Cross-Module Causality） <!-- term:CrossModuleCausality -->。補救方式不是回到大量註解，而是在**決策點**留下最小必要的 why/why-not 標注。

> [!IMPORTANT]
> **跨模組因果** <!-- term:CrossModuleCausality --> (Cross-Module Causality): 一個模組的實作細節受限於另一個模組的隱含規則，且在靜態程式碼中不直接呈現的因果依賴 <!-- anchor:CrossModuleCausality -->


### 消減手段的共同邊界

型別、命名、意圖測試——這些手段回答 **what** 和 **how**，但不回答 **why-not** 和跨模組因果 <!-- term:CrossModuleCausality -->。對 agent 而言，後者才是主要錯誤來源。

這個共同邊界指向一個核心結論：不存在單一手段能完整恢復**因果連續性**（Causal Continuity） <!-- term:CausalContinuity -->。需要的是**多手段組合**，每種手段覆蓋不同的因果維度：

> [!IMPORTANT]
> **因果連續性** <!-- term:CausalContinuity --> (Causal Continuity): 系統中某項決策或邏輯的完整依據在 Token 序列中完全可見且未被中斷的狀態 <!-- anchor:CausalContinuity -->


| 手段 | 覆蓋維度 |
|---|---|
| 型別標注 | 形狀 <!-- term:DataShape --> |
| 好命名 | 意圖（what，部分 why） |
| 意圖測試 | **預期行為**（Expected Behavior） <!-- term:ExpectedBehavior --> |
| why-not 註解 | **排除邏輯**（Why-Not Comment） <!-- term:WhyNotComment --> |
| 綁定清單 | **執行期繫結**（Runtime Binding） <!-- term:RuntimeBinding --> |
| co-located README | 跨模組因果 <!-- term:CrossModuleCausality --> |

> [!IMPORTANT]
> **預期行為** <!-- term:ExpectedBehavior --> (Expected Behavior): 系統或模組在特定輸入或情境下被要求達到的正確輸出與副作用狀態 <!-- anchor:ExpectedBehavior -->
> **排除邏輯** <!-- term:WhyNotComment --> (Why-Not Comment): 在程式碼中記錄「為何不採用某種方案」的說明，用以補全 Agent 無法從程式碼推導的因果鏈 <!-- anchor:WhyNotComment -->
> **執行期繫結** <!-- term:RuntimeBinding --> (Runtime Binding): 在程式執行期才動態確立的物件或事件訂閱關係，是靜態分析的常見盲區 <!-- anchor:RuntimeBinding -->


## 分析：代碼層約束集

### 局部完備性原則

Agent 開發不需要全新的範式，而是在現有範式上施加一組**附加約束**——**附加濾鏡**（Supplemental Filter） <!-- term:SupplementalFilter -->。每個設計決策過傳統 review 之後，再過一次「agent 能否在局部完備地理解這個決策」的檢查。

> [!IMPORTANT]
> **附加濾鏡** <!-- term:SupplementalFilter --> (Supplemental Filter): 在傳統程式碼審查標準之外，針對 Agent 特性額外施加的局部完備性檢查規則 <!-- anchor:SupplementalFilter -->


核心原則是**局部完備性**（Local Completeness） <!-- term:LocalCompleteness -->：agent 在任何一個檔案、任何一個函數內，不需要跳轉到其他位置就能做出正確決策。

> [!IMPORTANT]
> **局部完備性** <!-- term:LocalCompleteness --> (Local Completeness): Agent 在單一檔案或函式內，無須跳轉或探索其他上下文即能做出正確修改決策的程式碼設計原則 <!-- anchor:LocalCompleteness -->


以下約束表對照傳統最佳實踐與 agent 約束：

| 維度 | 傳統最佳實踐 | Agent 約束 |
|---|---|---|
| DRY | 消除所有重複 | 允許**意圖不同**的結構重複存在；只消除意圖相同的重複 |
| 抽象層數 | 按職責分層 | 最多 2 次跳轉可達實作；超過則在中間層加型別標注或意圖註解 |
| 知識庫 | 集中管理 | 只存代碼推導不出的知識（why-not、跨模組因果 <!-- term:CrossModuleCausality -->）；可從代碼推導的**禁止**寫入 |
| **約束性規格**（Spec） <!-- term:Spec --> 權威 | **架構層**（Architecture） <!-- term:Architecture --> 代碼贏 | 架構層 <!-- term:Architecture --> 更新需要**溯源標記**（Provenance Marker） <!-- term:ProvenanceMarker -->——記錄是哪次變更、基於什麼證據更新 |
| 設計模式 | 按問題選模式 | 優先選靜態可追蹤模式；runtime 綁定的模式必須附帶**綁定清單**（誰綁誰、在哪綁） |
| 命名 | 自解釋 | 自解釋 + **作用域標記**——函數名要表達影響範圍（`updateLocalCache` vs `update`） |
| 註解 | 盡量少 | 決策點必須有 why/why-not；其餘仍然少 |

> [!IMPORTANT]
> **約束性規格** <!-- term:Spec --> (Spec): 以結構化或機器可讀格式定義的系統或 API 合約規範。 <!-- anchor:Spec -->
> **架構層** <!-- term:Architecture --> (Architecture): 規格文件中用以客觀記錄系統「實際在做什麼」的事實陳述層。 <!-- anchor:Architecture -->
> **溯源標記** <!-- term:ProvenanceMarker --> (Provenance Marker): 為多世代或多模型協作的產出，記錄其原始生成源頭與當前精煉環境的遙測後設資料標籤。 <!-- anchor:ProvenanceMarker -->


### 既有專案的訊號補回方案

對於已經高度封裝的既有專案，重寫不可行。補救原則是**不拆封裝，補訊號**——在現有封裝上補回 agent 需要但被封裝刪除的因果訊號。

依爆炸半徑排序補回優先順序，最高風險的先處理：

| 優先順序 | 目標 | 補回手段 | 風險原因 |
|---|---|---|---|
| 1 | DRY 共用路徑的函數 | `@context` 標記 + why-not 註解 | 改錯影響全域 |
| 2 | Runtime 綁定點 | 綁定清單 | Agent 完全看不到 |
| 3 | 非同步邊界 | 中間狀態變更註解 | 邏輯死區 |
| 4 | 模組入口 | co-located README | 跨模組因果 <!-- term:CrossModuleCausality --> |
| 5 | 其餘封裝 | 型別標注 | 漸進補充 |

同樣重要的是不做什麼：不拆封裝（那是重寫，不是補救）、不寫進集中知識庫（訊號必須與代碼同址，否則又回到過時風險）、不補代碼能推導出的（只補 agent 推導不出的）。

### 約束集的覆蓋邊界

代碼層約束能防止因果斷裂 <!-- term:CausalBreakpoint -->在單個 session 內發生，但管不到跨 session 的累積效應。具體來說，以下風險超出代碼層的覆蓋範圍：

- **約束性規格 <!-- term:Spec --> 條目的污染回寫**——agent 在 session A 中基於過時知識做了錯誤修改，session B 的 reconciliation 將錯誤固化為 架構層 <!-- term:Architecture -->
- **知識庫的維護一致性**——跨 session 的過時檢測沒有機制驅動
- **架構層 <!-- term:Architecture --> → Requirement 的提升決策**——權威升級是不可逆的，代碼層約束無法阻止

這些風險需要治理層的回應。

## 反思：治理層防護

代碼層約束集處理了 agent 在單個 session 內的因果斷裂 <!-- term:CausalBreakpoint -->問題。但跨 session 的累積污染——特別是 spec-driven 框架中的污染固化——需要治理機制的額外防線。

### Architecture 更新溯源標記

每次 架構層 <!-- term:Architecture --> 層的更新必須附帶溯源標記 <!-- term:ProvenanceMarker -->。溯源標記 <!-- term:ProvenanceMarker -->回答三個問題：是哪次代碼變更觸發了這次更新？基於什麼證據判斷代碼行為已改變？更新前的 架構層 <!-- term:Architecture --> 描述是什麼？

沒有溯源的 架構層 <!-- term:Architecture --> 更新無法被後續 session 驗證。Agent 看到一條 架構層 <!-- term:Architecture --> 條目時，無法區分「這是經過驗證的觀察」還是「這是前一個 session 的錯誤回寫」。溯源標記 <!-- term:ProvenanceMarker -->讓任何 session 都能回溯到變更源頭，判斷依據是否仍然有效。

對比有無溯源標記 <!-- term:ProvenanceMarker -->的效果：

```markdown
# 無溯源（agent 無法驗證）
### Architecture: Cache API 回傳結構
Cache API 回傳 `{ items: [...], total: N }`

# 有溯源（agent 可回溯驗證）
### Architecture: Cache API 回傳結構
Cache API 回傳 `{ items: [...], total: N }`
<!-- provenance: commit abc123, verified against service/cacheAPI.cpp:L45-L60, 2026-03-10 -->
```

### 知識路由污染防護

**知識路由規則**（Knowledge Routing Rule） <!-- term:KnowledgeRoutingRule -->需要增加一個顯式的污染防護約束：**只允許寫入代碼推導不出的知識**。可從代碼推導的知識禁止寫入知識庫。

> [!IMPORTANT]
> **知識路由規則** <!-- term:KnowledgeRoutingRule --> (Knowledge Routing Rule): 定義何種知識應與程式碼同址存放，何種知識可寫入集中庫，以避免過時資訊引發污染的路由策略 <!-- anchor:KnowledgeRoutingRule -->


這個約束的目的不僅是避免冗餘。更重要的是避免「代碼改了但知識庫沒同步」的過時風險。知識庫中的每一份可從代碼推導的條目，都是一個潛在的污染入口——代碼演進後，這些條目變成「錯誤存在」型的因果斷裂 <!-- term:CausalBreakpoint -->源，而且因為它們存在於「權威」的知識庫中，agent 會優先採信。

適合寫入知識庫的知識類型：

| 類型 | 範例 | 為什麼代碼推導不出 |
|---|---|---|
| Why-not 決策 | 「不用 WebSocket 是因為防火牆限制」 | 代碼中看不到被排除的方案 |
| 跨模組因果 <!-- term:CrossModuleCausality --> | 「A 模組的格式是因為 B 模組的解析器要求」 | 依賴方向在代碼中不可見 |
| 歷史約束 | 「保留舊 API 是因為第三方整合尚未遷移」 | 時間維度的決策在代碼中不表達 |

### RFC 2119 關鍵字的不對稱效應

RFC 2119 定義了 MUST、SHALL、SHOULD、MAY 等關鍵字的語意強度。在人類團隊中，這些關鍵字是溝通工具——即使寫了 MUST，資深工程師仍然可以憑判斷力質疑「這條 spec 是否過時」。但對 agent 而言，關鍵字是不可覆寫的指令強度梯度：

| 關鍵字 | 人類開發者 | Agent |
|--------|-----------|-------|
| MUST / SHALL | 遵守，但可憑經驗質疑 | **絕對服從**——無質疑能力，遇到矛盾時選擇服從 spec |
| SHOULD | 傾向遵守，了解例外存在 | **高權重服從**——除非 context window 中有明確的例外條件 token |
| MAY | 視情況選擇 | **低權重忽略**——除非上下文明確要求，否則傾向跳過 |

這個不對稱有兩個後果。第一，MUST 對 agent 的約束力遠超對人類——人類有「最終否決權」（直覺判斷 spec 可能過時），agent 沒有。第二，MAY 對 agent 的約束力遠低於對人類——人類會考慮 MAY 標記的選項是否適用，agent 在缺乏明確上下文時直接忽略。

這個梯度差異直接影響 spec 撰寫策略：

| 場景 | 錯誤選擇 | 正確選擇 | 原因 |
|------|---------|---------|------|
| 觀察性行為 | MUST | 架構層 <!-- term:Architecture --> 層描述，不用關鍵字 | 觀察不是契約，用 MUST 固化會阻止演進 |
| 有例外的規則 | MUST | SHOULD + 明確列出例外條件 | Agent 無法自行判斷例外，MUST 讓它在例外場景中強制執行錯誤行為 |
| 可選功能 | 不標記 | MAY + 觸發條件說明 | 不標記 = agent 不知道這個選項存在；MAY + 條件 = agent 在適當時機考慮 |
| 核心不變式 | SHOULD | MUST | 核心不變式需要最高約束力，SHOULD 給了 agent 不該有的迴旋空間 |

對比正確與錯誤的關鍵字使用：

```markdown
# 錯誤：觀察性行為用 MUST（一旦代碼演進，agent 會強制維護過時行為）
### Requirement: Cache TTL
Cache entries MUST expire after 300 seconds.

# 正確：觀察歸 Architecture，契約用 SHOULD 保留迴旋
### Architecture: Cache TTL
Cache entries currently expire after 300 seconds.
<!-- provenance: verified against cacheManager.cpp:L120, 2026-03-10 -->

### Requirement: Cache TTL
Cache entries SHOULD expire within a configurable TTL. The default TTL is defined in Architecture.
```

換言之，**關鍵字選擇本身就是一道污染防火牆**。SHOULD 而非 MUST 為 agent 保留了矛盾情境下的迴旋空間；架構層 <!-- term:Architecture --> 層的無關鍵字描述防止行為觀察被意外固化為契約。

### Requirement 提升閘門

架構層 <!-- term:Architecture --> → Requirement 的提升是污染鏈中的不可逆轉折點。一旦被污染的行為獲得 RFC 2119 權威，前述的不對稱效應就會啟動——agent 絕對服從，將任何修復嘗試打回為「spec violation」。

因此這個提升必須**設置人為閘門**（Human Gate） <!-- term:HumanGate -->——不能由 agent 自動執行，不能在 reconciliation 過程中隱式發生。閘門的檢查項：

> [!IMPORTANT]
> **設置人為閘門** <!-- term:HumanGate --> (Human Gate): 在 Architecture 提升為 Requirement 或執行關鍵變更時，必須由人類工程師進行審查介入的品質卡點 <!-- anchor:HumanGate -->


1. **多 session 交叉驗證**——觀察是否在至少 2 個獨立 session 中被確認？單一 session 的觀察可能基於污染後的代碼
2. **獨立代碼證據**——是否有直接的代碼證據（測試、型別簽名）支撐這個行為，而非僅依賴 reconciliation 的自動判斷？
3. **Requirement 一致性**——新的 Requirement 是否與現有 規範性需求 邏輯一致？矛盾是污染的強訊號
4. **關鍵字強度審查**——提升時選用的 RFC 2119 關鍵字是否匹配行為的確定性？有例外的規則不應使用 MUST

### 治理工具自身的防護

治理工具（reconciliation、precipitate、crystallize）本身也是 agent 操作的工具。它們在處理涉及架構決策、範式衝突或**語意邊界**（Semantic Boundary） <!-- term:SemanticBoundary -->的內容時，需要額外的品質防護。

> [!IMPORTANT]
> **語意邊界** <!-- term:SemanticBoundary --> (Semantic Boundary): 模組或類別在空間維度上定義其職責與封裝邊界的概念 <!-- anchor:SemanticBoundary -->


具體而言，**品質閘門**（Quality Gate） <!-- term:QualityGate -->需要包含一個檢查：涉及上述主題的產出，必須包含對比範例——incorrect/correct 或 before/after 的代碼或邏輯對比。這個要求的目的是防止抽象描述在多次傳遞後喪失區分力。抽象描述可以被任意解讀，但具體的代碼對比是不可模糊的——它固定了「正確」和「錯誤」的精確邊界。

> [!IMPORTANT]
> **品質閘門** <!-- term:QualityGate --> (Quality Gate): 控制產出品質的檢查點或審查機制 <!-- anchor:QualityGate -->


## 結論

Agent 開發不需要全新的範式。它需要在現有範式上施加一組附加約束——以局部完備性 <!-- term:LocalCompleteness -->為核心原則的濾鏡。代碼層約束確保 agent 在單個 session 內的因果連續性 <!-- term:CausalContinuity -->，治理層防護攔截跨 session 的累積污染。

兩層防線各有覆蓋範圍和邊界。代碼層管不到 spec 污染，治理層管不到單個函數內的因果斷裂 <!-- term:CausalBreakpoint -->。兩者不是替代關係，而是互補——缺任何一層，另一層的防護都會被繞過。