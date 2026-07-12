+++
title = "戳破 SDD 的集體幻覺與命名約束的物理邊界"
date = "2026-03-14T16:50:01+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "分析業界推行規格驅動開發 (SDD) 的常見迷思，確立命名必須被實作於編譯或驗證閘門 (Validation Gate) 的底層原則。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "AI 代理人", # term:AiAgent
    "規格驅動開發", # term:SpecDrivenDevelopment
    "技術債", # term:TechnicalDebt
    "API-First", # term:ApiFirst
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

在當代軟體工程的論述中，「**規格驅動開發**（Spec-Driven Development） <!-- term:SpecDrivenDevelopment -->」與「API 優先 (**API-First**（API-First） <!-- term:ApiFirst -->)」幾乎成了某種不容質疑的政治正確。無數的架構師與技術文章宣揚著：只要我們導入了標準化的結構定義檔案，只要我們在寫第一行程式碼之前先把綱要 (**結構合約**（Schema） <!-- term:Schema -->) 填好，跨團隊的整合痛苦就會煙消雲散，專案的**技術債**（Technical Debt） <!-- term:TechnicalDebt -->就會如同被聖光淨化般消失。

> [!IMPORTANT]
> **規格驅動開發** <!-- term:SpecDrivenDevelopment --> (Spec-Driven Development): 以規格文件為基準約束程式碼行為，確保實作與規格始終對齊的開發方法。 <!-- anchor:SpecDrivenDevelopment -->
> **API-First** <!-- term:ApiFirst --> (API-First): 在編寫實作程式碼之前，優先設計並宣告應用程式介面規格的開發理念。 <!-- anchor:ApiFirst -->
> **結構合約** <!-- term:Schema --> (Schema): 定義資料欄位、型別與排版限制的強型別規格定義，用於強制約束模型產出的格式。 <!-- anchor:Schema -->
> **技術債** <!-- term:TechnicalDebt --> (Technical Debt): 程式碼中為求快速交付而妥協、待重構與修復的設計或品質缺陷。 <!-- anchor:TechnicalDebt -->


這是一場極度昂貴的集體**幻覺**（Hallucination） <!-- term:Hallucination -->。本文將毫不留情地揭露這場幻覺 <!-- term:Hallucination -->背後的三大迷思，並重新確立在 AI **代理人**（AI Agent） <!-- term:AiAgent --> 時代，真正能讓系統存活下來的第一底層邏輯：「**命名即文件**（Naming As Documentation） <!-- term:NamingAsDocumentation -->」的物理意義。論述將不再侷限於單一專案的特定情境，而是將其提升至跨專案皆適用的工程治理哲學。

> [!IMPORTANT]
> **幻覺** <!-- term:Hallucination --> (Hallucination): 大型語言模型在面對不實或矛盾資訊時，生成不符合客觀現實或超出脈絡之回應的錯誤現象。 <!-- anchor:Hallucination -->
> **AI 代理人** <!-- term:AiAgent --> (AI Agent): 具備自主理解、推論與程式碼生成能力，能在給定規則下執行特定任務的 AI 協作者。 <!-- anchor:AiAgent -->
> **命名即文件** <!-- term:NamingAsDocumentation --> (Naming As Documentation): 將業務領域的核心詞彙與定義直接融入變數或屬性命名，使其具備物理約束與說明價值的工程哲學。 <!-- anchor:NamingAsDocumentation -->


## 發現

### 迷思一：文件驅動的「借屍還魂」

業界推行 SDD 最常見的死法，是把過時的「**文件驅動**（Document-Driven） <!-- term:DocumentDriven -->」思維披上了標準化綱要的外衣。

> [!IMPORTANT]
> **文件驅動** <!-- term:DocumentDriven --> (Document-Driven): 高度仰賴人工撰寫與維護的文字規格，常因缺乏編譯與執行期物理邊界而失效的傳統開發思維。 <!-- anchor:DocumentDriven -->


