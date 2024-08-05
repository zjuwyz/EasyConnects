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
        print("Audio queue empty")
    wav, chunk = wav_queue.get()
    if wav is None:
        outdata[:] = 0
    else:
        print("playing chunk {}".format(chunk))
        l = min(len(wav), len(outdata))
        outdata[:l, 0] = wav[:l]

latency = 1.0
sr = 44100 
blocksize=int(sr * latency / 10)

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
    wav, sr, expire_time = client.recv_pyobj()
    wav_queue.put((wav, chunk_id))
    print(f"received chunk {chunk_id} expire_time {expire_time:5.2f}")
    chunk_id += 1
    time.sleep(duration / 10)
