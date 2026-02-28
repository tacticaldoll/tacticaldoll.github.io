---
title: "在踩坑中前行：那些隱藏在 SPA 路由與 JSON 資料裡的陷阱"
date: 2026-03-01T03:15:00+08:00
description: "當靈感準備落地，隨之而來的就是無盡的瑣碎問題。記錄我在打造 Headless Hugo 時踩過的那些坑。"
author: "Tinkerer"
tags: ["Hugo", "Vue3", "SPA", "Debugging", "JSON"]
categories: ["Experience Sharing"]
series: ["初嘗 Antigravity 與 Vibe Coding：自製主題開發實錄"]
---

作為《自製主題實踐筆記》系列的最終篇，在上一篇總結完協作心法後，這篇我們要來點「接地氣」的血淚史。在將 Hugo 打造為 Headless CMS 並結合 Vue.js 構建單頁式應用（SPA）的旅程中，一旦脫離了理想的架構圖，現實中就會迎面撞上一些極具代表性的「技術坑」。這篇筆記，就是用來祭奠那些隱藏在自動化工具與環境差異夾縫中的時間。

<!--more-->

## 1. JSON 輸出中的「隱形」換行符

這是這次實驗中最隱蔽的一個 Bug。我用了 Hugo 的 `plainify` 過濾器來產生文章摘要（Summary），目的是去除 HTML 標籤，讓卡片排版穩一點。

**問題**：`plainify` 雖然去除了 HTML，但會保留原始 Markdown 內容中的**硬換行（Literal Line Breaks）**。在標準 JSON 字串中，物理上的直接換行是非法的。這導致生成的 `index.json` 無法被瀏覽器解析（Parsing Error），進而造成首頁文章完全消失。

**對策**：在 Hugo 模板中，必須強制用正則手動把換行壓平：
```go
"summary": (.Summary | plainify | replaceRE "[\\r\\n]+" " ")
```
這確保了輸出的 JSON 摘要是連續的字串，這才把首頁給救了回來。

## 2. JavaScript Runtime 的「未定義」炸彈

在 SPA 的組件切換中，也遇到過 Vue 應用直接整個白屏崩潰的狀況。

**問題**：在組件中直接拿了未定義的 `currentRoute` 和 `currentPageUrl` 變數來用。由於這是組件層級的錯誤，它直接阻斷了整個渲染鏈。

**對策**：乖乖回去看 Vue Router 的文檔，正確使用 `useRoute()` 搭配 `Vue.computed` 來做響應式綁定：
```javascript
const route = Vue.useRoute();
const currentRoute = Vue.computed(() => route.path);
const currentPageUrl = Vue.computed(() => window.location.origin + route.path);
```

## 3. 環境語法的「水土不服」

在開發過程中，自動化腳本的執行環境也常搗亂。

**問題**：PowerShell 不支援使用 `&&` 來連接同步命令（應使用 `;`），也不支援直接在命令末尾加 `&` 來執行背景任務。這類細微的語法差異在自動化執行時，常常會直接報錯中斷流程。

**對策**：明確使用針對 PowerShell 優化的腳本語句，或是乾脆寫 Node.js / Python 腳本來繞開這種平台差異。

## 【作者日誌：除錯也是一種對頻】

> [!TIP]
> **作者筆記 (Vibe Coding 觀察)**：
> 原本以為把這份擱置了**五年**的靈感寫完就沒事了，結果最後的時間都花在這些瑣碎的 Bug 上。
> 
> 在這次跟 Agent 的協作中，我發現處理 Bug 反而是最容易讓人煩躁的環節。Agent 常常會給出看似合理但其實少考慮了邊界條件的解法（例如 JSON 換行符的問題）。我得一直盯著它產出的細節，甚至要反過來糾正它的環境認知。這種「一邊整活、一邊還要幫機器擦屁股」的摩擦感，確實讓人身心俱疲。但轉念一想，正是這種跌跌撞撞的排雷過程，才讓這個點子真正從幻想變成了可以用的東西。

---

## 4. 結語 (系列完結)

SPA 與 Headless 的整合不僅是前端技術的挑戰，更是對數據交換格式與靜態網站生成器脾氣的深度摸索。這條踩坑之路走起來有點顛簸，但也算是為這個五年的點子畫上了一個還算完整的句點。

自此，《自製主題實踐筆記》系列五篇正式完結。技術與框架總會更迭，但這些與 Bug 搏鬥、與 AI 拉扯的經驗，都將成為下一次「擱置靈感」爆發時的最佳養料。
