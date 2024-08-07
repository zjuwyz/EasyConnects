import asyncio
import zmq
import zmq.asyncio
import argparse
import time
import queue
from easyconnects import TimeStamp, timer, logger
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


class ChatdemoServer(Server):
                
    def __init__(self):
        super().__init__()
        self.auto_start_handler = False
        self.device = 'cuda:1'
        timer.reset()
        
    def init_resampler(self, orig, target) -> Callable[[torch.Tensor], torch.Tensor]:
        import torchaudio as ta
        import torch
        resampler = ta.transforms.Resample(orig_freq=orig, new_freq=target).to(self.device)
        wav_zero = torch.zeros((1, orig), dtype=torch.float32).to(self.device)
        resampler(wav_zero)
        return resampler

    
    async def audio_handler(self):
        logger.info("Waiting audio input from chattts")
        await self.wait_ready('chattts')
        logger.info("chattts connected")
        input_socket = self.socket_by_name['chattts']
        names = ["talkshow", "flame", "speaker"]
        for name in names: 
            logger.info(f"Waiting socket {name}")
            await self.wait_ready(name)
            logger.info(f"{name} connected")

        deadlines: Dict[str, Fraction] = {name: 0 for name in names}
        sample_rates: Dict[str, int] = {name: self.meta_by_name[name]["sr"] for name in names}
        chunk_size: Dict[str, int] = {name: self.meta_by_name[name]["chunk_size"] for name in names}
        durations: Dict[str, Fraction] = {name: Fraction(chunk_size[name], sample_rates[name]) for name in names}
        default_chunks: Dict[str, np.ndarray] = {name: np.zeros(chunk_size[name], dtype=np.float32) for name in names}
        origin_sr: int = self.meta_by_name['chattts']['sr']
        resamplers: Dict[str, Callable[[torch.Tensor], torch.Tensor]] = {name: self.init_resampler(origin_sr, sample_rates[name]) for name in names}
        timer.reset()
        audio_num = 0
        while True:
            name, deadline = min(deadlines.items(), key= lambda x: x[1])
            
            try:
                timeout = deadline - timer.now()
                if timeout <= 0:
                    raise asyncio.TimeoutError
                wav, sr = await asyncio.wait_for(input_socket.recv_pyobj(), timeout)
                if (sr != origin_sr):
                    logger.error(f"sr {sr} origin_sr {sr}")
                    exit(0)
            except asyncio.TimeoutError:
                # 没有音频输入。给这个到期的往后塞个 chunk，无事发生
                socket = self.socket_by_name[name]
                wav = default_chunks[name]
                start = float(deadlines[name])
                end = float(start + durations[name])
                wav_ts = TimeStamp(id="e", start=start, end=end)
                deadlines[name] = end
                await socket.send_pyobj((wav, wav_ts))
                #logger.info(f"audio send to {name} {wav_ts}")
                continue
            
            length: float = len(wav) / origin_sr
            # 最近的可以更改的“未来”时间点是 ddl 里面最大的那个。对它来说 ddl 之前
            # 已经确定是 default_chunk 了。对其它的可以补零对齐。
            name, start_point = max(deadlines.items(), key = lambda x: x[1])
            wav_ts = TimeStamp(str(audio_num), float(start_point), float(start_point) + length)
            logger.info(f"audio recieved {wav_ts}")
            
            # 重采样
            wav_tensor = torch.from_numpy(wav).to(self.device).reshape(1, -1)
            resampled_audios: Dict[str, torch.Tensor] = {name: resamplers[name](wav_tensor) for name in names}
            logger.info(f"audio resampled {wav_ts}")
            
            # 对齐时间轴用的前缀 0
            leading = {name: math.floor(sample_rates[name] * (start_point - deadlines[name])) for name in names}
            
            # 对齐 chunk 用的后缀 0
            audio_len = {name: leading[name] + resampled_audios[name].shape[1] for name in names}
            tailing = {name: chunk_size[name] * (audio_len[name] // chunk_size[name] + 1) - audio_len[name] for name in names}
            chunked_audios = {name: torch.cat((
                torch.zeros((1, leading[name]), dtype=torch.float32), 
                resampled_audios[name].cpu(), 
                torch.zeros((1, tailing[name]), dtype=torch.float32)), dim=1).numpy() for name in names
            }
            audio_len = {name: chunked_audios[name].shape[1] for name in names}
            assert(all([audio_len[name] % chunk_size[name] == 0]))
            
            for name in names:
                chunks = audio_len[name] // chunk_size[name]
                start = float(deadlines[name])
                end = start + audio_len[name] / sample_rates[name]
                logger.info(f"audio padded for {name} ({leading[name]}|{tailing[name]}) {chunks} chunks")
                wav_ts = TimeStamp(wav_ts.id, start, end)
                wav = chunked_audios[name][0, :]
                await self.socket_by_name[name].send_pyobj((wav, wav_ts))   
                logger.info(f"audio send to {name} {wav_ts} ")
                deadlines[name] += Fraction(audio_len[name], sample_rates[name])

            audio_num += 1
    
    async def easyvolcap_handler(self):
        await self.wait_ready('talkshow')
        await self.wait_ready('flame')
        
        poses:asyncio.Queue[Tuple[Any, TimeStamp]] = asyncio.Queue()
        flames:asyncio.Queue[Tuple[Any, TimeStamp]] = asyncio.Queue()

        
        async def recv_pose():
            socket = self.socket_by_name["talkshow"]
            while True:
                pose, pose_ts = await socket.recv_pyobj()
                #logger.debug(f"recv pose {pose_ts}")

                poses.put_nowait((pose, pose_ts))
        
        async def recv_flame():
            socket = self.socket_by_name["flame"]
            while True:
                exp_code, flame_pose_params, flame_ts = await socket.recv_pyobj()
                #logger.debug(f"recv flame {flame_ts}")
                flames.put_nowait((exp_code, flame_pose_params, flame_ts))
            
        asyncio.create_task(recv_pose())
        asyncio.create_task(recv_flame())
        last_pose = await poses.get()
        last_flame = await flames.get()
        logger.info("pose and flames output ready")
        
        await self.wait_ready('easyvolcap')
        render = self.socket_by_name['easyvolcap']
        latency = 1.2
        while True:
            await render.recv()
            #logger.info("recv easyvolcap signal")
            now = timer.now() - latency
            while now >= last_pose[-1].end:
                
                last_pose = await poses.get()
            while now >= last_flame[-1].end:
                last_flame = await flames.get()
            await render.send_json(last_pose[0])
            exp_code, flame_pose_params = last_flame[:2]
            await render.send_npz(exp_code=exp_code, flame_pose_params=flame_pose_params)
            #logger.info(f"send easyvolcap pose {last_pose[-1]}")
            #logger.info(f"send easyvolcap flame {last_flame[-1]}")
    
    async def talkshow_only(self):
        init_flame = np.load('./init.npz')
        exp_code, flame_pose_params = init_flame['exp_code'], init_flame['flame_pose_params']
        pose_socket = self.socket_by_name['talkshow']
        render_socket = self.socket_by_name['easyvolcap']
        while True:
            await render_socket.recv()
            pose = await pose_socket.recv_json()
            await render_socket.send_json(pose)
            await render_socket.send_npz(exp_code=exp_code, flame_pose_params=flame_pose_params)
            
async def main():
    TEST_TALKSHOW=False
    server = ChatdemoServer()
    tasks = []
    if TEST_TALKSHOW:
        tasks.append(asyncio.create_task(server.talkshow_only()))
    else:
        tasks.append(asyncio.create_task(server.audio_handler()))
        tasks.append(asyncio.create_task(server.easyvolcap_handler()))
    
    serve = server.serve()
    await asyncio.gather(serve, *tasks)
    
if __name__ == "__main__":    
    asyncio.run(main())