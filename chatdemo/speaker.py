import numpy as np
from easyconnects import Client
import sounddevice as sd

#client = Client('speaker')

# Initialize variables
wav = None
sr = None

# Parameters
sr = 44100 # samples per second
freq = 440 # Hz, frequency of the sound you want to generate
duration = 10 # seconds
t = np.linspace(0, duration, int(sr * duration), endpoint=False)
wav = np.sin(2 * np.pi * freq * t).astype(np.float32) # Convert data to float32 type

def audio_callback(outdata, frames, time, status):
    global wav, sr
    if wav is not None:
        # Ensure the output data size matches the requested frames
        outdata[:, 0] = wav[:len(outdata)]
    else:
        outdata.fill(0)  # Silence if no data available

# Create a stream with the callback
stream = sd.OutputStream(callback=audio_callback, channels=1, dtype='float32', latency=0.1, blocksize=2048)
stream.start()

client = Client('speaker')
while True:
    npz = client.recv_npz()
    print("received")
    wav, sr = npz['wav'], npz['sr']
    # Update the stream samplerate if it changes
