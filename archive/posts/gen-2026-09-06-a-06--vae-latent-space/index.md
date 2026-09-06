+++
title = "VAE 如何學習潛在空間：機率編碼與變分推論"
date = "2026-09-06T02:36:06+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "變分自動編碼器學的是給定輸入時潛在變數的分佈。以證據下界說明重建與正則化之間的結構性張力，以及重參數技巧真正解決的問題。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "大型語言模型", # term:Llm
    "變分自動編碼器", # term:VariationalAutoencoder
    "證據下界", # term:EvidenceLowerBound
    "重參數技巧", # term:ReparameterizationTrick
    "後驗坍縮", # term:PosteriorCollapse
    "實務對比", # term:PracticalContrastiveExamples
    "差異", # term:Delta
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

<!--more-->

## 導言

自動編碼器可以把輸入壓縮成較小表示，再嘗試重建原資料。**變分自動編碼器**（Variational Autoencoder） <!-- term:VariationalAutoencoder -->不只產生一個編碼向量，而是學習給定輸入時潛在變數的機率分佈。

> [!IMPORTANT]
> **變分自動編碼器** <!-- term:VariationalAutoencoder --> (Variational Autoencoder): 學習潛在變數的條件分佈，並以證據下界同時訓練編碼器與解碼器的生成模型。 <!-- anchor:VariationalAutoencoder -->


這使模型能從潛在空間取樣並生成資料，但也帶來兩個同時存在的要求：潛在變數要保留輸入資訊，所有輸入的編碼又必須接近可取樣的共同先驗。

## 分析

VAE 假設生成過程為 $p_\theta(x\mid z)p(z)$。真實後驗 $p_\theta(z\mid x)$ 通常難以直接計算，因此使用編碼器 $q_\phi(z\mid x)$ 近似，並最大化**證據下界**（Evidence Lower Bound） <!-- term:EvidenceLowerBound -->：

> [!IMPORTANT]
> **證據下界** <!-- term:EvidenceLowerBound --> (Evidence Lower Bound): 對數邊際似然的可最佳化下界，由重建項與 KL 正則項組成。 <!-- anchor:EvidenceLowerBound -->


$$
\log p_\theta(x)
\ge
\mathbb E_{q_\phi(z\mid x)}
[\log p_\theta(x\mid z)]
-D_{\mathrm{KL}}\!\left(q_\phi(z\mid x)\|p(z)\right).
$$

第一項鼓勵重建，第二項限制編碼分佈不要離先驗太遠。兩者不是「正確與錯誤」的對立，而是可重建性與可取樣性的取捨。

若編碼器輸出 $\mu(x)$ 與 $\sigma(x)$，直接抽樣會阻斷一般的梯度路徑。**重參數技巧**（Reparameterization Trick） <!-- term:ReparameterizationTrick -->改寫為：

> [!IMPORTANT]
> **重參數技巧** <!-- term:ReparameterizationTrick --> (Reparameterization Trick): 把隨機取樣改寫為與參數無關之噪聲的可微形式，使梯度得以穿過取樣步驟。 <!-- anchor:ReparameterizationTrick -->


$$
z=\mu(x)+\sigma(x)\odot\epsilon,
\qquad \epsilon\sim\mathcal N(0,I).
$$

隨機性被移到與參數無關的 $\epsilon$，使梯度可穿過 $\mu$ 與 $\sigma$。

下列程式計算一維高斯後驗相對標準常態先驗的 KL 項：

```python
import numpy as np

def kl_standard_normal(mu, log_variance):
    return -0.5 * (1 + log_variance - mu**2 - np.exp(log_variance))

cases = [
    (0.0, 0.0),
    (1.0, 0.0),
    (0.0, np.log(0.25)),
]

for mu, log_var in cases:
    print(mu, round(np.exp(log_var), 3),
          round(kl_standard_normal(mu, log_var), 4))
```

當 $\mu=0$ 且變異數為 1，近似後驗等於先驗，KL 為零。這是最低正則化成本，但若所有輸入都得到相同分佈，潛在變數便不再攜帶輸入**差異**（Delta） <!-- term:Delta -->。

> [!IMPORTANT]
> **差異** <!-- term:Delta --> (Delta): 特定變更的契約，用於驅動實作並作為驗證實作的基準對象。 <!-- anchor:Delta -->


## 反思

VAE 的「潛在空間有意義」不是由連續性自動保證。意義取決於資料、解碼器能力、目標權重與評估方式；不同潛在方向未必對應人類可命名概念。

**後驗坍縮**（Posterior Collapse） <!-- term:PosteriorCollapse -->也不應只怪罪 KL 項。研究指出，強解碼器、最佳化路徑、局部極小值與編碼表示缺乏差異 <!-- term:Delta -->都可能參與形成。名稱描述結果，不是完整病因。

> [!IMPORTANT]
> **後驗坍縮** <!-- term:PosteriorCollapse --> (Posterior Collapse): 近似後驗退化為先驗、潛在變數不再攜帶輸入資訊的失效現象。 <!-- anchor:PosteriorCollapse -->


## 實務對比

錯誤做法是只降低重建誤差，然後宣稱模型學到良好生成空間。普通自動編碼器可能把訓練樣本映射到彼此隔離的位置，使任意取樣落在沒有資料支持的區域。

另一個極端是過度強迫所有後驗貼近先驗。模型可能得到容易取樣的表面形式，解碼器卻忽略 $z$，生成結果主要依賴自身能力。

合理評估需要同時查看重建、取樣品質，以及潛在變數與輸入之間的資訊。單一 ELBO 數值未必能顯示哪一部分正在失效。

## 結論

VAE 把編碼改寫成近似機率推論，並以證據下界 <!-- term:EvidenceLowerBound -->共同訓練編碼器與解碼器。它的生成能力來自重建項與分佈正則化之間的結構性張力。

重參數技巧 <!-- term:ReparameterizationTrick -->解決的是隨機取樣下的梯度估計，不是語意保證。只有把目標函數、潛在資訊與生成結果一起觀察，才能說明模型實際學到什麼。

基本推導見 Kingma 與 Welling 的 [Auto-Encoding Variational Bayes](https://arxiv.org/abs/1312.6114)。