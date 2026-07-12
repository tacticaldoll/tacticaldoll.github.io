+++
title = "速度陷阱：當生成速度超過驗證容量"
date = "2026-05-31T19:00:03+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "探討 AI 高速生成代碼與規格書時，與人類有限驗證容量之間的速度不對稱，以及由此產生的不可見技術債與三層防禦層級的限制。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "AI 代理人", # term:AiAgent
    "技術債", # term:TechnicalDebt
    "規格驅動開發", # term:SpecDrivenDevelopment
    "確定性邊界", # term:DeterministicTrustBoundary
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

## 背景

AI 工具最直觀的價值是速度。一份原本需要兩小時撰寫的規格文件，Claude Code 可以在幾分鐘內生成初稿。一次原本需要半天的 code review，Agent 可以在數分鐘內跑完多個維度。生產力的提升是真實的、可度量的、立即可見的。

但速度的提升有一個隱含假設：產出的消費端——review、驗證、整合——的容量也同步提升。事實上它沒有。

人類的 review 容量受制於認知頻寬：一個 reviewer 一天能深度 review 的 spec 數量、一個架構師能有效驗證的設計決策數量、一個 QA 能仔細驗收的功能數量——這些都有生理性的上限，不會因為 AI 加速了產出端而擴展。

當生成速度超過驗證容量，未被驗證的 artifact 開始堆積。這些 artifact 格式正確、CI 通過、流程合規——但它們的語意正確性沒有被人類確認過。它們是一種新型的**技術債**（Technical Debt） <!-- term:TechnicalDebt -->，看不見、不計息、直到出事才被發現。

> [!IMPORTANT]
> **技術債** <!-- term:TechnicalDebt --> (Technical Debt): 程式碼中為求快速交付而妥協、待重構與修復的設計或品質缺陷。 <!-- anchor:TechnicalDebt -->


---

## 分析

### SDD 中的速度不對稱

**速度陷阱**（Speed Trap） <!-- term:SpeedTrap -->在**規格驅動開發**（Spec-Driven Development） <!-- term:SpecDrivenDevelopment -->中尤其嚴重，因為 SDD 的 artifact 層次比純程式碼開發多出好幾層：

> [!IMPORTANT]
> **速度陷阱** <!-- term:SpeedTrap --> (Speed Trap): 指 AI 生成程式碼或規格書的速度遠超人類的驗證容量，導致在多層 Artifact 機制下未經檢驗的語意債務以人無法消化的速度高速堆積。 <!-- anchor:SpeedTrap -->
> **規格驅動開發** <!-- term:SpecDrivenDevelopment --> (Spec-Driven Development): 以規格文件為基準約束程式碼行為，確保實作與規格始終對齊的開發方法。 <!-- anchor:SpecDrivenDevelopment -->


```
純程式碼開發的產出：
  code → test → commit
  （一維，一個 review 點）

SDD 的產出：
  spec → code → test → code doc → commit → spec-code consistency check
  （多層 artifact，每層都需要 review）
```

AI 加速的是每一層的生成。但 review 的負擔是所有層的總和。一個功能從 spec 到 merge 可能產生：一份規格文件、數個原始碼檔案、對應的測試、程式碼文件的更新、以及 spec 與 code 的一致性驗證。AI 可以在一個下午生成所有這些。但 reviewer 需要：

- 讀懂 spec 並判斷它是否正確描述了需求
- 讀懂 code 並判斷它是否正確實作了 spec
- 驗證 test 是否覆蓋了 spec 中描述的邊界條件
- 確認 code doc 是否準確反映了實作行為
- 檢查 spec 和 code 之間有沒有語意落差

每一步都需要人類的認知投入。AI 加速了左邊（生成），但右邊（驗證）的速度沒有變。

### 防禦的層級結構

面對速度不對稱，實踐中浮現了一個防禦的層級結構。每一層用不同的確定性等級來補償人類驗證容量的不足：

