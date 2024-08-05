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

from collections import namedtuple
class TimeStamp(namedtuple('TimeStamp', ['num', 'start', 'end'])):
    def __repr__(self):
        return f"#{self.num} {self.start:6.3f}s - {self.end:6.3f}s"

    def partition(self, index, total):
        duration = (self.end - self.start) / total
        start = self.start + duration * index
        end = start + duration
        index = self.num * total + index
        return TimeStamp(index, start, end)
