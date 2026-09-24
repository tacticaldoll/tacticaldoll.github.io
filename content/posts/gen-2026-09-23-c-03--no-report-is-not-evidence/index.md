+++
title = "沒有人回報問題，不能用來證明沒有問題"
date = "2026-09-23T11:30:03+08:00"
author = "梅乾"
draft = false
isCJKLanguage = true
description = "零回報不能證明沒有問題。從挑戰者號發射前的資訊截留與組織沉默研究，檢視沉默如何讓決策者失去判斷依據。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "組織沉默", # term:OrganizationalSilence
    "似然比", # term:LikelihoodRatio
    "沉默氛圍", # term:ClimateOfSilence
    "順從性沉默", # term:AcquiescentSilence
    "防衛性沉默", # term:DefensiveSilence
    "親社會沉默", # term:ProsocialSilence
    "程序正義", # term:ProceduralJustice
  ]
series = ["表徵治理：通過、摘要與零回報如何取代現場"]
term_exclude = ["Guidelines", "Prerequisite"]
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

一次會議結束前，主持人問：有沒有人有任何限制事項或疑慮？沒有人開口。會議紀錄寫下「無」。這個「無」有兩個完全不同的世界可以生成它：一個是真的沒有問題；另一個是有問題，但知道問題的人沒有把它送到這個房間。紀錄本身無法區分這兩個世界。

**組織沉默**（Organizational Silence） <!-- term:OrganizationalSilence -->指的是組織成員保留、而非表達與工作相關的想法、資訊與意見。本文只處理一個主張：當沉默由結構生產時，「沒有收到回報」對「沒有問題」與「有問題但沒人說」幾乎沒有鑑別力。由此推出，資訊治理不能靠在管道下游加裝更多量測；必須先查清楚是什麼讓資訊不進管道。

> [!IMPORTANT]
> **組織沉默** <!-- term:OrganizationalSilence --> (Organizational Silence): 第一線知情無法轉化為系統修正時，由制度性恐懼所維繫的發聲停滯。 <!-- anchor:OrganizationalSilence -->


本文不處理資訊進了管道之後在層層摘要中衰減的情形。那是另一種失真，需要不同的工具。

## 分析

### 零回報的鑑別力

令觀測 $O$ 為「沒有收到問題回報」。世界有兩種狀態：$H_0$ 沒有問題，$H_1$ 有問題但資訊被保留。依貝氏定理，觀測之後兩種狀態的勝算比為：

$$
\frac{P(H_1 \mid O)}{P(H_0 \mid O)} = \frac{P(O \mid H_1)}{P(O \mid H_0)} \cdot \frac{P(H_1)}{P(H_0)}
$$

若 $H_0$ 為真，$P(O \mid H_0)$ 接近 1，因為沒有東西可報。若沉默機制存在，$P(O \mid H_1)$ 也接近 1，因為有東西可報但沒人報。兩者的比值，也就是**似然比**（Likelihood Ratio） <!-- term:LikelihoodRatio -->，接近 1。觀測之後的勝算比於是幾乎等於觀測之前的勝算比。看到零回報之後，對世界狀態的信念幾乎不該改變。

> [!IMPORTANT]
> **似然比** <!-- term:LikelihoodRatio --> (Likelihood Ratio): 在特定假設成立與不成立下觀測到同一徵候的條件機率之比，決定貝氏後驗更新的幅度。 <!-- anchor:LikelihoodRatio -->


這個推論不說零回報代表有問題。它說零回報不代表任何事。先驗仍然決定一切，而觀測沒有提供更新先驗的材料。

違反這個推論的情況是：存在某種訊號，只要問題存在就必然出現。但「必然出現」要求資訊通道不被沉默截斷，也就是把要證明的東西當成了前提。

Van Dyne、Ang 與 Botero (2003) 從另一個方向得到相近的命題：沉默比發聲更模糊，觀察者更容易誤判沉默背後的動機。發聲至少留下一段可以被檢查的話。沉默什麼都沒留下。

### 已發生的現場：徵詢限制事項，沒有得到回報

