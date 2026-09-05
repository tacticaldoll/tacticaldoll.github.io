+++
title = "梯度如何塑造參數：從線性模型到反向傳播"
date = "2026-09-06T02:36:02+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "模型能表示某個函數，不代表訓練找得到它。拆解反向傳播如何把輸出誤差分配到各層參數，以及梯度下降如何把這些訊號轉成實際更新。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "大型語言模型", # term:Llm
    "梯度下降", # term:GradientDescent
    "反向傳播", # term:Backpropagation
    "實務對比", # term:PracticalContrastiveExamples
    "差異", # term:Delta
    "反思", # term:Reflection
    "導言", # term:Introduction
  ]
series = ["統計模型如何學習：同一套骨架，如何長出不同的參數與表示"]
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

模型能表示某個函數，不代表訓練一定能找到它。神經網路的能力還取決於誤差如何穿過計算圖，以及每個參數收到多少修正訊號。

**梯度下降**（Gradient Descent） <!-- term:GradientDescent -->與**反向傳播**（Backpropagation） <!-- term:Backpropagation -->分別回答兩個問題：參數應朝哪個方向移動，以及複合函數的導數如何有效計算。它們是現代深度學習共享的製程，不是某一種網路的專屬智慧。

> [!IMPORTANT]
> **梯度下降** <!-- term:GradientDescent --> (Gradient Descent): 沿損失函數負梯度方向反覆更新參數的最佳化方法。 <!-- anchor:GradientDescent -->
> **反向傳播** <!-- term:Backpropagation --> (Backpropagation): 以連鎖律沿計算圖回傳誤差，有效求得各層參數梯度的演算法。 <!-- anchor:Backpropagation -->


## 分析

對損失 $L(\theta)$，最基本的更新式為：

$$
\theta_{t+1}=\theta_t-\eta\nabla_\theta L(\theta_t),
$$

其中 $\eta$ 是學習率。導數描述局部斜率，所以更新只保證在足夠小的鄰域內傾向降低損失；非凸目標、尺度**差異**（Delta） <!-- term:Delta -->與隨機批次都會改變路徑。

> [!IMPORTANT]
> **差異** <!-- term:Delta --> (Delta): 特定變更的契約，用於驅動實作並作為驗證實作的基準對象。 <!-- anchor:Delta -->


若兩層網路為 $\hat y=W_2\sigma(W_1x)$，鏈式法則把輸出誤差拆回各層：

$$
\frac{\partial L}{\partial W_1}
=
\frac{\partial L}{\partial \hat y}
\frac{\partial \hat y}{\partial \sigma}
\frac{\partial \sigma}{\partial (W_1x)}
\frac{\partial (W_1x)}{\partial W_1}.
$$

反向傳播 <!-- term:Backpropagation -->不是另一種最佳化器。它只是重用中間結果，避免對每個參數重算完整導數；最佳化器再使用這些梯度更新參數。

下列實驗以一個參數擬合 $y=3x$，直接展示梯度如何改變權重：

```python
import numpy as np

x = np.array([-2.0, -1.0, 1.0, 2.0])
y = 3.0 * x
w = 0.0
learning_rate = 0.1

for step in range(8):
    prediction = w * x
    loss = np.mean((prediction - y) ** 2)
    gradient = 2 * np.mean((prediction - y) * x)
    print(step, round(w, 4), round(loss, 4), round(gradient, 4))
    w -= learning_rate * gradient
```

權重不是理解出斜率 3，而是損失曲面的局部導數反覆把它推向較低誤差的位置。若學習率過大，同一條更新規則也可能越過谷底並發散。

## 反思

梯度提供的是局部資訊，不是全域導航。訓練成功通常還依賴初始化、資料尺度、正規化、殘差連接與最佳化器設計。把成功全部歸功於模型架構，會忽略這些共同條件。

另一方面，參數改變不等於能力單調增加。一次更新會同時影響多個輸入區域；降低目前批次的損失，可能提高其他樣本的損失。這種共享參數造成的干涉，是後續理解持續學習與能力漂移的重要基礎。

## 實務對比

錯誤做法是看到訓練損失下降，就推論模型正在逼近唯一正確的內部表示。不同初始化可能得到不同參數，卻在觀察資料上產生近似輸出。

較正確的檢查會同時觀察訓練與驗證曲線，並改變隨機種子重複實驗。若結論依賴特定參數方向，還需檢查重新參數化後是否仍成立。

因此，梯度能解釋某次更新如何發生，卻未必能單獨解釋模型為何形成某個高階概念。從局部導數到功能性表示，中間仍隔著資料分佈與整段訓練軌跡。

## 結論

反向傳播 <!-- term:Backpropagation -->把輸出誤差分配到參數，梯度下降 <!-- term:GradientDescent -->再把這些訊號轉成更新。模型的學習不是一次領悟，而是一連串受局部幾何、樣本與數值設定制約的狀態改變。

理解這個製程後，便能區分「架構理論上可表示」與「最佳化實際可學得」。兩者共同決定模型能力，任何一方都不能單獨代表學習本身。

梯度下降 <!-- term:GradientDescent -->與深度網路訓練的完整背景可參考 [Deep Learning：Numerical Computation](https://www.deeplearningbook.org/contents/numerical.html)。