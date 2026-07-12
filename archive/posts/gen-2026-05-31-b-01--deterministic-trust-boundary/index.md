+++
title = "確定性邊界即信任邊界：統計模型作為治理執行層的結構性限制"
date = "2026-05-31T18:00:01+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "分析規格驅動開發中統計模型（LLM）作為治理執行層的侷限性，探討為何 prompt 的調整無法消除機率性錯誤，並提出劃分確定性層與統計層以重建信任邊界的架構原則。"
tags = [
    "經驗報告", # term:ExperienceReport
    "AI 代理人", # term:AiAgent
    "確定性邊界", # term:DeterministicTrustBoundary
    "規格驅動開發", # term:SpecDrivenDevelopment
    "AI 治理", # term:AIGovernance
    "衝突封存", # term:Archive
  ]
series = ["SDD 治理運營：對齊確定性契約與統計執行層的閉環實踐"]
[ai_info]
    [ai_info.generation]
        model = "Claude Opus 4.6"
        agent = "Claude Code VSCode Extension 2.1.72"
    [ai_info.refinement]
        model = "Gemini 3.5 Flash"
        agent = "Antigravity IDE 2.0.4"
+++

---

<!--more-->

## Context

**規格驅動開發**（Spec-Driven Development） <!-- term:SpecDrivenDevelopment -->依賴一組工具鏈來維繫規格與實作之間的一致性。像 openspec、spec-kit 這類工具提供了 delta sync）、spec 生成等能力，讓規格不只是文件，而是開發流程中的可執行契約。

> [!IMPORTANT]
> **規格驅動開發** <!-- term:SpecDrivenDevelopment --> (Spec-Driven Development): 以規格文件為基準約束程式碼行為，確保實作與規格始終對齊的開發方法。 <!-- anchor:SpecDrivenDevelopment -->


這些工具鏈的核心引擎，越來越多建構在 LLM 之上。Command skill 負責解讀意圖並操作規格文件，生成器負責從需求文字產出結構化 spec，同步器負責比對程式碼變更與規格差異。表面上，這些操作被封裝在工具介面之後，使用者看到的是一個確定性的工作流程——輸入指令，產出結果。

但引擎是統計的。

---

## Incident

在一次 delta sync 操作中，同步器在合併規格差異時反覆帶入 orphan marker——指向已不存在的 spec section 或已過時的定義的殘留標記。這些 marker 在表面上像是正常的 spec 參照，不會觸發格式錯誤，也不會讓 CI 失敗。它們安靜地進入規格文件，直到下游引用斷裂時才被發現。

第一個反應是修改負責 delta sync 的 command skill。調整 prompt，增加「不要帶入過時參照」的指令，加上 few-shot 範例。執行，orphan marker 消失了——但下一次 sync 它又回來了，以不同的形態。

反覆修改 skill 四到五次。每次修改都有效一陣子，然後失效。有時是同一種 orphan marker 重新出現，有時是新的變體。Command skill 的行為就像一個有 95% 正確率的過濾器：多數時候它做對了，但你永遠無法確定這次是不是那 5%。

最終放棄修改 skill，改用一支 deterministic script 作為 linter。這支 script 做的事情很簡單：掃描規格文件中所有參照，比對實際存在的 section ID，標記不匹配的項目。沒有 prompt，沒有 token，沒有機率——純粹的字串比對與集合運算。

問題立即且永久地消失了。

---

## 分析

### 為什麼 Skill 失敗而 Script 成功

這不是 skill 寫得不好的問題。問題出在執行層的本質差異。

Command skill 的運作方式是：接收 context（當前 spec 內容、diff、指令），在 transformer 中計算 token 機率分佈，取樣產出新的 spec 內容。這個過程在每一步都有兩個不可消除的誤差來源：

**注意力窗口的局部性**。Transformer 在每一次推理中只看到 context window 內的資訊。**差量**（Delta） <!-- term:Delta --> sync 需要的全局一致性——「這個 ID 在整個 spec 體系中是否仍然存在」——超出了局部 context 的判斷範圍。模型可能看到 section A 引用了 section B，但如果 section B 的刪除發生在前一次 sync 且不在當前 context 中，模型沒有依據判斷這個引用已經失效。

> [!IMPORTANT]
> **差量** <!-- term:Delta --> (Delta): 相對於已存在規格基線的具體變化與修改項目。 <!-- anchor:Delta -->


**機率性輸出的不可歸零錯誤率**。即使提供了完美的 context，transformer 的輸出仍然是機率取樣。「不要帶入 orphan marker」這個指令在 prompt 中是一個 soft constraint——它提高了模型避免 orphan marker 的機率，但不能將機率推到 1.0。就像擲一顆加權骰子：你可以讓某個面出現的機率非常低，但你不能讓它變成零。

**決定性**（Deterministic） <!-- term:Deterministic --> script 不受這兩個限制。它掃描的是全局狀態（所有 spec 檔案的所有 ID），它的判斷是布林的（存在或不存在），它的結果是可重現的（同樣的輸入永遠得到同樣的輸出）。

