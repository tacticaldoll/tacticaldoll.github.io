+++
title = "95% 正確的危險地帶：靜默語意偏差的三層結構"
date = "2026-05-31T23:10:01+08:00"
author = "TTL::0"
draft = false
isCJKLanguage = true
description = "在 AI 協作開發中，明顯錯誤的程式碼很容易被拒絕——語法錯誤有紅線提示，邏輯錯誤會讓測試失敗，型別錯誤會被編譯器攔截。另一端，明確正確的程式碼可以安心接受。真正危險的是介於兩者之間的地帶：程式碼在語法上合法、在多數輸入上行為正確、在 code review 時外觀無異常，但語意與意圖之間存在一個只在特定條件下才暴露的間隙。"
tags = [
    "分析論述", # term:AnalyticalEssay
    "AI 代理人", # term:AiAgent
    "靜默語意偏差", # term:SilentSemanticDeviation
    "確認偏誤", # term:ConfirmationBias
    "版本漂移", # term:VersionDrift
    "依賴契約漂移", # term:DependencyContractDrift
    "隱含契約", # term:ImplicitContract
  ]
[ai_info]
    [ai_info.generation]
        model = "Claude Opus 4.6"
        agent = "Claude Code VSCode Extension 2.1.72"
    [ai_info.refinement]
        model = "Gemini 3.5 Flash"
        agent = "Antigravity IDE 2.0.4"
+++

<!--more-->

## 背景

在 AI 協作開發中，明顯錯誤的程式碼很容易被拒絕——語法錯誤有紅線提示，邏輯錯誤會讓測試失敗，型別錯誤會被編譯器攔截。另一端，明確正確的程式碼可以安心接受。真正危險的是介於兩者之間的地帶：程式碼在語法上合法、在多數輸入上行為正確、在 code review 時外觀無異常，但語意與意圖之間存在一個只在特定條件下才暴露的間隙。

這就是**靜默語意偏差**（Silent Semantic Deviation） <!-- term:SilentSemanticDeviation -->。它比「寫錯」更危險，因為寫錯會觸發防禦機制——紅線、crash、test failure——而 95% 正確的程式碼通過了所有已設好的檢查，因為這些檢查本身也是基於 happy path 設計的。

> [!IMPORTANT]
> **靜默語意偏差** <!-- term:SilentSemanticDeviation --> (Silent Semantic Deviation): 程式碼在語法上合法且多數輸入下正確，但語意與開發意圖之間存在間隙，僅在特定邊界條件下暴露的程式錯誤。 <!-- anchor:SilentSemanticDeviation -->


AI 協作放大了這個問題，有兩個面向。生成端，AI 是統計推測而非查表，它傾向生成「最常見」的寫法，而最常見的寫法恰好高度依賴語言的隱式行為。審查端，AI 生成的程式碼帶有一種「專業外觀」，讓 reviewer 的預設立場從懷疑轉向驗證——審查變成了**確認偏誤**（Confirmation Bias） <!-- term:ConfirmationBias -->的儀式，而不是真正的質疑。

> [!IMPORTANT]
> **確認偏誤** <!-- term:ConfirmationBias --> (Confirmation Bias): 開發或審查人員因程式碼外觀專業而傾向尋找支持其正確的證據，忽略潛在邏輯漏洞的認知偏差。 <!-- anchor:ConfirmationBias -->


靜默語意偏差 <!-- term:SilentSemanticDeviation -->發生在三個層次。每一層的漂移機制不同，可被工具攔截的程度也遞減。從語法的隱式行為，到設計模式的契約灰色地帶，再到領域模型的時間漂移——深度遞增的軸線是：從「能用規則擋」到「只能靠人判斷」到「連問題出現了都不一定會被注意到」。

## 分析

### 表層：語法、版本與依賴——同一寫法在不同環境語意不同

語法層的 95% 問題有三個來源，每一個都涉及語意與語法之間的間隙（semantic gap），但間隙的成因不同。

**語言本身的隱式行為。** 程式語言為了開發便利而引入大量隱式轉換：`||` 在 JavaScript 中同時承擔邏輯運算和預設值兩種語意、truthy/falsy 將任意值隱式轉為布林、`==` 執行隱式型別轉換、optional chaining（`?.`）靜默吞掉 null 而不報錯。這些機制構成一個四條件同時成立的 pattern：語法合法、通常正確、靜默失敗、人眼掃不出來。四條件缺任何一個，問題都會降級成普通 bug。