**第一層：Lint 與靜態分析。** 這是 SDD 實踐中已經確立的 deterministic 防禦。它可以自動化、可以跑在 CI 中、不需要人的認知投入。但它只能檢查結構性正確——格式、參照完整性、schema 合規。語意正確性在它的能力之外。

**第二層：依賴有持續資安維護的開源熱專案。** 這是一種社群 review 的外包。當團隊使用一個活躍維護的開源框架時，框架本身的 API 設計和型別系統會約束使用方式，降低錯誤空間。框架的大量使用者構成了一個隱性的 review 網路——常見的錯誤模式已經被社群發現並修正。團隊不需要自己驗證框架的每一個行為，因為社群的集體驗證已經涵蓋了大部分。

但這層防禦有前提：專案必須是「熱」的（活躍維護、大量使用者、快速回應資安問題）。一個冷門的或已停止維護的依賴不提供這種保證。

**第三層：編譯器層級的防護。** 型別系統、borrow checker、effect system——這些是程式語言層級的 deterministic 約束。它們不需要人的 review，不需要社群的驗證，語言本身拒絕不合法的狀態。

Rust 的 ownership model 比 C 的手動記憶體管理「限制更多」，但這些限制正是速度陷阱 <!-- term:SpeedTrap -->下最有價值的防禦：AI 可以高速生成 Rust 程式碼，但 borrow checker 會在編譯時攔住一整類記憶體安全問題，不管生成速度多快。AI 生成的 TypeScript 可能有型別錯誤，但 `tsc --strict` 會在 CI 中攔住它。

**但第三層需要架構規劃素養。** 選擇用 Rust 而非 C、用強型別而非弱型別、用 effect system 而非 exception——這些都是架構決策，需要人理解「為什麼這個限制對這個專案有價值」。這又回到了**確定性邊界**（Deterministic Trust Boundary） <!-- term:DeterministicTrustBoundary -->的核心命題：deterministic 工具的選擇和部署本身需要 probabilistic 的判斷。編譯器是最強的 gate，但選擇使用它的決定不是 deterministic 的。

> [!IMPORTANT]
> **確定性邊界** <!-- term:DeterministicTrustBoundary --> (Deterministic Trust Boundary): 在系統設計中，劃分確定性執行層（如腳本、CI）與統計推論層（如大語言模型）的介面契約，以確保關鍵操作的 100% 正確性。 <!-- anchor:DeterministicTrustBoundary -->


### 三層防禦的覆蓋率

```
問題空間                              防禦層覆蓋
─────────────────────────────────────────────────
格式錯誤、參照斷裂、schema 違規       ✓ Lint（第一層）
已知的安全漏洞模式、常見 anti-pattern  ✓ 開源社群（第二層）
記憶體安全、型別安全、並行安全         ✓ 編譯器（第三層）
─────────────────────────────────────────────────
業務邏輯正確性                         ✗ 無自動防禦
Spec 與需求的語意一致性                ✗ 無自動防禦
設計決策的長期可維護性                 ✗ 無自動防禦
```

三層防禦覆蓋的是「可以用規則表達的正確性」。剩下的——業務邏輯、語意一致性、設計品味——仍然只有人能驗證。而這些恰恰是 AI 最容易出錯的領域，也是出錯後成本最高的領域。

速度陷阱 <!-- term:SpeedTrap -->的本質是：AI 加速了所有層的生成，deterministic 防禦只能攔住一部分，剩下的部分以人類無法消化的速度堆積成未驗證債務。

### 未驗證債務的特性

未驗證債務和傳統技術債 <!-- term:TechnicalDebt -->不同：

**不**可見性**（Visibility） <!-- term:Visibility -->。** 技術債 <!-- term:TechnicalDebt -->通常有標記——TODO 註釋、已知的 workaround、有意識地推遲的重構。未驗證債務沒有標記。它看起來和已驗證的產出完全一樣。你無法從一份 spec 的外觀判斷它有沒有被深度 review 過。

