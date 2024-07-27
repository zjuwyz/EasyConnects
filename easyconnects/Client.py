import zmq
import zmq.asyncio
from typing import Dict, Any
import io

# Assuming EASYCONNECTS_HOST and EASYCONNECTS_PORT are defined in the same file or imported from another module
from easyconnects import EASYCONNECTS_HOST, EASYCONNECTS_PORT, Socket
    
class Client(Socket):
    
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
