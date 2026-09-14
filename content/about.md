+++
layout = "about"
title = "關於"
description = "安靜地紀錄技術實踐與靈感萃取的空間"
isCJKLanguage = true
author = "梅乾"

[[src]]
name = "Slotify"
category = "Frontend & UI"
url = "https://github.com/tacticaldoll/slotify"
demo = "https://tacticaldoll.github.io/slotify"
image = "/images/slotify-demo.png"
desc = "基於 Vue SPA 架構的無頭 (Headless) Hugo 主題。徹底分離前後端，提供無縫的客戶端路由與高度可擴展的動態元件系統。"

[[src]]
name = "Fornax"
category = "AI & Automation"
url = "https://github.com/tacticaldoll/fornax"
demo = ""
image = ""
desc = "可攜式、多代理人的技能註冊庫。以單一職責的 Agent Skills 協助程式代理人定位、規劃、理解與審查，同時維持唯讀、規劃與回報的安全邊界。"

[[src]]
name = "Tianheng"
category = "Architecture & Tooling"
url = "https://github.com/tacticaldoll/tianheng"
demo = ""
doc = "https://crates.io/crates/tianheng"
image = ""
desc = "Rust 原生的反應式架構治理框架。透過靜態、語意與執行期三個觀測維度，讓編譯器、CI 與執行期機制在架構偏移時立即反應。"

[[src]]
name = "Pacta"
category = "Infrastructure"
url = "https://github.com/tacticaldoll/pacta"
demo = ""
doc = "https://crates.io/crates/pacta"
image = ""
desc = "面向 Rust 自訂義務的精簡耐久契約核心與受治理模式框架。以小型生命週期核心承載宣告、認領、執行與結算，同時避免讓 Broker 式框架接管應用程式語意。"

[[src]]
name = "Worklane"
category = "Infrastructure"
url = "https://github.com/tacticaldoll/worklane"
demo = ""
doc = "https://crates.io/crates/worklane"
image = ""
desc = "原生型別安全的 Rust 非同步背景任務執行器。提供帶有重試機制、死信佇列 (Dead-lettering)、通道分區 (Lane partitioning) 的任務排程，並支援記憶體與 SQLite 兩種可插拔的 Broker 實作。"

[[src]]
name = "Modou"
category = "Architecture & Tooling"
url = "https://github.com/tacticaldoll/modou"
demo = ""
doc = "https://crates.io/crates/modou"
image = ""
desc = "類似 cargo-deny，但針對架構設計 — 宣告 Rust 中的 crate 與 module 邊界，並透過 CI 反饋來強制執行。"

+++

我是梅乾（梅花的梅，乾坤的乾）。職涯起於網路工程，後來轉向軟體工程；改變的是工作的介面，不變的是我理解問題的方式。

在網路與軟體之間轉換，也讓一些原本分屬不同領域的經驗開始彼此呼應。從封包如何抵達目的地，到程式如何在元件之間傳遞資料，某個情境裡看見的結構，換個情境仍可能成為理解問題的線索。我關注的不只是功能是否成立，也包括支撐它的路徑、狀態與邊界；面對軟體與 AI，我會先辨認這些關係，再把直覺展開成可討論的因果與可驗證的技術邊界。

這套理解方式也被我用來反向檢查圍繞 AI 形成的主流敘事與社群文化。當平台依賴被描述為便利，我會追問：控制權交給了誰，離開時又要付出什麼代價？當行銷承諾被包裝成技術進步，我會追問：增加的是可驗證的能力，還是只能被平台定義與展示的效果？當社群展演與變現需求開始主導討論，我更想知道：我們真的在解決原本的問題，還是在替一套早已決定答案的商業模式補寫理由？如果每個新名詞都要求更多依賴、更多信任與更少退出空間，那麼被販售的究竟是進步，還是一套讓人難以離開的敘事？

