import time
from socketserver.socket_utils import Client

def fake_easyvolcap(topic, fps, render_fps):
    socket = Client(topic)
    start = time.time()
    render_frameId = 0
    while True:
        socket.send(b"")
        pose = socket.recv_json()
        flame = socket.recv_npz()
        
        # do your work here
        exp_code = flame['exp_code']
        flame_pose_params = flame['flame_pose_params']
        
        now = time.time()
        frameId = pose['frameId']
        print(f"reltime: +{now - start:.2f}, smpl frameId {frameId} (+{frameId / fps:.2f}),  exp_code: {exp_code.shape}, flame_pose_params: {flame_pose_params.shape}")
        render_frameId += 1
        time.sleep(max(0, start + render_frameId / render_fps - now))
    
if __name__ == "__main__":
    fake_easyvolcap(topic="easyvolcap", fps = 4, render_fps=3)