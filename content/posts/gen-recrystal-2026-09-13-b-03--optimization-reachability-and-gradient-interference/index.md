+++
title = "最佳化可達性與動態梯度干涉：長程信用退化、鞍點阻斷與負向遷移正交化"
date = "2026-09-13T17:30:03+08:00"
author = "梅乾"
draft = false
isCJKLanguage = true
description = "假設空間裝得下目標函數，不代表梯度下降走得到。本文分離表達容量與最佳化可達性，推導時間展開的雅可比譜半徑衰減如何切斷長程信用分配，剖析多任務共享參數上的負向內積干涉，並以動態等距約束與 PCGrad 切空間正交投影建立可執行的防線。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "機器學習", # term:MachineLearning
    "梯度干涉", # term:GradientInterference
    "信用分配", # term:CreditAssignment
    "假設空間", # term:HypothesisSpace
    "鞍點", # term:SaddlePoint
    "災難性遺忘", # term:CatastrophicForgetting
    "多任務學習", # term:MultiTaskLearning
  ]
series = ["能力失效歸因：模型評估盲區、幾何失真與因果邊界的工程重建"]
[ai_info]
    [ai_info.generation]
        model = "Gemini 3.8 Flash"
        agent = "Antigravity IDE 2.5.5"
    [ai_info.refinement]
        model = "Claude Opus 5"
        agent = "Claude Code VSCode Extension 2.1.270"
+++

<!--more-->

## 導言

在一個複雜邏輯推論模型的開發過程中，演算法團隊遭遇了難以解釋的訓練停滯。任務要求模型在多個邏輯實體之間執行三步以上的符號關聯推理。根據神經網路架構診斷報告，工程師認為四層 Transformer 模組的「參數容量不足」，遂將模型深度從四層劇烈擴展至十二層，參數量翻了整整三倍。然而，擴容後的模型訓練損失曲線在初始下降後便徹底陷入水平鈍化，其在驗證集上的準確率甚至顯著落後於原本的四層輕量版本。儘管通用逼近定理在數學上證明了十二層網路的**假設空間**（Hypothesis Space） <!-- term:HypothesisSpace -->絕對包含目標推理函數，但基於**隨機梯度下降**（SGD） <!-- term:StochasticGradientDescent -->的局部搜尋演算法在非凸曲面上根本無法尋得通往該全域最優解的導引路徑。**「能夠表達（Expressible）」並不等同於「在最佳化上可達（Optimization Reachable）」**。

> [!IMPORTANT]
> **假設空間** <!-- term:HypothesisSpace --> (Hypothesis Space): 學習演算法可選函數所構成的集合，其大小決定泛化保證的鬆緊。 <!-- anchor:HypothesisSpace -->
> **隨機梯度下降** <!-- term:StochasticGradientDescent --> (Stochastic Gradient Descent): 以小批次樣本估計梯度並更新參數的最佳化演算法，其搜尋是局部的，不保證抵達全域最優。 <!-- anchor:StochasticGradientDescent -->


與此同時，另一套處理長文本序列對齊的模型展現了時間維度上的**信用分配**（Credit Assignment） <!-- term:CreditAssignment -->死局。該序列模型被要求在第 200 步輸出一個關鍵程式碼標記，而決策依據取決於第 3 步輸入的一個前綴參數。任務結構本身極為清晰，但無論如何調整學習率或更換最佳化器，模型在**反向傳播**（Backpropagation） <!-- term:Backpropagation -->時皆無法建立跨越 197 個時間步的依賴連結。展開後的**計算圖**（Unrolled Computational Graph） <!-- term:ComputationalGraph -->在進行鏈式求導時，雅可比矩陣乘積的譜半徑小於一，導致誤差信號在逆流過程中發生指數級湮滅；第 3 步的權重根本接收不到來自第 200 步的有效梯度，跨時間的信用分配 <!-- term:CreditAssignment -->徹底中斷。

> [!IMPORTANT]
> **信用分配** <!-- term:CreditAssignment --> (Credit Assignment): 判定某個結果應歸因於哪些參數或決策步驟的問題。 <!-- anchor:CreditAssignment -->
> **反向傳播** <!-- term:Backpropagation --> (Backpropagation): 以連鎖律沿計算圖回傳誤差，有效求得各層參數梯度的演算法。 <!-- anchor:Backpropagation -->
> **計算圖** <!-- term:ComputationalGraph --> (Computational Graph): 把前向運算展開成節點與邊的表示，反向傳播沿其反向鏈式求導。 <!-- anchor:ComputationalGraph -->


