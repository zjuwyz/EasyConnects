import numpy as np
from easyconnects import Client
import sounddevice as sd

#client = Client('speaker')

# Initialize variables
wav = None
sr = None


def audio_callback(outdata, frames, time, status):
    global wav, sr
    if status:
        print(status)
    if wav is not None:
        # Ensure the output data size matches the requested frames
        outdata[:, 0] = wav[:len(outdata)]
        # Roll the wav array to simulate continuous playback
        wav = np.roll(wav, -len(outdata))
    else:
        outdata.fill(0)  # Silence if no data available


blocksize=2048
latency=0.1
sr = 44100 
freq = 440 # Hz, frequency of the sound you want to generate
duration = 1 # seconds
t = np.linspace(0, duration, int(sr * duration), endpoint=False)
wav = np.sin(2 * np.pi * freq * t).astype(np.float32) # Convert data to float32 type

stream = sd.OutputStream(callback=audio_callback, channels=1, dtype='float32', latency=latency, blocksize=blocksize)

client = Client('speaker', sr=sr, latency=latency, blocksize=blocksize)
stream.start()

duration = blocksize / sr
chunk_id = 0
import time
while True:
    client.send(b'')
    wav, sr = client.recv_pyobj()
    print(f"received chunk {chunk_id}")
    chunk_id += 1
    time.sleep(duration / 2)
