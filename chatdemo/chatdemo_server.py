import asyncio
import zmq
import zmq.asyncio
import argparse
import time
import queue
from easyconnects.asyncio import Server, Socket
from collections import deque
import json
from typing import *
import numpy as np
import math
import logging 
import io

class RealtimeQueueGroup:
    
    # 一组实时队列，添加对象时附带这个对象的有效期，可以按实际时间线返回对象。
    # 队列中每个对象都带着一个相对于 session 起点的时间戳，表示这个 obj 的有效期截止时间。
    # 当时间戳为 math.inf 时表示 session 结束。
    
    def __init__(self, names: List[str], init_objs: List[Any], latencies: List[float]):
        # 初始化时给定所有队列地名字和初始对象。
        # latency 表示下游操作的延迟时间，单位秒
        # 对所有的队列的时间戳平移 self.offsets = self.max_latency - self.latencies[name]
        # 从而保证添加了下游延迟之后刚好是对齐的。
        # TODO: 实际上 latency 不应该是 per-queue 的，而应该是 per-consumer 的
        # 但动这个意味着时间线不是唯一的 time.time() 了，要大改整个类，目前没必要。
        
        self.queues: Dict[str, asyncio.Queue] = {name: asyncio.Queue() for name in names}
        self.latest: Dict[str, Tuple[Any, float]] = {name: (init_obj, math.inf) for name, init_obj in zip(names, init_objs)}
        self.latencies: Dict[str, float] = {name: l for name, l in zip(names, latencies)}
        self._reset_time()
        
    def _get_time(self):
        return time.time() - self.zero_time
        
    def _reset_time(self):
        self.zero_time = time.time()

    async def _next_obj(self, name):
        # 从队列中取元素，同时维护 self.latest。
        # 如果走到这里发现队列空了，那就说明输入队列的时间戳跟不上消耗的速度了。给个 warning。
        # 如果遇到 session 结束的情况就把上一次更新的内容留下来。
        # TODO: 如果将来需要插值的话，就在这里维护一个历史窗口。然后把插值结果写进 self.last 里面。
        if self.queues[name].qsize() == 0: logging.warning(f"Queue {name} can't keep up.")
        obj, expire_time = await self.queues[name].get()
        
        # 没给新的 obj 就沿用旧的 obj
        if obj is None:
            obj = self.latest[name][0]
            
        # 特殊处理 session 开始的情况，0 到 offset 这段时间仍然沿用上个 session 的最后一个 obj
        if self.latest[name][1] is math.inf:
            obj = self.latest[name][0]
            expire_time = self.latencies[name]
            
        self.latest[name] = (obj, expire_time)
    
    def set_latency(self, name: str, latency: float):
        self.latencies[name] = latency
        
    async def put(self, name: str, obj: Any, expire_time: float):
        # 给 name 队列放一个对象和它的有效期。如果时间戳为 math.inf，那就说明整个 session 结束了。
        # 这个对象的有效期的结束就是下一个对象有效期的开始。
        # 有效期添加一个偏移量，用于抵消下游的延迟。
        if name not in self.queues: raise ValueError(f"Unknown queue {name}")
        await self.queues[name].put((obj, expire_time + self.latencies[name]))

            
    async def get(self):
        # 如果所有 session 都结束了，并且下个 session 的数据也都来了，那么就重置时间戳，开始下个 session
        if all([expire_time is math.inf for _, expire_time in self.latest.values()]): 
            if all([q.qsize() > 0 for q in self.queues.values()]):
                for name in self.queues.keys(): await self._next_obj(name)
                self._reset_time()
                
        req_time = self._get_time()
        # 不断取出最旧的元素，直到所有元素到期时间都在 req_time 之后。
        # 如果 session 结束了，时间戳是 inf，自动排在所有 req_time 后面，
        while True:
            name, (_, expire_time) = min(self.latest.items(), key=lambda x: x[1][1])
            # 带上等号可以处理 math.inf 的情况
            if req_time <= expire_time: 
                return self.latest
            else:
                await self._next_obj(name)