更嚴重的工程失控發生在多任務微調（Multi-Task Fine-Tuning）管線中。團隊在已收斂的核心通用模型上微調一個新增的領域問答任務。新任務的指標在數個週期內迅速達標，但回歸測試套件卻發出紅色警報：模型在原始核心任務上的準確率暴跌了 20 個百分點。值班工程師直覺地採取暴力對策，將兩個任務的**損失函數**（Loss Function） <!-- term:LossFunction -->進行簡單的標量加權 $\mathcal{L}_{\text{total}} = \mathcal{L}_{\text{core}} + \lambda \mathcal{L}_{\text{new}}$ 並嘗試搜尋最佳權重 $\lambda$。然而，進一步的梯度幾何分析表明：兩個任務在共享參數子空間上的梯度向量內積持續為負（$\langle g_{\text{core}}, g_{\text{new}} \rangle < 0$）。沿著複合梯度更新參數，本質上是在物理維度上強行擦除核心任務已經構築的參數吸引子。

> [!IMPORTANT]
> **損失函數** <!-- term:LossFunction --> (Loss Function): 把模型輸出與目標之間的差距量化為單一數值的評分函數。 <!-- anchor:LossFunction -->


這些事故揭示了深度學習工程中一個被廣泛忽視的本質：**最佳化動力學（Optimization Dynamics） <!-- term:OptimizationDynamics -->是獨立於架構容量的物理規律約束**。當梯度流在時間軸上消亡或在任務空間中相互廝殺時，盲目擴增網路容量只會加速系統崩潰。

> [!IMPORTANT]
> **最佳化動力學** <!-- term:OptimizationDynamics --> (Optimization Dynamics): 參數在損失景觀上隨更新規則演化的過程，是獨立於架構容量之外的物理約束。 <!-- anchor:OptimizationDynamics -->


---

## 分析

神經網路訓練本質上是高維非凸景觀上的受限動力學系統。設模型參數為 $\theta \in \mathbb{R}^P$，假設空間 <!-- term:HypothesisSpace -->為 $\mathcal{H} = \{f_\theta \mid \theta \in \mathbb{R}^P\}$。目標風險為 $R(\theta) = \mathbb{E}[\ell(f_\theta(x), y)]$。通用逼近定理僅保證：

$$\inf_{f \in \mathcal{H}} R(f) \le \epsilon$$

但並未保證一階最佳化器軌跡 $\theta_{t+1} = \theta_t - \eta g_t$ 能夠收斂至具有**泛化**（Generalization） <!-- term:Generalization -->能力的流形區域。

> [!IMPORTANT]
> **泛化** <!-- term:Generalization --> (Generalization): 模型在訓練樣本以外的資料上維持表現的能力。 <!-- anchor:Generalization -->


```mermaid
flowchart TD
    subgraph LossLandscape["非凸損失景觀物理障礙"]
        Hessian["Hessian 矩陣病態條件數<br/>lambda_max / lambda_min >> 10^4"]
        Saddle["高維退化鞍點<br/>負特徵值吸引逃逸阻斷"]
    end

    subgraph TemporalChain["時間軸展開鏈式衰減"]
        Jac["循環求導雅可比矩陣鏈<br/>J_prod = ∏_{k=1}^T J_k"]
        SpecDecay["譜半徑衰減 rho(J) < 1<br/>長程梯度指數級湮滅"]
    end

    subgraph TaskClash["多任務切空間衝突"]
        DotNeg["負向梯度內積<br/>< g_core, g_new > < 0"]
        Destructive["破壞性干涉<br/>舊特徵子空間被覆寫"]
    end

    Hessian & Saddle --> Unreachable["假設空間存得住<br/>但最佳化路徑不可達"]
    Jac --> SpecDecay --> TemporalDeath["長程信用分配斷裂<br/>50 步之外梯度歸零"]
    DotNeg --> Destructive --> Catastrophic["災難性負遷移<br/>核心任務性能暴跌"]
```

