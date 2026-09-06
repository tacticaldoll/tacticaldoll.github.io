+++
title = "誤差如何成為參數更新"
date = "2026-09-06T21:16:02+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "求導、更新與泛化是三個不同命題。說明反向傳播如何重用計算圖中間量，以及學習率與條件數如何決定更新是否真的收斂。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "AI 代理人", # term:AiAgent
    "反向傳播", # term:Backpropagation
    "梯度下降", # term:GradientDescent
    "條件數", # term:ConditionNumber
    "泛化", # term:Generalization
    "差異", # term:Delta
  ]
series = ["從有限證據到生成分佈：統計學習如何形成模型能力"]
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

一個只有單一權重的模型要學 $y=3x$，看似沒有失敗空間。相同資料與相同均方誤差下，學習率 $0.1$ 會靠近斜率 3，學習率 $0.5$ 卻可能來回跳動。這個事故揭示：可表示正確函數、能算出導數、以及更新實際收斂，是三個不同命題。

**反向傳播**（Backpropagation） <!-- term:Backpropagation -->使用鏈式法則重用計算圖中的中間量；**梯度下降**（Gradient Descent） <!-- term:GradientDescent -->再把導數轉成參數位移。Rumelhart、Hinton 與 Williams 的經典工作描述了以輸出誤差反覆調整連接權重、形成隱藏表示的程序。[Nature 論文](https://www.nature.com/articles/323533a0) 回過頭來看，真正要追問的是：誤差經過哪些**中介變數**（Mediating Variable） <!-- term:MediatingVariable -->才成為能力，又會在哪裡斷裂？

> [!IMPORTANT]
> **反向傳播** <!-- term:Backpropagation --> (Backpropagation): 以連鎖律沿計算圖回傳誤差，有效求得各層參數梯度的演算法。 <!-- anchor:Backpropagation -->
> **梯度下降** <!-- term:GradientDescent --> (Gradient Descent): 沿損失函數負梯度方向反覆更新參數的最佳化方法。 <!-- anchor:GradientDescent -->
> **中介變數** <!-- term:MediatingVariable --> (Mediating Variable): 位於原因與結果之間、承載並使該段因果得以被觀察的可測量變數。 <!-- anchor:MediatingVariable -->


## 分析

### 求導不是更新，更新不是泛化

對兩層模型 $\hat y=W_2\sigma(W_1x)$ 與損失 $L(\hat y,y)$，反向傳播 <!-- term:Backpropagation -->計算

$$
\nabla_{W_1}L
=
\frac{\partial L}{\partial \hat y}
\frac{\partial \hat y}{\partial W_2\sigma}
\frac{\partial \sigma}{\partial W_1x}
\frac{\partial W_1x}{\partial W_1}.
$$

它回答「目前參數附近，損失對每個參數有多敏感」。更新規則

$$
\theta_{t+1}=\theta_t-\eta\nabla L(\theta_t)
$$

才回答「要移到哪裡」，其中 $\eta$ 是學習率。從發散軌跡回推的因果鏈是：曲率決定局部安全步幅；單一 $\eta$ 將梯度縮放成位移；步幅超過穩定區後跨越谷底；新的梯度反向且幅度更大，最後形成振盪或爆炸。失效點不在鏈式法則算錯，而在一階局部資訊被用到過遠。

若二次目標為 $L(w)=\frac{a}{2}(w-w^*)^2$，則誤差更新為

$$
w_{t+1}-w^*=(1-\eta a)(w_t-w^*).
$$

只有 $|1-\eta a|<1$，也就是 $0<\eta<2/a$，誤差才在線性模型下收縮。這個推導讓學習率的作用可被反駁，而不是依靠「太大可能不穩」的形容。深度網路的曲率會隨位置改變，但局部穩定區仍是診斷起點。[《Deep Learning》的最佳化章](https://www.deeplearningbook.org/contents/optimization.html)

### 同時檢查導數與更新的最小實驗

下列程式先以中央差分檢查解析梯度，再以三個學習率比較軌跡。這種雙控制把「反傳實作錯誤」與「更新規則不穩」分開。

```python
import numpy as np

x = np.array([-2.0, -1.0, 1.0, 2.0])
y = 3.0 * x

def loss(w):
    return np.mean((w * x - y) ** 2)

def gradient(w):
    return 2.0 * np.mean((w * x - y) * x)

eps = 1e-6
analytic = gradient(0.4)
numeric = (loss(0.4 + eps) - loss(0.4 - eps)) / (2 * eps)
print("gradient error", abs(analytic - numeric))

for learning_rate in (0.05, 0.1, 0.5):
    w = 0.0
    path = []
    for _ in range(12):
        path.append((w, loss(w)))
        w -= learning_rate * gradient(w)
    print(learning_rate, path[-1], "max_loss", max(v for _, v in path))
```

梯度誤差應接近浮點精度，這支持求導實作。三條路徑若隨學習率出現收縮、振盪與發散**差異**（Delta） <!-- term:Delta -->，則支持步幅—曲率機制。若數值梯度不吻合，必須先停止討論最佳化；若梯度吻合但所有路徑都穩定，則目前學習率沒有跨越這個資料的穩定界線。

> [!IMPORTANT]
> **差異** <!-- term:Delta --> (Delta): 特定變更的契約，用於驅動實作並作為驗證實作的基準對象。 <!-- anchor:Delta -->


### 訊號還要穿過表示

即使更新穩定，深層鏈式乘積仍可能讓早期層收到近零或極大訊號。資料尺度、飽和激活、初始化與殘差路徑會改變乘積。這形成另一條鏈：輸出誤差經 Jacobian 傳回；奇異值反覆縮放方向；部分參數長期收不到可辨識訊號；理論上可表示的特徵未被找到。Bengio 的實務建議把初始化、激活與梯度式最佳化視為共同條件，而非架構外的雜項。[梯度訓練綜述](https://arxiv.org/abs/1206.5533)

下圖把容易混在一起的三層責任拆開。它解決的是「損失下降究竟證明了什麼」的閱讀問題。

```mermaid
flowchart LR
    Y["輸出與目標"] --> L["損失差"]
    L --> B["反向傳播：求局部敏感度"]
    B --> G["梯度張量"]
    G --> U["最佳化器：形成位移"]
    U --> P["新參數"]
    P --> F["新一輪行為"]
    F -->|"僅在獨立資料上評估"| C["能力證據"]
```

圖中最重要的是最後一條邊。損失下降只證明更新改善了被計算的目標；它不會自動產生未見資料上的能力證據。

### 框架對照：autograd 只交付梯度，位移仍由最佳化器決定

上面的實驗手寫導數。真實框架把求導自動化，卻沒有把「求導」與「更新」合併。下列程式用 `gradcheck` 確認導數，再讓同一份梯度經過三個不同最佳化器。

```python
import torch

x = torch.tensor([-2.0, -1.0, 1.0, 2.0], dtype=torch.double)
y = 3.0 * x

def loss_fn(w):
    return ((w * x - y) ** 2).mean()

w = torch.tensor([0.4], dtype=torch.double, requires_grad=True)
print("gradcheck", torch.autograd.gradcheck(loss_fn, (w,)))

for name, make in (("sgd-0.05", lambda p: torch.optim.SGD(p, lr=0.05)),
                   ("sgd-0.5", lambda p: torch.optim.SGD(p, lr=0.5)),
                   ("adam-0.05", lambda p: torch.optim.Adam(p, lr=0.05))):
    w = torch.zeros(1, dtype=torch.double, requires_grad=True)
    opt, worst = make([w]), 0.0
    for _ in range(12):
        opt.zero_grad()
        loss = loss_fn(w)
        worst = max(worst, loss.item())
        loss.backward()
        opt.step()
    print(name, w.item(), "max_loss", worst)
```

`gradcheck` 通過表示反向實作正確；三個最佳化器仍會給出收縮、振盪或發散的不同軌跡。這正是本節的分工主張：導數正確不保證更新穩定。程式未在撰稿環境執行。

### 驗證契約

完整檢查要把數值正確性、動力穩定性與**泛化**（Generalization） <!-- term:Generalization -->分開。以下契約只處理前兩者，避免把玩具回歸誇大成深網結論。

> [!IMPORTANT]
> **泛化** <!-- term:Generalization --> (Generalization): 模型在訓練樣本以外的資料上維持表現的能力。 <!-- anchor:Generalization -->


| 項目 | 契約 |
| :--- | :--- |
| 資料 | 固定四個 $x$ 與無噪聲目標 $y=3x$ |
| 切分 | 本機制實驗不設泛化 <!-- term:Generalization -->切分；所有點只用於解析二次曲面 |
| seed | 無隨機性；若加入初始化噪聲，預註冊 0–29 |
| 指標 | 中央差分誤差、每步損失、距離 $|w-3|$ |
| 控制變因 | 資料、初值、步數與梯度公式固定，只改學習率 |
| 觀察量 | 誤差收縮比與最大損失 |
| 反駁條件 | 解析梯度與數值梯度不符，或軌跡不遵守推導出的穩定區 |
| 停止條件 | 12 步全部完成；出現非有限值則提前停止並記為發散 |

這份契約能隔離一階更新的局部幾何。它不能推出非凸深網必然收斂到全域解。

## 反思

一個重要反例是重新參數化。同一個函數可以由不同尺度的權重表示，梯度的數值大小與路徑卻不同。因此，大梯度不必然表示該功能重要，小梯度也不必然表示該參數沒有因果作用。

另一個邊界是隨機梯度。小批次梯度是完整訓練目標的帶噪估計；噪聲可能妨礙瞬時下降，也可能幫助離開某些狹窄區域。故「每一步都降低批次外損失」不是 SGD 的必要條件。

最後，兩個初始化可能到達功能近似但參數不同的解。反向傳播 <!-- term:Backpropagation -->解釋的是某條已觀察軌跡如何產生，不提供唯一的高階語意分解。這限制了從單一梯度或單一神經元直接推論概念的做法。

## 實務對比

錯誤診斷看到訓練不動便立刻更換模型。若解析梯度本身錯誤，換架構只會掩蓋實作問題；若梯度正確但尺度差數量級，真正問題可能是**條件數**（Condition Number） <!-- term:ConditionNumber -->與步幅。

> [!IMPORTANT]
> **條件數** <!-- term:ConditionNumber --> (Condition Number): 損失曲面各方向曲率的比值，決定固定學習率下梯度下降的收斂速度。 <!-- anchor:ConditionNumber -->


較好的順序是先用小模型做有限差分，再記錄各層梯度範數與更新／權重比。確認訊號正確後，才比較學習率、正規化、殘差路徑或最佳化器。一次只改一項，才能把改善歸因到具體機制。

另一個錯誤是以訓練損失下降宣稱表示已正確形成。對照做法另設驗證資料與功能探測；若訓練下降而驗證惡化，更新程序成功執行，學習目標卻沒有形成可遷移能力。

## 結論

誤差成為能力至少要跨過三道門：反向傳播 <!-- term:Backpropagation -->必須正確計算局部敏感度，最佳化器必須在曲率容許的尺度內累積更新，所得參數還必須在獨立資料上產生所需行為。

因此，導數正確、訓練收斂與泛化 <!-- term:Generalization -->成立應分別驗證。把三者壓成一句「模型學到了」，會讓數值錯誤、動力失穩與目標失配無法區分。