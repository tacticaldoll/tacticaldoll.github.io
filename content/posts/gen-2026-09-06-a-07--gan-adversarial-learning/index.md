+++
title = "GAN 如何透過對抗學習生成：生成器、判別器與動態平衡"
date = "2026-09-06T02:36:07+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "對抗生成不指定重建目標，而以判別器提供可學習的比較訊號。說明非定態目標如何同時帶來生成能力與訓練不穩定。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "AI 代理人", # term:AiAgent
    "生成對抗網路", # term:GenerativeAdversarialNetwork
    "模式坍縮", # term:ModeCollapse
    "實務對比", # term:PracticalContrastiveExamples
    "形狀", # term:DataShape
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

**生成對抗網路**（Generative Adversarial Network） <!-- term:GenerativeAdversarialNetwork -->不直接為每筆資料指定重建目標。它讓生成器產生樣本，再讓判別器分辨真實資料與生成資料，透過雙方競爭逼近資料分佈。

> [!IMPORTANT]
> **生成對抗網路** <!-- term:GenerativeAdversarialNetwork --> (Generative Adversarial Network): 由生成器與判別器相互競爭、以隱式方式逼近資料分佈的架構。 <!-- anchor:GenerativeAdversarialNetwork -->


這種方法能在沒有顯式似然函數的情況下訓練生成器。代價是訓練目標不再是單一固定曲面，而會隨另一個網路的更新持續改變。

## 分析

原始 GAN 的極小極大目標為：

$$
\min_G\max_D V(D,G)
=
\mathbb E_{x\sim p_{\mathrm{data}}}[\log D(x)]
+
\mathbb E_{z\sim p(z)}[\log(1-D(G(z)))].
$$

判別器 $D$ 希望提高真實樣本分數並降低生成樣本分數。生成器 $G$ 則改變生成分佈，使判別器更難區分。理想平衡下，生成分佈與資料分佈一致，判別器輸出二分之一。

實際訓練交替更新兩組參數。當判別器太強時，生成器可能收到缺乏辨識度的梯度；當生成器只找到少數能欺騙判別器的輸出時，它可能忽略其他資料模式。

下列玩具程式展示「只覆蓋一個模式」為何不能由平均值檢查發現：

```python
import numpy as np

rng = np.random.default_rng(4)
real = np.concatenate([
    rng.normal(-3, 0.3, 500),
    rng.normal(3, 0.3, 500),
])
collapsed = rng.normal(3, 0.3, 1000)

print("mean:", round(real.mean(), 3), round(collapsed.mean(), 3))
print("left-mode coverage:",
      round(np.mean(real < 0), 3),
      round(np.mean(collapsed < 0), 3))
```

這裡生成資料只保留右側模式。它展示**模式坍縮**（Mode Collapse） <!-- term:ModeCollapse -->的輸出**形狀**（Data Shape） <!-- term:DataShape -->，但沒有模擬 GAN 的梯度，因此不能用來證明任何特定訓練原因。

> [!IMPORTANT]
> **模式坍縮** <!-- term:ModeCollapse --> (Mode Collapse): 生成器只覆蓋資料分佈中少數模式，導致樣本多樣性不足的失效現象。 <!-- anchor:ModeCollapse -->
> **形狀** <!-- term:DataShape --> (Data Shape): 資料結構或物件所包含的屬性與型別定義，通常由型別系統來描述 <!-- anchor:DataShape -->


## 反思

GAN 的生成器通常定義一個從簡單潛在分佈到資料空間的映射。若多個 $z$ 被送到相近輸出，生成器仍可能在判別器目前可見的弱點上得分，卻失去分佈覆蓋。

「對抗」也不表示雙方具有意圖。它只是兩個**相依**（Depend） <!-- term:Depend -->目標的最佳化結構。訓練不穩、模式坍縮 <!-- term:ModeCollapse -->與震盪是可觀察現象，但成因會隨損失、架構與更新比例改變。

> [!IMPORTANT]
> **相依** <!-- term:Depend --> (Depend): 元件之間產生的耦合關係，一方改動會強制影響另一方。 <!-- anchor:Depend -->


## 實務對比

錯誤做法是挑選少量視覺效果最好的樣本，據此判定生成器已學會資料分佈。這只能顯示精度，不能顯示生成結果是否涵蓋所有模式。

較完整的評估會分開觀察品質與覆蓋率。對玩具分佈可以直接計算各模式比例；對高維資料則需要多種指標與人為檢查，且任何代理指標都有盲點。

另一個錯誤是把 GAN 的模式坍縮 <!-- term:ModeCollapse -->與其他模型中的 posterior collapse 或 model collapse 視為同一件事。它們共享「坍縮」名稱，卻涉及不同變數與訓練程序。

## 結論

GAN 透過判別器提供可學習的比較訊號，使生成器在沒有顯式資料似然的情況下逼近資料分佈。能力來自雙方相互調整，訓練困難也來自這個非定態目標。

理解 GAN 不能停在「兩個網路互相競爭」。真正需要追蹤的是生成分佈覆蓋了哪些資料模式，以及判別器梯度如何改變生成器的映射。

模式坍縮 <!-- term:ModeCollapse -->與展開最佳化的實驗可參考 [Unrolled Generative Adversarial Networks](https://arxiv.org/abs/1611.02163)。