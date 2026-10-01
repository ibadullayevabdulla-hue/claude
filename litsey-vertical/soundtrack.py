#!/usr/bin/env python3
"""Original cinematic soundtrack with an Uzbek flavour for the vertical lyceum
video, synthesised from scratch and timed to index.html (100 BPM, one bar = 2.4 s,
50 bars = 2:00).

Doira (frame drum) grooves, a karnay-like low horn, a surnay-like reed melody,
epic drums, spiccato strings, brass and choir. D minor with a Hijaz colour
(the A major chord), rising to E minor for the benefits section.

    python3 soundtrack.py          # writes out/soundtrack.wav and prints its path

Needs numpy and scipy.
"""
import pathlib
import wave

import numpy as np
from scipy import signal

HERE = pathlib.Path(__file__).resolve().parent
SR = 48000
BPM = 100
BEAT = 60 / BPM
BAR = 4 * BEAT
S16 = BEAT / 4
rng = np.random.default_rng(1991)

# ───────────── timeline (mirrors SCENES in index.html) ─────────────
SCENES = [("intro", 4), ("section", 2)] + [("item", 2)] * 8 + [("score", 3), ("section", 2)] + [("item", 2)] * 9 + [("outro", 5)]
T0, b = [], 0
for kind, bars in SCENES:
    T0.append((kind, b, bars))
    b += bars
TOTAL_BARS = b
DUR = TOTAL_BARS * BAR
N = int(DUR * SR)
BAR_KEY = T0[11][1]          # benefits section: key change
BAR_OUTRO = T0[-1][1]

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

def put(bus, t, sig, gain=1.0, pan=0.0, send=0.0):
    bus.add(t, sig, gain, pan)
    if send:
        verb.add(t, sig, gain * send, pan)

def tom(f):
    t = tt(0.4)
    return norm(np.sin(phase(f * (1 + 0.6 * np.exp(-t * 25)))) * np.exp(-t * 8) + bp(noise(0.4), 200, 2000) * np.exp(-t * 30) * 0.3)

def crash(d=2.0):
    t = tt(d)
    return norm(hp(noise(d), 3800, 4) * np.exp(-t * 2.3) + bp(noise(d), 6000, 14000) * np.exp(-t * 4) * 0.5)

def impact(d=1.8):
    t = tt(d)
    sub = np.sin(phase(30 + 70 * np.exp(-t * 9))) * np.exp(-t * 2.6)
    thump = lp(noise(d), 260) * np.exp(-t * 14) * 3
    return norm(np.tanh(1.4 * (sub + thump)))

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

def additive(f, d, parts, a=0.003, r=0.03, vib=None):
    t = tt(d)
    v = vibrato(t, *vib) if vib else 1
    x = sum(amp * np.sin(phase(np.full(len(t), f * ratio) * v)) * (np.exp(-t * dec) if dec else 1)
            for ratio, amp, dec in parts if f * ratio < SR / 2.2)
    return x * env(len(t), a, r)


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

def reverb_ir(rt60=1.8):
    t = tt(rt60)
    ir = np.stack([lp(noise(rt60), 5500) for _ in range(2)], 1) * np.exp(-6.9 * t / rt60)[:, None]
    ir = np.concatenate([np.zeros((int(0.015 * SR), 2)), ir])
    return ir / np.sqrt(np.sum(ir ** 2) / 2)


_GTR = {}


music, drums, sfx, verb = Bus(), Bus(), Bus(), Bus()
kick_times = []


def bar_t(b):
    return b * BAR


# ───────────── band instruments ─────────────
def snare_m(v=1.0):
    """Military field snare: crisp head plus a long wire rattle."""
    t = tt(0.32)
    head = np.sin(2 * np.pi * 210 * t) * np.exp(-t * 35) * .5
    wires = bp(noise(0.32), 1800, 10000) * np.exp(-t * (14 + 10 * (1 - v)))
    return norm(head + wires) * v


