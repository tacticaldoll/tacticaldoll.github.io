+++
title = "能力為何沒有形成：梯度障礙、坍縮與最佳化失敗"
date = "2026-09-06T02:58:02+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "架構能表示某個函數，不代表訓練找得到它。區分梯度障礙與 RNN、GAN、VAE 三種坍縮各自失去的對象，說明取得失敗不是能力老化。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "大型語言模型", # term:Llm
    "模式坍縮", # term:ModeCollapse
    "後驗坍縮", # term:PosteriorCollapse
    "遞迴式神經網路", # term:RecurrentNeuralNetwork
    "變分自動編碼器", # term:VariationalAutoencoder
    "生成對抗網路", # term:GenerativeAdversarialNetwork
    "實務對比", # term:PracticalContrastiveExamples
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

模型理論上能表示某種函數，不代表訓練一定能找到它。當損失停滯或輸出失去多樣性時，人們常說模型退化；但若能力從未形成，更準確的分類是取得失敗（acquisition failure）。

「坍縮」尤其容易製造錯誤統一。RNN 的梯度消失、GAN 的**模式坍縮**（Mode Collapse） <!-- term:ModeCollapse -->與 VAE 的**後驗坍縮**（Posterior Collapse） <!-- term:PosteriorCollapse -->都可能降低能力，三者失去的對象卻不同。

> [!IMPORTANT]
> **模式坍縮** <!-- term:ModeCollapse --> (Mode Collapse): 生成器只覆蓋資料分佈中少數模式，導致樣本多樣性不足的失效現象。 <!-- anchor:ModeCollapse -->
> **後驗坍縮** <!-- term:PosteriorCollapse --> (Posterior Collapse): 近似後驗退化為先驗、潛在變數不再攜帶輸入資訊的失效現象。 <!-- anchor:PosteriorCollapse -->


## 分析

**遞迴式神經網路**（Recurrent Neural Network） <!-- term:RecurrentNeuralNetwork -->的早期訊號需要穿過 Jacobian 連乘：

> [!IMPORTANT]
> **遞迴式神經網路** <!-- term:RecurrentNeuralNetwork --> (Recurrent Neural Network): 重複套用同一狀態轉換，把可變長度序列映射為固定維度隱藏狀態的網路。 <!-- anchor:RecurrentNeuralNetwork -->


$$
\frac{\partial h_T}{\partial h_k}
=
\prod_{t=k+1}^{T}
\frac{\partial h_t}{\partial h_{t-1}}.
$$

若多數方向的有效尺度小於 1，早期時間步收到的梯度會指數衰減。這妨礙**信用分配**（Credit Assignment） <!-- term:CreditAssignment -->：模型可能具備表示長程依賴的參數空間，最佳化卻難以取得那組參數。

> [!IMPORTANT]
> **信用分配** <!-- term:CreditAssignment --> (Credit Assignment): 判定某個結果應歸因於哪些參數或決策步驟的問題。 <!-- anchor:CreditAssignment -->


下列標準 Python 實驗隔離連乘效果：

```python
for scale in (0.8, 0.95, 1.0, 1.05, 1.2):
    influence = scale ** 50
    print(scale, f"{influence:.6g}")
```

這個標量例子只證明重複相乘可以消失或爆炸。真實網路包含矩陣方向、非線性函數與門控路徑，因此不能用單一底數預測所有 RNN。

**生成對抗網路**（Generative Adversarial Network） <!-- term:GenerativeAdversarialNetwork -->的模式坍縮 <!-- term:ModeCollapse -->失去的是分佈覆蓋。不同潛在輸入被映射到少數輸出模式；問題位於生成器與判別器的動態目標，不是時間梯度必然縮小。

> [!IMPORTANT]
> **生成對抗網路** <!-- term:GenerativeAdversarialNetwork --> (Generative Adversarial Network): 由生成器與判別器相互競爭、以隱式方式逼近資料分佈的架構。 <!-- anchor:GenerativeAdversarialNetwork -->


**變分自動編碼器**（Variational Autoencoder） <!-- term:VariationalAutoencoder -->的後驗坍縮 <!-- term:PosteriorCollapse -->則失去潛在變數資訊。當近似後驗接近先驗，

> [!IMPORTANT]
> **變分自動編碼器** <!-- term:VariationalAutoencoder --> (Variational Autoencoder): 學習潛在變數的條件分佈，並以證據下界同時訓練編碼器與解碼器的生成模型。 <!-- anchor:VariationalAutoencoder -->


$$
D_{\mathrm{KL}}(q_\phi(z\mid x)\|p(z))\approx 0,
$$

解碼器可能忽略 $z$。這個結果可能與解碼器能力、目標權重及推論網路落後有關，不能只由「KL 太強」一語定案。

三個現象可以共享上位分類「訓練未取得預期能力」，卻不共享低階病因。上位分類幫助整理症狀，修復時仍必須回到各自的狀態變數與目標函數。

## 反思

最佳化失敗與能力退化的時間方向不同。前者描述從初始化出發沒有到達預期目標，後者通常暗示已通過基準的模型後來變差。若沒有保存訓練中間點，兩者在最終輸出上可能看起來一樣。

名稱也可能隱藏觀察尺度。GAN 產生幾張漂亮圖片，仍可能缺少整體覆蓋；VAE 重建良好，仍可能沒有使用潛在變數。單一品質樣本無法證明整個機制正常。

## 實務對比

錯誤做法是建立通用「collapse 修復包」，同時對 RNN、GAN 與 VAE 調低學習率。梯度爆炸可能受益於裁剪，但 GAN 的模式覆蓋與 VAE 的潛在資訊需要不同觀察量。

較好的診斷會針對失去的對象設計量測：RNN 看跨時間梯度範數，GAN 看分佈覆蓋，VAE 看潛在變數與輸入的資訊及 KL 使用量。共同的名稱只負責導航，不負責下藥。

另一個錯誤是只看最終損失。對抗訓練的兩方損失未必直接對應樣本品質；VAE 的總下界也可能掩蓋重建項與 KL 項之間的重分配。

## 結論

能力未形成首先是訓練路徑問題，而不是已取得能力的自然老化。架構定義可表示範圍，最佳化動態決定實際抵達的位置。

不同算法可以共享失效分類，但機制必須逐一證成。診斷時應問「哪個資訊通道、分佈範圍或潛在變數失去作用」，而不是把所有坍縮壓成一條定律。

RNN 梯度分析見 [On the Difficulty of Training Recurrent Neural Networks](https://arxiv.org/abs/1211.5063)；GAN 模式覆蓋見 [Unrolled Generative Adversarial Networks](https://arxiv.org/abs/1611.02163)；VAE 訓練動態見 [Lagging Inference Networks and 後驗坍縮 <!-- term:PosteriorCollapse --> in Variational Autoencoders](https://arxiv.org/abs/1901.05534)。