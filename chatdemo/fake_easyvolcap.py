import time
from easyconnects import Client

def fake_easyvolcap(render_fps, has_timestamp: bool):
    
    topic = "easyvolcap"
    render_frameId = 0
    
    client = Client(topic, has_timestamp=has_timestamp)
    while True: 
        # 发个 ready 信号
        client.send(b"")
        
        pose = client.recv_json()
        flame = client.recv_npz()

        exp_code = flame['exp_code']
        flame_pose_params = flame['flame_pose_params']
        # do your work here
        obj = {
            "pose_time": "n/a",
            "flame_time": "n/a"
        }
        if has_timestamp:
            obj.update(client.recv_json())
            
        pose_time = obj["pose_time"]
        flame_time = obj["flame_time"]
                    
        print(f"smpl: +{pose_time:5.2f}, flame: +{flame_time:5.2f}, exp_code: {exp_code.shape}, flame_pose_params: {flame_pose_params.shape}")
        render_frameId += 1
        time.sleep(1 / render_fps)
    
if __name__ == "__main__":
    fake_easyvolcap(render_fps=50, has_timestamp=True)