過去，我們把系統規格寫在共用的知識庫文件裡。後來我們發現沒人會去更新它們，導致嚴重的「**權威文件漂移**（Authoritative Document Drift） <!-- term:AuthoritativeDocumentDrift -->」。為了解決這個問題，業界發明了結構化的機器可讀檔案格式。但多數團隊的做法是什麼？他們派了一群工程師，把原有的文字說明，一行一行地翻譯成了結構化的 YAML 檔案，然後把它丟在**資源庫**（Repository） <!-- term:Repository --> 的某個資料夾裡，宣佈：「看，我們現在是 規格驅動 了！」

> [!IMPORTANT]
> **權威文件漂移** <!-- term:AuthoritativeDocumentDrift --> (Authoritative Document Drift): 文件規格未與實作系統同步更新，導致文件與系統真實行為逐漸脫節的退化現象。 <!-- anchor:AuthoritativeDocumentDrift -->
> **資源庫** <!-- term:Repository --> (Repository): 存放專案原始碼、版本歷史紀錄與配置文件的中心儲存庫。 <!-- anchor:Repository -->


這不叫規格驅動，這叫「高成本的官僚主義」。

如果這份結構化檔案沒有與程式碼的型別系統（Type System）進行強綁定；如果負責執行業務邏輯的基礎設施沒有在每一次資源請求的時候去核對這份 結構合約 <!-- term:Schema -->──那麼，你只是創造了一份維護成本比純文字高出十倍、且依然會隨時過期的廢紙。對 代理人 <!-- term:AiAgent --> 而言，這種缺少**執行時約束**（Runtime Constraints） <!-- term:RuntimeConstraints --> 的文件，更是引發幻覺 <!-- term:Hallucination -->的超級溫床。Agent 讀取了一份聲明著完美結構的文件，卻在實際操作時遭遇了截然不同的執行時現實。

> [!IMPORTANT]
> **執行時約束** <!-- term:RuntimeConstraints --> (Runtime Constraints): 在程式執行期間由系統強制執行並驗證的型別或邏輯邊界限制。 <!-- anchor:RuntimeConstraints -->


### 迷思二：將「期望」暴力覆蓋「現實」的傲慢

SDD 提倡者最喜歡畫的餅是：**約束性規格**（Spec） <!-- term:Spec --> 是系統的**單一事實來源**（Single Source of Truth） <!-- term:SingleSourceOfTruth -->。這句話在邏輯上沒錯，但在時間維度上是個災難。

> [!IMPORTANT]
> **約束性規格** <!-- term:Spec --> (Spec): 以結構化或機器可讀格式定義的系統或 API 合約規範。 <!-- anchor:Spec -->
> **單一事實來源** <!-- term:SingleSourceOfTruth --> (Single Source of Truth): 指在特定工作執行緒中唯一被視為絕對真實與合法的結構化資料來源，所有操作皆以其為單向基準。 <!-- anchor:SingleSourceOfTruth -->


在真實世界的遺留系統 中，架構充滿了歷史共業。同一個「核心實體標識符」，在前端子系統叫 `userName`，在金流子系統叫 `buyer_id`，在資料庫裡可能又是一個詭異的縮寫。當團隊試圖導入 SDD 時，最常犯的錯誤就是「**過早統一**（Premature Unification） <!-- term:PrematureUnification -->」。

> [!IMPORTANT]
> **過早統一** <!-- term:PrematureUnification --> (Premature Unification): 在對系統現狀與未來需求理解不足時，過早強行統一概念或命名所引發的系統癱瘓現象。 <!-- anchor:PrematureUnification -->


團隊在共通的綱要裡寫下一個完美的 `CustomerName`。他們以為只要宣告了這份 約束性規格 <!-- term:Spec --> 是 SSOT，現實就會自動向其對齊。結果是一觸即發的災難：掛載上去的靜態分析工具 (**檢查工具**（Linter） <!-- term:Linter -->) 開始瘋狂報錯，舊有系統全面癱瘓。工程師為了解決這個人為製造的危機，開始在各個轉接層寫滿了骯髒的映射邏輯與型別忽略標籤 (`@ts-ignore` 等)。

> [!IMPORTANT]
> **檢查工具** <!-- term:Linter --> (Linter): 在開發期或持續整合管線中，用以靜態掃描程式碼並揪出風格或語法錯誤的工具。 <!-- anchor:Linter -->


