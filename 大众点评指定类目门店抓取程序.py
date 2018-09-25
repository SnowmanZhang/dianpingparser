# -*- coding: utf-8 -*-
"""
Created on Sun Sep 16 10:41:43 2018

@author: Machenike
"""

import requests
from bs4 import BeautifulSoup
import time
from queue import Queue
import os 
import re
import pickle

headers_citylist = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:62.0) Gecko/20100101 Firefox/62.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    'Accept-Encoding': 'gzip, deflate',
    'Referer': 'http://www.dianping.com/',
    'Cookie': 'cy=1; cye=beijing;  \
               _lxsdk_cuid=165fc135be1c8-0d9153c3c493f7-36664c08-144000-165fc135be1c8; \
               _lxsdk=165fc135be1c8-0d9153c3c493f7-36664c08-144000-165fc135be1c8; \
               _hc.v=e751418f-d068-1ba6-0986-117072db96a1.1537532452; \
               s_ViewType=10; \
               _lx_utm=utm_source%3DBaidu%26utm_medium%3Dorganic; \
               _lxsdk_s=%7C%7C0',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0'       
    }

def G_proxy():
    url = 'http://webapi.http.zhimacangku.com/getip?num=1&type=1&pro=&city=0&yys=0&port=1&time=1&ts=0&ys=0&cs=0&lb=1&sb=0&pb=5&mr=1&regions='
    while True:
        try:
            req = requests.get(url)
        except Exception as err:
            print(err)
            print("获取代理地址发生错误")
        if '秒后再次请求' in req.text:
            time.sleep(1)
        else:
            content = req.text.replace("\r","").replace("\n","")
            proxy = {"http":content
                     }
            return proxy   

def citycount(requrl,cityname,proxy):
    '''
    输入:   单一城市的某一门类数据 requrl.  形如http://www.dianping.com/abaxian/ch10/g132p2
            该城市名称cityname   形如  beijing
            代理ip地址 proxy     形如  123.123.123.12:83712
    返回:   访问内容
    '''
    headers_citylist['Cookie'].replace("beijing",cityname)
    content = requests.get(requrl,headers=headers_citylist,proxies=proxy,timeout=30).text
    headers_citylist['Cookie'].replace(cityname,"beijing")
    return content

def W2citynumber(unit,number,logfile,tempcount=""):
    '''
    输入:   请求页面基本信息字符串unit ,形如 http://www.dianping.com/abaxian/ch10/g132p2
            该页面拥有的页数(如探查潍坊市咖啡馆数量页面，则一共有8页，number=8)
            页面源码tempcount(number = 0时为空)
    '''
    with open("raw/"+logfile,"a",encoding="utf8") as f:
        f.write(unit+'\t'+str(number)+'\n')
    if number != 0:
        with open("raw/citylist/"+unit+'.html',"w",encoding="utf8") as f:
            f.write(tempcount)
            
def G_allpage(citynumber):
    '''
    输入:   城市页码字典citynumber  形如 key = http://www.dianping.com/abaxian/ch10/g132
                                        value = 4
    输出:   下载字典中所有城市页面(程序结束)
                                        
    '''
    parserlist = Queue()
    countproxy = 0
    proxy = G_proxy()
    hadlist = os.listdir("raw\citylist")
    for k in citynumber:
        maxnumber = int(citynumber[k])
        i = 1
        while i <= maxnumber:
            requrl = k + 'p' + str(i)
            filename = requrl.replace("http://www.dianping.com/","").replace("/","")
            if filename+'.html' not in hadlist:
                parserlist.put((requrl,filename))
            else:
                print("had get file %s"%filename)
            i += 1

    print("prepare to parser")
    while parserlist.empty() is not True:
        unit = parserlist.get()
        requrl = unit[0]
        filename = unit[1]
        try:
            tempcount = citycount(requrl,"beijing",proxy)
        except Exception as e:
            print("error 1 %s ,now the len of queue is %s"%(filename,parserlist.qsize()))
            proxy = G_proxy()
            parserlist.put(unit)
            continue
        BSobj = BeautifulSoup(tempcount,"lxml")
        if '验证中心' in BSobj.title.text:
            print("遭遇验证中心%s"%filename)
            countproxy += 1
            if countproxy > 4:
                proxy = G_proxy()
                countproxy = 0
            parserlist.put(unit)
            continue
        else:
            with open("raw/citylist/"+filename+'.html',"w",encoding="utf8") as f:
                f.write(tempcount)


def G_citylist(charstr):
    '''
    产生特定目录的Queue对象。元素形如(http://www.dianping.com/abaxian/ch10/g132,abaxian,abaxianch10g132)
    '''
    with open("citylist.pkl","rb") as f:  #读取城市列表
        linklist = pickle.load(f)
    index = 0
    while index < len(linklist):
        linklist[index] = ('http://' + linklist[index] + charstr,linklist[index].replace("www.dianping.com/",""),linklist[index].replace("www.dianping.com/","")+charstr.replace("/",""))
        index += 1
    citylistqueue = Queue()
    for unit in linklist:
        citylistqueue.put(unit)
    return citylistqueue
    

