import numpy as np
from easyconnects import Client
import sounddevice as sd
import queue
#client = Client('speaker')

# Initialize variables
wav_queue = queue.Queue()

def audio_callback(outdata: np.ndarray, frames, time, status):
    global wav, sr
    if wav_queue.empty() or (wav := wav_queue.get()) is None:
        outdata.fill(0)  # Silence if no data available
    else:
        l = max(len(wav), len(outdata))
        outdata[:l, 0] = wav[:l]

latency = 0.5
sr = 44100 
blocksize=int(sr * latency / 5)

# freq = 440 # Hz, frequency of the sound you want to generate
# duration = 1 # seconds
# t = np.linspace(0, duration, int(sr * duration), endpoint=False)
# wav = np.sin(2 * np.pi * freq * t).astype(np.float32) # Convert data to float32 type

stream = sd.OutputStream(callback= audio_callback, channels=1, dtype='float32', latency=latency, blocksize=blocksize)
client = Client('speaker', sr=sr, latency=latency, blocksize=blocksize)

stream.start()

duration = blocksize / sr
chunk_id = 0
import time
while True:
    client.send(b'')
    wav, sr = client.recv_pyobj()
    wav_queue.put(wav)
    print(f"received chunk {chunk_id}")
    chunk_id += 1
    time.sleep(duration / 10)
