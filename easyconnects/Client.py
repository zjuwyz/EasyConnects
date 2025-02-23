import zmq
from typing import Dict, Any
import io

# Assuming EASYCONNECTS_HOST and EASYCONNECTS_PORT are defined in the same file or imported from another module
from easyconnects import EASYCONNECTS_HOST, EASYCONNECTS_PORT

class Socket(zmq.Socket):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
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


class Client(Socket):
    def __init__(self, name: str, **kwargs: Dict[str, Any]):
        kwargs["name"] = name
        context = zmq.Context.instance()

        # Connect to meta socket
        meta_socket: zmq.Socket = context.socket(zmq.REQ)
        meta_socket.connect(f"tcp://{EASYCONNECTS_HOST}:{EASYCONNECTS_PORT}")
        meta_socket.send_string(name)
        endpoint = meta_socket.recv_string()
        meta_socket.close()
        if endpoint.startswith("Error"):  raise ValueError(f"Error: {endpoint}")
        # Confirm connection to server by sending meta.
        super().__init__(context, zmq.PAIR)
        self.connect(endpoint)
        self.send_pyobj(kwargs)
        self.recv()
        print("Server connected")
        
    def close(self):
        self.send_string("exit")
        super().close()
        
