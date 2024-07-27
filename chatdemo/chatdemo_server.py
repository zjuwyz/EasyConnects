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

class Clock():
    def __init__(self):
        self.reset_time()
        
    def get_current_time(self):
        return time.time() - self.zero_time
    
    def reset_time(self, offset=0):
        self.zero_time = time.time() - offset
    
class ChatdemoServer(Server):
    def __init__(self):
        super().__init__()
        self.clock = Clock()
        self.talkshow_queue = asyncio.Queue()
        self.flame_queue = asyncio.Queue()
        self.audio_queue = asyncio.Queue()
        self.session_on = False
        self.talkshow_input_finished = False
        self.render_ready = False
        self.meta: Dict[str, Dict] = {}
    
    async def handle_talkshow(self, socket: Socket, meta):

        fps = meta['fps']
        frameId = 0
        while True:
            obj = await socket.recv_json()
            if not obj:
                break
            await self.talkshow_queue.put((obj, frameId / fps))
            print(f"[Server] handle talkshow\t put frameId {frameId} time {frameId / fps:5.2f}")
            frameId += 1
            
        socket.close()
        self.talkshow_input_finished = True
            
    async def handle_flame(self, socket: Socket, meta):

        fps = meta["fps"]
        frameId = 0
        while True:
            obj = await socket.recv()
            if not obj:
                break
            await self.flame_queue.put((obj, frameId / fps))
            print(f"[Server] handle flame\t put frameId {frameId} time {frameId / fps:5.2f}")
            frameId += 1
    
    async def handle_easyvolcap(self, socket: Socket, meta):
        
        has_timestamp = meta['has_timestamp'] if 'has_timestamp' in meta else False
        last_pose = None
        last_flame = None
        while not (self.talkshow_queue.empty() and self.talkshow_input_finished):
            await socket.recv() # wait for renderer ready signal
            print("[Server] render ready signal recieved")
            if not self.session_on: # first frame. reset clock
                self.session_on = True
                self.clock.reset_time()
            
            # TODO 如果要做插值的话，就在这里做。目前只是拿出来了当前时刻的一帧。
            async def get_current_frame(queue: asyncio.Queue, last: Optional[Tuple[object, float]]) -> Dict:
                obj, obj_time = last if last is not None else await queue.get()
                while not queue.empty() and obj_time < self.clock.get_current_time():
                    obj, obj_time = queue.get_nowait()
                return obj, obj_time
            
            pose, pose_time = last_pose = await get_current_frame(self.talkshow_queue, last_pose)
            flame, flame_time = last_flame = await get_current_frame(self.flame_queue, last_flame)
            
            await socket.send_json(pose)
            await socket.send(flame)
            if (has_timestamp):
                await socket.send_json({
                    "pose_time": pose_time,
                    "flame_time": flame_time,
            })

    async def handle_microphone(self, socket: Socket, meta):
        input_audio = queue.Queue()
        while True:
            audio = await socket.recv()
            input_audio.put(audio)
            if 'whisper' in self.sockets:
                whisper = self.sockets['whisper']
                while not input_audio.empty():
                    whisper.send(input_audio.get())
                    
    async def handle_whisper(self, socket: Socket, meta):
        input_text = queue.Queue()
        while True:
            text = await socket.recv_string()
            input_text.put(text)
            if 'llm' in self.sockets:
                llm = self.sockets['llm']
                while not input_text.empty():
                    llm.send_string(llm)
                    
    async def handle_llm(self, socket: Socket, meta):
        input_text = queue.Queue()
        while True:
            text = await socket.recv_string()
            input_text.put(text)
            if 'chattts' in self.sockets:
                chattts = self.sockets['chattts']
                while not input_text.empty():
                    chattts.send_string(chattts)
            
    async def handle_chattts(self, socket: Socket, meta):
        input_text = queue.Queue()
        while True:
            text = await socket.recv_string()
            input_text.put(text)
            if 'speaker' in self.sockets:
                chattts = self.sockets['speaker']
                while not input_text.empty():
                    chattts.send_string(chattts)        
    
async def main():
    parser = argparse.ArgumentParser(description='Start an asyncio socket server.')
    parser.add_argument('--dump', type=bool, help='whether or not to dump all traffic to disk')
    args = parser.parse_args()

    server = ChatdemoServer()
    await server.serve()
            
    
if __name__ == "__main__":    
    asyncio.run(main())

