+++
title = "遞迴狀態何時能保留可學習的歷史"
date = "2026-09-06T21:16:04+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "同一個連乘同時牽動前向記憶與反向梯度。分離狀態是否仍受歷史影響、與誤差是否教得動早期轉移這兩個不同問題。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "AI 代理人", # term:AiAgent
    "遞迴式神經網路", # term:RecurrentNeuralNetwork
    "長短期記憶網路", # term:LongShortTermMemory
    "實務對比", # term:PracticalContrastiveExamples
    "反向傳播", # term:Backpropagation
    "信用分配", # term:CreditAssignment
    "形狀", # term:DataShape
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

把一個數值反覆乘以 $0.8$ 五十次，早期輸入的影響只剩約 $1.4\times10^{-5}$；改乘 $1.2$，影響則超過九千。這個標量事故常被拿來描述遞迴網路的記憶，但它其實同時打開兩個問題：歷史是否仍影響目前狀態，以及誤差是否能反向教會早期轉移。

遞迴神經網路（recurrent neural network, RNN）以共享狀態轉移處理可變長度序列。這裡真正要問的是：前向資訊與反向梯度經過什麼機制保留，門控又在哪些條件下只提供通道而沒有提供記憶保證？

## 分析

### 同一個連乘，兩種不同診斷

最小 RNN 為

$$
h_t=\tanh(W_hh_{t-1}+W_xx_t+b),
\qquad \hat y_t=W_yh_t.
$$

早期狀態對晚期狀態的敏感度包含 Jacobian 連乘

$$
\frac{\partial h_T}{\partial h_k}
=\prod_{t=k+1}^{T}J_t,
\qquad
J_t=\frac{\partial h_t}{\partial h_{t-1}}.
$$

從長程任務學不到的症狀回推，因果鏈是：同一轉移沿時間重複；每個 $J_t$ 對不同方向伸縮；乘積讓部分方向指數衰減或增長；早期事件收到不可辨識或不穩定的學習訊號。失效點是只看狀態值尚未消失，就推論參數仍能從遠端誤差學習。

