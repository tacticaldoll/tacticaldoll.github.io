+++
title = "地基會動：模型版本遷移的無聲漂移"
date = "2026-05-31T19:00:01+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "分析底層大型語言模型無聲更替帶來的全局語意漂移，探討其對規格驅動開發（SDD）治理機制及人機協作認知基準的根本性挑戰。"
tags = [
    "經驗報告", # term:ExperienceReport
    "AI 代理人", # term:AiAgent
    "規格驅動開發", # term:SpecDrivenDevelopment
    "模型版本遷移", # term:ModelVersionMigration
  ]
series = ["驗證瓶頸：當底層漂移與生成洪流觸碰審查天花板"]
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

軟體工程有一條不成文的假設：工具鏈的行為是穩定的。編譯器升級時你會讀 changelog，測試框架更新時你會跑 regression suite，但這些升級的頻率是以月或季度計的，而且變更是可枚舉的——release notes 會列出 breaking changes。

LLM 作為工具鏈的核心引擎，打破了這個假設。以 Claude Code 為例，它的底層模型 Claude Opus 在半年內經歷了 4.6、4.7、4.8 三個主版本。模型版本之間的行為差異不可枚舉——沒有 breaking changes 列表，因為模型的行為不是 API spec 定義的，而是權重矩陣決定的。同一個 prompt、同一套 skill 定義、同一份 CLAUDE.md，在 Opus 4.7 上的輸出可能與 4.6 截然不同，但「不同」的方式和範圍無法事前預測。

這不是理論推演。Opus 4.7 相對於 4.6 在部分場景出現了推理品質的退化——更冗長、更不精確，而且定價更高。使用者在沒有被通知的情況下被切換到新版本，直到觀察到產出品質的變化才意識到底層模型已經不同。4.8 的發行又即將到來，同樣的循環即將再次發生。

---

## Incident

一個使用 Claude Code 進行**規格驅動開發**（Spec-Driven Development） <!-- term:SpecDrivenDevelopment -->的團隊，花了數週調校一組 command skill，用於規格文件的生成、同步和驗證。這些 skill 在 Opus 4.6 上表現穩定：生成的 spec 結構一致、delta sync 的遺漏率可控、驗證 skill 能攔住大部分格式錯誤。

> [!IMPORTANT]
> **規格驅動開發** <!-- term:SpecDrivenDevelopment --> (Spec-Driven Development): 以規格文件為基準約束程式碼行為，確保實作與規格始終對齊的開發方法。 <!-- anchor:SpecDrivenDevelopment -->


模型底層從 Opus 4.6 切換到 4.7 後，skill 的行為開始漂移。變化是漸進的、分散的：

- 某個生成 skill 開始在 spec 中加入先前不會加的章節標題，格式上合法但語意上冗餘。
- **差量**（Delta） <!-- term:Delta --> sync skill 的合併策略變得更「保守」——保留了更多舊版內容，導致 spec 膨脹。
- 驗證 skill 的 false positive 率上升，開發者開始習慣性地忽略**警告**（Warning） <!-- term:Warning -->。

> [!IMPORTANT]
> **差量** <!-- term:Delta --> (Delta): 相對於已存在規格基線的具體變化與修改項目。 <!-- anchor:Delta -->
> **警告** <!-- term:Warning --> (Warning): 術語審計中指出的潛在問題或警告 <!-- anchor:Warning -->


沒有任何單一事件觸發警報。每個變化都在容忍範圍內——多一個標題、多保留一段文字、多一個警告 <!-- term:Warning -->。但這些微小漂移的累積效果是：spec 的品質基準在不知不覺中下移。

發現問題的契機不是某個 skill 壞了，而是一位資深成員在 review 時注意到「最近的 spec 讀起來不太一樣」——一個無法精確定義的直覺。回溯後才定位到 Opus 版本更替是根因。而 Claude Code 的介面上，使用者並不總是清楚當前使用的是哪個 Opus 版本，模型切換可以在背景中發生。

---

## 分析

### 無聲漂移的三個特徵

**模型版本遷移**（Model Version Migration） <!-- term:ModelVersionMigration -->造成的漂移有三個特徵，使它比傳統的工具鏈升級更難偵測：

