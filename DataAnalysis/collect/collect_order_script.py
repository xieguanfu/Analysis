#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author:  zhoujiebing
@contact: zhoujiebing@maimiaotech.com
@date: 2012-08-25 16:18
@version: 0.0.0
@license: Copyright alibaba-inc.com
@copyright: Copyright alibaba-inc.com

"""
import re
import sys
import urllib2
import datetime
import socket
import random
import time
if __name__ == '__main__':
    sys.path.append('../../')

from DataAnalysis.conf.settings import CURRENT_DIR
from DataAnalysis.analysis.wxb_tools import login 
from CommonTools.ztc_order_tools import ZtcOrder, SOFT_CODE
from CommonTools.logger import logger
from CommonTools.send_tools import send_sms, DIRECTOR
socket.setdefaulttimeout(10)
def operate_exception(MAX_RETRY_TIMES=3):
    def _wrapper_func(func):
        def _wraped_func(*args,**kwargs):
            retry_time=0
            res=None
            next=True
            while next:
                retry_time+=1
                if retry_time>MAX_RETRY_TIMES:
                    break
                try:
                    res=func(*args,**kwargs)
                    next=False
                except socket.timeout:
                    retry_time+=1
                except Exception,e:
                    retry_time+=1
            return res
        return _wraped_func
    return _wrapper_func
class ZtcOrderCollect(ZtcOrder):
    
    def __init__(self, today):
        #获取所有直通车软件
        self.id_data = SOFT_CODE.items()
        self.today = today
        self.yesterday = self.today - datetime.timedelta(days=1)
        self.id_name = ''
        self.order_dict = ZtcOrder.get_store_order(self.id_data, CURRENT_DIR, self.today)
    
    def write_order(self):
        file_name = ZtcOrder.get_file_name(CURRENT_DIR, self.today)
        file_obj = file(file_name, 'w')
        for key in self.order_dict:
            soft_order_dict = self.order_dict[key]
            for order in soft_order_dict.values():
                outer = str(key)+','+order['nick']+','+order['version']+','+order['deadline']+','+order['payTime']+'\n'
                file_obj.write(outer)
        file_obj.close()

    def get_order(self):

        _tb_token="e531e38e35e3e" 
        #agent_nick="麦苗科技营销" #代理账号,如果此账号不为空则自动切换到此账号
        #ztc_dict=login("麦苗科技001","TestMaimiao2014#",_tb_token,agent_nick=None,is_tp = True)
        #if not ztc_dict:
        #    print '%s order get failed because login failed' % datetime.datetime.now()
        #    return
        for id_info in self.id_data:
            self.id_name = id_info[0]
            id = id_info[1]
            print 'id_name: ',self.id_name
            store_order = self.order_dict[self.id_name]
            order_list = self.get_order_by_soft(id, str(self.today))
            print 'order_list len: ',len(order_list)
            for order in order_list:
                key = ZtcOrder.hash_ztc_order(order)
                if not store_order.has_key(key):
                    store_order[key] = order


    @operate_exception(10)
    def getWebPage(self, url):
        agent_1 = '''Mozilla/5.0 (Windows NT 6.1; rv:33.0) Gecko/20100101 Firefox/33.0'''
        agent_2 = '''Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36'''
        agent_3 = '''Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36 SE 2.X MetaSr 1.0'''
        agent_4 = '''Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1650.63 Safari/537.36'''
        agent_list =[agent_1,agent_2,agent_3,agent_4]
        if random.randint(1,5) in [2,5]:
            sleep_time = random.sample([0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1,1.2,1.3,1.5,1.6,2,2.3,2.6,3,4],1)[0]
            time.sleep(sleep_time)
        request = urllib2.Request(url)
        request.add_header('User-Agent', random.sample(agent_list,1)[0])
        wp = urllib2.urlopen(url=request, timeout=5)
        #wp = urllib2.urlopen(url)
        content = wp.read()
        return content
    
    def getUrl(self, id, day):
        url = 'http://fuwu.taobao.com/serv/rencSubscList.do?serviceCode=' + id + '&currentPage=' + day + '&pageCount=' + day+'&tracelog=search&scm=&ppath=&labels='
        return url
    
    def get_order_by_soft(self, id, today):
        """
        order:{'nick': '\xe4\xb9\x89**\xe5\x9f\x8e', 'version': '\xe9\x95\xbf\xe5\xb0\xbe\xe7\x89\x88', 'deadline': '3\xe4\xb8\xaa\xe6\x9c\x88', 'isB2CSeller': '0', 'rateSum': '2_4', 'rateNum': '', 'payTime': '2013-03-05 15:16:58', 'isTryoutSubed': 0, 'isPlanSubed': '0'}
        """
        order_list = []
        for page in range(1,16):
            flag = False
            url = self.getUrl(id, str(page))
            content = self.getWebPage(url).split('\n')
            page_dict = ZtcOrder.eval_ztc_order(content[1])

            page_list = page_dict['data']
            for order in page_list:
                if order['payTime'].find(today) != -1:
                    order_nick = order['nick']
                    if order_nick.find('<font title="') != -1:
                        order_nick = order_nick.split('"')
                        order['nick'] = order_nick[1]
                    order_list.append(order)
                    flag = True
            if not flag and order['payTime'].find(str(self.yesterday)) != -1:
                break

        return order_list


def collect_order_script(_days=0):
    today = datetime.date.today() - datetime.timedelta(days=_days)
    try:
        ztc = ZtcOrderCollect(today)
        ztc.get_order()
        ztc.write_order()
    except Exception,e:
        logger.error('collect_order_script %s: %s' % (str(today), str(e)))
        send_sms(DIRECTOR['PHONE'], 'collect_order_script %s: %s' % (str(today), str(e)))
    else:
        logger.info('collect_order_script %s ok', str(today))

if __name__ == '__main__':
    if len(sys.argv) == 1:
        collect_order_script()
    else:
        collect_order_script(int(sys.argv[1]))
