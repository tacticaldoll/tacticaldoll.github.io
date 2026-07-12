+++
title = "回饋迴路：從 Open-Loop 治理到 Closed-Loop 觀測"
date = "2026-05-31T18:00:03+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "系統性設計規格驱动開發的閉環觀測與回饋迴路，將觀測區分為規則遵守率、規則有效性與治理摩擦成本三個層次，並指出治理決策最終必須保留人在迴路中的判斷本質。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "AI 代理人", # term:AiAgent
    "回饋迴路", # term:FeedbackLoop
    "AI 治理", # term:AIGovernance
    "確定性邊界", # term:DeterministicTrustBoundary
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

## 背景

SDD 治理面臨兩個已知的結構性問題：統計模型作為執行層的確定性天花板，以及**耦合系統**（Coupled System） <!-- term:CoupledSystem -->中回滾即衝突的困境。兩者的結論都指向同一個缺口——觀測。

> [!IMPORTANT]
> **耦合系統** <!-- term:CoupledSystem --> (Coupled System): 由程式碼與規格文件等相互依賴、協同演化的元件所構成的系統，其特點是任何局部變更或回滾皆可能引發全局或關聯性的語意衝突。 <!-- anchor:CoupledSystem -->


**確定性邊界**（Deterministic Trust Boundary） <!-- term:DeterministicTrustBoundary -->的劃分需要知道哪些操作正在被統計層錯誤地執行；衝突的即時處理需要知道漂移正在發生；恢復策略的選擇需要知道影響範圍。這些「知道」都預設了一個觀測機制的存在。但在多數 SDD 實踐中，這個機制要麼不存在，要麼是事後的——問題被發現時，已經擴散。

> [!IMPORTANT]
> **確定性邊界** <!-- term:DeterministicTrustBoundary --> (Deterministic Trust Boundary): 在系統設計中，劃分確定性執行層（如腳本、CI）與統計推論層（如大語言模型）的介面契約，以確保關鍵操作的 100% 正確性。 <!-- anchor:DeterministicTrustBoundary -->


治理機制的設計已經有了大量的實踐積累。但治理機制的運營——它有效嗎？它的成本合理嗎？它應該收緊還是放寬？——幾乎沒有被系統性地處理。所有治理都在 open-loop 中運行：設定規則，執行規則，但不觀測規則的效果。

這篇報告處理閉環的最後一塊：**回饋迴路**（Feedback Loop） <!-- term:FeedbackLoop -->的設計。

> [!IMPORTANT]
> **回饋迴路** <!-- term:FeedbackLoop --> (Feedback Loop): 用於持續觀測治理機制運營效能的閉環系統，通常包含規則遵守率、規則有效性與治理摩擦成本三個觀測層次，藉以驅動治理規則的動態調整。 <!-- anchor:FeedbackLoop -->


---

## 分析

### Lint 不是迴路

一個常見的誤解是把 lint 等同於回饋迴路 <!-- term:FeedbackLoop -->。以 delta sync 中的 orphan marker 為例——用 deterministic script linter 取代 LLM skill 確實解決了即時檢測的問題。但 lint 是迴路中的一個組件，不是迴路本身。

區別在於 lint 回答的是「這次有沒有問題」，而迴路回答的是「這個機制整體上是否在運作」。

```
Lint：  input → check → pass/fail
         （單次，局部，二元結果）

迴路：  機制運行 → 觀測效果 → 度量 → 判斷 → 調整機制
         （持續，全局，方向性決策）
```

具體地說，lint 不回答以下問題：

- **Orphan marker 在被 linter 攔截之前，平均在 spec 中存活了多久？** 如果答案是「三週」，那 linter 的部署位置可能需要前移——從 CI 提前到 pre-commit hook。
- **檢查工具**（Linter） <!-- term:Linter --> 的 false positive 率是多少？開發者因為 false positive 而忽略 linter **警告**（Warning） <!-- term:Warning -->的頻率是多少？ 如果 false positive 率高到開發者開始習慣性地跳過警告 <!-- term:Warning -->，linter 的實際效用遠低於帳面攔截率。
- **自從部署 linter 以來，command skill 產生 orphan marker 的基礎率有沒有變化？** 如果 LLM 模型升級後 orphan marker 的基礎率已經下降到 0.1% 以下，linter 的維護成本是否仍然合理？