def snare_roll(d, v0=.15, v1=1.0, rate=16):
    """Closed roll: `rate` strokes per beat, crescendo from v0 to v1."""
    n = int(d / BEAT * rate)
    out = np.zeros(int((d + .4) * SR))
    for i in range(n):
        v = v0 + (v1 - v0) * (i / max(1, n - 1)) ** 1.5
        s = snare_m(.6 + .4 * v)[: int(.12 * SR)] * v * (0.85 + 0.3 * rng.random())
        j = int(i * d / n * SR)
        out[j:j + len(s)] += s
    return out


def bass_drum(v=1.0):
    t = tt(1.2)
    body = np.sin(phase(48 + 40 * np.exp(-t * 18))) * np.exp(-t * 3.2)
    skin = lp(noise(1.2), 400) * np.exp(-t * 25) * 1.5
    return norm(np.tanh(1.3 * (body + skin))) * v


def timpani(f, d=2.2, v=1.0):
    t = tt(d)
    x = (np.sin(phase(f * (1 + .03 * np.exp(-t * 20)))) + .5 * np.sin(2 * np.pi * f * 1.504 * t) * np.exp(-t * 1.5)
         + .3 * np.sin(2 * np.pi * f * 1.742 * t) * np.exp(-t * 2.5)) * np.exp(-t * 1.6)
    mallet = bp(noise(d), 200, 2500) * np.exp(-t * 60) * .6
    return (x + mallet) * env(len(t), .001, .1) * v


def timp_roll(f, d, v0=.1, v1=1.0):
    t = tt(d + .8)
    n = int(d / BEAT * 8)
    out = np.zeros(len(t))
    for i in range(n):
        v = v0 + (v1 - v0) * (i / max(1, n - 1)) ** 1.4
        s = timpani(f, .8, v * .5)
        j = int(i * d / n * SR)
        out[j:j + len(s)] += s[: len(out) - j]
    return out


_BR = {}


def brass(f, d, bright=1.0):
    """Brass section voice: sawtooth whose brightness opens on the attack ("blat")."""
    key = (round(f, 2), round(d, 3), bright)
    if key not in _BR:
        t = tt(d)
        v = vibrato(t, 5.2, .004, .25)
        fc = (700 + 2600 * bright) * (0.55 + 0.45 * np.exp(-t * 6)) + 900 * bright * np.minimum(t / .05, 1)
        x = np.zeros(len(t))
        for k in range(1, 22):
            if f * k > 12000:
                break
            x += np.sin(phase(np.full(len(t), f * k) * v)) / k * np.exp(-f * k / fc)
        x = np.tanh(1.6 * x) * env(len(t), .03, .08)
        _BR[key] = x
    return _BR[key]


def brass_chord(midis, d, bright=1.0):
    out = np.zeros((int(d * SR) + 1, 2))
    for i, m in enumerate(midis):
        for j, cents in enumerate((-6, 6)):
            s = brass(mtof(m) * 2 ** (cents / 1200), d, bright)
            pan = (-.35 + .7 * i / max(1, len(midis) - 1)) * (1 if j else .8)
            a = (pan + 1) * np.pi / 4
            out[: len(s), 0] += s * np.cos(a)
            out[: len(s), 1] += s * np.sin(a)
    return out / (len(midis) * 1.4)


def strings_stac(f, d):
    t = tt(d)
    x = sum(np.sin(2 * np.pi * f * k * t + k) / k * np.exp(-f * k / 2200) for k in range(1, 14) if f * k < 12000)
    return x * env(len(t), .008, .04) * np.exp(-t * 4)


def choir(midis, d):
    """Choir 'ah': a soft pad pushed through two vowel formants."""
    p = pad(midis, d, 3200, .5, .6)
    return bp(p, 550, 1250, 2) * 1.6 + bp(p, 2300, 3200, 2) * .5


def glock(f, d=1.2):
    return bell(f, d)


def shing():
    """Metallic sweep for the spinning badge."""
    t = tt(.9)
    x = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * dec) for f, dec in ((2350, 3), (3270, 4), (4610, 5), (5930, 6)))
    return norm(x * np.minimum(t / .02, 1) + bp(noise(.9), 5000, 12000) * np.exp(-t * 10) * .4)



