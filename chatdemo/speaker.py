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
    wav, wav_ts = wav_queue.get()
    if wav is None:
        logger.debug("audio write 0")
        outdata[:] = 0
    else:
        l = min(len(wav), len(outdata))
        outdata[:l, 0] = wav[:l]
        logger.debug(f"audio playing {wav_ts}")
        
latency = 1.2
sr = 44100  
chunk_size=sr // 20
stream = sd.OutputStream(callback=audio_callback, samplerate=sr, channels=1, dtype='float32', latency=latency, blocksize=chunk_size)

client = Client('speaker', sr=sr, chunk_size=chunk_size)
pre_enque = int(latency / (chunk_size / sr))

while True:
    wav, wav_ts = client.recv_pyobj()
    stream.start()
    
    for i in range(pre_enque - wav_queue.qsize()):
        wav_queue.put((None, None))
    is_start = False
    assert(len(wav) % chunk_size == 0)
    chunks = len(wav) // chunk_size
    
    for i in range(chunks):
        wav_clip = wav[chunk_size * i: chunk_size * i + chunk_size]
        wav_clip_ts = wav_ts.partition(index=i, total=chunks)
        wav_queue.put((wav_clip, wav_clip_ts))
    logger.info(f"audio recieved {wav_ts}")