def G_cityshopcount(citylistqueue,logfile):
    '''
    输入： Queue实例，队列元素形如
    为该函数给出一个QUEUE对象，元素形如(http://www.dianping.com/abaxian/ch10/g132,abaxian,abaxianch10g132)
        可返回citynumber字典,字典记录了每个城市该类目的页码数量
    '''
    countproxy = 0
    citynumber = {}
    proxy = G_proxy()
    while citylistqueue.empty() is not True:
        unit = citylistqueue.get()   
        requrl = unit[0] #形如http://www.dianping.com/abaxian/ch10/g132p1
        cityname = unit[1] #形如abaxian
        filename = unit[2] #形如 abaxianch30g134
        if len(unit) > 3:
            flag = False
        else:
            flag = True
        try: #尝试获取该链接内容(即该地区首页内容)
            tempcount = citycount(requrl,cityname,proxy)
        except Exception as e:
            print("error 1 %s ,now the len of queue is %s"%(filename,citylistqueue.qsize()))
            proxy = G_proxy()
            citylistqueue.put(unit)
            continue
        
        
        if '没有找到符合条件的商户' not in tempcount:
            try:
                BSobj = BeautifulSoup(tempcount,"lxml")
                if '验证中心' in BSobj.title.text:
                    print("遭遇验证中心%s"%filename)
                    countproxy += 1
                    if countproxy > 4:
                        proxy = G_proxy()
                        countproxy = 0
                    citylistqueue.put(unit)
                    continue
            except Exception as e:
                print("error 2 %s"%filename)
                citylistqueue.put(unit)
                continue
            try:
                if BSobj.find_all("a","PageLink")[-1].text == '50':
                    if flag:
                        W2citynumber(filename,50,logfile,tempcount)  #首先将filename 写入文件
                        with open("raw/citylist/"+filename+'.html',"r",encoding="utf8") as f:
                            BSobj = BeautifulSoup(f.read(),"lxml")
                        regionnav = BSobj.find("div",id="region-nav")
                        for singlehref in regionnav.find_all("a"):    
                            tempunit = (singlehref['href'],cityname,singlehref['href'].replace("http://www.dianping.com/","").replace("/",""),False)
                            citylistqueue.put(tempunit)
                        os.remove("raw/citylist/"+filename+'.html')
                    else:
                        citynumber[requrl] = 50
                        W2citynumber(filename+'p1',50,logfile,tempcount)
                else:
                    citynumber[requrl] = int(BSobj.find_all("a","PageLink")[-1].text)
                    W2citynumber(filename+'p1',citynumber[requrl],logfile,tempcount)
            except IndexError:
                print("INDEXERROR")
                citynumber[requrl] = '1'
                W2citynumber(filename+'p1',1,logfile,tempcount)  #形如abaxianch10g132p1
                continue
            except Exception as e:
                print(e)
                print("error 3 %s"%filename)
                citylistqueue.put(unit)
                continue
            time.sleep(0.1)
        else:#若无店面，则仅记录该城市
            W2citynumber(filename,0,logfile)
    return citynumber

def convert2shopinfo(folder,OUTPUTname):
    '''给定文件夹路径，解析出该文件夹内所有文件的店面信息,存入OUTPUTname文件'''
    citylist = []
    filelist = os.listdir(folder)
    for filename in filelist:
        try:
            with open(folder+filename,"r",encoding="utf8") as f:
                BSobj = BeautifulSoup(f.read(),"lxml")
        except Exception as e:
            print(filename)
            continue
        try:
            shopinfo = BSobj.find("div",id="shop-all-list").find_all("li")
        except:
            print(filename)
            continue
        cityid = re.findall("cityId.*?(\d*?)',",BSobj.find("script").text)[0]
        cityname = re.findall("cityChName..*?'(.*?)',",BSobj.find("script").text)[0]
        for unit in shopinfo:
            unitid = unit.find("div","tit").find("a")['href'][29:]
            unitname = unit.find("div","tit").find("h4").text
            try:
                unitcommit = unit.find("div","comment").find("b").text
            except:
                unitcommit = '0'
            citylist.append((unitid,unitname,unitcommit,cityid,cityname))
            with open(OUTPUTname,"a",encoding="utf8") as f:
                f.write('\t'.join((unitid,unitname,unitcommit,cityid,cityname))+'\n')
    return citylist
            


        

if __name__ == '__main__':
    citylistqueue = G_citylist("/ch30/g133")
    citynumber = G_cityshopcount(citylistqueue,"bar.csv")
    G_allpage(citynumber)
    citylist = convert2shopinfo("raw/citylist/","bar_info_0925.csv")
    
    