以 `||` 當預設值為例。`const name = input || 'default'` 在幾乎所有場景下行為正確。但 `const count = input || 10` 在 `input` 為 `0` 時會被覆蓋——而 `0` 是完全合法的計數值。正確的寫法是 nullish coalescing（`??`），但 AI 訓練資料中 `||` 當預設值的出現頻率遠高於 `??`，因為後者是較新的語法。AI 傾向生成它見過最多次的寫法，而最常見的寫法正好依賴 truthy 判斷。

類似的間隙存在於每一個隱式行為中。`&&` 當執行條件看起來是 guard clause，但它是表達式——`list.length && render()` 在 `list` 為空時回傳 `0` 而非 `false`，如果回傳值被使用（而不只是丟棄），語意就偏離了。Optional chaining `obj?.foo?.bar` 把 null 靜默轉為 `undefined`，掩蓋了「這裡本來就不該是 null」的設計問題，讓 bug 在下游才爆發。雙重否定 `if (!notFound)` 在認知上等同於 `if (found)`，但認知負荷讓 reviewer 的視線滑過——而 AI 對「讀起來卡不卡」沒有感覺，因為它不閱讀，它生成。

這些隱式行為共享一個 pattern：都是「語言設計者為了便利而引入的隱式轉換」。每一個「隱式」都是語意與語法之間的間隙。人類靠直覺和上下文填補這個間隙，AI 靠統計頻率填補。95% 的情況下兩者填出同一個答案，但剩下 5% 沒有任何語法層面的訊號告訴你填錯了。

**版本漂移**（Version Drift） <!-- term:VersionDrift -->。 然而，即使把所有隱式行為的 linter 規則都開滿，語法層的 95% 問題仍然存在——因為同一段語法在不同 runtime 版本下可能根本不存在，或者存在但行為不同。

> [!IMPORTANT]
> **版本漂移** <!-- term:VersionDrift --> (Version Drift): 同一段程式碼在不同的 runtime 環境或依賴庫版本下運作時，因底層行為改變而產生的語意或執行差異。 <!-- anchor:VersionDrift -->


`Array.prototype.at()` 在 Node.js 14 會拋出 Type錯誤，在 16.6 以上正常運作。Python 的 `dict | dict` 語法在 3.9 才引入，3.8 是 Type錯誤。AI 的訓練資料跨越多個版本，它不追蹤你的 runtime 版本，生成的程式碼語法完全合法——只是在你的環境中不存在或行為不同。CI 環境通常能攔截「不存在」的情況（直接報錯），但更微妙的是同一 API 在不同版本的行為差異——那不會報錯，只會在特定輸入下產出不同結果。

**依賴契約漂移**（Dependency Contract Drift） <!-- term:DependencyContractDrift -->。 版本漂移 <!-- term:VersionDrift -->至少還有 CI 和 lockfile 作為部分防線。依賴契約漂移 <!-- term:DependencyContractDrift -->幾乎沒有。

> [!IMPORTANT]
> **依賴契約漂移** <!-- term:DependencyContractDrift --> (Dependency Contract Drift): 專案升級或替換第三方套件時，因 API 在邊界輸入或異常處理上的未明示契約差異導致的行為偏差。 <!-- anchor:DependencyContractDrift -->


當專案遷移依賴——例如從 moment.js 換到 dayjs——API 表面幾乎相同，但邊界輸入的行為不同。`dayjs('2024-2-29').isValid()` 回傳 `true`（寬鬆解析），moment 的結果則取決於 strict mode 設定。AI 看到 codebase 使用了新依賴，會用新 API 的語法生成程式碼，語法完全正確——但它不知道兩個函式庫在邊界條件的語意差異。這類差異幾乎不可能被工具攔截，因為沒有 linter 知道兩個不同函式庫的相同方法名稱在語意上有何不同。

三個來源的工具可攔截程度構成一個遞減梯度：語言隱式行為多數有對應的 linter 規則（前提是規則已被啟用且覆蓋完整）、版本漂移 <!-- term:VersionDrift -->部分可透過 CI 和版本鎖定攔截、依賴契約漂移 <!-- term:DependencyContractDrift -->幾乎完全依賴人的領域知識。

**風格作為語意損耗率。** 語法層的 95% 問題還有一個放大器：個人程式風格。Magic number、極簡命名（`d`、`tmp`、`val`）、隱式回傳、條件濃縮（`isValid && !isLocked && hasPermission && execute()`）——這些偏好構成一個語意壓縮（semantic compression）的頻譜。一端是高語意保留：`const SECONDS_PER_DAY = 86400`；另一端是高語意壓縮：直接寫 `86400`。

