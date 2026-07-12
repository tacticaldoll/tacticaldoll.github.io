+++
title = "防禦型 Agent 架構：在多模型協作中實踐最小注入與血統追蹤"
date = "2026-03-28T17:00:01+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "探討在多模型協作管線中，如何透過語意隔離原則（如 YAML 法拉第籠）與環境區分的溯源標記，防範大型語言模型產生語意污染與越權修改，建立穩健的防禦型 Agent 架構。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "AI 代理人", # term:AiAgent
    "多模型協作", # term:MultiModelCoordination
    "語意隔離", # term:SemanticIsolation
    "法拉第籠", # term:FaradayCage
    "溯源標記", # term:ProvenanceMarker
    "模型遙測後設資料", # term:TelemetryMetadata
    "權責的阻斷切割", # term:SeparationOfAccountability
  ]
[ai_info]
    [ai_info.generation]
        model = "Gemini 3.1 Pro"
        agent = "Antigravity IDE 1.19.6.0"
    [ai_info.refinement]
        model = "Gemini 3.5 Flash"
        agent = "Antigravity IDE 2.0.4"
+++

<!--more-->

## 導言

隨著大語言模型 (LLM) 被廣泛接入**自動化腳本**（Actuators） <!-- term:Actuators -->的控制管線，**多模型協作**（Multi-Model Coordination） <!-- term:MultiModelCoordination -->——即一個模型負責摘要總結，交棒給自動化腳本 <!-- term:Actuators -->分發處理，再傳遞給另一個高智商模型進行文稿精煉——已經成為現代開發架構的常態範式。

> [!IMPORTANT]
> **自動化腳本** <!-- term:Actuators --> (Actuators): 在自動化系統中負責接收控制指令並具體執行 CRUD 或其他物理狀態修改的程式元件。 <!-- anchor:Actuators -->
> **多模型協作** <!-- term:MultiModelCoordination --> (Multi-Model Coordination): 在同一個控制管線中，協調多個不同模型與自動化腳本依次完成不同任務的開發範式。 <!-- anchor:MultiModelCoordination -->


然而，大語言模型對於自然語言的超高敏銳度與強大的聯想泛化能力，在這類由腳本驅動的流水線中，既是最強的武器，亦是牽一髮而動全身的致命隱患。當我們單純地提供一份以 Markdown 撰寫的結構指引文件時，模型極易在其推理過程中產生**語意污染**（Semantic Pollution） <!-- term:SemanticPollution -->——它們將純粹用於定界資料結構的描述，誤認為是要求其發散邏輯的開放性寫作指令。

> [!IMPORTANT]
> **語意污染** <!-- term:SemanticPollution --> (Semantic Pollution): 指在共享上下文或設定檔中引入無關、混亂或具備多義性的指令，導致 AI 代理理解與推論精確度下降的現象。 <!-- anchor:SemanticPollution -->


為了確保**多代理**（Multi-Agent） <!-- term:MultiAgent -->協作體系的絕對約束與穩健流轉，我們必須嚴格落實**語意隔離**（Semantic Isolation） <!-- term:SemanticIsolation --> 原則，建立無法被自然語言穿越的實體邊界；並透過嚴密的環境區分建立**溯源標記**（Provenance Marker） <!-- term:ProvenanceMarker -->，為多世代的知識產出明確錨定品質究責與來源歸屬。

> [!IMPORTANT]
> **多代理** <!-- term:MultiAgent --> (Multi-Agent): 多個智慧代理程式協同運作，共同完成複雜任務的系統架構。 <!-- anchor:MultiAgent -->
> **語意隔離** <!-- term:SemanticIsolation --> (Semantic Isolation): 在 LLM 上下文中，建立無法被自然語言穿透的實體邊界，防止模型因理解多餘資訊而引發語意坍塌。 <!-- anchor:SemanticIsolation -->
> **溯源標記** <!-- term:ProvenanceMarker --> (Provenance Marker): 為多世代或多模型協作的產出，記錄其原始生成源頭與當前精煉環境的遙測後設資料標籤。 <!-- anchor:ProvenanceMarker -->


## 分析

大模型在解析含有大量標籤與格式（如二級標題、強調語法、清單）的 Markdown 規格文件時，其底層機制往往會將注意力資源過度揮霍在「理解並模仿真實文件的排版結構」，從而對其核心需要產出的「精確數據特徵」失焦。

若我們將專案中的 Core **結構合約**（Schema） <!-- term:Schema --> 規範與寫作指路教學（工作流）混合在同一個由 LLM 讀取的上下文脈絡中，一旦某些邊界觸發了模型的過度聯想，它往往會主動越權去填補不屬於它的欄位，甚至擅自修改腳本預期的介面陣列。

> [!IMPORTANT]
> **結構合約** <!-- term:Schema --> (Schema): 定義資料欄位、型別與排版限制的強型別規格定義，用於強制約束模型產出的格式。 <!-- anchor:Schema -->


### 解方：YAML 法拉第籠

為了消除這種聯想空間，將所有涉及**架構層**（Architecture） <!-- term:Architecture -->面的邊界定義嚴格封裝進去語意化、強型別的純文字 `YAML` 字典模型中，這形同為 LLM 的創意奔放機制打造了一座名副其實的「**法拉第籠**（Faraday Cage） <!-- term:FaradayCage -->」。YAML 或是 JSON 結構強制剝離了自然語言渲染的上下文敘事，將模型認知收斂並限縮進入「填表答卷 (Fill-in-the-blanks)」的單純狀態。

