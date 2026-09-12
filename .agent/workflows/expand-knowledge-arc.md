---
name: expand-knowledge-arc
description: 作為重新結晶的上游展開階段。突破既有篇章框架限制，萃取議題、精神與客觀知識並過濾不可靠引用；自由進行深化、合併、拆分以重構最佳敘事弧，並系統化規劃流程圖、可執行程式碼與數學公式輔助表達。
argument-hint: "[target-path-or-series] [--dry-run]"
user-invokable: true
schema: []
spec: "../reference/agent-operating-guideline.md"
---

# 知識展開與敘事重構 (Knowledge Arc Expansion & Narrative Reframing)

本工作流是「重新結晶（Re-crystallization）」的**上游認知展開工序**。當既有貼文、粗糙草稿或歷史對話具備高度洞察與批判精神，但內文存在不可靠引用、鬆散數字、AI 生成痕跡或僵化的章節切割時，本工作流負責進行**去污染解構**、**第一性原理重鑄**與**自由敘事弧重構**，為下游的 `/recrystallize-post-series` 或 `/crystallize-report` 提供高解析度的架構藍圖。

---

## 0. 核心理念與認知自由度 (Core Principles & Freedom)

1. **取神棄形（Extract Essence, Discard Shell）**：
   - 嚴禁被原始素材的篇章數量、目錄階層或段落順序綁架。
   - 原始文本是發想種子與問題意識的來源，**絕非敘事天花板**。
2. **去污染與第一性原理求真（De-pollution & First-Principles Grounding）**：
   - 徹底清除一切無法考證的二手文獻指涉、疑似 AI 幻覺之論文引用、非精確的實驗數字與空泛學術修辭。
   - 將所有論點重新錨定至底層數學（機率論、微積分、線性代數、資訊論）、物理/幾何直覺、系統不變式（型別理論、狀態機、形式邏輯），以及零未安裝相依的可執行代碼模擬。
   - **理論奠基與行內出處規範 (Authoritative Theoretical & Engineering Grounding)**：
     - 去污染並非反對客觀權威源頭，而是掃除無連結的空泛指涉與假文獻。
     - 當論及經典機制、數學定理、開創性框架或核心工業標準時，**必須在論述該機制的當前段落行內（Inline Link），提供精確可查驗的真實文獻/標準超連結**（格式如 `[學者等人，年份 / 《論文名》](真實 URL / DOI / arXiv)` 或 `[機構，年份 / 規範代號](真實官方標準 URL)`）。
     - 嚴禁在文末開闢獨立參考文獻章節（正文必須以收束結論為終點，保持敘事自洽閉合）。
3. **拓撲自由重構（Topological Re-architecting）**：
   - 賦予 Agent 充分裁量權進行三種拓撲操作：
     - **深化（Deepen）**：將原文一筆帶過、實則蘊含核心機制的命題（如前向探針與反向梯度的代數差異），展開為獨立論證。
     - **合併（Merge）**：將本質同構、論點重複的篇章熔接為單一高密度的核心章節。
     - **拆分（Split）**：將單篇中超載、混雜多個獨立因果線的篇章，解耦為多個層次分明的認知節點。
4. **反換皮與抗鏡像禁令 (Anti-Reskinning Guardrail) [CRITICAL]**：
   - **嚴禁 1:1 換皮照抄**：若重構後的篇章 Slot 數量與主題分工與原始輸入素材完全一致（例如原素材為 10 篇，重構後也對應為 10 篇微調標題的報告），**判定為偽重構，必須即刻中止並打回重煉**。
   - **篇數自由度由問題域客觀因果結構決定**：重構後的篇數 $N$ 由問題域的內在因果複雜度決定（例如 3～8 篇皆屬健康區間），嚴禁為了湊特定數量（如刻板的「剛好 4 篇」）而人為合併不同正交核心或生硬拆分；反換皮禁令僅針對「未經思考的 1:1 照搬」，絕不限制由深度展開自然產生的篇數規模。
   - 重構必須體現**維度升級（Dimensional Elevation）**：必須以更高的問題域維度（如：度量自欺、表徵偽證、流形盲區、可證偽閉環）統攝整合，將破碎材料重新熔鑄為層次分明的宏大敘事弧。
