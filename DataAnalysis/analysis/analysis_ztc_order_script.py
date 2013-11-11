#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: zhoujiebing
@contact: zhoujiebing@maimiaotech.com
@date: 2013-04-22 10:52
@version: 0.0.0
@license: Copyright maimiaotech.com
@copyright: Copyright maimiaotech.com

"""
import os
import re
import sys
import datetime

if __name__ == '__main__':
    sys.path.append('../../')

from DataAnalysis.conf.settings import CURRENT_DIR
from CommonTools.ztc_order_tools import ZtcOrder, SOFT_CODE
from CommonTools.ztc_report_tools import ZtcReport, ORDER_TYPE, NUM_TYPE, EXACT_TYPE, KEYS, STRNUM, HEAD
from CommonTools.logger import logger
from CommonTools.send_tools import send_email_with_html, send_sms, DIRECTOR

class ZtcOrderReport(ZtcOrder):
    
    def __init__(self):
        
        #获取所有直通车软件
        self.id_data = SOFT_CODE.items()
        self.today = datetime.date.today()
        self.yesterday = self.today - datetime.timedelta(days=1)
        self.strNum = STRNUM
        self.head = HEAD
        self.result = []
        self.yesterday_reports = self.get_yesterday_report(str(self.yesterday))
        self.get_store_order(str(self.yesterday))
        self.id_name = ''

    def get_yesterday_report(self, yesterday):
        """获取昨天的直通车报告"""

        file_name = ZtcReport.get_file_name(CURRENT_DIR, self.yesterday)
        id_report_dict = {}
        if os.path.isfile(file_name):
            for line in file(file_name):
                report = ZtcReport.parser_ztc_report(line)
                id_report_dict[report['id_name']] = report
        return id_report_dict

    def get_store_order(self, date):
        """将文件中的已collect 到的order 导出 并增加唯一key"""

        self.order_dict = ZtcOrder.get_store_order(self.id_data, CURRENT_DIR, date)
        for id_name in self.order_dict:
            order_dict_key = self.order_dict[id_name] 
            self.order_dict[id_name] = order_dict_key.values()

    def write_report(self):
        """将软件报表写入文件"""

        file_name = ZtcReport.get_file_name(CURRENT_DIR, self.today)
        file_obj = file(file_name, 'w')
        strhead = ','.join(self.head) + '\n'
        file_obj.write(strhead)
        for report in self.result:
            file_obj.write(ZtcReport.to_string(report)+'\n')
        file_obj.close()

    def mergeDeltaNum(self, num, delta_num):
        flag = ''
        if delta_num > 0:
            flag = '(+' + str(delta_num) + ')'
        elif delta_num < 0:
            flag = '(' + str(delta_num) + ')'

        if str(num) == '0':
            return '少于100'
        return str(num) + flag 

    def getHtml(self):
        bg = ["#E8FFC4","#FCFCFC"]
        html = ''
        html_head = """
               <html><body>
                  <table align="center" border="0"  bordercolor="#000000">
                     <tr align="center" bgcolor="#548C00" style="height:50px" >
               """
        html_head += '<td width="80"><b>软件名称</td>'
        for type in ORDER_TYPE:
            html_head += '<td width="40"><b>' + type + '</td>'
        html_head += '<td width="80"><b>%s 订单总数</td>'%self.today
        for strnum in self.strNum:
            html_head += '<td width="90"><b>' + strnum + '</td>'
        html_tail = '</table></body></html>'

        html_data = ''
        if not self.result:
            return None
        self.result.sort(key = lambda x:int(x['add_num']), reverse = True)
        sum_order_num =0
        for report in self.result[:]:
            html_onedata = ''
            yesterday_report = self.yesterday_reports.get(report['id_name'], None)
            
            if yesterday_report:
                for key in NUM_TYPE+EXACT_TYPE:
                    if key == 'grade':
                        continue
                    delta = int(report[key]) - int(yesterday_report[key]) 
                    report[key] = self.mergeDeltaNum(report[key], delta)
                
            sum_order_num +=int(report["add_num"])
            for key in KEYS:
                html_onedata += '<td align = "center">%s</td>'% str(report[key])
            html_onedata = '<tr bgcolor=' + bg[0] + '>' + html_onedata + '</tr>'
            html_data += html_onedata
        html_sum = "<tr  bgcolor='"+ bg[0]+"'>"
        for idx in range(len(KEYS)):
            temp_data="&nbsp;"
            if idx ==0:
                temp_data="汇总"
            if idx ==6:
                temp_data= str(sum_order_num)
            html_sum +="<td align='center'>"+temp_data+"</td>"
        html_sum += "<tr>"
        html_data += html_sum
        html += html_head
        html += html_data
        html += html_tail
        return html

    def make_report(self,end_time = None):
        """生成报表"""
        
        exact_num_dict = ZtcOrder.get_exact_num_dict()
        for id_info in self.id_data:
            self.id_name = id_info[0]
            if self.id_name not in exact_num_dict:
                continue    
            id = id_info[1]
            report = self.count_order(self.id_name,end_time)
            report['add_num'] = sum(report.values())
            report['id_name'] = self.id_name
            total_num = ZtcOrder.get_total_num(id)
            for key in NUM_TYPE:
                report[key] = total_num[key]
            exact_num = exact_num_dict[self.id_name]
            for i in range(len(EXACT_TYPE)):
                report[EXACT_TYPE[i]] = exact_num[i]

            self.result.append(report)
    
    def count_order(self, id_name,end_time = None):
        """汇总今天的订单类型和数量"""
        
        type_num = {}
        for key in ORDER_TYPE:
            type_num[key] = 0
        order_list = self.order_dict[id_name]
        for order in order_list:
            if end_time is not None and datetime.datetime.strptime(order["payTime"],"%Y-%m-%d %H:%M:%S") >end_time:
                continue

            if not type_num.has_key(order['deadline']):
                type_num['其他'] += 1
            else:
                type_num[order['deadline']] += 1

        return type_num

def analysis_ztc_order_script_2():
    ToMe = DIRECTOR['EMAIL']
    ToAll = 'all@maimiaotech.com'
    try:
        ztc = ZtcOrderReport()
        ztc.today = datetime.date.today()
        ztc.yesterday = ztc.today - datetime.timedelta(days=0)
        ztc.strNum = STRNUM
        ztc.head = HEAD
        ztc.result = []
        ztc.yesterday_reports = ztc.get_yesterday_report(str(ztc.yesterday))
        ztc.get_store_order(str(ztc.yesterday))
        now = datetime.datetime.now().replace(second=0,minute=0)
        ztc.make_report(now)
        ztc.write_report()
        html = ztc.getHtml()
        send_email_with_html("zenglinjian@maimiaotech.com", html, str(ztc.today)+" "+str(datetime.datetime.now().hour)+'点__直通车软件报表内测版')
        send_email_with_html("xuyaoqiang@maimiaotech.com", html, str(ztc.today)+" "+str(datetime.datetime.now().hour)+'点__直通车软件报表内测版')
        send_email_with_html("tangxijin@maimiaotech.com", html, str(ztc.today)+" "+str(datetime.datetime.now().hour)+'点__直通车软件报表内测版')
        send_email_with_html(ToMe, html, str(ztc.today)+" "+str(datetime.datetime.now().hour)+'点__直通车软件报表内测版')
    except Exception,e:
        logger.exception('analysis_ztc_order_script error: %s' % (str(e)))
        send_sms(DIRECTOR['PHONE'], 'analysis_ztc_order_script error: '+str(e))
    else:
        logger.info('analysis_ztc_order_script ok')

def analysis_ztc_order_script():
    ToMe = DIRECTOR['EMAIL']
    ToAll = 'all@maimiaotech.com'
    try:
        ztc = ZtcOrderReport()
        ztc.make_report()
        ztc.write_report()
        html = ztc.getHtml()
        #send_email_with_html(ToMe, html, str(ztc.today)+'__直通车软件报表内侧版')
        send_email_with_html(ToAll, html, str(ztc.today)+'__直通车软件报表公测版')
    except Exception,e:
        logger.exception('analysis_ztc_order_script error: %s' % (str(e)))
        send_sms(DIRECTOR['PHONE'], 'analysis_ztc_order_script error: '+str(e))
    else:
        logger.info('analysis_ztc_order_script ok')
if __name__ == '__main__':
    analysis_ztc_order_script()
