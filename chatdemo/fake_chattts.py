from easyconnects import Client
import os
from typing import *
import time
import numpy as np
import librosa
import time


def fake_chattts(path, **kwargs):
    topic = "chattts"
    segs = list(os.listdir(path))
    segs.sort(key=lambda x: int(x))
    client=Client(topic)
    
    for seg in segs:
        print(f"seg {seg} loading file")
        import pickle
        with open(os.path.join(path, seg, 'audio.pkl'), 'rb') as f:
            wav, sr = pickle.load(f)
        print(f"loaded wav length {wav.shape[0] / sr}")
        client.send_pyobj([wav, sr])
        print("wav sent")
        time.sleep(len(wav)/sr + 5) 
        
if __name__ == "__main__":
    fake_chattts('data_segs')
    