+++
title = "不可見能力如何被展示：Demo、Benchmark 與行銷敘事"
date = "2026-09-06T03:14:03+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "汽車可以試駕，模型涵蓋多少情境卻難以直接檢查。Demo 與 Benchmark 把不可見能力轉成市場可讀訊號，而展示總是一種選擇。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "大型語言模型", # term:Llm
    "實務對比", # term:PracticalContrastiveExamples
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

消費者可以試駕汽車，卻難以直接檢查一個模型涵蓋多少情境。Demo 提供具體體驗，Benchmark 提供可比較數字；兩者都把不可見能力轉成市場可讀訊號。

問題不在展示必然造假，而在展示總是選擇。題目、提示、隨機種子、指標與競爭者共同決定觀眾看見哪一面。

## 分析

評測分數可寫成有限樣本平均：

$$
\hat S(f;D,m)=\frac{1}{n}\sum_{i=1}^{n}
m(f(x_i),y_i).
$$

這個數字只對資料集 $D$ 與指標 $m$ 有直接意義。把它外推到「通用智慧」需要額外假設，例如樣本代表實際使用、評分方法捕捉真正效用，而且評測沒有被反覆調參耗盡。

多次嘗試後只公開最高分，會產生選擇偏差。下面假設所有候選系統真實能力相同，只因有限評測而有隨機波動；挑選次數越多，最佳觀察值通常越樂觀。

```python
import random

rng = random.Random(21)
true_score = 0.70
sample_size = 100

def measured_score():
    correct = sum(rng.random() < true_score for _ in range(sample_size))
    return correct / sample_size

for trials in (1, 5, 20, 100):
    best = max(measured_score() for _ in range(trials))
    print(trials, round(best, 3))
```

這不是說任何高分都虛假，而是公開規則必須包含試驗次數、選擇程序與未見測試集。若 Benchmark 成為開發目標，團隊會合理地朝它最佳化，分數與未測能力便可能逐漸**脫鉤**（Desynchronization） <!-- term:Desynchronization -->。

> [!IMPORTANT]
> **脫鉤** <!-- term:Desynchronization --> (Desynchronization): 中介索引檔與真實檔案系統狀態不再一致的現象，是雙重狀態同步最典型的故障表現。 <!-- anchor:Desynchronization -->


Demo 的選擇性更直觀。預錄展示可以凸顯產品上限；現場隨機任務較接近日常變異。兩者服務不同問題，誤導發生在上限展示被包裝成典型可靠度時。

多維評估可以減少單一分數的壓縮。準確率、校準、穩健性、公平性與效率可能互相取捨；完整呈現不會消除選擇，但能讓被忽略的維度可見。

## 反思

市場需要簡化，否則買方無法比較產品。Benchmark 因此不只是技術工具，也是市場基礎設施；它建立共同語言，同時決定哪些能力值得投資。

行銷也未必與科學相反。好的展示能提出可重現主張，讓競爭者與使用者檢驗。真正的邊界是可追溯性：觀眾能否知道展示條件，以及結論是否超出那些條件。

## 實務對比

錯誤做法是宣稱模型在某項考試超越人類，因此能承擔該職業。考試只抽樣部分任務；職業還包含責任、工具操作、資訊蒐集與例外處理。

較好的做法把主張限定為「在指定提示與評分規則下，模型於此資料集得到某分數」，再另行測試實際流程。這種句子較長，卻保留可反駁性。

另一個錯誤是因一次失敗 Demo 就認定模型完全無用。單次失敗能反駁「永不失敗」，不能估計整體錯誤率；負面展示也需要代表性。

## 結論

Demo 與 Benchmark 都是能力的測量介面，不是能力本身。它們讓產品可見、可比較，也把選擇與外推風險帶入市場敘事。

最可靠的展示會公開條件、保留多維指標，並把上限、平均與失敗案例分開。市場敘事不必消失，但應讓讀者看見它從有限證據跨出了多遠。

多情境、多指標與透明輸出的評測設計見 [Holistic Evaluation of Language Models](https://arxiv.org/abs/2211.09110)；反覆使用測試資料的統計風險可參考 [The Reusable Holdout](https://www.science.org/doi/10.1126/science.aaa9375)。