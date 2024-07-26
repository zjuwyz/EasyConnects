# Import the necessary module
from easyconnects import Client

# Create a client object with a unique name for identification
alice = Client("alice")
# Additional metadata can be sent as keyword arguments to the server
bob = Client("bob", key1=1, key2="2", key3=[3, 4, 5])
# A more recent client with the same name will override the older one.
# P.S. you may not want to do that explicitly. This is for reconnection.
alice = Client("alice", alice="new")

# Clients can send and receive string messages.
alice.send_string("test string")
print(bob.recv_string())

# Clients can also send and receive raw bytes.
bob.send(b"\xDE\xAD\xBE\xEF")
print(alice.recv())

# Json-serializable objects
alice.send_json({"This is": "a dict"})
print(bob.recv_json())

# And non-json-serializable objects
bob.send_pyobj(set([1, '2']))
print(alice.recv_pyobj())

# In addition, we provide an interface that acts similar to np.savez()/np.load()
import numpy as np
alice.send_npz(mat=np.eye(5), arr=np.random.normal(size=10))
npz = bob.recv_npz()
print(npz['mat'], npz['arr'])