> [!IMPORTANT]
> **模型版本遷移** <!-- term:ModelVersionMigration --> (Model Version Migration): 指底層大型語言模型發生無聲更替，導致其行為、意圖理解和隱性規則產生全局性且難以察覺的無聲漂移。 <!-- anchor:ModelVersionMigration -->


**非二元性。** 傳統工具鏈的升級要嘛壞（編譯失敗、測試不過），要嘛不壞。Opus 版本的漂移不是壞，是「不太一樣」。輸出仍然是合法的、格式正確的、語意上說得通的——只是微妙地偏離了先前版本的行為模式。CI 不會攔它，lint 不會標它，只有對「先前行為」有內隱記憶的人才能感覺到差異。

**全局性。** 編譯器升級影響的是特定語法或 API。模型版本的變化影響的是所有依賴該模型的 skill——同時、全面、以不同方式。團隊不會看到「某個 skill 壞了」，而是看到一種彌漫的、難以歸因的品質偏移。每個人都覺得「最近好像有點不對」，但沒人能指出具體是什麼。當 Claude Code 的底層 Opus 版本更新時，團隊裡每個人的每個 skill 同時受影響。

**不可回溯性。** Claude Code 使用者通常無法自行選擇回退到舊版 Opus。即使 API 層面提供版本鎖定，鎖定的版本有存續期限。而且即使能回去，在新版本期間產生的所有 artifact 都帶著新版本的行為特徵——它們不會因為你切回舊版本而自動修正。

### 為什麼現有治理機制攔不住

SDD 治理通常依賴三層防禦——**確定性邊界**（Deterministic Trust Boundary） <!-- term:DeterministicTrustBoundary -->、**衝突封存**（Archive） <!-- term:Archive -->、**回饋迴路**（Feedback Loop） <!-- term:FeedbackLoop -->。這三層在模型遷移面前各有盲區：

> [!IMPORTANT]
> **確定性邊界** <!-- term:DeterministicTrustBoundary --> (Deterministic Trust Boundary): 在系統設計中，劃分確定性執行層（如腳本、CI）與統計推論層（如大語言模型）的介面契約，以確保關鍵操作的 100% 正確性。 <!-- anchor:DeterministicTrustBoundary -->
> **衝突封存** <!-- term:Archive --> (Archive): 這是 SDD 治理框架中的三層防禦之一，旨在記錄版本歷史與衝突狀態，但在底層模型發生無聲漂移時，由於缺乏清晰分界點，難以有效捕捉連續的品質滑坡。 <!-- anchor:Archive -->
> **回饋迴路** <!-- term:FeedbackLoop --> (Feedback Loop): 用於持續觀測治理機制運營效能的閉環系統，通常包含規則遵守率、規則有效性與治理摩擦成本三個觀測層次，藉以驅動治理規則的動態調整。 <!-- anchor:FeedbackLoop -->


**確定性邊界** <!-- term:DeterministicTrustBoundary --> 攔截的是**結構性錯誤**（Structural Error） <!-- term:StructuralError -->，但模型漂移產生的不是結構性錯誤 <!-- term:StructuralError -->——它產生的是語意偏移。Lint 會通過，因為格式沒變；diff 看不出問題，因為每個單獨的變更都是「合理的」。

> [!IMPORTANT]
> **結構性錯誤** <!-- term:StructuralError --> (Structural Error): 軟體架構或設計模式選用不當導致的程式結構缺陷，通常可透過型別約束或結構重組來消除與偵測。 <!-- anchor:StructuralError -->


**衝突封存** <!-- term:Archive --> 記錄的是版本歷史，但模型漂移不會產生一個明確的「壞版本」需要被 archive。它產生的是一個連續的品質滑坡，沒有清晰的分界點可以用來劃定「從這裡開始是漂移」。

**回饋迴路** <!-- term:FeedbackLoop --> 的第一層（規則遵守率）不會偵測到異常，因為沒有規則被違反。第二層（規則有效性）需要足夠的時間跨度才能看到趨勢。第三層（治理摩擦成本）確實可能捕捉到「最近 spec 品質下降」的訊號，但它是最慢、最不精確的觀測層。

