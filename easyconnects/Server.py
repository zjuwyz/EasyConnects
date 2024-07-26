import asyncio
import zmq
import zmq.asyncio
from typing import *

from easyconnects import EASYCONNECTS_HOST, EASYCONNECTS_PORT
class Server:
    def __init__(self):
        self.__tasks: Dict[str, asyncio.Task] = {}
        self.sockets: Dict[str, zmq.asyncio.Socket] = {}
    
    async def serve(self):
        self.__context = zmq.asyncio.Context.instance()
        self.__endpoint_socket = self.__context.socket(zmq.REP)
        self.__endpoint_socket.bind(f"tcp://{EASYCONNECTS_HOST}:{EASYCONNECTS_PORT}")
        print(f"Server listening on {self.__endpoint_socket.getsockopt(zmq.LAST_ENDPOINT).decode('ascii')}")
        
        while True:
            try:
                meta = await self.__endpoint_socket.recv_json()
                if "name" not in meta:
                    raise ValueError(f"meta must contains 'name'")
                name = meta["name"]
                if not hasattr(self, f"handle_{name}"):
                    raise ValueError(f"Handler for {name} not implemented")
                
                socket = self.__context.socket(zmq.PAIR)
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
                self.__endpoint_socket.send(endpoint)
                print(f"{name} connected at {endpoint.decode('ascii')}")
                
            except ValueError as e:
                print(e)
                await self.__endpoint_socket.send_string("Error: " + str(e))
                