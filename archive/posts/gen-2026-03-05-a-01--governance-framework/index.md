+++
title = "為遺留專案導入治理框架"
date = "2026-03-05T09:07:01+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "詳細記錄在遺留專案中導入文件階層與治理框架的歷程，解決了專案慣例、工程標準與累積知識的結構性混亂問題。"
tags = [
    "經驗報告", # term:ExperienceReport
    "AI 代理人", # term:AiAgent
    "AI 治理", # term:AIGovernance
    "專案架構", # term:ProjectArchitecture
    "知識庫管理", # term:KnowledgeBaseManagement
    "遺留系統重構", # term:LegacySystemRefactoring
    "以程式碼為文件", # term:CodeAsDocumentation
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

一個長期運行的遺留專案——前端採用舊世代框架、後端為 C++ 服務——依靠單一指令檔承載所有專案慣例、工程標準和累積知識。隨著內容持續膨脹，這份單體檔案開始暴露結構性問題：編碼約束和工具技能混在一起、規範性指令和**描述性知識**（Knowledge） <!-- term:Knowledge -->不分層級、沒有衝突解決機制。每次新增一條規則，都必須在同一個檔案裡找到合適的位置——但什麼是「合適」，缺乏判斷依據。

> [!IMPORTANT]
> **描述性知識** <!-- term:Knowledge --> (Knowledge): 逆向工程產出的描述性知識，在專案中被視為債務指標 <!-- anchor:Knowledge -->


知識庫同樣缺少邊界。逆向工程產出的架構文件（architecture documents）與待建構的規格共存於同一個目錄，沒有機制區分「已知事實」和「應該遵循的規則」。當有人問「這份知識庫裡有哪些內容其實是規格？」時，答案揭示了更深的問題：系統能確保流程正確，卻無法確保結果正確——因為根本沒有規格層。

## 發現

### 階段一：辨識觸發點

對既有知識庫進行全面盤點後，三個結構性缺陷浮現。首先，索引檔引用了三份不存在的文件——**幽靈引用**（Phantom References） <!-- term:PhantomReferences -->表明索引從未被系統性維護。其次，一份描述資源操作允許條件的文件，其內容實質上是規範性的（prescriptive），卻被歸類為描述性知識 <!-- term:Knowledge -->。第三，八個工具技能中有四個——負責程式碼扁平化、架構嚴謹性、業務規則封裝和資料領域隔離——不產出任何成品，而是在幾乎所有編碼場景下始終啟用。它們的行為更像約束規則，而非事件驅動的工具。

> [!IMPORTANT]
> **幽靈引用** <!-- term:PhantomReferences --> (Phantom References): 索引檔中指向不存在文件的引用 <!-- anchor:PhantomReferences -->


這些發現指向一個核心缺口：系統完全是技能驅動的（skill-driven）。技能定義「如何做」，知識記錄「是什麼」，但沒有任何機制扮演「應該建造什麼」的角色。換言之，系統能保證流程品質，卻無法保證成果正確性。

### 階段二：文件階層設計

缺口確認後，問題轉向：「是否需要一份**準則**（Guidelines） <!-- term:Guidelines -->的準則 <!-- term:Guidelines -->？」既有的規則文件在粒度、結構和強制力上各不相同——有的管理單一關注點，有的涵蓋 SOLID 原則加設計模式加遺留轉換，卻處於同一層級。沒有統一的 MUST/SHOULD/MAY 定義，也沒有衝突解決規則。

> [!IMPORTANT]
> **準則** <!-- term:Guidelines --> (Guidelines): 強制性的專案準則，指導如何正確地做事 <!-- anchor:Guidelines -->


> [!NOTE]
> **Decision Point**: 治理元規則的放置位置
> — Alternatives: 嵌入 project instructions（保證每次載入）、放入自訂目錄（語意正確但不自動載入）、使用路徑範圍規則（精準觸發、標準機制）
> — Outcome: 選擇路徑範圍規則——編輯規則檔案時自動注入，結合 project instructions 宣告階層以建立「憲法意識」。技術上不存在優先序強制機制，但三層疊加（宣告 + 自動注入 + RFC 2119 語意）最大化遵循度

四層文件階層由此建立。Level 0 是元規則本身，具有絕對權威且保持最小化。Level 1 是強制性準則 <!-- term:Guidelines -->，存放於規則目錄。Level 2 是**外部規格**（Specifications） <!-- term:Specifications -->輸入（specifications），由外部團隊提供，專案不自行管理。Level 3 是描述性知識 <!-- term:Knowledge -->，存放於知識庫。衝突發生時，高層級無條件勝出。

> [!IMPORTANT]
> **外部規格** <!-- term:Specifications --> (Specifications): 由外部團隊提供的權威性系統規格文件 <!-- anchor:Specifications -->


階層設計過程中，一次內容回流（content backflow）審查發現元規則初稿包含了按其自身分類標準應屬於 Level 1 的內容——索引維護規則、內容格式規則、生命週期規則。這些被抽出為獨立的準則 <!-- term:Guidelines -->檔案，元規則僅保留三個職責：階層定義、分類測試、結構骨架。

### 階段三：機制分類

技能與規則的混淆是階段一發現的核心問題之一。解決方案是建立一套「機制選擇」測試，採用**首次匹配**（First-Match） <!-- term:FirstMatch -->邏輯：需要隔離上下文或**持久記憶**（Persistent Memory） <!-- term:PersistentMemory -->的是 Agent；延伸能力、可執行任務或參考知識的是 Skill；強制執行約束或治理檢查點的是 Rule。

> [!IMPORTANT]
> **首次匹配** <!-- term:FirstMatch --> (First-Match): 採用首次命中邏輯的分類或測試機制 <!-- anchor:FirstMatch -->
> **持久記憶** <!-- term:PersistentMemory --> (Persistent Memory): 代理人跨對話維護的長期記憶，用於存放使用者偏好與互動規則。 <!-- anchor:PersistentMemory -->


> [!NOTE]
> **Decision Point**: 四個偽技能重新分類為規則
> — Alternatives: 保持技能身份但加上「始終啟用」標記（維持現狀的最小變動）vs. 重新分類為規則（語意正確、與平台原生定義對齊）
> — Outcome: 重新分類。區分標準清晰——技能產出成品且由事件驅動；規則始終啟用且不產出成品。四個單元的觸發描述證實了這一點：每一個都寫著「任何編碼、審查場景」，這正是規則而非技能的特徵

分類系統也釐清了**準則驅動**（Guideline-Driven） <!-- term:GuidelineDriven -->和規格驅動的關係。兩者互補而非競爭：準則 <!-- term:Guidelines -->回答「如何正確地做」（流程品質），規格回答「什麼算完成」（結果正確性）。成熟路徑是先建立準則 <!-- term:Guidelines -->，再用準則 <!-- term:Guidelines -->約束規格品質，最終進入兩者並行的穩態。

> [!IMPORTANT]
> **準則驅動** <!-- term:GuidelineDriven --> (Guideline-Driven): 以自動化規則與檢查哨護欄引導系統演進的過程導向開發模式。 <!-- anchor:GuidelineDriven -->


### 階段四：結構骨架與耦合段落同步

階層建立後，每種文件類型需要定義結構（structural skeleton）。準則 <!-- term:Guidelines -->骨架包含固定段落——目的、規則、檢查清單——且一份檔案只管一個關注點。技能骨架遵循平台原生格式。知識骨架包含**前置資料**（Front Matter） <!-- term:FrontMatter -->的型別標籤。

> [!IMPORTANT]
> **前置資料** <!-- term:FrontMatter --> (Front Matter): Markdown 檔案頂部的後設資料區塊 <!-- anchor:FrontMatter -->


更重要的是耦合段落同步（coupled-section synchronization）的概念。某些骨架中的段落是成對的：準則 <!-- term:Guidelines -->的「規則」段落和「檢查清單」段落必須一一對應，每條規則都有檢查項，每個檢查項都追溯到規則。當修改其中一個段落時，必須觸發另一個段落的同步審查。

這個概念在元規則自身的交叉矛盾審查中得到了驗證。階層規則第四條（「任何文件不得宣稱對自身層級或以上的權威」）與擴展規則第五條（「允許 project instructions 包含修改 Level 0 的過渡計畫」）存在矛盾。修正方式是在第四條中加入例外子句——這正是耦合段落同步機制要捕捉的那種不一致。

### 階段五：知識庫定位與知識路由

知識庫的物理位置引發了一場關於身份的討論。將其改為**隱藏目錄**（Dot-Prefix） <!-- term:DotPrefix -->的提案被分析後否決——知識庫的性質更接近專案文件（如 `docs/`），而非工具配置（如 `.git/`），應保持可見。但更根本的問題是知識庫的定位本身。

> [!IMPORTANT]
> **隱藏目錄** <!-- term:DotPrefix --> (Dot-Prefix): 以點開頭的隱藏目錄命名慣例 <!-- anchor:DotPrefix -->


**以程式碼為文件**（Code-As-Documentation） <!-- term:CodeAsDocumentation --> 原則將知識庫從「永久知識庫」重新定義為**債務指標**（Debt Indicator） <!-- term:DebtIndicator -->。每一份知識庫條目都代表程式碼自我文件化能力的一個缺口——逆向工程產出的知識之所以存在，是因為程式碼本身無法表達同樣的資訊。知識庫允許存在的場景被限縮為三種：跨切分析、遺留程式碼補償、經驗報告。

> [!IMPORTANT]
> **以程式碼為文件** <!-- term:CodeAsDocumentation --> (Code-As-Documentation): 將程式碼本身視為主要文件的開發原則 <!-- anchor:CodeAsDocumentation -->
> **債務指標** <!-- term:DebtIndicator --> (Debt Indicator): 用以標示系統或程式碼缺乏自我解釋能力的技術債務指標 <!-- anchor:DebtIndicator -->


這個重新定位需要一張**知識路由**（Attribution Routing） <!-- term:AttributionRouting -->表（knowledge routing table），指明各類知識的正確目的地。程式碼行為回歸原始碼本身，元件設計寫入就近的 README，技能運作經驗寫入技能定義檔的經驗段落，跨切分析才進入知識庫。預設選擇最高優先序的目的地——知識庫是最後手段，不是預設選項。

> [!IMPORTANT]
> **知識路由** <!-- term:AttributionRouting --> (Attribution Routing): 將系統的非結構化知識或遺留債務，精準指派並分流至合適的追蹤與管理工具之機制。 <!-- anchor:AttributionRouting -->


**查找順序**（Discovery Rule） <!-- term:DiscoveryRule -->也因此變成階段相依的：當前階段先查知識庫再查程式碼；知識庫消解完成後，先查就近 README 再查知識庫殘餘條目；最終進入規格驅動階段時，先查規格再查就近文件。

> [!IMPORTANT]
> **查找順序** <!-- term:DiscoveryRule --> (Discovery Rule): 決定知識或文件查找順序的規則 <!-- anchor:DiscoveryRule -->


### 階段六：過渡計畫

治理框架建立後，需要一條從逆向工程知識到**規格驅動開發**（Spec-Driven Development） <!-- term:SpecDrivenDevelopment -->的遷移路徑。知識庫本身就是遷移清單——每一份條目都是一筆債務，指向某個原始碼目錄缺乏自我文件化能力的事實。

> [!IMPORTANT]
> **規格驅動開發** <!-- term:SpecDrivenDevelopment --> (Spec-Driven Development): 以規格文件為基準約束程式碼行為，確保實作與規格始終對齊的開發方法。 <!-- anchor:SpecDrivenDevelopment -->


過渡計畫被組織為五個階段。第零階段（逆向工程知識庫）和第一階段（建立編碼標準）已在先前完成。第二階段（治理重構）是本次工作的主體——技能到規則的遷移、元規則建立、以程式碼為文件 <!-- term:CodeAsDocumentation -->規則的建立。第三階段（消解知識庫）的驗證指標是知識庫條目的縮減而非文件的增長——方向是吸收、就近放置、標記跨切或標記過時。第四階段是工程端能做的最後一件事：將無法消解的跨切條目轉換為規格輸入範例，交給外部團隊。第五階段需要外部規格 <!-- term:Specifications -->輸入，工程端無法單方面啟動。

**知識沉澱工具**（Knowledge Precipitation） <!-- term:KnowledgePrecipitation -->的核心功能——寫入知識庫——與知識庫作為債務的新定位產生了衝突。這個衝突被刻意延後解決而非提前修改，遵循不做投機設計的原則。衝突被登記為第四階段的**前置條件**（Prerequisite） <!-- term:Prerequisite -->：第三階段期間工具仍可寫入知識庫（新增條目成為第四階段的規格素材），第四階段開始前必須改變輸出路由。

> [!IMPORTANT]
> **知識沉澱工具** <!-- term:KnowledgePrecipitation --> (Knowledge Precipitation): 將知識沉澱到專案文件或知識庫的過程或工具 <!-- anchor:KnowledgePrecipitation -->
> **前置條件** <!-- term:Prerequisite --> (Prerequisite): 執行某項開發活動之前必須滿足的準備工作或狀態。 <!-- anchor:Prerequisite -->


跨 session 連續性的最終驗證確認了理解路徑的完整性：project instructions 是唯一入口，宣告治理階層指向元規則、宣告工程標準指向規則檔案、宣告過渡計畫指向過渡文件、宣告知識庫查找順序 <!-- term:DiscoveryRule -->引用過渡文件的階段演進表。新 session 無需先備知識，所有指引可達。

## 決議

| # | 決策 | 原因 |
|---|------|------|
| 1 | Level 0 保持最小化 | 快速發展期——膨脹的 Level 0 造成修改瓶頸（需要擴展規則授權） |
| 2 | 四個偽技能重分類為規則 | 技能 = 產出成品 + 事件驅動；規則 = 始終啟用 + 不產出成品 |
| 3 | 知識庫 = 債務指標 <!-- term:DebtIndicator -->，非永久知識 | **絞殺者模式**（Strangler Pattern） <!-- term:StranglerPattern -->應用於文件——每份條目代表程式碼自文件化能力的缺口 |
| 4 | Level 2（規格）是外部輸入 | 逆向工程產出的內容描述「現況」而非「應然」——只有外部團隊能提供權威規格 |
| 5 | 過渡階段追蹤知識庫消解，非 README 建立 | 指標是知識庫縮減而非文件增長 |
| 6 | 擴展規則 3：短生命週期路徑不得存放長生命週期準則 <!-- term:Guidelines --> | 將生命週期錯配教訓形式化 |
| 7 | 查找順序 <!-- term:DiscoveryRule -->階段相依 | 靜態查找順序 <!-- term:DiscoveryRule -->會與跨階段演進的知識位置衝突 |
| 8 | 元規則放置於路徑範圍規則 | 精準觸發——僅在編輯規則檔案時自動載入 |
| 9 | 知識庫保持可見（非隱藏目錄 <!-- term:DotPrefix -->） | 性質接近專案文件，非工具配置 |
| 10 | precipitate 衝突延後解決 | 不做投機設計——登記為第四階段前置條件 <!-- term:Prerequisite --> |

> [!IMPORTANT]
> **絞殺者模式** <!-- term:StranglerPattern --> (Strangler Pattern): 逐步替換遺留系統的架構模式 <!-- anchor:StranglerPattern -->


## 技術啟示

1. **單體指令檔的極限是結構性的，不是容量性的。** 問題不在於檔案太長，而在於不同性質的內容（約束、工具、知識）需要不同的強制機制和生命週期。拆分必須沿著性質邊界進行，而非沿著主題邊界。

2. **分類測試優於分類標籤。** 與其用標籤標記文件類型再依標籤決定處置方式，不如建立首次匹配 <!-- term:FirstMatch -->的測試流程——測試本身就是定義，消除了標籤和定義不同步的風險。

3. **債務視角翻轉知識庫的價值判斷。** 當知識庫從「資產」變成「債務指標 <!-- term:DebtIndicator -->」，增長不再是好事。每新增一筆條目都代表一個程式碼無法自我表達的缺口，而消解一筆條目才是進步。

4. **過渡計畫需要明確的外部依賴邊界。** 工程端能做的事有清晰的上限——將逆向工程知識轉化為規格輸入範例是最後一步。跨越這個邊界需要外部權威的介入，承認這一點比假裝自給自足更務實。

5. **階段相依的規則比靜態規則更精確但更脆弱。** 查找順序 <!-- term:DiscoveryRule -->隨階段演變解決了靜態規則與演進現實的衝突，但引入了一個新的維護責任——每次階段轉換都必須更新查找順序 <!-- term:DiscoveryRule -->。過渡文件成為這個同步的唯一真實來源。

6. **衝突登記優於投機修改。** 發現設計衝突（如知識沉澱工具 <!-- term:KnowledgePrecipitation -->與知識庫新定位的矛盾）時，記錄衝突並標記解決時機比提前修改更安全——提前修改是在為尚未發生的情境做投機設計，而衝突的最佳解決方案往往需要實際情境的驗證。