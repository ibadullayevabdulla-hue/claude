#!/usr/bin/env python3
"""Original, copyright-free soundtrack for the cartoon timeline video.

All music and sound effects are synthesised here from scratch and timed to the
animation in index.html (126 BPM, one character per bar). The style evolves
with the decades: old-radio ragtime (1920s-30s) -> swing -> 60s rock -> 70s funk
-> 80s synthwave -> 90s/2000s dance, with a key change at the 1990s.

    python3 soundtrack.py          # writes out/soundtrack.wav and prints its path

Needs numpy and scipy (pip install numpy scipy).
"""
import json
import pathlib
import wave

import numpy as np
from scipy import signal

HERE = pathlib.Path(__file__).resolve().parent
SR = 48000
BPM = 126
BEAT = 60 / BPM
BAR = 4 * BEAT
rng = np.random.default_rng(2026)

# ───────────── timeline (mirrors build() in index.html) ─────────────
DECADES = ["1920s", "1930s", "1940s", "1950s", "1960s", "1970s", "1980s", "1990s", "2000s"]
CHARS = json.loads((HERE / "characters.json").read_text())
SEGS = []  # (bar, kind, decade_index, char|None, from_year)
bar, prev_year = 2, 1920
for di, dk in enumerate(DECADES):
    SEGS.append((bar, "card", di, None, None))
    bar += 1
    for c in CHARS:
        if f"{c['year'] // 10 * 10}s" == dk:
            SEGS.append((bar, "char", di, c, prev_year))
            prev_year = c["year"]
            bar += 1
OUTRO_BAR = bar
TOTAL_BARS = bar + 3
DUR = TOTAL_BARS * BAR
N = int(DUR * SR)
BAR_90S = next(b for b, k, di, _, _ in SEGS if k == "card" and di == 7)


def bar_t(b):
    return b * BAR


def decade_of_bar(b):
    di = 8
    for sb, _, sdi, _, _ in SEGS:
        if sb <= b:
            di = sdi
    return di


# ───────────── dsp helpers ─────────────
def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def tt(d):
    return np.arange(max(1, int(d * SR))) / SR


def _sos(kind, f, order=2):
    return signal.butter(order, f, btype=kind, fs=SR, output="sos")


def lp(x, f, o=2):
    return signal.sosfilt(_sos("lowpass", f, o), x, axis=0)


def hp(x, f, o=2):
    return signal.sosfilt(_sos("highpass", f, o), x, axis=0)


def bp(x, lo, hi, o=2):
    return signal.sosfilt(_sos("bandpass", [lo, hi], o), x, axis=0)


def noise(d):
    return rng.standard_normal(int(d * SR))


def norm(x, peak=1.0):
    m = np.max(np.abs(x))
    return x * (peak / m) if m > 0 else x


def env(n, a=0.003, r=0.02):
    e = np.ones(n)
    ai, ri = min(n, int(a * SR)), min(n, int(r * SR))
    if ai:
        e[:ai] = np.linspace(0, 1, ai)
    if ri:
        e[n - ri:] *= np.linspace(1, 0, ri)
    return e


def vibrato(t, rate=5.5, depth=0.004, delay=0.15):
    return 1 + depth * np.sin(2 * np.pi * rate * t) * np.clip((t - delay) / 0.2, 0, 1)


def phase(f_t):
    return 2 * np.pi * np.cumsum(f_t) / SR


def sweep_noise(d, f0, f1, width=0.5):
    n = int(d * SR)
    f, ft, Z = signal.stft(rng.standard_normal(n), SR, nperseg=1024)
    fc = f0 * (f1 / f0) ** np.clip(ft / d, 0, 1)
    H = np.exp(-0.5 * ((np.log2(np.maximum(f, 1))[:, None] - np.log2(fc)[None, :]) / width) ** 2)
    _, y = signal.istft(Z * H, SR, nperseg=1024)
    return norm(y[:n])


class Bus:
    def __init__(self):
        self.x = np.zeros((N, 2))

    def add(self, t, sig, gain=1.0, pan=0.0):
        if sig.ndim == 1:
            a = (pan + 1) * np.pi / 4
            sig = np.stack([sig * np.cos(a), sig * np.sin(a)], 1) * np.sqrt(2)
        i = int(round(t * SR))
        if i < 0:
            sig, i = sig[-i:], 0
        n = min(len(sig), N - i)
        if n > 0:
            self.x[i:i + n] += sig[:n] * gain