模型遷移暴露的是：**這些防禦體系預設地基是穩定的。當地基本身在動時，所有建構在地基之上的治理機制同時失效——不是因為機制設計不好，而是因為它們的參考基準在漂移。**

### 版本鎖定的虛幻承諾

一個直覺反應是「鎖定模型版本」。Anthropic 的 API 確實支援指定模型版本（例如 `claude-opus-4-6-20250527`）。但版本鎖定只是把問題延後：

- 鎖定的版本有存續期限。Anthropic 會在新版發布後的一段時間內退役舊版。終止支援時你仍然要遷移，而且是被迫遷移，時間壓力更大。
- 鎖定在舊版意味著放棄新版本的能力提升。如果 Opus 4.8 在某些維度確實比 4.6 更好，鎖定是在用確定性換效能。
- 團隊的 skill 和 prompt 會在鎖定期間持續演化，但演化是基於鎖定版本的行為。解鎖時，所有在鎖定期間做的調校都可能失效。
- Claude Code 作為工具的使用者，對底層模型版本的控制力有限。工具層的版本選擇與 API 層的版本鎖定是兩個不同的決策面。

版本鎖定不是解決遷移問題，而是把一次漸進漂移替換成一次被迫的階躍遷移。總風險可能更集中。

---

## 省思

模型版本遷移 <!-- term:ModelVersionMigration -->最深層的問題不在技術面——lint 可以加強、regression suite 可以為 skill 建立、版本鎖定可以爭取緩衝時間。問題在認知面：**團隊必須持續意識到「地基在動」這件事，但人的認知本能是把環境假設為穩定的。**

當 skill 在 Opus 4.6 上調校完成且表現良好時，它會被認知標記為「已解決的問題」——注意力轉移到其他事情上。底層模型切換到 4.7 時，沒有任何事件提醒團隊「你之前解決的問題可能需要重新驗證」。漂移在背景中累積，直到某個人的直覺響了警報。

Opus 4.6 → 4.7 的退化案例尤其值得記錄，因為它打破了一個隱含假設：模型升級等於改善。4.7 在某些場景下比 4.6 更差——更冗長、更不精確、更昂貴。這意味著「升級」不是單向的進步，而是多維度的權衡。在某些維度上提升的同時，其他維度可能退化。而你在哪些維度上建構了依賴，決定了這次「升級」對你來說是改善還是損害。

這個認知盲區不是個人的疏忽，而是人類注意力分配的結構性限制。我們不擅長監視緩慢的、連續的、沒有明確觸發事件的變化。氣候變遷難以引起即時反應，不是因為人不關心，而是因為漸變不觸發警報系統。模型**版本漂移**（Version Drift） <!-- term:VersionDrift -->是同一種現象的微縮版。

> [!IMPORTANT]
> **版本漂移** <!-- term:VersionDrift --> (Version Drift): 同一段程式碼在不同的 runtime 環境或依賴庫版本下運作時，因底層行為改變而產生的語意或執行差異。 <!-- anchor:VersionDrift -->


---

## 結論

在 Claude Code 和類似的 LLM 驅動開發工具中，模型版本遷移 <!-- term:ModelVersionMigration -->不是一次性事件，而是持續的背景狀態。Opus 4.6、4.7、4.8 的快速迭代意味著「地基在動」是常態，不是例外。

這對既有的 SDD 治理框架構成根本性挑戰——確定性邊界 <!-- term:DeterministicTrustBoundary -->、衝突封存 <!-- term:Archive -->、回饋迴路 <!-- term:FeedbackLoop -->，這些機制的設計和校準都是針對特定版本的模型行為。當模型版本更替時，不只是 skill 的行為在漂移，治理機制本身的有效性也在漂移。你用來偵測問題的工具，和製造問題的引擎，建構在同一個移動的地基上。

而偵測這種漂移，目前依賴的是人的直覺——「最近的 spec 讀起來不太一樣」。這意味著模型版本遷移 <!-- term:ModelVersionMigration -->的防禦最終落在人的判斷力上——一種無法自動化、無法用 deterministic script 替代的能力。如果這種判斷力本身因為過度依賴 AI 而未曾真正發展，那麼地基的移動就是不可觀測的，而不可觀測的漂移是所有治理機制最危險的失效模式。