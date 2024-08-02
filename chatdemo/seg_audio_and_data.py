import librosa
import numpy as np

from faster_whisper import WhisperModel
whisper_model = WhisperModel('large-v2', device="cuda", device_index=0, compute_type="float16", local_files_only=True)
segments, info = whisper_model.transcribe('./data/0703_1_sync.mp3', language='zh', initial_prompt="以下是简体中文。" )

wav, sr = librosa.load(f'./data/0703_1_sync.mp3')
print('sr=', sr)
for seg_id, segment in enumerate(segments):
    print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
    import os
    d = f'./data_segs/{seg_id:02}/'
    os.makedirs(d, exist_ok=True)
    wav_seg = wav[int(segment.start*sr): int(segment.end*sr)]
    fps = 30
    file_seg_start, file_seg_stop = int(segment.start * fps), int(segment.end * fps)
    os.makedirs(d + 'pose', exist_ok=True)
    os.makedirs(d + 'flame', exist_ok=True)
    with open(d + 'text.txt', 'w') as f:
        f.write(segment.text)
    with open(d + 'audio.pkl', 'wb') as f:
        import pickle
        pickle.dump([wav_seg, sr], f)
    np.savez(d + 'audio.npz', wav=wav_seg, sr=sr)
    for i in range(file_seg_start, file_seg_stop):
        import shutil
        # poses are json files
        shutil.copy(f'./data/demo_pose/{i:06d}.json', d + 'pose')
        # flames are npz files
        shutil.copy(f'./data/demo_flame/{i:06d}.npz', d + 'flame')