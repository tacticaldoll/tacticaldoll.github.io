+++
title = "消滅隱式依賴的架構課：從狀態追蹤到領域自洽"
date = "2026-06-07T23:42:01+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "從雙重狀態同步與排程器神物件這兩大反模式出發，拆解管線如何在不知不覺中積累隱式依賴；並透過「實體目錄即資料庫」的無狀態設計與建造者模式，重建單一真相來源與清晰的領域邊界。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "AI 代理人", # term:AiAgent
    "分析論文", # term:AnalyticalEssay
    "建造者模式", # term:BuilderPattern
    "領域驅動設計", # term:DomainDrivenDesign
    "發佈排程腳本", # term:OrchestratorScript
    "雙重狀態同步", # term:DualStateSynchronization
    "隱式狀態突變", # term:ImplicitStateMutation
  ]
[ai_info]
    [ai_info.generation]
        model = "Gemini 3.1 Pro"
        agent = "Antigravity IDE 2.0.4"
    [ai_info.refinement]
        model = "Claude Opus 4.8"
        agent = "Claude Code VSCode Extension 2.1.169"
+++

<!--more-->

## 導言

在自動化知識處理與發布管線（Publishing Pipeline）的演進歷程中，為了解決任務進度追蹤與動態元數據注入的迫切需求，系統架構往往會不知不覺地積累隱式依賴（Implicit Dependencies）。這些依賴最初看似無害的便利捷徑，但隨著時間推移與管線複雜度的陡增，它們會逐漸演變成全域變數的幽靈，成為系統擴展、自動化測試與除錯的嚴重阻礙。

本次架構**反思**（Reflection） <!-- term:Reflection -->旨在探討並解決管線設計中的兩大核心反模式（Anti-patterns）：第一，是過度依賴全域中介檔案（Global Index Files）所帶來的脆弱狀態同步問題；第二，是**發佈排程腳本**（Orchestrator Script） <!-- term:OrchestratorScript -->因承載過多業務邏輯而膨脹為難以測試的神物件（God Object）。這不僅是一次語法層面的簡單重構，更是重新確立系統單一真相來源（**單一事實來源**（Single Source of Truth） <!-- term:SingleSourceOfTruth -->，SSOT）與落實**領域驅動設計**（Domain-Driven Design） <!-- term:DomainDrivenDesign -->嚴格邊界的關鍵重塑。

> [!IMPORTANT]
> **反思** <!-- term:Reflection --> (Reflection): 對現行架構與工程盲點進行的深層檢討與批判。 <!-- anchor:Reflection -->
> **發佈排程腳本** <!-- term:OrchestratorScript --> (Orchestrator Script): 負責橫向流程調度的腳本；在健康的架構中只做排程與依賴傳遞，不應親自承載標籤萃取、設定解析等縱向領域邏輯。 <!-- anchor:OrchestratorScript -->
> **單一事實來源** <!-- term:SingleSourceOfTruth --> (Single Source of Truth): 指在特定工作執行緒中唯一被視為絕對真實與合法的結構化資料來源，所有操作皆以其為單向基準。 <!-- anchor:SingleSourceOfTruth -->
> **領域驅動設計** <!-- term:DomainDrivenDesign --> (Domain-Driven Design): 指採用領域驅動架構（DDD），將邏輯與行為封裝於自描述領域實體中的結構化設計方法。 <!-- anchor:DomainDrivenDesign -->


## 分析

在傳統的管線實作中，我們觀察到兩個存在根本缺陷的設計決策，這兩個缺陷共同造就了高耦合的脆弱系統。

**缺陷一：**雙重狀態同步**（Dual State Synchronization） <!-- term:DualStateSynchronization -->
過去，系統為了掌握每一份生成任務的進度，選擇依賴獨立的狀態追蹤檔案（如 `session_records` 或 JSON 索引清單）。這不可避免地導致了真實檔案系統狀態與 JSON 紀錄之間的**脫鉤**（Desynchronization） <!-- term:Desynchronization -->。當實體檔案產生失敗、暫存目錄被開發者手動清理，或是跨越不同環境部署時，這種中介檔案便會成為錯誤狀態的溫床。它從根本上違反了 SSOT 原則，迫使開發者在排除故障時必須同時核對實體檔案與索引紀錄這兩個潛在衝突的真相來源。

> [!IMPORTANT]
> **雙重狀態同步** <!-- term:DualStateSynchronization --> (Dual State Synchronization): 同時維護實體檔案系統與獨立 JSON 索引兩套狀態的反模式，兩者容易脫鉤而違反單一真相來源。 <!-- anchor:DualStateSynchronization -->
> **脫鉤** <!-- term:Desynchronization --> (Desynchronization): 中介索引檔與真實檔案系統狀態不再一致的現象，是雙重狀態同步最典型的故障表現。 <!-- anchor:Desynchronization -->


