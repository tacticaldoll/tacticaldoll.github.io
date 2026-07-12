+++
title = "Token Namespace Collision：LLM 協作環境的命名空間約束"
date = "2026-03-24T23:30:05+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "深入分析通用詞彙被多重定義時產生的命名空間碰撞與無線電同頻干擾現象，為 AI 指引提供實用的去雙語化與命名空間隔離約束。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "AI 代理人", # term:AiAgent
    "同頻干擾", # term:CoChannelInterference
    "反思", # term:Reflection
    "正面描述", # term:PositiveDescription
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

在一份 legacy code 考古 skill 的審查過程中，使用者在 IDE 裡選中了 `context` 這個詞，問了一個看似簡單的問題：「為何裡面仍有提到 context？」

當時 `context` 在 skill 文件裡出現了三次，每一次都是普通的英文用法 — `"isolated context"`、`"input context"`、`"surrounding context"`。跟專案裡某個同名目錄毫無關係。

但使用者的直覺指向一個更深層的問題：**在 LLM 的 attention mechanism 裡，「毫無關係」這件事不成立。** 同一個 token 的所有出現位置，無論語意是否相同，都會互相吸引 attention weight。這不是語意理解的失敗 — 這是 Transformer 架構的物理特性。

這篇文章從這個觀察出發，系統化分析 token 層級的命名碰撞問題，並提出 LLM 協作環境下的命名約束原則。

## 分析

### 碰撞的機制

Transformer 的 self-attention 對每個 token 計算 Query × Key 矩陣。兩個位置的 key embedding 越相似，attention weight 越高。同一個詞在不同位置的 embedding 高度相似 — 即使上下文賦予了不同的語意。

假設一份 skill 文件裡有這三行：

```
Line 35: "...from source code, never from knowledge-base documents..."
Line 103: "...Step 2.5 as input context..."
Line 136: "...(7 agents, isolated context)..."
```

三個位置的 `context` token embedding 相似度極高。Attention mechanism 讓它們互相參照。但問題不僅止於此 — 同一個 attention window 裡還有：

- System prompt 裡的 `"context window"` 相關指令
- 專案設定檔裡的同名目錄路徑引用
- 其他 skill 定義裡的 `"context"` 字樣

所有這些 `context` token 形成一個 attention cluster，互相拉扯。一個本意是「附近幾行」的 `"surrounding context"` 會意外提高 LLM 對同名目錄的注意力 — 這是可觀測的行為偏移，不是理論推測。

### 碰撞的嚴重性因素

並非所有同形詞碰撞都同樣嚴重。三個因素決定影響程度：

**頻率** — 這個詞在 skill 或 rule 文件中出現幾次？出現 10 次的詞比出現 1 次的詞產生更強的 cluster 效應。

**權重** — 這個詞在 system prompt 或 tool protocol 裡是否有特殊地位？`system`、`user`、`assistant` 是 message role 標記，每條訊息都帶，具有極高的 base attention weight。

**曝光量** — 這個詞是目錄名還是內文偶爾出現？目錄名出現在每個路徑引用裡（`knowledge/api/tech/routing.md`、`knowledge/module-a/backlog.md`...），曝光量遠高於內文中偶爾的一次使用。

將這三個因素相乘，可以得到一個簡單的嚴重性估計：

```
嚴重性 ≈ 頻率 × 權重 × 曝光量
```

### 碰撞詞分級

依據上述框架，可以將常見的碰撞詞分為三級。

**高碰撞** — 在幾乎每個 prompt 都大量出現的 LLM 基礎設施詞彙：

| 詞彙 | 基礎設施含義 | 專案常見用途 |
|------|-------------|------------|
| `context` | context window | 知識庫目錄 |
| `system` | system prompt / system message | 系統設定 |
| `user` | user message role | 使用者資料 |
| `assistant` | assistant message role | 助理功能 |
| `role` | message role | 角色權限 |
| `message` | conversation message | 訊息物件 |

這些詞的 base attention weight 極高，因為它們在每一輪對話的 message header 中反覆出現。用它們做目錄名或檔名等於在每個路徑引用裡疊加一次干擾。

