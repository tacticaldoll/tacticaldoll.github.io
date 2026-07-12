---
name: reanchor-posts
description: 將當前術語庫冪等回貼至已發佈貼文,維護內文術語錨點 (Re-anchor Posts)
user-invokable: true
schema: ["../schemas/terminology.schema.yaml"]
spec: "../reference/agent-operating-guideline.md"
---

# 技能：貼文再錨定 (Re-anchor Posts)

本技能是 [consolidate-terminology](consolidate-terminology.md) 的下游遷移層。當核心術語庫經策展變更後(新增、降級、封存術語),本流程把這些決定**冪等地回貼**到已發佈貼文的內文錨點,使貼文維持為「術語庫的可逆投影」。

> [!IMPORTANT]
> **本流程是少數獲授權寫入 `content/` 的工作流。** 因 `content/` 屬受保護目錄(`.antigravityignore`),`--apply` 屬治理層級操作,**必須先經 `--scan` 人工檢視變更摘要後才可執行**。禁止 `// turbo`。

> [!NOTE]
> **冪等性與安全前提**:再錨定複用發佈管線同一套 `TerminologyInjector.apply_lexicon(mode="anchor_first")`——先完整移除既有錨點,再依當前術語庫重貼。**前置 TOML front matter 除 `tags` 區塊外逐字保留**;`tags` 區塊由共用 `TagAnchorer` 以**鍵為身分**原地、無損地(regex,非 tomllib 往返)重推導顯示值與 `# term:Key`,因此既不遺失標籤註解、又能讓標籤與術語庫保持同步。

## 0. 涵蓋範圍 (Scope)

- **維護對象**:① 內文(body)術語錨點 `<!-- term:Key -->`、雙語標註 `（English）`、定義呼叫框 `> [!IMPORTANT] ... <!-- anchor:Key -->`、以及術語的**首見粗體修飾**;② front matter `tags` 的**標註**(顯示值與 `# term:Key`)。
- **回貼效果**:
  - 術語**降為 level 3** → 內文錨點被移除(level 3 不錨定);**且其遺留的「首見粗體」`**詞**` 也一併移除**——L3(IGNORE_LIST)通用詞不應以術語形式加粗,去錨必須連同當初加上的粗體一起清除。僅移除**對稱獨立**的 `**詞**`;若該詞只是更長作者粗體的邊緣(單側標記),則保留不破壞該粗體片段。
  - 術語**自核心封存/移除** → 其孤兒錨點被清除(同上,若降為未錨定狀態,對稱獨立粗體一併清)。
  - 術語**新增**且命中舊貼文內文 → 回補錨點(自我修復)。
  - 術語**雙語/顯示**更新 → 標註刷新。
  - 標籤以**鍵為身分**重推導:顯示漂移 → 刷新;術語**降 level 3 或自核心移除** → 整條標籤刪除;重複鍵 → 去重。
- **標籤選取(刻意不在範圍)**:哪些標籤存在、genre(來自 `scope`)、domain 偵測屬**組裝期選取**,依賴 handoff(reanchor 期可能已歸檔),本流程**不重跑、不新增/採集**,只重推導**既有**標籤的標註。

## 1. 變更掃描 (Dry-run Scan) — 不寫入

```bash
python3 .agent/scripts/workflows/reanchor-posts/reanchor.py --scan
```

逐篇於記憶體再錨定並與原檔比對,輸出變更摘要(將變更之貼文數、各篇錨點增減量)至 `.agent-scratch/reanchor-report.md`。**不寫入任何貼文。**

針對單篇預覽:

```bash
python3 .agent/scripts/workflows/reanchor-posts/reanchor.py --scan --post <slug>
```

## 2. 人工檢視 (Human Review)

- 閱讀 `reanchor-report.md`,確認變更符合預期(尤其是大量錨點移除——可能源於誤降級或誤封存)。
- 若變更異常,回到 `/consolidate-terminology` 修正術語庫後重新掃描。

## 3. 套用 (Apply) — 寫入 content/

```bash
python3 .agent/scripts/workflows/reanchor-posts/reanchor.py --apply
```

僅重寫有實際變更的貼文;front matter 除 `tags` 區塊原地重推導外逐字不動。完成後以 `git diff` 複核跨篇變更,再提交。

## 4. 邊界與權責 (Boundaries)

1. **Front matter 限縮變更**:僅 `tags` 區塊由 `TagAnchorer` 原地、無損重推導(改寫既有標籤的顯示值/ `# term:Key`、去重、刪除孤兒/降級);`tags` 以外的 front matter 與 `+++` 之後的內文比照各自規則,其餘逐字不動。
2. **冪等**:術語庫未變時重跑應為 no-op(零貼文變更)。
3. **先掃描後套用**:`--apply` 前必有一次人工檢視過的 `--scan`。
