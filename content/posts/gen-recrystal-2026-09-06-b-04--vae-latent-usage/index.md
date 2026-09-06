+++
title = "低 KL 為何不是唯一診斷：VAE 的潛在通道失用"
date = "2026-09-06T22:50:04+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "低 KL 只是症狀，不是判決。用 ELBO 分解檢查解碼器是否已繞過潛在通道，並區分目標權衡、推論落後與模型容量三種候選機制。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "AI 代理人", # term:AiAgent
    "變分自動編碼器", # term:VariationalAutoencoder
    "後驗坍縮", # term:PosteriorCollapse
    "互資訊", # term:MutualInformation
    "證據下界", # term:EvidenceLowerBound
  ]
series = ["模型能力失效：從一句「模型變差了」到可被推翻的診斷"]
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

**變分自動編碼器**（Variational Autoencoder） <!-- term:VariationalAutoencoder -->可以有良好的重建或生成似然，潛在變數卻不攜帶輸入資訊。這種**後驗坍縮**（Posterior Collapse） <!-- term:PosteriorCollapse -->容易被簡化成「KL 懲罰太強」，但低 KL 只是症狀。這就衍生出一個問題：如何證明解碼器已繞過潛在通道，並區分目標權衡、推論落後與模型容量等候選機制？

> [!IMPORTANT]
> **變分自動編碼器** <!-- term:VariationalAutoencoder --> (Variational Autoencoder): 學習潛在變數的條件分佈，並以證據下界同時訓練編碼器與解碼器的生成模型。 <!-- anchor:VariationalAutoencoder -->
> **後驗坍縮** <!-- term:PosteriorCollapse --> (Posterior Collapse): 近似後驗退化為先驗、潛在變數不再攜帶輸入資訊的失效現象。 <!-- anchor:PosteriorCollapse -->


