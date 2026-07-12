---
name: physical-enforcement
description: 執行物理級肅清，徹底移除隱性污染並重設治理權限 (Execute Physical Enforcement to purge latent pollution)
user-invokable: true
schema: []
spec: "../reference/agent-operating-guideline.md"
---

# 治理技能：物理級肅清 (Physical Enforcement)

本指引定義了當專案語義環境遭受「隱性污染 (Latent Pollution)」或發生「憑空重構 (Phantom Reconstruction)」時的極端清理流程。核心目標在於透過物理手段（刪除與重構歷史）強行切斷 AI 的錯誤認知。

## 1. 執行時機 (Trigger Conditions)
1. **認知坍縮**：AI 持續生成已廢棄的舊路徑或過時內容。
2. **語義異常**：發現 AI 正在參考不存在於當前工作區但存在於 `git log` 中的資訊。
3. **重啟治理**：當工作流（如 `publish-article`）發生結構性錯誤，需要從乾淨的 Session 重新開始時。

## 2. 第一階段：清理實體檔案 (Filesystem Purge)
1. **刪除污染路徑**：
   - 刪除所有受污染的生成目錄：`rm -rf content/posts/gen-*`
   - 刪除所有未追蹤的殘骸：`git clean -fd`

## 3. 第二階段：重構 Git 歷史 (History Reconstruction)
為了斷開 AI 的「歷史即指令」錯覺，必須執行：
1. **遠端基準錨點 (Remote as Anchor)**：歷史重構必須以遠端分支 (`origin/main`) 作為不可變的權威起點。執行 `git reset --hard origin/main` 以確保本地狀態與遠端權威完全同步。
2. **禁止未經確認的同步**：在未獲得人類明確確認前，**嚴禁** 執行 `git push --force`。所有歷史修正僅限於本地環境，直到驗證完成。

## 4. 第三階段：驗證與確認 (Verification & Consent)
1. **狀態檢查**：執行 `git status` 與 `git log -n 1` 確保環境為 `clean` 且無污染痕跡。
2. **人類確認**：向使用者展示預計推動的變更。僅在使用者確認後，方可執行最終的遠端同步。

> [!CAUTION]
> **強制性警告**：物理級肅清會永久移除 Git 歷史與實體檔案，執行前必須確認當前已結晶的素材（Reports）已安全存儲於 `.agent-scratch/` 中。
