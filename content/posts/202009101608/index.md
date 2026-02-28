---
title: "安裝並嘗試使用Arista ZTPServer"
date: 2020-09-10T16:08:00+08:00
isCJKLanguage: true
draft: false
series: 
  - "網路設備自動化"
tags: 
  - "Arista"
  - "Automation"
  - "ZTP"
  - "EVE-NG"
---

首先用安裝必要的包
```
# apt install git python-pip libyaml-dev isc-dhcp-server
```

ztpserver在安裝過程中會用pip下載所需的套件，這裡已經事先偷看過requirements.txt了
```:requirements.txt
webob
routes
pyyaml
requests
sleekxmpp    # dev only
mock         # dev only
jsonrpclib   # dev only
```

需要留意的是libyaml-dev要記得裝，否則安裝PyYAML的時候會跳出的小錯誤會很容易忽略，後續影響為何還要再觀察
```text {hl_lines=[9, 10]}
Searching for pyyaml
Reading https://pypi.org/simple/pyyaml/
Downloading https://files.pythonhosted.org/packages/64/c2/b80047c7ac2478f9501676c988a5411ed5572f35d1beff9cae07d321512c/PyYAML-5.3.1.tar.gz#sha256=b8eac752c5e14d3eca0e6dd9199cd627518cb5ec06add0de9d32baeee6fe645d
Best match: PyYAML 5.3.1
Processing PyYAML-5.3.1.tar.gz
Writing /tmp/easy_install-DJq89r/PyYAML-5.3.1/setup.cfg
Running PyYAML-5.3.1/setup.py -q bdist_egg --dist-dir /tmp/easy_install-DJq89r/PyYAML-5.3.1/egg-dist-tmp-mJzK1J
In file included from ext/_yaml.c:596:
ext/_yaml.h:2:10: fatal error: yaml.h: No such file or directory
 #include <yaml.h>
```

接下來設定DHCP Server，在/etc/default/isc-dhcp-server中找到以下兩行並我修改
```:/etc/default/isc-dhcp-server
...
DHCPDv4_CONF=/etc/dhcp/dhcpd.conf
...
INTERFACESv4="ens33"
```

注意listen interface，這裡是ens33
```
$ ip link show
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
2: ens33: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
    link/ether 00:0c:29:58:88:13 brd ff:ff:ff:ff:ff:ff
```

再來就是到/etc/dhcp/dhcpd.conf加入下列設定，這次沒用到的部分就先註解掉了

```:/etc/dhcp/dhcpd.conf
...
subnet 192.168.171.0 netmask 255.255.255.0 {
  range 192.168.171.200 192.168.171.205;
  option routers 192.168.171.2;
  #option domain-name-servers <ipaddr>;
  #option domain-name "<org>";

  # Only return the bootfile-name to Arista devices
  class "Arista" {
    match if substring(option vendor-class-identifier, 0, 6) = "Arista";
    # Interesting bits:
    # Relay agent IP address
    # Option-82: Agent Information
    #     Suboption 1: Circuit ID
    #       Ex: 45:74:68:65:72:6e:65:74:31 ==> Ethernet1
    option bootfile-name "http://192.168.171.127:8080/bootstrap";
  }
}
```
DHCP Server告一段落了

接下來是ztpserver，如果用pip的話會比較快速
```
$ pip install ztpserver
```

但這裡貪圖git裡面的各種設定及範本，所以還是用git clone的方式
```
$ git
$ git clone https://github.com/arista-eosplus/ztpserver.git
$ cd ztpserver/
$ python setup.py build
$ python setup.py install
```

安裝完成就可以我啟動了
```
ztps
```

### <p id=2>在ENE-NG上我建立vEOS Switch</p>