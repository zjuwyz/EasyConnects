import zmq
import io

class Socket(zmq.Socket):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        
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
