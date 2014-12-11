#encoding=utf-8
"""
    @author: xieguanfu
"""
import os ,sys
import urllib
import urllib2
import cookielib
import datetime
import time
from urllib2 import URLError, HTTPError
from BeautifulSoup import BeautifulSoup
import re
import socket
import traceback
from urllib import urlencode
import simplejson as json
from optparse import OptionParser
if __name__ =="__main__":
    sys.path.append("../..")

from data_center.conf.settings import RPT_PATH
PLANS = {'1':14666026, '2':14955998, '3':14957740, '4':14872531,'5':14965207,'6':14656392,'7':14872501,'8':14956000}



def operate_exception(MAX_RETRY_TIMES=20):
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
                    print e
                    retry_time+=1
                time.sleep(2)
            return res
        return _wraped_func
    return _wrapper_func

def login( username, password,_tb_token,agent_nick,is_tp = False):
    """登入淘宝并进入直通车页面,抓取计划数 """
    cj = cookielib.CookieJar()
    path = 'https://login.taobao.com/member/login.jhtml?redirectURL=http://trade.taobao.com/trade/itemlist/list_bought_items.htm'
    myProxy = urllib2.ProxyHandler({'http':'127.0.0.0:9001'})
    #opener = urllib2.build_opener(myProxy,urllib2.HTTPCookieProcessor(cj))
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
 
    opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:21.0) Gecko/20100101 Firefox/26.0')]
   
    urllib2.install_opener(opener)
    post_data=get_post_data(username,password,_tb_token)
    req = urllib2.Request(path, post_data)
    try:
        conn = urllib2.urlopen(req)
        html = conn.read()
        if html.decode("gbk").encode("utf8").find("为了您的账户安全，请输入验证码") > 0:
            soup = BeautifulSoup(html)
            data_src = soup.find("img", {"id":"J_StandardCode_m"}).get("data-src")
            img_data = get_response(data_src)
            open(RPT_PATH+"/code.jpg","wb").write(img_data)
            print "==========wait code ======="
            check_code = raw_input("please input checkcode:")
            print check_code
            if not check_code:
                print "没有输入验证码"
                return None	
            post_data=get_post_data(username,password,_tb_token,check_code)
            req = urllib2.Request(path, post_data)
            conn = urllib2.urlopen(req)
            html = conn.read()
        if is_tp:
            ztc_dict = go_to_seller(username)
        else:
            ztc_dict=go_to_ztc(agent_nick)
        return ztc_dict
    except URLError,e:
        traceback.print_exc()
    except HTTPError, e:   
        traceback.print_exc()
    return None
    

def go_to_ztc(agent_nick=None,debug=False):
    if debug:
        """淘宝直通车入口"""
        #conn = urllib2.urlopen("http://qw.simba.taobao.com/")
        """"一淘直通车入口 """
    html = get_response("http://qw.simba.taobao.com/home.html")
    #conn = urllib2.urlopen("http://qw.simba.taobao.com/home.html")
    #html = conn.read()

    #open('ztc.html','w').write(html)
    soup = BeautifulSoup(html)
    #登入的是代理账号
    if "switchDelegate.htm" in html:
        option_list = soup.find("select",{"id":"selectDelegate"}).findAll("option")
        idx =0
        for op in option_list:
            idx += 1
            lab = op["lab"]
            v = op["value"]
            title = op.text.encode("utf-8")
            if (idx ==1 and agent_nick is None or agent_nick.strip() =="") or (agent_nick and title.startswith(agent_nick)):
                soup.decompose()
                url = "http://qw.simba.taobao.com/switchDelegate.htm?memberId=%s&outSideNumId=%s" %(lab,v)
                html = conn = urllib2.urlopen(url).read()
                #open('ztc.html','w').write(html)
                soup =  BeautifulSoup(html)
                break
                
    token_a=soup.find("input",{"id":"token"})
    if token_a is  None:
        raise Exception("未找到token,可能还未登入")
    token=token_a["value"]
    custid_obj = soup.find("div",{"class":"top-nav"}).li.text
    #custid = re.findall("(\w+)",custid_obj.text)[0]
    custid ="1104895516" 
    camp_list =get_campaign_list(token)
    ztc={"token":token,"campaigns":camp_list,"cusid":custid}
    soup.decompose()
    return ztc

