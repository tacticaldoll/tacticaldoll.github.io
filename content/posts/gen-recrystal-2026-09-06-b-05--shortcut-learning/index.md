+++
title = "高分模型為何仍可能學錯：偽相關與跨環境反例"
date = "2026-09-06T22:50:05+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "同分佈的高分可能建立在錯的理由上。用環境切分與跨環境反例分離偽相關形成的捷徑，說明測試分數為何不能代替穩定性證據。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "AI 代理人", # term:AiAgent
    "偽相關", # term:SpuriousCorrelation
    "捷徑學習", # term:ShortcutLearning
    "經驗風險", # term:EmpiricalRisk
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

測試分數很高的模型仍可能在換醫院、相機或網站模板後失效。問題未必是部署後才退化；模型可能從一開始就使用**偽相關**（Spurious Correlation） <!-- term:SpuriousCorrelation -->形成的**捷徑學習**（Shortcut Learning） <!-- term:ShortcutLearning -->。Geirhos 等人將捷徑定義為在標準基準有效、卻無法轉移到更具挑戰條件的決策規則，並把模型解釋與基準設計列為共同防線。[捷徑學習 <!-- term:ShortcutLearning --> in Deep Neural Networks](https://doi.org/10.1038/s42256-020-00257-z)

> [!IMPORTANT]
> **偽相關** <!-- term:SpuriousCorrelation --> (Spurious Correlation): 在訓練分佈中與標籤同時出現、但不具因果支撐的統計關聯。 <!-- anchor:SpuriousCorrelation -->
> **捷徑學習** <!-- term:ShortcutLearning --> (Shortcut Learning): 模型採用在標準基準有效、卻無法轉移到更具挑戰條件的決策規則。 <!-- anchor:ShortcutLearning -->


這就衍生出一個問題：當核心訊號與捷徑都能降低**經驗風險**（Empirical Risk） <!-- term:EmpiricalRisk -->時，什麼證據能辨認模型用的是哪一條？

> [!IMPORTANT]
> **經驗風險** <!-- term:EmpiricalRisk --> (Empirical Risk): 模型在有限訓練樣本上的平均損失，是目標分佈期望風險的間接替代量。 <!-- anchor:EmpiricalRisk -->


## 分析

經驗風險 <!-- term:EmpiricalRisk -->最小化選擇

$$
\hat f=\arg\min_{f\in\mathcal H}\frac1n\sum_{i=1}^n\ell(f(x_i),y_i).
$$

若特徵 $x_c$ 與 $x_s$ 在訓練環境都預測 $y$，目標不會自動偏好人類稱為「核心」的 $x_c$。資料頻率、模型偏置與最佳化容易度會決定先被利用的規則。因果鏈是：資料生成程序把背景與標籤綁定，隨機切分保留此關係，捷徑帶來低損失，測試分數確認了同一關係，部署環境一旦打破它便暴露失敗。

以下 NumPy 實驗建立三個環境。操弄變因是捷徑與標籤的相關方向；核心規則保持不變；觀察量是兩個單特徵分類器的準確率。

```python
import numpy as np

y = np.array([0, 0, 1, 1] * 50)
core = y.copy()
shortcut_train = y.copy()
shortcut_same = y.copy()
shortcut_flip = 1 - y

def score(feature):
    return np.mean(feature == y)

print("core", score(core))
print("shortcut/iid", score(shortcut_same))
print("shortcut/counterexample", score(shortcut_flip))
```

訓練與同分佈測試都無法區分兩條規則；反相關環境使捷徑從 100% 降到 0%。這個設計支持「需要跨環境反例」，但它預先知道核心特徵。真實系統通常沒有這項特權。

下圖把案例的回推鏈明文化。

```mermaid
flowchart LR
    A[來源環境綁定背景與標籤] --> B[隨機切分保留綁定]
    B --> C[捷徑快速降低損失]
    C --> D[同分佈測試高分]
    D --> E[團隊宣稱可部署能力]
    E --> F[新環境解除或反轉綁定]
    F --> G[表現崩落]
```

圖支持資料契約與評測契約共同造成誤判。它不能證明捷徑一定「簡單」，也不能證明模型沒有同時使用核心訊號。

上面的比較預先知道哪個特徵是核心。下列程式讓模型自己在兩個同樣有預測力的特徵之間分配權重，觀察它偏好哪一個。

```python
import torch

torch.manual_seed(0)

def make(n, shortcut_sign, noise):
    y = torch.randint(0, 2, (n, 1)).float()
    core = (2 * y - 1) + noise * torch.randn(n, 1)          # 較吵的核心特徵
    shortcut = shortcut_sign * (2 * y - 1) + 0.05 * torch.randn(n, 1)
    return torch.cat((core, shortcut), dim=1), y

x, y = make(4000, +1, noise=0.8)
model = torch.nn.Linear(2, 1)
opt = torch.optim.Adam(model.parameters(), lr=0.05)
for _ in range(800):
    opt.zero_grad()
    torch.nn.functional.binary_cross_entropy_with_logits(model(x), y).backward()
    opt.step()
print("weights core/shortcut", model.weight.detach().flatten().tolist())

for name, sign in (("iid", +1), ("flipped", -1)):
    xe, ye = make(2000, sign, noise=0.8)
    acc = (((model(xe) > 0).float()) == ye).float().mean().item()
    print(name, "accuracy", acc)
```

兩個特徵在訓練環境有同樣的標籤相關性，只有噪聲不同。模型的捷徑權重應明顯大於核心權重，同分佈準確率仍然很高，反相關環境則應掉到 0.5 以下。這說明捷徑偏好來自可用性而非相關性強度——把兩者混談，會誤以為提高核心特徵的相關性就能解決問題。這段程式未在撰寫時的環境執行。

驗證契約：資料按來源、時間或設備建立環境，禁止先混合再隨機切分；每環境內另留測試集；seed 為 0–9；指標含平均與最差群組準確率、群組**校準**（Calibration） <!-- term:Calibration -->、反事實翻轉率；控制標籤、模型容量、訓練步數；操弄疑似捷徑但保持任務語義；若介入捷徑後行為不變，則反駁模型依賴該捷徑；當最差群組區間窄於 3 個百分點或資料蒐集上限到達時停止。

> [!IMPORTANT]
> **校準** <!-- term:Calibration --> (Calibration): 模型輸出機率與實際正確率的一致程度。 <!-- anchor:Calibration -->


## 反思

捷徑不等於完全無用。背景在目前環境可能真的有預測力。失敗來自部署主張越過了相關性可維持的範圍，而非模型神秘地違反訓練目標。

反例是疑似捷徑本身位於穩定因果鏈上，例如固定製程中的感測器校準 <!-- term:Calibration -->訊號。刻意移除它可能降低真實效用。另一邊界是「人類可理解」不等於因果；人類指定的核心特徵也可能只是另一個相關代理。

## 實務對比

錯誤做法是把同一醫院影像隨機切成訓練與測試，然後以高分宣稱跨院**泛化**（Generalization） <!-- term:Generalization -->。正確做法按醫院或設備切分，另外建立疾病語義相同、設備標記改變的對照。

> [!IMPORTANT]
> **泛化** <!-- term:Generalization --> (Generalization): 模型在訓練樣本以外的資料上維持表現的能力。 <!-- anchor:Generalization -->


另一個錯誤是無差別增加同來源資料。若新資料保留相同偽相關 <!-- term:SpuriousCorrelation -->，模型只會更有信心。正確做法增加能區分候選規則的環境，並在獨立資料上確認探索所得切片。

## 結論

高同分佈分數只能證明某條規則在該環境有效，不能證明模型採用了可轉移機制。偽相關 <!-- term:SpuriousCorrelation -->診斷的關鍵不是看更多相同樣本，而是設計「任務語義保持、疑似捷徑改變」的環境。若模型在這個反例中仍穩定，捷徑假說才被削弱；若它隨捷徑翻轉，原來的高分便是學錯的證據，而不是後來的退化。