5. **四維結構化表達與認知工學 (Quad-structure Expressive Rigor & Cognitive Ergonomics) [CRITICAL]**：
   - 拒絕純文字長篇大論造成讀者的認知超載。對每一個重構的主題節點，**強制規劃「流程圖（Mermaid）＋ 認知表格（Table）＋ 最小驗證程式碼（Code）＋ 嚴密數學/形式化模型（Math / Invariants）」**。
   - **表格是不可或缺的認知支架**：每篇報告必須配備至少兩類結構化表格：
     - **認知走一遍對照表 (Walkthrough Table)**：強制規劃具體輸入到輸出的閉環推演，杜絕純概念名詞羅列。依問題性質選用**「數值走一遍 (Numerical Walkthrough)」**（數值演算與機率模型：極端輸入 $\to$ 中間敏感度 $\to$ 理論極限 $\to$ 經驗輸出）或**「決策／狀態轉移走一遍 (Decision / State-Transition Walkthrough)」**（架構、型別、協定與治理邊界：邊界輸入案例 $\to$ 關鍵判定條件/不變式 $\to$ 狀態轉移 $\to$ 最終處置結果）；
     - **跨維度診斷與範式對照表 (Diagnostic Matrix & Paradigm Comparison Table)**：將多個概念橫向對比（如表面讀數/現象 vs 底層物理/架構病灶 vs 舊代脆弱做法 vs 新代嚴格工程防線）。
6. **藍圖架構權威（Blueprint Authority Over Downstream）**：
   - 本工作流產出的知識展開藍圖具備最高架構權威。
   - 當下游 `/recrystallize-post-series` 消費本藍圖時，藍圖定義的重構 Slot（篇數 $N$ 由因果拓撲自由決定）直接覆寫既有依候選貼文篇數鎖定之規則，下游不得以篇數變更為由強迫拆回碎片。

---

## 1. 輸入與邊界約定 (Inputs & Boundaries)

| 輸入類型 | 處理方式 |
| :--- | :--- |
| 指定母系列路徑（如 `content/posts/...`） | 批量掃描該系列所有關聯文章 |
| 指定單一草稿或報告路徑 | 針對該主題進行深度發散、解耦與重整 |
| 指定對話上下文或議題關鍵字 | 從對話紀錄中提取核心問題域與精神 |

### 邊界禁制
- **不寫最終長文報告**：本工作流產出的是**重構藍圖（Reconstruction Blueprint / Dossier）**，非最終篇章正文。
- **不更動 `content/` 原檔**：嚴禁就地修改、刪除既有發布內容。
- **不進行術語錨定**：術語錨定屬於下游發布管線職責。

---

## 2. 執行四階段程序 (Process Execution)

```mermaid
flowchart TD
    In["原始輸入素材<br/>(舊貼文 / 鬆散草稿 / 對話)"] --> S1["階段一：去污染核心萃取<br/>議題 (Issue) + 精神 (Spirit) + 客觀知識 (Knowledge)"]
    S1 --> S2["階段二：敘事拓撲重構<br/>打破框架：深化 (Deepen) / 合併 (Merge) / 拆分 (Split)"]
    S2 --> S3["階段三：四維結構化資產工程規格<br/>流程圖 (Mermaid) + 認知表格 (Tables) + 驗證代碼 (Code) + 數學模型 (Math / Invariants)"]
    S3 --> S4["階段四：產出知識展開藍圖<br/>(Reconstruction Blueprint)"]
    S4 --> Out["交付下游：<br/>/recrystallize-post-series 或 /crystallize-report"]
```

