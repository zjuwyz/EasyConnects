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
    files = list(os.listdir(path))
    files.sort()
    start = time.time()
    socket = Client(topic, fps=fps)
    while True:
        for frameId, file in enumerate(files):
            flame = np.load(os.path.join(path, file))
            exp_code = flame['exp_code']
            flame_pose_params = flame['flame_pose_params']
            socket.send_npz(exp_code=exp_code, flame_pose_params=flame_pose_params)
            socket.recv()
            now = time.time()
            print(f"[Flame] {now - start:.2f} flame send frameId {frameId} (+{frameId / fps:5.2f})")
            time.sleep(max(0, start + frameId / generate_fps - now))
        socket.send(b'')
        time.sleep(5)
            
if __name__ == "__main__":
    fake_flame('./data/demo_flame', fps=30, generate_fps=40)
    