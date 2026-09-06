+++
title = "平均準確率不變，壓縮仍可能失真：模型近似的保真度契約"
date = "2026-09-06T22:50:07+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "量化、剪枝與知識蒸餾都能省資源，建立近似的方式卻不同。平均準確率相同時，用個體翻轉、機率校準與罕見類別看見被平均掩蓋的失真。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "AI 代理人", # term:AiAgent
    "模型壓縮", # term:ModelCompression
    "量化", # term:Quantization
    "剪枝", # term:Pruning
    "知識蒸餾", # term:KnowledgeDistillation
    "校準", # term:Calibration
    "實務對比", # term:PracticalContrastiveExamples
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

把模型移到手機或邊緣裝置，通常要降低記憶體、延遲或能耗。**量化**（Quantization） <!-- term:Quantization -->、**剪枝**（Pruning） <!-- term:Pruning -->與**知識蒸餾**（Knowledge Distillation） <!-- term:KnowledgeDistillation -->都能達成這個目的，但三者建立近似的方式不同。即使壓縮前後平均準確率相同，決策邊界附近、罕見類別與機率**校準**（Calibration） <!-- term:Calibration -->仍可能改變。

> [!IMPORTANT]
> **量化** <!-- term:Quantization --> (Quantization): 以較少位元表示權重或啟動值，改變數值格點以降低記憶體與計算成本的近似方法。 <!-- anchor:Quantization -->
> **剪枝** <!-- term:Pruning --> (Pruning): 移除模型中影響較小的連接或結構，以縮減規模的壓縮方法。 <!-- anchor:Pruning -->
> **知識蒸餾** <!-- term:KnowledgeDistillation --> (Knowledge Distillation): 以較大模型的輸出分佈為目標，訓練較小模型重新估計其行為的壓縮方法。 <!-- anchor:KnowledgeDistillation -->
> **校準** <!-- term:Calibration --> (Calibration): 模型輸出機率與實際正確率的一致程度。 <!-- anchor:Calibration -->


