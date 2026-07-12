+++
title = "分類 Dispatch 演進：Decorator Chain 語意斷裂的根因、三段取捨、與不可能三角"
date = "2026-03-27T18:30:01+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "剖析 GoF Decorator Pattern 在路徑解析與資源分類中的語意斷裂根因，探討集中式 Helper 模組到宣告式資料表的演進取捨，並揭示不 facade、不 god function、不分散分類的「不可能三角」。"
tags = [
    "經驗報告", # term:ExperienceReport
    "AI 代理人", # term:AiAgent
    "裝飾器鏈", # term:DecoratorChain
    "不可能三角", # term:ImpossibleTrinity
    "宣告式分派", # term:DeclarativeDispatch
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

一個系統需要將使用者提供的路徑解析為帶有操作行為的資源描述子。系統有 16 種資源類型——網路共享資料夾、ISO 掛載、檔案系統快照、外接裝置等——每種有不同的識別條件和操作行為。部分類型共享相同的路徑解析邏輯但 guard 條件不同；其他類型使用完全不同的路徑 scheme。

初始設計採用 GoF Decorator pattern 以 chain 方式部署。運作一段時間後，出現了一個不易察覺的問題：當系統問一個資源「你是什麼 kind？」時，ISO 掛載和檔案系統快照都回答 "readonly"——它們的身份被行為名稱覆蓋了。這就是語意斷裂。

本文記錄從發現這個問題到最終解決方案的三段演進，以及過程中浮現的結構性約束。

## 發現

### 第一幕：為什麼 Decorator Chain 會吞掉身份

**裝飾器鏈**（Decorator Chain） <!-- term:DecoratorChain --> 的結構是垂直與水平的疊加：鏈（水平）負責分類——依序嘗試每個 decorator 的 `try_resolve()`，第一個認領的勝出；嵌套（垂直）負責行為組合——外層 decorator 覆寫特定操作（例如寫入回傳唯讀錯誤），未覆寫的操作委派給內層。兩個方向各自是正確的——問題在於它們疊加在同一個介面上，而 `kind_name()` 也在這個介面上。

> [!IMPORTANT]
> **裝飾器鏈** <!-- term:DecoratorChain --> (Decorator Chain): GoF 裝飾器模式的鏈式部署結構，同時處理水平分類與垂直行為組合時易造成語意斷裂。 <!-- anchor:DecoratorChain -->


具體來說，ISO 掛載的組合是 `ReadonlyDecorator { inner: SyscallDecorator }`，快照的組合也是 `ReadonlyDecorator { inner: SyscallDecorator }`。當外部程式碼呼叫 `kind_name()` 時，最外層的 `ReadonlyDecorator` 回答 "readonly"——這是行為名稱，不是 kind 身份。ISO 和快照變得不可區分。

根因不是嵌套或鏈本身有缺陷，而是水平分類、垂直行為組合、身份查詢三個正交關注點被疊加在同一個抽象上。垂直方向的外層以行為命名，水平方向產生的 kind 身份就被遮蔽了。

> [!NOTE]
> **Decision Point**: 將 decorator 雙層介面拆為三個獨立關注點：操作 trait（純操作）、分類用的獨立函數、身份用的 enum
> — Alternatives: 在 decorator 介面上加 kind_name override — 治標不治本，每個 decorator 都要手動覆寫
> — Outcome: 身份問題解決，但引入了新的分散問題

### 第二幕：分散的代價

遷移解決了身份問題。每個 kind 有一個命名的 ops struct 和 1:1 對應的 enum variant。身份查詢從此回傳 "iso" 而非 "readonly"。

但分類函數被分散到每個 kind 檔案中，每個都自己寫路徑解析邏輯。某個 kind 有完整的三種路徑形式處理（相對路徑、symlink、絕對路徑），另一個 kind 手動重寫了路徑提取邏輯，卻只處理了其中一種形式——漏掉了另外兩種。

這不是個案。16 種資源類型中有 6 種是 share-based，它們共享相同的路徑解析邏輯但各自需要不同的 guard 條件（類型碼判斷、硬體抽象層呼叫）。如果每個 kind 都自己寫分類函數，就會有 6 份幾乎相同的路徑解析程式碼，每份都可能漏掉某個形式。

另一個問題是分類註冊表的順序隱式地控制了優先序。每個 kind 的分類函數看似自包含，但實際上它能不能成功認領取決於它在陣列中的位置。這種「自包含是假象」的狀況讓維護者難以推理。

> [!NOTE]
> **Decision Point**: 將路徑解析集中為共用 helper 模組，kind 只保留 ops + build
> — Alternatives: 保留各 kind 的分類函數但抽取共用 helper — 仍有分散判斷，半集中半分散
> — Outcome: 路徑解析一致性問題消除，遺漏的路徑形式覆蓋缺口修復

### 第三幕：集中到什麼程度？

確定要集中路徑解析後，下一個問題是分類規則本身要不要也集中。

最初的提案是 helper + 分散 guard：共用解析器統一路徑解析，但每個 kind 仍有自己的 guard 函數。Catch-all fallback kind 需要顯式化——從隱式「排最後」變成程式碼中的一行顯式呼叫。

> [!NOTE]
> **Decision Point**: 完全消解各 kind 的分類函數——kind 不持有任何「是不是我」的邏輯，分類規則集中為 dispatch 模組中的**宣告式**（Declarative） <!-- term:Declarative -->資料表
> — Alternatives: kind 自註冊（guard 作為 const 從 kind 檔案 export，dispatch 模組收集引用）— kind 更自描述但分類知識仍跨兩處；保留各 kind 的 guard 函數 — 仍有分散判斷
> — Outcome: Kind 檔案瘦身為純 ops + build（thin facade），分類規則一張表可審計

> [!IMPORTANT]
> **宣告式** <!-- term:Declarative --> (Declarative): 一種編程或治理正規，僅描述預期達成的狀態或目標，將具體執行與自癒細節委派給底層實體或系統。 <!-- anchor:Declarative -->


最終設計是兩階段宣告式 <!-- term:Declarative --> dispatch：pattern 表處理前綴/包含模式匹配（用於 pattern-based kind），guard 表處理 share-based kind 的 metadata predicate 條件，預設 share kind 是顯式 fallback。

規模推演支持這個選擇。16 種 kind 全啟用後：decorator chain 需要 16 個 decorator struct 加上複雜的 wrapping 拓撲；分散分類函數會有多份路徑解析複製；而 data table 只是 ~20 行表條目，每行一個 pattern 或 guard。

> [!NOTE]
> **Decision Point**: 兩張表分離——pattern 規則（字串模式）和 share guard（metadata predicate）用不同結構
> — Alternatives: 統一規則 enum 包裝兩種匹配機制 — 過度抽象，兩族的匹配簽名根本不同
> — Outcome: 各自結構清晰，新增 kind 只需在正確的表加一行

### 尾聲：命名精確度的意外收穫

實作完成後，review 發現新建的模組檔名沿用了被消解的分類概念。重命名後又發現它跟既有的 kind 模組在語意上模糊——兩者都跟同一個領域詞有關但職責不同。經過三次命名才選定精確對應其所含 struct 的名稱。

這個三次命名的過程推導出一條原則：檔案名必須精確反映其單一職責，不得與同層其他模組產生歧義。型別名稱應與所在檔案名對應。參數名必須跟隨結構變更——函數簽名中的舊術語殘留會產生語意殘影。

## 決議

| # | Decision | Rationale | Alternatives Rejected |
|---|----------|-----------|----------------------|
| D1 | Decorator 介面拆為操作 trait + 分類函數 + 身份 enum | 三個正交關注點不應共用一個介面 | 在 decorator 介面上加 kind_name override |
| D2 | 路徑解析集中為共用 helper | 6 個 share-based kind 共用相同邏輯，分散複製導致遺漏 | 保留各 kind 分類函數 + 抽取共用函數 |
| D3 | 完全消解各 kind 分類函數，集中為宣告式 <!-- term:Declarative -->表 | 分類函數的「自包含」是假象，順序是全局知識 | Kind 自註冊；保留各 kind guard 函數 |
| D4 | 兩張表分離（pattern 規則 + share guard） | 兩族匹配機制根本不同 | 統一規則 enum |
| D5 | Catch-all kind 顯式 fallback | catch-all 語意不同於 guard；顯式一行比隱式排最後更清楚 | 將 catch-all 加入 guard 表尾部 |

## 補充知識

### 不可能三角

三段演進揭示了一個結構性約束：**不 facade、不 god function、不分散分類**三個目標不可能同時滿足。

| | 不 facade | 不 god fn | 不分散分類 |
|---|:---:|:---:|:---:|
| Decorator chain | ✓ | ✓ | ✗ |
| Self-registration | ✓ | ✓ | ✗ |
| God function | ✓ | ✗ | ✓ |
| 數據 table | ✗ | ✓ | ✓ |
| ADT dispatch | ✗ | ✓ | ✓ |

這個三角的封閉條件取決於語言能力。在缺乏型別探索或反射機制的語言中（如 Rust），分類規則無法自動從 kind 定義中收集，必須手動註冊——手動註冊就是某種形式的集中。具備 annotation scanning 的語言（Java、C#）可以接近打破這個三角：分類規則作為 annotation 附著在 kind 上，framework 自動掃描收集，kind 保持自包含但分類仍可一次審計。

在靜態 dispatch 語言的約束下，data table 選擇犧牲自包含性（kind 變為 thin facade），這是代價最低的取捨——kind 檔案仍然 1:1 對應、仍然自描述、build 函數仍然在 kind 檔案中。

### 規模退化矩陣

| 方案 | 4 kind（現行） | 16 kind（全啟用） | 退化模式 |
|------|:---:|:---:|---|
| Decorator chain | 4 decorator + 簡單 wrapping | 16 decorator + 複雜拓撲 | wrapping 組合爆炸 |
| 分散分類函數 | 4 份路徑解析 | 16 份路徑解析（6 份幾乎相同） | 複製 → 遺漏 |
| 數據 table | ~8 行表 | ~20 行表 | 線性增長，可控 |

## 技術啟示

**垂直水平疊加是語意斷裂的根因。** 嵌套（垂直行為組合）和鏈（水平分類）各自正確，疊加在同一介面上才出問題。當一個抽象同時承擔水平分類、垂直行為組合、身份查詢三個職責時，垂直方向的外層命名（通常按行為）會遮蔽水平方向產生的身份。

**「自包含」可能是假象。** 每個 kind 擁有自己的分類函數看似自包含，但註冊表的順序隱式控制了誰能認領。真正的獨立性需要排除全局依賴——而分類優先序天生就是全局知識。

**分類全局性是不可逃避的約束。** 無論用什麼模式，分類規則的互斥和優先順序是全局知識。任何正確的方案都需要某種形式的集中——差別只在表達方式（imperative if-else、declarative table、type-level dispatch）和身份保留方式。

**命名必須跟隨結構變更。** 消解一個概念後，沿用其術語會在程式碼中留下語意殘影。檔案名、型別名、參數名都是語意的載體——它們的精確度直接影響後續開發者（和 AI agent）的理解。