from easyconnects import Client
import os
from typing import *
import time
import numpy as np
import zmq
def fake_flame(path, **kwargs):
    
    topic = "flame"
    fps = kwargs['fps']
    generate_fps = kwargs['generate_fps']
    segs = list(os.listdir(path))
    segs.sort(key=lambda x: int(x))
    client = Client(topic, fps=fps)
    
    for seg in segs:
        start = time.time()
        files = list(os.listdir(os.path.join(path, seg, 'flame')))
        files.sort()
        print(f"[Flame] waiting seg {seg} input from chattts")
        client.recv()
        print(f"[Flame] inferenceing seg {seg}")
        time.sleep(8)
        print(f"[Flame] inferenceing seg {seg} done")

        for frameId, file in enumerate(files):
            flame = np.load(os.path.join(path, seg, 'flame', file))
            exp_code = flame['exp_code']
            flame_pose_params = flame['flame_pose_params']
            client.send_npz(exp_code=exp_code, flame_pose_params=flame_pose_params)
            now = time.time()
            print(f"[Flame] {now - start:.2f} flame send frameId {frameId} (+{frameId / fps:5.2f})")
            time.sleep(max(0, start + frameId / generate_fps - now))
        client.send(b'')
            
if __name__ == "__main__":
    fake_flame('./data_segs', fps=30, generate_fps=40)
    