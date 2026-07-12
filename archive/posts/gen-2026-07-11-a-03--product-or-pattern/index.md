+++
title = "獨立產品，還是既有核心的 pattern？"
date = "2026-07-11T00:36:03+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "假設你已經判斷某個候選是 runtime 產品(而非治理引擎的能力)。還有一刀要切：**它是 一個獨立產品，還是一個圍繞既有核心的 pattern？**"
tags = [
    "分析論述", # term:AnalyticalEssay
    "AI 代理人", # term:AiAgent
    "架構演進", # term:ArchitectureEvolution
    "收斂規劃器", # term:Reconciler
    "終局結果", # term:TerminalResult
    "殘差規劃", # term:ResidualPlanning
    "無狀態", # term:Stateless
    "擁有權", # term:Ownership
  ]
series = ["薄產品策略：看見空缺、節制野心與跨越邊界的決策漏斗"]
[ai_info]
    [ai_info.generation]
        model = "Claude Opus 4.8"
        agent = "Claude Code VSCode Extension 2.1.206"
    [ai_info.refinement]
        model = "Gemini 3.1 Pro"
        agent = "Antigravity IDE 2.1.1"
+++

<!--more-->

## 背景

假設你已經判斷某個候選是 runtime 產品(而非治理引擎的能力)。還有一刀要切：**它是
一個獨立產品，還是一個圍繞既有核心的 pattern？**

這一刀切錯會很痛。把一個本該是 pattern 的東西獨立成產品，你會得到兩套彼此重疊的
**身分**（Identity） <!-- term:Identity -->、狀態、**擁有權**（Ownership） <!-- term:Ownership -->——兩個核心搶同一種權威，長期互相污染。反過來，把一個真正正交的
產品硬塞成某核心的附庸，又會扭曲它的**形狀**（Data Shape） <!-- term:DataShape -->。這篇給出一個判準，並用一個具體案例——
「為昂貴且不可逆的操作設計 reconciler」——展示 pattern 是如何被一個產品的**困難個案**
拉出來的。

> [!IMPORTANT]
> **身分** <!-- term:Identity --> (Identity): 系統元件在架構中宣告的核心職責與自我定位。 <!-- anchor:Identity -->
> **擁有權** <!-- term:Ownership --> (Ownership): 系統元件對資料、狀態或生命週期的絕對控制權。 <!-- anchor:Ownership -->
> **形狀** <!-- term:DataShape --> (Data Shape): 資料結構或物件所包含的屬性與型別定義，通常由型別系統來描述 <!-- anchor:DataShape -->


## 分析

### 一、重建權威測試

判準只有一句：

> **這個候選，會不會重建既有核心已經擁有的權威？**
>
> 一個「有生命週期權威」的核心，通常擁有這幾樣：**身分 <!-- term:Identity -->、在途狀態
> (in-flight state)、擁有權 <!-- term:Ownership -->、**終局結果**（Terminal Result） <!-- term:TerminalResult -->、持久化
> (persistence)**。
>
> - 若候選會**重造這幾樣中的多個** → 它是這個核心周邊的一個 **pattern**，不是同輩
>   產品。
> - 若候選與核心**正交**(不共享任何權威) → 它可以是一個**獨立產品**。

> [!IMPORTANT]
> **終局結果** <!-- term:TerminalResult --> (Terminal Result): 系統執行完一系列狀態變更後的最終穩定一致狀態。 <!-- anchor:TerminalResult -->


