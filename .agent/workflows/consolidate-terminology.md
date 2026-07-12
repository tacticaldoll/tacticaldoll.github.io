---
name: consolidate-terminology
description: 將累積於草稿層的術語,經確定性驗證與人工複審後固化進核心術語庫 (Consolidate Terminology)
user-invokable: true
schema: ["../schemas/terminology.schema.yaml"]
spec: "../reference/agent-operating-guideline.md"
---

# 技能：術語固化 (Consolidate Terminology)

本技能補上專案知識流「**對話 → 結晶 → 固化**」中,術語長期缺失的那一段「**固化 (Consolidate)**」。

> [!NOTE]
> **設計前提（為何需要本流程）**：術語的「精確」本質上是**跨語料、需時間沉澱**的屬性——正規形式、變體調和、粒度、定義穩定性,沒有一項能從單一報告判定。而 `/publish-article` 的 `--promote` 在**發佈當下**就把草稿直接晉升核心,等於讓術語跳過沉澱期。本流程把「鑄造」與「固化」在時間上拆開：文章照常把候選流入 `draft`(瞬時、局部、允許噪音),由本流程**批次**地、跨語料地驗證與策展後,才晉升 `core`(經沉澱、精確)。

> [!IMPORTANT]
> 本流程**禁止 `// turbo`**。階段二為強制人工複審閘門。確定性驗證(階段一)負責擋掉結構性噪音,人工只裁決機械無法判定的語意殘渣。

## 0. 觸發時機與前置 (Trigger & Preconditions)

- 本流程**非** per-publish 步驟。應在 `terminology.draft.json` **累積一定數量**後批次執行。
- 前置：`/publish-article` 的 `--promote` 已不再是術語進入核心的唯一路徑——常態下應停用該自動晉升,改由本流程把關(見 [agent-operating-guideline.md](../reference/agent-operating-guideline.md))。

## 1. 確定性驗證掃描 (Deterministic Scan) — 不可變更

```bash
python3 .agent/scripts/workflows/consolidate-terminology/consolidate.py --scan
```

對 `draft` 套用三道既有 `lint` 未涵蓋的確定性驗證,並對 `core` 做唯讀稽核(報告既有污染)：

- **① 結構性碎片**：`zh` 含句讀標點、以語助詞(`是`/`而是`/`不是`…)開頭、或長度 ≥ 上限 → **封存(quarantine),不晉升**。
- **② 近義變體**：`zh` 與既有核心術語編輯距離 ≤ 1 → 標記為疑似變體,**封存**並提示應合併或登記為 `forbidden`。
- **③ 過度通用**：跨 `content/posts/` 的 document-frequency 超過門檻 → 建議**降為 level 3**(安全防護詞,不參與標籤收割)。

掃描為純唯讀,輸出人工複審報告至 `.agent-scratch/consolidation-report.md`,**不變更任何資料**。

## 2. 人工複審 (Human Review) — 第 ④ 類語意裁決

- 閱讀 `consolidation-report.md`。
- 確定性驗證已濾掉 ①②③；人工**只需裁決 `REVIEW` 區塊**(結構乾淨、但語意正確性需人腦判斷者)。
- 欲否決某術語：自 `terminology.draft.json` **刪除**該條目。
- 欲挽救被誤判的 ①② false-positive：修正其 `zh` 或於核心術語登記關係後,再重跑階段一。

## 3. 套用與晉升 (Apply & Promote)

```bash
python3 .agent/scripts/workflows/consolidate-terminology/consolidate.py --apply
```

- 將 ①② `blocked` 條目移入 `terminology.archive.json` 並自 draft 移除。
- 將 ③ `generic` 條目於 draft 內就地降為 `level: 3`。
- 對 draft 殘存(經人工保留)者,委派 `LexiconManager.promote_all_drafts()` 晉升——該步仍會執行既有 `lint` 作為終端閘門。

## 4. 既有核心污染與未來遷移 (Existing Pollution & Future Migration)

- 階段一對 `core` 的稽核為**唯讀提示**。清理既有核心污染需重寫已發佈貼文,屬獨立的**再錨定遷移**(Re-anchor Migration),不在本流程範圍。
- 貼文以穩定 key(`<!-- term:Key -->`)錨定,為 lexicon 的**可逆投影**;故核心策展決定可於日後經授權的遷移流程冪等回貼。本流程先確保「新血」乾淨。

## 5. 邊界與權責 (Boundaries)

1. **唯讀於發佈物**：本流程**不寫入** `content/`。
2. **確定性優先**：①②③ 由腳本機械裁定,人工不複查;人工只負責 ④。
3. **封存非刪除**：被擋的術語移入 archive,保留審計痕跡,不可物理刪除。
