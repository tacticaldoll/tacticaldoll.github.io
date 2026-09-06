+++
title = "卷積何時能把局部性換成樣本效率"
date = "2026-09-06T21:16:03+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "權重共享把平移結構寫進架構，用自由度換樣本效率。說明這項空間偏置何時降低樣本需求，又在何時刪掉任務需要的資訊。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "AI 代理人", # term:AiAgent
    "卷積神經網路", # term:ConvolutionalNeuralNetwork
    "平移等變性", # term:TranslationEquivariance
    "感受野", # term:ReceptiveField
    "結構偏置", # term:StructuralBias
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

一個邊緣偵測器若只在影像左側學到權重，邊緣移到右側時便可能失效。把同一組權重滑過所有位置後，反應會跟著圖樣移動。這不是資料自行發現了平移規律，而是架構先宣告「相同局部模式可在不同位置重用」。

**卷積神經網路**（Convolutional Neural Network） <!-- term:ConvolutionalNeuralNetwork -->的經典文件辨識系統把局部**感受野**（Receptive Field） <!-- term:ReceptiveField -->與共享權重用於手寫字辨識，並在完整文件管線中聯合辨識與其他模組。[LeCun 等人，1998](https://bottou.org/papers/lecun-98h) 這裡真正要問的是：這項空間偏置在什麼條件下降低樣本需求，又會在何時刪掉任務需要的自由度？

> [!IMPORTANT]
> **卷積神經網路** <!-- term:ConvolutionalNeuralNetwork --> (Convolutional Neural Network): 以局部連接與權重共享處理格狀資料的網路架構，把空間鄰近性寫進模型結構。 <!-- anchor:ConvolutionalNeuralNetwork -->
> **感受野** <!-- term:ReceptiveField --> (Receptive Field): 輸出單元實際可見的輸入區域範圍，隨層數與步幅累積擴張。 <!-- anchor:ReceptiveField -->


## 分析

### 從位置外失敗回推權重共享

一維交叉相關可寫成

$$
y_i=\sum_{k=0}^{K-1}w_kx_{i+k}+b.
$$

同一個 $w$ 用於每個 $i$。忽略邊界效應時，若 $T_\delta$ 表示平移 $\delta$，卷積算子 $C$ 滿足

$$
C(T_\delta x)=T_\delta C(x).
$$

這是**平移等變性**（Translation Equivariance） <!-- term:TranslationEquivariance -->：輸入變換後，特徵圖以對應方式變換。它不是平移不變性；只有後續聚合或讀出忽略位置時，最終決策才可能近似不變。

> [!IMPORTANT]
> **平移等變性** <!-- term:TranslationEquivariance --> (Translation Equivariance): 輸入平移時輸出隨之平移的性質，由卷積的權重共享自然產生。 <!-- anchor:TranslationEquivariance -->


從位置外失敗回推，可見一條三節點鏈：位置專屬參數只在出現過的位置收到梯度；未觀察位置的同類參數沒有被約束；模式平移後，讀出遇到未訓練權重而失效。共享權重把多個位置的證據合併到同一參數，降低了估計方差與參數數量。失效點則是任務若需要位置專屬規則，共享會把本應不同的函數強制綁在一起。

Cohen 與 Welling 將這個觀念推廣到群等變卷積，並以旋轉、反射等對稱增加共享；這項成果同時說明標準卷積只內建特定對稱，不會免費得到所有幾何不變性。[PMLR 論文](https://proceedings.mlr.press/v48/cohenc16)

### 感受野不是每個位置的等量影響

對 stride 1、無 dilation 的 $L$ 層寬度 $K$ 卷積，理論感受野 <!-- term:ReceptiveField -->是

$$
R_L=1+L(K-1).
$$

它只表示哪些輸入可能連到輸出。Luo 等人的分析顯示，有效感受野 <!-- term:ReceptiveField -->通常只占理論感受野 <!-- term:ReceptiveField -->的一部分，影響量還會集中於中央；深度、非線性、下採樣與跳接都會改變分布。[NeurIPS 論文](https://papers.nips.cc/paper/6203-understanding-the-effective-receptive-field-in-deep-convolutional-neural-networks.pdf)

因果鏈因此多一個中介：堆疊擴大拓撲可達範圍，但梯度路徑的數量與強度不均，使遠端位置實際影響較弱。只計算 $R_L$ 會把「可達」誤當成「已使用」。

### 隔離平移先驗的合成實驗

下列程式建立長度 12 的訊號。正類包含局部模板 `[1, -1, 1]`。訓練只在左半部出現模板，測試則移到右半部；共享偵測器與位置專屬偵測器使用相同閾值，只差是否跨位置共用權重。

```python
import numpy as np

template = np.array([1.0, -1.0, 1.0])

def trial(seed, position):
    rng = np.random.default_rng(seed)

    def make_sample(positive):
        x = rng.normal(0.0, 0.15, size=12)
        if positive:
            x[position:position + 3] += template
        return x

    def shared_score(x):
        return max(np.dot(x[i:i + 3], template) for i in range(10))

    def position_score(x):
        return np.dot(x[1:4], template)  # 只使用訓練位置

    rows = [(make_sample(bool(y)), y) for y in ([0, 1] * 200)]
    return [np.mean([(score(x) > 1.5) == y for x, y in rows])
            for score in (shared_score, position_score)]

for split, position in (("train", 1), ("shifted", 8)):
    runs = np.array([trial(seed, position) for seed in range(30)])
    for i, name in enumerate(("shared", "position")):
        print(split, name, runs[:, i].mean(), runs[:, i].std())
```

讀者應比較兩個模型從訓練位置移到新位置時的準確率落差。共享模型若保留表現，而位置模型跌到近似猜測，便支持「正確對稱可把證據跨位置合併」。若把標籤改為「模板只在左側才算正類」，共享加全域最大值反而會犯錯，這是同一偏置的直接反例。

### 框架對照：等變誤差與位置外落差

手寫版本用固定核心。下列程式改用可訓練的 `Conv1d` 與參數量相近的 `Linear`，並直接量測前文定義的 $E_{eq}=\lVert F(T_\tau x)-T_\tau F(x)\rVert_2$。

```python
import torch

torch.manual_seed(19)
x = torch.randn(64, 1, 12)
conv = torch.nn.Conv1d(1, 4, kernel_size=3, bias=False)
dense = torch.nn.Linear(12, 4 * 10, bias=False)

def equivariance_error(shifted, forward):
    a = forward(torch.roll(x, shifted, dims=-1))
    b = torch.roll(forward(x), shifted, dims=-1)
    return (a - b).flatten(1).norm(dim=1).mean().item()

for tau in (1, 3):
    print("conv  ", tau, equivariance_error(tau, lambda t: conv(t)))
    print("dense ", tau, equivariance_error(
        tau, lambda t: dense(t.flatten(1)).view(-1, 4, 10)))
```

`conv` 的誤差應只來自邊界（`roll` 是循環平移，卷積在邊界截斷），`dense` 則沒有理由保持等變。若兩者誤差相近，共享權重並未生效，此時不能把樣本效率歸因於**結構偏置**（Structural Bias） <!-- term:StructuralBias -->。撰稿環境未安裝 PyTorch，未執行此段。

> [!IMPORTANT]
> **結構偏置** <!-- term:StructuralBias --> (Structural Bias): 架構預先宣告的關係假設，用限制自由度換取樣本效率。 <!-- anchor:StructuralBias -->


### 驗證契約

為避免把一次隨機噪聲當成架構證據，實驗依下表固定。表後的解讀只限於平移先驗，不擴張到自然影像的所有變換。

| 項目 | 契約 |
| :--- | :--- |
| 資料 | 長度 12 高斯噪聲；正類加入固定三點模板 |
| 切分 | 訓練位置 1，位置外測試位置 8；正負類各 200 |
| seed | 0–29，各自重建完整資料 |
| 指標 | 訓練準確率、位置外準確率與落差 |
| 控制變因 | 模板、噪聲、閾值與樣本數固定，只改參數共享 |
| 觀察量 | 平移後的準確率保持率 |
| 反駁條件 | 共享模型在位置外沒有穩定優勢，或優勢只來自不同閾值 |
| 停止條件 | 30 個 seed 完成；不得事後挑選模板與閾值 |

如果反駁條件發生，不能以「CNN 理論上等變」掩蓋；必須檢查邊界 padding、讀出方式或資料生成是否破壞了假設。

## 反思

局部性不是普遍真理。若輸出取決於兩個相距很遠的位置，小核心需要深層傳遞才能**組合**（Compose） <!-- term:Compose -->它們；有限深度與集中的有效感受野 <!-- term:ReceptiveField -->可能形成瓶頸。全域關係任務是卷積局部偏置的反例，不是單純「資料不足」。

> [!IMPORTANT]
> **組合** <!-- term:Compose --> (Compose): 將多個獨立元件串聯運作的方式，強調資料流轉而非直接相依。 <!-- anchor:Compose -->


池化也不是免費的不變性。降低位置敏感度有利於分類，卻可能破壞關鍵點定位與細邊界分割。若目標要求精確座標，stride 與 pooling 造成的解析度損失需要跳接、多尺度特徵或位置精修補回。

此外，離散網格、padding 和 stride 會破壞嚴格等變性。標準卷積對平移的理論關係必須連同邊界條件陳述，不能直接推成旋轉、縮放或視角變化下的穩健性。

## 實務對比

錯誤做法是因影像任務便預設所有位置共享同一規則。醫學影像中的器官位置、道路場景中的地平線，可能讓絕對位置本身具有預測價值。強制全域共享會丟掉這個訊號。

較可靠的做法先做變換測試：保持語意不變，只平移、旋轉或縮放輸入，再測輸出應該等變還是不變。若只有平移應共享，就使用標準卷積；若旋轉也應共享，需資料增強或相符的群等變結構，並用未見角度驗證。

另一個錯誤是以理論感受野 <!-- term:ReceptiveField -->覆蓋整張影像，便宣稱網路使用了全域資訊。正確對照會測輸入梯度、遮蔽敏感度或干預遠端區域，確認遠端像素是否實際改變決策。

## 結論

卷積的樣本效率來自一個可檢查的交換：把位置專屬自由度換成跨位置共享的證據。當資料機制具有局部、可平移重用的規律，這項限制會提高估計效率；當標籤依賴絕對位置、遠距關係或其他變換，它也可能成為錯誤來源。

因此，評估 CNN 應明確回答三個問題：任務具備哪種對稱，輸出需要等變還是不變，以及理論可達範圍是否真的承載影響。結構偏置 <!-- term:StructuralBias -->提供的是可學習捷徑，不是無條件能力。