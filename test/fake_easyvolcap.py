import time
from easyconnects import Client

def fake_easyvolcap(fps, render_fps, recv_time):
    

    topic = "easyvolcap"
    start = time.time()
    render_frameId = 0
    socket = Client(topic)
    socket.send_json({
        "recv_time": recv_time
    }) # meta
    print(f"meta sent")
    while True: 
        socket.send(b"")
        
        # pose_time 和 flame_time 只有测试用。
        pose = socket.recv_json()
        flame = socket.recv_npz()
        
        obj = {
            "pose_time": "n/a",
            "flame_time": "n/a"
        }
        if recv_time:
            obj.update(socket.recv_json())
        pose_time = obj["pose_time"]
        flame_time = obj["flame_time"]
                    
        # do your work here
        exp_code = flame['exp_code']
        flame_pose_params = flame['flame_pose_params']
        
        now = time.time()
        print(f"reltime: +{now - start:.2f}, smpl: +{pose_time}, flame: +{flame_time}, exp_code: {exp_code.shape}, flame_pose_params: {flame_pose_params.shape}")
        render_frameId += 1
        time.sleep(max(0, start + render_frameId / render_fps - now))
    
if __name__ == "__main__":
    fake_easyvolcap(fps = 4, render_fps=3, recv_time=True)