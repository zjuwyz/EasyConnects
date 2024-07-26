from easyconnects import Client
import json
import os
from typing import *
import time
def fake_talkshow(path, **kwargs):
    
    topic = "talkshow"
    fps = kwargs['fps']
    generate_fps = kwargs['generate_fps']
    loop = kwargs['loop']
    files = os.listdir(path)
    files.sort()
    start = time.time()
    socket = Client(topic, fps=fps)

    while True:
        for frameId, file in enumerate(files):
            fullpath = os.path.join(path, file)
            with open(fullpath, "r") as f:
                obj = json.load(f)
            socket.send_json(obj)
            now = time.time()
            print(f"[Talkshow] {now - start:.2f} talkshow send frameId {frameId} (+{frameId / fps:.2f})")
            time.sleep(max(0, start + frameId / generate_fps - now))
            
        if not loop:
            break

if __name__ == "__main__":
    fake_talkshow('./data/demo_pose', fps=5, generate_fps=6, loop=True)
    