### 階段一：去污染核心萃取 (De-polluted Essence Extraction)

針對輸入素材進行穿透式閱讀，剝離表面裝飾，填寫**本質反推卡**：

```markdown
### 主題名稱：[暫定主題]
1. 議題核心 (Issue/Problem Domain)：本文試圖反思或解決的工程/理論盲區是什麼？
2. 批判精神 (Spirit/Stance)：本文堅持的認識論態度、審判視角與反直覺警示是什麼？
3. 客觀知識 (Objective Knowledge)：移除文獻假託後，底層真正成立的客觀規律、因果機制是什麼？
4. 污染掃除 (Contamination Purge)：
   - 需刪除之不可靠引用 / 模糊論文指涉：[列出]
   - 需替換之浮誇數字 / 未經驗證案例：[列出]
   - 需撥正之概念混淆：[列出]
```

### 階段二：敘事拓撲重構 (Narrative Arc Re-architecting)

1. **依據因果依賴與認知遞進，重劃篇章階梯**：
   - 建立自然的認知演進階梯（例如依問題複雜度展開為 3～8 個不可替代的主題節點；如「機制立論 $\to$ 邊界判準 $\to$ 防禦工程 $\to$ 跨尺度傳播」，或「度量自欺 $\to$ 內部表徵 $\to$ 高維盲區 $\to$ 契約驗證」）。**篇數嚴禁刻板湊數，全憑因果解耦與正交問題域的客觀複雜度決定**。
2. **標定拓撲操作**：
   - `[MERGE]`：指明哪些篇章的因果鏈與結論同構，應合併吸收。
   - `[SPLIT]`：指明哪篇素材暗藏多個獨立核心問題，必須拆分為獨立 Slot。
   - `[DEEPEN]`：指明哪些在原文中僅有一兩句話帶過的潛在深度，應拉昇為核心骨幹。
3. **繪製全新系列/篇章全景因果拓撲圖（Mermaid）**。

### 階段三：四維結構化資產工程規格 (Quad-structure Asset Blueprinting)

為重構後的每個 Slot / 篇章，強制指定以下四維資產規劃：

1. **流程與因果圖（Visual Flowchart / DAG）**：
   - 指定 Mermaid 圖表類型（`flowchart`, `stateDiagram-v2`, `sequenceDiagram`）。
   - 明確標注該圖承載的因果傳播鏈、責任邊界、狀態轉移或破壞機制。
2. **對比與診斷表格（Structured Tables & Cognitive Ergonomics）**：
   - **認知走一遍對照表 (Walkthrough Table)**：強制規劃具體輸入到輸出的閉環推演，杜絕純概念名詞羅列。依問題域性質二選一或並用：
     - **數值走一遍 (Numerical Walkthrough)**：適用於數值演算、機率模擬與統計度量（初始邊界輸入 $\to$ 中間敏感度 $\to$ 理論極限 $\to$ 經驗輸出）。
     - **決策／狀態轉移走一遍 (Decision / State-Transition Walkthrough)**：適用於架構、協定、型別約束、權責劃界與治理防衛（邊界輸入案例 $\to$ 關鍵判定條件/不變式 $\to$ 狀態轉移 $\to$ 最終處置結果）。
   - **跨維度診斷與範式對照表 (Diagnostic Matrix & Paradigm Comparison Table)**：橫向對比「表面讀數/現象 $\to$ 底層物理/架構病灶 $\to$ 舊代脆弱做法 $\to$ 新代嚴格工程防衛」。