def go_to_seller(nick):
    url = 'http://mai.taobao.com/seller_admin.htm'
    html = get_response(url)
    soup = BeautifulSoup(html,fromEncoding='gbk')
    token_obj = soup.find('input',attrs = {'name':'_tb_token_'})
    if not token_obj:
        raise Exception('未找到token,可能还未登入')
    return {'token':token_obj['value']}

def get_campaign_list(token):
    query = {"token":token,"isAjaxRequest":"true"}
    url = "http://qw.simba.taobao.com/campaign/ajListCampaign.html?token="+token+"&isAjaxRequest=true"
    html =get_response(url)
    if html is None or "campaignList" not in html:
        return None
    cam_list=json.loads(html)["d"]["campaignList"]
    campaigns = []
    for campaign in cam_list:
        c_dict ={"campaign_name":campaign["title"],"campaign_id":campaign["id"]}
        c_dict.update(campaign)
        campaigns.append(c_dict)
    return campaigns

@operate_exception()
def get_response(url,params = None):
    if not params:
        conn = urllib2.urlopen(url)
    else:
        post_data = urllib.urlencode(params)
        req = urllib2.Request(url, post_data)
        conn = urllib2.urlopen(req)
    html = conn.read()
    return html

def download_rpt(start_date,end_date,token,download_type,locate_path=None):
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    flag = "adgroup" 
    if "campaign" in download_type:
        flag = "campaign"
    elif "tag" in download_type:
        flag = "tag"
    elif "adgroup" in download_type :
        flag = "adgroup"
    else:
        raise Exception("download type:%s not exists" %(download_type))
    url = "http://qw.simba.taobao.com/report/downloadReportDetail.html"
    p_dict = {"dtBegin":start_date_str,"dtEnd":end_date_str,"order":"desc","orderType":"cost","type":download_type,"token":token}
    html = get_response(url,p_dict)
    print url +"?"+urllib.urlencode(p_dict)
    curr = os.path.normpath(os.path.dirname(__file__))
    path = curr+"/rpt_data/"
    if locate_path is not None and locate_path.strip() != "":
        path = locate_path
    if not os.path.isdir(path):
        os.makedirs(path)
    file_name = path + "/"+start_date_str+"_"+end_date_str+flag+".xls"
    file_obj =open(file_name,"wb")
    file_obj.write(html)
    file_obj.close()
    print "%s 到 %s 的报表下载成功,保存在:%s" %(start_date_str,end_date_str,file_name)
    return file_name 


def download_rpt_strong(start_date_str,end_date_str,token,download_type,locate_path =None,retry_time =5):
    """加强版下载报表"""
    for x in range(retry_time):
        try:
            rpt = download_rpt(start_date_str,end_date_str,token,download_type,locate_path)
        except Exception,e:
            print e
            time.sleep(10)
        else:
            if not rpt:
                time.sleep(10)
            else:
                return rpt


def get_post_data(username, password,_tb_token,check_code=None):
      p_dict = {
         'CtrlVersion': '1,0,0,7',
         'TPL_password':password,
         'TPL_redirect_url':'',
         'TPL_username':username.decode('utf-8').encode('gb2312'),
        '_tb_token_':_tb_token,
         'action':'Authenticator',
         'callback':'',
         'css_style':'',
         'event_submit_do_login':'anything',
         'fc':2,
         'from':'tb',
         'from_encoding':'',
         'guf':'',
         'gvfdcname':'10',
         'isIgnore':'',
         'llnick':'',
         'loginType':3,
         'longLogin':0,
         'minipara' :'',
         'minititle':'',
         'need_sign':'',
         'need_user_id':'',
         'not_duplite_str':'',
         'popid':'',
         'poy':'',
         'pstrong':'',
         'sign':'',
         'style':'default',
         'support':'000001',
        'tid':'XOR_1_000000000000000000000000000000_63504554470A7C710D060B0A'
        }
      if check_code :
          p_dict["TPL_checkcode"] = check_code
          p_dict["need_check_code"] = "yes"
      post_data = urllib.urlencode(p_dict)
      return post_data


