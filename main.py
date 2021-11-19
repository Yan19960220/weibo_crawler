# -*- coding: utf-8 -*-
# @Time    : 11/5/21 2:54 PM
# @Author  : Yan
# @Site    : 
# @File    : main.py
# @Software: PyCharm

import os
import sys

from absl import app
sys.path.append(os.path.abspath(os.path.dirname(os.getcwd())))
from spider.spider import main

app.run(main)