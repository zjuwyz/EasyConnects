import zmq
import zmq.asyncio
from typing import Dict, Any
import io

# Assuming EASYCONNECTS_HOST and EASYCONNECTS_PORT are defined in the same file or imported from another module
from easyconnects import EASYCONNECTS_HOST, EASYCONNECTS_PORT
    
class Client(zmq.Socket):
    
    def __init__(self, name: str, **kwargs: Dict[str, Any]):
        # Connect to meta socket
        kwargs["name"] = name
        context = zmq.Context.instance()
        meta_socket: zmq.Socket = context.socket(zmq.REQ)
        meta_socket.connect(f"tcp://{EASYCONNECTS_HOST}:{EASYCONNECTS_PORT}")
        meta_socket.send_json(kwargs)
        endpoint = meta_socket.recv_string()
        meta_socket.close()
        
        if endpoint.startswith("Error"):
            raise ValueError(f"Error: {endpoint}")
        print(f"Client {name} received endpoint: {endpoint}")
        
        super().__init__(zmq.Context.instance(), zmq.PAIR)
        self.connect(endpoint)

    def send_npz(self, *args, **kwargs):
        import numpy as np
        buf = io.BytesIO()
        np.savez(buf, *args, **kwargs)
        buf.seek(0)
        self.send(buf.read())
        
    def recv_npz(self, *args, **kwargs):
        import numpy as np
        buf = io.BytesIO(self.recv())
        return np.load(buf, *args, **kwargs)

    def send_pt(self, x):
        import torch
        buf = io.BytesIO()
        torch.save(x, buf)
        buf.seek(0)
        self.send(buf.read())
        
    def recv_pt(self, *args, **kwargs):
        import torch
        buf = io.BytesIO(self.recv())
        return torch.load(buf, *args, **kwargs)
