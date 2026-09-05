+++
title = "AI 為何不是普通 SaaS：推論成本、雲端租金與毛利結構"
date = "2026-09-06T03:14:05+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "一份程式服務大量客戶的想像，遇上每次請求都要推論的現實。追蹤貢獻利益如何隨使用強度變化，以及雲端平台在這個市場的雙重位置。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "大型語言模型", # term:Llm
    "貢獻利益", # term:ContributionMargin
    "自回歸", # term:Autoregressive
    "實務對比", # term:PracticalContrastiveExamples
    "人工補償", # term:HumanCompensation
    "反思", # term:Reflection
    "導言", # term:Introduction
  ]
series = ["智慧敘事如何進入現實：不是市場受騙，而是敘事協調了投資與改造"]
[ai_info]
    [ai_info.generation]
        model = "GPT 5.6 Sol"
        agent = "Codex VS Code extension 26.901.22334"
    [ai_info.refinement]
        model = "Claude Opus 5"
        agent = "Claude Code VSCode Extension 2.1.261"
+++

---

<!--more-->

## 導言

傳統 SaaS 的一份程式可以服務大量客戶，因此常被想像成新增使用量幾乎免費。生成式 AI 每次請求卻需要推論，輸入長度、輸出長度、模型大小與延遲承諾都會消耗計算資源。

AI 仍可採訂閱制或 API 計價，但收入形式相同不表示成本結構相同。若忽略使用量與人工審核，席次成長可能同時增加收入與交付成本。

## 分析

單位期間的簡化**貢獻利益**（Contribution Margin） <!-- term:ContributionMargin -->可寫成：

> [!IMPORTANT]
> **貢獻利益** <!-- term:ContributionMargin --> (Contribution Margin): 收入扣除隨使用量變動的成本後，可用以覆蓋固定支出的餘額。 <!-- anchor:ContributionMargin -->


$$
CM=R-C_{\mathrm{serving}}
-C_{\mathrm{support}}-C_{\mathrm{review}}-C_{\mathrm{other}}.
$$

服務成本 $C_{\mathrm{serving}}$ 不應重複計算。自建推論時，它包含晶片折舊、能源與網路；呼叫第三方 API 時，這些支出被包成雲端租金。兩者會計位置不同，物理資源並未消失。正式財報的毛利仍須依公司會計分類計算，不能直接套用這條內部單位經濟式。

下面比較固定月費在不同使用強度下的貢獻毛利。數字只是假設，用來展示方向：

```python
monthly_price = 30.0
fixed_service_cost = 4.0
cost_per_request = 0.008
review_cost_per_flagged_request = 0.60
flag_rate = 0.02

for requests in (100, 1000, 5000):
    variable = requests * (
        cost_per_request + flag_rate * review_cost_per_flagged_request
    )
    contribution = monthly_price - fixed_service_cost - variable
    margin = contribution / monthly_price
    print(requests, round(contribution, 2), round(margin, 3))
```

若價格固定而使用量無上限，重度使用者可能壓縮毛利。供應商可以透過速率限制、分級模型、快取、批次處理與用量計價改變曲線，但每種方法也會影響品質或體驗。

**大型語言模型**（Large Language Model） <!-- term:LargeLanguageModel -->還有**自回歸**（Autoregressive） <!-- term:Autoregressive -->特性：輸出 token 逐步生成，請求完成時間與輸出長度相關。服務系統會用動態批次與記憶體管理提升吞吐，顯示推論成本不是單純拿模型大小乘以請求數。

> [!IMPORTANT]
> **大型語言模型** <!-- term:LargeLanguageModel --> (Large Language Model): 基於海量文本數據訓練的深層神經網路模型，用於處理、生成和理解自然語言 <!-- anchor:LargeLanguageModel -->
> **自回歸** <!-- term:Autoregressive --> (Autoregressive): 逐步以先前輸出作為後續輸入條件的生成方式，使完成時間與輸出長度相關。 <!-- anchor:Autoregressive -->


雲端平台在這個市場具有雙重位置。它既向應用商收取運算與模型服務費，也可能直接銷售 AI 應用；上層 SaaS 的收入成長，可能同時成為下層雲端的租金收入。

## 反思

稱 AI 不是「普通 SaaS」不表示所有傳統 SaaS 都有零邊際成本。儲存、影音、搜尋與客服本來就有使用成本；生成式推論只是讓成本與互動量的連動更明顯。

模型效率提升也不必然降低總支出。單次推論變便宜可能刺激更多使用，形成反彈效應。單位成本、總成本與產品毛利必須分開觀察。

## 實務對比

錯誤做法是用年度訂閱收入除以席次，便宣稱 AI 產品具有軟體式高毛利。這沒有扣除每次推論、第三方模型費與人工處理成本。

較好的做法按客戶與工作負載計算貢獻毛利，並區分訓練、推論和產品整合。訓練是前置投資，推論隨使用發生；兩者混在一起會看不出規模是否改善經濟性。

另一個錯誤是引用單一 API 價格作永久成本。價格、模型版本、批次折扣與硬體效率會改變；案例必須附日期與服務條件。

## 結論

AI 可以用 SaaS 方式販售，但它把持續推論帶回每次互動。商業模式是否成立，取決於價格、使用強度、服務效率與**人工補償**（Human Compensation） <!-- term:HumanCompensation -->，而非「軟體」標籤本身。

> [!IMPORTANT]
> **人工補償** <!-- term:HumanCompensation --> (Human Compensation): 以人力審核與例外處理填補模型不可靠之處，使系統整體達到可交付品質的做法。 <!-- anchor:HumanCompensation -->


真正需要追蹤的是單位經濟如何隨規模變化。效率提高若快於價格下降與用量增加，毛利可以擴張；反之，採用越成功也可能需要越多資本與運算。

自回歸 <!-- term:Autoregressive -->模型的服務排程見 [Orca](https://www.usenix.org/conference/osdi22/presentation/yu)，記憶體管理見 [PagedAttention](https://arxiv.org/abs/2309.06180)。作為有日期的企業揭露案例，Microsoft 在截至 2026 年 6 月的 [Form 10-K](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm) 中同時描述 AI 基礎設施投資、使用成長與毛利壓力。