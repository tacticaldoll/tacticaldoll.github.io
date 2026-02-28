---
title: "使用LINE發送Node-RED爬蟲資料"
date: 2021-01-05T14:17:00+08:00
isCJKLanguage: true
draft: false
series: 
  - "網路設備自動化"
tags: 
  - "Node-RED"
  - "LINE"
  - "Automation"
  - "API"
---

首先進入<a href="https://developers.line.biz/" target="_blank">LINE Developers</a>，登入至console後我建立provider，並在這個provider我建立一個channel，建立完成後取"Basic"中的user id
![](1.png)

與"Messaging API"中的Channel access token

![](2.png)

測試就像這樣，來個哈囉沃德吧！POST Content是JSON，content中的"to"填入的是剛才的user id，而header中的Authorization: Bearer token就是剛才的Channel access token
```
$ curl -X POST https://api.line.me/v2/bot/message/push \
    -H 'Content-Type: application/json' \ 
    -H 'Authorization: Bearer yU5C4Y5Jfihkn/c5lzIA0w....' \
    -d '{"to":"U0e9aa2....","messages":[{"type":"text","text":"Hello, world!"}]}'
```

response是個空白的JSON就代表成功了
```
{}
```

LINE有加自己的Channel就能看到剛才的推送訊息，如此一來就完成一將近一半了

![](3.png)

### 使用Node-RED操作LINE Messaging API