**挑戰者號**（Challenger） <!-- term:Challenger -->事故總統調查委員會的報告第五章，記下了一次可以逐小時對照的零回報。以下事實出自該章。

> [!IMPORTANT]
> **挑戰者號** <!-- term:Challenger --> (Challenger): 1986 年發射失事的太空梭；其調查紀錄用於檢視豁免、摘要與資訊回報的失效。 <!-- anchor:Challenger -->


太空梭的決策分層：馬歇爾太空飛行中心的推進器計畫屬於 Level III，詹森太空中心的計畫經理屬於 Level II，總部的太空飛行副署長屬於 Level I。負責發射的是 Level I 與 Level II 管理層。

1986 年 1 月 27 日中午 12 時 36 分，當天的發射因側風取消。隨後約半小時的討論中，所有相關人員都被徵詢 24 小時內發射是否可行，並被要求提出任何限制事項。報告寫道，這次會議沒有產生任何關於固態火箭推進器表現的限制或疑慮。下午 2 時的任務管理小組會議討論了低溫對發射設施的影響，同樣沒有人對推進器的 O 形環表示疑慮；所有成員被要求重新檢視狀況，若有任何問題就打電話回報。

同一天下午約 2 時 30 分，在猶他州的承包商工廠，一位經理得知預報的低溫後召集了工程師。他事後回憶，工程師們對這個低溫「非常堅決地表達了疑慮」，因為它遠低於資料庫的範圍，也遠低於資格驗證的溫度。當晚的電話會議上，承包商工程部門建議不要在 O 形環溫度低於 53°F 時發射。承包商管理層在一次離線討論之後改變立場，建議發射。

沒有人為此打電話給 Level II。晚上約 11 時 30 分，推進器計畫經理打給 Level II 的計畫經理，談的是回收區的天氣；他作證說，他沒有和對方談剛結束的那場承包商會議。1 月 28 日上午 9 時的任務管理小組會議討論了發射台的結冰，報告的年表記著：沒有明顯討論溫度對 O 形環密封的影響。

聴證中，委員問馬歇爾的太空梭計畫經理：你是不是實際上做出不把此事升級到 Level II 的決定的人？他答：是的。推進器計畫經理說明，他認為那是 Level III 的問題，沒有違反任何發射準則，不需要**豁免**（Waiver） <!-- term:Waiver -->。馬歇爾中心主任被問到為何沒有轉告上級時說：那不是回報管道。委員會主席逐一詢問甘迴迪太空中心主任、發射主任、計畫經理與太空飛行副署長，發射前是否知道承包商的反對。四個人都答：不知道。

> [!IMPORTANT]
> **豁免** <!-- term:Waiver --> (Waiver): 經批准而不適用特定限制的例外處置；形式上的批准不代表原本的風險已消失。 <!-- anchor:Waiver -->


委員會的結論是：做出發射決定的人不知道 O 形環與接頭近期的問題歷史，不知道承包商最初的書面建議，也不知道管理層改變立場後工程師持續的反對；如果決策者知道全部事實，極不可能在 1 月 28 日發射。委員會的第三項發現寫道：令委員會不安的是，馬歇爾管理層似乎傾向於把潛在的嚴重問題留在內部解決，而不是往前傳達。

從 Level I 與 Level II 的位置看，從 1 月 27 日下午到發射當天早上，他們得到的觀測就是 $O$：要求有問題就回報，沒有回報。而 $H_1$ 為真。

這份紀錄不能被整齊地歸成員工不敢說。工程師說了，而且說得很清楚。資訊停在一個**判斷**（Judgment） <!-- term:Judgment -->「這不需要往上送」的層級。報告第六章另記下一位承包商經理的證詞：他曾認為在問題修好之前不應再出貨任何火箭發動機；被問到是否表達過這個疑慮時，他說：「很不幸，沒有對對的人說。」另一位工程師描述當晚的離線討論時說，他在發現沒有人要聽之後就停下了。

> [!IMPORTANT]
> **判斷** <!-- term:Judgment --> (Judgment): 面對規則未覆蓋或情境已改變時，根據脈絡評估決定的實質後果。 <!-- anchor:Judgment -->


