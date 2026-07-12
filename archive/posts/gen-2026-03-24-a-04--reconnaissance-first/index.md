+++
title = "Reconnaissance-first：LLM Agent 多階段分析的分工模式"
date = "2026-03-24T23:30:04+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "分享在大型 C 語言函式庫考古中採用先偵察後挖掘（Reconnaissance-first）模式的實戰經驗，設計多階段分析與分工模式以有效降低 AI 代理人的認知負荷。"
tags = [
    "經驗報告", # term:ExperienceReport
    "AI 代理人", # term:AiAgent
    "類型標籤", # term:TypeLabel
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

在設計一個 legacy code 考古 skill 時，面臨了一個具體的問題：如何從一個大型 C function 中提取多個面向的行為事實（Entry & Dispatch、Parameters、Authorization、Core Logic、錯誤 Taxonomy、Side Effects、Response Contract）。

LLM 的 attention 是零和的 — softmax 把 attention weight 分配給 window 裡所有 token，對 A 的注意力增加必然意味著對 B 的注意力減少。一個 agent 同時追蹤 7 個目標，等於把有限的 attention budget 分成 7 份。微妙的行為在 7 個目標的競爭中容易被淹沒。

## 發現

### 第一階段：純隔離方案

最直觀的解法是分兵 — 7 個 agent 各負責 1 個 facet。每個 agent 的 attention 100% 聚焦在自己的目標上，精確度理論最大化。

為了效率，7 個 agent 分成 3 個 batch 平行執行（3 + 3 + 1）。每個 agent 收到：handler function 的行範圍、該 facet 專屬的 grep patterns（先縮窄範圍再精讀）、以及只屬於該 facet 的 checklist。

這個方案在一個假設下是最優的：**各面向互相獨立。**

### 第二階段：發現隱性資料流

使用者指出了一個關鍵問題：legacy C code 用 global variable 做跨階段的隱性通訊。

以某個 handler 為例，`g_is_alternate_path` 這個 global variable 在 Parameters 階段被設值（某個 check function 的回傳值），然後在 Authorization、Core Logic、錯誤 Taxonomy 都被讀取。它的值決定了：
- Authorization 檢查是走本地路徑還是遠端路徑
- 錯誤 response 用哪一組 serializer
- 路徑解析走哪一條分支

純隔離的 Authorization agent 看到 `if(g_is_alternate_path == 1)` 卻不知道這個值是在哪裡、什麼條件下被設成 1 — 因為那段 code 在 Parameters agent 的視野裡。

> [!NOTE]
> **Decision Point**: 純隔離方案在「各面向互相獨立」的假設下最優，但 legacy C code 的 global variable 打破了這個假設
> — Alternatives: (a) 放棄隔離，回到單 agent 掃描全部 → 精確度問題未解；(b) 在隔離前插入一個全局偵察階段 → 兼顧隔離的精確度和全局的連貫性
> — Outcome: 選擇 (b)，進入 hybrid 設計

這個問題不是 legacy C 的特例。任何有跨切面狀態的系統都會出現：微服務間的 shared database、React 的 context provider、Makefile 的 environment variable 跨 target 傳遞。只要有「在 A 設值、在 B 讀取」的隱性通道，純隔離的分析就會漏掉連接。

### 第三階段：Hybrid 設計

解法是在隔離之前插入兩個預處理階段，形成三層管線：

**第一層：Mechanical Extraction（Call Chain Index）。** 在任何 agent 讀 code 之前，用 grep 機械式提取 handler function 裡所有的 function call。這是零解釋的純模式匹配 — 產出一張表，列出每個 call 的行號、函式名、定義位置、和**類型標籤**（Type Label） <!-- term:TypeLabel -->。

> [!IMPORTANT]
> **類型標籤** <!-- term:TypeLabel --> (Type Label): 對程式碼元件或函式呼叫進行機械式分類的識別標記（如 validation、auth、syscall 等），用以輔助自動化靜態分析。 <!-- anchor:TypeLabel -->


> [!NOTE]
> **Decision Point**: 在 Recon agent 之前增加一個機械式 grep 步驟
> — Alternatives: 讓 Recon agent 自己在讀 code 時建立 call chain → Recon 的注意力會被 call chain 提取分散，影響 State Flow Map 的品質
> — Outcome: 獨立的 Mechanical Extraction 步驟讓 Recon 可以專注在 global variable flow

**第二層：Reconnaissance（State Flow Map）。** 一個 Recon agent 讀完整 function 一次，收到 Call Chain Index 作為輸入。這個 agent 不做任何 facet 分析 — 它只產出一份緊湊的 State Flow Map（上限 40 行），包含三個部分：

- Global Variables 表：哪個變數在哪一行被設值、在哪些行被讀取、用途是什麼
- `#ifdef` Branches 表：每個條件編譯分支影響的行範圍
- Execution Skeleton：純行號的執行流程骨架

**第三層：Per-Facet Agents。** 7 個隔離的 agent，每個收到 Call Chain Index + State Flow Map + 自己的 facet checklist + grep patterns。State Flow Map 讓每個 agent 知道「這個 global variable 是在別的地方設的，這是它被設值的條件」，而不需要自己去找。

三層的職責嚴格分離：Mechanical Extraction 不解讀，只列舉；Recon 不分析面向，只描繪結構；**Specialists** 不掃描全局，只深挖局部。

### 設計的驗證

這個 hybrid 結構解決了 `g_is_alternate_path` 的問題：Recon agent 在 State Flow Map 裡記錄了它在某行被設值、在多個後續位置被讀取。Authorization agent 看到 `if(g_is_alternate_path == 1)` 時，可以從 State Flow Map 得知這個值的來源，而不需要自己去讀 Parameters 的 code 段。

## 決議

| # | 決策 | 選項 | 結果 |
|---|------|------|------|
| 1 | 注意力分配策略 | 4 種（grep-first / single-pass / per-facet / hybrid） | 選 hybrid |
| 2 | 純隔離的假設檢驗 | 隔離 vs 全局 | 隔離假設不成立，需 Recon 補全局資訊 |
| 3 | Mechanical Extraction 獨立步驟 | Recon 自己做 vs 獨立 grep | 獨立，讓 Recon 專注 |

## 延伸知識

### 軍事 ISR 鏈

這個三層結構與軍事的 ISR（Intelligence, Surveillance, Reconnaissance）鏈一致。衛星/無人機提供機械式感測（地形圖、熱感影像），對應 Call Chain Index 的 grep 提取。偵察隊深入前線建立敵軍配置和移動路線，對應 Recon agent 的 State Flow Map。作戰分隊（步兵、砲兵、工兵）各自依據偵察報告執行專業任務，對應 Facet agents。

關鍵原則是：偵察隊不開火，作戰分隊不偵察。職責混合意味著兩件事都做不好。

### 編譯器的 Pass 架構

現代編譯器的管線是同一個模式的另一個實例。Lexing/Parsing 是機械式轉換（text → AST），不理解語意。Control Flow 分析 和 數據 Flow 分析 建立全局結構（CFG + reaching definitions），對應 Recon 的 State Flow Map。每個 Optimization Pass（dead code elimination、constant folding、loop unrolling）各自獨立執行，收到 CFG 和 data flow 的結果但不需要自己重建它們。

### 認知科學的 Chunking

George Miller（1956）發現人類工作記憶容量約 7±2 個 chunks。面對超過容量的資訊，人類的策略是先掃描全局建立 schema，再逐一深入每個 chunk。**結構合約**（Schema） <!-- term:Schema --> 讓 specialist 階段不需要重新掃描全局。LLM 的 attention window 容量不是 7±2，但原理相同：全局掃描和局部深挖不能高效地同時進行，必須分階段。

> [!IMPORTANT]
> **結構合約** <!-- term:Schema --> (Schema): 定義資料欄位、型別與排版限制的強型別規格定義，用於強制約束模型產出的格式。 <!-- anchor:Schema -->


### 注意力窗口的經濟學

Recon agent 消耗了一次完整讀取的 token — 這是成本。但如果沒有 Recon，7 個 facet agents 各自需要在自己的 window 裡「發現」跨切面狀態，每個 agent 都在做低效的全局掃描。Recon 把「需要全局視野的工作」集中在一個 agent 完成，是 attention 的分工經濟 — 用一次全局讀取的成本換取 7 次局部讀取的精確度。

## 技術啟示

**分析面向的獨立性不能假設，必須驗證。** 只要分析對象存在跨切面狀態（global variables、shared state、environment variables），純隔離的 agent 就會遺漏連接。獨立性是需要驗證的前提，不是可以假設的預設。

**三層管線：機械提取 → 偵察 → 專業分析。** 每一層只做一件事。Mechanical extraction 不解讀，Recon 不分析面向，Specialists 不掃描全局。職責混合會降低每一層的品質。

**Recon 的產出必須緊湊。** State Flow Map 超過 40 行就開始包含 facet 層級的細節，等於 Recon 變成了第 8 個 facet agent。Recon 的價值是提供結構，不是提供分析。

**機械步驟先於智力步驟。** Call Chain Index 用 grep 就能產出，不需要 LLM 的理解能力。把機械式的工作從 LLM agent 的 window 裡移出，讓 agent 專注在需要理解力的工作上。