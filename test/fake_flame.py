from easyconnects import Client
import os
from typing import *
import time
import numpy as np
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
    })
    
    while loop:
        for frameId, file in enumerate(files):
            flame = np.load(os.path.join(path, file))
            exp_code = flame['exp_code']
            flame_pose_params = flame['flame_pose_params']
            socket.send_npz(exp_code=exp_code, flame_pose_params=flame_pose_params)
            now = time.time()
            print(f"reltime +{now - start:.2f} flame send frameId {frameId} (+{frameId / fps:.2f})")
            time.sleep(max(0, start + frameId / send_fps - now))
            
        if not loop:
            break

if __name__ == "__main__":
    fake_talkshow('./data/demo_flame', fps=4, send_fps=5, loop=True)
    