報告沒有提供足夠的材料判定這些人的動機。本文不把他們歸入任何一種沉默的類型。本文只需要一件事：從決策者的位置看，機制是什麼並不改變 $O$ 的鑑別力。

### 沉默是氛圍，不是性格

Morrison 與 Milliken (2000) 把沉默從個人屬性重新定位為集體現象。他們提出**沉默氛圍**（Climate of Silence） <!-- term:ClimateOfSilence -->的概念：組織中廣泛共享的一種信念，認為談論問題是徒勞的，或是危險的。依他們的模型，這個信念在成員彼此交換「說了會怎樣」的判讀中形成。這是理論命題，不是該文的實證發現。

> [!IMPORTANT]
> **沉默氛圍** <!-- term:ClimateOfSilence --> (Climate of Silence): 組織成員共享的信念：談論問題徒勞無功，或可能帶來負面後果。 <!-- anchor:ClimateOfSilence -->


Milliken、Morrison 與 Hewlin (2003) 訪談了 40 名員工，多數人都曾對某個問題有疑慮卻沒有向上提出。最常被提到的理由，是怕被看成或被貼上負面標籤，進而損害珍視的關係。在當事人的計算裡，沉默是安全的選項，發聲才是要付出代價的那個。

若沉默是氛圍，招募更敢說話的人就不是解方。新人學習組織規範的第一課，就是觀察什麼話沒有人說。氛圍由管理實踐與結構生產，也只能在同一層次被改變。

### 三種動機，三種介入

Van Dyne、Ang 與 Botero (2003) 依動機把沉默分成三型。三型對應不同的失效，介入不能通用：

| 類型 | 驅動動機 | 當事人的狀態 | 對應的介入 |
| :--- | :--- | :--- | :--- |
| **順從性沉默**（Acquiescent Silence） <!-- term:AcquiescentSilence --> | 認為說了也沒用 | 放棄、脫離 | 用可見的行動證明發聲會被處理 |
| **防衛性沉默**（Defensive Silence） <!-- term:DefensiveSilence --> | 害怕後果 | 判斷 <!-- term:Judgment -->仍在，主動隱瞞 | 建立**程序正義**（Procedural Justice） <!-- term:ProceduralJustice -->，證明說真話不會被記下來秋後算帳 |
| **親社會沉默**（Prosocial Silence） <!-- term:ProsocialSilence --> | 為保護他人或組織而保留 | 仍投入，但資訊被截留 | 把「讓組織知道真相」納入忠誠的內容 |

> [!IMPORTANT]
> **順從性沉默** <!-- term:AcquiescentSilence --> (Acquiescent Silence): 因認為發聲也不會改變結果而放棄表達的沉默。 <!-- anchor:AcquiescentSilence -->
> **防衛性沉默** <!-- term:DefensiveSilence --> (Defensive Silence): 因擔心發聲的後果而主動保留工作相關資訊的沉默。 <!-- anchor:DefensiveSilence -->
> **程序正義** <!-- term:ProceduralJustice --> (Procedural Justice): 決策程序納入意見、保持一致且可修正，使提出異議的人相信意見會受到公平處理。 <!-- anchor:ProceduralJustice -->
> **親社會沉默** <!-- term:ProsocialSilence --> (Prosocial Silence): 為保護同事或組織而有意保留資訊的沉默，即使動機善意仍可能截斷回報。 <!-- anchor:ProsocialSilence -->


第三型最反直覺。它的動機常常是好的：保護犯錯的同事，避免團隊在客戶面前難堪，不讓組織的弱點暴露給不友善的審查者。結果與前兩型相同：決策者接觸不到現實。由此得出一個不舒服的推論：成員忠誠度高，不能作為沉默不存在的證據。高忠誠可能正以親社會沉默 <!-- term:ProsocialSilence -->的形式截留資訊，而當事人不覺得自己有問題，任何「鼓勵發聲」的通用訊息都觸及不到他們。

### 誰從沉默中得利