class ChatdemoServer(Server):
    
    def __init__(self, args):
        super().__init__()
        self.args = args
        with open(args.init_pose, 'r') as f:    
            init_pose = json.load(f)
        with open(args.init_flame, 'rb') as f:
            init_flame = np.load(f)
        
        # self.rqg = RealtimeQueueGroup(
        #     names=['talkshow', 'flame', 'chattts'], 
        #     init_objs=[init_pose, init_flame, empty_wav], 
        #     buffer=0.1
        # )
        self.rqg = RealtimeQueueGroup(
            names=['chattts'], 
            init_objs=[[None, None]],
            latencies=[0.1]
        )
        
        
    async def handle_chattts(self, socket: Socket, meta):
        await self.wait_ready('speaker')
        
        speaker_chunk_size = self.meta_by_name['speaker']['blocksize']
        speaker_sr = self.meta_by_name['speaker']['sr'] 
        speaker_lat = self.meta_by_name['speaker']['latency']
        self.rqg.set_latency('chattts', speaker_lat)
        
        while True:
            wav, sr = await socket.recv_pyobj()
            print("chattts recieved wav")

            if 'talkshow' in self.socket_by_name:
                await self.socket_by_name['talkshow'].send_npz(wav=wav, sr=sr)
            if 'flame' in self.socket_by_name:
                await self.socket_by_name['flame'].send_npz(wav=wav, sr=sr)

            # 有必要的话 resample 一下
            # TODO: 直接通知 speaker 用 chattts 的 sr
            if sr != speaker_sr:
                import librosa
                wav = librosa.resample(wav, orig_sr=sr, target_sr=speaker_sr)
            # 然后把 wav 切成 chunk，每个 chunk 放进队列里面。
            # 注意时间要传到期时间
            for i in range(0, len(wav), speaker_chunk_size):
                await self.rqg.put('chattts', [wav[i:i+speaker_chunk_size], sr], (i + speaker_chunk_size) / sr)
            
            # 结束之后传个空的进去，在 speaker 里处理
            print("chattts wav done")
            await self.rqg.put('chattts', [None, None], math.inf)
            

    async def handle_talkshow(self, socket: Socket, meta):
        fps = meta['fps']
        while True: # session
            frameId = 0
            while True: # frame
                frameId += 1
                obj = await socket.recv()
                if not obj: break # session stop signal
                await self.rqg.put('talkshow', obj, frameId / fps)
                print(f"[Server] handle talkshow\t put frameId {frameId} session time {frameId / fps:5.2f}")
            await self.rqg.put(name='talkshow', obj=None, expire_time=math.inf)
   
    async def handle_flame(self, socket: Socket, meta):
        fps = meta['fps']
        while True: # session
            frameId = 0
            while True: # frame
                frameId += 1
                obj = await socket.recv()
                if not obj: break # session stop signal
                await self.rqg.put('flame', obj, frameId / fps)
                print(f"[Server] handle flame\t put frameId {frameId} session time {frameId / fps:5.2f}")
            await self.rqg.put(name='flame', obj=None, expire_time=math.inf)
    
    async def handle_easyvolcap(self, socket: Socket, meta):
        has_timestamp = meta['has_timestamp'] if 'has_timestamp' in meta else False
        while True:
            await socket.recv() # 新一帧请求
            latest = await self.rqg.get()
            pose, flame = latest['talkshow'], latest['flame']
            await socket.send_json(pose[0], zmq.SNDMORE)
            await socket.send_npz(flame[0])
            
            if (has_timestamp):
                await socket.send_json({
                    "pose_time": pose[1],
                    "flame_time": flame[1],
            })
            
    async def handle_speaker(self, socket: Socket, meta):
        last_expire_time = None
        sr = meta['sr']
        blocksize = meta['blocksize']
        
        while True:
            await socket.recv()
            while True:
                (wav, _), expire_time = (await self.rqg.get())['chattts']
                if expire_time != last_expire_time:
                    last_expire_time = expire_time
                    await socket.send_pyobj([wav, sr])
                    break
                await asyncio.sleep(blocksize / sr / 2)
    
    async def serve(self):
        await super().serve()
    
async def main():
    parser = argparse.ArgumentParser(description='Start an asyncio socket server.')
    parser.add_argument('--dump', type=bool, help='whether or not to dump all traffic to disk')
    parser.add_argument('--init_pose', type=str, default='data/init.json', help='Path to the empty pose to send to renderer if pipeline is not ready')
    parser.add_argument('--init_flame', type=str, default='data/init.npz', help='Path to the empty flame to send to renderer if pipeline is not ready')
    parser.add_argument('--init_chattts', type=str, default='data/empty_wav.npz', help='Path to the empty audio to send to speaker if pipeline is not ready')
    args = parser.parse_args()

    server = ChatdemoServer(args)
    await server.serve()
            
if __name__ == "__main__":    
    asyncio.run(main())

