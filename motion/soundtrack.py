#!/usr/bin/env python3
"""Soundtrack for the Claude Code motion: synthesised music + sound effects,
timed against the animation in index.html (all times below are in seconds of
the 30 s timeline).

    python3 soundtrack.py               # out/soundtrack-uz.wav
    python3 soundtrack.py --lang en     # out/soundtrack-en.wav

Needs numpy and scipy (pip install numpy scipy).
"""
import argparse
import pathlib
import re
import wave

import numpy as np
from scipy import signal

SR = 48000
DUR = 30.0
N = int(SR * DUR)
HERE = pathlib.Path(__file__).resolve().parent

# 126.3 BPM grid. Bars land on the intro flash (3.7), the drop (17.0) and the
# kinetic-word cuts (17.0, 18.9, 20.8 — 17.95 and 19.85 are half bars).
BEAT = 0.475
BAR = 4 * BEAT
ORIGIN = 17.0 - 9 * BAR

rng = np.random.default_rng(11)


# ───────────── dsp helpers ─────────────
def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def tt(d):
    return np.arange(int(d * SR)) / SR


def _sos(kind, f, order=2):
    return signal.butter(order, f, btype=kind, fs=SR, output="sos")


def lp(x, f, o=2):
    return signal.sosfilt(_sos("lowpass", f, o), x)


def hp(x, f, o=2):
    return signal.sosfilt(_sos("highpass", f, o), x)


def bp(x, lo, hi, o=2):
    return signal.sosfilt(_sos("bandpass", [lo, hi], o), x)


def noise(d):
    return rng.standard_normal(int(d * SR))


def norm(x, peak=1.0):
    m = np.max(np.abs(x))
    return x * (peak / m) if m > 0 else x


def env_ar(n, a, r):
    """Linear attack / release envelope over n samples."""
    e = np.ones(n)
    ai, ri = min(n, int(a * SR)), min(n, int(r * SR))
    if ai:
        e[:ai] = np.linspace(0, 1, ai)
    if ri:
        e[n - ri:] *= np.linspace(1, 0, ri)
    return e


def sweep_noise(d, f0, f1, width=0.5):
    """Noise through a band-pass whose centre glides exponentially f0 -> f1."""
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


drums, music, sfx, verb = Bus(), Bus(), Bus(), Bus()
kick_times = []


def put(bus, t, sig, gain=1.0, pan=0.0, send=0.0):
    bus.add(t, sig, gain, pan)
    if send:
        verb.add(t, sig, gain * send, pan)


# ───────────── instruments ─────────────
def kick():
    t = tt(0.5)
    f = 48 + 120 * np.exp(-t * 32)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6.5)
    click = hp(noise(0.5), 2500) * np.exp(-t * 400) * 0.3
    return np.tanh(1.8 * (body + click)) / np.tanh(1.8)


def clap():
    t = tt(0.4)
    e = sum(np.where(t >= d, np.exp(-np.maximum(t - d, 0) * 220), 0) for d in (0, 0.011, 0.023))
    e = e + np.where(t >= 0.03, np.exp(-np.maximum(t - 0.03, 0) * 13), 0) * 0.7
    return norm(bp(noise(0.4), 900, 3800) * e)


def snare(pitch=1.0):
    t = tt(0.25)
    tone = np.sin(2 * np.pi * 190 * pitch * t) * np.exp(-t * 30) * 0.6
    rattle = bp(noise(0.25), 1500, 9000) * np.exp(-t * 20)
    return norm(tone + rattle)


def hat(open_=False):
    d = 0.32 if open_ else 0.07
    t = tt(d)
    return norm(hp(noise(d), 7500, 4) * np.exp(-t * (11 if open_ else 85)))


def bass(f, d):
    t = tt(d)
    x = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) + 0.12 * np.sin(6 * np.pi * f * t)
    e = env_ar(len(t), 0.004, 0.03) * (0.65 + 0.35 * np.exp(-t * 9))
    return np.tanh(1.7 * x) * e