主流研究預設沉默是管理層想解決的問題。Donaghey、Cullinane、Dundon 與 Wilkinson (2011) 拒絕這個預設：要理解沉默，必須承認沉默有時對管理層有利，因此管理層可能有維持甚至製造沉默的動機。機制不是明文禁言，而是議程設定與制度結構：把異議定義為不建設性，設計出有形式無回應的管道，讓特定議題系統性地進不了議程。員工於是被「安排出」發聲過程，而沒有任何人被明令禁止說話。

Pinder 與 Harlos (2001) 把沉默界定為員工對感知到的不公所做的回應。沿著這條線讀，沉默在低權力位置上常是理性選擇；把它當成偏差來處理，等於懲罰理性。

這決定了一個檢查順序：在設計任何發聲機制之前，先查現有制度在功能上獎勵什麼。若異議在考核、晉升與議程設定中實際被懲罰，不需要明文，只需要可觀察的模式，那麼新增的管道只是表演。功能性的獎勵比宣告性的政策更能預測行為。

管道還有兩個前置條件。第一是程序正義 <!-- term:ProceduralJustice -->：決策是否納入意見、前後一致、基於準確資訊、可修正、無偏見。Tangirala 與 Ramanujam (2008) 對 30 個工作群體、606 名護理師的調查發現，程序正義 <!-- term:ProceduralJustice -->氛圍較高時，群體認同與職業承諾抑制沉默的作用更強。第二是**互動正義**（Interactional Justice） <!-- term:InteractionalJustice -->：Colquitt (2001) 把它拆成人際與資訊兩面，也就是執行決策的人是否以尊嚴與尊重對待當事人，是否提供解釋。

> [!IMPORTANT]
> **互動正義** <!-- term:InteractionalJustice --> (Interactional Justice): 執行決策時以尊重對待當事人，並提供充分的資訊與解釋。 <!-- anchor:InteractionalJustice -->


反過來，調查意見卻不行動，會留下具體的、可引用的「說了也沒用」的證據。這正是順從性沉默 <!-- term:AcquiescentSilence -->賴以維持的材料。

## 反思

本文不主張所有零回報都來自沉默。多數時候，沒有回報可能真的是因為沒有問題。本文的主張更窄：在沉默機制可能存在的組織裡，零回報不提供區分兩者的材料。要區分，得從別處取得證據。

本文也不處理資訊進入管道之後的衰減。即使每個人都說了，層層摘要仍會丟掉判斷 <!-- term:Judgment -->與預測。那是另一種失敗，與沉默互相獨立。治好沉默，不治好摘要；縮短摘要鏈，也不使不說的人開口。

挑戰者號 <!-- term:Challenger -->的紀錄容易被收成兩個不屬於本文的結論。第一個是「工程師應該更勇敢」。工程師說了。資訊停在別處。第二個是「中間管理層隱瞞」。委員會用的詞是「傾向於留在內部解決」，並把它與一個容許內部安全問題繞過關鍵管理者的結構並列。本文不需要壞人。從 Level I 的位置看，零回報在那一天不是證據，這句話成立不依賴任何人的動機。

## 實務對比

同樣是「沒有聽到壞消息」，不同的觀測能排除的東西不同：

| 觀測 | 它能排除什麼 | 它不能排除什麼 |
| :--- | :--- | :--- |
| 零事故回報 | 已被回報的事故 | 未被回報的事故與前兆 |
| 全員調查沒有負面意見 | 願意在調查中表達的不滿 | 對調查本身不信任的人所保留的資訊 |
| 會議中徵詢限制事項，無人回應 | 在場者願意當場提出的限制 | 停在其他層級、沒有被送進這個房間的限制 |
| 有人提出異議，被記錄，且回應可見 | 較少：這是少數能提供鑑別力的觀測 | 仍不能排除親社會沉默 <!-- term:ProsocialSilence --> |

前三列都是零回報的變形，似然比 <!-- term:LikelihoodRatio -->都接近 1。第四列不同：它是一個發聲被處理過的紀錄。它本身提供資訊，也改變之後每一次零回報的意義，因為它降低了 $P(O \mid H_1)$。

## 結論