個人開發時選擇壓縮端完全合理——你就是唯一的讀者，補語意的成本是零。但三件事會讓這個等式翻轉：AI 生成偏好簡潔（訓練資料中 compact idiom 得到更多正面回饋），AI 審查也傾向放過慣用寫法（因為它「看起來像對的」），而當更多人加入時，每多一個讀者，「讀者自己補語意」的失敗率就乘一次。Magic number `86400` 在作者腦中是「一天的秒數」，但沒有人問：這裡要的是 calendar day 還是 24 小時？閏秒？DST？語意壓縮把這些問題藏在一個數字後面，而 AI 和 reviewer 都不會主動展開它。

### 中層：設計模式的契約灰色地帶——結構正確但隱含假設不一致

如果說語法層的 95% 來自語言機制的隱式行為，設計模式層的 95% 來自另一種間隙：**模式被正確使用，但模式內的**隱含契約**（Implicit Contract） <!-- term:ImplicitContract -->沒有被所有參與者——包括 AI——以相同方式理解。**

> [!IMPORTANT]
> **隱含契約** <!-- term:ImplicitContract --> (Implicit Contract): 軟體設計模式中未在型別系統或介面定義中明示，但實作者與呼叫者必須共同遵循的時序、前置條件或狀態假設。 <!-- anchor:ImplicitContract -->


這裡有一個重要的區隔。設計模式本身選擇錯誤——例如 Decorator pattern 在同一介面上疊加水平分類和垂直行為組合（horizontal classification + vertical composition），導致外層 decorator 的行為名稱遮蔽了內層的身份——那是**結構性錯誤**（Structural Error） <!-- term:StructuralError -->。它可以被測試偵測（兩個不同物件回傳相同的 `kind_name()`），也可以被結構重組消除（改用**宣告式**（Declarative） <!-- term:Declarative -->表和獨立的身份列舉）。**結構約束**（Structural Constraint） <!-- term:StructuralConstraint -->能有效窄化這類錯誤的出錯空間，因為**收斂性任務**（Convergent Task） <!-- term:ConvergentTask -->的答案**形狀**（Data Shape） <!-- term:DataShape -->已知，約束在此幫助所有參與者——包括 AI——填入正確的內容。

> [!IMPORTANT]
> **結構性錯誤** <!-- term:StructuralError --> (Structural Error): 軟體架構或設計模式選用不當導致的程式結構缺陷，通常可透過型別約束或結構重組來消除與偵測。 <!-- anchor:StructuralError -->
> **宣告式** <!-- term:Declarative --> (Declarative): 一種編程或治理正規，僅描述預期達成的狀態或目標，將具體執行與自癒細節委派給底層實體或系統。 <!-- anchor:Declarative -->
> **結構約束** <!-- term:StructuralConstraint --> (Structural Constraint): 限制開發自由度與變體形狀的程式碼結構設計，用以消除非法操作空間、收窄錯誤表面。 <!-- anchor:StructuralConstraint -->
> **收斂性任務** <!-- term:ConvergentTask --> (Convergent Task): 答案形狀已知、主要工作為在既定結構內填入內容的開發任務，適合以強結構約束降低出錯率。 <!-- anchor:ConvergentTask -->
> **形狀** <!-- term:DataShape --> (Data Shape): 資料結構或物件所包含的屬性與型別定義，通常由型別系統來描述 <!-- anchor:DataShape -->


95% 危險地帶講的不是這個。這裡的問題是：模式選擇完全正確，程式碼結構無懈可擊，但模式內部的語意契約存在灰色地帶（contract gray zone）。灰色不是因為契約有錯，而是因為契約根本沒被明確表述。

以 Observer pattern 為例。一個 `OrderService` 在 `save()` 之後 `emit('orderCreated', order)`，結構上完美。但「saved」的語意是什麼？是 ORM `flush()` 完成（但 transaction 尚未 commit）？還是 DB commit 完成（資料已持久化）？如果某個 listener 在收到事件後對同一筆 order 做查詢，在 transaction 尚未 commit 的情況下，查詢結果取決於資料庫的隔離層級設定。95% 的場景下這不是問題——多數 listener 不會立即重查資料庫，或者 transaction 在 emit 前就已經 commit。但在高併發場景下，這個未定義的時機契約會導致間歇性失敗——最難 debug 的那種。

AI 生成 Observer pattern 時不會犯語法錯誤。它產出的結構完美、命名專業、event handler 實作整齊。問題在於 AI 對「saved 事件的**語意邊界**（Semantic Boundary） <!-- term:SemanticBoundary -->」會根據訓練資料的統計分佈推測——而訓練資料中大多數範例的 emit 確實在 commit 之後。但你的 codebase 可能不是。