例如，一個做「去重/**冪等**（Idempotent） <!-- term:Idempotent -->裁決」的候選：它需要身分 <!-- term:Identity -->、在途、終局結果 <!-- term:TerminalResult -->、持久紀錄——這正是
一個生命週期核心已經有的東西。若讓它獨立，它會重建一整套平行的身分 <!-- term:Identity -->與狀態。結論：
它是核心的一個 pattern(以裁決策略的形式附著)，不是獨立產品。持久生命週期仍由核心
擁有。

> [!IMPORTANT]
> **冪等** <!-- term:Idempotent --> (Idempotent): 一個步驟可反覆執行而結果穩定的性質；對已是最新狀態的產物再跑一次，應為無變更。 <!-- anchor:Idempotent -->


### 二、正交是必要條件，不是充分條件

這裡有一個很容易滑倒的地方：**「它不與產品 #1 重疊」不等於「它該成為產品 #2」。**

正交(不重建核心權威)只證明了它**可以**獨立，沒證明它**該**現在獨立。「不撞既有
產品」是必要條件；充分條件是**有一個真實消費者在拉它**。用「它很正交、很優雅、很
互補」當作獨立的理由，就是把「不耦合」冒充成「被需要」——這是一個很體面的陷阱，因為
理由聽起來都對。

所以次序是：先用重建權威測試排除掉 pattern；剩下的正交候選裡，只有**已經有消費者**
的那個，才值得現在被拉成獨立產品線。其餘正交候選，保留其世界觀，等各自的消費者
出現。

### 三、pattern 如何附著：核心保持不知情

一個 pattern 附著到核心的方式，是**選配的橋接**，而不是核心把它吸收進來：

- pattern 的純核心可以**孤立地原型化**(它多半是一個 sans-I/O 的純函數/狀態機)，
  在真空裡單元測試學形狀 <!-- term:DataShape -->，先不接線。
- 等到它的消費場景真的成形(見下一節的案例)，再由一個**單向的橋接**把它接上核心。
- 核心**對這個 pattern 一無所知**：它照樣可以獨立使用。這保證了核心不被 pattern 綁死。

### 四、案例：為昂貴且不可逆的操作設計 reconciler

考慮一個常見的 runtime 產品：**收斂規劃器**（Reconciler） <!-- term:Reconciler -->——比較「期望狀態」與
「觀測狀態」，推導出要做哪些修正。當修正動作是**便宜且冪等** <!-- term:Idempotent -->時(例如寫一個設定值)，
一個天真的 level-triggered 迴圈就夠了：觀測、動作、再觀測、重複；重發也無所謂。

> [!IMPORTANT]
> **收斂規劃器** <!-- term:Reconciler --> (Reconciler): 負責比對當前狀態與期望狀態，並計算出收斂路徑的核心元件。 <!-- anchor:Reconciler -->


但當修正是**昂貴且不可逆**時(例如佈署一台實體機、切換 DNS、遷移資料庫)，同一個
天真迴圈會出事：level-triggered 每個週期都會**重發同一個修正**，直到世界收斂——而
重發一個不可逆的昂貴操作是災難。這個困難個案，逼出五個設計性質：

1. **先計畫，後動作。** 規劃器產出一份**可檢視、可審批**的計畫(而不是直接觸發副
   作用)。因為不可逆，必須讓人或政策在動手前 gate。
2. **殘差規劃**（Residual Planning） <!-- term:ResidualPlanning -->。** diff 的對象是「觀測 ∪ 在途」，而不是只有觀測。
   規劃器被餵進「已經在進行中的修正」並扣掉它們，於是再觀測不會重發一個正在執行的
   操作。
3. **在接縫處做冪等 <!-- term:Idempotent -->的 create-or-attach。** 一個被重發的修正，應**附著到既有的義務**，
   而不是產生一筆重複義務。
4. **標記不可逆，絕不承諾 rollback。** 核心永遠不假裝能撤銷一個 one-way 操作；要不要
   放行，交給 gate。
5. **補償只在「明確決定退卻」時觸發，不在失敗時自動觸發。** 失敗後由一個 recovery
   policy 決定 retry / replan / retreat / escalate；只有選 retreat，才交給補償邏輯去
   推導有序的回退。

> [!IMPORTANT]
> **殘差規劃** <!-- term:ResidualPlanning --> (Residual Planning): 將複雜問題拆解，由核心解決主幹，其餘邊角案例交由上層或周邊處理的策略。 <!-- anchor:ResidualPlanning -->


看清楚這裡發生了什麼：**「冪等 <!-- term:Idempotent -->」(性質 3)與「補償」(性質 5)這兩個 pattern，是被
reconciler 這個產品的困難個案拉出來的。** 它們不是憑空獨立的產品，而是「一個昂貴/
不可逆的收斂迴圈」這個真實消費者所需要的附著 pattern。這正好同時印證了第一、二節：
它們通過重建權威測試被判為 pattern(冪等 <!-- term:Idempotent -->要用到身分 <!-- term:Identity -->/在途/終局)，且它們的第一個消費
者是明確的(這個迴圈)。

## 省思

**先射箭再畫靶的風險。** 第二節的教訓在這裡加倍：很容易因為「這個正交產品很優雅、
剛好補足我的專長」就把它預定為產品 #2。但優雅不是消費者。若沒有一個真實的困難個案
在拉它，它就是一塊正交版的「乾淨但未證實」。

**組合必須讓核心保持 agnostic。** 即便你決定做那個橋接(例如把 reconciler 接上一個
持久義務核心)，reconciler 的核心也應該**能在沒有那個核心時獨立運作**(在途集合給空
即退化成**無狀態**（Stateless） <!-- term:Stateless -->收斂)。一旦核心開始假設某個特定 pattern 存在，你就失去了「核心不被
pattern 綁死」這個最重要的性質。

> [!IMPORTANT]
> **無狀態** <!-- term:Stateless --> (Stateless): 不依賴任何中介追蹤檔、任務完成與否完全由輸出目錄的實體檔案決定的設計，帶來冪等性與韌性。 <!-- anchor:Stateless -->


**pattern 與產品的界線會隨消費者移動。** 今天判為 pattern 的東西，若哪天出現一個
「完全不需要那個核心、只需要它自己」的真實消費者，它就可能升格為獨立產品。判準始終
回到消費者，而不是一次性的分類。

## 結論

可攜的原則：

1. **重建權威測試**：候選若重造既有核心的身分 <!-- term:Identity -->/在途/擁有權 <!-- term:Ownership -->/終局/持久，它是 pattern，
   不是同輩產品；正交才可能是獨立產品。
2. **正交是必要非充分**：「不撞既有產品」≠「該成為新產品」；充分條件是有真實消費者
   在拉。別讓優雅冒充需要。
3. **pattern 靠孤立純核 + 單向橋接附著**，核心對它不知情、可獨立使用。
4. **困難個案拉出 pattern**：以昂貴/不可逆 reconciler 為例，先計畫後動作、殘差規劃 <!-- term:ResidualPlanning -->、
   接縫冪等 <!-- term:Idempotent -->、標記不可逆、補償只在明確退卻時觸發——冪等 <!-- term:Idempotent -->與補償兩個 pattern 正是被這個
   產品的困難個案拉出來的。
5. **界線隨消費者移動**：分類不是一次定終身；新的、只需要它自己的消費者出現時，
   pattern 可升格為產品。