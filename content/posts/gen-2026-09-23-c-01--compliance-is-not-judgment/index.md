+++
title = "通過檢查的決定仍可能是錯的，為此補上的規則也會被通過"
date = "2026-09-23T10:50:01+08:00"
author = "梅乾"
draft = false
isCJKLanguage = true
description = "合規不蘊含品質。從挑戰者號發射限制的連續豁免，檢視為何為錯誤補上的規則仍可能被通過。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "合規", # term:Compliance
    "判斷", # term:Judgment
    "挑戰者號", # term:Challenger
    "豁免", # term:Waiver
    "飛行準備審查", # term:FlightReadinessReview
  ]
series = ["表徵治理：通過、摘要與零回報如何取代現場"]
[ai_info]
    [ai_info.generation]
        model = "Claude Opus 5.5"
        agent = "GitHub Copilot Chat v0.66.0"
    [ai_info.refinement]
        model = "GPT-6 Sol"
        agent = "GitHub Copilot Chat v0.66.0"
+++

<!--more-->

## 導言

一個決定通過了所有規定的檢查，後來證明對系統有害。事後的標準反應是補一條規則，讓下一次同樣的決定過不了檢查。下一次，另一個決定通過了包含新規則在內的所有檢查，後來同樣證明有害。

本文只處理這一個主張：**合規**（Compliance） <!-- term:Compliance -->不蘊含品質。規則檢查的是可觀察的形式，形式與品質之間只有相關，沒有蘊含。為「合規 <!-- term:Compliance -->但不正確」補上的規則，本身又是一個可被通過的形式。規則是過去**判斷**（Judgment） <!-- term:Judgment -->的沉澱物，不是判斷 <!-- term:Judgment -->的來源。

> [!IMPORTANT]
> **合規** <!-- term:Compliance --> (Compliance): 決定或行動符合明文規則與程序的狀態，不等於實質上正確。 <!-- anchor:Compliance -->
> **判斷** <!-- term:Judgment --> (Judgment): 面對規則未覆蓋或情境已改變時，根據脈絡評估決定的實質後果。 <!-- anchor:Judgment -->


本文不主張規則無用，也不主張規則越少越好。地板仍然需要。本文要劃清的是：通過地板，不等於站在正確的位置上。

## 分析

### 可檢查的形式與它代表的東西

令 $S$ 為組織中所有需要做決定的情境，$R \subseteq S$ 為已被規則明確覆蓋的情境。令 $C(x)$ 表示「決定 $x$ 通過合規 <!-- term:Compliance -->檢查」，$Q(x)$ 表示「決定 $x$ 對系統的長期健康是好的」。本文的主張寫成兩條：

$$
\exists x \in R:\ C(x) \land \neg Q(x), \qquad S \setminus R \neq \emptyset
$$

第一條說，即使在規則覆蓋的範圍內，也存在通過檢查卻有害的決定。它不說每一個合規 <!-- term:Compliance -->的決定都是錯的。它只說合規 <!-- term:Compliance -->推不出正確。第二條說，規則覆蓋不了全部情境；落在 $S \setminus R$ 的決定，沒有規則可以通過或不通過，只能由判斷 <!-- term:Judgment -->承擔。

違反這個主張的世界長這樣：存在一套規則使 $R = S$，而且在 $R$ 上 $C$ 蘊含 $Q$。這正是「把規則寫得夠完整，人就無法做錯」所預設的世界。本文不證明這個世界在原理上不可能。本文說明的是，為什麼它無法靠持續補規則逼近。

規則檢查的永遠是可觀察的東西：步驟有沒有執行、欄位有沒有填、簽核有沒有完成。它想要的是另一件事。兩者的關係如下：

| 制度宣稱 | 檢查實際保證的東西 | 檢查沒有觸及的東西 |
| :--- | :--- | :--- |
| 有流程 | 步驟被執行過 | 執行的人是否做出了判斷 <!-- term:Judgment --> |
| 合規 <!-- term:Compliance --> | 沒有違反明文規則 | 決定是否實質正確 |
| 通過審查 | 文件與會議程序完成 | 被審查的東西是否是好的 |
| 指標全綠 | 代理量達標 | 代理量代表的狀態是否健康 |