Pascanu、Mikolov 與 Bengio 從解析、幾何與動力系統角度研究消失及爆炸梯度，並以梯度裁剪處理爆炸情形。[PMLR 論文](https://proceedings.mlr.press/v28/pascanu13.html) 裁剪限制更新幅度，卻不會恢復已衰減到零的方向。

### 門控建立加法高速路

**長短期記憶網路**（Long Short-Term Memory） <!-- term:LongShortTermMemory -->的簡化單元狀態是

> [!IMPORTANT]
> **長短期記憶網路** <!-- term:LongShortTermMemory --> (Long Short-Term Memory): 以門控結構調節資訊與梯度路徑的遞迴網路變體。 <!-- anchor:LongShortTermMemory -->


$$
c_t=f_t\odot c_{t-1}+i_t\odot\tilde c_t.
$$

$f_t$ 控制保留，$i_t$ 控制寫入。若忽略門本身對狀態的間接依賴，沿直接路徑有

$$
\frac{\partial c_T}{\partial c_k}
\approx\prod_{t=k+1}^{T} f_t.
$$

這個式子沒有取消連乘，而是讓模型學習一條接近 1 的加法路徑。Hochreiter 與 Schmidhuber提出 LSTM 的直接動機正是長時間間隔下不足、衰減的誤差回流。[Neural Computation 論文](https://doi.org/10.1162/neco.1997.9.8.1735)

下圖分開前向保存與反向可訓練性。這個分離能避免把「狀態裡還有訊號」與「模型能學會使用訊號」混成同一件事。

```mermaid
flowchart LR
    X["早期輸入 xₖ"] --> S["寫入狀態 cₖ"]
    S -->|"忘記門連乘"| T["晚期狀態 c_T"]
    T --> Y["任務輸出"]
    Y --> E["遠端誤差"]
    E -->|"反向 Jacobian 路徑"| U["早期轉移的梯度"]
    U --> P["參數更新"]
```

前向邊斷裂會讓早期內容不可辨識；反向邊斷裂則讓目前參數無法從失敗中修正。兩者相關但不等價。

### 隔離狀態與梯度的實驗

下列 NumPy 程式同時計算普通標量遞迴與固定忘記門的影響。操弄變因是轉移尺度或門值，觀察量是不同距離的敏感度。

```python
import numpy as np

distances = np.array([10, 20, 50])

def influence(scale):
    return scale ** distances

for scale in (0.8, 0.99, 1.0, 1.2):
    print("plain", scale, influence(scale))

for forget_gate in (0.8, 0.99, 1.0):
    direct_path = influence(forget_gate)
    print("gated", forget_gate, direct_path)
```

應觀察 0.99 並非「永久記憶」：距離增加仍會衰減，只是時間常數更長。1.0 保留直接路徑，但若輸出損失從不依賴該內容，模型仍沒有寫入或讀出的訓練理由。此實驗支持乘積機制，不足以證明矩陣 RNN 的所有方向具有相同尺度。

### 框架對照：把純量連乘換成真實 Jacobian

純量模型只說明乘積**形狀**（Data Shape） <!-- term:DataShape -->。下列程式用 autograd 直接取 $\partial h_T/\partial h_k$ 的範數，並讓 `RNN` 與 `LSTM` 在相同隱藏維度下比較。

> [!IMPORTANT]
> **形狀** <!-- term:DataShape --> (Data Shape): 資料結構或物件所包含的屬性與型別定義，通常由型別系統來描述 <!-- anchor:DataShape -->


```python
import torch

def sensitivity(cell, length, hidden=32, seed=0):
    torch.manual_seed(seed)
    x = torch.randn(1, length, hidden, requires_grad=True)
    out, _ = cell(x)
    out[:, -1].sum().backward()
    return x.grad[0].norm(dim=1)  # 每個時間步對末端的影響

for name, cell in (("rnn", torch.nn.RNN(32, 32, batch_first=True)),
                   ("lstm", torch.nn.LSTM(32, 32, batch_first=True))):
    g = sensitivity(cell, 60)
    print(name, "t=59", g[-1].item(), "t=30", g[30].item(), "t=0", g[0].item())
```

觀察量是同一條曲線的兩端比值，而不是單一梯度範數。若 `lstm` 在 $t=0$ 的敏感度顯著高於 `rnn`，支持加法路徑延長了可學習距離；若兩者同樣衰減，門控在這個初始化下沒有生效，長程失敗就要另找原因。未初始化訓練的網路只反映初始化，不代表訓練後行為。本段未在撰稿環境執行。

### 驗證契約

要檢查長程能力，序列任務必須把距離當成獨立變因。若只報混合長度平均，短序列可能掩蓋遠端失效。

| 項目 | 契約 |
| :--- | :--- |
| 資料 | 合成 copy 任務；第一個符號在延遲後要求重現，干擾符號獨立均勻抽樣 |
| 切分 | 訓練延遲 5–20；插值測試 5–20；外推測試 30、50 |
| seed | 初始化與資料 seed 0–9 全部報告 |
| 指標 | 各延遲準確率、$\|\partial h_T/\partial h_1\|$、梯度範數 |
| 控制變因 | 隱藏維度、資料量、最佳化器、步數固定；只改普通 RNN 與門控 |
| 觀察量 | 準確率與敏感度隨延遲的衰減曲線 |
| 反駁條件 | 門控在相同參數與訓練預算下未延長有效距離，或效果無法跨 seed 重現 |
| 停止條件 | 預定步數完成或驗證損失 20 次評估無改善；不得用外推集早停 |

這份契約能判斷門控是否在指定任務延長可學習距離。它不能把 copy 任務的成功外推成人類式記憶或開放世界推理。

## 反思

第一個反例是正交或單位尺度的遞迴。連乘不必然消失；適當譜結構可以保留範數。然而保留所有方向也可能讓無關歷史持續干擾，穩定梯度不是選擇性記憶的充分條件。

第二個邊界是截斷時間**反向傳播**（Backpropagation） <!-- term:Backpropagation -->。即使前向狀態跨越很久，訓練若每 20 步截斷，超過窗口的**信用分配**（Credit Assignment） <!-- term:CreditAssignment -->路徑便被人工切斷。模型可能透過局部代理訊號學到某些長程行為，但不能把它當成完整遠端梯度的證據。

> [!IMPORTANT]
> **反向傳播** <!-- term:Backpropagation --> (Backpropagation): 以連鎖律沿計算圖回傳誤差，有效求得各層參數梯度的演算法。 <!-- anchor:Backpropagation -->
> **信用分配** <!-- term:CreditAssignment --> (Credit Assignment): 判定某個結果應歸因於哪些參數或決策步驟的問題。 <!-- anchor:CreditAssignment -->


第三個邊界是目標函數。若損失不獎勵保存某項資訊，門控最合理的行為可能正是遺忘。這不是故障，而是架構能力與任務要求不匹配時的可預期結果。

## 實務對比

錯誤說法是「RNN 每讀一個 token 就更新參數」。推論時更新的是樣本狀態；共享參數通常在反向傳播 <!-- term:Backpropagation -->與最佳化步驟才改變。混淆兩者會把上下文遺失錯診成線上學習覆寫。

另一個錯誤是看到梯度爆炸便只把學習率調小。較完整的做法同時記錄時間距離、Jacobian 或梯度範數，並比較裁剪前後。裁剪若只阻止非有限更新而未改善長距離準確率，爆炸只是被控制，消失或信用分配 <!-- term:CreditAssignment -->問題仍在。

可靠實作還會把普通 RNN、門控 RNN 與簡單的固定窗口基線放在同一資料預算下。若固定窗口已足以解題，就不能把門控勝任歸因於長期狀態。

## 結論

遞迴狀態的「記憶」需要兩條路都成立：歷史必須在前向狀態中保持可辨識，遠端誤差也必須在反向路徑中提供可學習訊號。LSTM 的門控重塑這兩條路，卻不保證內容會被寫入、保留或使用。

因此，長程能力應以距離分層的行為、狀態敏感度與梯度量測共同驗證。只看一個末端準確率，無法區分保存失敗、訓練失敗與目標根本沒有要求保存。