3. **最小驗證程式碼（Minimal Executable Code & Self-Verifying Invariants）**：
   - **語言領域適配原則（Language Domain Alignment）**：程式碼的核心目標是展示不可動搖的系統不變式與因果機制。**嚴禁無腦鎖死單一語言**，應依據問題域選擇原生最適語言：
     - 數值演算法、機率模擬、資料分析、通用因果：優先使用 **Python**（限標準函式庫或基礎 NumPy）。
     - 型別系統、編譯期防線、模組封裝：優先使用具備強型別/編譯期機制的語言（如 **TypeScript / Node.js**, **Rust**, **Go**, **Java**）。
     - 系統與作業系統邊界、程序控制、資源隔離：優先使用 **POSIX Shell / Bash** 或 **C**。
     - 資料約束、狀態機不變式：亦可採用 **SQL DDL/DML**。
   - **自驗證紀律（Self-Verifying & Zero Heavy Dependency）**：
     - 嚴禁偽代碼或無法驗證的殘缺片段；嚴禁引入未安裝的外部重型依賴庫（如 PyTorch、TensorFlow、外部雲端 SDK）。
     - 必須具備秒級執行或確定性驗證能力（< 1s）：
       - 解譯執行語言（Python, JS/TS, Bash）：必須包含自驗證邏輯（如 `assert` 斷言、確定性條件比對或非零 exit code 自檢），無報錯執行通過。
       - 編譯/型別約束語言（Rust, TS, Go, Java）：必須明確展示「合法建構 vs 破壞不變式時的編譯/型別錯誤（Compile-time failure）」之對比驗證，或最小可執行單元。
4. **數學模型與形式化理論奠基 (Rigorous Math / Formal Invariants & Authoritative Grounding)**：
   - **內生機制與反裝飾性數學禁令 (Anti-Mathiness Guardrail)**：
     - 若問題域涉及機率、統計、微積分、線性代數、資訊論、圖論或博弈論，必須給出嚴密數理公式表示（如 Jensen 不等式、Hessian 條件數、奈奎斯特取樣邊界等）。
     - 若問題域屬於軟體架構、型別理論、協定設計或治理防衛，**形式化邏輯推導、集合論邊界定義、狀態機不變式（State Invariants）或嚴密型別簽名（Type Signatures）** 視為同等嚴謹之第一性原理表達。**嚴禁為了湊形式而硬造毫無演算價值的裝飾性偽公式（Mathiness）**。
   - **權威來源前綴規範 (Authoritative Provenance Prefixes)**：每個 Slot 必須標定該機制對應之經典權威來源，且 URL 必須指向真實且權威的門戶：
     - **學術理論源**：`doi.org/`, `arxiv.org/abs/`, `proceedings.mlr.press/`, `jstor.org/`, `acm.org/`, `ieee.org/` 等。
     - **權威工程規範、官方標準與第一手規格**：IETF RFC (`datatracker.ietf.org/`), 語言官方演進提案（`openjdk.org/jeps/`, `peps.python.org/`, `tc39.es/`, `w3.org/`）, 權威安全漏洞庫（`nvd.nist.gov/`, `cve.org/`）, 法定監管機構披露（`sec.gov/`）, 核心開源專案官方規格（如 `sqlite.org/`, `kernel.org/`）。
     - 嚴禁偽造連結或無來源泛稱。

### 階段四：產出知識展開藍圖與防漂移握手 (Output Downstream Blueprint & Handshake)

將上述分析匯整為完整的規格書，寫入 `.agent-scratch/recrystal-<date>-<slot>/series-map.md`。藍圖對下游 `/recrystallize-post-series` 具有最高架構鎖定效力：
- 藍圖凍結一份包含**固定槽位編號（Slot ID）、目錄 slug、不可替代角色、錨定文獻與邊界聲明**的結構化清單；
- 下游單篇結晶時必須無條件遵守該清單，嚴禁任何篇數塌縮、目錄更名或自由度漂移。

---

## 3. 輸出產物規格 (Deliverable Blueprint Schema)

產出的重構藍圖必須包含以下結構：

