import os, numpy as np, soundfile as sf, librosa

def _extract_f0_loudness(audio: np.ndarray, sr: int, hop_ms=10):
    import crepe
    a16 = librosa.resample(audio, orig_sr=sr, target_sr=16000)
    _, f0, conf, _ = crepe.predict(a16, 16000, step_size=hop_ms, verbose=0)
    f0 = np.where(conf > 0.5, f0, 0.0).astype(np.float32)
    hop = int(sr * (hop_ms / 1000.0))
    frames = max(1, (len(audio) + hop - 1) // hop)
    rms = np.zeros(frames, dtype=np.float32)
    for i in range(frames):
        s = i * hop
        e = min(len(audio), s + hop)
        if e > s:
            rms[i] = np.sqrt(np.mean(audio[s:e] ** 2) + 1e-9)
    return f0, rms, hop

def _placeholder_squeak(vocal_wav: str, out_wav: str):
    y, sr = librosa.load(vocal_wav, sr=44100, mono=True)
    f0, loud, hop = _extract_f0_loudness(y, sr, hop_ms=10)
    out = np.zeros(hop * len(f0), dtype=np.float32)
    phase = 0.0
    for i, hz in enumerate(f0):
        s = i * hop
        e = min(len(out), s + hop)
        if e <= s:
            continue
        seg = e - s
        t = np.arange(seg, dtype=np.float32) / sr
        if hz <= 0:
            continue
        wob = 1.0 + 0.02 * np.sin(2 * np.pi * 6.0 * t)  # 6 Hz wobble
        omega = 2 * np.pi * hz * wob / sr
        ph = phase + np.cumsum(omega).astype(np.float32)
        wave = np.tanh(3.0 * np.sin(ph))  # soft-clip for squeak timbre
        phase = float(ph[-1] % (2 * np.pi))
        amp = min(2.5, 8.0 * float(loud[i]))
        out[s:e] += amp * wave
    peak = np.max(np.abs(out)) or 1.0
    out *= 0.95 / peak
    sf.write(out_wav, out, sr, subtype="PCM_16")

def render_chicken(vocal_wav: str, out_wav: str, checkpoint_path: str | None):
    # TODO: swap this with real DDSP inference using your trained checkpoint.
    _placeholder_squeak(vocal_wav, out_wav)