music, old, drums, sfx, verb = Bus(), Bus(), Bus(), Bus(), Bus()
kick_times = []


def put(bus, t, sig, gain=1.0, pan=0.0, send=0.0):
    bus.add(t, sig, gain, pan)
    if send:
        verb.add(t, sig, gain * send, pan)


# ───────────── instruments ─────────────
def kick(punch=1.0):
    t = tt(0.45)
    f = 50 + 120 * punch * np.exp(-t * 30)
    body = np.sin(phase(f)) * np.exp(-t * 7)
    click = hp(noise(0.45), 2500) * np.exp(-t * 400) * 0.25
    return np.tanh(1.8 * (body + click)) / np.tanh(1.8)


def snare(tone=190):
    t = tt(0.25)
    return norm(np.sin(2 * np.pi * tone * t) * np.exp(-t * 28) * 0.6 + bp(noise(0.25), 1500, 9000) * np.exp(-t * 19))


def gated_snare():
    t = tt(0.3)
    s = snare()
    body = np.pad(s, (0, max(0, len(t) - len(s))))[: len(t)]
    tail = bp(noise(0.3), 800, 7000) * np.where(t < 0.2, 0.55, 0) * np.exp(-t * 2)
    return norm(body + tail) * env(len(t), 0.001, 0.02)


def clap():
    t = tt(0.35)
    e = sum(np.where(t >= d, np.exp(-np.maximum(t - d, 0) * 220), 0) for d in (0, 0.011, 0.022))
    e = e + np.where(t >= 0.03, np.exp(-np.maximum(t - 0.03, 0) * 14), 0) * 0.7
    return norm(bp(noise(0.35), 900, 3800) * e)


def hat(open_=False):
    d = 0.3 if open_ else 0.06
    return norm(hp(noise(d), 7500, 4) * np.exp(-tt(d) * (11 if open_ else 90)))


def brush():
    t = tt(0.3)
    e = np.minimum(t / 0.02, 1) * np.exp(-t * 10)
    return norm(bp(noise(0.3), 2000, 8000) * e)


def tom(f):
    t = tt(0.4)
    return norm(np.sin(phase(f * (1 + 0.6 * np.exp(-t * 25)))) * np.exp(-t * 8) + bp(noise(0.4), 200, 2000) * np.exp(-t * 30) * 0.3)


def tamb():
    t = tt(0.12)
    return norm(bp(noise(0.12), 6000, 14000) * np.exp(-t * 35))


def crash(d=2.0):
    t = tt(d)
    return norm(hp(noise(d), 3800, 4) * np.exp(-t * 2.3) + bp(noise(d), 6000, 14000) * np.exp(-t * 4) * 0.5)


def impact(d=1.8):
    t = tt(d)
    sub = np.sin(phase(30 + 70 * np.exp(-t * 9))) * np.exp(-t * 2.6)
    thump = lp(noise(d), 260) * np.exp(-t * 14) * 3
    return norm(np.tanh(1.4 * (sub + thump)))


def bass(f, d, bright=0.35):
    t = tt(d)
    x = np.sin(2 * np.pi * f * t) + bright * np.sin(4 * np.pi * f * t) + bright * 0.35 * np.sin(6 * np.pi * f * t)
    return np.tanh(1.6 * x) * env(len(t), 0.004, 0.03) * (0.7 + 0.3 * np.exp(-t * 8))


def tuba(f, d):
    t = tt(d)
    x = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(4 * np.pi * f * t) + 0.25 * np.sin(6 * np.pi * f * t) + 0.1 * np.sin(8 * np.pi * f * t)
    return x * env(len(t), 0.025, 0.06) * (0.6 + 0.4 * np.exp(-t * 5))


def saw_bass(f, d):
    t = tt(d)
    x = sum(np.sin(2 * np.pi * f * k * t) / k * np.exp(-f * k / (900 + 2500 * np.exp(-t * 12))) for k in range(1, 16))
    return np.tanh(1.4 * x) * env(len(t), 0.003, 0.02)


def additive(f, d, parts, a=0.003, r=0.03, vib=None):
    t = tt(d)
    v = vibrato(t, *vib) if vib else 1
    x = sum(amp * np.sin(phase(np.full(len(t), f * ratio) * v)) * (np.exp(-t * dec) if dec else 1) for ratio, amp, dec in parts)
    return x * env(len(t), a, r)


