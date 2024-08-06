import numpy as np
import sounddevice as sd

# 设置参数
duration = 1.0  # 音频持续时间（秒）
fs = 44100      # 采样率，每秒样本数
f = 440.0       # 频率，赫兹

# 生成时间轴
t = np.linspace(0, duration, int(fs * duration), endpoint=False)

# 生成正弦波
audio_signal = np.sin(2 * np.pi * f * t)

# 调整音量，避免过载
audio_signal = audio_signal * (0.5 / np.max(np.abs(audio_signal)))

# 播放音频
sd.play(audio_signal, fs)
sd.wait()  # 等待音频播放完成