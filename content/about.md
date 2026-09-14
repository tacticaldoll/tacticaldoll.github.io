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

我是梅乾（梅花的梅，乾坤的乾）。職涯起於網路工程，後來轉向軟體工程與系統架構；改變的是工作的介面與觀測的尺度，不變的是我理解問題的方式。

在網路、軟體、系統與組織之間轉換，讓一些原本分屬不同領域的經驗開始彼此呼應。從封包如何在路由節點之間轉送，到任務如何在系統與流程中流動，某個情境裡看見的守恆與阻力，換個情境仍是理解問題的關鍵線索。我關注的不只是表面效果是否成立，也包括支撐它的因果鏈、不可見的代價與實質邊界。

「梅乾」取梅花經霜傲骨與乾坤定位之意，一如歷經風乾凝縮的質地——在紛雜的技術狂潮、熱門敘事與膨脹宣稱面前，**主動風乾多餘的水分與修飾，回歸純粹的因果結構與真實代價**。

作為一個長期的系統觀察者，我看見技術從來無法脫離整體的代價而孤立存在。不可判定的技術承諾，往往在下游引發不可逆的架構摩擦；評測讀數的表象，常與真實的單位經濟產生斷層；而自動化光環的背後，也往往隱匿著未被記錄的人工補償與制度成本。

因此，這裡的觀察視角，始終錨定在四個相互咬合的實務分野：
- **工程約束**：看見形式極限、約束覆蓋率與不可逆承諾的技術邊界；
- **組織流動**：看見作業守恆律、排程批量與在製品（WIP）對端到端交付的實質影響；
- **商業對帳**：看見供應商准入、退出鎖定成本、微觀邊際貢獻與全生命週期的真實 TCO；
- **制度權責**：看見界面背後的責任歸屬、救濟鏈路，以及系統運作中被隱匿的代償成本。

這裡記錄網路、系統、AI、組織流動與制度對帳。留下來的未必是現成的定論，而是一些足以讓人看清因果、衡量代價、辨識邊界的觀察線索，在面對預設選項時，擁有獨立判斷與退出的空間。

---

{{< adr-heading num="01" title="四維觀測矩陣：實務因果與對帳判準" >}}

{{< adr-legend >}}
  <span class="adr-legend__item">{{< adr-badge color="rose" >}}強制拒絕{{< /adr-badge >}} 不可證偽之黑箱依賴</span>
  <span class="adr-legend__item">{{< adr-badge color="amber" >}}嚴格檢驗{{< /adr-badge >}} 截斷目標與表演性指標</span>
  <span class="adr-legend__item">{{< adr-badge color="green" >}}守恆對帳{{< /adr-badge >}} 邊際效益與真實 TCO</span>
{{< /adr-legend >}}

{{< adr-grid cols="2" >}}

  {{< adr-card title="工程約束 · 形式極限與不可逆承諾" status="強制拒絕" statusColor="rose" meta="architecture · 形式判準" confidence="high" >}}
  系統導入成本隨規模呈二次律發散。在不可判定性下做出全域不可逆承諾具有極高風險；規格的真實效力取決於其誘導之拒絕算子對違規空間的覆蓋率。缺乏形式約束與獨立驗證能力的方案，難以在長期演進中維持穩定。
  {{< /adr-card >}}

  {{< adr-card title="組織流動 · 守恆排程與 WIP 治理" status="嚴格檢驗" statusColor="amber" meta="operations · 作業管理" confidence="high" >}}
  系統交付受在製品（WIP）與交接定義域約束，將填滿工時的「假動作」誤判為實質產能易導致交期發散。警惕被指標截斷的目標函數；以可稽核的留痕機制取代虛應故事的自評，方能看清真實瓶頸。
  {{< /adr-card >}}

  {{< adr-card title="商業對帳 · 採購准入與單位經濟" status="守恆對帳" statusColor="green" meta="procurement · 資本效率" confidence="high" >}}
  評估任何 Vendor 或技術服務時，退出成本與遷移路徑為關鍵指標；穿透 Benchmark 讀數，核算用量增長下的邊際毛利與 Jevons 反彈。將內部膠水工時計入完整 TCO，方能衡量真實的經濟效益。
  {{< /adr-card >}}

  {{< adr-card title="制度權責 · 救濟鏈路與代償清算" status="強制拒絕" statusColor="rose" meta="governance · 制度經濟" confidence="high" >}}
  以擬人化界面掩蓋系統決策，容易消解權責歸屬與制度救濟鏈。必須關注自動化背後由人類警覺度衰退、情緒勞動與殘餘佇列極化所背負的「人工補償四本帳」，審視真實的倫理與制度承載。
  {{< /adr-card >}}

{{< /adr-grid >}}

{{< adr-callout label="梅乾 · 核心界標" >}}
**當虛妄的承諾失去可證偽性，系統必須主動終止；當信任被無度借貸，唯有回歸純粹因果。**

讓已受污染的 context、借來的信任、外部強加的期待與未經檢查的假設，隨著 session 的生命週期一同失效。留下來的不是盲目的樂觀，而是足以拒絕預設選項、退出既有敘事的確定性骨架。
{{< /adr-callout >}}

{{< adr-heading num="02" title="系統邊界與退出代價矩陣" >}}

{{< adr-spec-list >}}
  {{< adr-spec-row key="ZERO-LOCKIN" >}}
  **採購與依賴邊界**：所有技術引進與外部服務採購皆須具備「可無痛抽離（Zero Lock-in）」的退出路徑。若引入依賴的成本遠小於抽離與置換成本，該依賴即具備顯著的架構負債。
  {{< /adr-spec-row >}}

  {{< adr-spec-row key="FLOW-OVER-UTILIZATION" >}}
  **作業與排程管轄**：流程與研發遵循嚴格的流動守恆。追求端到端的前進延遲，避免以填滿工時的假動作阻塞交付管線；實質控制對象應是在製品批量，而非單純的資源利用率。
  {{< /adr-spec-row >}}

  {{< adr-spec-row key="TCO-CONSERVATION" >}}
  **資本與對帳守恆**：自動化所節省的帳面成本，若轉化為下游人員的審查摩擦、對帳工時與人工代償，本質上並未創造盈餘。商業轉換鏈必須衡量全生命週期的真實 TCO。
  {{< /adr-spec-row >}}

  {{< adr-spec-row key="FALSIFIABILITY-GATE" >}}
  **工程與契約驗收**：一份規格、架構或交付契約的真實價值，不等於其文字完備性，而等於其拒絕算子對違規空間的覆蓋率。不能拒絕任何東西的架構，等同不存在。
  {{< /adr-spec-row >}}
{{< /adr-spec-list >}}

