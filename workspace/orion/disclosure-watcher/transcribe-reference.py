from faster_whisper import WhisperModel
import numpy as np, wave
w=wave.open("lit_q3.wav"); audio=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768.0
m = WhisperModel("small.en", device="cpu", compute_type="int8", cpu_threads=4)
segs, info = m.transcribe(audio, vad_filter=True, beam_size=1, initial_prompt="Lighter, LIT, zkLighter, perps, buyback, Robinhood, staking, TVL, open interest")
with open("lit_q3.txt","w") as f:
    for s in segs:
        f.write(f"[{int(s.start//60):02d}:{int(s.start%60):02d}] {s.text.strip()}\n"); f.flush()
print("done")
