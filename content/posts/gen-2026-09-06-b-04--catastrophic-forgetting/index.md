+++
title = "新知識為何覆蓋舊能力：梯度干涉與災難性遺忘"
date = "2026-09-06T02:58:04+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "微調新任務後舊任務表現崩落，並不是參數自然老化。以梯度內積分析共享參數上的干涉，說明遺忘是支撐舊行為的結構被改寫。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "大型語言模型", # term:Llm
    "災難性遺忘", # term:CatastrophicForgetting
    "梯度干涉", # term:GradientInterference
    "彈性權重固化", # term:ElasticWeightConsolidation
    "實務對比", # term:PracticalContrastiveExamples
    "梯度下降", # term:GradientDescent
    "差異", # term:Delta
  ]
series = ["模型能力如何失效：在歸咎模型之前，先固定比較條件"]
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

模型先完成任務 A，再針對任務 B 微調，A 的表現可能急劇下降。這種**災難性遺忘**（Catastrophic Forgetting） <!-- term:CatastrophicForgetting -->確實涉及參數隨時間改變，但它不是參數自然老化。

> [!IMPORTANT]
> **災難性遺忘** <!-- term:CatastrophicForgetting --> (Catastrophic Forgetting): 針對新任務更新參數後，先前任務表現急劇下降的現象。 <!-- anchor:CatastrophicForgetting -->


更精確的問題是：同一組共享參數同時承載多項行為時，降低新任務損失的更新是否會提高舊任務損失？這可以從梯度方向直接分析。

## 分析

令兩個任務損失為 $L_A(\theta)$ 與 $L_B(\theta)$。針對 B 執行一步**梯度下降**（Gradient Descent） <!-- term:GradientDescent -->：

> [!IMPORTANT]
> **梯度下降** <!-- term:GradientDescent --> (Gradient Descent): 沿損失函數負梯度方向反覆更新參數的最佳化方法。 <!-- anchor:GradientDescent -->


$$
\theta'=\theta-\eta\nabla L_B(\theta).
$$

以一階近似觀察 A：

$$
L_A(\theta')\approx L_A(\theta)
-\eta\nabla L_A(\theta)^\top\nabla L_B(\theta).
$$

若兩個梯度內積為負，更新 B 會在局部提高 A 的損失。這稱為**梯度干涉**（Gradient Interference） <!-- term:GradientInterference -->。它提供一個機制，但不是遺忘的完整充分條件；學習率、曲率、資料順序與參數冗餘都會改變實際結果。

> [!IMPORTANT]
> **梯度干涉** <!-- term:GradientInterference --> (Gradient Interference): 不同任務的梯度方向相衝，使一方的更新提高另一方損失的情形。 <!-- anchor:GradientInterference -->


下面以兩個互相衝突的二次損失展示覆蓋過程：

```python
def loss_a(theta):
    return 0.5 * (theta - 1.0) ** 2

def loss_b(theta):
    return 0.5 * (theta + 1.0) ** 2

theta = 1.0
learning_rate = 0.25

for step in range(7):
    print(step, round(theta, 4),
          round(loss_a(theta), 4), round(loss_b(theta), 4))
    gradient_b = theta + 1.0
    theta -= learning_rate * gradient_b
```

參數從 A 的最佳點朝 B 的最佳點移動。B 的損失下降時，A 的損失上升；這不是所有多任務學習的宿命，只是兩個目標在這個參數方向上確實衝突。

**彈性權重固化**（Elastic Weight Consolidation） <!-- term:ElasticWeightConsolidation -->為舊任務重要參數加入二次懲罰：

> [!IMPORTANT]
> **彈性權重固化** <!-- term:ElasticWeightConsolidation --> (Elastic Weight Consolidation): 依參數對舊任務的重要性施加懲罰，以減緩遺忘的正則化方法。 <!-- anchor:ElasticWeightConsolidation -->


$$
L(\theta)=L_B(\theta)+
\frac{\lambda}{2}\sum_iF_i
(\theta_i-\theta^*_{A,i})^2.
$$

$F_i$ 近似參數對 A 的重要性。這使重要方向較難移動，但代價是降低可塑性；當任務真的需要重寫同一組參數時，保留與學習之間沒有免費解。

## 反思

遺忘是功能層現象，不等於某顆參數被刪除。神經網路具有重新參數化與分散表示，同樣大小的權重變化可能造成完全不同的行為影響。

反過來，舊任務分數不變也不保證內部表示沒有改組。只要輸出仍通過有限基準，功能漂移便可能被遮蔽。因此，參數距離與行為保留應分別測量。

## 實務對比

錯誤做法是比較微調前後的權重平均差，並把較小**差異**（Delta） <!-- term:Delta -->等同較少遺忘。大量不重要參數保持不變，仍可能掩蓋少數關鍵方向遭到破壞。

> [!IMPORTANT]
> **差異** <!-- term:Delta --> (Delta): 特定變更的契約，用於驅動實作並作為驗證實作的基準對象。 <!-- anchor:Delta -->


較好的做法會保存舊任務的資料切片與輸出基線，在每個微調階段重播。若不能保存原始資料，也可考慮生成重播、功能正則化或參數重要性近似，但每種方法都有資訊損失。

另一個錯誤是要求新舊能力都完全不變。當兩個任務定義互相矛盾，任何單一模型都必須接受取捨；此時問題不是找到神奇最佳化器，而是明確指定優先順序與容許損失。

## 結論

災難性遺忘 <!-- term:CatastrophicForgetting -->不是參數壽命耗盡，而是後續更新改變了支撐舊行為的共享結構。梯度內積提供局部干涉的可計算線索，卻不能取代完整行為測試。

持續學習的核心張力是穩定性與可塑性。保留舊能力需要限制更新，取得新能力又需要允許更新；合理方法只能管理這個衝突，不能宣稱將它普遍消除。

參數重要性與二次約束的經典方法見 Kirkpatrick 等人的 [Overcoming 災難性遺忘 <!-- term:CatastrophicForgetting --> in Neural Networks](https://pmc.ncbi.nlm.nih.gov/articles/PMC5380101/)。