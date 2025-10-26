import os, numpy as np, soundfile as sf, librosa

# Simple placeholder version — makes a funny "chicken tone" so your pipeline works.
# Later you'll replace this with your trained DDSP checkpoint.
DDSP_READY = False

def extract_f0_loudness(audio: np.ndarray, sr: int, hop_ms=10):
    import crepe
    a16 = librosa.resample(audio, orig_sr=sr, target_sr=16000)
    _, f0, conf, _ = crepe.predict(a16, 16000, step_size=hop_ms, verbose=0)
    f0 = np.where(conf > 0.5, f0, 0.0)
    hop = int(sr * (hop_ms / 1000.0))
    frames = 1 + (len(audio) - 1) // hop
    rms = []
    for i in range(frames):
        s = i * hop
        e = min(len(audio), s + hop)
        rms.append(np.sqrt(np.mean(np.square(audio[s:e]) + 1e-9)))
    return f0.astype(np.float32), np.array(rms, dtype=np.float32)

def placeholder_squeaky_synth(vocal_wav: str, out_wav: str):
    y, sr = librosa.load(vocal_wav, sr=44100, mono=True)
    f0, loud = extract_f0_loudness(y, sr, hop_ms=10)
    hop = int(sr * 0.01)
    out = np.zeros(len(y), dtype=np.float32)
    phase = 0.0
    for i, hz in enumerate(f0):
        s = i * hop
        e = min(len(out), s + hop)
        if e <= s:
            continue
        amp = loud[i] * 2.0
        if hz <= 0:
            continue
        t = np.arange(e - s) / sr
        wave = np.sin(2 * np.pi * hz * t).astype(np.float32)
        out[s:e] += amp * wave
    out /= max(1e-6, np.max(np.abs(out)))
    sf.write(out_wav, out, sr, subtype="PCM_16")

def render_chicken(vocal_wav: str, out_wav: str, checkpoint_path: str | None):
    placeholder_squeaky_synth(vocal_wav, out_wav)