**缺陷二：管線腳本的**隱式狀態突變**（Implicit State Mutation） <!-- term:ImplicitStateMutation -->
早期的排程器承攬了壓倒性的領域職責。它不僅負責橫向的流程調度，還親自下場進行縱向的標籤萃取、設定檔解析、作者錨定以及遙測數據的過濾。更致命的是，排程器頻繁透過直接修改傳入的文件實體（Document Entity）來完成任務，產生了大量難以追蹤的副作用。物件被丟進一個巨大的黑箱中，出來時已被塞滿各式屬性，這使得單元測試變得幾乎不可能，且嚴重違反了單一職責原則（SRP）。

> [!IMPORTANT]
> **隱式狀態突變** <!-- term:ImplicitStateMutation --> (Implicit State Mutation): 排程器直接修改傳入文件實體、產生難以追蹤副作用的反模式，違反單一職責原則並使單元測試近乎不可能。 <!-- anchor:ImplicitStateMutation -->


為了解決上述問題，我們透過架構圖來視覺化新舊設計的根本差異：

```mermaid
graph TD
    subgraph 舊架構：隱式突變與雙重狀態
        O[Orchestrator Script] -->|讀寫| I[(index.json 中介狀態)]
        O -->|隱式修改| D1[Document Entity]
        O -->|隱式修改| D1
        I -.->|狀態容易脫鉤| FS[(實體檔案系統)]
    end

    subgraph 新架構：顯式組裝與無狀態
        OS[Orchestrator Script] -->|鏈式傳遞依賴| B[Document Assembler]
        B -->|純函數構建| D2[Document Entity]
        D2 -->|產出| FS2[(實體檔案系統 / SSOT)]
    end
```

如上圖所示，架構的修正分為雙軌進行：首先，**果斷廢除所有中介追蹤檔案**，確立「實體目錄結構即資料庫」的**無狀態**（Stateless） <!-- term:Stateless -->設計。任務的完成與否，完全取決於輸出目錄中實體檔案的存在與否。其次，**導入**建造者模式**（Builder Pattern） <!-- term:BuilderPattern -->，建立專屬的**文件組裝器**（Document Assembler） <!-- term:DocumentAssembler -->。讓排程腳本退回它應有的本分——單純負責排程與依賴傳遞，而將「如何組裝一份合法文件」的領域知識，完全委託給自洽的領域模型。

> [!IMPORTANT]
> **無狀態** <!-- term:Stateless --> (Stateless): 不依賴任何中介追蹤檔、任務完成與否完全由輸出目錄的實體檔案決定的設計，帶來冪等性與韌性。 <!-- anchor:Stateless -->
> **建造者模式** <!-- term:BuilderPattern --> (Builder Pattern): 透過 Fluent API 鏈式組裝物件的設計模式，將「如何組裝一份合法文件」的領域知識封裝於專屬組裝器。 <!-- anchor:BuilderPattern -->
> **文件組裝器** <!-- term:DocumentAssembler --> (Document Assembler): 採建造者模式、以純函數方式顯式構建文件實體的領域元件，取代排程器對傳入物件的隱式修改。 <!-- anchor:DocumentAssembler -->


## 反思

廢除全域狀態追蹤，雖然在初期會讓開發者產生失去「全域掌控感」的錯覺，但這種短期的犧牲卻換來了系統韌性的大幅提升。當我們不再需要費心維護兩套平行的狀態時，許多極端的**邊界狀況**（Edge Cases） <!-- term:EdgeCases -->便迎刃而解。舉例來說，如果一個節點在處理過程中意外崩潰，無狀態 <!-- term:Stateless -->的設計賦予了系統完美的冪等性（Idempotence）——我們只需重新執行指令，系統便能依據實體檔案的現狀無縫接續，而不會因為中介檔案殘留的髒數據而卡在無效狀態。

> [!IMPORTANT]
> **邊界狀況** <!-- term:EdgeCases --> (Edge Cases): 流程中的極端情境（如節點處理途中崩潰、暫存目錄被手動清理）；無狀態設計可藉冪等重試自然化解。 <!-- anchor:EdgeCases -->


此外，引入領域組裝器後，排程腳本的程式碼行數通常能縮減 70% 以上，不僅可測試性與可讀性有了質的飛躍，更在模組間畫下了清晰的界線。然而，這種設計也伴隨著嚴格的紀律要求：未來任何元數據的新增或修改需求，都必須嚴格遵守領域邊界，不能圖一時方便直接在排程器中進行屬性賦值。這份「**刻意的約束**（Intentional Constraint） <!-- term:IntentionalConstraint -->」，正是維持軟體架構純淨的必要代價。