def pad(midis, d, cutoff=1800, att=0.35, rel=0.7):
    """Detuned additive saw pad, stereo."""
    t = tt(d + rel)
    out = np.zeros((len(t), 2))
    for m in midis:
        for j, cents in enumerate((-9, 0, 9)):
            f = mtof(m) * 2 ** (cents / 1200)
            s = np.zeros(len(t))
            for k in range(1, 16):
                fk = f * k
                if fk > 12000:
                    break
                s += np.sin(2 * np.pi * fk * t + rng.uniform(0, 2 * np.pi)) * np.exp(-fk / cutoff) / k
            out[:, 0] += s * (1.0, 0.75, 0.35)[j]
            out[:, 1] += s * (0.35, 0.75, 1.0)[j]
    e = env_ar(len(t), att, 0) * np.where(t > d, np.exp(-(t - d) * 5 / rel), 1)
    e *= 1 + 0.06 * np.sin(2 * np.pi * 0.35 * t)
    return out * e[:, None] / (len(midis) * 2.2)


def pluck(f, d=0.6, bright=1.0):
    t = tt(d)
    x = sum(np.sin(2 * np.pi * f * k * t) * np.exp(-t * (3 + k * 2.6 / bright)) / k ** 1.1 for k in range(1, 9))
    return x * env_ar(len(t), 0.002, 0.02)


def bell(f, d=1.6):
    t = tt(d)
    parts = ((1, 1, 1.8), (2.0, 0.45, 2.6), (2.76, 0.3, 3.4), (5.4, 0.14, 5.5), (8.93, 0.06, 8))
    x = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * dec) for r, a, dec in parts)
    return x * env_ar(len(t), 0.002, 0.05)


def stab(midis, d=0.5, cutoff=3800):
    t = tt(d)
    x = np.zeros(len(t))
    for m in midis:
        f = mtof(m)
        for k in range(1, 14):
            if f * k > 14000:
                break
            x += np.sin(2 * np.pi * f * k * t) * np.exp(-f * k / cutoff) / k
    return norm(x * np.exp(-t * 6.5) * env_ar(len(t), 0.003, 0.03))


def key(space=False, release=True):
    """Mechanical keyboard keystroke."""
    t = tt(0.1)
    body_f = rng.uniform(110, 140) if space else rng.uniform(175, 245)
    body = np.sin(2 * np.pi * body_f * t) * np.exp(-t * (50 if space else 95))
    clack = bp(noise(0.1), 1800, 7000) * np.exp(-t * (450 if space else 700))
    tick = bp(noise(0.1), 3500, 11000) * np.exp(-t * 1600)
    x = 0.6 * body + 0.9 * clack + 0.35 * tick
    if release:
        r = int(rng.uniform(0.04, 0.06) * SR)
        x[r:] += (bp(noise(0.1), 2500, 8000) * np.exp(-t * 900))[: len(x) - r] * 0.25
    return norm(x) * rng.uniform(0.8, 1.0)


def tick(f=3200):
    t = tt(0.04)
    return np.sin(2 * np.pi * f * t) * np.exp(-t * 180) + bp(noise(0.04), 4000, 12000) * np.exp(-t * 900) * 0.2


def blip(f):
    out = np.zeros(int(0.2 * SR))
    for i, (ff, dt) in enumerate(((f, 0), (f * 1.5, 0.05))):
        t = tt(0.15)
        x = (np.sin(2 * np.pi * ff * t) + 0.18 * np.sin(6 * np.pi * ff * t)) * np.exp(-t * 32)
        s = int(dt * SR)
        out[s:s + len(x)] += x * (1, 0.8)[i]
    return out


def pop(f1):
    t = tt(0.16)
    f = f1 * 0.45 + f1 * 0.55 * (1 - np.exp(-t * 70))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 26)
    return x + hp(noise(0.16), 3000) * np.exp(-t * 700) * 0.15