> [!IMPORTANT]
> **檢查工具** <!-- term:Linter --> (Linter): 在開發期或持續整合管線中，用以靜態掃描程式碼並揪出風格或語法錯誤的工具。 <!-- anchor:Linter -->
> **警告** <!-- term:Warning --> (Warning): 術語審計中指出的潛在問題或警告 <!-- anchor:Warning -->


這些問題的共同特徵是：它們不是關於單次執行的正確性，而是關於治理機制本身的效能演化。回答它們需要跨時間的聚合數據，不是單次的 pass/fail。

### 觀測的三個層次

回饋迴路 <!-- term:FeedbackLoop -->的觀測可以分為三個層次，每個層次觀測的對象和所需的工具不同：

**第一層：規則遵守率（deterministic 可測）**

這一層回答的是「規則有沒有被遵守」。它的度量指標是可以用 deterministic script 計算的：

- 治理規則被繞過的次數（例如 `--no-verify` flag 的使用頻率）
- 檢查工具 <!-- term:Linter --> 攔截率（攔截數 / 總執行數）
- **spec-code** 不一致的數量（deterministic diff 可以計算）
- 歷史封存 操作的頻率與時機（是主動歸檔還是被漂移逼著歸檔）

這些指標的特性是客觀、可自動化、可做趨勢分析。它們構成迴路的基礎數據層。

**第二層：規則有效性（需要人判斷）**

規則被遵守不等於規則有效。這一層回答的是「遵守規則之後，品質有沒有變好」。

- **約束性規格**（Spec） <!-- term:Spec --> 經過 review 後仍然在實作階段被發現有缺陷的比率。如果 review 通過的 spec 仍然頻繁出問題，review 流程本身可能需要調整。
- 從漂移發生到被偵測的平均時間（MTTD）。這個指標衡量的是觀測機制的延遲，不是規則的品質。
- 恢復操作的成本（花了多少時間做 forward-fix / 影響了多少人的工作）。如果恢復成本持續上升，可能意味著耦合度正在增加，需要重新評估模組邊界。

> [!IMPORTANT]
> **約束性規格** <!-- term:Spec --> (Spec): 以結構化或機器可讀格式定義的系統或 API 合約規範。 <!-- anchor:Spec -->


這些指標中有些可以半自動化，但「品質有沒有變好」的判斷最終需要人來做。

**第三層：治理的摩擦成本（最難觀測）**

治理有效不等於治理值得。這一層回答的是「治理帶來的價值是否大於它造成的阻力」。

- 開發者花在滿足治理要求上的時間佔比
- 因為治理流程而被延遲的交付
- 「合規但空洞」的比率——格式上符合要求但語意上沒有資訊量的 artifact

第三層幾乎不可能用 deterministic 方法度量。「這份 spec 是真正有價值的還是只是為了合規而存在」是一個語意判斷，而語意判斷正是前述報告中分類為低確定性的操作。諷刺的是，觀測治理效果的最深層問題，恰好落在統計模型的能力範圍內——但這意味著觀測本身有統計模型的確定性天花板。

### 迴路的閉合：從觀測到決策

觀測產生數據，但數據不是決策。迴路的閉合需要一個從數據到行動的決策框架。

在 SDD 治理的語境下，決策的核心問題只有三類：

**收緊還是放寬？** 某條規則的攔截率很高，可能意味著它很有效（攔住了很多問題），也可能意味著它太嚴格（製造了很多 false positive）。單看攔截率無法區分這兩種情況。需要同時看第二層的「被攔截後修正的問題中，有多少確實會造成下游影響」。

**Probabilistic 降級為 deterministic？** 前述報告中 command skill 被 script linter 取代，就是一次降級決策。觸發降級的訊號是：某個 LLM-based 操作的失敗率在多次 prompt 調整後仍然不收斂。觀測到「失敗率不收斂」這個模式，是降級決策的前提。

**Workaround 升級為正式治理？** Script linter 最初是一個繞過 skill 的 workaround。它應該停留在 workaround 狀態（個人使用，不進 CI），還是升級為正式治理機制？決策依據是它的效果是否可泛化——如果只有一個人需要它，它是 workaround；如果所有人都在產生同類問題，它應該是基礎設施。

### 迴路本身的分層

回到核心公理：確定性需求和執行層要匹配。觀測迴路本身也需要分層：

