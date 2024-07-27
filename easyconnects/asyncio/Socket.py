import asyncio
import zmq
import zmq.asyncio
import io

class Socket(zmq.asyncio.Socket):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        
    async def send_npz(self, *args, **kwargs):
        import numpy as np
        buf = io.BytesIO()
        np.savez(buf, *args, **kwargs)
        buf.seek(0)
        await self.send(buf.read())
        
    async def recv_npz(self, *args, **kwargs):
        import numpy as np
        buf = io.BytesIO(await self.recv())
        return np.load(buf, *args, **kwargs)

    async def send_pt(self, x):
        import torch
        buf = io.BytesIO()
        torch.save(x, buf)
        buf.seek(0)
        await self.send(buf.read())
        
    async def recv_pt(self, *args, **kwargs):
        import torch
        buf = io.BytesIO(await self.recv())
        return torch.load(buf, *args, **kwargs)