_BR = {}


def brass(f, d, bright=1.0):
    """Brass section voice: sawtooth whose brightness opens on the attack ("blat")."""
    key = (round(f, 2), round(d, 3), bright)
    if key not in _BR:
        t = tt(d)
        v = vibrato(t, 5.2, .004, .25)
        fc = (700 + 2600 * bright) * (0.55 + 0.45 * np.exp(-t * 6)) + 900 * bright * np.minimum(t / .05, 1)
        x = np.zeros(len(t))
        for k in range(1, 22):
            if f * k > 12000:
                break
            x += np.sin(phase(np.full(len(t), f * k) * v)) / k * np.exp(-f * k / fc)
        x = np.tanh(1.6 * x) * env(len(t), .03, .08)
        _BR[key] = x
    return _BR[key]


def brass_chord(midis, d, bright=1.0):
    out = np.zeros((int(d * SR) + 1, 2))
    for i, m in enumerate(midis):
        for j, cents in enumerate((-6, 6)):
            s = brass(mtof(m) * 2 ** (cents / 1200), d, bright)
            pan = (-.35 + .7 * i / max(1, len(midis) - 1)) * (1 if j else .8)
            a = (pan + 1) * np.pi / 4
            out[: len(s), 0] += s * np.cos(a)
            out[: len(s), 1] += s * np.sin(a)
    return out / (len(midis) * 1.4)



def choir(midis, d):
    """Choir 'ah': a soft pad pushed through two vowel formants."""
    p = pad(midis, d, 3200, .5, .6)
    return bp(p, 550, 1250, 2) * 1.6 + bp(p, 2300, 3200, 2) * .5


def glock(f, d=1.2):
    return bell(f, d)




def bar_t(b):
    return b * BAR


# ───────────── instruments ─────────────
def doira_dum(v=1.0):
    t = tt(.5)
    body = np.sin(phase(70 + 50 * np.exp(-t * 30))) * np.exp(-t * 7)
    skin = bp(noise(.5), 150, 900) * np.exp(-t * 30) * .6
    return norm(body + skin) * v


def doira_tak(v=1.0):
    t = tt(.25)
    ring = np.sin(2 * np.pi * 880 * t) * np.exp(-t * 40) * .5 + np.sin(2 * np.pi * 1320 * t) * np.exp(-t * 55) * .3
    slap = bp(noise(.25), 1500, 9000) * np.exp(-t * 45)
    return norm(ring + slap) * v


def jingles(v=1.0):
    """The small metal rings inside the doira frame."""
    t = tt(.35)
    x = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * np.exp(-t * d) for f, d in ((5200, 14), (6900, 17), (8300, 20), (9700, 24)))
    return norm(x * (1 + .5 * np.sin(2 * np.pi * 38 * t)) + hp(noise(.35), 7000) * np.exp(-t * 18) * .6) * v


def epic_drum(v=1.0):
    t = tt(1.6)
    body = np.sin(phase(42 + 60 * np.exp(-t * 14))) * np.exp(-t * 2.4)
    hit = lp(noise(1.6), 600) * np.exp(-t * 18) * 1.4
    return norm(np.tanh(1.5 * (body + hit))) * v


def low_tom(f, v=1.0):
    t = tt(.6)
    return norm(np.sin(phase(f * (1 + .5 * np.exp(-t * 18)))) * np.exp(-t * 6) + bp(noise(.6), 100, 1200) * np.exp(-t * 25) * .4) * v


def karnay(f, d):
    """Long ceremonial horn: slow swell, a slight upward bend and a raspy edge."""
    t = tt(d)
    bend = 2 ** (-.4 / 12 * np.exp(-t * 3))
    v = vibrato(t, 4.2, .003, .5)
    fc = 900 + 1400 * np.minimum(t / .8, 1)
    x = np.zeros(len(t))
    for k in range(1, 26):
        if f * k > 9000:
            break
        x += np.sin(phase(np.full(len(t), f * k) * bend * v)) / k ** .8 * np.exp(-f * k / fc)
    rasp = 1 + .12 * lp(noise(d), 60) * 3
    return np.tanh(1.3 * x * rasp) * env(len(t), .45, .5)