這是在治標不治本，用更深的程式碼債務去掩蓋框架上的治理無能。他們沒有意識到：把「**未來的期望**（What Should Be） <!-- term:WhatShouldBe -->」寫進代表「**當前系統契約**（System Contract） <!-- term:SystemContract -->」的文件裡，是架構腐化、引發**前瞻性漂移**（Forward-Looking Spec Drift） <!-- term:ForwardLookingSpecDrift --> 的第一步。

> [!IMPORTANT]
> **未來的期望** <!-- term:WhatShouldBe --> (What Should Be): 計畫在後續階段實作，但目前在系統中尚未真實落地的設計願景。 <!-- anchor:WhatShouldBe -->
> **當前系統契約** <!-- term:SystemContract --> (System Contract): 代表系統當前真實執行與支援之功能與資料結構的合約狀態。 <!-- anchor:SystemContract -->
> **前瞻性漂移** <!-- term:ForwardLookingSpecDrift --> (Forward-Looking Spec Drift): 由於把未來的期望當作當前實作寫入規格，所導致的規格與現實不一致現象。 <!-- anchor:ForwardLookingSpecDrift -->


### 迷思三：無牙老虎的悲哀與分析癱瘓

第三個迷思，是對於「權威」來源的誤解。很多團隊宣稱他們擁有一份「絕對權威」的 約束性規格 <!-- term:Spec -->，但當你問他們：「如果明天有人推了一個修改請求 時用肉眼看」。

這如同頒布了一部憲法，卻解散了警察局。

更糟的是，因為團隊被灌輸了「必須完全遵循 約束性規格 <!-- term:Spec --> 才能開發」的教條，在專案啟動初期，當需求還不明確的「**規格稀疏期**（Spec-Sparse Period） <!-- term:SpecSparsePeriod -->」，整個團隊會陷入嚴重的**分析癱瘓**（Analysis Paralysis） <!-- term:AnalysisParalysis -->。消費端不敢動工，因為介面端還沒把輸出的欄位敲定；介面端不敢接資料，因為後端說資料結構還在審查。專案為了等待一份「完美的 約束性規格 <!-- term:Spec -->」，硬生生地把所有的開發動能消耗殆盡。

> [!IMPORTANT]
> **規格稀疏期** <!-- term:SpecSparsePeriod --> (Spec-Sparse Period): 專案初期或規格導入早期，此時規格覆蓋率低，多數行為以程式碼為真相來源的過渡階段。 <!-- anchor:SpecSparsePeriod -->
> **分析癱瘓** <!-- term:AnalysisParalysis --> (Analysis Paralysis): 因過度追求完美規格或陷入無止盡討論，導致開發動能喪失、無法實際推進的停滯狀態。 <!-- anchor:AnalysisParalysis -->


## 實務對比

以下具體展示「命名約束」在缺乏與具備物理邊界時的架構差異。

**[錯誤/稀釋] 僅具備語意，缺乏驗證邊界的綱要**

此範例展示了被誤當作 SDD 實作，實質上僅為一紙空文的結構描述。

```yaml
# 缺乏強制力的 API-First 實作
schema:
  type: object
  description: "使用者名稱。後端尚未確認命名長度與格式要求。"
  properties:
    userName:
      type: string
```

分析：此綱要無法阻擋任何違規的請求進入系統，充其量僅是一份結構化的註解。工程師與 AI 代理人 <!-- term:AiAgent -->可隨意修改程式碼而不受約束，導致系統內部充斥 `userName`、`user_name`、`UserName` 等不受控的同義詞與潛在錯誤。

**[正確/高解析度] 確立「命名即編譯邊界」的強制性綱要**

此範例展示了真正的命名約束應如何被實作於編譯或驗證閘門 (Validation Gate) 中。

```yaml
# 具備執行與編譯期物理防護的綱要
schema:
  type: object
  description: "使用者核心實體標識符。任何對此屬性的操作皆需經過 Linter 與 Runtime 雙重檢驗。"
  x-governance-level: Level-1-Guideline
  required:
    - user_name
  properties:
    user_name:
      type: string
      pattern: '^[a-zA-Z0-9_]{3,20}$'
      description: "遵循蛇形命名，禁止使用其他變體。"
```