def marimba(f, d=0.6):
    return additive(f, d, ((1, 1, 6), (3.93, 0.35, 18), (9.2, 0.08, 40)), 0.001, 0.02)


def piano(f, d=0.8):
    return additive(f, d, ((1, 1, 3.5), (2, 0.5, 5), (3, 0.3, 7), (4, 0.18, 9), (5, 0.1, 12), (6, 0.06, 15)), 0.002, 0.05)


def clarinet(f, d):
    return additive(f, d, ((1, 1, 0), (3, 0.45, 0), (5, 0.25, 0), (7, 0.13, 0), (9, 0.07, 0)), 0.03, 0.06, (5.5, 0.005, 0.12))


def organ(f, d):
    t = tt(d)
    x = additive(f, d, ((0.5, 0.45, 0), (1, 1, 0), (1.5, 0.55, 0), (2, 0.5, 0), (3, 0.3, 0), (4, 0.28, 0)), 0.005, 0.04)
    return x * (1 + 0.12 * np.sin(2 * np.pi * 6.2 * t))


def surf(f, d):
    t = tt(d)
    x = sum(np.sin(2 * np.pi * f * k * t) * np.exp(-t * (2.5 + k * 1.6)) / k ** 1.05 for k in range(1, 10))
    return x * (1 - 0.4 * (0.5 + 0.5 * np.sin(2 * np.pi * 8 * t))) * env(len(t), 0.002, 0.03)


def clav(f, d):
    t = tt(d)
    fc = 500 * (4 ** np.clip(t / 0.18, 0, 1))  # wah opening
    x = np.zeros(len(t))
    for k in range(1, 14):
        w = np.exp(-0.5 * ((np.log2(f * k) - np.log2(fc)) / 0.7) ** 2)
        x += np.sin(2 * np.pi * f * k * t) * w / k ** 0.6
    return x * np.exp(-t * 6) * env(len(t), 0.002, 0.02)


def saw_lead(f, d, voices=(-7, 7), cutoff=5000):
    t = tt(d)
    v = vibrato(t, 5.8, 0.006, 0.18)
    x = np.zeros(len(t))
    for c in voices:
        ff = f * 2 ** (c / 1200)
        for k in range(1, 18):
            if ff * k > 15000:
                break
            x += np.sin(phase(np.full(len(t), ff * k) * v)) * np.exp(-ff * k / cutoff) / k
    return x / len(voices) * env(len(t), 0.008, 0.06)


def supersaw(f, d):
    return saw_lead(f, d, (-18, -8, 0, 8, 18), 6500)


def pad(midis, d, cutoff=1800, att=0.3, rel=0.5):
    t = tt(d + rel)
    out = np.zeros((len(t), 2))
    for m in midis:
        for j, cents in enumerate((-9, 0, 9)):
            f = mtof(m) * 2 ** (cents / 1200)
            s = sum(np.sin(2 * np.pi * f * k * t + rng.uniform(0, 6.28)) * np.exp(-f * k / cutoff) / k for k in range(1, 14) if f * k < 12000)
            out[:, 0] += s * (1.0, 0.75, 0.35)[j]
            out[:, 1] += s * (0.35, 0.75, 1.0)[j]
    e = np.minimum(t / att, 1) * np.where(t > d, np.exp(-(t - d) * 5 / rel), 1)
    return out * e[:, None] / (len(midis) * 2.2)


def chord(fn, midis, d, spread=0.0):
    return sum(fn(mtof(m), d) for m in midis) / len(midis)


def bell(f, d=1.4):
    return additive(f, d, ((1, 1, 2), (2.0, 0.45, 3), (2.76, 0.3, 4), (5.4, 0.12, 6), (8.93, 0.05, 9)), 0.002, 0.05)


def pop(f1):
    t = tt(0.16)
    x = np.sin(phase(f1 * 0.45 + f1 * 0.55 * (1 - np.exp(-t * 70)))) * np.exp(-t * 26)
    return x + hp(noise(0.16), 3000) * np.exp(-t * 700) * 0.15


def tick(f=3000):
    t = tt(0.035)
    return np.sin(2 * np.pi * f * t) * np.exp(-t * 200) + bp(noise(0.035), 4000, 12000) * np.exp(-t * 900) * 0.25


