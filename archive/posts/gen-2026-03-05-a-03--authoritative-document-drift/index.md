+++
title = "當權威文件出錯時"
date = "2026-03-05T09:20:03+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "一次針對文件內部一致性的系統性審計經驗，探討當外部權威（如官方文件）與系統執行時行為發生矛盾時的解決方案與教訓。"
tags = [
    "經驗報告", # term:ExperienceReport
    "AI 代理人", # term:AiAgent
    "術語管理", # term:TerminologyManagement
    "AI 治理", # term:AIGovernance
    "自動化審計", # term:AutomatedAudit
    "架構演進", # term:ArchitectureEvolution
    "以程式碼為文件", # term:CodeAsDocumentation
    "可攜帶衍生物", # term:PortableDerivatives
  ]
series = ["遺留系統的 AI 協同治理：從單體指令到執行時優先的結構化實踐"]
[ai_info]
    [ai_info.generation]
        model = "Claude Opus 4.6"
        agent = "Claude Code VSCode Extension 2.1.66"
    [ai_info.refinement]
        model = "Gemini 3.5 Flash"
        agent = "Antigravity IDE 2.0.4"
+++

<!--more-->

## 背景

多份治理文件和**知識萃取**（Knowledge Extraction） <!-- term:KnowledgeExtraction -->工具已經運作——規則引用技能、技能引用規則，所有文件都宣稱與外部平台規格對齊。元規則明確聲明「當專案慣例與原生定義分歧時，原生定義優先」。系統看似完整，但從未被系統性地審計過內部一致性。

> [!IMPORTANT]
> **知識萃取** <!-- term:KnowledgeExtraction --> (Knowledge Extraction): 從非結構化的開發對話中，提取有價值決策與技術知識的過程。 <!-- anchor:KnowledgeExtraction -->


知識萃取 <!-- term:KnowledgeExtraction -->管線剛完成設計，提供了評估、結構化和持久化對話知識的工具。在使用這些工具的過程中，大量文件被建立和修改。術語在不同文件間流動——同一個概念可能在不同地方使用不同措辭，規格更新可能遺漏下游引用。建立一個術語審計技能來檢測這些漂移成為自然的需求。

## 發現

### 階段一：首次審計

術語審計技能被設計為四維掃描：術語一致性、原生規格對齊、結構骨架合規、交叉**引用完整性**（Referential Integrity） <!-- term:ReferentialIntegrity -->。建立後立即對所有治理文件執行。

> [!IMPORTANT]
> **引用完整性** <!-- term:ReferentialIntegrity --> (Referential Integrity): 批量變更或重命名時，系統中所有交叉引用（包括非典型位置的類型標記與文件段落）皆被同步更新的狀態。 <!-- anchor:ReferentialIntegrity -->


首次審計掃描了 15 份文件，產出 7 項發現。兩項錯誤是**結晶**（Crystallize） <!-- term:Crystallize -->技能中殘留的舊版機制選擇措辭——「由情境觸發、產出成品」用於描述技能，而當前的權威定義是「延伸能力——可執行任務、參考知識或領域專業」。兩項**警告**（Warning） <!-- term:Warning -->是沉澱技能中的動詞漂移——「**蒸餾**（Distill） <!-- term:Distill -->知識」出現在應使用「萃取知識」之處，因為沉澱是蒸餾 <!-- term:Distill -->的下游，不應宣稱執行蒸餾 <!-- term:Distill -->動作。

> [!IMPORTANT]
> **結晶** <!-- term:Crystallize --> (Crystallize): 將蒸餾後的關鍵知識沉澱並結構化為正式報告或規格的過程。 <!-- anchor:Crystallize -->
> **警告** <!-- term:Warning --> (Warning): 術語審計中指出的潛在問題或警告 <!-- anchor:Warning -->
> **蒸餾** <!-- term:Distill --> (Distill): 從長對話或大量開發脈絡中萃取關鍵資訊的處理過程。 <!-- anchor:Distill -->


這些修正直接明確，逐項套用後提交。但還有一項**資訊性發現**（Info） <!-- term:Info -->被標記為「稍後處理」——跨 11 份技能定義檔的欄位拼寫問題：`user-invokable`（帶 k）出現在所有檔案中，而審計推測正確拼寫應為 `user-invocable`（帶 c）。

> [!IMPORTANT]
> **資訊性發現** <!-- term:Info --> (Info): 術語審計中指出的資訊性發現 <!-- anchor:Info -->


### 階段二：執行時矛盾

為了確認拼寫推測，團隊查閱了外部平台的官方文件。文件明確記載欄位名稱為 `user-invocable`（帶 c）。基於官方文件的權威性，開始在所有 11 份技能定義檔中將 `user-invokable` 改為 `user-invocable`。

九份檔案修改成功。但隨即，IDE 的 schema 驗證器——外部平台 VSCode 擴充套件內建的 YAML frontmatter 驗證功能——注入了診斷訊息：