He 等人觀察到訓練初期推論網路追不上移動中的真實後驗，生成模型因而學會忽略編碼；加強推論網路更新能緩解此路徑。[Lagging Inference Networks and 後驗坍縮 <!-- term:PosteriorCollapse --> in Variational Autoencoders](https://arxiv.org/abs/1901.05534) 另有研究顯示，解碼器的局部極小值也能導致坍縮，所以推論落後不能被升格成唯一病因。[The Usual Suspects? Reassessing Blame for VAE 後驗坍縮 <!-- term:PosteriorCollapse -->](https://proceedings.mlr.press/v119/dai20c.html)

## 分析

VAE 最大化**證據下界**（Evidence Lower Bound） <!-- term:EvidenceLowerBound -->：

> [!IMPORTANT]
> **證據下界** <!-- term:EvidenceLowerBound --> (Evidence Lower Bound): 對數邊際似然的可最佳化下界，由重建項與 KL 正則項組成。 <!-- anchor:EvidenceLowerBound -->


$$
\mathcal L(x)=
\mathbb E_{q_\phi(z\mid x)}[\log p_\theta(x\mid z)]
-D_{\mathrm{KL}}(q_\phi(z\mid x)\Vert p(z)).
$$

第一項獎勵重建，第二項限制近似後驗偏離先驗。若強解碼器可在不看 $z$ 時仍預測 $x$，令 $q_\phi(z\mid x)=p(z)$ 會使 KL 為零，而且不必付出很大重建代價。因果鏈是：推論網路暫時不準，$z$ 對解碼器顯得不可靠，解碼器改用自身上下文，使用 $z$ 的邊際收益下降，梯度再把後驗推向先驗。失效點是資訊通道失去功能。

平均 KL 可以分解為與聚合後驗相關的項，卻不能單獨等同**互資訊**（Mutual Information） <!-- term:MutualInformation -->。實務診斷至少要並看 $D_{KL}$、活躍維度、重建在打亂 $z$ 後的變化，以及估計的 $I_q(X;Z)$。

> [!IMPORTANT]
> **互資訊** <!-- term:MutualInformation --> (Mutual Information): 兩個隨機變數之間共享的資訊量，用來量化潛在變數是否攜帶輸入資訊。 <!-- anchor:MutualInformation -->


以下 NumPy 實驗直接隔離「是否使用 $z$」。操弄變因是把每筆輸入的潛在碼打亂；控制模型與輸入；觀察量是均方重建誤差。

```python
import numpy as np

def mse(a, b):
    return np.mean((a - b) ** 2)

def trial(seed):
    rng = np.random.default_rng(seed)
    x = np.linspace(-2, 2, 200)
    z = x + rng.normal(0, 0.05, size=x.size)
    decoder_uses_z = z
    decoder_ignores_z = np.full_like(x, x.mean())
    permuted = rng.permutation(z)
    return (mse(x, decoder_uses_z), mse(x, permuted),
            mse(x, decoder_ignores_z))

runs = np.array([trial(seed) for seed in range(10)])
mean, std = runs.mean(axis=0), runs.std(axis=0)
print("uses z:      ", mean[0], "-> permuted", mean[1], "sd", std[1])
print("ignores z:   ", mean[2], "-> permuted", mean[2], "sd", std[2])
```

使用潛在碼的解碼器在打亂後誤差大增；忽略潛在碼者完全不變。這是介入式使用測試，不是完整 VAE 訓練，也不能估計真實資料上的互資訊 <!-- term:MutualInformation -->。

下圖說明推論落後如何形成自我強化路徑。

```mermaid
flowchart LR
    A[真實後驗隨生成模型移動] --> B[推論網路暫時落後]
    B --> C[z 對解碼器不可靠]
    C --> D[解碼器改靠自身上下文]
    D --> E[使用 z 的收益下降]
    E --> F[q 接近先驗]
    F --> C
```

圖支持一條候選機制，不排除解碼器容量、局部極小值或資料可預測性等替代原因。

代理模型沒有推論網路。下列程式訓練一個最小 VAE，並用契約中的兩個觀察量收尾：逐維 KL 決定的活躍單元數，以及打亂 $z$ 之後的重建變化。

```python
import torch

torch.manual_seed(11)
factors = torch.randn(2048, 1)          # 資料真正只有一個自由度
x = factors @ torch.tensor([[1.0, -0.7, 0.3, 0.5]]) + 0.05 * torch.randn(2048, 4)

class VAE(torch.nn.Module):
    def __init__(self, latent=4):
        super().__init__()
        self.enc = torch.nn.Linear(4, 2 * latent)
        self.dec = torch.nn.Sequential(torch.nn.Linear(latent, 32),
                                       torch.nn.ReLU(), torch.nn.Linear(32, 4))

    def forward(self, x):
        mu, log_var = self.enc(x).chunk(2, dim=-1)
        z = mu + (0.5 * log_var).exp() * torch.randn_like(mu)
        return self.dec(z), mu, log_var, z

for beta in (0.1, 1.0, 10.0):
    model = VAE()
    opt = torch.optim.Adam(model.parameters(), lr=1e-2)
    for _ in range(1500):
        opt.zero_grad()
        xr, mu, log_var, z = model(x)
        kl_dim = -0.5 * (1 + log_var - mu**2 - log_var.exp()).mean(0)
        loss = ((xr - x) ** 2).mean() + beta * kl_dim.sum()
        loss.backward()
        opt.step()
    with torch.no_grad():
        xr, mu, log_var, z = model(x)
        kl_dim = -0.5 * (1 + log_var - mu**2 - log_var.exp()).mean(0)
        shuffled = model.dec(z[torch.randperm(z.size(0))])
        print(beta, "active", int((kl_dim > 0.01).sum()),
              "recon", ((xr - x) ** 2).mean().item(),
              "shuffled", ((shuffled - x) ** 2).mean().item())
```

$\beta$ 提高時活躍單元數應下降；一旦降到零，打亂 $z$ 的重建誤差應與原重建誤差相同——解碼器已經不讀潛在碼。這兩個量一起才構成坍縮證據，單看總 ELBO 不行。這段程式未在撰寫時的環境執行。

驗證契約：資料使用已知因子的合成集與一個真實序列集；切分固定訓練、驗證、測試；seed 為 0–9；指標含 ELBO 兩項、活躍單元、估計互資訊 <!-- term:MutualInformation -->及打亂 $z$ 的重建差；控制解碼器容量與總更新數；操弄推論網路每次生成更新前的步數；若加強推論更新不提高潛在使用，則反駁推論落後為主要機制；當各指標區間跨三次檢查無實務變化或預算耗盡時停止。

## 反思

低 KL 不必然是失效。資料若沒有需要編碼的變異，或任務只要求邊際生成品質，忽略 $z$ 可能是目標的有效解。反之，總 KL 非零也不保證每個維度有用；少數樣本或少數維度可承擔全部訊息。

反例是弱解碼器依賴 $z$，但近似後驗很差。打亂測試會顯示通道被使用，生成品質仍可能不佳。於是「通道使用」和「模型正確」是兩個問題，不能用同一指標代替。

## 實務對比

錯誤做法是看到 KL 接近零便只調低 KL 權重。這可能暫時提高資訊量，也可能破壞先驗匹配。正確做法同時記錄兩個 ELBO 項、互資訊 <!-- term:MutualInformation -->代理量與打亂介入，再比較 KL annealing、解碼器容量及推論更新比例。

另一個錯誤是以重建良好宣稱學到有用表示。正確對比會用下游 probe 或受控因子檢查 $z$，並說明 probe 成功只證明資訊可讀取，不證明因果解纏結。

## 結論

VAE 後驗坍縮 <!-- term:PosteriorCollapse -->的核心不是「KL 數字小」，而是潛在變數不再改變解碼行為。可信診斷需要三項相連證據：後驗接近先驗、介入 $z$ 幾乎不改變輸出，以及訓練動態或模型結構能解釋這條旁路。任何單項成立，都不足以把責任歸給 KL 或推論網路。