每一列的中欄與右欄之間沒有邏輯關係，只有經驗上的相關。這個相關在行動者開始以「通過檢查」為目標之後會衰減，因為讓中欄成立的最便宜路徑，通常不經過右欄。

### 規則是判斷的沉澱物

一條規則寫下來的時候，是某個人在某個情境裡做出的判斷 <!-- term:Judgment -->：這種情況下，應該這樣做。規則把這個判斷 <!-- term:Judgment -->凍結，交給之後的人使用。它省下了重新判斷 <!-- term:Judgment -->的成本，也拿走了重新判斷 <!-- term:Judgment -->的機會。

之後的情境若與寫規則時相同，凍結的判斷 <!-- term:Judgment -->仍然有效。之後的情境若不同，規則仍然可以被通過，而它已經不再攜帶當初那個判斷 <!-- term:Judgment -->。規則最有價值的時刻，是寫下它的那一刻；規則最危險的時刻，是它被當成判斷 <!-- term:Judgment -->本身的那一刻。

判斷 <!-- term:Judgment -->密集的工作裡，最要緊的問題通常沒有規則可以回答：這個抽象層是否值得存在；這個依賴現在方便，三年後是否會變成負擔；這個局部最佳化是否正在破壞整體；這個風險該現在處理，還是應該有意識地接受。這些問題的答案依賴還沒有被寫下的脈絡。能把這些脈絡寫成規則的人，正是已經具備判斷 <!-- term:Judgment -->的人。

預防性工作讓這個困難最尖銳。架構、安全、可靠性的產出在成功時不可見：事故沒有發生，系統沒有腐化。結果無從考核，組織只能考核過程；而過程一旦成為考核對象，檢查就只能看到中欄。

### 已發生的現場：發射限制與它的六次豁免

太空梭**挑戰者號**（Challenger） <!-- term:Challenger -->事故總統調查委員會的報告，保留了一段規則被補上、然後被通過的完整紀錄。以下事實出自該報告第六章。

> [!IMPORTANT]
> **挑戰者號** <!-- term:Challenger --> (Challenger): 1986 年發射失事的太空梭；其調查紀錄用於檢視豁免、摘要與資訊回報的失效。 <!-- anchor:Challenger -->


太空梭計畫的 Level I 需求文件第 2.8 段規定，除主結構、熱防護與壓力容器外，各子系統的冗餘不得低於「故障安全」（fail-safe）。1982 年 12 月 17 日，固態火箭推進器接頭的密封被改列為 Criticality 1，也就是承認第二道 O 形環在接頭轉動後不能作為備援。1983 年 3 月，Level I 與 Level II 批准了一份 Criticality 1 狀態的**豁免**（Waiver） <!-- term:Waiver -->；報告寫明，這份豁免 <!-- term:Waiver -->「是為了避免第 2.8 段加諸於太空梭計畫的義務」而批准的。規則要求冗餘。接頭沒有冗餘。豁免 <!-- term:Waiver -->讓規則被滿足。

> [!IMPORTANT]
> **豁免** <!-- term:Waiver --> (Waiver): 經批准而不適用特定限制的例外處置；形式上的批准不代表原本的風險已消失。 <!-- anchor:Waiver -->


1985 年 4 月 29 日發射的 STS 51-B，其噴嘴接頭的主 O 形環被侵蝕 0.171 英吋而沒有密封，第二道 O 形環也被侵蝕 0.032 英吋。推進器計畫經理稱第二道環被侵蝕是「新而重大的事件」。1985 年 7 月，他與馬歇爾太空飛行中心（Marshall Space Flight Center）的問題評估委員會對太空梭系統設下一道發射限制（launch constraint）。依 1980 年的定義，限制應持續到問題解決，或有充分理由判定問題不會發生。

