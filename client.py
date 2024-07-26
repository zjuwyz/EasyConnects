from easyconnects import Client

# Create a client object with a unique name for identification
alice = Client("alice")

# Additional metadata can be sent as keyword arguments to the server
bob = Client("bob", key1=1, key2="2", key3=[3, 4, 5])

# A recent client with the same name will override the old one.
# P.S. you may not want to do that explicitly. This is for reconnection.
alice = Client("alice", alice="new")

# Clients can send/receive string messages.
alice.send_string("test string")
print(bob.recv_string())

# And also raw bytes.
bob.send(b"\xDE\xAD\xBE\xEF")
print(alice.recv())

# Json-serializable objects
alice.send_json({"This is": "a dict"})
print(bob.recv_json())

# And non-json-serializable objects
bob.send_pyobj(set([1, '2']))
print(alice.recv_pyobj())

# send_npz()/recv_npz() works like np.savez()/np.load()
import numpy as np
alice.send_npz(mat=np.eye(5), arr=np.random.normal(size=10))
npz = bob.recv_npz()
print(npz['mat'], npz['arr'])

# send_pt()/load_pt() works like torch.save()/torch.load()
import torch
t = torch.randn(10)
bob.send_pt(t)
print(alice.recv_pt())