零回報無法區分「沒有問題」與「有問題但沒人說」。在沉默機制存在的組織裡，它的似然比 <!-- term:LikelihoodRatio -->接近 1，看到它之後不該更新信念。

挑戰者號 <!-- term:Challenger -->發射前一天，任務管理小組要求有問題就回報，直到發射當天早上都沒有收到 O 形環的回報；同一段時間，承包商工程師正在反對發射。

沉默是氛圍，不是性格。它由結構生產，靠共享的判讀維持，成因消失後仍可存續。

先分型，再介入。順從、防衛、親社會三型的藥方互不通用；高忠誠不是沉默不存在的證據。

先查現有制度在功能上獎勵什麼，再建管道。程序正義 <!-- term:ProceduralJustice -->與可見的回應是管道的前置條件，順序不能反。

## 來源

- Presidential Commission on the Space Shuttle Challenger Accident. (1986). *Report of the Presidential Commission on the Space Shuttle Challenger Accident*, Vol. 1, Chapter V: The Contributing Cause of the Accident. National Aeronautics and Space Administration. [https://www.nasa.gov/history/rogersrep/v1ch5.htm](https://www.nasa.gov/history/rogersrep/v1ch5.htm). 本文只引用該章寫明的 1 月 27 日至 28 日會議紀錄與年表、承包商工程師的疑慮與建議、聽證問答、委員會主席的逐一詢問，以及章首與章末的結論。
- Presidential Commission on the Space Shuttle Challenger Accident. (1986). *Report of the Presidential Commission on the Space Shuttle Challenger Accident*, Vol. 1, Chapter VI: An Accident Rooted in History. National Aeronautics and Space Administration. [https://www.nasa.gov/history/rogersrep/v1ch6.htm](https://www.nasa.gov/history/rogersrep/v1ch6.htm). 本文只引用該章所記承包商經理「沒有對對的人說」的證詞。
- Morrison, E. W., & Milliken, F. J. (2000). Organizational silence: A barrier to change and development in a pluralistic world. *Academy of Management Review*, 25(4), 706–725. [https://doi.org/10.5465/amr.2000.3707697](https://doi.org/10.5465/amr.2000.3707697)
- Milliken, F. J., Morrison, E. W., & Hewlin, P. F. (2003). An exploratory study of employee silence: Issues that employees don't communicate upward and why. *Journal of Management Studies*, 40(6), 1453–1476. [https://doi.org/10.1111/1467-6486.00387](https://doi.org/10.1111/1467-6486.00387)
- Van Dyne, L., Ang, S., & Botero, I. C. (2003). Conceptualizing employee silence and employee voice as multidimensional constructs. *Journal of Management Studies*, 40(6), 1359–1392. [https://doi.org/10.1111/1467-6486.00384](https://doi.org/10.1111/1467-6486.00384)
- Donaghey, J., Cullinane, N., Dundon, T., & Wilkinson, A. (2011). Reconceptualising employee silence: Problems and prognosis. *Work, Employment and Society*, 25(1), 51–67. [https://doi.org/10.1177/0950017010389239](https://doi.org/10.1177/0950017010389239)
- Pinder, C. C., & Harlos, K. P. (2001). Employee silence: Quiescence and acquiescence as responses to perceived injustice. In *Research in Personnel and Human Resources Management* (Vol. 20, pp. 331–369). ISBN 0762308400. [https://doi.org/10.1016/S0742-7301(01)20007-3](https://doi.org/10.1016/S0742-7301(01)20007-3)
- Tangirala, S., & Ramanujam, R. (2008). Employee silence on critical work issues: The cross-level effects of procedural justice climate. *Personnel Psychology*, 61(1), 37–68. [https://doi.org/10.1111/j.1744-6570.2008.00105.x](https://doi.org/10.1111/j.1744-6570.2008.00105.x)
- Colquitt, J. A. (2001). On the dimensionality of organizational justice: A construct validation of a measure. *Journal of Applied Psychology*, 86(3), 386–400. [https://doi.org/10.1037/0021-9010.86.3.386](https://doi.org/10.1037/0021-9010.86.3.386)