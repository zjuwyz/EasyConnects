import asyncio
import zmq
import zmq.asyncio
from typing import *
PORT = 12000
HOST = "localhost"
import io
import numpy as np
class Server:
    def __init__(self):
        self.__tasks: Dict[str, asyncio.Task] = {}
        self.sockets: Dict[str, zmq.asyncio.Socket] = {}
    
    async def handle_test(self, socket: zmq.asyncio.Socket):
        while True:
            print(await socket.recv_string())
            
    async def serve(self):
        self.__context = zmq.asyncio.Context.instance()
        self.__endpoint_socket = self.__context.socket(zmq.REP)
        self.__endpoint_socket.bind(f"tcp://{HOST}:{PORT}")
        print(f"Server listening on {self.__endpoint_socket.getsockopt(zmq.LAST_ENDPOINT).decode('ascii')}")
        
        while True:
            try:
                name = await self.__endpoint_socket.recv_string()
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
                
                self.__tasks[name] = asyncio.create_task(handle(socket))
                self.sockets[name] = socket
                self.__endpoint_socket.send(endpoint)
                print(f"{name} connected at {endpoint.decode('ascii')}")
                
            except ValueError as e:
                print(e)
                await self.__endpoint_socket.send_string("Error: " + str(e))
                
    
class Client(zmq.Socket):               
    def __init__(self, name):
        context = zmq.Context.instance()
        init_socket: zmq.Socket = context.socket(zmq.REQ)
        init_socket.connect(f"tcp://{HOST}:{PORT}")
        init_socket.send_string(name)
        endpoint = init_socket.recv_string()
        init_socket.close()
        if endpoint.startswith("Error"):
            raise ValueError(endpoint)
        print(f"Client {name} recieved endpoint: {endpoint}")
        super().__init__(context, zmq.PAIR)
        super().connect(endpoint)
    
    def send_npz(self, *args, **kwargs):
        buf = io.BytesIO()
        np.savez(buf, *args, **kwargs)
        self.send(buf)
        
    def recv_npz(self):
        b = self.recv()
        buf = io.BytesIO(b)
        return np.load(buf)
        
    
    
if __name__ == "__main__":
    import threading
    def client_thread():
        client = Client("test")
        i = 0
        while True:
            client.send_string(f"{i}")
            i += 1
            import time
            time.sleep(1)
            
    thread = threading.Thread(target=client_thread)
    thread.start()
    
    asyncio.run(Server().serve())