def whoosh(d, f0, f1, pan0=0.0, pan1=0.0, peak=0.5):
    x = sweep_noise(d, f0, f1, 0.45)
    u = np.linspace(0, 1, len(x))
    x *= np.where(u < peak, (u / peak) ** 2, ((1 - u) / (1 - peak)) ** 1.6)
    a = (np.linspace(pan0, pan1, len(x)) + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], 1) * np.sqrt(2)


def riser(d, f0=300, f1=9000):
    t = tt(d)
    u = t / d
    air = sweep_noise(d, f0, f1, 0.5) * u ** 2.2
    tone = np.sin(phase(180 * 8 ** u)) * u ** 2.6 * 0.3
    return air + tone


def slide_whistle(f0, f1, d):
    t = tt(d)
    f = f0 * (f1 / f0) ** (t / d) * (1 + 0.012 * np.sin(2 * np.pi * 7 * t))
    x = np.sin(phase(f)) + 0.08 * np.sin(phase(2 * f))
    breath = bp(noise(d), 1500, 6000) * 0.06
    return (x + breath) * env(len(t), 0.03, 0.05)


def click():
    t = tt(0.05)
    return norm(bp(noise(0.05), 1500, 9000) * np.exp(-t * 400) + np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 300) * 0.4)


def crackle(d):
    n = int(d * SR)
    x = np.zeros(n)
    idx = rng.integers(0, n, int(d * 26))
    x[idx] = rng.uniform(-1, 1, len(idx)) * rng.uniform(0.2, 1, len(idx)) ** 3
    return hp(x, 1500) * 0.8 + lp(noise(d), 4000) * 0.012


def reverb_ir(rt60=1.8):
    t = tt(rt60)
    ir = np.stack([lp(noise(rt60), 5500) for _ in range(2)], 1) * np.exp(-6.9 * t / rt60)[:, None]
    ir = np.concatenate([np.zeros((int(0.015 * SR), 2)), ir])
    return ir / np.sqrt(np.sum(ir ** 2) / 2)


# ───────────── harmony & melody ─────────────
# I–V–vi–IV in C; everything moves up a whole step from the 1990s
CHORDS = [  # root (bass), minor?, voicing
    (48, False, [60, 64, 67, 72]),  # C
    (43, False, [59, 62, 67, 71]),  # G
    (45, True, [57, 60, 64, 69]),   # Am
    (41, False, [57, 60, 65, 69]),  # F
]
A = [(0, 76, .5), (.5, 79, .5), (1, 84, 1), (2.5, 83, .5), (3, 79, 1),
     (4, 79, .5), (4.5, 81, .5), (5, 83, 1), (6, 86, .5), (6.5, 83, .5), (7, 79, 1),
     (8, 81, .5), (8.5, 84, .5), (9, 88, 1), (10.5, 86, .5), (11, 84, 1),
     (12, 81, .5), (12.5, 79, .5), (13, 77, .5), (13.5, 76, .5), (14, 74, 1), (15, 79, 1)]
B = A[:16] + [(12, 84, .5), (12.5, 86, .5), (13, 88, 1), (14.5, 91, .5), (15, 88, 1)]
C = [(0, 84, .75), (.75, 84, .75), (1.5, 83, .5), (2, 84, .5), (2.5, 88, 1.5),
     (4, 86, .75), (4.75, 86, .75), (5.5, 84, .5), (6, 83, .5), (6.5, 79, 1.5),
     (8, 84, .75), (8.75, 84, .75), (9.5, 83, .5), (10, 84, .5), (10.5, 88, 1), (11.5, 91, .5),
     (12, 89, .75), (12.75, 88, .75), (13.5, 86, .5), (14, 84, 1), (15, 83, .5), (15.5, 79, .5)]
PHRASES = [A, B, C, B]


def key_of(b):
    return 2 if b >= BAR_90S else 0


def harmony(b):
    root, minor, voicing = CHORDS[(b - 2) % 4]
    k = key_of(b)
    return root + k, minor, [v + k for v in voicing]