整數推論研究顯示，權重與啟動值量化 <!-- term:Quantization -->可顯著降低記憶體並改善特定 ARM CPU 上的延遲，但論文同時強調應在真實硬體測量，而不是從位元數直接推斷速度。[量化 <!-- term:Quantization --> and Training of Neural Networks for Efficient Integer-Arithmetic-Only Inference](https://openaccess.thecvf.com/content_cvpr_2018/html/Jacob_Quantization_and_Training_CVPR_2018_paper.html) 知識蒸餾 <!-- term:KnowledgeDistillation -->則用教師的軟輸出訓練較小學生，並非逐參數保存。[Distilling the **描述性知識**（Knowledge） <!-- term:Knowledge --> in a Neural Network](https://arxiv.org/abs/1503.02531)

> [!IMPORTANT]
> **描述性知識** <!-- term:Knowledge --> (Knowledge): 逆向工程產出的描述性知識，在專案中被視為債務指標 <!-- anchor:Knowledge -->


## 分析

均勻量化 <!-- term:Quantization -->可寫成

$$
Q_\**差異**（Delta） <!-- term:Delta -->=\差異 <!-- term:Delta -->\operatorname{round}(w/\差異 <!-- term:Delta -->),
$$

> [!IMPORTANT]
> **差異** <!-- term:Delta --> (Delta): 特定變更的契約，用於驅動實作並作為驗證實作的基準對象。 <!-- anchor:Delta -->


在不截斷且取最近格點時，單一權重誤差滿足 $|Q_\差異 <!-- term:Delta -->-w|\leq\差異 <!-- term:Delta -->/2$。但輸出誤差還受輸入尺度、層間放大與非線性影響。因果鏈是：表示格點變粗，權重或啟動值產生誤差，logit 邊際縮小或改號，個體決策翻轉，而平均值可能因正負翻轉互抵而不變。

剪枝 <!-- term:Pruning -->把連接設為零，失真來自被移除方向；重新訓練可能讓剩餘參數補償。**蒸餾**（Distill） <!-- term:Distill -->最小化學生與教師在蒸餾 <!-- term:Distill -->資料上的輸出差。溫度為 $T$ 的軟目標是

> [!IMPORTANT]
> **蒸餾** <!-- term:Distill --> (Distill): 從長對話或大量開發脈絡中萃取關鍵資訊的處理過程。 <!-- anchor:Distill -->


$$
p_i^{(T)}=\frac{\exp(z_i/T)}{\sum_j\exp(z_j/T)}.
$$

它暴露類別間的相對分數，但學生容量與資料覆蓋限制能被轉移的行為。三種方法共享「資源換近似」的上位問題，不共享低階失真機制。

以下 NumPy 實驗隔離量化 <!-- term:Quantization -->造成的邊界翻轉。操弄量化 <!-- term:Quantization -->步長；控制輸入與分類閾值；觀察逐樣本 margin、翻轉率及平均準確率。

```python
import numpy as np

x = np.array([0.10, 0.49, 0.51, 0.80, 2.00])
y = np.array([0, 0, 1, 1, 1])
w, b, step = 0.26, -0.13, 0.20
qw = step * np.round(w / step)
qb = step * np.round(b / step)

base_margin = w * x + b
compressed_margin = qw * x + qb
base = base_margin >= 0
compressed = compressed_margin >= 0
print(np.c_[x, base_margin, compressed_margin, base, compressed])
print("flip rate", np.mean(base != compressed))
print("accuracy", np.mean(base == y), np.mean(compressed == y))
```

讀者應觀察低邊際案例最容易翻轉。這個線性例只隔離數值格點，不能代表剪枝 <!-- term:Pruning -->或蒸餾 <!-- term:Distill -->，也不能把單一權重誤差界延伸成深層網路的全域界。

這張表解決三種壓縮常被同名掩蓋的比較問題。

| 方法 | 被改變的對象 | 必要對照 | 特有觀察量 |
| :--- | :--- | :--- | :--- |
| 量化 <!-- term:Quantization --> | 權重與啟動值的數值格點 | 同一圖、同一硬體上的浮點與整數路徑 | 飽和率、逐層量化 <!-- term:Quantization -->誤差、翻轉率 |
| 剪枝 <!-- term:Pruning --> | 連接、通道或結構 | 同一稀疏度下有無重新訓練 | 稀疏模式、延遲、切片損失 |
| 蒸餾 <!-- term:Distill --> | 學生的函數與容量 | 教師、硬標籤學生與軟目標學生 | 教師忠實度、校準 <!-- term:Calibration -->、資料外差異 <!-- term:Delta --> |

表格顯示共同平均準確率不足以定位失真。它也不能決定最佳方法；硬體核心、稀疏支援與任務風險會改變選擇。

線性例子沒有層間放大。下列程式量化 <!-- term:Quantization -->一個已訓練網路的全部權重，並同時報告平均準確率與翻轉率——契約要求兩者並列的原因就在這裡。

```python
import copy
import torch

torch.manual_seed(0)
x = torch.randn(4000, 8)
y = (x[:, 0] + 0.5 * x[:, 1] > 0).long()
net = torch.nn.Sequential(torch.nn.Linear(8, 32), torch.nn.ReLU(),
                          torch.nn.Linear(32, 2))
opt = torch.optim.Adam(net.parameters(), lr=1e-2)
for _ in range(600):
    opt.zero_grad()
    torch.nn.functional.cross_entropy(net(x), y).backward()
    opt.step()

with torch.no_grad():
    base_logit = net(x)
    base = base_logit.argmax(1)
    margin = (base_logit[:, 1] - base_logit[:, 0]).abs()
    for bits in (8, 4, 2):
        clone = copy.deepcopy(net)
        state = {k: v.clone() for k, v in net.state_dict().items()}
        for k, v in state.items():
            step = v.abs().max() / (2 ** (bits - 1) - 1)
            state[k] = step * torch.round(v / step)
        clone.load_state_dict(state)
        q = clone(x).argmax(1)
        low = margin < margin.quantile(0.1)
        print(bits, "acc", (q == y).float().mean().item(),
              "flip", (q != base).float().mean().item(),
              "flip@low-margin", (q[low] != base[low]).float().mean().item())
```

位元數下降時平均準確率可能幾乎不動，翻轉率卻上升，而且翻轉應集中在低 margin 切片。若翻轉在各 margin 分位上均勻分布，數值格點就不是主要機制，該另找原因。這段程式未在撰寫時的環境執行。

驗證契約：資料使用凍結測試集、低邊際集及罕見切片；切分與校準 <!-- term:Calibration -->集互斥；seed 為 0–9；指標含平均與最差切片分數、翻轉率、ECE、延遲、記憶體和能耗；控制前後處理、批次、硬體與測量工具；操弄位元數、稀疏度或學生容量；若行為差異 <!-- term:Delta -->在未壓縮重跑中同樣出現，則反駁壓縮歸因；在達到資源目標且所有風險指標低於預設容差，或 Pareto 前緣不再改善時停止。

## 反思

壓縮不是退化的同義詞。量化 <!-- term:Quantization -->感知訓練或重新訓練可能改善指定基準；浮點執行也會因硬體與算子融合不同而變動。合理契約應定義行為容差，而不是要求逐位一致。

反例是壓縮後平均分數上升，但安全閾值附近的假陰性增加。單一平均值會判定成功，風險契約卻應拒絕。另一個反例是模型檔縮小但硬體不支援稀疏算子，延遲反而不變；理論壓縮率不能證明系統收益。

## 實務對比

錯誤做法是只在平衡測試集比較 top-1 accuracy。正確做法先保存逐樣本 logits，再檢查決策翻轉、校準 <!-- term:Calibration -->與風險切片，並在目標硬體實測。

另一個錯誤是把蒸餾 <!-- term:Distill -->稱為無損複製。正確對比包含教師、只學硬標籤的同容量學生，以及使用軟目標的學生。只有這樣才能區分容量限制、資料缺口與蒸餾 <!-- term:Distill -->訊號的效果。

## 結論

**模型壓縮**（Model Compression） <!-- term:ModelCompression -->是受資源約束的近似，不是單一機制。量化 <!-- term:Quantization -->改變數值格點，剪枝 <!-- term:Pruning -->移除計算方向，蒸餾 <!-- term:Distill -->以有限學生重估教師行為。保真度契約因此必須同時問：哪些個體翻轉、哪些切片受損、機率是否失準，以及真實硬體是否得到收益。平均準確率只能作起點，不能充當無損證明。

> [!IMPORTANT]
> **模型壓縮** <!-- term:ModelCompression --> (Model Compression): 以量化、剪枝或蒸餾等方式縮減模型資源需求的近似手段。 <!-- anchor:ModelCompression -->