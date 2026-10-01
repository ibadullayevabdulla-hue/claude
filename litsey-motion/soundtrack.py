#!/usr/bin/env python3
"""Original military-march soundtrack for the lyceum video, synthesised from
scratch and timed to index.html (120 BPM, one bar = 2 s).

Snare-drum cadences, concert bass drum, timpani, a brass fanfare, low string
ostinato and a choir pad; D minor, rising to E minor for the benefits section,
ending on a bright E major chord. Plus sound effects for every animation.

    python3 soundtrack.py          # writes out/soundtrack.wav and prints its path

Needs numpy and scipy.
"""
import pathlib
import wave

import numpy as np
from scipy import signal

HERE = pathlib.Path(__file__).resolve().parent
SR = 48000
BPM = 120
BEAT = 60 / BPM
BAR = 4 * BEAT
rng = np.random.default_rng(1221)

# ───────────── timeline (mirrors SCENES in index.html) ─────────────
SCENES = [("intro", 3), ("section", 2)] + [("panel", 2)] * 8 + [("score", 2), ("section", 2)] + [("panel", 2)] * 9 + [("outro", 3)]
T0, b = [], 0
for kind, bars in SCENES:
    T0.append((kind, b))
    b += bars
TOTAL_BARS = b
DUR = TOTAL_BARS * BAR
N = int(DUR * SR)
BAR_SEC_I = T0[11][1]      # benefits section starts here (key change)
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


# ───────────── harmony & melody ─────────────
# 4-bar loop i–VI–III–VII (Dm Bb F C); every 8 bars ends on A major (V) for the cadence.
CH = {"Dm": (38, [62, 65, 69]), "Bb": (34, [62, 65, 70]), "F": (41, [60, 65, 69]), "C": (36, [60, 64, 67]), "A": (33, [61, 64, 69]),
      "D": (38, [62, 66, 69])}
PROG = ["Dm", "Bb", "F", "C", "Dm", "Bb", "F", "A"]
MEL = [  # (beat, midi, beats) per bar
    [(0, 74, 1), (1, 69, .5), (1.5, 69, .5), (2, 74, 1), (3, 76, .5), (3.5, 77, .5)],
    [(0, 79, 1.5), (1.5, 77, .5), (2, 76, 1), (3, 74, 1)],
    [(0, 72, 1), (1, 77, 1), (2, 81, 1.5), (3.5, 79, .5)],
    [(0, 76, 2), (2, 72, 1), (3, 76, 1)],
    [(0, 77, 1), (1, 76, .5), (1.5, 74, .5), (2, 81, 1.5), (3.5, 77, .5)],
    [(0, 79, 1), (1, 77, 1), (2, 74, 1), (3, 70, 1)],
    [(0, 72, 1), (1, 69, .5), (1.5, 72, .5), (2, 77, 1), (3, 76, 1)],
    [(0, 76, 2), (2, 73, 1), (3, 69, 1)],
]
FANFARE = [(0, 62, .33), (.33, 62, .33), (.67, 62, .33), (1, 69, 1), (2, 69, .33), (2.33, 69, .33), (2.67, 69, .33), (3, 74, 1)]


def key_of(b):
    return 2 if b >= BAR_SEC_I else 0


def chord_at(b, i):
    root, voicing = CH[PROG[i % 8]]
    k = key_of(b)
    return root + k, [v + k for v in voicing]


def add_march_bar(b, i, melody=True, lead_gain=.2, choir_on=False, glock_on=False):
    """One bar of the march: bass drum 1 & 3, snare cadence, strings ostinato, brass chords, melody."""
    t0 = bar_t(b)
    at = lambda beat: t0 + beat * BEAT  # noqa: E731
    root, voicing = chord_at(b, i)
    for beat in (0, 2):
        put(drums, at(beat), bass_drum(.9), .55)
    # field-drum cadence: accents on 2 & 4, flams and a short roll at the end of the bar
    for pos, v in ((1, 1), (1.5, .45), (2.5, .5), (2.75, .4), (3, 1)):
        put(drums, at(pos), snare_m(v), .32 * v, .15, send=.15)
        if v == 1:
            put(drums, at(pos) - .018, snare_m(.4), .1, .15)
    if i % 2 == 1:
        put(drums, at(3.5), snare_roll(BEAT * .5, .3, .8), .22, .15, send=.15)
    else:
        for pos in (3.5, 3.75):
            put(drums, at(pos), snare_m(.6), .18, .15)
    # timpani on the root
    put(drums, at(0), timpani(mtof(root + 12)), .35, -.2, send=.2)
    # low strings: driving eighths on root and fifth
    for e in range(8):
        n = root + 12 + (7 if e in (3, 7) else 0)
        put(music, at(e / 2), strings_stac(mtof(n), BEAT * .45), .3, -.3, send=.15)
        put(music, at(e / 2), strings_stac(mtof(n + 12), BEAT * .45), .16, .3, send=.15)
    # brass chords: on 1, and a push on the & of 3
    put(music, at(0), brass_chord(voicing, BEAT * 1.6, .7), .5, send=.25)
    put(music, at(2.5), brass_chord(voicing, BEAT * 1.4, .6), .36, send=.25)
    put(music, at(0), brass(mtof(root), BEAT * 3.8, .5), .28, -.1, send=.15)  # tuba/trombone root
    if choir_on:
        put(music, t0, choir(voicing, BAR), .55, send=.4)
    if melody:
        k = key_of(b)
        for s, m, d in MEL[i % 8]:
            put(music, at(s), brass(mtof(m + k), d * BEAT * .92, 1.0), lead_gain, .1, send=.3)
            if glock_on:
                put(music, at(s), glock(mtof(m + k)), .07, .35, send=.3)