def get_options(args):
    p = OptionParser()

    p.add_option("--delete", action="store_true", dest="delete", default=False, help = u"删除")
    p.add_option("--add", action="store_true", dest="add", default=False, help = u"添加图片")
    p.add_option("--update", action="store_true", dest="update", default=False, help = u"修改")
    p.add_option("--replace", action="store_true", dest="replace", default=False, help = u"替换图片")
    p.add_option("--readd", action="store_true", dest="readd", default=False, help = u"替换图片")
    p.add_option("--rpt", action="store_true", dest="rpt", help = u"下载报表")
    p.add_option("--monitor", action="store_true", dest="monitor", help = u"下载报表")
    p.add_option("--mail", action="store_true", dest="mail", help = u"下载报表")
    p.add_option("--img_name", type="string", action="store", dest="img_name", help = u"图片标识")
    p.add_option("--new_img_name", type="string", action="store", dest="new_img_name", help = u"图片标识")
    p.add_option("--img", type="string", action="store", dest="img", help = u"图片文件的路径")
    p.add_option("--img_type", type="string", action="store", dest="img_type", default="default", help = u"图片类型")
    p.add_option("--img_url", type="string", action="store", dest="img_url",  help = u"图片类型")
    p.add_option("--cat", type="string", action="store", dest="cat",  default="ztc", help = u"推广类目，默认为ztc，商品管理类目为im")
    p.add_option("--plan", type="string", action="store", dest="plan", help = u"需要修改的计划名")
    p.add_option("--app", type="string", action="store", dest="app",default="syb", help = u"推广的应用,默认syb")
    p.add_option("--num", type="int", action="store", dest="num", default=0,  help = u"需要操作推广组的个数，默认为0, 添加图片时为计划所有可添加的推广组个数，删除和修改为当前图片或计划所有的推广组")
    p.add_option("--default_price", type="float", action="store", dest="default_price", help = u"默认出价")
    p.add_option("--banner_price", type="float", action="store", dest="banner_price", help = u"banner出价")
    p.add_option("--ww_price", type="float", action="store", dest="ww_price", help = u"旺旺出价")
    p.add_option("--male_price", type="float", action="store", dest="male_price", help = u"男性出价,默认等于default_price")
    p.add_option("--female_price", type="float", action="store", dest="female_price", help = u"女性出价，默认等于default_price")
    p.add_option("--title", type="string", action="store", dest="title",  help = u"图片推广组标题")
    p.add_option("--bidword", type="string", action="store", dest="bidword", help = u"关键词设置，默认问'直通车优化解决方案'")
    p.add_option("--start_date", type="string", action="store", dest="start_date", help = u"报表开始时间,格式为yyyy-mm-dd, 默认为昨天")
    p.add_option("--end_date", type="string", action="store", dest="end_date", help = u"报表结束时间,格式为yyyy-mm-dd 默认为昨天")
    p.add_option("--rpt_path", type="string", action="store", dest="rpt_path", help = u"报表存放的路径, 默认为当前路径的rpt_data目录下")
    p.add_option("--nonsearch", type = "string",action="store", dest="nonsearch", default='ww_banner', help = u"打开定向,可选值:ww_banner,ww_big,ww_small,ww_banner,ww_word 分别是:直通车banner,旺旺焦点大图,焦点小图,旺旺banner,旺旺文字链")

    #print dir(p)
    (options, args) = p.parse_args(args)
    
    return options
    

#--------------------------------------------------------------------
if __name__ == '__main__' :
   
    
    options = get_options(sys.argv)    
 
    "登入淘宝时必须的参数,每天都会变化,在淘宝的cookie中 _tb_token "
    _tb_token="ylD7uO2T8sm" 
    #agent_nick="麦苗科技营销" #代理账号,如果此账号不为空则自动切换到此账号
    ztc_dict=login("麦苗科技营销","Mm-marketing2#",_tb_token,agent_nick=None)
    agent_nick="麦苗科技营销" #代理账号,如果此账号不为空则自动切换到此账号
    if not ztc_dict:
        print "login fialed"
        sys.exit(1)

    token = ztc_dict["token"]
    cusid = ztc_dict["cusid"]
    if options.rpt:
        print options.rpt
        yesterday = str(datetime.date.today() - datetime.timedelta(days=1))

        start_date = options.start_date
        end_date = options.end_date
        if not options.start_date:
            start_date = yesterday
        if not options.end_date:
            end_date = yesterday
        if not options.rpt_path:
            rpt_path = 'rpt'

        start_date = datetime.datetime.fromtimestamp(time.mktime(time.strptime(options.start_date, "%Y%m%d")))
        end_date   = datetime.datetime.fromtimestamp(time.mktime(time.strptime(options.end_date, "%Y%m%d")))

        page_rpt = download_rpt_strong(start_date, end_date, token, 'adgroup', locate_path = rpt_path)
        keyword_rpt = download_rpt_strong(start_date, end_date, token, 'tag', locate_path = rpt_path)
    sys.exit()
