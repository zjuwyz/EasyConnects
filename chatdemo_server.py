import asyncio
import zmq
import zmq.asyncio
import argparse
import time
import queue
from easyconnects import Server
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
    
    async def handle_talkshow(self, socket: zmq.asyncio.Socket):
        self.meta["talkshow"] = meta = await socket.recv_json()
        print(f"[Server] handle talkshow meta {meta}")

        fps = meta["fps"]
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
            
    async def handle_flame(self, socket: zmq.asyncio.Socket):
        self.meta["flame"] = meta = await socket.recv_json()
        print(f"[Server] handle flame meta {meta}")

        fps = meta["fps"]
        frameId = 0
        while True:
            obj = await socket.recv()
            if not obj:
                break
            await self.flame_queue.put((obj, frameId / fps))
            print(f"[Server] handle flame\t put frameId {frameId} time {frameId / fps:5.2f}")
            frameId += 1
            
    # async def handle_audio(self, socket: zmq.asyncio.Socket):
    #     while True:
    #         clip = await socket.recv()
    #         await self.audio_queue.put(clip)
    
    async def handle_easyvolcap(self, socket: zmq.asyncio.Socket):
        
        self.meta["easyvolcap"] = meta = await socket.recv_json()
        recv_time = meta["recv_time"]
        print(f"[Server] handle easyvolcap meta {meta}")
        while not (self.talkshow_queue.empty() and self.talkshow_input_finished):
            await socket.recv() # wait for renderer ready signal
            print("[Server] render ready signal recieved")
            if not self.session_on: # first frame. reset clock
                self.session_on = True
                self.clock.reset_time()
            
            # TODO 如果要做插值的话，就在这里做。目前只是拿出来了当前时刻的一帧。
            async def get_current_frame(queue: asyncio.Queue) -> Dict:
                obj, obj_time = await queue.get()
                while not queue.empty() and obj_time < self.clock.get_current_time():
                    obj, obj_time = queue.get_nowait()
                return obj, obj_time
                
            pose, pose_time = await get_current_frame(self.talkshow_queue)
            flame, flame_time = await get_current_frame(self.flame_queue)
            
            await socket.send_json(pose)
            await socket.send(flame)
            if (recv_time):
                await socket.send_json({
                    "pose_time": pose_time,
                    "flame_time": flame_time,
                })

async def main():
    parser = argparse.ArgumentParser(description='Start an asyncio socket server.')
    parser.add_argument('--dump', type=bool, help='whether or not to dump all traffic to disk')
    args = parser.parse_args()

    server = ChatdemoServer()
    await server.serve()
            
    
if __name__ == "__main__":
    
    asyncio.run(main())


