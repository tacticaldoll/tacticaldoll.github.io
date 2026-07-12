+++
title = "先修正契約，再擴充能力"
date = "2026-06-12T08:09:02+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "產品與系統開發中，常會同時出現兩種都合理的下一步。一種讓已經存在的能力更完整： 補齊某個 API 的行為、讓某個概念真正落地、改善使用者可見的不一致。另一種比較 不顯眼：它修正底層契約，防止未來出現錯誤狀態、資料遺失、重複 mutation 或生命週期 語義破裂。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "AI 代理人", # term:AiAgent
    "反思", # term:Reflection
    "差異", # term:Delta
  ]
[ai_info]
    [ai_info.generation]
        model = "GPT 5.5"
        agent = "Codex VS Code extension 26.609.30741"
    [ai_info.refinement]
        model = "Gemini 3.1 Pro"
        agent = "Antigravity IDE 2.0.4"
+++

<!--more-->

## 背景

產品與系統開發中，常會同時出現兩種都合理的下一步。一種讓已經存在的能力更完整：
補齊某個 API 的行為、讓某個概念真正落地、改善使用者可見的不一致。另一種比較
不顯眼：它修正底層契約，防止未來出現錯誤狀態、資料遺失、重複 mutation 或生命週期
語義破裂。

直覺上，可見的功能完整性更容易被排到前面，因為它能被使用者立刻感知。但若底層
契約存在錯誤模型，外顯能力越完整，錯誤被繼承和放大的面積也越大。因此，當兩者
競爭時，預設排序應該是：先修正 correctness foundation，再擴充 feature completeness。

本文討論這個排序原則，以及另一個同等重要的邊界：一個 contract fix 可能 enable
更大的能力，但它不應在同一個 change 裡吞掉那些被 enable 的能力。

## 分析

### 兩種都合理，但風險傳播方式不同的改動

外顯完整性和契約正確性都不是次要工作。外顯完整性讓系統更符合已宣告的承諾。
例如一個概念已經出現在 API、文件或使用者心智中，但實作還只是部分支援；補齊它
能減少驚訝，讓產品表面更一致。

契約正確性處理的是另一層問題。它問的不是「這個功能是否完整」，而是「系統是否
允許不該發生的狀態轉移」。這類改動通常不顯眼，因為正常路徑看起來本來就能跑。
它的重要性會在錯誤路徑、競態、重試、權限失效、部分失敗或未來擴充時出現。

兩者真正的**差異**（Delta） <!-- term:Delta -->在風險傳播。外顯完整性的缺口通常局部可見：某個使用情境不完整。
契約錯誤則像地基裂縫：後續能力會蓋在它上面，而且可能把同一個錯誤模型帶到更多
地方。

> [!IMPORTANT]
> **差異** <!-- term:Delta --> (Delta): 特定變更的契約，用於驅動實作並作為驗證實作的基準對象。 <!-- anchor:Delta -->


### 為什麼 correctness foundation 通常應先行

若一個改動防止 invalid lifecycle state，它通常應該早於功能擴充。原因不是它比較
底層，而是它會被後續功能繼承。後續功能可能增加使用量、增加並發、增加持久化、
增加外部整合。這些擴充都會放大底層契約的假設。

一個錯誤契約若留在核心中，後續 feature 會面臨兩種壞選擇。第一種是照著錯誤契約
實作，使問題正式成為系統行為的一部分。第二種是在每個 feature 裡局部補洞，導致
相同 correctness concern 被分散處理。兩者都會增加日後修正成本。

因此，prioritization 不只是價值排序，也是污染控制。先修正會被廣泛繼承的錯誤模型，
能讓後續功能建立在較穩定的語義上。

### 判準：不是所有底層工作都叫 foundation

這條原則有一個危險的濫用方式：把任何底層、抽象、未來可能有用的工作都稱為
foundation。這會讓團隊掉進 premature infrastructure，把時間花在尚未被需求證明
的架構想像上。

真正的 correctness foundation 應該通過更嚴格的檢查：

- 它是否防止一個明確的 invalid state？
- 它是否阻止不可逆或錯誤的 mutation？
- 它是否保護核心生命週期語義？
- 它是否會被多個已知後續能力繼承？
- 若現在不修，後續功能是否會被迫依賴錯誤契約？

如果答案只是「這比較抽象」、「以後可能需要」、「做了會比較漂亮」，那還不是
foundation。它可能只是 infrastructure appetite。correctness foundation 的重點
不是層級低，而是它阻止錯誤模型擴散。

### 第二個陷阱：把 enabling contract 做成 enabled feature

即使某個 foundation 值得優先，仍然要避免另一個陷阱：把支撐條件和被支撐能力混成
同一個 change。很多 contract fix 會 enable 更大的 feature。它可能讓未來可以
安全加入並發、持久化、分散式協調或更複雜的 runtime model。但「讓未來可以安全
加入」不等於「現在就應該加入」。