「梅乾」取梅花傲骨與乾坤定位之意，一如歷經風乾凝縮的質地——褪去多餘的水分與浮誇的修飾，保留最純粹的因果結構。對我而言，這也是一種主動終止與沉澱：讓已受污染的 context、借來的信任、外部強加的期待與未經檢查的假設，隨著 session 的生命週期一同失效。

這裡記錄網路、軟體、系統與 AI，也嘗試把那些被話術掩蓋的前提、代價與邊界重新攤開。留下來的未必是答案，而是一些足以讓人重新判斷問題、拒絕預設選項，並在必要時退出既有敘事的線索。

---

{{< adr-heading num="01" title="審查算子：反向檢查主流敘事的工程判準" >}}

{{< adr-legend >}}
  <span class="adr-legend__item">{{< adr-badge color="rose" >}}強制拒絕{{< /adr-badge >}} 無退出空間之鎖定依賴</span>
  <span class="adr-legend__item">{{< adr-badge color="amber" >}}嚴格檢驗{{< /adr-badge >}} 平台定義之展演效果</span>
  <span class="adr-legend__item">{{< adr-badge color="green" >}}可證偽契約{{< /adr-badge >}} 客觀因果與確定性邊界</span>
{{< /adr-legend >}}

{{< adr-grid cols="3" >}}

  {{< adr-card title="控制權與依賴轉移" status="強制拒絕" statusColor="rose" meta="boundary · 結構型" confidence="high" >}}
  當平台依賴被包裝為「便利」，拒絕算子即刻觸發：控制權被交給了誰？離開這套架構時又要付出多大的遷移代價？若無低成本退出路徑，該技術便利性即為負資產。
  {{< /adr-card >}}

  {{< adr-card title="能力驗證 vs 效果展示" status="嚴格檢驗" statusColor="amber" meta="falsifiability · 判準型" confidence="high" >}}
  當行銷承諾被宣稱為「技術突破」，追問其本質：增加的是在不可判定性下仍能提供客觀保證的約束覆蓋率，還是僅能在封閉平台環境內被特定展示定義的效果展演？
  {{< /adr-card >}}

  {{< adr-card title="敘事補完與商業依附" status="邊界劃分" statusColor="cyan" meta="teleology · 目的型" confidence="med" >}}
  當社群展演與變現節奏主導技術討論：我們是否真在解決原本的工程瓶頸，抑或僅是替一套早已預設答案的商業模式補寫合理化依據？拒絕為不可逆依賴買單。
  {{< /adr-card >}}

{{< /adr-grid >}}

{{< adr-callout label="梅乾 · 核心邊界" >}}
**當封包的 TTL 歸零，它便停止轉送；當信任與前提失去可證偽性，系統必須主動終止。**

讓已受污染的 context、借來的信任、外部強加的期待與未經檢查的假設，隨著 session 的生命週期一同失效。留下來的不是盲目的答案，而是足以拒絕預設選項、退出既有敘事的確定性線索。
{{< /adr-callout >}}

{{< adr-heading num="02" title="系統邊界與退出代價矩陣" >}}

{{< adr-spec-list >}}
  {{< adr-spec-row key="CONTEXT-PURITY" >}}
  拒絕無界限的 Context 繼承。代理人與模組必須在確定性沙盒內隔離運行，嚴禁隱性狀態累積與語意交叉污染。
  {{< /adr-spec-row >}}

  {{< adr-spec-row key="EXIT-RUNWAY" >}}
  所有架構決策皆須保留「可無痛抽離（Zero Lock-in）」的逃生路徑。若引入依賴的成本遠小於移除成本，該依賴即被視為架構壞疽。
  {{< /adr-spec-row >}}

  {{< adr-spec-row key="FALSIFIABILITY" >}}
  一份規格或架構的真實價值，不等於其文字完備性，而等於其誘導之拒絕算子對違規空間的覆蓋率。不能拒絕任何東西的規格，等同不存在。
  {{< /adr-spec-row >}}
{{< /adr-spec-list >}}

