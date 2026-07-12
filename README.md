# last hop

[tacticaldoll.github.io](https://tacticaldoll.github.io/) 的網站原始碼。

這是一個記錄網路、軟體、系統與 AI，以及其背後假設、代價與邊界的個人網站。

## 本機開發

初始化子模組：

```bash
git submodule update --init --recursive
```

啟動開發伺服器：

```bash
hugo server
```

執行正式建置：

```bash
hugo --minify
```

## 專案結構

- `content/`：網站內容。
- `layouts/`：網站層級的 Hugo 與 Slotify 覆寫。
- `static/`：靜態資產與 JavaScript 覆寫。
- `themes/slotify/`：唯讀的佈景主題子模組。
- `.agent/`：內容、術語與發布工作流。

## 專案治理

變更前請先閱讀 [`GUIDE.md`](GUIDE.md)。

## 授權

[Unlicense](LICENSE)