> 「屬性 'user-invocable' 在技能檔案中不受支援。支援的屬性包含：...user-invokable...」

> [!NOTE]
> **Decision Point**: 執行時驗證器否決了官方文件確認的拼寫
> — Alternatives: 信任官方文件（假設驗證器有 bug）vs. 信任執行時行為
> — Outcome: 信任執行時行為。九份已修改的檔案全部還原為 `user-invokable`。執行時驗證器反映的是系統的實際 schema，而文件記載的可能已過時或有誤

這個發現不僅修正了拼寫——它暴露了治理框架中一個未被定義的層：元規則宣告「原生定義優先」，但沒有定義什麼算是「原生定義」，也沒有指定如何驗證。官方文件被隱性地視為最終權威，而執行時行為揭示了這個假設的脆弱性。

### 階段三：建立驗證優先序

追問「IDE schema 驗證器到底是什麼？」引出了一個層次分析。驗證器是外部平台 VSCode 擴充套件內建的 YAML frontmatter schema 驗證功能，它嵌入了與執行時相同的 schema。這意味著它反映的不是文件描述的行為，而是系統的實際行為。

將驗證來源按照可靠性排序，形成了外部權威的驗證優先序：

1. **執行時 schema 驗證器**（實際行為——系統接受什麼）
2. **原始碼**（設計意圖——系統被建造成什麼）
3. **官方文件**（**描述性**（Descriptive） <!-- term:Descriptive -->——系統被說成什麼）

> [!IMPORTANT]
> **描述性** <!-- term:Descriptive --> (Descriptive): 用於記錄系統「實際如何運作」的知識屬性，代表逆向工程的客觀觀察事實，不具備強制的行為契約效力。 <!-- anchor:Descriptive -->


高優先序否決低優先序。這個優先序被記錄為術語審計技能的經驗段落，作為未來審計的操作基準。

### 階段四：辨識內部平行

驗證優先序建立後，一個結構性的相似浮現。專案自身的**以程式碼為文件**（Code-As-Documentation） <!-- term:CodeAsDocumentation -->規則（code-as-documentation）已定義了內部知識的優先序：程式碼本身 > 就近文件 > 知識庫。兩者的邏輯結構完全同構——「實際行為優先於描述性 <!-- term:Descriptive -->文件」。

> [!IMPORTANT]
> **以程式碼為文件** <!-- term:CodeAsDocumentation --> (Code-As-Documentation): 將程式碼本身視為主要文件的開發原則 <!-- anchor:CodeAsDocumentation -->


這個辨識產生了一個可泛化的原則：任何宣稱與外部權威對齊的治理框架，必須同時定義該權威的驗證層級。否則，對齊宣告只是信任假設，不是可驗證的約束。文件可能落後於執行時，原始碼可能偏離文件，唯有實際行為是不可辯駁的。

### 階段五：後設資料中的殘留術語

在結晶 <!-- term:Crystallize -->技能經歷大幅增強（可讀性指南、**部署套件**（Deploy Kit） <!-- term:DeployKit -->規格、批次協調、**報告索引**（Report Index） <!-- term:ReportIndex -->）後，第二次術語審計被執行。這次專門針對結晶 <!-- term:Crystallize -->技能本身。

> [!IMPORTANT]
> **部署套件** <!-- term:DeployKit --> (Deploy Kit): 將專案配置與成果打包，供獨立部署或執行的套件 <!-- anchor:DeployKit -->
> **報告索引** <!-- term:ReportIndex --> (Report Index): 記錄歷史生成報告之後設資料，供去重與重結晶評估的索引檔案。 <!-- anchor:ReportIndex -->


審計發現了一個典型的**後設資料**（Metadata） <!-- term:Metadata -->陳舊模式：技能的流程段落和規則段落已從「**可攜帶衍生物**（Portable Derivatives） <!-- term:PortableDerivatives -->」全面更新為「部署套件 <!-- term:DeployKit -->」，但檔案頂端的 frontmatter description 仍寫著「optional portable derivatives」。問題的根因是概念重命名的工作流程覆蓋了流程段落（內容本體），卻遺漏了後設資料 <!-- term:Metadata -->標頭（一行描述文字）——後設資料 <!-- term:Metadata -->不在重命名操作的自然工作路徑上。

> [!IMPORTANT]
> **後設資料** <!-- term:Metadata --> (Metadata): 描述其他資料的資料，例如 frontmatter 或標頭資訊 <!-- anchor:Metadata -->
> **可攜帶衍生物** <!-- term:PortableDerivatives --> (Portable Derivatives): 早期用於描述可獨立執行的衍生套件，現已更新為部署套件 <!-- anchor:PortableDerivatives -->


修正是將 frontmatter description 更新為反映當前術語。但這個發現本身揭示了一個更一般性的漂移模式：當一個概念在文件的主體中被重命名，**非主體位置**（frontmatter、註解、範例中的引用）是最容易被遺漏的，因為它們不在修改操作的主要關注路徑上。

