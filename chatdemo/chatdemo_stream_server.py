import asyncio
import zmq
import zmq.asyncio
import argparse
import time
import queue
from easyconnects import TimeStamp
from easyconnects.asyncio import Server, Socket
from collections import deque
import json
from typing import *
import numpy as np
import math
import logging 
import io
from fractions import Fraction
import torch
import math
class Timer:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.start = time.time()
        
    def now(self):
        return time.time() - self.start
    
    def sleep_until(self, t):
        time.sleep(max(0, t - self.now()))
        
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
logger.setLevel(logging.DEBUG)

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

class ChatdemoServer(Server):
    def _get_time(self):
        return time.time() - self.zero_time
    
    def _to_int_ms(self, sec: float) -> int:
        import math
        return math.floor(sec * 1000)
        
    def _reset_time(self):
        self.zero_time = time.time()
        
    def __init__(self):
        super().__init__()
        self.auto_start_handler = False
        self.device = 'cuda:1'
        self._reset_time()
        
    def init_resampler(self, orig, target) -> Callable[[torch.Tensor], torch.Tensor]
        import torchaudio as ta
        import torch
        resampler = ta.transforms.Resample(orig_freq=orig, new_freq=target).to(self.device)
        wav_zero = torch.zeros((1, orig), dtype=torch.float32).to(self.device)
        resampler(wav_zero)
        return resampler
    
    async def audio_handler(self):
        logger.info("Waiting audio input from chattts")
        await self.ready('chattts')
        #names = ["talkshow", "flame", "speaker"]
        names = ["talkshow"]
        for stream in names: await self.ready(stream)

        logger.info("chattts connected")
        input_socket = self.socket_by_name['chattts']
        
        deadlines: Dict[str, Fraction] = {name: 0 for name in names}
        sr: Dict[str, int] = {name: self.meta_by_name[name]["sr"] for name in names}
        chunk_size: Dict[str, int] = {name: self.meta_by_name[name]["chunk_size"] for name in names}
        durations: Dict[str, Fraction] = {name: Fraction(chunk_size[name], sr[name]) for name in names}
        default_chunks: Dict[str, np.ndarray] = {name: np.zeros(name) for name in names}
        origin_sr: int = self.meta_by_name['chattts']['sr']
        resamplers: Dict[str, Callable[[torch.Tensor], torch.Tensor]] = {name: self.init_resampler(origin_sr, sr[name]) for name in names}
        self._reset_time()
        audio_num = 0
        while True:
            name, deadline = min(deadlines.items(), key= lambda x: x[1])
            timeout = self._to_int_ms(max(0, deadline - self._get_time()))
            event = await input_socket.poll(timeout=timeout, flags=zmq.POLLIN)
            if not event: # 没有音频输入。给这个到期的往后塞个 chunk，无事发生
                socket = self.socket_by_name[name]
                wav = default_chunks[name]
                deadlines[name] += durations[name]
                await socket.send_pyobj(wav)
                continue
            assert(event & zmq.POLLIN) # 来活了
            wav: np.ndarray
            wav_ts: TimeStamp
            wav, wav_ts = input_socket.recv_pyobj()
            length: float = wav_ts.end - wav_ts.start
            # 最近的可以更改的“未来”时间点是 ddl 里面最大的那个。对它来说 ddl 之前
            # 已经确定是 default_chunk 了。对其它的可以补零对齐。
            name, start_point = max(deadlines.items(), key = lambda x: x[1])
            wav_ts.start = float(start_point)
            wav_ts.end = wav_ts.start + length
            logger.info(f"audio {audio_num} recieved {wav_ts}")
            
            # 重采样
            wav_tensor = torch.from_numpy(wav).to(self.device).reshape(1, -1)
            resampled_audios = {name: resamplers[name](wav_tensor).to('cpu').numpy() for name in names}
            logger.info(f"audio {audio_num} resampled")
            
            # 对齐时间轴用的前缀 0
            leading = math.floor(sr[name] * (start_point - deadlines[name]) for name in names)
            
            # 对齐 chunk 用的后缀 0
            audio_len = {name: leading[name] + resampled_audios[name].shape[1] for name in names}
            tailing = {name: chunk_size[name] * (audio_len[name] // chunk_size[name] + 1) - audio_len[name] for name in names}
            chunked_audios = {name: torch.cat((
                torch.zeros(1, leading[name]), 
                resampled_audios[name], 
                torch.zeros(1, tailing[name])))
            }
            audio_len = {name: chunked_audios[name].shape[1] for name in names}
            assert(all[audio_len[name] % chunk_size[name] == 0])
            
            for name in names:
                chunks = audio_len[name] / chunk_size[name]
                start = float(deadlines[name])
                end = start + audio_len[name] / sr[name]
                logger.info(f"audio {audio_num} padded {name} ({leading[name]}|{tailing[name]}) {chunks} chunks {start:6.3f} - {end:6.3f}")
                
            for name in names:
                wav = chunked_audios[name].to('cpu').squeeze().numpy()
                await self.socket_by_name[name].send_pyobj()
                logger.info(f"audio {audio_num} send to {name}")
                
            