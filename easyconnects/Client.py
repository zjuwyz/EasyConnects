import zmq
from typing import Dict, Any
import io
import threading

# Assuming EASYCONNECTS_HOST and EASYCONNECTS_PORT are defined in the same file or imported from another module
from easyconnects import EASYCONNECTS_HOST, EASYCONNECTS_PORT

class Socket(zmq.Socket):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def send_int(self, x: int, length=4, endian="little", *args, **kwargs):
        self.send(x.to_bytes(length, byteorder=endian), *args, **kwargs)
        
    def send_npz(self, *args, **kwargs):
        import numpy as np
        buf = io.BytesIO()
        np.savez(buf, *args, **kwargs)
        buf.seek(0)
        self.send(buf.read())
    
    def recv_int(self, endian="little", *args, **kwargs):
        return int.from_bytes(self.recv(*args, **kwargs), byteorder=endian)
        
        
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
        super().__init__(zmq.Context.instance(), zmq.PAIR)
        # Setup monitor thread
        monitor_url = f"inproc://monitor-{name}"
        monitor_socket: zmq.Socket = context.socket(zmq.PAIR)
        monitor_socket.connect(monitor_url)
        threading.Thread(target=self.monitor_loop, args=(monitor_socket, kwargs)).start()
        self.monitor(monitor_url, zmq.EVENT_CONNECTED | zmq.EVENT_DISCONNECTED)
        self.__dict__['connected_event'] = None
        self.connected_event = threading.Event()
        # Connect to meta socket
        meta_socket: zmq.Socket = context.socket(zmq.REQ)
        meta_socket.connect(f"tcp://{EASYCONNECTS_HOST}:{EASYCONNECTS_PORT}")
        meta_socket.send_string(name)
        endpoint = meta_socket.recv_string()
        meta_socket.close()
        if endpoint.startswith("Error"):  raise ValueError(f"Error: {endpoint}")
        # Confirm connection to server
        self.connect(endpoint)
        self.connected_event.wait()
        
        
    def monitor_loop(self, socket: Socket, meta):

        while True:
            event_type, event_val = socket.recv_multipart()
            if event_type == zmq.EVENT_CONNECTED:
                print("Connected to server.")
                self.send_pyobj(meta)
                self.connected_event.set()
                
            elif event_type == zmq.EVENT_DISCONNECTED:
                print(f"Disconencted from server")
                
        
    def close(self):
        self.send_string("exit")
        super().close()
        