def whoosh(d, f0, f1, pan0=0.0, pan1=0.0, peak=0.55):
    x = sweep_noise(d, f0, f1, 0.45)
    u = np.linspace(0, 1, len(x))
    e = np.where(u < peak, (u / peak) ** 2, ((1 - u) / (1 - peak)) ** 1.6)
    x *= e
    a = (np.linspace(pan0, pan1, len(x)) + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], 1) * np.sqrt(2)


def riser(d, f0=300, f1=9000):
    t = tt(d)
    u = t / d
    air = sweep_noise(d, f0, f1, 0.5) * u ** 2.2
    fp = 180 * (8 ** u)
    ph = 2 * np.pi * np.cumsum(fp) / SR
    tone = (np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.2 * np.sin(3 * ph)) * u ** 2.6 * 0.35
    trem = 1 - 0.35 * (0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(4 + 18 * u ** 2) / SR))
    return (air + tone) * trem


def crash(d=2.2):
    t = tt(d)
    return norm(hp(noise(d), 3800, 4) * np.exp(-t * 2.3) + bp(noise(d), 6000, 14000) * np.exp(-t * 4) * 0.5)


def impact(d=2.2):
    t = tt(d)
    f = 30 + 70 * np.exp(-t * 9)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.4)
    thump = lp(noise(d), 260) * np.exp(-t * 14) * 3
    return norm(np.tanh(1.4 * (sub + thump)))


def reverb_ir(rt60=2.2):
    t = tt(rt60)
    ir = np.stack([lp(noise(rt60), 5500) for _ in range(2)], 1) * np.exp(-6.9 * t / rt60)[:, None]
    ir[: int(0.004 * SR)] *= np.linspace(0, 1, int(0.004 * SR))[:, None]
    ir = np.concatenate([np.zeros((int(0.018 * SR), 2)), ir])
    return ir / np.sqrt(np.sum(ir ** 2) / 2)


# ───────────── arrangement ─────────────
PENTA = [69, 72, 74, 76, 79, 81, 84, 86, 88, 91, 93, 96]  # A minor pentatonic, A4 up
PROG = [  # bass root, pad voicing
    (45, [57, 60, 64, 71]),  # Am(add9)
    (41, [53, 57, 60, 64]),  # Fmaj7
    (48, [55, 60, 62, 64]),  # C(add9)
    (43, [55, 59, 62, 64]),  # G6
]


def bar_t(k):
    return ORIGIN + k * BAR


def chord(k):
    return PROG[(k - 9) % 4]


def add_kick(t, gain=1.0):
    put(drums, t, kick(), gain)
    kick_times.append(t)


