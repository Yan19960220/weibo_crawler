# -*- coding: utf-8 -*-
# @Time    : 11/7/21 2:16 PM
# @Author  : Yan
# @Site    : 
# @File    : topic.py
# @Software: PyCharm

import sys
import urllib
import csv
import os
import time
import json
import datetime
import random
import logging
import traceback

try:
    import wx
    from urllib.request import Request, urlopen
except ImportError:
    sys.stderr.write('no module named wx\n')

from bs4 import BeautifulSoup

class Topic:
    def __init__(self, keyword, startTime, endTime, savedir, interval='10', flag=True,
                 begin_url_per="http://s.weibo.com/weibo"):
        self.begin_url_per = begin_url_per  # 设置固定地址部分，默认为"http://s.weibo.com/weibo/"，或者"http://s.weibo.com/wb/"
        self.setKeyword(keyword)  # 设置关键字
        self.setTimescope(startTime, endTime)  # 设置搜索的时间
        self.setSaveDir(savedir)  # 设置结果的存储目录
        self.setInterval(interval)  # 设置邻近网页请求之间的基础时间间隔（注意：过于频繁会被认为是机器人）
        self.setFlag(flag)  # 设置
        self.logger = logging.getLogger('main.Topic')  # 初始化日志

        def set_config():
            config_path = os.path.join(os.getcwd(), "../..") + os.sep + 'config.json'

            with open(config_path) as f:
                config = json.loads(f.read())
                return config

        self.config = set_config()

    ## 设置关键字
    ## 关键字需解码
    def setKeyword(self, keyword):
        # self.keyword = keyword.decode('GBK').encode("utf-8")
        self.keyword = keyword
        print('twice encode:' + self.getKeyWord())

    ## 设置起始范围，间隔为1小时
    ## 格式为：yyyy-mm-dd-HH
    def setTimescope(self, startTime, endTime):
        if not (startTime == '-'):
            self.timescope = startTime + ":" + endTime
        else:
            self.timescope = '-'

    ## 设置结果的存储目录
    def setSaveDir(self, save_dir):
        self.save_dir = save_dir
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

    ## 设置邻近网页请求之间的基础时间间隔
    def setInterval(self, interval):
        self.interval = int(interval)

    ## 设置是否被认为机器人的标志。若为False，需要进入页面，手动输入验证码
    def setFlag(self, flag):
        self.flag = flag

    ## 构建URL
    def getURL(self):
        return self.begin_url_per + "?q=" + self.getKeyWord() + "&typeall=1&suball=1" + "&timescope=custom:" + self.timescope + "&Refer=g&page="

    ## 关键字需要进行两次urlencode
    def getKeyWord(self):
        once = urllib.parse.urlencode({"kw": self.keyword})[3:]
        # return urllib.urlencode({"kw":once})[3:]
        return once
        return self.keyword

    ## 爬取一次请求中的所有网页，最多返回50页
    def download(self, url, maxTryNum=4):
        scale = 50
        print("执行开始，祈祷不报错".center(25, "-"))
        start = time.perf_counter()
        with open(self.save_dir + os.sep + "weibo_contents.txt", "w") as content: # 向结果文件中写微博内容
            writer = csv.writer(content)
            header = ['name', 'content']
            writer.writerow(header)
            hasMore = True  # 某次请求可能少于50页，设置标记，判断是否还有下一页
            isCaught = False  # 某次请求被认为是机器人，设置标记，判断是否被抓住。抓住后，需要复制log中的文件，进入页面，输入验证码
            mid_filter = set([])  # 过滤重复的微博ID

            i = 1  # 记录本次请求所返回的页数
            while hasMore and i < scale + 1 and (not isCaught):  # 最多返回50页，对每页进行解析，并写入结果文件
                source_url = url + str(i)  # 构建某页的URL
                data = ''  # 存储该页的网页数据
                netSuccess = True  # 网络中断标记

                ## 网络不好的情况，试着尝试请求三次
                for tryNum in range(maxTryNum):
                    try:
                        # 登陆微博, 使用自己的cookie
                        # Cookie = 'SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9W5K3TLau8c8ZxBM_.ib3H1d5NHD95QfShqRSoqf1K50Ws4Dqcjdi--fiKysi-8si--fi-2Xi-24i--ciK.RiKy8; SSOLoginState=1636123035; SUB=_2A25MgTHLDeRhGeNK7VoX9ivFyz-IHXVvil-DrDV8PUJbkNAfLVnEkW1NSUTbvQ_2mqCIovsAwnnU9iI7JmOkR6lL; _s_tentry=www.google.com; UOR=www.google.com,kefu.weibo.com,www.google.com; Apache=676215441464.7336.1636209339082; SINAGLOBAL=676215441464.7336.1636209339082; ULV=1636209339086:1:1:1:676215441464.7336.1636209339082:; wvr=6'

                        headers = {
                            'Cookie': self.config["cookie"],
                            'Host': 's.weibo.com',
                            'User_Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36'
                        }
                        req = Request(url=source_url, headers=headers)
                        # html = requests.get(source_url, headers=headers)
                        html = urlopen(req).read()
                        soup = BeautifulSoup(html, "html.parser")
                        myAttrs = {'class': 'card-wrap'}
                        tags = soup.find_all(name='div', attrs=myAttrs)
                        for tag in tags:
                            if tag.find('p') is None:
                                continue
                            m_name = tag.find('p').get('nick-name')
                            m_text = tag.find('p', class_='txt')
                            if m_text is None:
                                continue
                            m_content = [item.strip() for item in m_text.contents if
                                         not item.name and item.strip().replace('\u200b', '')]
                            s_content = "".join(m_content)
                            writer.writerow([m_name, s_content])
                        break
                    except:
                        self.logger.error(traceback.format_exc())
                        if tryNum < (maxTryNum - 1):
                            time.sleep(10)
                        else:
                            print('Internet Connect Error!')
                            self.logger.error('Internet Connect Error!')
                            # self.logger.info('filePath: ' + self.savedir)
                            self.logger.info('url: ' + source_url)
                            # self.logger.info('fileNum: ' + str(fileNum))
                            self.logger.info('page: ' + str(i))
                            self.flag = False
                            netSuccess = False
                            break
                if netSuccess:
                    a = "*" * i
                    b = "." * (scale - i)
                    c = (i / scale) * 100
                    dur = time.perf_counter() - start
                    ## 设置两个邻近URL请求之间的随机休眠时间，防止Be Caught。目前没有模拟登陆
                    sleeptime_one = random.randint(self.interval - 10, self.interval - 5)
                    sleeptime_two = random.randint(self.interval, self.interval + 5)
                    if i % 2 == 0:
                        sleeptime = sleeptime_two
                    else:
                        sleeptime = sleeptime_one
                    # print('sleeping ' + str(sleeptime) + ' seconds...')
                    print("\r{:^3.0f}%[{}->{}]dur-{:.2f}s sleep-{}".format(c, a, b, dur, sleeptime), end="")
                    time.sleep(0.01)
                    i += 1
                    time.sleep(sleeptime)
                else:
                    self.logger.error('Network Not Connected!')
                    break
            print("\n" + "执行结束，万幸".center(scale // 2, "-"))
            content.close()
            content = None

    ## 改变搜索的时间范围，有利于获取最多的数据
    def getTimescope(self, perTimescope, hours):
        if not (perTimescope == '-'):
            times_list = perTimescope.split(':')
            start_datetime = datetime.datetime.fromtimestamp(time.mktime(time.strptime(times_list[-1], "%Y-%m-%d-%H")))
            start_new_datetime = start_datetime + datetime.timedelta(seconds=3600)
            end_new_datetime = start_new_datetime + datetime.timedelta(seconds=3600 * (hours - 1))
            start_str = start_new_datetime.strftime("%Y-%m-%d-%H")
            end_str = end_new_datetime.strftime("%Y-%m-%d-%H")
            return start_str + ":" + end_str
        else:
            return '-'


def main():
    logger = logging.getLogger('main')
    logFile = './collect.log'
    logger.setLevel(logging.DEBUG)
    filehandler = logging.FileHandler(logFile)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s: %(message)s')
    filehandler.setFormatter(formatter)
    logger.addHandler(filehandler)

    while True:
        keyword = input('Enter the keyword(type \'quit\' to exit ):') or "S11"
        if keyword.lower() in ['quit', 'q', 'exit', 'bye']:
            sys.exit()
        startTime = input('Enter the start time(Format:YYYY-mm-dd-HH):') or '2021-09-01-10'
        region = input('Enter the end time(Format:YYYY-mm-dd-HH):):') or '2021-11-01-16'
        savedir = input('Enter the save directory(Like C://data//):') or '/Users/zhangyan/Desktop/hk/spider_weibo/results'
        interval = input('Enter the time interval( >30 and deafult:10):') or 10

        ## 实例化收集类，收集指定关键字和起始时间的微博
        cd = Topic(keyword, startTime, region, savedir, interval)
        while cd.flag:
            print(cd.timescope)
            logger.info(cd.timescope)
            url = cd.getURL()
            cd.download(url)
            break
            cd.timescope = cd.getTimescope(cd.timescope, 1)  # 改变搜索的时间，到下一个小时
        else:
            cd = None
            print('-----------------------------------------------------')
            print('-----------------------------------------------------')
    else:
        logger.removeHandler(filehandler)
        logger = None


if __name__ == '__main__':
    main()