def surnay(f, d, grace=True):
    """Double-reed lead: nasal formants, vibrato, a quick grace-note fall into each long note."""
    t = tt(d)
    v = vibrato(t, 6.0, .007, .12)
    g = 2 ** ((2 if grace and d > BEAT * .7 else 0) / 12 * np.exp(-t * 40)) if grace else 1
    x = np.zeros(len(t))
    for k in range(1, 30):
        fk = f * k
        if fk > 12000:
            break
        amp = (np.exp(-((fk - 1300) / 700) ** 2) + .8 * np.exp(-((fk - 2800) / 900) ** 2) + .25) / k ** .5
        x += amp * np.sin(phase(np.full(len(t), fk) * v * g))
    return np.tanh(1.2 * x) * env(len(t), .025, .06)


def spiccato(f, d=None):
    d = d or S16 * 1.6
    t = tt(d)
    x = sum(np.sin(2 * np.pi * f * k * t + k) / k * np.exp(-f * k / 2600) for k in range(1, 14) if f * k < 12000)
    return x * env(len(t), .004, .03) * np.exp(-t * 9)


def braam(midis, d):
    """Huge low brass hit with a slowly opening filter."""
    out = np.zeros(int(d * SR) + 1)
    for m in midis:
        t = tt(d)
        f = mtof(m)
        fc = 300 + 2400 * (1 - np.exp(-t * 2.5)) * np.exp(-t * .6)
        x = sum(np.sin(2 * np.pi * f * k * t + k) / k * np.exp(-f * k / fc) for k in range(1, 30) if f * k < 9000)
        out[:len(t)] += np.tanh(2 * x) * env(len(t), .02, .8)
    return out / len(midis)


def shimmer(d=1.2):
    t = tt(d)
    x = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * np.exp(-t * (2 + i)) for i, f in enumerate((2637, 3136, 3951, 4699, 5274)))
    return norm(x * np.minimum(t / .05, 1))


# ───────────── harmony & melody ─────────────
CH = {"Dm": (38, [62, 65, 69]), "Bb": (34, [62, 65, 70]), "Gm": (43, [62, 67, 70]), "A": (33, [61, 64, 69]), "F": (41, [60, 65, 69])}
PROG = ["Dm", "Bb", "Gm", "A", "Dm", "Bb", "Gm", "A"]
MEL = [
    [(0, 69, 1), (1, 74, .5), (1.5, 76, .5), (2, 77, 1.5), (3.5, 76, .25), (3.75, 74, .25)],
    [(0, 74, 1), (1, 72, .5), (1.5, 70, .5), (2, 72, 1), (3, 74, 1)],
    [(0, 67, .5), (.5, 69, .5), (1, 70, 1), (2, 69, .5), (2.5, 67, .5), (3, 65, 1)],
    [(0, 69, 1.5), (1.5, 70, .5), (2, 73, 1), (3, 69, 1)],
    [(0, 74, 1), (1, 77, 1), (2, 81, 1.5), (3.5, 79, .5)],
    [(0, 77, 1), (1, 76, .5), (1.5, 74, .5), (2, 77, 1), (3, 74, 1)],
    [(0, 70, 1), (1, 74, 1), (2, 79, 1), (3, 77, .5), (3.5, 76, .5)],
    [(0, 76, 2), (2, 73, 1), (3, 69, 1)],
]
DOIRA = {  # 16th steps: dum, tak, ghost tak
    "dum": [0, 3, 8, 10], "tak": [4, 12], "ghost": [2, 6, 7, 14, 15],
}


def key_of(b):
    return 2 if b >= BAR_KEY else 0


def chord_at(b, i):
    root, voicing = CH[PROG[i % 8]]
    k = key_of(b)
    return root + k, [v + k for v in voicing]