> [!IMPORTANT]
> **刻意的約束** <!-- term:IntentionalConstraint --> (Intentional Constraint): 主動限制元數據只能經領域邊界寫入、禁止在排程器直接賦值的紀律，是維持架構純淨的必要代價。 <!-- anchor:IntentionalConstraint -->


## 實務對弄 (Practical Contrastive Examples)

為了更清晰地界定**語意邊界**（Semantic Boundary） <!-- term:SemanticBoundary -->並對抗抽象漂移，以下對比了兩種不同的架構實作方式。請注意排程器角色的轉變與屬性變更的清晰度。

> [!IMPORTANT]
> **語意邊界** <!-- term:SemanticBoundary --> (Semantic Boundary): 模組或類別在空間維度上定義其職責與封裝邊界的概念 <!-- anchor:SemanticBoundary -->


**反面模式：隱式狀態突變** <!-- term:ImplicitStateMutation -->
在這種設計中，排程腳本**越俎代庖**（Overstepping Boundaries） <!-- term:OversteppingBoundaries -->，直接對傳入的物件進行大量隱式修改。這使得排程器與文件結構產生了極高的強耦合，任何領域邏輯的變更都會直接波及排程層。

> [!IMPORTANT]
> **越俎代庖** <!-- term:OversteppingBoundaries --> (Overstepping Boundaries): 元件承擔超出自身職責範圍工作的反模式，例如排程器親自進行領域層的屬性賦值與標籤萃取。 <!-- anchor:OversteppingBoundaries -->


```python
# 錯誤示範：全能排程器中的元數據注入
def _inject_metadata(self, document_entity, processing_context, vocabulary_db):
    # 排程器親自執行數百行的字串解析、比對與陣列操作
    author_name = self._parse_global_config()
    normalized_tags = self._resolve_tags(processing_context, vocabulary_db)
    
    # 隱式的狀態突變，導致物件難以追蹤修改來源
    document_entity.metadata["author"] = author_name
    document_entity.metadata["tags"] = normalized_tags
```

**正確模式：**顯式領域組裝**（Explicit Domain Assembly） <!-- term:ExplicitDomainAssembly -->
在這種設計中，排程器僅透過 Fluent API 傳遞所需的依賴與上下文。這種寫法不只是語法糖，而是一種「編譯期與執行期的防禦機制」，它強制要求所有屬性必須透過組裝器所開放的介面（Interface）進行顯式構建，意圖明確且毫無隱藏副作用。

> [!IMPORTANT]
> **顯式領域組裝** <!-- term:ExplicitDomainAssembly --> (Explicit Domain Assembly): 強制所有屬性都經組裝器開放介面顯式構建的做法，意圖明確且無隱藏副作用，作為編譯期與執行期的防禦機制。 <!-- anchor:ExplicitDomainAssembly -->


```python
# 正確示範：排程器僅負責依賴傳遞與鏈式調用
document_entity = (DocumentAssembler(document_entity)
                   .with_base_meta(processing_context)
                   .with_author(global_config_path)
                   .with_vocabulary_tags(processing_context, vocabulary_db)
                   .with_telemetry(processing_context)
                   .build())
```

## 結論

回過頭來看，這次重塑其實揭示了一個更通用的軟體工程原理：任何需要「**暗中同步**（Covert Synchronization） <!-- term:CovertSynchronization -->」或「越俎代庖 <!-- term:OversteppingBoundaries -->」的設計，最終都會演變成難以償還的**技術債**（Technical Debt） <!-- term:TechnicalDebt -->。依賴倒置與單一真相來源法則（SSOT）並不僅僅是理論上的教條，而是對抗系統熵增的具體武器。

> [!IMPORTANT]
> **暗中同步** <!-- term:CovertSynchronization --> (Covert Synchronization): 需要在背景偷偷維持多份狀態一致的設計傾向，最終會累積成難以償還的技術債。 <!-- anchor:CovertSynchronization -->
> **技術債** <!-- term:TechnicalDebt --> (Technical Debt): 程式碼中為求快速交付而妥協、待重構與修復的設計或品質缺陷。 <!-- anchor:TechnicalDebt -->


當我們讓實體目錄結構原原本本地反映任務真實狀態，並讓領域物件完全掌握自身的組裝邏輯時，系統便能獲得面對未來規模化擴展所需的絕對韌性與清晰度。讓排程歸排程，讓實體歸實體，堅守物件的領域自洽性，這正是領域驅動設計 <!-- term:DomainDrivenDesign -->最堅實的防線。