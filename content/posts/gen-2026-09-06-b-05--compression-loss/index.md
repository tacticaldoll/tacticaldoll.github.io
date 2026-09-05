+++
title = "壓縮保留了分數，是否保留了能力：剪枝、量化與蒸餾"
date = "2026-09-06T02:58:05+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "平均準確率不變，不代表決策邊界、罕見類別與校準程度都沒變。比較剪枝、量化與知識蒸餾三種近似機制各自改變了什麼。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "大型語言模型", # term:Llm
    "剪枝", # term:Pruning
    "量化", # term:Quantization
    "知識蒸餾", # term:KnowledgeDistillation
    "實務對比", # term:PracticalContrastiveExamples
    "差異", # term:Delta
    "反思", # term:Reflection
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

模型從訓練環境移到手機或邊緣裝置時，常需要減少記憶體與計算。**剪枝**（Pruning） <!-- term:Pruning -->、**量化**（Quantization） <!-- term:Quantization -->與**知識蒸餾**（Knowledge Distillation） <!-- term:KnowledgeDistillation -->都可稱為壓縮，卻以不同方式建立近似模型。

> [!IMPORTANT]
> **剪枝** <!-- term:Pruning --> (Pruning): 移除模型中影響較小的連接或結構，以縮減規模的壓縮方法。 <!-- anchor:Pruning -->
> **量化** <!-- term:Quantization --> (Quantization): 以較少位元表示權重或啟動值，改變數值格點以降低記憶體與計算成本的近似方法。 <!-- anchor:Quantization -->
> **知識蒸餾** <!-- term:KnowledgeDistillation --> (Knowledge Distillation): 以較大模型的輸出分佈為目標，訓練較小模型重新估計其行為的壓縮方法。 <!-- anchor:KnowledgeDistillation -->


若壓縮後平均準確率不變，人們容易宣稱能力完整保留。然而，平均值可能看不見決策邊界附近、罕見類別或校準程度的改變。

## 分析

量化 <!-- term:Quantization -->把連續權重映射到離散格點。最簡單的均勻量化 <!-- term:Quantization -->可寫成：

$$
Q_\**差異**（Delta） <!-- term:Delta -->=\差異 <!-- term:Delta -->\operatorname{round}(w/\差異 <!-- term:Delta -->).
$$

> [!IMPORTANT]
> **差異** <!-- term:Delta --> (Delta): 特定變更的契約，用於驅動實作並作為驗證實作的基準對象。 <!-- anchor:Delta -->


若沒有截斷且採最近格點，單一權重誤差滿足 $|Q_\差異 <!-- term:Delta -->-w|\leq\差異 <!-- term:Delta -->/2$。輸出誤差仍會受輸入尺度、層數與非線性影響，不能把單一權重界直接當成整體模型界。

下列實驗比較原始線性分類器與粗量化 <!-- term:Quantization -->版本。大多數樣本維持不變，靠近邊界的樣本卻可能翻轉。

```python
def quantize(value, step):
    return step * round(value / step)

weight, bias = 0.26, -0.13
q_weight = quantize(weight, 0.2)
q_bias = quantize(bias, 0.2)
samples = [0.1, 0.49, 0.51, 0.8, 2.0]

for x in samples:
    original = int(weight * x + bias >= 0)
    compressed = int(q_weight * x + q_bias >= 0)
    print(x, original, compressed,
          round(weight * x + bias, 3),
          round(q_weight * x + q_bias, 3))
```

這個翻轉不是權重自然退化，而是部署表示改變。若測試集很少包含低邊際樣本，整體準確率可能完全不動。

剪枝 <!-- term:Pruning -->將部分連接設為零，常以權重大小或重要性近似選擇。重新訓練可以讓剩餘參數補償，但被剪除方向是否影響罕見行為，仍取決於評測覆蓋。

知識蒸餾 <!-- term:KnowledgeDistillation -->則重新訓練較小的學生模型，使其匹配教師輸出。常見軟目標為：

$$
p_i^{(T)}=
\frac{\exp(z_i/T)}{\sum_j\exp(z_j/T)}.
$$

溫度 $T$ 展開類別間的相對分數。學生學到的是教師行為的受限近似，不是把每個參數直接壓小；其失真來源與量化 <!-- term:Quantization -->不同。

## 反思

壓縮本身不是退化的同義詞。經過量化 <!-- term:Quantization -->感知訓練或重新訓練，壓縮模型可能在指定基準上維持甚至改善表現。應被檢查的是能力分佈是否改變，而不是檔案大小是否變小。

同樣地，浮點模型也不是唯一真實模型。不同硬體核心、算子融合與數值精度都可能帶來差異 <!-- term:Delta -->；部署契約應包含可接受的輸出容差，而非假定逐位一致。

## 實務對比

錯誤做法是只在平衡測試集上比較 top-1 accuracy。壓縮可能集中傷害罕見類別、低對比影像或接近安全閾值的案例，平均值仍幾乎不動。

較好的做法會比較輸出差、決策翻轉率、校準與行為切片。還應在真正部署硬體上測量延遲和記憶體，因為理論位元數下降不保證系統端收益。

另一個錯誤是把**蒸餾**（Distill） <!-- term:Distill -->當成無損複製。學生容量、蒸餾 <!-- term:Distill -->資料與溫度共同限制可轉移行為；教師在資料外的反應通常沒有被完整指定。

> [!IMPORTANT]
> **蒸餾** <!-- term:Distill --> (Distill): 從長對話或大量開發脈絡中萃取關鍵資訊的處理過程。 <!-- anchor:Distill -->


## 結論

模型壓縮是一組受資源約束的近似程序。量化 <!-- term:Quantization -->改變數值格點，剪枝 <!-- term:Pruning -->移除連接，蒸餾 <!-- term:Distill -->重新估計較小模型；三者不能只因目的相似就視為同一機制。

壓縮是否削弱能力，必須以固定資料與推論契約比較行為。平均分數是起點，不是無損證明；越靠近決策邊界或越少見的案例，越需要獨立切片。

剪枝 <!-- term:Pruning -->與訓練後量化 <!-- term:Quantization -->的早期整合見 [Deep Compression](https://arxiv.org/abs/1510.00149)；整數推論見 [量化 <!-- term:Quantization --> and Training of Neural Networks for Efficient Integer-Arithmetic-Only Inference](https://arxiv.org/abs/1712.05877)；蒸餾 <!-- term:Distill -->目標見 [Distilling the **描述性知識**（Knowledge） <!-- term:Knowledge --> in a Neural Network](https://arxiv.org/abs/1503.02531)。

> [!IMPORTANT]
> **描述性知識** <!-- term:Knowledge --> (Knowledge): 逆向工程產出的描述性知識，在專案中被視為債務指標 <!-- anchor:Knowledge -->