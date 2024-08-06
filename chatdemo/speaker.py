import numpy as np
from easyconnects import Client, logger
import sounddevice as sd
import queue
#client = Client('speaker')

# Initialize variables
wav_queue = queue.Queue()

def audio_callback(outdata: np.ndarray, frames, time, status):
    global wav, sr
    if wav_queue.empty():
        print("Audio queue empty")
    wav = wav_queue.get()
    if wav is None:
        logger.debug("audio write 0")
        outdata[:] = 0
    else:
        logger.debug(f"audio write {l}")
        l = min(len(wav), len(outdata))
        outdata[:l, 0] = wav[:l]
latency = 1.2
sr = 44100  
chunk_size=sr // 20
stream = sd.OutputStream(callback=audio_callback, channels=1, dtype='float32', latency=latency, blocksize=chunk_size)
ret = stream.start()

client = Client('speaker', sr=sr, chunk_size=chunk_size)
pre_enque = int(latency / (chunk_size / sr))

is_start = True
while True:
    client.send(b'')
    wav, wav_ts = client.recv_pyobj()
    if is_start:
        for i in range(pre_enque):
            wav_queue.put(None)
        is_start = False
    assert(len(wav) % chunk_size == 0)
    for i in range(len(wav) // chunk_size):
        wav_queue.put(wav[chunk_size * i:chunk_size * i + chunk_size])
    logger.info(f"audio recieved {wav_ts}")
    wav_queue.put(wav)