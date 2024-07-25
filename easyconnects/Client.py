import asyncio
import zmq
import zmq.asyncio
from typing import *

import io
import numpy as np
from . import EASYCONNECTS_HOST, EASYCONNECTS_PORT
    
class Client(zmq.Socket):               
    def __init__(self, name):
        context = zmq.Context.instance()
        init_socket: zmq.Socket = context.socket(zmq.REQ)
        init_socket.connect(f"tcp://{EASYCONNECTS_HOST}:{EASYCONNECTS_PORT}")
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
        