限制設下之後，計畫經理在 1985 年 7 月 10 日之後的每一次飛行都把它豁免 <!-- term:Waiver -->。他在聽證中說明這道限制的意思：必須處理這些觀察，看上一次飛行有沒有出現改變先前理由的東西，並在**飛行準備審查**（Flight Readiness Review） <!-- term:FlightReadinessReview -->中提出；目的是確保「我們仍在測試經驗範圍內」。委員會的結論寫得很直接：51-L 之前連續六次豁免 <!-- term:Waiver -->發射限制，使它在沒有任何豁免 <!-- term:Waiver -->紀錄、甚至沒有明示限制的情況下飛行。

> [!IMPORTANT]
> **飛行準備審查** <!-- term:FlightReadinessReview --> (Flight Readiness Review): 太空梭計畫中供不同層級檢視發射條件、限制與疑慮的審查程序。 <!-- anchor:FlightReadinessReview -->


同年 12 月，承包商工程師依要求提出將 O 形環侵蝕問題「結案」，而改良工作仍在進行。委員會主席問他，既然還在想辦法修，為什麼要結案。他答：「因為我被要求這麼做。」問題追蹤系統隨後記下「承包商已申請結案」與「問題視為已結案」。計畫經理事後作證說這兩筆紀錄是錯的。結果是，51-L 的飛行準備審查 <!-- term:FlightReadinessReview -->沒有把這道限制當成未結的限制提出。

用上面的兩條式子讀這段紀錄，每一步的 $C$ 都為真。豁免 <!-- term:Waiver -->有簽核。限制在審查中「處理」過。結案有申請、有紀錄。每一步的 $Q$ 都為假：接頭沒有被修好。更要緊的是順序：51-B 的損壞是一次「合規 <!-- term:Compliance -->但不正確」，組織的回應是一條新規則，也就是發射限制；這條新規則隨即成為一個可以被通過的形式，連續被通過了六次。

這份報告不支持「有人刻意規避規則」這個讀法。它記下的是每一個人都在做規則要求他做的事。它也不支持「沒有人有判斷 <!-- term:Judgment -->」。第二道環受損之後，設下限制這件事本身就是一個判斷 <!-- term:Judgment -->。問題在於判斷 <!-- term:Judgment -->一旦被凍結成限制，限制就只要求被「處理」，不再要求那個判斷 <!-- term:Judgment -->被重新做一次。判斷 <!-- term:Judgment -->在場，決定由形式做出。

### 為什麼補上的規則也會被通過

規則指定一個可觀察的形式。行動者的任務於是變成讓那個形式成立。規則禁止 $X$，行為就演化成技術上不是 $X$ 的 $X'$。限制要求在審查中提出，提出就演化成證明觀察「仍在經驗範圍內」。委員會把這個機制寫成一句：只追蹤、只延續那些「超出資料庫」的異常，使重大問題得以從回報系統中被移除、被遺失。

補上一條規則，也就補上一個新的可通過形式。真正需要判斷 <!-- term:Judgment -->的空白沒有縮小，只是被更厚的形式蓋住。蓋住之後，它更難被看見，因為每一層形式都回報「已通過」。

## 反思

這不是反制度論。完全沒有外在控制的組織，防不住最壞的行為，也無法讓陌生人協作。委員會在第五章的發現中指出，當時沒有任何制度使發射限制及其豁免 <!-- term:Waiver -->必須由各級管理層考慮。這個缺口該補，而補上的是一條規則，而且是應該有的規則。本文排除的是另一件事：把這條規則寫下之後，就認為下一次決定會是對的。

《論語·為政》的對比常被用來講這件事：「道之以政，齊之以刑，民免而無恥；道之以德，齊之以禮，有恥且格。」它常被讀成對一切制度的否定。更精確的讀法是：只靠外在規則與懲罰塑造行為，人學到的是怎樣不越線，不是怎樣做對。禮也是形式；差別在於形式是傳遞判斷 <!-- term:Judgment -->的載體，還是判斷 <!-- term:Judgment -->的替代品。本文用這段話作為對照，不作為論證。

