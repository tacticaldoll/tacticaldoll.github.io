+++
title = "模型為何學錯：資料雜訊、偽相關與捷徑學習"
date = "2026-09-06T02:58:03+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "測試分數高不代表理由正確。只要表面特徵在訓練資料上穩定預測標籤，經驗風險最小化就有理由採用它，形成只在同分佈環境有效的捷徑。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "大型語言模型", # term:Llm
    "機器學習", # term:MachineLearning
    "資料雜訊", # term:DataNoise
    "泛化", # term:Generalization
    "實務對比", # term:PracticalContrastiveExamples
    "反思", # term:Reflection
    "導言", # term:Introduction
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

模型在測試集表現良好，仍可能依賴錯誤理由。只要某個表面特徵在訓練資料上穩定預測標籤，經驗風險最小化就有理由使用它。

這種現象不一定是模型先學對再退化。模型可能從一開始便學到偽相關（spurious correlation），並形成只在同分佈測試環境中有效的捷徑學習（shortcut learning）。

## 分析

給定候選規則 $f$，訓練程序常近似選擇：

$$
\hat f=\arg\min_{f\in\mathcal H}
\frac{1}{n}\sum_{i=1}^n
\ell(f(x_i),y_i).
$$

若核心特徵與捷徑特徵都能降低訓練損失，這個目標沒有自動偏好人類認為較合理的因果規則。架構、資料頻率與最佳化容易度會決定哪條規律先被利用。

下面建立兩個環境。`core` 始終等於標籤，`shortcut` 在訓練環境高度相關，部署時則反轉。

```python
train = [
    {"core": 0, "shortcut": 0, "label": 0},
    {"core": 0, "shortcut": 0, "label": 0},
    {"core": 1, "shortcut": 1, "label": 1},
    {"core": 1, "shortcut": 1, "label": 1},
]

deployment = [
    {"core": 0, "shortcut": 1, "label": 0},
    {"core": 0, "shortcut": 1, "label": 0},
    {"core": 1, "shortcut": 0, "label": 1},
    {"core": 1, "shortcut": 0, "label": 1},
]

def score(feature, rows):
    return sum(row[feature] == row["label"] for row in rows) / len(rows)

for feature in ("core", "shortcut"):
    print(feature, score(feature, train), score(feature, deployment))
```

訓練分數無法區分兩條規則，跨環境測試才暴露捷徑。實務上通常不知道 `core` 的真實身份，因此需要刻意建立會破壞可疑相關性的資料切片或介入。

**資料雜訊**（Data Noise） <!-- term:DataNoise -->是另一種問題。隨機標籤錯誤會降低可達到的一致性；系統性標註偏差則可能建立新的偽相關。兩者都涉及資料品質，但前者偏向增加變異，後者可能穩定地把模型推向錯誤規則。

> [!IMPORTANT]
> **資料雜訊** <!-- term:DataNoise --> (Data Noise): 標註錯誤或量測誤差造成的標籤與特徵偏差。 <!-- anchor:DataNoise -->


捷徑也不等於完全無用。背景、來源或文字格式在目前分佈中可能真的具有預測力。問題是部署主張超出了該相關性可維持的環境，而不是模型違反了最佳化目標。

## 反思

「模型學錯」包含人類價值判斷。從訓練損失看，模型可能選到最便宜且最有效的訊號；從部署目標看，那條訊號卻缺乏穩定性。因此，錯誤往往存在於資料與任務契約之間。

資料量增加也不保證修復。如果新增資料持續保留同一偽相關，模型只會更有信心。真正需要的是環境多樣性，或能區分候選機制的反例。

## 實務對比

錯誤做法是隨機切分同一來源的資料，再把高測試分數當成跨環境能力。若訓練與測試共享拍攝背景、醫院設備或網站模板，捷徑會同時存在於兩邊。

較好的做法按來源、時間或環境切分，並建立「核心相同、捷徑改變」的對照集。這種切片不一定完整證明因果，但比隨機切分更能反駁脆弱規則。

另一個錯誤是把所有失敗稱為資料污染。惡意內容、錯誤標註、抽樣偏差與模型生成資料具有不同的資料生成程序；它們需要不同證據，不能只靠「資料不乾淨」統攝。

## 結論

模型學到的不是資料背後唯一正確的規律，而是訓練條件允許且目標函數獎勵的規律。高同分佈分數只能證明規則在該分佈有效。

要判斷能力是否可靠，應尋找能分離核心訊號與捷徑的環境。真正有說服力的證據不是更多同類樣本，而是模型在相關性被破壞後仍維持行為。

跨領域的捷徑學習整理可參考 Geirhos 等人的 [Shortcut Learning in Deep Neural Networks](https://arxiv.org/abs/2004.07780)。