```
觀測層              適合的執行方式          產出
──────────────────────────────────────────────────
規則遵守率           deterministic script    dashboard / alert
規則有效性           半自動 + 人判斷        定期 review report
治理摩擦成本         人判斷（LLM 輔助）     季度回顧決策
```

第一層可以且應該完全自動化。它是 lint 的延伸——不是單次檢查，而是聚合統計。一支 script 定期掃描 commit 歷史、CI 記錄、archive 操作日誌，產出趨勢圖表。這不需要 LLM，不需要判斷，只需要計數和時序分析。

第二層需要人定期檢視第一層的數據，結合實際開發經驗做判斷。這是一個 review 活動，適合放在團隊的定期回顧（sprint retro、月度 review）中。LLM 可以輔助——例如從大量的 issue 記錄中摘要出反覆出現的問題模式——但判斷本身不能委託給 LLM。

第三層是策略性的，頻率最低，影響最大。它決定的是治理機制的增減，需要對團隊的工作方式有整體理解。這是管理決策，不是工程決策。

---

## 省思

回看整個系列的脈絡，一個完整的治理運營週期浮現：

```
設計信任邊界（確定性邊界）
  → 邊界劃定後，在邊界內運行
     → 運行中產生耦合衝突（衝突與封存）
        → 衝突處理中產生漂移
           → 漂移的偵測需要觀測（回饋迴路）
              → 觀測結果回饋修正信任邊界的劃定
                 → 回到起點，但帶著新的數據
```

這個週期和傳統的 PDCA（Plan-Do-Check-Act）有表面的相似性，但有一個關鍵差異：在 **AI 治理**（AI Governance） <!-- term:AIGovernance -->中，**Check 和 Act 本身受到統計模型的確定性天花板限制**。你不能用 LLM 來可靠地判斷 LLM 治理是否有效——這是一個自指問題。觀測的 deterministic 層（規則遵守率）可以自動化，但觀測的 probabilistic 層（規則有效性、摩擦成本）需要人在迴路中。

> [!IMPORTANT]
> **AI 治理** <!-- term:AIGovernance --> (AI Governance): 規範 AI 在專案中行為與輸出品質的治理框架 <!-- anchor:AIGovernance -->


這意味著 AI 治理 <!-- term:AIGovernance -->的回饋迴路 <!-- term:FeedbackLoop -->不可能完全自動化。它可以被大幅度地工具化——自動收集數據、自動產出報表、自動標記異常——但最終的「這條規則該留還是該廢」的判斷，必須由理解治理目的的人來做。

這不是技術限制的遺憾，而是治理本質的體現。治理不是演算法——它是一組持續演化的社會性契約，由人制定，為人服務。工具可以讓這個契約的執行和觀測更精確，但契約的設計和修訂不能外包給工具。

---

## 結論

沒有回饋迴路 <!-- term:FeedbackLoop -->的治理是 open-loop 控制——設定參數，期望結果，但不驗證結果。Open-loop 控制在穩定環境中可以運作，但 SDD 的環境不穩定：模型在升級，團隊在變化，專案的耦合度在演化。Open-loop 治理在這個環境中會逐漸偏離目標，而偏離的累積直到產生事故才被發現。

回饋迴路 <!-- term:FeedbackLoop -->的建設分三層：deterministic 的規則遵守率觀測（可自動化），半自動的規則有效性評估（需要人定期檢視），以及策略性的治理摩擦成本判斷（管理決策）。三層各有適合的工具和頻率，不能混為一談。

SDD 治理的運營框架由三個互相支撐的機制構成：確定性邊界 <!-- term:DeterministicTrustBoundary -->劃分可信的執行層，衝突管理和封存策略應對不可避免的漂移，回饋迴路 <!-- term:FeedbackLoop -->觀測治理機制本身的效能並驅動迭代修正。三者的共同前提是同一條公理：統計模型有不可歸零的錯誤率，治理架構必須將確定性需求與執行層的確定性能力對齊。

這條公理不會因為模型的進步而失效。未來的模型會把錯誤率壓得更低，但 P(error) > 0 的不等式不會被推翻。治理架構如果建立在「模型夠好就不需要 deterministic 層」的假設上，遲早會撞到天花板——而撞到時的恢復成本，在耦合系統 <!-- term:CoupledSystem -->中，遠高於事先劃好邊界的設計成本。