> [!IMPORTANT]
> **決定性** <!-- term:Deterministic --> (Deterministic): 保證在相同的輸入與控制下，自動化管線每次執行所產出的文件結構與內容完全收斂一致的特性。 <!-- anchor:Deterministic -->


### 確定性分級

這個案例揭示了一個更一般的分類原則。治理操作可以沿著確定性軸分為三類：

| 確定性等級 | 操作性質 | 適合的執行層 | 範例 |
|-----------|---------|-------------|------|
| 高 | 結構一致性檢查 | deterministic script / CI gate | ID 參照完整性、格式合規、schema 驗證 |
| 中 | 模式判斷 | LLM + deterministic 驗證 | commit message 品質、命名慣例一致性 |
| 低 | 意圖理解 | LLM | 「這個 PR 的變更是否符合 spec 的意圖」 |

錯誤在於把高確定性需求的操作交給低確定性的執行層。Orphan marker 檢查是高確定性操作——答案是二元的（是 orphan 或不是）——但它被放在 LLM 這個低確定性執行層中執行。

### Script-as-Interface：信任邊界的重劃

修復 orphan marker 問題後，一個更深層的模式浮現。它不只適用於 linting，而是一種通用的架構原則：

**LLM 傳遞意圖，deterministic script 執行操作。兩者之間的介面就是信任邊界。**

這和 interface-driven design 是同構的。在物件導向設計中，interface 的作用是把「做什麼」和「怎麼做」分開——呼叫者不需要信任實作的內部細節，只需要信任介面的契約。同樣地，在 **AI 治理**（AI Governance） <!-- term:AIGovernance -->中：

> [!IMPORTANT]
> **AI 治理** <!-- term:AIGovernance --> (AI Governance): 規範 AI 在專案中行為與輸出品質的治理框架 <!-- anchor:AIGovernance -->


- LLM 負責判斷「應該做什麼」（意圖層）
- Script 負責執行「怎麼做」（操作層）
- 介面契約保證操作的確定性，無論意圖層的判斷品質如何波動

這個模式甚至適用於同一個 repo 內部。即使 LLM agent 有完整的檔案讀寫權限，寫入操作仍然應該經由 deterministic script 封裝。不是因為不信任 agent 的「能力」，而是因為不信任統計推論作為最終寫入層的確定性保證。

```
LLM（統計層）
  │
  │  意圖：「更新 spec-X 的 version 欄位為 2.1」
  │
  ▼
Script interface（信任邊界）
  │
  │  驗證：spec-X 存在、version 欄位存在、2.1 是合法版本號
  │  執行：確定性寫入
  │
  ▼
File system
```

如果 LLM 直接寫入，它可能在更新 version 的同時微調了旁邊的描述文字——因為 transformer 生成的是完整文本，不是差異補丁。Script 只改它被要求改的欄位，其餘不動。

---

## 省思

回看這個事件，最值得記錄的不是解法（用 script 取代 skill），而是解法出現之前的認知延遲。

反覆修改 skill 四到五次，每次都相信「這次的 prompt 調整會解決問題」。這個信念的基礎是一個未經檢驗的假設：LLM 的錯誤是可修復的——只要 prompt 夠好、context 夠完整、few-shot 範例夠精準，模型就能做到零錯誤。

這個假設是錯的。不是因為技術不夠成熟，而是因為統計模型的數學本質排除了零錯誤的可能性。P(error) > 0 對任何基於 transformer 的系統都成立，無論模型多大、prompt 多精緻、fine-tuning 多徹底。這不是工程問題，是數學事實。

認知延遲的代價不只是時間。每一次「修改 skill 然後觀察」的迭代，都強化了「問題在 skill 實作」的歸因框架，讓「問題在執行層選擇」這個正確歸因越來越難浮現。如果在第一次失敗後就問「這個操作需要的確定性等級是什麼？」，答案會立即指向 deterministic script。

這個認知模式可以泛化為一條檢查規則：

> 當一個 LLM-based 操作反覆失敗，且失敗模式在每次修正後以不同變體重現時，問題可能不在 prompt 或 context，而在操作的確定性需求超過了統計模型能提供的確定性上限。正確的修正不是改善模型的輸入，而是更換執行層。

---

## 結論

不管一個工具多成熟、多知名、多少團隊在生產環境中使用——只要它的核心引擎是 transformer，只要它的輸出是 token 機率分佈的取樣結果，它就有不可歸零的錯誤率。這不是缺陷，是性質。

信任邊界不應該畫在人與人之間、系統與系統之間、repo 與 repo 之間。它應該畫在確定性層與統計層之間。凡是需要 100% 正確性的操作——結構一致性、參照完整性、schema 合規——執行層必須是 deterministic code。LLM 的角色是判斷「該做什麼」，不是執行「怎麼做」。

這條原則的推論是：一個 SDD 工具鏈的可靠性，不取決於它的 LLM 引擎有多強，而取決於它在確定性操作和統計操作之間的邊界劃得多清楚。模型會進步，但 P(error) > 0 這個不等式不會被未來的模型推翻。架構設計不能建立在「未來模型夠好就不需要這條邊界」的假設上。

邊界是永久的。