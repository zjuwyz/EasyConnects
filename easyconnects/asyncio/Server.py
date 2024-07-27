import asyncio
import zmq
import zmq.asyncio
from typing import *

from easyconnects import EASYCONNECTS_HOST, EASYCONNECTS_PORT

import asyncio
import zmq
import zmq.asyncio
import io

class Socket(zmq.asyncio.Socket):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
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


class Server:
    def __init__(self):
        self.__tasks: Dict[str, asyncio.Task] = {}
        self.sockets: Dict[str, Socket] = {}
    
    async def serve(self):
        self.context = zmq.asyncio.Context.instance()
        self.endpoint_socket = self.context.socket(zmq.REP)
        self.endpoint_socket.bind(f"tcp://{EASYCONNECTS_HOST}:{EASYCONNECTS_PORT}")
        print(f"Server listening on {self.endpoint_socket.getsockopt(zmq.LAST_ENDPOINT).decode('ascii')}")
        
        while True:
            try:
                meta = await self.endpoint_socket.recv_json()
                if "name" not in meta:
                    raise ValueError(f"meta must contains 'name'")
                name = meta["name"]
                if not hasattr(self, f"handle_{name}"):
                    raise ValueError(f"Handler for {name} not implemented")
                
                socket = Socket(self.context, zmq.PAIR)
                socket.bind(f"tcp://*:0")
                endpoint = socket.getsockopt(zmq.LAST_ENDPOINT)
                endpoint.decode('ascii')
                handle = getattr(self, f"handle_{name}")
                
                if name in self.__tasks:
                    self.__tasks[name].cancel()
                    
                if name in self.sockets:
                    self.sockets[name].close()
                
                self.__tasks[name] = asyncio.create_task(handle(socket, meta))
                self.sockets[name] = socket
                await self.endpoint_socket.send(endpoint)
                print(f"{name} connected at {endpoint.decode('ascii')}")
                
            except ValueError as e:
                print(e)
                await self.endpoint_socket.send_string("Error: " + str(e))
                