> [!IMPORTANT]
> **可見性** <!-- term:Visibility --> (Visibility): 知識在開發團隊或 AI 代理人之間的公開與可存取程度。 <!-- anchor:Visibility -->


**非線性爆發。** 技術債 <!-- term:TechnicalDebt -->的成本通常是線性的——更多的 debt 意味著更慢的開發速度。未驗證債務的成本是非線性的——它可能完全沒有影響（如果 AI 產出恰好是正確的），也可能在某個時刻連鎖爆發（當一個未驗證的 spec 錯誤導致一連串基於它的實作全部偏離需求）。

**難以償還。** 傳統技術債 <!-- term:TechnicalDebt -->可以排進 sprint 來還——重構一個模組、補寫測試、清理依賴。未驗證債務的「償還」意味著對已經 merge 的所有 AI 產出做事後 review。但事後 review 的效率遠低於即時 review——reviewer 不記得當時的 context，diff 已經被後續變更覆蓋，原始意圖已經模糊。

---

## 省思

速度陷阱 <!-- term:SpeedTrap -->的諷刺之處在於：它是「AI 有效」的直接後果。如果 AI 的產出品質很差，速度陷阱 <!-- term:SpeedTrap -->不會發生——因為問題會被即時發現，產出會被退回。速度陷阱 <!-- term:SpeedTrap -->只在 AI 產出「大部分是對的」的情況下才會發生——正確率高到足以通過粗略 review，但不是 100%，使得少量錯誤混入已驗證的產出中。

這與**技能幻覺**（Skill Illusion） <!-- term:SkillIllusion -->的機制互相強化：AI 產出的表面品質越高，越難辨識其中的錯誤，未驗證債務堆積得越快。

> [!IMPORTANT]
> **技能幻覺** <!-- term:SkillIllusion --> (Skill Illusion): 指 AI 賦能讓開發者產生自身具備相應能力的錯覺，實質上相關能力從未在組織或個人中真正存在，並在 Skill 堆積文化中自我強化。 <!-- anchor:SkillIllusion -->


三層防禦（lint、社群、編譯器）提供的是一個安全網——它保證即使人類 review 跟不上，至少結構性的和已知模式的錯誤被攔住了。但安全網下面是開放的：業務邏輯的正確性、設計的長期可維護性——這些只有人能判斷，而人的判斷容量沒有因為 AI 的存在而增加。

這意味著在 AI 輔助開發中，人的角色不是「做更多」而是「選擇性地做更深」。三層防禦處理了廣度（所有產出都經過結構檢查），人的 review 需要聚焦在深度（對最關鍵的語意決策做深度驗證）。但「哪些決策最關鍵」本身又是一個需要判斷力的問題。

---

## 結論

生成速度超過驗證容量時，未被驗證的 AI 產出以 CI 通過、格式合規的外觀堆積成一種不可見的技術債 <!-- term:TechnicalDebt -->。三層防禦——lint、開源社群的隱性 review、編譯器層級的型別安全——可以攔住結構性和已知模式的錯誤，但業務邏輯和語意正確性仍然只有人能驗證。

速度陷阱 <!-- term:SpeedTrap -->不能通過「加速 review」來解決，因為人類的認知頻寬是硬限制。它也不能通過「減慢生成」來解決，因為那就放棄了 AI 的核心價值。唯一的結構性應對是把防禦層級做對——讓 deterministic 的層攔住所有它能攔的，讓人集中有限的認知資源在它攔不住的語意層。

但防禦層級的選擇——用什麼語言、什麼型別系統、什麼框架——本身需要架構規劃的素養。而這種素養是否也在速度陷阱 <!-- term:SpeedTrap -->中被稀釋，是一個值得警惕的自指風險：速度陷阱 <!-- term:SpeedTrap -->可能正在侵蝕抵抗速度陷阱 <!-- term:SpeedTrap -->所需要的能力。