import numpy as np
import sounddevice as sd
from easyconnects import Client
print("connecting")
client = Client('speaker')
print("connected")
while True:
    npz = client.recv_npz()
    print("recieved")
    wav, sr = npz['wav'], npz['sr']
    sd.play(wav, sr)
    sd.wait()
