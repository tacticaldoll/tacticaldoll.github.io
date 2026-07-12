---
name: calibrate-guidelines
description: 確保所有專案指引文件與工作流程符合語義一致性、結構邏輯與邊界規範 (Calibrate Guidelines)
user-invokable: true
schema: ["../schemas/terminology.schema.yaml"]
spec: "../reference/agent-operating-guideline.md"
---

# 技能：指引校正 (Calibrate Guidelines)

本技能為專案的「後設指引 (Meta-Guideline)」，用於維護專案規則的整體一致性。當您（AI Agent）被要求進行指引校正、或是在開始大規模變更前，**必須呼叫此流程**。

## 1. 語義一致性校正 (Semantic Consistency)
- **術語統一**：檢查所有 `.md` 格式的指引文件。必須強制讀取並對照 [.agent/lexicon-core/databases/terminology.json](../lexicon-core/databases/terminology.json) 進行校正。
- **原生對齊檢核**：驗證所有新目錄命名或術語是否符合 `GUIDE.md` 中的「原生對齊優先」原則。
- **術語候選掃描 (Terminology Candidate Scan)**：主動偵測文件中符合 `中文（English）` 格式但尚未被術語庫收錄的新概念。若發現，應在校正報告中列出預計收錄清單。
- **關鍵字對齊**：確保所有提及指令性、規範性文件的詞彙，統一使用專案定義的核心術語（如將「規章」、「教程」統一為**「指引」**）。
- **去擬人化排除**：檢查並移除指引中任何帶有「建議」、「請」、「謝謝」等擬人化社交語法，確保規則以**冷酷的物理約束**形式呈現。

## 2. 合規性界限校正 (Compliance Boundary)
- **路徑合規掃描 (Path Compliance Scan)**：強制檢查所有文件，確保不存在本機絕對路徑（如 `file:///Users/`）。連結必須使用相對路徑。

## 3. 指引原子化與工具對齊 (Atomization & Tool Alignment)
- **格式與工具約束**：
    - 驗證是否明確標註了特定目錄（如 `content/`）的硬性格式要求（如 **TOML** 標記）。
    - 驗證所有的工具調用說明是否符合「原子化 (Atomization)」與「減少語義負載」的防禦原則。

## 4. 技能與指引同步 (Consistency Verification)
- **標題規範**：確保技能（Workflows）標題明確標示其「功能屬性」，並與核心指引中的術語完全對應。
- **因果鏈驗證**：檢查各指引間的執行順序與依賴關係。例如：文章生成指引必須符合「先建立 Page Bundle、後填入內容」的物理順序，不得產生邏輯越位。

## 5. 變更鑑識 (Change Forensics)
- 每次校正後，應對照 [../reference/agent-operating-guideline.md](../reference/agent-operating-guideline.md) 的 Permanent Gates 章節，檢視本次校正是否解決了過去發生的行為漂移（Behavioral Drift）或冷啟動失效問題。