> [!IMPORTANT]
> **語意邊界** <!-- term:SemanticBoundary --> (Semantic Boundary): 模組或類別在空間維度上定義其職責與封裝邊界的概念 <!-- anchor:SemanticBoundary -->


類似的契約灰色地帶存在於每一個常用模式中。下表列出幾個代表性案例，每一個的結構都正確，問題都在未被表達的假設：

| 模式 | 結構正確的 95% | 未定義的契約 | 5% 的爆發條件 |
|------|--------------|------------|-------------|
| **資源庫**（Repository） <!-- term:Repository --> | `find()` 介面完整，有 cache 有 invalidation | cache 行為是對外承諾還是內部細節？caller 能否假設每次 `find()` 都回資料庫？ | 兩個 caller 對 cache 行為做了不同假設，各自測試都通過 |
| Strategy | 多個策略實作同一個 interface，可替換 | **前置條件**（Prerequisite） <!-- term:Prerequisite -->不對稱——A 不需要前置條件 <!-- term:Prerequisite -->、B 需要 auth context、C 需要 auth + rate limit state，但 interface 簽名統一抹平了差異 | AI 新增 Strategy D，從現有實作的統計分佈推測前置條件 <!-- term:Prerequisite --> |
| Middleware | 每個 middleware 職責清晰，單獨可測 | 順序是隱式契約——middleware B 依賴 middleware A 的副作用（例如在 request 上附加 user 物件），但依賴關係沒有宣告 | 新 middleware 插入位置不對，前面的 middleware 尚未執行 |
| Builder | 鏈式呼叫語法流暢，每個方法型別安全 | 哪些欄位組合是非法的？ | `build()` 只在 runtime 才拋出例外，組合約束不在型別系統中 |

> [!IMPORTANT]
> **資源庫** <!-- term:Repository --> (Repository): 存放專案原始碼、版本歷史紀錄與配置文件的中心儲存庫。 <!-- anchor:Repository -->
> **前置條件** <!-- term:Prerequisite --> (Prerequisite): 執行某項開發活動之前必須滿足的準備工作或狀態。 <!-- anchor:Prerequisite -->


這些案例的共同結構是：程式碼表達了模式的結構契約（interface、方法簽名、繼承關係），但沒有表達模式的語意契約（時機、前置條件 <!-- term:Prerequisite -->、責任歸屬、合法組合）。結構契約可以被編譯器和型別系統驗證。語意契約只存在於設計者的腦中——或者更常見的情況是，連設計者都沒有顯式想過。

這就是為什麼結構約束 <!-- term:StructuralConstraint -->在這一層失效。結構約束 <!-- term:StructuralConstraint -->的力量在於「讓非法操作在結構上不可能」，但當模式本身的結構是正確的，「非法」的定義不在結構層面——它在語意層面，而語意無法被結構完整表達。

### 深層：領域模型漂移——邏輯在寫下的那一刻是對的，但世界變了

最深的一層 95% 問題與語法和結構都無關。它發生在程式碼忠實反映了某一時刻的領域知識，但那個時刻的領域知識已經不再成立。

一個折扣計算 `order.subtotal * (1 - discount.rate)` 完全正確——直到業務規則改成「折扣不能套用在已經促銷的品項上」。一個權限檢查 `user.role === 'admin'` 完全正確——直到組織引入了跨部門的委派授權機制。一個地址驗證 `if (zipCode.length === 5)` 完全正確——直到產品擴展到使用不同郵遞區號格式的市場。

這層的 95% 最陰險，因為三個條件同時成立。第一，程式碼在被寫下的那一刻是 100% 正確的——不是「差不多對」，而是完全符合當時的需求。第二，領域知識的改變發生在程式碼之外——在會議室、在法規文件、在客戶需求中——程式碼不會自動跟著漂移。第三，AI 生成新程式碼時參考的是既有 codebase，它看到既有的折扣計算方式就會延續同樣的模式——而這個「一致性」恰好強化了 reviewer 的信心：「這段新 code 跟我們原來的做法一樣，所以應該是對的。」

「一致性等於正確性」的假設在領域穩定時成立。但領域在漂移時，一致性反而成了陷阱——新程式碼忠實地複製了一個已經過時的假設，而且做得越完美越難被發現。

## 省思

### 三層的統一結構

三層問題的表象不同，但共享同一個底層結構：**表面相同、底層漂移，且漂移的發生不會產生任何主動訊號。**

語法層的漂移載體是 runtime 環境和依賴函式庫——同一行程式碼在不同版本下語意不同。模式層的漂移載體是參與者的心智模型——同一個 interface 在不同開發者腦中代表不同的契約。領域層的漂移載體是業務規則本身——同一段邏輯在不同時間點對應不同的需求。

