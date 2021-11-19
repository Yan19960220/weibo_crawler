# -*- coding: utf-8 -*-
# @Time    : 11/5/21 3:00 PM
# @Author  : Yan
# @Site    : 
# @File    : datetime_util.py
# @Software: PyCharm

from datetime import datetime


def str_to_time(text):
    """将字符串转换成时间类型"""
    if ':' in text:
        result = datetime.strptime(text, '%Y-%m-%d %H:%M')
    else:
        result = datetime.strptime(text, '%Y-%m-%d')
    return result
