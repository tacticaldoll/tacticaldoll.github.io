---
title: "將Zeek logs傳送至ELK Stack"
date: 2021-04-01T08:56:00+08:00
isCJKLanguage: true
draft: false
series: 
  - "系統架構與儲存"
tags: 
  - "Zeek"
  - "ELK"
  - "Logstash"
  - "Monitoring"
---

參考官方<a href="https://docs.zeek.org/en/current/get-started.html" target="_blank">Zeek quick start</a>，接著從安裝開始，環境是CentOS 7，所以用7的repo，這樣比從source安裝來得輕鬆容易
```
# cd /etc/yum.repos.d/
# wget https://download.opensuse.org/repositories/security:zeek/CentOS_7/security:zeek.repo
# yum -y install zeek
```

安裝下來的版本是4.0.0
```
[root@node1 ~]# zeek -v
zeek version 4.0.0
```

接下來用shell示範，首先暫時加入PATH以利接下來操作
```
[root@node1 ~]# export PATH=/opt/zeek/bin:$PATH
```

接著進入操作目錄，結構大概是這樣，需要使用的binary file都在./bin，而./logs將會是之後輸出的東西
```
[root@node1 ~]# cd /opt/zeek
[root@node1 ~]# tree -d
.
├── bin
│   └── broctl -> /opt/zeek/lib/zeek/python/zeekctl
├── etc
│   └── zkg
├── include
│   ├── binpac
│   ├── broker
│   │   ├── alm
│   │   ├── detail
│   │   └── mixin
...
```

接下來更改etc/node.cfg，將interface改為實際的interface
```:etc/node.cfg
# Example ZeekControl node configuration.
#
# This example has a standalone node ready to go except for possibly changing
# the sniffing interface.

# This is a complete standalone configuration.  Most likely you will
# only need to change the interface.
[zeek]
type=standalone
host=localhost
interface=ens33
```

像目前個人環境是ens33
```
[root@node1 zeek]# ip link show
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
2: ens33: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
    link/ether 00:0c:29:29:c1:3d brd ff:ff:ff:ff:ff:ff
```

接著install→start就開始運作了
```
[root@node1 zeek]# zeekctl 
Warning: zeekctl node config has changed (run the zeekctl "deploy" command)

Welcome to ZeekControl 2.3.0

Type "help" for help.

[ZeekControl] > install
removing old policies in /opt/zeek/spool/installed-scripts-do-not-touch/site ...
removing old policies in /opt/zeek/spool/installed-scripts-do-not-touch/auto ...
creating policy directories ...
installing site policies ...
generating standalone-layout.zeek ...
generating local-networks.zeek ...
generating zeekctl-config.zeek ...
generating zeekctl-config.sh ...
[ZeekControl] > start
starting zeek ...
creating crash report for previously crashed nodes: zeek
[ZeekControl] > 
```

接下來進行測試，像我在local用`curl www.gogole.com`來試著產生流量，就會輸出log
```:/opt/zeek/logs/current/conn.log 
#separator \x09
#set_separator  ,
#empty_field    (empty)
#unset_field    -
#path   conn
#open   2021-04-01-17-00-10
#fields ts      uid     id.orig_h       id.orig_p       id.resp_h       id.resp_p       proto   service        duration        orig_bytes      resp_bytes      conn_state      local_orig      local_resp    missed_bytes     history orig_pkts       orig_ip_bytes   resp_pkts       resp_ip_bytes   tunnel_parents
#types  time    string  addr    port    addr    port    enum    string  interval        count   count string   bool    bool    count   string  count   count   count   count   set[string]
1617267600.372464       CHSiZd4C1O4cshYqNe      192.168.149.131 49304   8.8.8.8 53      udp     dns   0.007085 0       46      SHR     T       F       0       Cd      0       0       1       74      -
1617267600.387133       CyUiG03tFWAlDH9oLh      192.168.149.131 34398   8.8.8.8 53      udp     dns   0.004931 0       62      SHR     T       F       0       Cd      0       0       1       90      -
1617267600.406175       CdlOnF2L8iphj6bKuc      192.168.149.131 50972   8.8.8.8 53      udp     dns   0.004991 0       44      SHR     T       F       0       Cd      0       0       1       72      -
1617267600.418985       Cp20ej3GjcOji8Z91a      192.168.149.131 44319   8.8.8.8 53      udp     dns   0.004332 0       103     SHR     T       F       0       Cd      0       0       1       131     -
1617267600.429460       CtTxvF14IJDFfhdUv1      192.168.149.131 38851   8.8.8.8 53      udp     dns   0.006173 0       84      SHR     T       F       0       Cd      0       0       1       112     -
1617267073.050473       ChR0fl3uIxHQhxbx7i      192.168.149.1   3467    192.168.149.131 22      tcp   -        249.904010      2880    0       OTH     T       T       0       
```

