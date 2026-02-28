---
title: "使用cephadm部屬Ceph Cluster"
date: 2020-11-10T16:52:00+08:00
isCJKLanguage: true
draft: false
series: 
  - "系統架構與儲存"
tags: 
  - "Ceph"
  - "Storage"
  - "Linux"
---

首先安裝cephadm執行時需要的python3與校時的chrony
```
# yum install -y python3 chrony
```

安裝完啟用chrony
```
# systemctl start chronyd
# systemctl enable chronyd
```

Ceph的daemon是以container形式存在於host上，所以需要docker或是podman，否則會出現這樣的錯誤
```
ERROR: Unable to locate any of ['podman', 'docker']
```

這裡的範例是安裝docker(需增加repo)
```
# yum install -y yum-utils
# yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
# yum install -y docker-ce docker-ce-cli containerd.io
```

安裝完記得我啟動
```
# systemctl start docker
# systemctl enable docker
```

增加hosts
```
[root@node1 ~]# cat >> /etc/hosts <<EOF
> 192.168.149.131 node1
> 192.168.149.132 node2
> 192.168.149.133 node3
> EOF
```

## 1. 我建立Cluster