def doira_bar(b, v=1.0, jingle=True):
    t0 = bar_t(b)
    for s in DOIRA["dum"]:
        put(drums, t0 + s * S16, doira_dum(1 if s in (0, 8) else .6), .45 * v, -.15)
    for s in DOIRA["tak"]:
        put(drums, t0 + s * S16, doira_tak(1), .3 * v, .2, send=.12)
    for s in DOIRA["ghost"]:
        put(drums, t0 + s * S16, doira_tak(.5), .12 * v, .25)
    if jingle:
        for s in range(0, 16, 2):
            put(drums, t0 + s * S16, jingles(.8 if s % 4 == 0 else .5), .07 * v, .35)


def groove_bar(b, i, melody=True, lead=.24, choir_on=False, fill=False, density=1.0):
    t0 = bar_t(b)
    at = lambda beat: t0 + beat * BEAT  # noqa: E731
    root, voicing = chord_at(b, i)
    doira_bar(b, density)
    for beat in (0, 2):
        put(drums, at(beat), epic_drum(.9), .55 * density)
        kick_times.append(at(beat))
    if fill:
        for j, s in enumerate(range(12, 16)):
            put(drums, t0 + s * S16, low_tom((140, 120, 100, 85)[j]), .32, send=.15)
    # spiccato strings: driving sixteenths
    pat = [0, 0, 12, 0, 0, 7, 0, 12, 0, 0, 12, 0, 7, 0, 12, 7]
    for s, iv in enumerate(pat):
        put(music, t0 + s * S16, spiccato(mtof(root + 12 + iv)), .2 if s % 4 else .28, -.25 + .5 * (s % 2), send=.1)
    put(music, t0, brass_chord(voicing, BAR * .95, .45), .32, send=.3)
    put(music, t0, brass(mtof(root), BAR * .95, .4), .22, send=.15)
    if choir_on:
        put(music, t0, choir([v + 12 for v in voicing], BAR), .45, send=.45)
    if melody:
        k = key_of(b)
        for s, m, d in MEL[i % 8]:
            put(music, at(s), surnay(mtof(m + k), d * BEAT * .95), lead, .1, send=.3)
            if choir_on:
                put(music, at(s), glock(mtof(m + k + 12), .9), .035, .4, send=.4)


def stinger(t, b, i=0, gain=1.0):
    root, voicing = chord_at(b, i)
    put(drums, t, epic_drum(1.0), .8 * gain)
    kick_times.append(t)
    put(sfx, t, impact(1.8), .4 * gain)
    put(sfx, t, crash(2.8), .26 * gain, send=.35)
    put(music, t, braam([root, root + 7, root + 12], 2.6), .55 * gain, send=.35)
    put(music, t, brass_chord([v + 12 for v in voicing], 1.6, 1.0), .5 * gain, send=.4)


