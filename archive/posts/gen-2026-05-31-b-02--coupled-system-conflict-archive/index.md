+++
title = "耦合系統的衝突與封存：當回滾成為衝突的子類"
date = "2026-05-31T18:00:02+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "探討在規格與程式碼緊密耦合的系統中，回滾操作如何因語意圖的複雜度而成為新的衝突來源，並剖析歷史版本封存（archive）機制在漂移溯源上的精妙設計與三個結構性盲區。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "AI 代理人", # term:AiAgent
    "耦合系統", # term:CoupledSystem
    "衝突封存", # term:Archive
    "規格驅動開發", # term:SpecDrivenDevelopment
    "引用完整性", # term:ReferentialIntegrity
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

在傳統軟體工程中，回滾是一個確定性操作。`git revert` 產生一個反向 commit，程式碼回到先前狀態，問題解除。這個操作的前提是變更的可逆性——程式碼是一維的時間線，沿著時間線往回走就能復原。

**規格驅動開發**（Spec-Driven Development） <!-- term:SpecDrivenDevelopment -->打破了這個前提。當程式碼與規格文件（spec）構成**耦合系統**（Coupled System） <!-- term:CoupledSystem -->時，變更不再是一維的。一次功能實作同時修改了程式碼和對應的 spec；spec 之間有引用關係；其他開發者可能已經基於新版 spec 開始下游工作。在這樣的系統中，「回滾」不再是沿著時間線往回走——它是對一個多維耦合圖的局部操作，而局部操作在耦合系統 <!-- term:CoupledSystem -->中必然產生不一致。

> [!IMPORTANT]
> **規格驅動開發** <!-- term:SpecDrivenDevelopment --> (Spec-Driven Development): 以規格文件為基準約束程式碼行為，確保實作與規格始終對齊的開發方法。 <!-- anchor:SpecDrivenDevelopment -->
> **耦合系統** <!-- term:CoupledSystem --> (Coupled System): 由程式碼與規格文件等相互依賴、協同演化的元件所構成的系統，其特點是任何局部變更或回滾皆可能引發全局或關聯性的語意衝突。 <!-- anchor:CoupledSystem -->


這篇報告分析為什麼回滾在 code-spec 耦合系統 <!-- term:CoupledSystem -->中本質上是一個新的衝突來源，以及 archive 機制如何制度化地回應這個問題——包括它解決了什麼、迴避了什麼。

---

## 分析

### 回滾的不可逆性

考慮一個具體場景。開發者 A 完成了一個功能，涉及以下變更：

- 程式碼：新增模組 M，修改介面 I
- 規格：新增 spec-X 描述模組 M 的行為，更新 spec-Y 引用 spec-X 的定義

上線後發現問題，需要回滾。程式碼層面，`git revert` 可以乾淨地移除模組 M、還原介面 I。但規格層面：

- spec-X 描述的是 v3 的行為。回滾程式碼到 v2 後，spec-X 的內容與程式碼不一致。
- spec-Y 在更新時引用了 spec-X 的定義。即使 revert spec-X，spec-Y 中的引用可能已經嵌入了 v3 的語意。
- 如果 spec 的同步由 LLM 驅動（例如 delta sync），revert 後的重新同步可能產生與手動 revert 不同的結果——因為模型看到的 context 變了。

根本問題是：**程式碼的回滾是確定性的（反向 diff），但規格的回滾不是**。**約束性規格**（Spec） <!-- term:Spec --> 之間的引用構成一個語意圖，而語意圖沒有自動的反向操作。你可以 revert 一個檔案的文字內容，但你不能 revert 它對其他文件語意理解的影響。

> [!IMPORTANT]
> **約束性規格** <!-- term:Spec --> (Spec): 以結構化或機器可讀格式定義的系統或 API 合約規範。 <!-- anchor:Spec -->


### 多人協作下的回滾風暴

單人場景的回滾已經困難。多人並行時，回滾從困難升級為衝突製造器。

```
A 的時間軸：  spec-X v1 → v2 → v3(壞) → revert to v2
B 的時間軸：  spec-Y v1 ───引用 spec-X v3───→ 繼續開發中
C 的時間軸：  spec-Z v1 ───引用 spec-Y（間接依賴 spec-X v3）───→ 繼續開發中
```