特定protocol的也有
```:logs/current/http.log 
#separator \x09
#set_separator  ,
#empty_field    (empty)
#unset_field    -
#path   http
#open   2021-04-01-11-01-23
#fields ts      uid     id.orig_h       id.orig_p       id.resp_h       id.resp_p       trans_depth     method  host    uri     referrer        version user_agent      origin  request_body_len        response_body_len      status_code      status_msg      info_code       info_msg        tags    username        password        proxied orig_fuids      orig_filenames  orig_mime_types resp_fuids      resp_filenames  resp_mime_types
#types  time    string  addr    port    addr    port    count   string  string  string  string  string  string  string  count   count   count   string  count   string  set[enum]       string  string  set[string]     vector[string]  vector[string]  vector[string]  vector[string]  vector[string]  vector[string]
1617246083.475994       CVQf6b1T0kF62QfLGb      192.168.149.131 58566   172.217.160.100 80      1       -       -       -       -       1.1     -       -       0       370     302     Found   -       -       (empty) -      -        -       -       -       -       F10mzw4W7rnzD1ZIF2      -       text/html
1617246110.589529       CszGkz1WuedRAcY4cb      192.168.149.131 58568   172.217.160.100 80      1       -       -       -       -       1.1     -       -       0       370     302     Found   -       -       (empty) -      -        -       -       -       -       FXO4sMNQ5bca6pMWd       -       text/html
```

```:logs/current/dns.log 
#separator \x09
#set_separator  ,
#empty_field    (empty)
#unset_field    -
#path   dns
#open   2021-04-01-11-00-11
#fields ts      uid     id.orig_h       id.orig_p       id.resp_h       id.resp_p       proto   trans_id        rtt     query   qclass  qclass_name     qtype   qtype_name      rcode   rcode_name      AA      TC      RD     RA       Z       answers TTLs    rejected
#types  time    string  addr    port    addr    port    enum    count   interval        string  count   string  count   string  count   string  bool    bool    bool    bool    count   vector[string]  vector[interval]       bool
1617246000.367800       CYZscL1WZgToo0aFF2      192.168.149.131 56696   8.8.8.8 53      udp     49314   -       -       -       -       -       -       3       NXDOMAIN        F       F       F       F       0       -      -        T
1617246000.379853       C9R48F26JuUAtrJJLe      192.168.149.131 36461   8.8.8.8 53      udp     48755   -       -       -       -       -       -       3       NXDOMAIN        F       F       F       F       0       -      -        F
1617246000.390934       Cp9FG4EHDInTZ6HXi       192.168.149.131 50133   8.8.8.8 53      udp     47126   -       -       -       -       -       -       3       NXDOMAIN        F       F       F       F       0       -      -        T
1617246000.403496       Cdx4KT2Elnhilucw9i      192.168.149.131 53514   8.8.8.8 53      udp     4357    -       8.8.8.8.in-addr.arpa    -       -       -       -       0       NOERROR F       F       F       T       0      dns.google       21259.000000    F
1617246000.416114       CSxB3p2gsvyQqYYltj      192.168.149.131 44751   8.8.8.8 53      udp     43509   -       36.200.58.216.in-addr.arpa      -       -       -       -       0       NOERROR F       F       F       T      0        tsa01s08-in-f4.1e100.net,tsa01s08-in-f36.1e100.net      20406.000000,20406.000000       F
1617246000.427219       CrEBdC1JfzdCrhaRT9      192.168.149.131 37798   8.8.8.8 53      udp     24914   -       -       -       -       -       -       3       NXDOMAIN        F       F       F       F       0       -      -        T
1617246083.436974       CigcJd2IFtMv5YXQi2      192.168.149.131 50755   8.8.8.8 53      udp     19516   -       www.google.com  -       -       -       -       0       NOERROR F       F       F       T       0       2404:6800:4012:1::2004  180.000000      F
1617246083.436940       CigcJd2IFtMv5YXQi2      192.168.149.131 50755   8.8.8.8 53      udp     47407   -       www.google.com  -       -       -       -       0       NOERROR F       F       F       T       0       172.217.160.100 211.000000      F
1617246110.557257       CqJ2n8WPwuhPaVVNl       192.168.149.131 37226   8.8.8.8 53      udp     7595    -       www.google.com  -       -       -       -       0       NOERROR F       F       F       T       0       2404:6800:4012:1::2004  153.000000      F
1617246110.557297       CqJ2n8WPwuhPaVVNl       192.168.149.131 37226   8.8.8.8 53      udp     16544   -       www.google.com  -       -       -       -       0       NOERROR F       F       F       T       0       172.217.160.100 184.000000      F
```

<h2 id=2>準備ELK Stack</h2>