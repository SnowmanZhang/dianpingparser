# dianpingparser
该程序用于抓取大众点评指定类目文件信息。This program is used to get the shop infomation of dianping.com

## 程序介绍

该程序用于抓取大众点评特定门店信息，配置简单，抓取便捷，速度尚可。

程序语言：python

包依赖：

```python
import requests
from bs4 import BeautifulSoup
import time
from queue import Queue
import os 
import re
import pickle
```

## 背景简介

由于众所周知的原因，大众点评网[https://www.dianping.com/](https://www.dianping.com/) 的爬取难度正在越来越高，本程序的最深抓取层级为门店基本信息，未进入到shop页面以及其评论页面。但在README.md最后，笔者会谈及如何抓取里面详细信息。

## 文件介绍

1. `citylist.pkl` 文件存放大众点评所有细分城市的列表，元素类以`www.dianping.com\beijing` 。

## 函数介绍

1. citylistqueue = G_citylist("/ch30/g133")
	输入特定门类标志字符串，可由citylist.pkl生成待抓取的一级城市队列`citylistqueue`并返回,队列元素形如(http://www.dianping.com/abaxian/ch10/g132,abaxian,abaxianch10g132)
2. citynumber = G_cityshopcount(citylistqueue,"bar.csv")
	输入上一步生成的待抓取队列，与城市门店页数记录表名，可生成城市页数字典，即每个城市含有的该门类门店一共有多少页，其中大城市超过50页的情况，已自动寻址下一级行政区分区查询并返回。同时本函数将不足50页的城市的第一页资料已自动下载，不与下一步全局下载相冲突。以上工作均封装在本函数内。
3. G_allpage(citynumber)
	输入上一步生成的城市页数字典`citynumber`，下载所有页的相关门店信息。若上一步已下载相关页面，则不再次下载。
4. citylist = convert2shopinfo("raw/citylist/","bar_info_0925.csv")
	该函数指定源文件下载目录，以及最终生成文件名，将所有文件的信息进行提取，生成最终的门店信息表。