def melody(b, phrase=None):
    ph = phrase or PHRASES[((b - 2) // 4) % 4]
    j = (b - 2) % 4
    return [(s - 4 * j, m + key_of(b), d) for s, m, d in ph if 4 * j <= s < 4 * (j + 1)]


LEADS = [  # instrument, octave shift, gain, reverb send
    (marimba, 0, .34, .35), (marimba, 0, .32, .3), (clarinet, -12, .22, .3), (organ, -12, .17, .3),
    (surf, 0, .3, .35), (clav, -12, .32, .2), (saw_lead, 0, .2, .35), (supersaw, 0, .2, .3), (supersaw, 0, .2, .3),
]


def add_kick(t, g):
    put(drums, t, kick(), g)
    kick_times.append(t)


# ───────────── arrangement ─────────────
def style_bar(b, di, with_melody=True):
    t0 = bar_t(b)
    root, minor, voicing = harmony(b)
    third, sixth = (3, 8) if minor else (4, 9)
    bus = old if di <= 1 else music
    at = lambda beat: t0 + beat * BEAT  # noqa: E731
    swing = lambda beat: at(beat + (2 / 3 - .5 if beat % 1 == .5 else 0))  # noqa: E731

    if di <= 1:  # ragtime on an old radio
        for beat, note in ((0, root - 12), (2, root - 5)):
            put(bus, at(beat), tuba(mtof(note), BEAT * 0.9), .5)
        for beat in (1, 3):
            put(bus, at(beat), chord(piano, voicing, 0.4), .32, send=.2)
        for beat in (0, 2):
            put(bus, at(beat), kick(.5), .3)
        for beat in (1, 3):
            put(bus, at(beat), brush(), .22)
        if di == 1:
            for i in range(8):
                put(bus, swing(i / 2), hat(), .05 if i % 2 else .07, .3)
    elif di <= 3:  # swing
        walk = [0, third, 7, sixth]
        for beat in range(4):
            put(music, at(beat), bass(mtof(root - 12 + walk[beat]), BEAT * .85), .42)
        for beat in (0, 2):
            add_kick(at(beat), .5)
        for beat in (1, 3):
            put(drums, at(beat), snare(), .26, send=.15)
            if di == 3:
                put(drums, at(beat), clap(), .16, send=.2)
        for i in range(8):
            put(drums, swing(i / 2), hat(), .07 if i % 2 else .1, .3)
        for beat in (1, 2.5 + 1 / 6):
            put(music, at(beat), chord(piano, voicing, 0.35), .22, -.2, send=.2)
    elif di == 4:  # 60s rock
        for i in range(8):
            put(music, at(i / 2), bass(mtof(root - 12 + (12 if i == 7 else 0)), BEAT * .45), .38)
        for beat in (0, 2, 2.5):
            add_kick(at(beat), .7)
        for beat in (1, 3):
            put(drums, at(beat), snare(), .32, send=.2)
        for i in range(8):
            put(drums, at(i / 2), hat(), .07, .3)
        for i in range(16):
            put(drums, at(i / 4), tamb(), .04 if i % 2 else .06, -.4)
        put(music, t0, chord(organ, voicing, BAR * .98), .2, send=.25)
    elif di == 5:  # 70s funk
        for pos, iv in ((0, 0), (.75, 12), (1.5, 0), (2, 7), (2.75, 12), (3.5, 10)):
            put(music, at(pos), bass(mtof(root - 12 + iv), BEAT * .3, .6), .42)
        for beat in (0, .75, 2.5):
            add_kick(at(beat), .7)
        for beat in (1, 3):
            put(drums, at(beat), snare(220), .32, send=.2)
        for beat in (1.75, 3.5):
            put(drums, at(beat), snare(220), .08)
        for i in range(16):
            put(drums, at(i / 4), hat(), (.08, .04, .06, .04)[i % 4], .3)
        for pos in (.5, 1.25, 2.5, 3.25):
            put(music, at(pos), chord(clav, voicing, .25), .2, .25)
    elif di == 6:  # 80s synthwave
        for i in range(8):
            put(music, at(i / 2), saw_bass(mtof(root - 12 + (12 if i % 2 else 0)), BEAT * .45), .3)
        for beat in (0, 2, 2.5):
            add_kick(at(beat), .8)
        for beat in (1, 3):
            put(drums, at(beat), gated_snare(), .34, send=.35)
        for i in range(8):
            put(drums, at(i / 2), hat(), .07, .3)
        arp = [voicing[i] + 12 for i in (0, 1, 2, 3, 2, 1, 2, 3)] * 2
        for i, m in enumerate(arp):
            put(music, at(i / 4), saw_lead(mtof(m), BEAT * .22, (-5, 5), 3000), .06, (-.5, .5)[i % 2], send=.3)
        put(music, t0, pad(voicing, BAR, 2200, .05, .3), .3, send=.3)
    else:  # 90s / 2000s dance
        for beat in range(4):
            add_kick(at(beat), .95)
            put(music, at(beat + .5), bass(mtof(root - 12), BEAT * .4, .5), .45)
            put(drums, at(beat + .5), hat(True), .1, .3)
            for s in range(4):
                put(drums, at(beat + s / 4), hat(), (.08, .035, .06, .035)[s], -.25)
        for beat in (1, 3):
            put(drums, at(beat), clap(), .34, send=.25)
        for pos in (0, .75, 1.5, 2.5, 3.25):
            put(music, at(pos), chord(piano, voicing + [voicing[0] + 12], .45), .26, send=.25)
        put(music, t0, pad(voicing, BAR, 2600, .05, .3), .22, send=.3)

    if with_melody:
        inst, octave, g, send = LEADS[di]
        for s, m, d in melody(b, C if b >= OUTRO_BAR else None):
            put(bus if di <= 1 else music, at(s), inst(mtof(m + octave), d * BEAT * .95), g, .15, send=send)
            if di >= 8 or b >= OUTRO_BAR:
                put(music, at(s), inst(mtof(m + octave + 12), d * BEAT * .95), g * .4, -.2, send=send)


def card_bar(b, di):
    """Decade title card: slide whistle -> slam, held chord, fill into the next bar."""
    t0 = bar_t(b)
    root, minor, voicing = harmony(b)
    bus = old if di <= 1 else music
    put(sfx, t0, slide_whistle(500, 1500, .3), .14, send=.2)
    put(sfx, t0 + .3, impact(), .7, send=.2)
    put(sfx, t0 + .3, crash(), .22, send=.3)
    hold = piano if di <= 3 else organ if di <= 5 else None
    if hold:
        put(bus, t0 + .3, chord(hold, voicing, BAR - .35), .28, send=.35)
    else:
        put(music, t0 + .3, pad(voicing, BAR - .35, 2600, .02, .3), .4, send=.35)
    put(bus, t0 + .3, (tuba if di <= 1 else bass)(mtof(root - 12), BAR - .4), .4)
    if di == 7:  # the 90s get a riser into the key change
        put(sfx, t0 + .4, riser(BAR - .4), .2)
    for i in range(4):  # fill on beat 4
        tb = t0 + (3 + i / 4) * BEAT
        if di <= 3:
            put(bus if di <= 1 else drums, tb, snare(), .15 + .06 * i)
        else:
            put(drums, tb, tom((180, 150, 120, 95)[i]), .3)


def build():
    # intro: two bars of build-up under the hook question
    put(music, 0, pad([60, 64, 67, 72], 2 * BAR - .1, 1500, 1.2, .2), .35, send=.4)
    for i in range(12):
        put(sfx, .05 + i * .07 + .08, pop(mtof(72 + [0, 2, 4, 7, 9, 12][i % 6])), .18, -.6 + (i % 5) * .3)
    put(sfx, .45, whoosh(.5, 400, 4000), .2)
    put(music, .45, chord(piano, [60, 64, 67, 72], .6), .35, send=.3)
    put(sfx, .9, impact(1.2), .4)
    put(music, .9, chord(piano, [67, 71, 74, 79], .8), .4, send=.3)
    put(sfx, 1.85, pop(900), .25)
    hits = [i * .5 for i in range(4)] + [2 + i * .25 for i in range(8)]
    for i, beat in enumerate(hits):  # snare build across bar 1
        put(drums, bar_t(1) + beat * BEAT, snare(), .1 + .3 * i / len(hits))
    for beat in range(4):
        add_kick(bar_t(1) + beat * BEAT, .5)
    put(sfx, bar_t(2) - 1.8, riser(1.8), .28)
    put(sfx, bar_t(2) - 1.2, crash(1.2)[::-1], .18)

    for b, kind, di, c, from_year in SEGS:
        t0 = bar_t(b)
        if kind == "card":
            card_bar(b, di)
            continue
        style_bar(b, di)
        # character entrance
        put(sfx, t0 - .02, whoosh(.38, 600, 4500, .8, -.2, .45), .15)
        put(sfx, t0 + .15, pop(mtof(72 + (c["year"] % 7))), .26)
        put(sfx, t0 + BEAT * .9 + .08, bell(mtof(88 + key_of(b)), .9), .06, .4, send=.4)
        # odometer: one tick per year rolled
        steps = c["year"] - from_year
        for s in range(1, steps + 1):
            target = s / steps
            lo, hi = 0.0, 1.0
            for _ in range(30):
                mid = (lo + hi) / 2
                v = 4 * mid ** 3 if mid < .5 else 1 - (-2 * mid + 2) ** 3 / 2
                lo, hi = (mid, hi) if v < target else (lo, mid)
            put(sfx, t0 + .05 + .65 * hi, tick(2200 + 90 * s), .07, 0)

    # outro: two bars of finale, then the last hit
    for b in (OUTRO_BAR, OUTRO_BAR + 1):
        style_bar(b, 8)
    t0 = bar_t(OUTRO_BAR)
    put(sfx, t0, whoosh(.6, 300, 5000), .25)
    for i in range(0, 50, 2):
        put(sfx, t0 + .2 + i * .024 + .08, pop(mtof(74 + (i // 2) % 12)), .07, -.6 + (i % 10) * .13)
    put(sfx, t0 + 1.5, pop(1000), .22)
    put(sfx, t0 + 2.4, pop(800), .22)
    put(sfx, t0 + 3.45, click(), .5)
    for i, m in enumerate((90, 95)):
        put(sfx, t0 + 3.5 + i * .12, bell(mtof(m), 1.5), .14, .2, send=.4)
    tf = bar_t(OUTRO_BAR + 2)
    root, _, voicing = harmony(OUTRO_BAR + 2)
    put(music, tf, chord(piano, voicing + [voicing[0] + 12], 1.9), .45, send=.5)
    put(music, tf, pad(voicing, 1.6, 2600, .02, .4), .35, send=.4)
    put(music, tf, bass(mtof(root - 12), 1.6), .45)
    put(music, tf, supersaw(mtof(voicing[0] + 12), 1.6), .16, send=.4)
    add_kick(tf, 1.0)
    put(sfx, tf, crash(2.4), .3, send=.3)
    put(sfx, tf, impact(), .5)


def mixdown():
    # old-radio treatment for the 1920s–30s
    end20 = bar_t(next(b for b, k, di, _, _ in SEGS if k == "card" and di == 1))
    end30 = bar_t(next(b for b, k, di, _, _ in SEGS if k == "card" and di == 2))
    radio = np.zeros_like(old.x)
    heavy = np.tanh(2.2 * bp(old.x, 320, 3200, 2)) / 1.4
    light = bp(old.x, 140, 6500, 1)
    t = np.arange(N) / SR
    w = np.clip((t - end20) / 0.3, 0, 1)[:, None]
    radio = heavy * (1 - w) + light * w
    radio += np.stack([crackle(DUR)] * 2, 1) * (np.where(t < end30, 1.0, 0.0) * np.where(t < end20, 1, .5))[:, None] * np.where(t >= bar_t(2), 1, 0)[:, None]

    duck = np.ones(N)
    shape = 1 - 0.5 * np.exp(-tt(0.32) / 0.08)
    for tk in kick_times:
        i = int(tk * SR)
        n = min(len(shape), N - i)
        duck[i:i + n] = np.minimum(duck[i:i + n], shape[:n])
    dry = drums.x + music.x * duck[:, None] + radio * 1.15 + sfx.x
    wet = np.stack([signal.fftconvolve(verb.x[:, c], reverb_ir()[:, c])[:N] for c in range(2)], 1)
    mix = hp(dry + 0.3 * wet, 30)
    mix = norm(mix, 1.6)
    mix = np.tanh(mix) / np.tanh(1.6)
    mix *= np.clip((DUR - t) / 0.7, 0, 1)[:, None] ** 1.5
    mix *= np.clip(t / 0.01, 0, 1)[:, None]
    return norm(mix, 0.89)


def main():
    build()
    out = HERE / "out" / "soundtrack.wav"
    out.parent.mkdir(exist_ok=True)
    pcm = (mixdown() * 32767).astype("<i2")
    with wave.open(str(out), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(out)


if __name__ == "__main__":
    main()
