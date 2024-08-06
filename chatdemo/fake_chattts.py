from easyconnects import Client
import os
from typing import *
import time
import numpy as np
import librosa
import time

def is_speaking(audio, sr):
    # Calculate the RMS (Root Mean Square) of the audio signal
    rms = np.sqrt(np.mean(np.square(audio)))
    # If the RMS is above a certain threshold, assume speech is present
    return rms > 0.01

def pad_audio(wav, sr):
    # Check if there's speech in the first second of the audio
    if is_speaking(wav[:sr], sr):
        wav = np.concatenate([np.zeros(sr, dtype=np.float32), wav])
    # Check if there's speech in the last second of the audio
    if is_speaking(wav[-sr:], sr):
        wav = np.concatenate([wav, np.zeros(sr, dtype=np.float32)])
    return wav

def fake_chattts(path, **kwargs):
    topic = "chattts"
    segs = list(os.listdir(path))
    segs.sort(key=lambda x: int(x))
    wav, sr = librosa.load("data/infer.mp3")
    #wav, sr = librosa.load("data/0703_1_sync.mp3")
    #wav, sr = np.zeros((44100 * 100), dtype=np.float32), 44100
    client=Client(topic, sr=sr)
    
    from easyconnects import TimeStamp
    ts = TimeStamp(0, 0, sr / len(wav))
    input()
    print("send wav")
    client.send_pyobj([wav, sr])
    client.recv()
    # for seg in segs:
    #     print(f"seg {seg} loading file")
    #     import pickle
    #     with open(os.path.join(path, seg, 'audio.pkl'), 'rb') as f:
    #         wav, sr = pickle.load(f)
    #         wav = pad_audio(wav, sr)

    #     # TODO: Padding with an empty second of audio
    #     # if there's people speaking in last 1 second, pad with 1 second empty wav
    #     # Also if there's people speaking in first 1 seconds, pad with 1 second wav
    #     print(f"loaded wav length {wav.shape[0] / sr}")
    #     client.send_pyobj([wav, sr])
    #     print("wav sent")
    #     time.sleep(len(wav)/sr + 5) 
        
if __name__ == "__main__":
    fake_chattts('data_segs')
    