EASYCONNECTS_PORT = 12000
EASYCONNECTS_HOST = "10.76.2.117"

from easyconnects.Client import Client, Socket
EC_KNOWN_PORTS = {
    'talkshow':12011,
    'chattts':12012,
    'flame':12013,
    'speaker':12014,
    'easyvolcap':12015
}

import time
import logging
from collections import namedtuple
class TimeStamp(namedtuple('TimeStamp', ['id', 'start', 'end'])):
    def __repr__(self):
        return f"#{self.id} {self.start:6.3f}s - {self.end:6.3f}s"

    def partition(self, index, total):
        duration = (self.end - self.start) / total
        start = self.start + duration * index
        end = start + duration
        id = '.'.join([self.id, str(index)])
        return TimeStamp(id, start, end)

class Timer:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.start = time.time()
        
    def now(self):
        return time.time() - self.start
    
        
class CustomFormatter(logging.Formatter):
    def format(self, record):
        # 从全局变量中获取计时器实例
        global timer
        # 将自定义的时间差添加到日志记录中
        record.timer_now = timer.now()
        return super().format(record)

# 创建计时器实例
timer = Timer()

# 配置日志记录器
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = CustomFormatter('[%(timer_now)6.3f] [%(levelname)s] %(funcName)s:\t%(message)s (%(filename)s:%(lineno)d)')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.propagate = False  # Add this line
logger.setLevel(logging.DEBUG)