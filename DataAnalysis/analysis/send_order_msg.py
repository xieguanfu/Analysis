#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Xie Guanfu
@contact: xieguanfu@maimiaotech.com
@date: 2013-10-14 14:49
@version: 0.0.0
@license: Copyright Maimiaotech.com
@copyright: Copyright Maimiaotech.com

"""



import os
import re
import sys
import datetime

if __name__ == '__main__':
    sys.path.append('../../')

from DataAnalysis.analysis.analysis_ztc_order_script import analysis_ztc_order_script_2
from DataAnalysis.collect.collect_order_script  import collect_order_script

#直通车软件报表
collect_order_script()
print "colect order ok"
analysis_ztc_order_script_2()