def stinger(t, root_midis, gain=1.0, d=1.8):
    """Big hit: bass drum, timpani, crash, brass chord."""
    put(drums, t, bass_drum(1.0), .8 * gain)
    put(drums, t, timpani(mtof(root_midis[0] - 12), 2.4), .5 * gain, send=.3)
    put(sfx, t, crash(2.6), .3 * gain, send=.3)
    put(music, t, brass_chord(root_midis, d, 1.0), .7 * gain, send=.4)
    put(sfx, t, impact(1.6), .35 * gain)


# ───────────── build ─────────────
def build():
    # intro: bar 0 build-up, logo slam at 2.0 s, fanfare
    put(drums, 0, snare_roll(BAR - .05, .05, .9), .35, .1, send=.2)
    put(drums, 0, timp_roll(mtof(38), BAR - .1, .05, .9), .5, -.1, send=.25)
    put(sfx, BAR - 1.3, riser(1.3, 200, 7000), .22)
    put(sfx, BAR - 1.0, crash(1.0)[::-1], .2)
    put(music, 0, pad([50, 57, 62], BAR, 1200, 1.2, .2), .3, send=.3)
    stinger(BAR, [62, 65, 69, 74], 1.0, BAR * .9)
    for i in range(6):
        put(sfx, BAR + .1 + i * .05, glock(mtof(81 + [0, 5, 7, 12, 17, 19][i]), 1.4), .06, -.5 + i * .2, send=.5)
    # bars 1–2: fanfare over timpani
    for b in (1, 2):
        t0 = bar_t(b)
        for s, m, d in FANFARE:
            put(music, t0 + s * BEAT, brass(mtof(m + 12), d * BEAT * .9, 1.0), .26, send=.35)
            put(music, t0 + s * BEAT, brass(mtof(m), d * BEAT * .9, .8), .14, -.2, send=.3)
        for beat in (0, 1, 2, 3):
            put(drums, t0 + beat * BEAT, timpani(mtof(50 if beat % 2 == 0 else 45), 1.0), .3, send=.2)
        put(music, t0, pad([50, 57, 62, 65], BAR, 2000, .3, .3), .25, send=.3)
    put(drums, bar_t(2) + 2 * BEAT, snare_roll(BEAT * 2, .1, 1.0), .3, send=.2)
    put(sfx, 2.45, whoosh(.6, 500, 5000), .1)                        # title letters
    put(sfx, 3.1, shing(), .08, send=.4)                             # logo shine + title wipe
    put(sfx, 5.0, shing(), .06, .3, send=.4)

    # scenes
    i_mel = 0
    for idx, (kind, b0) in enumerate(T0):
        t0 = bar_t(b0)
        if kind in ("intro", "outro"):
            continue
        if kind == "section":
            root, voicing = chord_at(b0, 0)
            stinger(t0, [v + 12 for v in voicing], .9)
            put(sfx, t0 - .35, whoosh(.5, 300, 6000), .2)
            for b in (b0, b0 + 1):
                add_march_bar(b, b - b0, melody=False)
            for j in range(9):  # tracker nodes popping in
                put(sfx, t0 + .5 + j * .12, pop(mtof(74 + (j * 2) % 12 + key_of(b0))), .08, -.6 + j * .15)
            put(sfx, t0 + .9, shing(), .06, send=.4)
            put(drums, bar_t(b0 + 1) + 2 * BEAT, snare_roll(BEAT * 2, .1, .9), .25, send=.2)
            continue
        if kind == "score":
            for j, b in enumerate((b0, b0 + 1)):
                root, voicing = chord_at(b, 6 + j)
                put(music, bar_t(b), pad(voicing, BAR, 2400, .2, .3), .35, send=.3)
                put(drums, bar_t(b), timpani(mtof(root + 12)), .4, send=.2)
                for e in range(8):
                    put(music, bar_t(b) + e * BEAT / 2, strings_stac(mtof(root + 12), BEAT * .45), .3, send=.15)
            for j in range(2):  # score counters
                for c in range(0, 24):
                    put(sfx, t0 + .5 + j * .2 + 1.2 * (1 - (1 - c / 24) ** 0.33), tick(2600 + 40 * c), .05, -.4 + .8 * j)
            put(sfx, t0 + 1.1, whoosh(.7, 400, 4000, -.6, .6), .12)       # bar wipe
            put(sfx, t0 + 1.6, pop(700), .2)
            stinger(t0 + 1.6, [64, 67, 72], .45, 1.2)
            put(sfx, BAR_SEC_I * BAR - 1.4, riser(1.4, 250, 8000), .25)
            put(drums, bar_t(b0 + 1), snare_roll(BAR, .05, 1.0), .3, send=.2)
            continue
        # panel
        sec_i = b0 >= BAR_SEC_I
        for b in (b0, b0 + 1):
            add_march_bar(b, i_mel, lead_gain=.2 if not sec_i else .22, choir_on=sec_i, glock_on=sec_i or i_mel >= 8)
            i_mel += 1
        put(sfx, t0 - .1, whoosh(.65, 500, 5500, .7, -.2, .4), .2)       # card flies in
        put(sfx, t0 + .3, shing(), .07, -.4, send=.4)                     # badge spin
        put(sfx, t0 + .45, pop(mtof(79)), .1, -.4)
        put(sfx, t0 + .75, whoosh(.3, 2000, 8000), .05)                   # gold rule
        put(sfx, t0 + .8, glock(mtof(88 + key_of(b0)), .8), .04, .5, send=.5)  # shine sweep
        for j in range(4):                                                # chips / extra photos
            put(sfx, t0 + 1.15 + j * .16, pop(mtof(76 + j * 3)), .08, -.4)
    # the benefits shields: counter ticks
    for idx in (18, 19):
        kind, b0 = T0[idx]
        pct = 30 if idx == 18 else 15
        for c in range(pct):
            u = (c + 1) / pct
            put(sfx, bar_t(b0) + .6 + 1.4 * (1 - (1 - u) ** (1 / 3)), tick(2400 + 50 * c), .05, .3)

    # outro: big hit, slogan words on the beat, final E major chord
    t0 = bar_t(BAR_OUTRO)
    stinger(t0, [64, 67, 71, 76], 1.0, BAR * 1.2)
    put(music, t0, choir([64, 67, 71], BAR), .6, send=.5)
    put(drums, t0 + BAR - BEAT * 2, snare_roll(BEAT * 2, .1, 1.0), .3, send=.2)
    for j, beat in enumerate((0, 1, 1.5, 2)):
        tw = t0 + BAR + beat * BEAT
        put(drums, tw, bass_drum(1.0), .6)
        put(drums, tw, snare_m(1.0), .35, send=.25)
        if j < 3:
            put(music, tw, brass_chord([64, 68, 71], BEAT * .8, .9), .45, send=.3)
    tf = t0 + BAR + 2 * BEAT
    put(music, tf, brass_chord([52, 64, 68, 71, 76], BAR * 1.4, 1.0), .75, send=.5)
    put(music, tf, choir([64, 68, 71, 76], BAR * 1.3), .6, send=.5)
    put(drums, tf, timp_roll(mtof(40), BEAT * 2.5, .9, .3), .4, send=.3)
    put(sfx, tf, crash(3.0), .35, send=.4)
    put(sfx, tf, impact(2.0), .4)
    for i in range(8):
        put(sfx, tf + .1 + i * .06, glock(mtof(76 + [0, 4, 7, 12, 16, 19, 24, 28][i]), 1.6), .05, -.6 + i * .17, send=.5)


def mixdown():
    t = np.arange(N) / SR
    dry = drums.x * 1.0 + music.x + sfx.x
    wet = np.stack([signal.fftconvolve(verb.x[:, c], reverb_ir(2.4)[:, c])[:N] for c in range(2)], 1)
    mix = hp(dry + 0.35 * wet, 30)
    mix = norm(mix, 2.1)                 # soft-clip the drum peaks for a louder, denser band
    mix = np.tanh(mix) / np.tanh(2.1)
    mix *= np.clip((DUR - t) / 1.2, 0, 1)[:, None] ** 1.5
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