三者的深度遞增不只是「更難擋」，而是**可觀測性**（Observability） <!-- term:Observability -->的遞減。語法層的漂移至少有可能被工具偵測——如果你知道要找什麼。模式層的漂移在程式碼上完全不可見——需要去讀設計文件或問原作者。領域層的漂移連「知道要問」都不一定做得到——因為你可能根本不知道業務規則已經改了。

> [!IMPORTANT]
> **可觀測性** <!-- term:Observability --> (Observability): 軟體系統或程式邏輯的運作狀態被外部工具或監控機制感知、偵測與度量的難易程度。 <!-- anchor:Observability -->


### AI 在每一層都是放大器

AI 在三層問題上扮演的角色不只是「可能犯錯」——它系統性地放大了每一層的漂移風險，而且放大機制各不相同。

在語法層，AI 的統計傾向讓它偏好最常見的寫法，而最常見的寫法通常是歷史最久、隱式行為最多的那一種。在模式層，AI 對契約的理解來自訓練資料中大量範例的統計分佈——它填入的是「最可能的契約」而非「你的 codebase 實際使用的契約」。在領域層，AI 只能看到程式碼中已被表達的領域知識，看不到尚未被更新到程式碼中的業務規則變更。

但更深層的放大效應在審查端。當 reviewer 面對 AI 生成的程式碼，它的「專業外觀」觸發了一種認知捷徑：既然看起來像專家寫的，大概就是對的。審查從質疑模式切換到確認模式——而這正是 95% 正確最需要被質疑卻最容易被放過的時刻。

### 工具防線的天花板

每一層都有對應的工具防線，但防線的覆蓋率隨深度遞減。

語法層有 linter、type checker、靜態分析。它們能擋住已經被寫成規則的 pattern——但規則的完備性取決於「是否有人想到這個問題並寫了規則」。ESLint 有 `no-eq-null` 規則來攔截 `== null`，但沒有「你的 dayjs 跟之前的 moment 在日期解析寬鬆度上不同」的規則。版本漂移 <!-- term:VersionDrift -->有 CI 和 lockfile 作為部分防線，但依賴契約漂移 <!-- term:DependencyContractDrift -->幾乎沒有工具能覆蓋。

模式層有設計文件、架構決策紀錄（**架構層**（Architecture） <!-- term:Architecture --> Decision Record, ADR）、interface 文件化。這些機制能將隱含契約 <!-- term:ImplicitContract -->顯式化——但需要有人先意識到契約是隱含的，然後花時間把它寫下來。在實務中，契約通常要等到出問題時才被意識到和文件化——那時 95% 已經造成了損害。

> [!IMPORTANT]
> **架構層** <!-- term:Architecture --> (Architecture): 規格文件中用以客觀記錄系統「實際在做什麼」的事實陳述層。 <!-- anchor:Architecture -->


領域層幾乎沒有工具防線。持續跟領域專家對齊的紀律是唯一的防禦——但這不是工具，而是組織行為，也是最難 scale 的防線。

## 結論

靜默語意偏差 <!-- term:SilentSemanticDeviation -->的危險不在於它不可解決，而在於它的解決方案在每一層都不同，且隨深度遞增，解決方案越來越依賴人的判斷而非工具的規則。

語法層的 95% 可以透過更嚴格的語言特性和工具鏈部分緩解——但前提是知道要擋什麼，而版本漂移 <!-- term:VersionDrift -->和依賴契約漂移 <!-- term:DependencyContractDrift -->已經超出靜態分析的能力範圍。模式層的 95% 需要將隱含契約 <!-- term:ImplicitContract -->顯式化——不是更多的程式碼，而是更多的文字，說明「這個 interface 的使用者應該假設什麼、不應該假設什麼」。領域層的 95% 沒有技術解——它需要持續的領域對齊紀律，而這正是最容易在交期壓力下被犧牲的東西。

三層共同指向一個更根本的認知：**AI 協作沒有讓審查變得不重要，而是改變了審查的本質。** 過去的審查問的是「這段程式碼有沒有 bug」——語法對不對、邏輯通不通、edge case 有沒有處理。這些問題可以被機械化，也已經大量被工具化了。現在的審查需要加上一個新維度：「這段程式碼的隱含假設是否跟現在的 context 一致」——寫法跟環境版本匹配嗎、契約跟其他使用者的理解一致嗎、邏輯跟當前的業務規則對齊嗎。這個維度無法被機械化，因為它的答案不在程式碼裡——而 95% 正確的程式碼最擅長的，就是讓這個問題看起來不需要被問。