> [!IMPORTANT]
> **架構層** <!-- term:Architecture --> (Architecture): 規格文件中用以客觀記錄系統「實際在做什麼」的事實陳述層。 <!-- anchor:Architecture -->
> **法拉第籠** <!-- term:FaradayCage --> (Faraday Cage): 比喻在語意層面使用強型別、結構化的資料（如 YAML）來封裝 LLM 的輸入，阻絕其不必要聯想的防禦機制。 <!-- anchor:FaradayCage -->


## 實務對比

**❌ 錯誤與稀釋的範例（暴露於 Markdown 結構性污染）**
```markdown
# Agent 填寫準則 [CRITICAL]
當你在輸出 `manifest.json` 時，請務必主動檢測並整理出現的雙語專有名詞。你要把它們用 `terms.discovered` 陣列標示出來。
此外，對於被查核出的違禁詞，請幫我寫在 `terms.forbidden_found` 中。
```
*(致命後果：LLM 完全將自己視為系統主宰。它可能會虛構「不存在於文章」的違禁詞，甚至擅自竄改陣列的命名與結構；嚴重時還會在正式文檔的回應中加入「我已經過濾完這些名詞...」的絮語。)*

**✅ 高解析度對比範例（封裝為 YAML 的語意隔離 <!-- term:SemanticIsolation -->屏障）**
```yaml
terms:
  # [NLP 單向發布區] 若使用特殊術語需建立連結，請於此陣列手動宣告。
  # 此為唯一的合法介接點，作為避免術語漏接的一次性保護機制。
  declared:
    - zh: "輸入術語 1"
      en: "English Term 1"
      
  # -------------------------------------------------------------
  # ⚠ 特權保留區 (System Reserved Zones) ⚠
  # 以下欄位由 Python 自動化引擎獨佔。嚴禁由 NLP 以任何形式干涉或提早定義。
  # -------------------------------------------------------------
  # existing: []
  # discovered: []
  # locked: []
```
*(**決定性**（Deterministic） <!-- term:Deterministic -->成果：對 LLM 而言，它只看見了一組嚴格限定的「**輸入繫結**（Input Bindings） <!-- term:InputBindings -->」，它不會對被註解屏蔽的高階陣列產生任何不必要的遐想。這不僅省下了海量的上下文 Token，更對運算腳本提供了可以無腦進行 Strict 結構合約 <!-- term:Schema --> Validation 的可靠輸入防線。)*

> [!IMPORTANT]
> **決定性** <!-- term:Deterministic --> (Deterministic): 保證在相同的輸入與控制下，自動化管線每次執行所產出的文件結構與內容完全收斂一致的特性。 <!-- anchor:Deterministic -->
> **輸入繫結** <!-- term:InputBindings --> (Input Bindings): 在 UI 或語意合約中，被嚴格限定只接收特定型別或欄位內容的輸入映射關係。 <!-- anchor:InputBindings -->


## 反思

當管線的建構涉及多位「參與者」時，知識往往經歷了異常漫長的生命週期：比如報告的初步歸納源自對話紀錄的 LLM，但最終排版套件的產出則交棒給了另一個純執行的 Agent。

傳統架構中，最後一個按鈕的執行者往往會殘暴地覆蓋掉原始創作者的所有蹤跡，使得最終渲染出來的「**模型遙測後設資料**（Telemetry Metadata） <!-- term:TelemetryMetadata -->」完全失去了源頭的指紋。為此，我們必須在管線初始化前段（如 Stage 0），強制將管線產能的通訊介面 (Telemetry) 層級化：區分為「**原始輸入源**（Generation Context） <!-- term:GenerationContext -->」與「**當前精煉環境**（Refinement Context） <!-- term:RefinementContext -->」。

> [!IMPORTANT]
> **模型遙測後設資料** <!-- term:TelemetryMetadata --> (Telemetry Metadata): 用於記錄大語言模型在特定工作流執行時的架構、模型版本、代理版本等追蹤性數據。 <!-- anchor:TelemetryMetadata -->
> **原始輸入源** <!-- term:GenerationContext --> (Generation Context): 記錄多代理協作中，知識或文件最初生成的模型、提示詞與上下文資訊。 <!-- anchor:GenerationContext -->
> **當前精煉環境** <!-- term:RefinementContext --> (Refinement Context): 記錄多代理協作中，對原始產出進行編譯、格式化或下錨的執行腳本與執行環境資訊。 <!-- anchor:RefinementContext -->


這不僅僅是為了撰寫無意義的日誌或進行純粹的溯源。更核心的原因在於**權責的阻斷切割**（Separation Of Accountability） <!-- term:SeparationOfAccountability -->：當文件出現邏輯荒謬、詞彙偏誤時，追責的箭頭指向的是 `Generation` 端的提示詞漏洞；而若是出現格式破版、TOML 引號錯亂，我們需要檢修的靶點則是對準 `Refinement` 的管線腳本設計。這份帶有立體深度的追蹤機制，為日後的自動化安全查核 (Safety Guarding 甚至物理修正巡檢) ，提供了最不可或缺的干預座標。

> [!IMPORTANT]
> **權責的阻斷切割** <!-- term:SeparationOfAccountability --> (Separation Of Accountability): 在多階段管線中，明確區分生成端提示漏洞與精煉端腳本錯誤之責任歸屬的設計原則。 <!-- anchor:SeparationOfAccountability -->


## 結論

一個具備長期維護價值、優雅且防禦性極佳的代理程式 vs Instruction），以及高解析度多段落的知識溯源標記 <!-- term:ProvenanceMarker -->，從真正的工程物理邊界上，徹底拒絕模型認知失控的可能性。只有劃清了不可逾越的絕對界線，多代理 <!-- term:MultiAgent -->管線方能邁入真正意義上的量產化。