# ───────────── build ─────────────
def build():
    # intro: drone + karnay swells, doira roll into the logo hit at bar 1
    put(music, 0, karnay(mtof(38), BAR * 1.05), .5, -.2, send=.3)
    put(music, .1, karnay(mtof(45), BAR * 1.0), .35, .2, send=.3)
    put(music, 0, pad([50, 57, 62], BAR * 4, 900, 1.5, .5), .28, send=.4)
    n = 32
    for j in range(n):                               # doira roll, accelerating crescendo
        tj = BAR * (1 - (1 - j / n) ** 1.6) - .02
        put(drums, tj, doira_tak(.4 + .6 * j / n), .06 + .22 * (j / n) ** 2, (-.3, .3)[j % 2])
    put(sfx, BAR - 1.6, riser(1.6, 200, 7000), .22)
    put(sfx, BAR - 1.0, crash(1.0)[::-1], .18)
    put(sfx, .2, shimmer(2.0), .05, send=.5)                      # halo drawing
    stinger(BAR, 1, 0, 1.1)                                       # LOGO
    for j in range(6):
        put(sfx, BAR + .1 + j * .06, glock(mtof(81 + [0, 3, 7, 12, 15, 19][j]), 1.4), .05, -.5 + j * .2, send=.5)
    put(sfx, BAR + .45, whoosh(.6, 500, 5000), .1)               # title letters
    put(sfx, 4.0, shimmer(1.4), .05, .3, send=.4)                 # logo shine
    # bars 1-3: karnay phrase over a soft groove that builds
    for b in (1, 2, 3):
        root, voicing = chord_at(b, b - 1)
        put(music, bar_t(b), karnay(mtof(root + 12), BAR * .98), .3, -.2, send=.35)
        put(music, bar_t(b), pad(voicing, BAR, 1600, .3, .3), .25, send=.35)
        if b >= 2:
            doira_bar(b, .55 if b == 2 else .8, jingle=b == 3)
            for s in range(16):
                put(music, bar_t(b) + s * S16, spiccato(mtof(root + 12 + (12 if s % 4 == 2 else 0))), .16, send=.1)
    for j, (s, m, d) in enumerate(MEL[0] + [(4 + s, m, d) for s, m, d in MEL[3]]):   # surnay intro phrase
        put(music, bar_t(2) + s * BEAT, surnay(mtof(m), d * BEAT * .95), .2, .1, send=.35)
    put(sfx, bar_t(4) - 1.1, whoosh(1.1, 300, 6000), .2)           # logo flies to the header
    put(sfx, bar_t(4) - 1.4, riser(1.4, 300, 8000), .2)

    mel_i = 0
    for idx, (kind, b0, bars) in enumerate(T0):
        t0 = bar_t(b0)
        if kind in ("intro", "outro"):
            continue
        if kind == "section":
            stinger(t0, b0, 0)
            put(music, t0, karnay(mtof(chord_at(b0, 0)[0] + 12), BAR * 2), .35, send=.35)
            for b in (b0, b0 + 1):
                groove_bar(b, b - b0, melody=False, fill=b == b0 + 1, choir_on=b0 >= BAR_KEY)
            put(sfx, t0 + .25, pop(220), .3)
            for j in range(9):
                put(sfx, t0 + .35 + j * .035 * 4, pop(mtof(74 + (j * 2) % 12 + key_of(b0))), .06, -.6 + j * .15)
            for j in range(9):
                put(sfx, t0 + 1.0 + j * .1, tick(2600 + 80 * j), .05, -.5 + j * .12)
            put(sfx, bar_t(b0 + 2) - 1.0, riser(1.0, 400, 7000), .15)
            continue
        if kind == "score":
            for j, b in enumerate(range(b0, b0 + bars)):
                root, voicing = chord_at(b, 4 + j)
                put(music, bar_t(b), pad(voicing, BAR, 2400, .2, .3), .35, send=.35)
                put(music, bar_t(b), karnay(mtof(root + 12), BAR * .98), .18, send=.3)
                doira_bar(b, .45, jingle=False)
                for s in range(0, 16, 2):
                    put(music, bar_t(b) + s * S16, spiccato(mtof(root + 12)), .18, send=.1)
            put(sfx, t0, impact(1.2), .3)
            for j in range(2):
                put(sfx, t0 + .25 + j * .2, whoosh(.5, 600, 5000, -.5 + j, .2), .12)
                for c in range(24):
                    put(sfx, t0 + .8 + j * .2 + 1.5 * (1 - (1 - c / 24) ** .33), tick(2500 + 40 * c), .045, -.4 + .8 * j)
            put(sfx, t0 + 1.9, whoosh(.8, 400, 4000, -.6, .6), .12)
            stinger(t0 + 2.6, b0 + 1, 7, .5)
            for c in range(30):
                put(sfx, t0 + 2.7 + 1.4 * (1 - (1 - c / 30) ** .33), tick(2800 + 30 * c), .04, .2)
            put(sfx, bar_t(b0 + bars) - 2.0, riser(2.0, 250, 9000), .26)
            continue
        # one item = two bars of the full groove with the surnay melody
        sec_i = b0 >= BAR_KEY
        for j, b in enumerate((b0, b0 + 1)):
            groove_bar(b, mel_i, lead=.24, choir_on=sec_i, fill=j == 1 and mel_i % 4 == 3)
            mel_i += 1
        put(sfx, t0 - .2, whoosh(.6, 400, 6000, -.3, .3, .45), .2)      # star turns
        put(sfx, t0 + .05, shimmer(1.0), .045, send=.4)                   # sparks
        put(sfx, t0 + .1, pop(mtof(55 + key_of(b0))), .18)                # badge flip
        put(sfx, t0 + .25, whoosh(.9, 2000, 9000), .04)                    # icon drawing
        for j in range(6):                                                # chips / title words
            put(sfx, t0 + 1.0 + j * .14, pop(mtof(74 + j * 2 + key_of(b0))), .06, -.4 + j * .15)
    # counters for +30% and +15%, and the icon switches on the clubs card
    for idx, pct in ((19, 30), (20, 15)):
        b0 = T0[idx][1]
        for c in range(pct):
            put(sfx, bar_t(b0) + .8 + 1.6 * (1 - (1 - (c + 1) / pct) ** (1 / 3)), tick(2400 + 45 * c), .05, .3)
    b5 = T0[16][1]
    for j in range(3):
        put(sfx, bar_t(b5) + .1 + j * BAR * 2 / 3.2, shimmer(.8), .05, send=.4)

    # outro: logo flies back and lands on beat 3, slogan words on the next beats, final chord
    t0 = bar_t(BAR_OUTRO)
    put(sfx, t0, whoosh(1.2, 300, 6000), .22)
    put(sfx, t0, riser(1.2, 300, 8000), .2)
    groove_bar(BAR_OUTRO, 7, melody=False, choir_on=True, density=.6)
    stinger(t0 + 1.2, BAR_OUTRO, 4, 1.0)
    put(music, t0 + 1.2, karnay(mtof(40), BAR * 2), .35, send=.4)
    put(sfx, t0 + 1.7, whoosh(.6, 500, 5000), .1)
    for j, at in enumerate((2.4, 3.6, 4.8)):
        tw = t0 + at
        put(drums, tw, epic_drum(1.0), .7)
        put(drums, tw, doira_dum(1.0), .4)
        put(drums, tw, doira_tak(1.0), .25)
        put(sfx, tw, impact(1.0), .25 + .1 * j)
        root, voicing = chord_at(BAR_OUTRO, (0, 5, 7)[j])
        if j < 2:
            put(music, tw, brass_chord([v + 12 for v in voicing], 1.0, .9), .45, send=.3)
    tf = t0 + 4.8
    fin = [64, 68, 71, 76]                                   # E major
    put(music, tf, brass_chord(fin, 6.5, 1.0), .7, send=.5)
    put(music, tf, choir(fin, 6.5), .55, send=.5)
    put(music, tf, karnay(mtof(40), 6.5), .4, send=.4)
    put(music, tf, braam([40, 47, 52], 6.0), .5, send=.4)
    put(sfx, tf, crash(3.4), .32, send=.4)
    for j in range(8):
        put(sfx, tf + .1 + j * .07, glock(mtof(76 + [0, 4, 7, 12, 16, 19, 24, 28][j]), 1.6), .05, -.6 + j * .17, send=.5)


def mixdown():
    t = np.arange(N) / SR
    duck = np.ones(N)
    shape = 1 - .35 * np.exp(-tt(.4) / .1)
    for tk in kick_times:
        i = int(tk * SR)
        n = min(len(shape), N - i)
        if n > 0:
            duck[i:i + n] = np.minimum(duck[i:i + n], shape[:n])
    dry = drums.x + music.x * duck[:, None] + sfx.x
    wet = np.stack([signal.fftconvolve(verb.x[:, c], reverb_ir(2.6)[:, c])[:N] for c in range(2)], 1)
    mix = hp(dry + 0.35 * wet, 30)
    mix = norm(mix, 2.1)
    mix = np.tanh(mix) / np.tanh(2.1)
    mix *= np.clip((DUR - t) / 1.6, 0, 1)[:, None] ** 1.5
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