```markdown
# [系列/報告名稱]：知識展開與敘事重構藍圖

## 1. 認知階梯與因果拓撲 (Narrative Topology)
[包含全局 Mermaid 流程圖，說明各階層的認知演進與不可替代性]

## 2. 篇章重組對照與拓撲決策 (Structural Decisions)
[表格列出：新篇章 Slot | 來源素材映射 | 拓撲操作 (Merge/Split/Deepen) | 核心因果鏈]

## 3. Master Reports 角色、不可替代性與閱讀順序 (Slot Manifest) [N 篇，依因果拓撲自由決定]
[清單鎖定：順序 | 報告目錄 slug | 核心問題 | 不可替代角色 | 邊界聲明 | 建議 Tags]

## 4. 四類展開方向盤點表 (Expansion Audit Matrix)
[四類狀態逐項宣告：共用前提就地自含、概念地圖/拓撲、反例與邊界條件、結構化資產]

## 5. 逐篇四維結構化資產工程規格 (Per-Slot Quad-structure Specifications)
### Slot 01: [篇名]
- **核心問題與精神**：
- **理論奠基文獻 / 權威工程標準 (Authoritative Provenance)**：[精確文獻/標準名與權威 URL]
- **數理核心 / 形式化不變式 (Math / Invariants)**：[具體公式、型別簽名或狀態不變式]
- **圖表規格 (Mermaid)**：[圖表結構與節點語意]
- **表格規格 (Tables)**：[數值走一遍或決策/狀態走一遍表 + 跨維度診斷表設計]
- **程式碼規格 (Code)**：[語言選型、驗證目標、自檢斷言/編譯約束與預期行為]
- **邊界與反例**：[何時不適用]

[...依序規劃其餘 Slot...]

## 6. 去污染稽核清單 (De-pollution Audit)
[明確列出已清除之不可靠來源、文獻與替代 First-principles 方案]

## 7. 品質閘門自檢 (Quality Gate Audit)
```

---

## 4. 品質閘門 (Quality Gate)

產出重構藍圖前必須逐項自檢：

- [ ] **去污染徹底**：所有二手不可靠論文引用與未經檢驗的實驗數字皆已被標記剔除，並替換為數學、物理或工程第一性原理。
- [ ] **框架破除與篇數自由度**：新架構明確展現出深化、合併或拆分的拓撲演進，未淪為原素材的 1:1 機械照搬；篇數由因果複雜度客觀決定（3～8 篇皆屬合規），未受湊數定勢扭曲。
- [ ] **拒絕換皮照抄**：新架構的 Slot 數量與主題分工不可與原始素材呈 1:1 鏡像對應，必須有實質的跨篇章熔接或多核心解耦。
- [ ] **文獻/標準權威前綴合規**：所有理論或工程奠基來源均指向真實權威前綴（DOI, arXiv, PMLR, RFC, JEP/PEP, NVD CVE, SEC 等），無偽造或無連結泛稱。
- [ ] **四維資產無缺漏**：每個新規劃的主題節點均具備流程圖、認知表格、最小驗證代碼與數學/形式化模型之明確規劃。
- [ ] **認知表格非退化**：走一遍表具備「輸入 $\to$ 敏感度/判定 $\to$ 輸出」因果鏈（數值型或架構決策型）；範式診斷表具備「現象-病灶-脆弱-防衛」四維對照。
- [ ] **領域代碼自驗證**：代碼語言適配問題域（Python/TS/Rust/Go/Java/Bash/SQL 等），純度達標（零外部重型相依），具備秒級自檢能力（assert 斷言或編譯/型別錯誤對比）。
- [ ] **反裝飾性數學 (Anti-Mathiness)**：數理模型皆具實質演算價值；架構或工程主題採用集合論、形式邏輯或狀態不變式，無空泛偽公式。
- [ ] **防漂移清單凍結**：藍圖鎖定結構化 Slot Manifest，定義權威 slug、邊界與角色，防止下游執行自由度漂移。
- [ ] **敘事因果閉合**：篇章之間的依賴關係由因果推進決定，形成完整的認識論閉環。
