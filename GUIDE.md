# 專案指引準則 (Project Guidelines)

本文件定義了 **Journey Technical Notes** 專案的開發與維護準則。所有參與者（包含 AI 代理人）均須嚴格遵守以下規範。

## 0. 開發模式規範 (Development Mode)

- **SDD 模式**：本專案採用 **SDD (Spec-Driven Development，規格驅動開發)** 模式撰寫。所有功能變更與代碼實作均須先定義規格、確認計畫後方可執行，以確保架構的一致性與可追蹤性。

## 1. 語言規範 (Language Policy)

- **核心語言**：本專案的所有說明文件、計畫書 (Implementation Plan)、進度紀錄 (Walkthrough) 以及文章導覽，皆必須使用 **繁體中文** 撰寫。
- **一致性**：為了保持專案脈絡的一致性，避免在同一份文件中混用不同語言（代碼與技術術語除外）。

## 2. Git 與子模組管理 (Git & Submodule Management)

- **子模組完整性**：`.gitmodules` 檔案與其定義的子模組路徑 **絕對不可被更動**。
- **更新原則**：主題 (Theme)應維持作為外部 Submodule 存在。若需更新主題，應使用 `git submodule update --remote` 進行同步，而非修改子模組的指標或路徑。
- **佈景主題覆寫 (Theme Overrides)**：若需修改主題的 Layout 範本或元件，**絕對不可直接修改** `themes/` 目錄下的原始碼。應將需要修改的檔案複製到專案根目錄相對應的 `layouts/` 或 `assets/` 目錄下進行覆寫。
- **忽略編譯產出**：`public/` 目錄為 Hugo 編譯的目標目錄（Build Destination）。由於本專案採用 **GitHub CD** 自動化部署，開發環境下的 `public/` 目錄 **絕對不可提交至 Git**，必須始終保留在 `.gitignore` 中。

## 3. 內容組織與結構規範 (Content Organization)

### 文章結構 (Page Bundles)
- 所有文章必須使用 **Page Bundle** 格式：`content/posts/<post-name>/index.md`。
- 圖片、附件應存放於該文章目錄下，以便於移植與維護。

### 分類與標籤 (Taxonomies)
- **禁用 Categories**：本專案不使用 `categories` 項目，請將分類需求轉化為 `tags` 或 `series`。
- **使用 Tags**：用於標記具體的技術點（如 `Hugo`, `Prometheus`）。
- **使用 Series**：用於歸納性質相近或具連續性的文章（如 `自製主題開發實錄`）。

### 文章摘要 (Summary Generation)
- **手動切分**：請務必在文章的第一或第二段落後手動插入 `<!--more-->` 標記。這能精確控制首頁與列表頁顯示的預覽長度，避免文字過多。

### 過時內容提醒 (Stale Content Warning)
- 系統會自動檢測文章日期。若發布時間超過 **3 年**，會在 JSON 內容最前端自動插入警告區塊，提醒讀者資訊可能已過時。

---

## 4. 技術實作標準 (Technical Standards)

### Hugo 範本自定義 (Layout Customization)
- **JSON 輸出命名**：在 `layouts/_default/` 下覆寫 JSON 格式相關範本時，檔案副檔名應使用 `.json.html`（例如 `single.json.html`）。
    - *註：這能防止 Hugo 的內建 JSON 校驗器誤將包含範本標籤（{{ ... }}）的檔案當作純 JSON 解析而報錯。*
- **邏輯抽離**：複雜的資料字典建構應放在 `layouts/partials/` 中（如 `get-single-data.html`），`single.json.html` 應保持簡潔，僅負責組合 Partial 並使用 `jsonify` 輸出。

## 5. 變更流程 (Workflow)

- **規範執行**：所有變更應嚴格遵守 **Section 0** 定義的 SDD 模式，先於 `implementation_plan.md` 中說明規格。
- **自動化驗證**：任何變更後應執行 `hugo` 編譯並核對 `public/` 目錄結構，確保 SPA 所需的數據產出正常。