**中碰撞** — 在 tool use 和 agent 架構中頻繁出現的詞彙：

| 詞彙 | 基礎設施含義 | 專案常見用途 |
|------|-------------|------------|
| `tool` | tool use protocol | 工具目錄 |
| `agent` | sub-agent spawning | 代理程式 |
| `memory` | persistent memory | 記憶體/快取 |
| `prompt` | prompt engineering | 提示文字 |
| `model` | LLM model selection | 資料模型 |
| `output` | model output | 輸出目錄 |
| `input` | model input | 輸入資料 |
| `token` | tokenization unit | 認證 token |

**低碰撞** — 偶爾出現，通常能從語境區分：

| 詞彙 | 基礎設施含義 | 專案常見用途 |
|------|-------------|------------|
| `instruction` | instruction-following | 指令文件 |
| `response` | API response | HTTP 回應 |
| `completion` | text completion | 完成狀態 |
| `function` | function calling | 程式函式 |
| `parameter` | function parameters | 參數 |

低碰撞詞通常不需要迴避 — LLM 對程式碼裡的 `function` 和 tool protocol 裡的 `function calling` 有足夠的上下文線索來區分。

### 類比框架

這個現象在其他領域有精確的對應，有助於理解其本質和解法。

**無線電的**同頻干擾**（Co-Channel Interference） <!-- term:CoChannelInterference -->。** 兩個電台在同一頻率廣播，接收器收到疊加訊號，無法分離各自的內容。LLM 的 attention 就是接收器，同一個 token 就是同一個頻率。解法與無線電相同：分頻（用不同的詞）、分時（出現在不同段落）、或方向性天線（agent 隔離，只接收相關內容）。

> [!IMPORTANT]
> **同頻干擾** <!-- term:CoChannelInterference --> (Co-Channel Interference): 無線電通信中多個電台使用相同頻率導致訊號無法分離的干擾現象，在 AI 協作中指同形 Token 在 Attention 機制中相互吸引拉扯造成行為偏移。 <!-- anchor:CoChannelInterference -->


**程式語言的 Variable Shadowing。** 程式語言用 scope 解決命名碰撞 — 內層 scope 的變數遮蔽外層同名變數。但 LLM 沒有 scope。整個 attention window 是一個 flat namespace，所有同名 token 同時可見，永遠在互相 shadow。程式語言在幾十年前就解決了命名碰撞，但 LLM prompt engineering 還沒有等價的 scoping 機制。

**C Preprocessor Macro Pollution。** 當第三方 library 的 header 裡 `#define model void*`，你的 code 裡 `struct model { ... }` 就會被 macro 展開成無意義的東西。LLM 的 system prompt 就像一組全局 `#define` — 它為 `context`、`tool`、`system` 等詞設定了隱性語意。專案檔案裡的同名詞被這些隱性定義干擾，只是不會報編譯錯誤，而是默默偏移行為。

**DNS **命名空間碰撞**（Namespace Collision） <!-- term:NamespaceCollision -->。** `.dev` 曾被開發者隨意用作本地域名，直到 Google 註冊了 `.dev` 頂級域名。本地的 `myapp.dev` 和公網的 `myapp.dev` 碰撞。LLM 的 token space 沒有「頂級域」的治理機構 — `context` 被 Anthropic/OpenAI 的 API protocol 和專案同時「註冊」，沒有機制防止碰撞。

> [!IMPORTANT]
> **命名空間碰撞** <!-- term:NamespaceCollision --> (Namespace Collision): 專案命名（如目錄、變數）與 AI 基礎設施或 Tool 協定所使用的高權重詞彙重疊，導致 Attention 機制產生意外交叉參照與行為偏移的現象。 <!-- anchor:NamespaceCollision -->


## 結論

### 排除清單是反模式

這個發現的一個直接推論是：**排除清單本身會注入碰撞**。

「不要讀某個目錄」這條排除規則把該目錄名注入了 prompt。每一條排除聲明都在 attention space 裡多一次碰撞詞的出現。這與 Wegner（1987）的 Ironic Process Theory 一致 — 刻意壓制一個想法反而讓它更頻繁浮現。