本文也不主張規則的密度會讓判斷 <!-- term:Judgment -->力萎縮。這個說法可能成立，但本文沒有證據。本文也不處理判斷 <!-- term:Judgment -->如何被養成。那需要另外的來源。

還有一個容易被收成錯誤結論的地方。挑戰者號 <!-- term:Challenger -->的紀錄很容易被讀成「規則寫得不夠嚴」：如果豁免 <!-- term:Waiver -->需要更高層核准，如果結案需要證明修好了，事故就不會發生。這些規則也許會有幫助。但它們仍是可被通過的形式。本文的主張不是這些規則寫錯了，而是任何規則被通過，都只證明形式成立。

## 實務對比

同一類檢查，通過時能證明什麼、不能證明什麼，可以並排看：

| 形式 | 通過時證明了什麼 | 通過時沒有證明什麼 | 挑戰者號 <!-- term:Challenger -->紀錄中的對應 |
| :--- | :--- | :--- | :--- |
| 需求文件的冗餘條款 | 冗餘要求有處置 | 硬體有冗餘 | Criticality 1 豁免 <!-- term:Waiver -->在 1983 年 3 月批准 |
| 發射限制 | 觀察在審查中被處理過 | 問題被解決 | 1985 年 7 月之後連續六次豁免 <!-- term:Waiver --> |
| 問題結案 | 有申請、有紀錄 | 修正已完成並被驗證 | 1985 年 12 月依要求申請結案，紀錄其後被認為錯誤 |
| 架構審查通過 | 文件與會議程序完成 | 架構是好的 | 無 |

前三列都是規則被滿足、而規則原本要防的事仍在。第四列沒有現場，只用來提醒：同一個形狀不限於太空梭。

## 結論

合規 <!-- term:Compliance -->不蘊含品質。規則覆蓋的情境裡存在通過檢查卻有害的決定；規則沒覆蓋的情境只能由判斷 <!-- term:Judgment -->承擔。

規則是過去判斷 <!-- term:Judgment -->的沉澱物。它被寫下的那一刻攜帶判斷 <!-- term:Judgment -->，之後只攜帶形式。

為「合規 <!-- term:Compliance -->但不正確」補上的規則，本身又是一個可被通過的形式。挑戰者號 <!-- term:Challenger -->的發射限制是對一次損壞的判斷 <!-- term:Judgment -->，隨後連續被豁免 <!-- term:Waiver -->六次。

評估一項制度時，該問的不是它能不能讓人無法做錯，而是它要求的東西被滿足時，當初寫下它的那個判斷 <!-- term:Judgment -->是否仍被做了一次。

事故之後，除了問哪條規則有漏洞，也要問：當時通過檢查的每一步，有哪一步重新做了判斷 <!-- term:Judgment -->。

## 來源

- Presidential Commission on the Space Shuttle Challenger Accident. (1986). *Report of the Presidential Commission on the Space Shuttle Challenger Accident*, Vol. 1, Chapter VI: An Accident Rooted in History. National Aeronautics and Space Administration. [https://www.nasa.gov/history/rogersrep/v1ch6.htm](https://www.nasa.gov/history/rogersrep/v1ch6.htm). 本文只引用該章寫明的 Criticality 1 豁免 <!-- term:Waiver -->、STS 51-B 侵蝕數據、1985 年 7 月的發射限制與其豁免 <!-- term:Waiver -->、12 月的結案紀錄，以及章末發現。
- Presidential Commission on the Space Shuttle Challenger Accident. (1986). *Report of the Presidential Commission on the Space Shuttle Challenger Accident*, Vol. 1, Chapter V: The Contributing Cause of the Accident. National Aeronautics and Space Administration. [https://www.nasa.gov/history/rogersrep/v1ch5.htm](https://www.nasa.gov/history/rogersrep/v1ch5.htm). 本文只引用章末第二項發現。
- 《論語·為政》。[中國哲學書電子化計劃](https://ctext.org/analects/wei-zheng)。作為對照，不作為論證。