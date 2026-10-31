"""Synthesised (royalty-free) SFX for the hook. usage: python3 sfx.py outdir"""
import numpy as np, wave, sys, os

SR = 48000
out = sys.argv[1]
os.makedirs(out, exist_ok=True)
rng = np.random.default_rng(7)


def save(name, x):
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    x = x / (np.abs(x).max() + 1e-9) * 0.89
    with wave.open(os.path.join(out, name), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def t_(d):
    return np.arange(int(d * SR)) / SR


def lowpass(x, fc):  # one-pole, fc may be array
    y = np.zeros_like(x); a = np.exp(-2 * np.pi * np.broadcast_to(fc, x.shape) / SR); s = 0.0
    for i in range(len(x)):
        s = (1 - a[i]) * x[i] + a[i] * s; y[i] = s
    return y


def highpass(x, fc):
    return x - lowpass(x, fc)


# 1. riser: filtered noise + rising detuned tones, exponential swell
def riser(d):
    t = t_(d); p = t / d
    n = highpass(lowpass(rng.standard_normal(len(t)), 300 + 7000 * p ** 2), 200)
    f = 110 * 2 ** (2.5 * p)
    tone = sum(np.sin(2 * np.pi * np.cumsum(f * k * (1 + dt)) / SR) / k for k, dt in [(1, 0), (1, 0.006), (2, -0.004), (3, 0.003)])
    env = p ** 2.2
    return (0.55 * n / (np.abs(n).max() + 1e-9) + 0.45 * tone / 2.5) * env


# 2. boom / impact: pitch-dropping sub + noise click + long tail
def boom(d=2.8):
    t = t_(d)
    f = 38 + 90 * np.exp(-t * 9)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6)
    click = lowpass(rng.standard_normal(len(t)), 2500) * np.exp(-t * 35)
    tail = lowpass(rng.standard_normal(len(t)), 600) * np.exp(-t * 2.2) * 0.25
    x = sub + 0.6 * click / (np.abs(click).max() + 1e-9) + tail / (np.abs(tail).max() + 1e-9) * 0.2
    return np.tanh(1.8 * x)


# 3. heartbeat accelerating
def heartbeat(d, bpm0=70, bpm1=105):
    t = t_(d); x = np.zeros_like(t); pos = 0.15
    def thump(at, amp):
        i0 = int(at * SR); tt = t_(0.25)
        s = np.sin(2 * np.pi * (55 + 25 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 16) * amp
        j = min(len(x), i0 + len(s)); x[i0:j] += s[: j - i0]
    while pos < d - 0.3:
        bpm = bpm0 + (bpm1 - bpm0) * pos / d
        thump(pos, 1.0); thump(pos + 0.17, 0.7)
        pos += 60 / bpm
    return np.tanh(2.2 * x)


# 4. reverse swoosh (sucks into the cut)
def rev_swoosh(d=1.0):
    t = t_(d)
    n = lowpass(rng.standard_normal(len(t)), 1500 + 6000 * np.exp(-t * 4)) * np.exp(-t * 5)
    return n[::-1]


# 5. glitch hit: stuttered digital burst
def glitch(d=0.45):
    t = t_(d); x = np.zeros_like(t); seg = int(0.03 * SR)
    for i in range(0, len(t), seg):
        f = rng.choice([180, 360, 720, 1440, 95])
        tt = t_(seg / SR)[: len(t) - i]
        sq = np.sign(np.sin(2 * np.pi * f * tt)) * (rng.random() > 0.25)
        x[i:i + len(tt)] = 0.6 * sq + 0.4 * rng.standard_normal(len(tt))
    return x * np.exp(-t * 4) + boom(d) * 0.8


# 6. whoosh (transition)
def whoosh(d=0.7):
    t = t_(d); p = t / d
    env = np.sin(np.pi * p) ** 2
    n = lowpass(rng.standard_normal(len(t)), 400 + 5000 * np.sin(np.pi * p))
    pan = np.stack([n * (1 - p), n * p], 1) * env[:, None]
    return pan


# 7. soft hit for key phrases: short sub thump + airy click (sits under the voice)
def hit(d=0.5):
    t = t_(d)
    sub = np.sin(2 * np.pi * np.cumsum(60 + 80 * np.exp(-t * 25)) / SR) * np.exp(-t * 9)
    air = highpass(lowpass(rng.standard_normal(len(t)), 6000), 1500) * np.exp(-t * 28)
    return np.tanh(1.5 * (sub + 0.35 * air / (np.abs(air).max() + 1e-9)))


# 8. pop for the subscribe button: quick rising blip
def pop(d=0.22):
    t = t_(d)
    f = 500 + 900 * (1 - np.exp(-t * 40))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 18) * (1 - np.exp(-t * 800))


if __name__ == "__main__":
    d = float(sys.argv[2]) if len(sys.argv) > 2 else 2.9
    save("riser.wav", riser(d))
    save("boom.wav", boom())
    save("heartbeat.wav", heartbeat(d + 0.6))
    save("rev_swoosh.wav", rev_swoosh(1.0))
    save("glitch.wav", glitch())
    save("whoosh.wav", whoosh())
    save("hit.wav", hit()); save("pop.wav", pop())
    print("ok")
