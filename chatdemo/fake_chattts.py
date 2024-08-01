from easyconnects import Client
import os
from typing import *
import time
import numpy as np
import librosa
import time


def fake_chattts(path, **kwargs):
    topic = "chattts"
    print("loading file")
    wav, sr = librosa.load(path, sr=None)
    print("loaded")
    client=Client(topic)
    while True:
        client.send_pyobj([wav, sr])
        print("client send npz")
        time.sleep(len(wav)/sr + 5)
        
if __name__ == "__main__":
    fake_chattts('./data/0703_1_sync.mp3')
    