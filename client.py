from easyconnects import Client

# Client must specify an unique name.
alice = Client("alice")
# another_alice = Client("alice")
# This will override the first alice. 

# Client can carry kwargs as metadata.
# metadata will send to server.
bob = Client("bob", key1=1, key2="2", key3=[3, 4, 5])

# Client can send messages
alice.send_string("test string")
# And also recieve
print(bob.recv_string())

# Besides string, message can be bytes
alice.send(b"\xDE\xAD\xBE\xEF")
print(bob.recv())

# ... or json
alice.send_json({"This is": "a dict"})
print(bob.recv_json())

# ... or npz, 
# follows the same api of np.savez() and np.load() 
# but without fd
import numpy as np
alice.send_npz(mat=np.eye(5), arr=np.random.normal(size=10))
npz = bob.recv_npz()
print(npz['mat'], npz['arr'])

# or pyobj, uses pickle behind the scene.
alice.send_pyobj(set([1, '2']))
print(bob.recv_pyobj())

