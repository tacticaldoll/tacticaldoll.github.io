+++
title = "CNN 如何利用局部結構：卷積、共享權重與感受野"
date = "2026-09-06T02:36:03+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "卷積網路不是從零學會平移不變，而是先用局部連接與權重共享限制可選函數。說明結構偏置如何讓模型以較少資料學得影像規律。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "大型語言模型", # term:Llm
    "卷積神經網路", # term:ConvolutionalNeuralNetwork
    "平移等變性", # term:TranslationEquivariance
    "實務對比", # term:PracticalContrastiveExamples
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

全連接網路把每個輸入位置視為不同變數。影像卻具有局部性：相鄰像素通常比遠距像素更相關，同一種邊緣也可能出現在不同位置。

**卷積神經網路**（Convolutional Neural Network） <!-- term:ConvolutionalNeuralNetwork -->把這項假設寫入架構。它並不是從零學會「位置可平移」，而是先以局部連接與權重共享限制可選函數，再從資料學習濾波器內容。

> [!IMPORTANT]
> **卷積神經網路** <!-- term:ConvolutionalNeuralNetwork --> (Convolutional Neural Network): 以局部連接與權重共享處理格狀資料的網路架構，把空間鄰近性寫進模型結構。 <!-- anchor:ConvolutionalNeuralNetwork -->


## 分析

一維離散卷積可簡化寫成：

$$
y_i=\sum_{k=0}^{K-1}w_kx_{i+k}+b.
$$

同一組 $w_k$ 會滑過所有位置，因此參數量不隨輸入長度線性增加。若輸入中的模式平移，輸出特徵也相應平移，形成**平移等變性**（Translation Equivariance） <!-- term:TranslationEquivariance -->。

> [!IMPORTANT]
> **平移等變性** <!-- term:TranslationEquivariance --> (Translation Equivariance): 輸入平移時輸出隨之平移的性質，由卷積的權重共享自然產生。 <!-- anchor:TranslationEquivariance -->


堆疊卷積層會擴大感受野（receptive field）。對 stride 為 1、無 dilation 的 $L$ 層、核心寬度 $K$，理論感受野為：

$$
R_L=1+L(K-1).
$$

理論感受野只表示可能接收哪些位置，不代表每個位置影響相等。深層網路的有效感受野通常更集中，池化也會以降低空間解析度換取較大的不變性。

下列程式以一個邊緣濾波器展示共享權重：

```python
import numpy as np

x = np.array([0., 0., 1., 1., 1., 0., 0.])
kernel = np.array([-1., 1.])

def valid_convolution(signal, weight):
    return np.array([
        np.dot(signal[i:i + len(weight)], weight)
        for i in range(len(signal) - len(weight) + 1)
    ])

print(valid_convolution(x, kernel))
print(valid_convolution(np.roll(x, 1), kernel))
```

模式平移後，反應位置也跟著移動。模型沒有為每個位置分別學一個邊緣偵測器，這正是共享權重帶來的統計效率。

## 反思

卷積的優勢依賴局部結構確實存在。若任務的重要關係跨越整個輸入，固定小核心就需要許多層才能傳遞訊息。局部偏置既能節省樣本，也可能排除不符合假設的函數。

平移等變性 <!-- term:TranslationEquivariance -->也不等於旋轉、縮放或視角不變性。資料增強可以補入部分變換，但那是訓練分佈的設計，不是標準卷積自動具有的能力。

## 實務對比

錯誤說法是「CNN 會自己發現所有影像結構」。事實上，它先假定局部模式可重複使用，再透過資料決定哪些模式值得保留。

另一個錯誤是把池化視為免費的不變性。池化降低位置敏感度時，也可能破壞精確定位。姿態估計研究便需要額外的位置精修，以補償下採樣造成的定位損失。

因此，評估 CNN 時不能只問準確率，也要問任務需要局部辨識還是精確定位。相同結構在兩種目標下可能分別是優勢與限制。

## 結論

CNN 的學習能力來自資料與結構偏置的合作。共享權重降低參數需求，局部連接把空間鄰近性寫入模型，層疊則逐步擴大可整合範圍。

這個例子揭示了更一般的原理：算法不只是學習程序，也是一組先驗限制。模型能以較少資料學得某類規律，通常因為架構已排除了大量其他可能性。

感受野的形式與有效範圍可參考 [Understanding the Effective Receptive Field in Deep Convolutional Neural Networks](https://arxiv.org/abs/1701.04128)。