A 的回滾是合理的：v3 有問題，需要退回 v2。但這個操作對 B 和 C 來說不是「恢復」，而是「破壞」：

- B 的 spec-Y 引用了 spec-X v3 的定義。A revert 後，B 的引用指向了一個不再存在的版本。
- C 甚至不知道自己間接依賴了 spec-X——依賴是通過 spec-Y 傳遞的。A 的回滾到了 C 這裡，表現為一個原因不明的 spec 不一致。

每個人都在做合理的事情：A 在修復問題，B 在正常開發，C 在引用穩定的上游 spec。衝突不是任何人的錯誤，而是耦合系統 <!-- term:CoupledSystem -->在並行操作下的結構性現象。

**一個人的恢復操作，就是另一個人的失敗模式。**

### Archive：漂移的制度化

面對這個結構性問題，像 openspec、spec-kit 這類 SDD 工具提供了 archive 機制——將規格文件的歷史版本封存為永久記錄。歷史封存 不修改當前狀態，只記錄過去的狀態。

這是一個精妙的設計選擇。它的本質是：**承認一致性是暫態，不一致是常態，然後提供一個機制讓不一致能被溯源。**

```
沒有 archive：
  spec v3 和 code v2 不一致 → 這是一個 bug，有人要修

有了 archive：
  spec v3 被 archive → 它是「歷史版本」
  spec v4 重新對齊 code v2 → 現在是一致的
  v3 → v4 的差異是「演化」，不是「錯誤」
```

歷史封存 把漂移從語意上重新分類：它不再是需要修復的 bug，而是可以查閱的歷史。這是一種語意操作，而非技術操作——同樣的不一致，因為有了 archive 記錄，從「故障」變成了「軌跡」。

### Archive 的三個盲區

歷史封存 解決了溯源，但它有三個結構性盲區：

**盲區一：跨 spec 引用的 orphan 化。** 當 spec-X 被 archive 時，spec-Y 中引用 spec-X 的定義不會自動更新。歷史封存 機制處理的是單一 spec 的版本歷史，不處理 spec 之間的引用圖。結果是 archive 動作本身可能製造新的 orphan reference——和 delta sync 產生 orphan marker 的問題同構。

**盲區二：archive 時機的判斷。** 什麼時候一個 spec 應該被 archive？如果漂移已經發生但沒人注意到，spec 會繼續以過時的狀態被引用。歷史封存 是一個需要人（或 agent）主動觸發的操作，但觸發的前提是知道漂移已經發生——這又回到了觀測問題。

**盲區三：archive 後的 reconciliation。** 歷史封存 記錄了「過去是什麼」，但不回答「現在應該是什麼」。spec-X 被 archive 後，spec-Y 中引用 spec-X 的部分需要人來判斷：是刪除引用、更新到新版本、還是保留指向 archive 的歷史引用？這個判斷是語意性的，不能自動化——至少不能用 deterministic script 自動化。如果用 LLM 來判斷，就回到了統計模型的確定性天花板。

---

## Alternatives

既然完美回滾在耦合系統 <!-- term:CoupledSystem -->中不存在，替代策略有三條路線：

### Forward-fix：永遠往前修

不回滾程式碼，也不回滾 spec。發現問題後，推一個新版本修正問題，同時更新 spec 到 v4。

**優勢**：不產生漂移。所有 spec 的時間線只往前走，引用關係始終指向存在的版本。B 和 C 的工作不受影響——他們引用的 spec-X v3 仍然存在，只是被標記為「已知有問題，修正見 v4」。

**代價**：速度。Forward-fix 意味著修正必須同時涵蓋程式碼和 spec，而且修正本身也要經過完整的 review 流程。在緊急情況下（生產事故），「修正」的時間壓力可能導致 spec 更新被跳過——產生另一種形式的漂移。

**適用條件**：問題不緊急，或團隊有紀律同時推進 code 和 spec 的修正。

### Atomic rollback：整組回滾

把 code 和 spec 綁定為一個版本單元。回滾時，整個單元一起回滾——不能只 revert code 不 revert spec。