上圖清晰梳理了三條導致最佳化破滅的動力學機制。在實務中，其數學本質可分別由以下原理精確刻劃：

### 1. 雅可比譜半徑與跨時間信用分配坍塌

在時間軸展開序列模型中，狀態轉移方程為 $h_t = \sigma(W_{hh} h_{t-1} + W_{xh} x_t)$。總損失相對於早期狀態 $h_0$ 的偏導數遵循鏈式法則：

$$\frac{\partial \mathcal{L}}{\partial h_0} = \frac{\partial \mathcal{L}}{\partial h_T} \prod_{t=1}^T \frac{\partial h_t}{\partial h_{t-1}} = \frac{\partial \mathcal{L}}{\partial h_T} \prod_{t=1}^T J_t$$

正如 [Pascanu 等人，2013 / 《On the difficulty of training recurrent neural networks》](https://proceedings.mlr.press/v28/pascanu13.html) 的開創性研究所證明的，若轉移雅可比矩陣 $J_t$ 的最大奇異值（或譜半徑 $\rho(J)$）在大部分區域滿足 $\rho(J) < 1$，則：

$$\left\| \frac{\partial \mathcal{L}}{\partial h_0} \right\| \le \left\| \frac{\partial \mathcal{L}}{\partial h_T} \right\| \prod_{t=1}^T \|J_t\| \le c \cdot \gamma^T \quad (\gamma < 1)$$

當序列長度 $T = 200$ 且 $\gamma = 0.95$ 時，傳播至起點的梯度模長將衰減至原值的 $3.5 \times 10^{-5}$。此時梯度信號完全被數值浮點噪聲掩埋，神經網路在物理上喪失了辨識時間因果的能力。

### 2. 多任務梯度干涉與切空間正交投影 (PCGrad)

當多個任務共享同一組網路主幹參數 $\theta$ 時，任務 $i$ 與任務 $j$ 各自產生的更新方向分別為 $g_i = \nabla_\theta \mathcal{L}_i$ 與 $g_j = \nabla_\theta \mathcal{L}_j$。兩者的餘弦相似度定義為：

$$\cos(\phi_{ij}) = \frac{\langle g_i, g_j \rangle}{\|g_i\| \|g_j\|}$$

當 $\cos(\phi_{ij}) < 0$ 時，表明沿著 $g_j$ 的更新步伐將嚴格增加任務 $i$ 的損失值：

$$\mathcal{L}_i(\theta - \eta g_j) \approx \mathcal{L}_i(\theta) - \eta \langle \nabla_\theta \mathcal{L}_i, g_j \rangle = \mathcal{L}_i(\theta) - \eta \langle g_i, g_j \rangle > \mathcal{L}_i(\theta)$$

[Yu 等人，2020 / 《Gradient Surgery for Multi-Task Learning: Cross-Gradient Projection》](https://proceedings.neurips.cc/paper/2020/hash/3fe78a8ac530e0ab59720b2d600377e4-Abstract.html) 提出了投影正交化手術（PCGrad）。其核心思想是在偵測到衝突時，將 $g_i$ 投影到 $g_j$ 的正交切平面上：

$$g_i^* = g_i - \frac{\langle g_i, g_j \rangle}{\|g_j\|^2} g_j \quad (\text{if } \langle g_i, g_j \rangle < 0)$$

經過投影後，$\langle g_i^*, g_j \rangle = 0$。此項變換嚴格保證了在更新任務 $i$ 時不會破壞任務 $j$ 的已有幾何結構，消除毀滅性負遷移。

為展示干涉偵測與正交化手術的因果演進，下表呈現了狀態轉移走一遍的詳細推演：

| 迭代步驟 | 任務 A 梯度向量 $g_A$ | 任務 B 梯度向量 $g_B$ | 梯度內積 $\langle g_A, g_B \rangle$ | 系統衝突狀態 | 投影手術處置 (PCGrad) | 修正後更新方向 $g^*$ | 系統狀態與效能收斂 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Step 01** | $[1.0, 2.0, 0.5]$ | $[1.2, 1.8, 0.4]$ | $+5.00$ ($\cos \approx 0.98$) | 諧振協同 | 無需介入，直接相加 | $g = g_A + g_B$ | 兩任務同向收斂 |
| **Step 02** | $[1.0, -2.0, 0.5]$ | $[-2.0, 1.0, 0.2]$ | **$-3.90$** ($\cos \approx -0.87$) | **破壞性干涉** | 啟動正交投影手術 | $g_A^* = g_A - \frac{\langle g_A, g_B \rangle}{\|g_B\|^2} g_B$ | 阻斷任務 A 對任務 B 的負向侵蝕 |
| **Step 03** | 投影後向量 | 原始反向向量 | **$0.00$** ($\cos = 0.00$) | **嚴格正交** | 沿切平面更新 | 兩任務損失同時單調不增 | 帕累托最優邊界得以保持 |
| **反例：暴力加權** | 忽略負內積，強制執行 $g_{\text{naive}} = g_A + 2.0 g_B = [-3.0, 0.0, 0.9]$ | **持續侵蝕** | 任務 B 強行覆寫參數空間 | 任務 A 準確率暴跌 $20\%$ | **災難性遺忘**（Catastrophic Forgetting） <!-- term:CatastrophicForgetting -->發生 |

> [!IMPORTANT]
> **災難性遺忘** <!-- term:CatastrophicForgetting --> (Catastrophic Forgetting): 針對新任務更新參數後，先前任務表現急劇下降的現象。 <!-- anchor:CatastrophicForgetting -->


下表進一步對比傳統最佳化迷思與基於動力學的第一性原理工程防衛：

| 診斷維度 | 表面現象與觀測指標 | 底層動力學病灶 | 舊代脆弱反射做法 | 新代嚴格工程防衛 |
| :--- | :--- | :--- | :--- | :--- |
| **損失曲線鈍化** | 網路加深至十二層後，訓練損失停滯，驗證集表現倒退。 | Hessian 矩陣病態**條件數**（Condition Number） <!-- term:ConditionNumber -->與高維退化**鞍點**（Saddle Point） <!-- term:SaddlePoint -->阻斷了一階梯度的有效導航。 | 盲目進一步擴容網路，或調大學習率。 | **殘差跳躍與動態等距初始化**：強制限制 Jacobian 譜半徑接近 1.0，確保可達路徑。 |
| **長程記憶消失** | 序列模型在間隔 100 步以上無法傳遞資訊，注意力權重發散。 | 時間展開乘積鏈中的雅可比譜半徑 $\rho(J) < 1$，梯度指數級消亡。 | 增加模型寬度或堆疊密集全連接層。 | **梯度流門控結構（Gated Flow）與跨時間跳躍連結**：維持跨時間步的高速無阻通道。 |
| **多任務負遷移** | 微調新任務達標，但原有核心能力遭遇斷崖式崩潰。 | 共享參數空間上多任務梯度內積為負，更新方向直接抹除舊特徵。 | 人工手動微調損失加權係數 $\lambda$。 | **梯度手術（PCGrad） <!-- term:GradientSurgery -->與**模組化參數隔離**（LoRA/Adapters） <!-- term:ModularParameterIsolation -->**：切空間投影正交化，徹底隔離更新基底。 |

> [!IMPORTANT]
> **條件數** <!-- term:ConditionNumber --> (Condition Number): 損失曲面各方向曲率的比值，決定固定學習率下梯度下降的收斂速度。 <!-- anchor:ConditionNumber -->
> **鞍點** <!-- term:SaddlePoint --> (Saddle Point): 梯度為零但 Hessian 同時具備正負特徵值的臨界點，在高維非凸景觀中遠多於局部極小值。 <!-- anchor:SaddlePoint -->
> **梯度手術** <!-- term:GradientSurgery --> (Gradient Surgery): 偵測任務梯度之間的負向內積，並把衝突分量投影到正交切空間的更新修正法，PCGrad 為其代表。 <!-- anchor:GradientSurgery -->
> **模組化參數隔離** <!-- term:ModularParameterIsolation --> (Modular Parameter Isolation): 以 LoRA、Adapter 等旁路模組承載新任務更新，使核心權重不被覆寫的架構隔離手段。 <!-- anchor:ModularParameterIsolation -->


---

## 反思

最佳化動力學 <!-- term:OptimizationDynamics -->防線的深層張力，體現在**「共享表徵的泛化 <!-- term:Generalization -->紅利」**與**「參數干涉的穩定性風險」**之間的經典權衡。

**多任務學習**（Multi-Task Learning） <!-- term:MultiTaskLearning -->的核心初衷，是希望不同任務在共享的主幹網路中互相汲取歸納偏置（Inductive Bias），以更少的樣本學得更具通用性的表徵。然而，當兩個任務在特徵需求上並非完全對齊時（例如一個任務需要高度不變性抽象，另一個任務需要細粒度局部邊緣），參數空間的幾何吸引子必然產生拓撲排斥。

> [!IMPORTANT]
> **多任務學習** <!-- term:MultiTaskLearning --> (Multi-Task Learning): 多個目標共享同一組參數進行訓練的範式，其收益取決於各任務梯度在共享子空間中是否相容。 <!-- anchor:MultiTaskLearning -->


如果為了絕對避免干涉而走向極端——對每個任務完全隔離權重（例如各自訓練獨立模型），則會徹底喪失參數共享帶來的推論能耗節省與跨任務知識遷移紅利。反之，如果過度迷信單一萬能大模型，將所有正交目標強行壓縮進同一個不可拆分的密集矩陣中，最佳化器在梯度反向傳播 <!-- term:Backpropagation -->時便會淪為多方拉扯的震盪系統。

因此，最佳化治理的實質不是消滅衝突，而是**在編譯期與執行期顯式監控梯度幾何關係**，並在衝突不可調和時提供優雅降級的架構隔離機制。

---

## 實務對比

為具體防禦多任務訓練中的破壞性干涉並確保長程梯度傳播，以下透過 Rust 實作嚴格的幾何**不變式**（Invariant） <!-- term:Invariant -->檢驗程式碼。錯誤做法盲目執行加權向量合成，而正確做法實作了雅可比譜半徑衰減監控與 PCGrad 梯度切空間正交化。

> [!IMPORTANT]
> **不變式** <!-- term:Invariant --> (Invariant): 系統在任何合法狀態下都必須成立的斷言，是把評估規則寫成可執行檢查的基本單位。 <!-- anchor:Invariant -->


```rust
// 梯度計算與動態干涉正交化模組 (PCGrad & Optimization Invariants)

fn dot_product(a: &[f64], b: &[f64]) -> f64 {
    assert_eq!(a.len(), b.len(), "Dimension mismatch in dot product");
    a.iter().zip(b.iter()).map(|(x, y)| x * y).sum()
}

fn norm_squared(a: &[f64]) -> f64 {
    dot_product(a, a)
}

// 錯誤做法：盲目加權求和，完全忽略負向內積引發的破壞性特徵覆寫
pub fn naive_gradient_merge(g1: &[f64], g2: &[f64], weight: f64) -> Vec<f64> {
    g1.iter().zip(g2.iter()).map(|(x, y)| x + weight * y).collect()
}

// 正確做法：實作 PCGrad 切空間正交化，將衝突梯度投影至彼此的法平面
pub fn pcgrad_project(g1: &[f64], g2: &[f64]) -> (Vec<f64>, Vec<f64>) {
    assert_eq!(g1.len(), g2.len(), "Dimension mismatch in PCGrad");
    let mut g1_star = g1.to_vec();
    let mut g2_star = g2.to_vec();

    let dot = dot_product(g1, g2);

    // 衝突偵測不變式：僅在梯度方向夾角大於 90 度 (內積為負) 時介入手術
    if dot < 0.0 {
        let n2_sq = norm_squared(g2);
        if n2_sq > 1e-12 {
            let scale1 = dot / n2_sq;
            for i in 0..g1.len() {
                g1_star[i] -= scale1 * g2[i];
            }
        }

        let n1_sq = norm_squared(g1);
        if n1_sq > 1e-12 {
            let scale2 = dot / n1_sq;
            for i in 0..g2.len() {
                g2_star[i] -= scale2 * g1[i];
            }
        }
    }

    (g1_star, g2_star)
}

// 時間展開雅可比譜半徑衰減模擬
pub fn verify_temporal_gradient_decay(
    initial_grad: f64,
    spectral_radius: f64,
    steps: usize,
) -> f64 {
    let mut grad = initial_grad;
    for _ in 0..steps {
        grad *= spectral_radius;
    }
    grad
}

fn main() {
    // 1. 驗證時間展開長程信用衰減
    let init_norm = 1.0;
    let rho = 0.95; // 雅可比譜半徑小於 1.0
    let horizon = 200;
    let final_grad = verify_temporal_gradient_decay(init_norm, rho, horizon);

    println!("[Temporal Credit Check] Steps: {}, Initial: {:.2}, Final: {:.6e}", horizon, init_norm, final_grad);
    // 斷言：200 步後梯度必然衰減至小於 1e-4，驗證跨時間信用分配斷裂
    assert!(final_grad < 1e-4, "Invariant failure: gradient should vanish under sub-unitary spectral radius");

    // 2. 驗證多任務梯度破壞性干涉
    // 任務 1 (核心任務) 與任務 2 (微調任務) 的梯度向量
    let g_core = vec![1.0, -2.0, 0.5];
    let g_new = vec![-2.0, 1.0, 0.2];

    let initial_dot = dot_product(&g_core, &g_new);
    println!("[Interference Check] Initial Gradient Inner Product: {:.2}", initial_dot);
    
    // 斷言：初始狀態必須為破壞性衝突 (< 0)
    assert!(initial_dot < 0.0, "Setup failure: initial vectors should be in conflict");

    // 脆弱做法結果
    let naive_update = naive_gradient_merge(&g_core, &g_new, 1.0);
    let erosion = dot_product(&naive_update, &g_core);
    println!("[Naive Update] Inner product with g_core: {:.2} (Erosion occurred)", erosion);

    // 嚴格工程做法：啟動 PCGrad 正交手術
    let (g_core_star, g_new_star) = pcgrad_project(&g_core, &g_new);
    let post_dot_1 = dot_product(&g_core_star, &g_new);
    let post_dot_2 = dot_product(&g_new_star, &g_core);

    println!("[PCGrad Update] Projected g_core* dot g_new: {:.6e}", post_dot_1);
    println!("[PCGrad Update] Projected g_new* dot g_core: {:.6e}", post_dot_2);

    // 斷言不變式：投影後的修正梯度向量，與對立任務的內積必須收斂至正交 (零或極微小數值)
    assert!(post_dot_1.abs() < 1e-9, "PCGrad invariant failure: g_core_star must be orthogonal to g_new");
    assert!(post_dot_2.abs() < 1e-9, "PCGrad invariant failure: g_new_star must be orthogonal to g_core");

    println!("All Rust Optimization and PCGrad Verification Invariants Successfully Passed.");
}
```

此段 Rust 程式碼展現了零成本抽象（Zero-cost Abstractions）在模型治理中的威力。透過強型別切片操作與編譯期確定的邊界檢查，它將高維梯度衝突的幾何檢查直接落實為毫秒級執行的常規斷言，在多任務更新合流前建立起不可動搖的切空間**正交性**（Orthogonality） <!-- term:Orthogonality -->防線。

> [!IMPORTANT]
> **正交性** <!-- term:Orthogonality --> (Orthogonality): 兩個設計維度或系統特質之間互不干涉、獨立運作的結構關係。 <!-- anchor:Orthogonality -->


---

## 結論

在深度學習的工程構建中，不能將最佳化過程視為一個可以無窮透支的黑盒求解器。模型在假設空間 <!-- term:HypothesisSpace -->上的理論存在性，無法代替**梯度下降**（Gradient Descent） <!-- term:GradientDescent -->在非凸景觀上的可達性；時間展開求導中的雅可比譜半徑衰減，直接決定了模型信用分配 <!-- term:CreditAssignment -->的物理長度；而多任務共享參數空間中的負內積干涉，則是引發災難性遺忘 <!-- term:CatastrophicForgetting -->的直接力學源頭。

> [!IMPORTANT]
> **梯度下降** <!-- term:GradientDescent --> (Gradient Descent): 沿損失函數負梯度方向反覆更新參數的最佳化方法。 <!-- anchor:GradientDescent -->


成熟的工程實踐必須將「最佳化動力學 <!-- term:OptimizationDynamics -->的可達性審查」置於「網路架構擴展」之前。在跨時間架構中，必須嚴格維持轉移矩陣的動態等距性以抵禦梯度消亡；在多任務與微調管線中，則必須引入幾何干涉偵測與 PCGrad 正交化投影。唯有當梯度流被約束於無衝突的切空間之內，高維系統的能力積累才不再是一場相互毀滅的零和博弈。