分析：此處的命名被賦予了實質的物理強制力。任何試圖使用 `userName` 或 `client_id` 來繞過約定的提交，將直接觸發驗證阻斷。對 AI 代理人 <!-- term:AiAgent -->而言，字典即為物理邊界。這消除了模型猜測屬性名稱的空間，也防堵了人為疏失的滲透。

## 反思

如果上述全是業界的誤區，那麼在導入治理框架時，正確的底層原理是什麼？

### 原理一：「命名即文件」必須具備物理性的編譯邊界

傳統軟體工程中，「命名即文件 <!-- term:NamingAsDocumentation -->」是指變數名稱應該要有意義，以減少註解（例如用 `elapsedTimeInDays` 取代 `d`）。但在高度依賴 AI 代理人 <!-- term:AiAgent -->的架構中，這個概念必須被**升級為物理邊界**。

對 Agent 來說，模糊的 Wiki 說明是毒藥，精準的 Dictionary 是救贖。我們必須將業務領域的共同語彙（Terminology）直接編碼進核心的 結構合約 <!-- term:Schema --> 中。當 Agent 看到 `SecurityAuditResult`，它不應該需要去查閱外部文件來理解這是什麼；這個字串本身，以及它在 結構合約 <!-- term:Schema --> 中的定義，就必須是全宇宙唯一且窮盡的解釋。

更重要的是，這個「命名」必須能觸發編譯器或驗證工具。凡是不在 結構合約 <!-- term:Schema --> 字典裡的**自鑄新詞**（Jargon） <!-- term:Jargon -->，必須在開發週期的第一步（IDE 內或預先提交階段）就被無情地攔截。

> [!IMPORTANT]
> **自鑄新詞** <!-- term:Jargon --> (Jargon): 團隊自行發明或非通用的特定技術與業務術語。 <!-- anchor:Jargon -->


### 原理二：絕對的驗證優先序

當文件宣稱的真理，與系統實際運作的行為發生衝突時，聽誰的？

這是一個必須被寫進架構元規則（Meta-rules）的通用原理。答案永遠是：**現實優先**。

我們必須確立三層**驗證優先序 (**絕對的驗證優先序**（Verification Precedence） <!-- term:VerificationPrecedence -->)**：
1.  **執行時行為**：系統實際接收與處理什麼資料。
2.  **原始碼 (Source Code & Auto-generated Interfaces)**：系統被建造成什麼具體結構。
3.  **觀察性文件**（Descriptive Documentation/Specs） <!-- term:DescriptiveDocumentationSpecs -->：系統被描述成什麼理想藍圖。

> [!IMPORTANT]
> **絕對的驗證優先序** <!-- term:VerificationPrecedence --> (Verification Precedence): 當規格與真實系統行為發生衝突時，以執行時行為為最高真理的優先序決策順序。 <!-- anchor:VerificationPrecedence -->
> **觀察性文件** <!-- term:DescriptiveDocumentationSpecs --> (Descriptive Documentation/Specs): 以記錄當前系統真實運作狀況與既存問題為主，而非強加未來限制的說明文件。 <!-- anchor:DescriptiveDocumentationSpecs -->


高層級無條件否決低層級。如果一份規格書聲稱時間格式是 ISO8601，但執行時的介面實際只接受 Unix Timestamp 整數，AI 代理人 <!-- term:AiAgent -->或開發者的第一反應，決不能是「強行修改客戶端程式碼以吻合空洞的規格書」（迷思二的錯誤），而是必須**「立刻修改規格書，標註現狀與理想規格的技術債 <!-- term:TechnicalDebt -->落差」**。

## 結論

在真正的架構治理中，我們寧可擁有一份「誠實描述系統積弊有多深」的觀察性文件 <!-- term:DescriptiveDocumentationSpecs -->，也絕不允許存在一份「美麗卻充滿謊言」的強制定義規格書。

「命名即文件 <!-- term:NamingAsDocumentation -->」不應停留在提升人類可讀性的修辭學層次。它必須被轉化為機器的約束邊界。只有當命名成為不可迴避的領域字典，且該字典成為系統所有的進入點與編譯期的攔截基礎時，規格驅動開發 <!-- term:SpecDrivenDevelopment --> 才具備免於崩塌的實踐可能。承認這一點，是從 SDD 的集體幻覺 <!-- term:Hallucination -->中清醒的第一步。