enabling contract 和 enabled feature 有不同的驗證邊界。前者的驗證重點是錯誤
狀態是否被拒絕、狀態轉移是否被保護、API contract 是否表達正確 authority。後者
的驗證重點可能是吞吐量、任務調度、故障恢復、操作性或使用者工作流。把它們放在
同一個 change，會讓測試面和風險面同時膨脹。

更好的做法是讓 foundation change 小而清楚。它只修正契約、錯誤行為、驗證邏輯與
必要測試。被它 enable 的功能另開 change。這不是形式主義，而是保持因果鏈清楚：
先證明地基能承重，再決定要蓋什麼。

### scope control：小的 foundation change 才真的可驗證

foundation change 的誘惑在於它聽起來很重要。重要的東西很容易膨脹：既然已經碰
核心契約，那就順手加 runtime model；既然已經改 validation，那就順手加新 backend；
既然已經支援未來能力，那就順手做完未來能力。這些「順手」會讓 change 從可驗證的
契約修正變成多方向專案。

一個健康的 foundation change 應該能被簡短描述：

```text
Before：the system allowed this invalid transition.
After：the system rejects it and preserves the existing valid transitions.
```

這句話若無法成立，scope 可能已經漂移。好的 foundation change 會保留現有正常路徑，
新增或修正錯誤路徑，並用 focused tests 證明兩者。它不需要同時展示所有未來能力。

### 一個預設排序模型

當多個 change 競爭時，可以用四層預設排序來降低任意性：

1. **Correctness foundations**: 防止 invalid lifecycle state、data loss、duplicate
   mutation、stale authority 或 broken core semantics。
2. **Specified feature completeness**: 讓已宣告、已暴露或已被使用者合理期待的能力
   真正完整。
3. **Operator and developer ergonomics**: 改善輪詢、CLI、dashboard、metrics、debuggability
   等核心外圍工作流。
4. **Scale-out features**: concurrency、durable backend、distributed scheduling 等擴展性
   能力。

這不是永恆階級，而是衝突時的預設。它把問題從「哪個比較有趣」轉成「哪個風險會
被後續工作繼承」。預設排序也不是用來壓制例外，而是讓例外需要被說明。

### 例外：什麼時候 feature completeness 可以先

若 correctness foundation 的風險還沒有被證明，feature completeness 可能應該先行。
有時一個較小的 visible slice 能揭露真實使用方式，避免過早凍結抽象契約。若團隊
尚不知道核心 contract 應該承諾什麼，先做一個受控、低風險的功能切片，可能比先做
大型 foundation 更誠實。

另一個例外是 foundation change 會過早決定未知領域。若它需要預設未來 backend、
未來 concurrency model 或未來操作語義，但這些尚無足夠證據，那它可能不是成熟的
foundation，而是猜測。此時應縮小它，或讓 feature exploration 先提供證據。

這些例外不推翻原則。它們只是提醒：correctness-first 的對象必須是真正已知且會
擴散的錯誤契約，不是任何看起來底層的想像。

## 結論

這個排序原則背後其實有兩個不同問題。priority 是風險傳播問題：哪個錯誤若不先修，
會被後續能力繼承？ scope 是生命週期邊界問題：哪個 change 只是在修支撐條件，哪個
change 才是在建被支撐能力？

把這兩個問題混在一起，會產生兩種相反的失敗。第一種是過度追求可見功能，讓底層
錯誤模型越鋪越廣。第二種是過度追求 foundation，把所有未來想像都塞進當前 change。
成熟的判斷不是永遠選底層，也不是永遠選可見；而是先辨認風險會如何被繼承，再讓每個
change 保持自己的驗證邊界。

因此，「先修正契約」不是工程潔癖。它是一種控制未來複雜度的方式。但「再擴充能力」
同樣重要。foundation 的價值最終要由它支撐的能力來實現。兩者應該排序，不應該混同。

## 結論

當兩個合理的下一步競爭時，不要只看哪個更可見。先看哪個錯誤若不處理，會被後續
能力繼承。若一個 change 明確防止核心契約產生錯誤狀態，它通常應該早於功能完整性。
但它也應保持為 contract change，不要吞掉它所 enable 的 feature。

可遷移的原則有四條：

1. **先修正會被繼承的錯誤契約。** correctness foundation 的優先性來自風險傳播，
   不是來自抽象層級。
2. **用嚴格判準辨認 foundation。** 它必須防止明確錯誤狀態或錯誤 mutation，而不
   只是「未來可能有用」。
3. **分開 enabling contract 和 enabled feature。** 支撐條件與被支撐能力有不同
   驗證邊界。
4. **讓排序與 scope 同時清楚。** priority 決定先做什麼；scope 決定這次只做什麼。