### 階段六：前瞻性規格問題

同一次審計還發現了另一類問題。結晶 <!-- term:Crystallize -->技能的報告索引 <!-- term:ReportIndex -->段落（Phase 8）聲明：「消費者：distill（在推薦萃取前檢查主題重疊）」。但檢查 distill 的技能定義檔，它沒有任何讀取或引用報告索引 <!-- term:ReportIndex -->的機制。

> [!NOTE]
> **Decision Point**: 文件宣稱了消費者尚未實作的行為
> — Alternatives: 移除消費者引用（失去設計意圖）vs. 保留但標註為計畫中（區分現況與意圖）
> — Outcome: 保留並標註「planned integration — not yet implemented in consumer skills」。這區分了系統現在做什麼（索引存在，無消費者讀取）和系統設計上最終要做什麼（distill 檢查重疊）

這是一種特殊類型的文件錯誤：**前瞻性規格**（Forward-Looking Spec） <!-- term:ForwardLookingSpec -->——將計畫中的行為描述為已實現的事實。文件讀起來像事實陳述，實際上是前瞻性的設計意圖。它與階段二的執行時矛盾結構上相同——文件描述的不是系統的實際狀態，而是系統的期望狀態。

> [!IMPORTANT]
> **前瞻性規格** <!-- term:ForwardLookingSpec --> (Forward-Looking Spec): 將計畫中但尚未實作的行為描述為已實現的規格 <!-- anchor:ForwardLookingSpec -->


## 決議

| # | 決策 | 原因 |
|---|------|------|
| 1 | 首次審計的直接修正（舊措辭、動詞漂移） | 明確的術語不一致，權威定義清晰 |
| 2 | 信任執行時驗證器，還原官方文件導向的修改 | 執行時 schema 反映實際行為，文件可能過時 |
| 3 | 建立三層驗證優先序 | 泛化教訓——任何外部權威對齊都需要驗證層級 |
| 4 | 後設資料 <!-- term:Metadata -->陳舊修正 | 概念重命名遺漏非主體位置 |
| 5 | 前瞻性規格 <!-- term:ForwardLookingSpec -->標註為「計畫中」 | 區分現況與設計意圖，避免誤導消費者 |

## 補充知識

權威文件至少有三種出錯方式，每種有不同的檢測策略：

| 出錯方式 | 定義 | 檢測 |
|----------|------|------|
| **事實錯誤** | 文件說 X，但執行時做 Y | 執行時驗證（schema 驗證器、測試執行） |
| **陳舊** | 文件曾經正確說 X，但底層系統已改變 | 定期重新驗證；非主體位置（frontmatter、範例引用）是高風險區 |
| **前瞻性** | 文件描述計畫中的行為如同已實現 | 消費者端驗證——檢查被宣稱的消費者是否實際具備相應機制 |

三者共享一個根因：文件描述**意圖或歷史狀態**，而程式碼和執行時描述**當前實際狀態**。任何信任文件而不驗證的治理框架都繼承了這個缺口。

## 技術啟示

1. **官方文件不是最終權威——執行時行為才是。** 當官方文件和執行時行為矛盾時，執行時贏。這不是因為文件「故意」出錯，而是因為文件描述的是意圖或歷史狀態，而執行時反映的是當前事實。驗證優先序是對這個現實的形式化。

2. **內部優先序原則可以延伸到外部依賴。** 以程式碼為文件 <!-- term:CodeAsDocumentation -->和外部權威驗證（runtime > source > docs）是同一個原則的兩個實例——實際行為優先於描述性 <!-- term:Descriptive -->文件。辨識這種同構性幫助避免在不同上下文中重新發明相同的原則。

3. **後設資料 <!-- term:Metadata -->是**術語漂移**（Terminology Drift） <!-- term:TerminologyDrift -->的高風險區。** 當概念在文件主體中被重命名時，frontmatter、單行描述、範例中的引用最容易被遺漏——它們不在修改操作的自然工作路徑上。術語審計必須將非主體位置納入掃描範圍。

> [!IMPORTANT]
> **術語漂移** <!-- term:TerminologyDrift --> (Terminology Drift): 在概念消解或變更的場景下，AI 代理人因對話上下文中舊術語高頻出現而沿用舊稱呼的預設行為。 <!-- anchor:TerminologyDrift -->


4. **前瞻性規格 <!-- term:ForwardLookingSpec -->需要明確標記。** 描述計畫中行為如同已實現的事實會誤導消費者。「計畫中的整合」標註雖然笨拙，但誠實地區分了系統的現況和設計意圖。這與程式碼中「TODO」註解的邏輯相同——標記未完成的部分比假裝完成更安全。

5. **治理框架的外部對齊宣告需要驗證機制。** 宣告「原生定義優先」而不定義驗證層級，等於把對齊建立在信任假設上。當信任假設被打破（如本例中的拼寫矛盾），對齊宣告就失去了可操作性。驗證優先序將信任假設轉換為可驗證的約束。