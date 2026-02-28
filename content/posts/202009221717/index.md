---
title: "Hugo輸出JSON踩坑紀錄"
date: 2020-09-22T17:17:00+08:00
isCJKLanguage: true
draft: false
series: 
  - "Hugo 實踐筆記"
tags: 
  - "Hugo"
  - "JSON"
  - "Web Development"
---

首先是在config.toml增加下列設定，也就是kind後面放上想輸出的格式，為了簡化所以範例只使用page，其他kind如同home、section、taxonamy或term其實大同小異
```:config.toml
...
[outputs]
  page = ["HTML", "JSON"]
```

run起來會很貼心的警告沒有template
```
WARN 2020/10/11 15:35:48 found no layout file for "JSON" for kind "page": You should create a template file which matches Hugo Layouts Lookup Rules for this combination.
```

接下來就我建立template，因為是page所以template名為single，section的話就是list，以此類推
```
│  404.html
│  index.html
│
├─partials
│     footer.html
│     head.html
│     header.html
│
├─posts
│      single.html
│      single.json ★
│
└─_default
        baseof.html
        baseof.json ★
        list.html
        single.html
```

仿造baseof.html的baseof.json，含result這個key
```:_default/baseof.json
{
    "result" : {{ block "result" .}}{{ end }}
}
```

主角的single.json，如此一來single.json內的block就會包進baseof輸出
```posts/single.json
{{ define "result" }}
{
    "title": "{{ .Title }}",
    "date": "{{ .Date.Format "2006-01-02 15:04" }}",
    "draft": "{{ .Draft }}",
    "categories": 
    [
        {{ range $i, $e := .Params.Categories }}
            {{ if $i }}, {{ end }}"{{ $e }}"
        {{ end }}
    ],
    "tags":
    [
        {{ range $i, $e := .Params.Tags }}
            {{ if $i }}, {{ end }}"{{ $e }}"
        {{ end }}
    ],

    "url": "{{ .Permalink }}"
}
{{ end }}
```

輸出後會在目錄下產生index.json，內容像是這個樣子，如此一來就大功告成了
```:posts/202009221717/index.json
{
    "result" : 
{
    "title": "讓Hugo輸出JSON格式",
    "date": "2020-09-22 17:17",
    "draft": "true",
    "categories": 
    [
        
            "網頁製作"
        
    ],
    "tags":
    [
        
            "Hugo"
        
    ],

    "url": "http://localhost:1313/posts/2020/09/202009221717/"
}

}
```

### <p id=1>踩坑紀錄</p>