**優勢**：保證 code-spec 一致性。任何時間點，code 和 spec 都是同一版本。

**代價**：需要基礎設施支持。Git 管理 code 的版本，但 spec 可能不在同一個 repo，或不在同一個 commit 粒度。實現 atomic rollback 需要一個跨 code-spec 的版本綁定機制——而這個機制本身的正確性又是一個需要保證的問題。此外，跨 spec 引用使得「原子」的邊界很難劃定：如果 spec-Y 引用了 spec-X，你回滾 spec-X 時是否也要回滾 spec-Y？

**適用條件**：spec 和 code 在同一個 repo 且版本粒度一致，或有成熟的跨 artifact 版本管理工具。

### Quarantine：隔離而非回滾

不回滾也不修正，先隔離有問題的部分。標記 spec-X v3 為「隔離中」，通知所有引用方「此 spec 暫不可用」，其餘開發繼續推進。

**優勢**：快。不需要立即修正任何東西，只需要一個標記和一個通知機制。其他團隊成員不會因為回滾產生的漂移而中斷工作。

**代價**：隔離需要模組邊界夠清楚。如果 spec-X 被 10 個其他 spec 引用，「隔離 spec-X」實際上是在告訴 10 個下游「你的依賴暫時不可用」——這可能比回滾造成更大的中斷。此外，隔離是一個暫態——它遲早需要被解除，而解除時仍然要面對 forward-fix 或回滾的選擇。

**適用條件**：模組邊界清晰，被隔離的 spec 的扇出度低（引用它的 spec 少）。

---

## 省思

三條替代路線各有適用條件，沒有普遍解。但它們共同揭示了一個更深層的觀察：

**耦合系統 <!-- term:CoupledSystem -->的治理成本不在「正確路徑」上——正確路徑走起來和傳統開發差不多。成本集中在「錯誤恢復路徑」上——而恢復路徑的代價，隨著耦合程度非線性增長。**

在純 code 的世界裡，revert 是 O(1) 操作——一個反向 commit。在 code-spec 耦合的世界裡，revert 是 O(n) 操作——n 是受影響的 spec 引用鏈長度。在多人並行的 code-spec 世界裡，revert 是 O(n × m) 操作——m 是同時在工作的人數。

這解釋了為什麼「回滾很難」不是一個實踐問題，而是一個結構問題。實踐問題可以通過更好的工具、更好的流程來解決。結構問題只能被理解和管理，不能被消除。

歷史封存 機制的智慧在於它沒有試圖解決回滾——它承認了漂移的不可避免性，然後提供了一個讓漂移可溯源的制度化框架。但 archive 解決的是「之後能查」，不是「當下能處理」。當下的處理——在多人並行的耦合系統 <!-- term:CoupledSystem -->中，即時發現漂移、判斷影響範圍、選擇正確的恢復策略——仍然是一個開放問題。漂移能否被即時觀測到，決定了這三條替代路線中的任何一條是否有機會在損害擴散之前啟動。

---

## 結論

在 code-spec 耦合系統 <!-- term:CoupledSystem -->中，回滾不是恢復手段，而是新衝突的來源。一個人的恢復操作必然影響其他人的**引用完整性**（Referential Integrity） <!-- term:ReferentialIntegrity -->。歷史封存 機制通過將漂移重新分類為歷史來回應這個問題，但它解決的是溯源，不是 reconciliation。

> [!IMPORTANT]
> **引用完整性** <!-- term:ReferentialIntegrity --> (Referential Integrity): 批量變更或重命名時，系統中所有交叉引用（包括非典型位置的類型標記與文件段落）皆被同步更新的狀態。 <!-- anchor:ReferentialIntegrity -->


三條替代路線——forward-fix、atomic rollback、quarantine——各有適用條件。選擇哪一條取決於具體情境：問題的緊急程度、模組邊界的清晰度、版本管理的基礎設施成熟度。但無論選擇哪條路線，都需要一個前提：你知道漂移正在發生。

沒有觀測，forward-fix 不知道要修什麼；atomic rollback 不知道要回滾到哪裡；quarantine 不知道要隔離什麼。所有恢復策略的前提是即時的漂移偵測——而這正是 SDD 治理中目前最薄弱的環節。