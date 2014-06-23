#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: zhoujiebing
@contact: zhoujiebing@maimiaotech.com
@date: 2013-02-27 15:52
@version: 0.0.0
@license: Copyright maimiaotech.com
@copyright: Copyright maimiaotech.com

"""
import sys
import datetime
if __name__ == '__main__':
    sys.path.append('../../')

import DataMonitor.conf.settings
from CommonTools.send_tools import send_sms, DIRECTOR,send_email_with_text
from CommonTools.logger import logger
#from DataMonitor.monitor.monitor_marketing_cost import monitor_marketing_cost
from DataMonitor.monitor.monitor_order_add import monitor_order_add
from DataMonitor.monitor.monitor_comment_add import monitor_comment_add

def monitor_soft_script():
    try:
        return_info = monitor_soft() 
    except Exception,e:
        logger.exception('monitor_soft error: %s', str(e))
        send_sms(DIRECTOR['PHONE'], 'monitor_soft_script error: '+str(e))
    else:
        logger.info(return_info)

def monitor_soft():
    """软件监测脚本
       1.麦苗科技营销花费 定期监测
       2.省油宝新增订单数 定期监测
       3.省油宝新增评价 定期监测
       4.北斗新增评价 定期监测
       省油宝,ts-1796606
       北斗,ts-1797607
    """
    current_time = datetime.datetime.now()
    print current_time
    rest_hours = range(2,7)
    if current_time.hour in rest_hours:
        return None

#已废弃marketing_info = monitor_marketing_cost()
    order_info = monitor_order_add('省油宝', 'ts-1796606')
    comment_info=monitor_comment_add('省油宝', 'ts-1796606')+monitor_comment_add('北斗', 'ts-1797607')
    return_info = order_info + comment_info 
    if return_info:
        #send_sms(DIRECTOR['PHONE'], return_info)

        #send XJ
        #send_sms('18658818166', return_info)
        if comment_info:
            sms_list=comment_info.split("\n")
            idx=0
            for sms  in sms_list:
                if sms is None or sms.strip()=="":
                    continue
                idx+=1
                print "time:%s,==%s==%s" %(datetime.datetime.now(),idx,sms) 
                #send_sms('15068116152', sms)
                #send LW
                send_sms('15158877255', sms)
                send_sms('13588342404', sms)
                send_sms('13456901833', sms)
                send_sms('15397136805', sms)
                send_sms('15168418068', sms)
                send_sms('15168416259', sms)
                send_sms('15268122271', sms)
                #send_sms('18658818166', sms)
                #send_sms('15068116152', sms)
        if order_info:
            #send YB
            send_sms('15858224656', return_info)
        return 'monitor_soft: ' + return_info
    else:
        return 'monitor_soft ok'

if __name__ == '__main__':
    monitor_soft_script()