正確的做法是**正面描述**（Positive Description） <!-- term:PositiveDescription -->允許的集合：「只讀 `src/*.c` 和 `include/*.h`」— 碰撞詞從未出現，零干擾。這比列舉所有被排除的對象更乾淨，也更短。

> [!IMPORTANT]
> **正面描述** <!-- term:PositiveDescription --> (Positive Description): 在引導 AI 時採用正面列舉允許集合的描述方式，避免使用排除清單將被排除項目的 Token 意外引入注意力空間。 <!-- anchor:PositiveDescription -->


### DDD Ubiquitous Language 的 LLM 時代修正

**領域驅動設計**（Domain-Driven Design） <!-- term:DomainDrivenDesign --> 提倡 Ubiquitous Language — 團隊對同一個詞有相同理解，避免溝通中的歧義。這在人類團隊有效，因為人能從語境區分多義詞。

> [!IMPORTANT]
> **領域驅動設計** <!-- term:DomainDrivenDesign --> (Domain-Driven Design): 指採用領域驅動架構（DDD），將邏輯與行為封裝於自描述領域實體中的結構化設計方法。 <!-- anchor:DomainDrivenDesign -->


但在 LLM 協作環境裡，這個原則需要一個修正：**專案的 ubiquitous language 不能與 LLM 的 infrastructure language 重疊。** DDD 沒有預見到這個約束，因為它假設所有對話參與者都是人類。當對話的參與者包含 LLM 時，需要額外考慮 attention mechanism 對同形詞的物理行為。

### 這不是所有碰撞都需要修復

判斷是否需要迴避的三個問題：

1. **這個詞會在 governance 文件中反覆出現嗎？** 目錄名出現在每個路徑引用裡，影響最大。內文偶爾一次，影響可忽略。

2. **這個詞在 system prompt 裡有特殊 attention weight 嗎？** `system`、`user`、`assistant` 是 message role 標記，attention 極強。`function` 在程式碼裡大量出現，但 LLM 能從語境區分。

3. **碰撞會導致可觀測的行為偏移嗎？** 如果用了碰撞詞但 LLM 的行為沒有偏移，就不需要修復。這是工程判斷，不是教條。

## 結論

Token namespace collision 是 LLM 協作環境中一個被忽視的設計約束。它不是語意理解的失敗，而是 Transformer attention mechanism 的物理特性 — 同形 token 必然互相吸引 attention weight，無論語意是否相同。

三條可行動的原則：

**命名時主動迴避 LLM 基礎設施詞彙。** 新建目錄、檔案、或 governance 文件中的反覆術語時，檢查是否與 LLM 常用詞碰撞。如果碰撞，選擇 domain-specific 的同義詞。

**用正面描述 <!-- term:PositiveDescription -->取代排除清單。** 排除清單把被排除的對象注入 attention space，是反模式。正面描述 <!-- term:PositiveDescription -->允許的集合更短、更乾淨、不注入碰撞詞。

**用 compound term 降低碰撞。** 當碰撞詞無法完全避免時，`data_model` 比 `model` 的碰撞度低 — compound term 的 embedding 與單詞的 embedding 有差異，降低了 attention 的交叉引用強度。

這些原則適用於新命名。對既有命名的改動需要另外評估成本效益 — 重命名一個被廣泛引用的目錄可能造成的 churn 超過碰撞帶來的干擾。

### 高碰撞詞替代建議

| 碰撞詞 | 替代建議 |
|--------|---------|
| `context` | `knowledge/`, `corpus/`, `domain/` |
| `system` | `platform/`, `infra/`, `host/` |
| `user` | `account/`, `operator/`, `principal/` |
| `model` | `schema/`, `entity/`, `blueprint/` |
| `tool` | `utility/`, `instrument/`, `kit/` |
| `agent` | `delegate/`, `worker/`, `daemon/` |
| `memory` | `store/`, `vault/`, `archive/` |
| `prompt` | `template/`, `blueprint/`, `cue/` |
| `output` | `artifact/`, `result/`, `product/` |
| `input` | `source/`, `feed/`, `intake/` |