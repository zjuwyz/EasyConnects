from easyconnects import Client
import json
import os
from typing import *
import time
import zmq
def fake_talkshow(path, **kwargs):
    
    topic = "talkshow"
    fps = kwargs['fps']
    generate_fps = kwargs['generate_fps']
    segs = list(os.listdir(path))
    segs.sort(key=lambda s: int(s))
    client = Client(topic, fps=fps, sr=22000)
    
    for seg in segs:
        start = time.time()
        files = list(os.listdir(os.path.join(path, seg, 'pose')))
        files.sort()
        print(f"[Talkshow] waiting seg {seg} input from chattts")
        client.recv()
        print(f"[Talkshow] inferencing seg {seg}")
        time.sleep(5)
        print(f"[Talkshow] inferencing seg {seg} done")
        for frameId, file in enumerate(files):
            fullpath = os.path.join(path, seg, 'pose', file)
            with open(fullpath, "r") as f:
                obj = json.load(f)        
            client.send_json(obj)
            now = time.time()
            print(f"[Talkshow] {now - start:.2f} talkshow send frameId {frameId} (+{frameId / fps:.2f})")
            time.sleep(max(0, start + frameId / generate_fps - now))
        client.send(b'')
        time.sleep(5)
        

if __name__ == "__main__":
    fake_talkshow('./data_segs', fps=30, generate_fps=40)
    