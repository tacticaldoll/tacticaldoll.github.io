+++
title = "Transformer 如何建立直接關聯：注意力、位置與平行計算"
date = "2026-09-06T02:36:05+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "自我注意力讓任意位置直接聚合彼此的表示，縮短計算路徑也允許平行訓練。拆解縮放點積注意力、位置編碼與多頭投影各自承擔什麼。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "大型語言模型", # term:Llm
    "自我注意力", # term:SelfAttention
    "縮放點積注意力", # term:ScaledDotProductAttention
    "位置編碼", # term:PositionalEncoding
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

RNN 讓資訊依時間步逐次傳遞。Transformer 則使用**自我注意力**（Self-Attention） <!-- term:SelfAttention -->，讓一個位置直接聚合其他位置的表示。這縮短了位置間的計算路徑，也讓訓練可沿序列位置平行進行。

> [!IMPORTANT]
> **自我注意力** <!-- term:SelfAttention --> (Self-Attention): 讓序列中任一位置直接以內容相依的權重聚合其他位置表示的機制。 <!-- anchor:SelfAttention -->


直接關聯常被敘述成模型不再遺忘。注意力實際產生的是輸入**相依**（Depend） <!-- term:Depend -->的加權和；它不保證每個位置都被保存，也不等於可持續存取的外部記憶體。

> [!IMPORTANT]
> **相依** <!-- term:Depend --> (Depend): 元件之間產生的耦合關係，一方改動會強制影響另一方。 <!-- anchor:Depend -->


## 分析

**縮放點積注意力**（Scaled Dot-Product Attention） <!-- term:ScaledDotProductAttention -->寫成：

> [!IMPORTANT]
> **縮放點積注意力** <!-- term:ScaledDotProductAttention --> (Scaled Dot-Product Attention): 以查詢與鍵的點積除以維度平方根作為關聯分數的注意力計算方式。 <!-- anchor:ScaledDotProductAttention -->


$$
\operatorname{Attention}(Q,K,V)
=
\operatorname{softmax}\!\left(
\frac{QK^\top}{\sqrt{d_k}}
\right)V.
$$

查詢 $Q$ 與鍵 $K$ 的點積產生關聯分數，Softmax 將每列轉為權重，再對值 $V$ 加權。除以 $\sqrt{d_k}$ 是為了控制高維點積的尺度，避免 Softmax 過早飽和。

下列程式展示同一組值如何因查詢改變而被重新混合：

```python
import numpy as np

def softmax(x):
    e = np.exp(x - np.max(x, axis=-1, keepdims=True))
    return e / e.sum(axis=-1, keepdims=True)

Q = np.array([[1., 0.], [0., 1.]])
K = np.array([[1., 0.], [0., 1.], [1., 1.]])
V = np.array([[10., 0.], [0., 10.], [5., 5.]])

weights = softmax(Q @ K.T / np.sqrt(K.shape[1]))
print(np.round(weights, 3))
print(np.round(weights @ V, 3))
```

輸出是值向量的加權**組合**（Compose） <!-- term:Compose -->，不是把全部輸入無損複製到每個位置。多頭注意力讓模型在不同**投影**（Projection） <!-- term:Projection -->空間形成多組關聯，但各頭仍受維度與訓練目標限制。

> [!IMPORTANT]
> **組合** <!-- term:Compose --> (Compose): 將多個獨立元件串聯運作的方式，強調資料流轉而非直接相依。 <!-- anchor:Compose -->
> **投影** <!-- term:Projection --> (Projection): 產物透過穩定鍵間接引用共享庫時，它不再是凍結快照，而是共享庫當前狀態一個可隨時重算的呈現。 <!-- anchor:Projection -->


因為注意力本身沒有序列順序，Transformer 還需要**位置編碼**（Positional Encoding） <!-- term:PositionalEncoding -->。原始架構加入正弦與餘弦位置向量，使相同 token 位於不同位置時得到不同表示。

> [!IMPORTANT]
> **位置編碼** <!-- term:PositionalEncoding --> (Positional Encoding): 為本身不含順序資訊的注意力模型補入序列位置的表示方法。 <!-- anchor:PositionalEncoding -->


標準全注意力需要形成長度 $N$ 的 $N\times N$ 分數矩陣。它縮短關聯路徑，卻以記憶體與計算成本交換；實際成本還包含前饋層、批次大小與硬體利用率，不能只由 $O(N^2)$ 判斷速度。

## 反思

Transformer 的關鍵優勢是關聯路徑與平行性，不是無限記憶。有限上下文會排除窗口外資訊，窗口內資訊也會因查詢、遮罩與層間轉換受到選擇。

注意力權重也不能直接等同因果解釋。某個位置權重較高，只表示當次前向計算中的混合比例較大；殘差連接、前饋層與後續層仍會改變最終輸出。

## 實務對比

錯誤說法是「任意兩個 token 距離為一，所以模型不會忘記」。常數層數的關聯路徑只描述計算圖，不保證訓練能學到正確關係，也不保證資訊通過多層後仍可辨識。

另一個錯誤是把資料污染直接推導成注意力均勻化。資料能改變所學參數，但 Softmax 是否平坦取決於查詢與鍵的分數；沒有實驗就不能把兩者寫成必然因果。

較完整的分析會同時測量任務表現、注意力分佈、表示秩與上下文位置效應。任何單一內部指標都不足以代表「理解」或「記憶」。

## 結論

Transformer 以內容相依 <!-- term:Depend -->的權重直接混合序列位置，減少遞迴造成的計算限制。位置編碼 <!-- term:PositionalEncoding -->補入順序，多頭投影 <!-- term:Projection -->擴充關聯視角，殘差與前饋層共同形成完整模型。

注意力提供的是可學習的資訊路由，不是人類式記憶。它讓某些關係更容易表示，也引入新的成本與邊界；這兩面都來自同一個架構選擇。

架構定義與原始實驗見 [Attention Is All You Need](https://arxiv.org/abs/1706.03762)。