+++
title = "生產力由模型與組織共同生產"
date = "2026-09-07T00:28:06+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "同一個工具在不同組織產生不同結果。用互補函數拆開流程適配、技能異質性、人工補償與資料回流，說明只量登入率為何會讓一半的因果消失。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "AI 代理人", # term:AiAgent
    "技術與組織互補", # term:OrganizationalComplementarity
    "人機協作", # term:HumanAiCollaboration
    "自動化反諷", # term:IroniesOfAutomation
    "人工補償", # term:HumanCompensation
    "中介變數", # term:MediatingVariable
    "資料回流", # term:DataFeedbackLoop
  ]
series = ["從能力宣稱到可驗證效用：AI 敘事的現實化鏈條"]
[ai_info]
    [ai_info.generation]
        model = "GPT 5.6 Sol"
        agent = "Codex VS Code extension 26.901.22334"
    [ai_info.refinement]
        model = "Claude Opus 5"
        agent = "Claude Code VSCode Extension 2.1.261"
+++

<!--more-->

## 導言

一項涵蓋 5,000 多名客服人員的實地研究發現，導入生成式 AI 助理後，每小時解決問題數平均提高約 15%，效果主要集中在較新、較低技能的工作者；高技能員工的增益較小。這不是模型固定「增加 15% 生產力」，而是工具、特定客服流程與人員經驗交互作用的結果。[Generative AI at Work](https://academic.oup.com/qje/article/140/2/889/7990658)

回過頭來看，真正要問的是：為何同一工具進入不同流程與人群，會產生不同甚至相反的結果？

## 分析

**技術與組織互補**（Organizational Complementarity） <!-- term:OrganizationalComplementarity -->指技術能力必須搭配流程重排與技能調整才形成產出。可用分析函數表示：

> [!IMPORTANT]
> **技術與組織互補** <!-- term:OrganizationalComplementarity --> (Organizational Complementarity): 技術能力必須搭配流程重排與技能調整才形成產出的互補關係。 <!-- anchor:OrganizationalComplementarity -->


$$
Y=Aq^\alpha o^{1-\alpha},\qquad 0<\alpha<1.
$$

$q$ 是任務上的模型品質，$o$ 是資料、權限、流程、訓練與例外處理的適配度，$A$ 是其他條件。乘法形式讓短板可見，但不是經驗普遍定律。真正效果還可能依技能 $s$ 改寫為 $Y(q,o,s)$。

客服案例可回推為：工具從高績效對話萃取可用模式，較新員工在即時建議下更快採用這些模式，解決率因此提高；原本已掌握模式的資深者可新增的知識較少。**中介變數**（Mediating Variable） <!-- term:MediatingVariable -->是建議採納、學習速度、處理時間與解決品質，而不是登入率。

> [!IMPORTANT]
> **中介變數** <!-- term:MediatingVariable --> (Mediating Variable): 位於原因與結果之間、承載並使該段因果得以被觀察的可測量變數。 <!-- anchor:MediatingVariable -->


共同生產還包含**人工補償**（Human Compensation） <!-- term:HumanCompensation -->：員工核對、改寫、找資料與處理例外。當日常工作被自動化，剩下的案例可能更難，人員又因少練習而較難接手。Bainbridge 將這種設計張力稱為**自動化反諷**（Ironies Of Automation） <!-- term:IroniesOfAutomation -->。[Ironies of Automation](https://www.sciencedirect.com/science/article/pii/0005109883900468)

> [!IMPORTANT]
> **人工補償** <!-- term:HumanCompensation --> (Human Compensation): 以人力審核與例外處理填補模型不可靠之處，使系統整體達到可交付品質的做法。 <!-- anchor:HumanCompensation -->
> **自動化反諷** <!-- term:IroniesOfAutomation --> (Ironies Of Automation): 自動化接手例行工作後，留給人的案例更難且練習更少，反而更難在關鍵時刻接管的設計張力。 <!-- anchor:IroniesOfAutomation -->


這張圖把隱形工作與**資料回流**（Data Feedback Loop） <!-- term:DataFeedbackLoop -->放回系統裡。讀者應注意回流資料也受介面和管理政策塑形。

> [!IMPORTANT]
> **資料回流** <!-- term:DataFeedbackLoop --> (Data Feedback Loop): 使用者接受、修改或拒絕的紀錄回到產品與流程更新，進而改變後續系統行為的循環。 <!-- anchor:DataFeedbackLoop -->


```mermaid
flowchart LR
    Q[模型品質] --> W[工作流程]
    O[流程適配] --> W
    W --> D{可直接採用？}
    D -->|是| A[執行]
    D -->|否| H[核對、改寫、例外]
    H --> A
    A --> R[客戶與營運結果]
    R --> L[接受、修改、拒絕紀錄]
    L --> M[產品更新]
    L --> P[流程與政策更新]
    M --> W
    P --> O
```

失效點包括員工無權拒絕、難例累積、回流標籤偏向管理目標，以及速度改善被重工抵銷。

### 可重現的機制隔離

接下來這段程式固定模型品質，操弄流程適配，並加入技能異質性。觀察量是平均產出及群組**差異**（Delta） <!-- term:Delta -->。

> [!IMPORTANT]
> **差異** <!-- term:Delta --> (Delta): 特定變更的契約，用於驅動實作並作為驗證實作的基準對象。 <!-- anchor:Delta -->


```python
def output(model_quality, process_fit, skill, alpha=0.5):
    complement = model_quality ** alpha * process_fit ** (1 - alpha)
    learning_gain = (1 - skill) * 0.20 * process_fit
    review_drag = skill * 0.10 * (1 - process_fit)
    return complement + learning_gain - review_drag

for fit in (0.4, 0.9):
    novice = output(0.9, fit, 0.2)
    expert = output(0.9, fit, 0.9)
    print(fit, round(novice, 3), round(expert, 3))
```

控制變因是模型品質和函數係數；操弄變因是流程適配與技能。預期強流程提高兩組結果，但增益不同。程式不能證明新手永遠受益較多；它只是隔離互補與異質性的可能機制。

## 反思

反例是可完全自動化、輸入規格固定且錯誤成本低的任務。若組織適配只需一次 API 串接，$o$ 的變異很小，模型改善可能主導結果。另一個反例是專家使用高品質科研工具：專家可能因判斷力而取得更大增益。

所以不能把客服研究外推到所有職業，也不能以平均值代表每種技能。把全部流程改造算成 AI 效益會高估模型；把永久合規覆核都算成模型失敗，也會低估完整服務。

要讓這個主張可被推翻，驗證契約是這樣設計的：資料是員工×週面板，導入前後各至少八週；依團隊與技能分層，70%估計、30%封存。隨機試驗 seed 為 53。指標包含每小時成功件數、一次解決率、客戶品質、重工、升級、覆核分鐘與員工學習。控制變因是案件難度、班次、團隊、模型版本與管理政策。觀察量是流程適配和技能是否中介效果。若只改善登入或速度而品質與總工時未改善，生產力宣稱被反駁；若客戶傷害或員工無法接管超過門檻，停止部署擴張。

## 實務對比

錯誤做法是購買工具後要求全員使用，以登入率當成功。較好的做法先選可逆、可覆核、低錯誤成本的子任務，建立基線，再分階段比較端到端結果與不同技能群組。

錯誤做法把人工覆核列為三個月後歸零的暫時成本。較好的做法把覆核分成學習期缺陷、模型不確定、法律責任與高風險例外；只有第一類可合理預期快速下降。

## 結論

AI 生產力不是模型隨安裝附送的常數。它由模型品質、流程適配、技能、人工補償 <!-- term:HumanCompensation -->與資料回流 <!-- term:DataFeedbackLoop -->共同生產。可信的採用證據必須量測端到端結果、異質效果與新增工作；若只量登入、速度或平均值，組織付出的那一半因果就會消失。