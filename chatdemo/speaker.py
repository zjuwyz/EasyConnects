import numpy as np
from easyconnects import Client, logger
import sounddevice as sd
import queue
#client = Client('speaker')

# Initialize variables
wav_queue = queue.Queue()
latency = 1.2

def audio_callback(outdata: np.ndarray, frames, time, status):
    global wav, sr
    if wav_queue.empty() or (wav := wav_queue.get()) is None:
        print("Audio queue empty")
    wav = wav_queue.get()
    if wav is None:
        outdata[:] = 0
    else:
        l = min(len(wav), len(outdata))
        outdata[:l, 0] = wav[:l]

sr = 44100
chunk_size=sr // 20


# freq = 440 # Hz, frequency of the sound you want to generate
# duration = 1 # seconds
# t = np.linspace(0, duration, int(sr * duration), endpoint=False)
# wav = np.sin(2 * np.pi * freq * t).astype(np.float32) # Convert data to float32 type

stream = sd.OutputStream(callback= audio_callback, channels=1, dtype='float32', latency=latency, blocksize=chunk_size)
client = Client('speaker', sr=sr, chunk_size=chunk_size)

stream.start()
pre_enque = int(latency / (chunk_size / sr))

is_start = True
while True:
    client.send(b'')
    wav, wav_ts = client.recv_pyobj()
    
    if is_start:
        for i in range(pre_enque):
            wav_queue.put(None)
    assert(len(wav) % chunk_size == 0)
    for i in range(len(wav) // chunk_size):
        wav_queue.put(wav[i, i + chunk_size])
    logger.info(f"audio recieved {wav_ts}")
    wav_queue.put(wav)