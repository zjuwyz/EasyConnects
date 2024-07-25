from easyconnects import Client
import json
import os
from typing import *
import time
def fake_talkshow(path, **kwargs):
    topic = "talkshow"
    fps = kwargs['fps']
    send_fps = kwargs['send_fps']
    loop = kwargs['loop']
    files = os.listdir(path).sort()
    start = time.time()
    
    socket = Client(topic)
    socket.send_json({
        "fps": fps
    }) # meta
    
    while loop:
        for frameId, file in enumerate(files):
            fullpath = os.path.join(path, file)
            with open(fullpath, "r") as f:
                obj = json.load(f)
            obj["fps"] = fps
            obj["frameId"] = frameId
            socket.send_json(obj)
            now = time.time()
            print(f"reltime +{now - start:.2f} talkshow send frameId {frameId} (+{frameId / fps:.2f})")
            time.sleep(max(0, start + frameId / send_fps - now))
            
        if not loop:
            break

if __name__ == "__main__":
    fake_talkshow('./data/demo_pose', fps=4, send_fps=5, loop=True)
    