+++
title = "有限樣本何時足以支持能力主張"
date = "2026-09-06T21:16:01+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "低訓練誤差不等於能力。拆解資料生成分佈、假設空間與選擇準則三層，說明把經驗風險外推成目標分佈能力還需要哪些條件。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "AI 代理人", # term:AiAgent
    "統計學習", # term:StatisticalLearning
    "經驗風險", # term:EmpiricalRisk
    "泛化", # term:Generalization
    "假設空間", # term:HypothesisSpace
    "損失函數", # term:LossFunction
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

十二個帶噪聲的點足以製造一個常見誤判。十次多項式可以把訓練誤差壓得比二次多項式更低，曲線卻在觀測區間外劇烈彎折。問題不是「模型是否記住」，而是有限資料何時能支持對未見樣本的能力主張。

**統計學習**（Statistical Learning） <!-- term:StatisticalLearning -->把這個問題寫成三個不同對象：資料生成分佈、可選函數集合，以及選擇函數的**準則**（Guidelines） <!-- term:Guidelines -->。深度學習教材也明確區分訓練集上的目標與資料生成分佈上的期望風險；前者只是後者的間接替代量。[Goodfellow、Bengio 與 Courville，第 8 章](https://www.deeplearningbook.org/contents/optimization.html)

> [!IMPORTANT]
> **統計學習** <!-- term:StatisticalLearning --> (Statistical Learning): 把學習寫成資料生成分佈、假設空間與選擇準則三者關係的理論框架。 <!-- anchor:StatisticalLearning -->
> **準則** <!-- term:Guidelines --> (Guidelines): 強制性的專案準則，指導如何正確地做事 <!-- anchor:Guidelines -->


這裡真正要問的是：觀察到低**經驗風險**（Empirical Risk） <!-- term:EmpiricalRisk -->後，還需要哪些條件，才能把它外推成目標分佈上的能力？

> [!IMPORTANT]
> **經驗風險** <!-- term:EmpiricalRisk --> (Empirical Risk): 模型在有限訓練樣本上的平均損失，是目標分佈期望風險的間接替代量。 <!-- anchor:EmpiricalRisk -->


## 分析

### 從低訓練誤差回推三層選擇

設資料集 $S=\{(x_i,y_i)\}_{i=1}^n$ 由分佈 $P$ 抽得，**假設空間**（Hypothesis Space） <!-- term:HypothesisSpace -->為 $\mathcal H$。經驗風險 <!-- term:EmpiricalRisk -->與母體風險分別是

> [!IMPORTANT]
> **假設空間** <!-- term:HypothesisSpace --> (Hypothesis Space): 學習演算法可選函數所構成的集合，其大小決定泛化保證的鬆緊。 <!-- anchor:HypothesisSpace -->


$$
\hat R_S(h)=\frac{1}{n}\sum_{i=1}^n \ell(h(x_i),y_i),
\qquad
R_P(h)=\mathbb E_{(x,y)\sim P}[\ell(h(x),y)].
$$

經驗風險 <!-- term:EmpiricalRisk -->最小化選擇 $\hat h\in\arg\min_{h\in\mathcal H}\hat R_S(h)$。這個式子定義的是選擇程序，不是**泛化**（Generalization） <!-- term:Generalization -->保證。從十次曲線的樣本外偏離回推，可得到一條三節點因果鏈：樣本只約束少數位置；較大的 $\mathcal H$ 提供更多同樣貼合樣本的函數；再次使用同一批資料選擇最低誤差者，會把抽樣噪聲也當成可利用訊號。失效點是把「被選中的訓練最小值」當成未經選擇偏差的風險估計。

> [!IMPORTANT]
> **泛化** <!-- term:Generalization --> (Generalization): 模型在訓練樣本以外的資料上維持表現的能力。 <!-- anchor:Generalization -->


這條鏈需要外加泛化 <!-- term:Generalization -->落差

$$
g(h,S)=R_P(h)-\hat R_S(h).
$$

若樣本近似獨立同分佈、損失受控，而且假設空間 <!-- term:HypothesisSpace -->相對樣本量不過度複雜，才可能用一致收斂或穩定性論證控制 $g$。Shalev-Shwartz 與 Ben-David 的教材把「受限制假設類上的經驗風險 <!-- term:EmpiricalRisk -->最小化」作為正式學習模型的起點，並特別處理單純 ERM 可能過度擬合的條件。[《Understanding **機器學習**（Machine Learning） <!-- term:MachineLearning -->》](https://www.cs.huji.ac.il/~shais/UnderstandingMachineLearning/)

> [!IMPORTANT]
> **機器學習** <!-- term:MachineLearning --> (Machine Learning): 先界定可選函數的範圍，再以資料估計其中參數的建模方法。 <!-- anchor:MachineLearning -->


### 一個隔離容量與樣本量的實驗

下列實驗固定真實函數、噪聲分佈與測試格點，只操弄訓練樣本數及多項式次數。它解決的閱讀問題是：低訓練誤差究竟來自較好的規律估計，還是來自更多可貼合噪聲的自由度。

```python
import numpy as np

def trial(seed, n, degree):
    rng = np.random.default_rng(seed)
    x = np.linspace(-1.0, 1.0, n)
    y = x**2 + rng.normal(0.0, 0.08, size=n)
    coef = np.polyfit(x, y, degree)
    train = np.mean((np.polyval(coef, x) - y) ** 2)
    grid = np.linspace(-1.3, 1.3, 400)
    target = np.mean((np.polyval(coef, grid) - grid**2) ** 2)
    return train, target

for n in (12, 40):
    for degree in (1, 2, 10):
        values = np.array([trial(seed, n, degree) for seed in range(30)])
        mean = values.mean(axis=0)
        print(n, degree, "train", mean[0], "target", mean[1])
```

應觀察的是訓練與目標誤差的差，而不是單看任一數值。若高次模型只在 $n=12$ 時出現大落差，容量與有限樣本的交互作用得到支持；若所有 seed 與樣本量下都沒有落差，這個具體反例便失去效力。實驗不能證明所有大型模型都會過度擬合，因為最佳化偏置、正則化與資料增強會改變實際可達函數。

### 框架對照：同一個落差在 autograd 下仍然存在

多項式擬合用閉式解，容易讓人以為落差是 `polyfit` 的性質。下列 PyTorch 版本改用梯度訓練的網路，量的仍是 $g(D)=$ 目標誤差 $-$ 訓練誤差。

```python
import torch

def gap(seed, n, width):
    torch.manual_seed(seed)
    x = torch.linspace(-1.0, 1.0, n).unsqueeze(1)
    y = x**2 + 0.08 * torch.randn(n, 1)
    net = torch.nn.Sequential(torch.nn.Linear(1, width), torch.nn.Tanh(),
                              torch.nn.Linear(width, 1))
    opt = torch.optim.Adam(net.parameters(), lr=0.05)
    for _ in range(2000):
        opt.zero_grad()
        loss = ((net(x) - y) ** 2).mean()
        loss.backward()
        opt.step()
    grid = torch.linspace(-1.3, 1.3, 400).unsqueeze(1)
    with torch.no_grad():
        target = ((net(grid) - grid**2) ** 2).mean()
    return loss.item(), target.item()

for n in (12, 40):
    for width in (4, 256):
        runs = torch.tensor([gap(s, n, width) for s in range(30)])
        print(n, width, runs.mean(0).tolist())
```

兩份程式應給出同方向的結論：落差隨 $n$ 縮小、隨容量放大。若只有閉式解出現落差，問題就在擬合程序而不在有限樣本。這段程式不宣稱已執行；撰稿環境沒有安裝 PyTorch。

### 驗證契約

要把「能力形成」變成可反駁命題，需要預先固定以下契約。各欄分別阻止測試資料洩漏、只報最好 seed，以及事後更換指標。

| 項目 | 契約 |
| :--- | :--- |
| 資料 | $y=x^2+\epsilon$，$\epsilon\sim\mathcal N(0,0.08^2)$；另建 $[-1.3,1.3]$ 等距目標格點 |
| 切分 | 訓練點只在 $[-1,1]$；目標格點不參與擬合 |
| seed | 0–29 全部報告平均與標準差 |
| 指標 | 訓練 MSE、目標 MSE、兩者差值 |
| 控制變因 | 真實函數、噪聲尺度、測試格點與擬合程序固定 |
| 觀察量 | 樣本數 × 次數對泛化 <!-- term:Generalization -->落差的交互作用 |
| 反駁條件 | 高次模型的落差不高於二次模型，或差異不隨樣本數改變 |
| 停止條件 | 30 個預註冊 seed 完成；不得因結果不顯著追加 seed |

這份契約驗證的是容量與有限樣本能否在此資料機制中造成選擇落差。它不驗證部署分佈是否與實驗分佈相同。

## 反思

第一個邊界是分佈偏移。即使 $g(h,S)$ 在 $P$ 下很小，部署分佈若變成 $Q$，真正關心的是 $R_Q(h)$。在 $P$ 上建立的泛化 <!-- term:Generalization -->證據不能自動跨越支持集、標註規則或族群比例的改變。

第二個邊界是**損失函數**（Loss Function） <!-- term:LossFunction -->。低平均 MSE 不能推出罕見區域、安全成本或**校準**（Calibration） <!-- term:Calibration -->都良好。損失把多維後果壓成可最佳化數字；沒有被計價的錯誤不會因訓練成功而消失。

> [!IMPORTANT]
> **損失函數** <!-- term:LossFunction --> (Loss Function): 把模型輸出與目標之間的差距量化為單一數值的評分函數。 <!-- anchor:LossFunction -->
> **校準** <!-- term:Calibration --> (Calibration): 模型輸出機率與實際正確率的一致程度。 <!-- anchor:Calibration -->


反例也很重要。若真實關係確為二次函數、噪聲很低且樣本密集，較大假設空間 <!-- term:HypothesisSpace -->不必然造成差泛化 <!-- term:Generalization -->；正則化也可能讓形式上很大的空間只探索平滑解。因而「參數多」本身不是充分診斷，必須檢查選擇程序實際使用了多少自由度。

## 實務對比

錯誤做法是在同一資料集上反覆試模型，最後只呈現最低誤差。資料此時同時扮演擬合、選擇與證明三個角色；即使最後數字很低，也無法估計選擇造成的樂觀偏差。

較可靠的做法先鎖定訓練、驗證與最終測試的職責。訓練集估計參數，驗證集選擇超參數，測試集只在決策凍結後使用一次。若部署存在低頻但高代價區域，還要預先分群報告，而不是用總平均掩蓋它。

另一個錯誤是把插值失敗直接等同外推失敗。訓練區間內的未見點與區間外的新點依賴不同假設；隨機切分只能測前者。正確對比會建立隨機切分與時間、位置或群組外切分，並分別說明它們模擬哪種部署條件。

## 結論

有限資料不會單獨決定模型能力。它只在假設空間 <!-- term:HypothesisSpace -->、損失與選擇程序共同建立的通道中排除部分函數。

因此，一項可檢查的能力主張必須明列三件事：樣本來自哪個分佈，候選函數如何受限，以及哪些未參與選擇的觀察能推翻它。訓練誤差回答「這批證據被解釋得多好」；只有獨立評估與成立條件，才回答這份解釋能走多遠。