def build(lang):
    page = (HERE / "index.html").read_text(encoding="utf-8")
    li = 0 if lang == "uz" else 1
    prompt = re.findall(r'prompt: "([^"]*)"', page)[li]
    final = re.findall(r'final: "([^"]*)"', page)[li]
    install = re.search(r'const INSTALL = "([^"]*)"', page).group(1)

    # ── intro 0–3.7 ──
    put(music, 0.0, pad([57, 64, 71, 76], 3.75, cutoff=1300, att=1.8, rel=0.5), 0.55, send=0.4)
    put(music, 0.0, bass(55.0, 3.7) * np.linspace(0, 1, int(3.7 * SR)) ** 1.5, 0.22)
    put(sfx, 0.12, bell(mtof(81), 2.5), 0.22, send=0.6)
    put(sfx, 0.14, bell(mtof(88), 2.5), 0.12, 0.2, send=0.6)
    put(sfx, 0.08, whoosh(1.0, 500, 5000, 0, 0, 0.35), 0.18, send=0.3)
    put(sfx, 0.95, whoosh(0.9, 1400, 500, 0, -0.5, 0.45), 0.16)
    for i in range(11):  # title letters
        put(sfx, 1.62 + i * 0.045, pluck(mtof(PENTA[i % 8 + 3]), 0.5, 1.4), 0.07, -0.6 + i * 0.12, send=0.5)
    put(sfx, 2.25, bell(mtof(64), 2.0), 0.12, send=0.5)
    put(sfx, 3.68 - 1.7, riser(1.7), 0.3)
    put(sfx, 3.68 - 1.3, crash(1.3)[::-1], 0.22)
    put(sfx, 3.68, impact(), 0.85, send=0.25)
    put(sfx, 3.68, crash(), 0.25, send=0.3)
    put(sfx, 3.95, whoosh(0.7, 300, 2600, 0.3, 0.3, 0.4), 0.18)

    # ── terminal: bars 2–3 (3.7–7.5) calm, bars 4–7 (7.5–15.1) groove ──
    for k in range(2, 8):
        t0 = bar_t(k)
        root, voicing = chord(k)
        groove = k >= 4
        put(music, t0, pad(voicing, BAR, cutoff=1500 if groove else 1100, att=0.3), 0.5, send=0.3)
        if groove:
            for s in range(8):
                put(music, t0 + s * BEAT / 2, bass(mtof(root - 12 + (12 if s in (3, 6) else 0)), BEAT / 2 * 0.9), 0.3 if s % 2 == 0 else 0.22)
            for b in (0, 1.75, 2.5):
                add_kick(t0 + b * BEAT, 0.62)
            for b in (1, 3):
                put(drums, t0 + b * BEAT, clap(), 0.2, send=0.25)
            for s in range(16):
                put(drums, t0 + s * BEAT / 4, hat(), (0.09, 0.035, 0.06, 0.035)[s % 4], 0.25)
            tones = [voicing[i % 4] + 12 for i in (0, 2, 1, 3, 2, 0, 3, 1)]
            for s, m in enumerate(tones):
                put(music, t0 + s * BEAT / 2, pluck(mtof(m), 0.45, 1.2), 0.075, (-0.4, 0.4)[s % 2], send=0.5)
        else:
            put(music, t0, bass(mtof(root - 12), BAR * 0.95), 0.2)
            if k == 3:
                for s in range(8):
                    put(drums, t0 + s * BEAT / 2, hat(), 0.04 if s % 2 else 0.06, 0.25)

    put(sfx, 4.75, whoosh(0.7, 2200, 500, -0.7, -0.2, 0.4), 0.13)
    # typing "claude" + enter
    for n in range(1, 7):
        put(sfx, 4.6 + n / 14, key(), 0.42, rng.uniform(-0.15, 0.15))
    put(sfx, 5.08, key(space=True), 0.55)
    for i, m in enumerate((84, 89, 93)):  # welcome box
        put(sfx, 5.15 + i * 0.04, bell(mtof(m), 1.2), 0.08, send=0.5)
    # typing the prompt + enter
    for n in range(1, len(prompt) + 1):
        put(sfx, 5.85 + n / 36, key(prompt[n - 1] == " ", release=False), 0.36, rng.uniform(-0.15, 0.15))
    put(sfx, 7.6, key(space=True), 0.6)
    # agent activity
    for tb, m in ((8.75, 81), (9.35, 84), (10.0, 86), (12.55, 88), (14.55, 91)):
        put(sfx, tb, blip(mtof(m)), 0.16, 0.2, send=0.3)
    for to in (9.05, 9.65, 10.3, 14.85):
        put(sfx, to, tick(2600), 0.1)
    for j in range(10):  # diff lines
        put(sfx, 10.57 + j * 0.085, tick(2200 + j * 160), 0.07, -0.3 + j * 0.06)

    def in_out_cubic(x):
        return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2

    for m in range(1, 25):  # test counter
        lo, hi = 0.0, 1.0
        for _ in range(40):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if in_out_cubic(mid) < m / 24 else (lo, mid)
        put(sfx, 12.95 + 1.15 * hi, tick(1800 + m * 70), 0.06, 0.25)
    for i, m in enumerate((84, 88, 91, 96)):  # tests passed
        put(sfx, 14.15 + i * 0.06, bell(mtof(m), 1.4), 0.13, 0.3, send=0.45)
    put(sfx, 14.2, pop(1100), 0.2, 0.6)
    put(sfx, 14.95, pop(900), 0.18, 0.5)
    for n in range(1, len(final) + 1, 3):  # streamed answer
        put(sfx, 15.35 + n / 78, tick(rng.uniform(2800, 3600)), 0.035, rng.uniform(-0.2, 0.2))

    # ── build-up bar 8 (15.1–17.0) ──
    t0 = bar_t(8)
    put(music, t0, pad(chord(8)[1], BAR - 0.12, cutoff=2600, att=0.5, rel=0.08), 0.65, send=0.3)
    put(music, t0, bass(mtof(43 - 12), BAR - 0.12), 0.2)
    hits = [b * 0.5 for b in range(4)] + [2 + b * 0.25 for b in range(4)] + [3 + b * 0.125 for b in range(6)]
    for i, b in enumerate(hits):
        put(drums, t0 + b * BEAT, snare(1 + i * 0.03), 0.2 + 0.45 * (i / len(hits)) ** 1.5, send=0.2)
    put(sfx, 17.0 - 1.95, riser(1.93), 0.38)
    put(sfx, 17.0 - 1.2, crash(1.2)[::-1], 0.25)

    # ── drop: bars 9–11 (17.0–22.7), cards bar 12–13 (22.7–25.55) ──
    for k in range(9, 14):
        t0 = bar_t(k)
        root, voicing = chord(k)
        drop = k <= 11
        last = k == 13
        put(music, t0, pad([v + 12 for v in voicing[1:]] + voicing, BAR, cutoff=3200, att=0.05), 0.42, send=0.3)
        beats = 2 if last else 4
        for b in range(beats):
            add_kick(t0 + b * BEAT, 0.95)
            if b % 2:
                put(drums, t0 + b * BEAT, clap(), 0.4, send=0.3)
            if drop:
                put(drums, t0 + (b + 0.5) * BEAT, hat(True), 0.13, 0.3)
            for s in range(4):
                put(drums, t0 + (b + s / 4) * BEAT, hat(), (0.1, 0.04, 0.07, 0.04)[s], -0.25)
            for s in (0.5,) if not drop else (0.5, 0.75):
                put(music, t0 + (b + s) * BEAT, bass(mtof(root - 12), BEAT * 0.22), 0.4)
            put(music, t0 + b * BEAT, bass(mtof(root - 24), BEAT * 0.4), 0.22)
    put(sfx, 17.0, impact(), 0.75, send=0.2)
    put(sfx, 17.0, crash(), 0.3, send=0.3)
    for i, ws in enumerate((17.0, 17.95, 18.9, 19.85, 20.8)):
        voicing = [v + 12 for v in chord(9 + (i // 2))[1]]
        put(music, ws, stab(voicing), 0.32, send=0.35)
        p0, p1 = {"b": (0, 0), "r": (0.8, -0.4), "t": (0, 0), "l": (-0.8, 0.4)}["brtlb"[i]]
        put(sfx, ws - 0.12, whoosh(0.6, 400, 4500, p0, p1, 0.4), 0.3)
        if i:
            put(sfx, ws, impact(0.8), 0.32)
    put(sfx, 22.0, whoosh(0.8, 300, 5000, 0, 0, 0.35), 0.3, send=0.3)
    put(sfx, 22.12, impact(1.2), 0.4)
    for i in range(6):  # cards pop in, then the highlight sweep
        put(sfx, 22.6 + i * 0.085, pop(mtof(PENTA[i + 4])), 0.16, -0.5 + (i % 3) * 0.5)
        put(sfx, 23.6 + i * 0.21, bell(mtof(PENTA[i + 6]), 0.9), 0.05, -0.5 + (i % 3) * 0.5, send=0.5)

    # ── converge + outro (25.55–30) ──
    put(sfx, 25.3, whoosh(0.6, 5000, 400, 0.6, 0, 0.75), 0.25)
    put(sfx, 26.5 - 1.2, crash(1.2)[::-1], 0.22)
    put(sfx, 26.5 - 0.95, riser(0.95, 800, 9000), 0.22)
    put(sfx, 25.85, bell(mtof(93), 2.2), 0.1, send=0.6)
    put(sfx, 25.87, bell(mtof(100), 2.2), 0.06, send=0.6)
    put(sfx, 26.5, impact(2.6), 0.9, send=0.3)
    put(sfx, 26.5, crash(2.6), 0.28, send=0.4)
    put(music, 26.5, stab([65, 69, 72, 76, 81]), 0.36, send=0.5)
    put(music, 26.5, pad([53, 57, 60, 64, 69], BAR, cutoff=2400, att=0.02, rel=0.9), 0.5, send=0.4)
    put(music, 26.5, bass(mtof(29), BAR), 0.3)
    put(music, 28.4, pad([48, 55, 62, 64, 67, 71], 1.6, cutoff=2000, att=0.4, rel=0.8), 0.5, send=0.5)
    put(music, 28.4, bass(mtof(36), 1.6), 0.28)
    for s in range(14):
        m = (69, 72, 76, 77, 81, 76, 72, 77)[s % 8] if s < 8 else (67, 72, 74, 76, 79, 76)[s - 8]
        put(music, 26.5 + s * BEAT / 2, pluck(mtof(m), 0.5), 0.06, (-0.35, 0.35)[s % 2], send=0.6)
    for i in range(11):  # title letters
        put(sfx, 26.9 + i * 0.035, pluck(mtof(PENTA[i % 9 + 3]), 0.4, 1.5), 0.05, -0.5 + i * 0.1, send=0.6)
    put(sfx, 27.35, bell(mtof(76), 1.8), 0.08, send=0.5)
    put(sfx, 27.7, whoosh(0.5, 600, 3000, -0.3, 0.3, 0.5), 0.14)
    for n in range(1, len(install) + 1, 2):
        put(sfx, 27.95 + n / 58, key(install[n - 1] == " ", release=False), 0.24, rng.uniform(-0.15, 0.15))
    put(sfx, 28.65, bell(mtof(88), 1.6), 0.12, 0.2, send=0.5)
    put(sfx, 28.7, bell(mtof(93), 1.6), 0.08, 0.2, send=0.5)


def mixdown():
    duck = np.ones(N)
    shape = 1 - 0.55 * np.exp(-tt(0.35) / 0.09)
    for tk in kick_times:
        i = int(tk * SR)
        n = min(len(shape), N - i)
        duck[i:i + n] = np.minimum(duck[i:i + n], shape[:n])
    dry = drums.x + music.x * duck[:, None] + sfx.x
    wet = np.stack([signal.fftconvolve(verb.x[:, c], reverb_ir()[:, c])[:N] for c in range(2)], 1)
    mix = dry + 0.32 * wet
    mix = np.stack([hp(mix[:, c], 28) for c in range(2)], 1)
    mix = norm(mix, 1.6)
    mix = np.tanh(mix) / np.tanh(1.6)                       # soft limiter
    t = np.arange(N) / SR
    mix *= np.clip((30.0 - t) / 0.6, 0, 1)[:, None] ** 1.5  # follows the video's fade to black
    mix *= np.clip(t / 0.01, 0, 1)[:, None]
    return norm(mix, 0.89)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="uz", choices=["uz", "en"])
    ap.add_argument("--out")
    a = ap.parse_args()
    out = pathlib.Path(a.out) if a.out else HERE / "out" / f"soundtrack-{a.lang}.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    build(a.lang)
    pcm = (mixdown() * 32767).astype("<i2")
    with wave.open(str(out), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(out)


if __name__ == "__main__":
    main()
