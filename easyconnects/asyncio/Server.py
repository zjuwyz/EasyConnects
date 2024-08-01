import asyncio
import zmq
import zmq.asyncio
from typing import *

from easyconnects import EASYCONNECTS_HOST, EASYCONNECTS_PORT, EC_KNOWN_PORTS

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
        self.socket_by_name: Dict[str, Socket] = {}
        self.ready: Dict[str, asyncio.Event] = {}
        self.metea_by_name: Dict[str, Any] = {}
    
    async def wait_ready(self, name):
        if name not in self.ready: self.ready[name] = asyncio.Event()
        await self.ready[name].wait()
    
    async def set_ready(self, name):
        if name not in self.ready: self.ready[name] = asyncio.Event()
        self.ready[name].set()
        
    # def recover_known_clients(self):
    #     for name, port in EC_KNOWN_PORTS.items():
    #         endpoint = f"tcp://{EASYCONNECTS_HOST}:{port}"
    #         socket = self.socket_by_name[name] = self.context.socket(zmq.PAIR, Socket)
    #         socket.bind(endpoint)
    #         asyncio.create_task(self.init_client(name, socket))
    
    async def init_client(self, name: str, socket: Socket):
        endpoint = socket.getsockopt(zmq.LAST_ENDPOINT).decode('ascii')
        handle = getattr(self, f"handle_{name}")
        if name not in self.ready: self.ready[name] = asyncio.Event()
        self.metea_by_name[name] = meta = await socket.recv_pyobj()
        self.ready[name].set()
        self.__tasks[name] = asyncio.create_task(handle(socket, meta))
        self.socket_by_name[name] = socket
        print(f"{name} connected at {endpoint}")

    async def serve(self):
        self.context = zmq.asyncio.Context.instance()
        #self.recover_known_clients()
        self.endpoint_socket = self.context.socket(zmq.REP)
        self.endpoint_socket.bind(f"tcp://*:{EASYCONNECTS_PORT}")
        print(f"Server listening on {self.endpoint_socket.getsockopt(zmq.LAST_ENDPOINT).decode('ascii')}")
        while True:
            try:
                name = await self.endpoint_socket.recv_string()
                if not hasattr(self, f"handle_{name}"):
                    raise ValueError(f"Handler for {name} not implemented")
                
                if name in self.socket_by_name:
                    self.__tasks[name].cancel()
                    self.socket_by_name[name].close()
                    del self.__tasks[name]
                    del self.socket_by_name[name]
                    del self.ready[name]
                    await asyncio.sleep(0.01) # wait for socket fully closed
                    
                if name not in EC_KNOWN_PORTS:
                    socket = Socket(self.context, zmq.PAIR)
                    socket.bind(f"tcp://{EASYCONNECTS_HOST}:0")
                    endpoint = socket.getsockopt(zmq.LAST_ENDPOINT)
                    endpoint.decode('ascii')
                else:
                    socket = Socket(self.context, zmq.PAIR)
                    endpoint=f"tcp://{EASYCONNECTS_HOST}:{EC_KNOWN_PORTS[name]}"
                    socket.bind(endpoint)
                    
                await self.endpoint_socket.send_string(endpoint)
                await self.init_client(name, socket)
                
            except ValueError as e:
                print(e)
                await self.endpoint_socket.send_string("Error: " + str(e))
                