#!/usr/bin/env python3
"""Original, copyright-free soundtrack for the October premieres video.

A playful spooky-season groove in D minor at 120 BPM (one film = two bars):
pizzicato strings, celesta, organ, choir pad and a theremin lead, plus sound
effects synced to index.html (poster swipes, calendar page flips, date stamps,
sparkles, calendar ticks, outro pops and the subscribe click).

    python3 soundtrack.py          # writes out/soundtrack.wav and prints its path
"""
import json
import pathlib
import wave

import numpy as np
from scipy import signal

HERE = pathlib.Path(__file__).resolve().parent
SR = 48000
BPM = 120
BEAT = 60 / BPM
BAR = 4 * BEAT
PER = 2 * BAR
INTRO = 2 * BAR
FILMS = json.loads((HERE / "films.json").read_text())
OUTRO = INTRO + len(FILMS) * PER
DUR = OUTRO + 3 * BAR
N = int(DUR * SR)
rng = np.random.default_rng(1031)


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


music, drums, sfx, verb = Bus(), Bus(), Bus(), Bus()
kick_times = []


def put(bus, t, sig, gain=1.0, pan=0.0, send=0.0):
    bus.add(t, sig, gain, pan)
    if send:
        verb.add(t, sig, gain * send, pan)


# ───────────── instruments ─────────────
def kick():
    t = tt(0.45)
    body = np.sin(phase(48 + 120 * np.exp(-t * 30))) * np.exp(-t * 7)
    return np.tanh(1.8 * (body + hp(noise(0.45), 2500) * np.exp(-t * 400) * 0.25)) / np.tanh(1.8)


def clap():
    t = tt(0.35)
    e = sum(np.where(t >= d, np.exp(-np.maximum(t - d, 0) * 220), 0) for d in (0, 0.011, 0.022))
    e = e + np.where(t >= 0.03, np.exp(-np.maximum(t - 0.03, 0) * 14), 0) * 0.7
    return norm(bp(noise(0.35), 900, 3800) * e)


def snare():
    t = tt(0.25)
    return norm(np.sin(2 * np.pi * 185 * t) * np.exp(-t * 28) * 0.6 + bp(noise(0.25), 1500, 9000) * np.exp(-t * 19))


def hat(open_=False):
    d = 0.3 if open_ else 0.06
    return norm(hp(noise(d), 7500, 4) * np.exp(-tt(d) * (11 if open_ else 90)))


def shaker():
    t = tt(0.09)
    return norm(bp(noise(0.09), 5000, 12000) * np.minimum(t / 0.015, 1) * np.exp(-t * 40))


def taiko():
    t = tt(0.9)
    body = np.sin(phase(70 + 50 * np.exp(-t * 20))) * np.exp(-t * 4.5)
    skin = bp(noise(0.9), 120, 900) * np.exp(-t * 18) * 0.5
    return norm(np.tanh(1.5 * (body + skin)))


def crash(d=2.0):
    t = tt(d)
    return norm(hp(noise(d), 3800, 4) * np.exp(-t * 2.3) + bp(noise(d), 6000, 14000) * np.exp(-t * 4) * 0.5)


def impact(d=1.8):
    t = tt(d)
    sub = np.sin(phase(30 + 70 * np.exp(-t * 9))) * np.exp(-t * 2.6)
    return norm(np.tanh(1.4 * (sub + lp(noise(d), 260) * np.exp(-t * 14) * 3)))


def gong(d=3.5):
    t = tt(d)
    parts = ((1, 1, 1.0), (1.48, .6, 1.4), (2.03, .5, 1.8), (2.72, .35, 2.4), (3.6, .2, 3.2), (4.9, .12, 4.0))
    x = sum(a * np.sin(2 * np.pi * 92 * r * t * (1 + .002 * np.sin(2 * np.pi * 3 * t))) * np.exp(-t * dcy) for r, a, dcy in parts)
    return norm(x * env(len(t), .004, .2))


def pluck_bass(f, d):
    t = tt(d)
    x = sum(np.sin(2 * np.pi * f * k * t) * np.exp(-t * (5 + 3 * k)) / k for k in range(1, 7))
    return np.tanh(1.4 * x) * env(len(t), .003, .03)


def sub(f, d):
    t = tt(d)
    return np.sin(2 * np.pi * f * t) * env(len(t), .01, .05) * (0.7 + 0.3 * np.exp(-t * 4))


def pizz(f, d=.35):
    t = tt(d)
    x = sum(np.sin(2 * np.pi * f * k * t) * np.exp(-t * (14 + 6 * k)) / k ** 1.2 for k in range(1, 9))
    body = bp(noise(d), f * .9, min(f * 3, 20000)) * np.exp(-t * 60) * .15
    return (x + body) * env(len(t), .001, .02)


def celesta(f, d=.9):
    t = tt(d)
    parts = ((1, 1, 4), (2, .35, 6), (3.01, .15, 9), (4.2, .08, 14))
    return sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * dcy) for r, a, dcy in parts) * env(len(t), .001, .03)


def organ(f, d):
    t = tt(d)
    x = sum(a * np.sin(2 * np.pi * f * r * t) for r, a in ((.5, .45), (1, 1), (1.5, .55), (2, .5), (3, .3), (4, .25)))
    return x * (1 + .12 * np.sin(2 * np.pi * 6.2 * t)) * env(len(t), .006, .05)


def choir(midis, d, att=.25, rel=.4):
    """Detuned saw pad through two vowel formants ('ah')."""
    t = tt(d + rel)
    x = np.zeros(len(t))
    for m in midis:
        for c in (-8, 0, 8):
            f = mtof(m) * 2 ** (c / 1200)
            x += sum(np.sin(2 * np.pi * f * k * t + rng.uniform(0, 6.28)) / k for k in range(1, 20) if f * k < 9000)
    x = bp(x, 600, 900, 1) * 1.2 + bp(x, 1050, 1400, 1)
    e = np.minimum(t / att, 1) * np.where(t > d, np.exp(-(t - d) * 5 / rel), 1)
    return norm(x * e * (1 + .05 * np.sin(2 * np.pi * 5 * t)))


def theremin(notes, d):
    """Gliding sine lead with wide vibrato; notes = [(start, midi, len)] in seconds."""
    t = tt(d)
    f = np.full(len(t), mtof(notes[0][1]))
    a = np.zeros(len(t))
    for s, m, ln in notes:
        i0, i1 = int(s * SR), min(len(t), int((s + ln) * SR))
        f[i0:] = mtof(m)
        a[i0:i1] = 1
    k = int(0.06 * SR)
    f = np.convolve(np.pad(f, (k, 0), mode="edge"), np.ones(k) / k, mode="valid")[: len(t)]   # portamento
    a = np.convolve(a, np.ones(int(.03 * SR)) / int(.03 * SR), mode="same")
    f = f * (1 + .012 * np.sin(2 * np.pi * 6 * t))
    x = np.sin(phase(f)) + .12 * np.sin(2 * phase(f))
    return x * a


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
    return sweep_noise(d, f0, f1, 0.5) * u ** 2.2 + np.sin(phase(160 * 8 ** u)) * u ** 2.6 * 0.3


def page_flip():
    t = tt(0.22)
    flutter = 0.55 + 0.45 * np.sin(2 * np.pi * 34 * t)
    return norm(bp(noise(0.22), 1200, 7000) * np.sin(np.pi * np.clip(t / 0.22, 0, 1)) * flutter)


def stamp():
    t = tt(0.3)
    thud = np.sin(phase(90 + 120 * np.exp(-t * 40))) * np.exp(-t * 18)
    slap = bp(noise(0.3), 300, 3000) * np.exp(-t * 60) * .6
    return norm(thud + slap)


def card_flick():
    t = tt(0.12)
    return norm(bp(noise(0.12), 2000, 9000) * np.exp(-t * 45) + np.sin(2 * np.pi * 900 * t) * np.exp(-t * 80) * .3)


def click():
    t = tt(0.05)
    return norm(bp(noise(0.05), 1500, 9000) * np.exp(-t * 400) + np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 300) * 0.4)


def reverb_ir(rt60=2.2):
    t = tt(rt60)
    ir = np.stack([lp(noise(rt60), 5000) for _ in range(2)], 1) * np.exp(-6.9 * t / rt60)[:, None]
    ir = np.concatenate([np.zeros((int(0.02 * SR), 2)), ir])
    return ir / np.sqrt(np.sum(ir ** 2) / 2)


# ───────────── harmony & melody (D minor: i – VI – VII – V) ─────────────
CHORDS = [(38, [62, 65, 69, 74]), (34, [58, 62, 65, 70]), (36, [60, 64, 67, 72]), (33, [61, 64, 69, 73])]
A = [(0, 74, .5), (.5, 77, .5), (1, 81, .5), (1.5, 86, 1), (2.5, 85, .5), (3, 81, 1),
     (4, 82, .5), (4.5, 81, .5), (5, 79, .5), (5.5, 77, .5), (6, 79, 1), (7, 74, 1),
     (8, 76, .5), (8.5, 79, .5), (9, 84, .5), (9.5, 88, 1), (10.5, 86, .5), (11, 84, 1),
     (12, 85, .5), (12.5, 88, .5), (13, 81, .5), (13.5, 79, .5), (14, 77, .5), (14.5, 76, .5), (15, 73, 1)]
B = A[:18] + [(12, 76, .5), (12.5, 77, .5), (13, 79, .5), (13.5, 81, .5), (14, 82, .5), (14.5, 85, .5), (15, 88, 1)]


def chord_of(b):
    return CHORDS[(b - 2) % 4]


def melody(b, phrase):
    j = (b - 2) % 4
    return [(s - 4 * j, m, d) for s, m, d in phrase if 4 * j <= s < 4 * (j + 1)]


def add_kick(t, g):
    put(drums, t, kick(), g)
    kick_times.append(t)


def section(b):
    """0: light, 1: fuller, 2: spooky theremin, 3: climax."""
    fi = (b - 2) // 2
    return 0 if fi < 4 else 1 if fi < 8 else 2 if fi < 12 else 3


def groove_bar(b, sec, phrase):
    t0 = b * BAR
    at = lambda beat: t0 + beat * BEAT  # noqa: E731
    root, voicing = chord_of(b)
    # bass: pizzicato upright on beats + offbeat bounce, sub underneath
    for beat, iv in ((0, 0), (1.5, 12), (2, 7), (3.5, 12)):
        put(music, at(beat), pluck_bass(mtof(root + iv), BEAT * .9), .5)
    put(music, t0, sub(mtof(root), BAR * .95), .28)
    # pizzicato ostinato (chord tones, 8ths)
    for i, m in enumerate([voicing[k] for k in (0, 2, 1, 2, 3, 2, 1, 2)]):
        put(music, at(i / 2), pizz(mtof(m)), .17 if sec < 3 else .2, (-.35, .35)[i % 2], send=.25)
    # drums
    for beat in (0, 2) if sec < 3 else (0, 1, 2, 3):
        add_kick(at(beat), .75)
    for beat in (1, 3):
        put(drums, at(beat), clap(), .32, send=.25)
        if sec >= 1:
            put(drums, at(beat), snare(), .14)
    for i in range(8 if sec == 0 else 16):
        put(drums, at(i / (2 if sec == 0 else 4)), shaker() if sec == 0 else hat(), .06 if i % 2 else .09, .3)
    if sec >= 1:
        put(drums, at(3.5), hat(True), .08, -.3)
    if sec >= 1:
        put(music, t0, organ(mtof(voicing[0] - 12), BAR * .98), .07, send=.3)
        put(music, t0, choir(voicing, BAR * .98), .12 if sec < 3 else .16, send=.4)
    if sec == 3 and (b - 2) % 2 == 0:
        put(drums, t0, taiko(), .45, send=.3)
    # lead
    notes = melody(b, phrase)
    if sec == 2:
        put(music, t0, theremin([(s * BEAT, m - 12, d * BEAT) for s, m, d in notes], BAR + .3), .2, .1, send=.45)
        for s, m, d in notes[::2]:
            put(music, at(s), celesta(mtof(m + 12)), .05, -.3, send=.4)
    else:
        for s, m, d in notes:
            put(music, at(s), celesta(mtof(m), max(.5, d * BEAT * 1.6)), .2 if sec < 3 else .17, .15, send=.4)
            if sec == 3:
                put(music, at(s), organ(mtof(m - 12), d * BEAT * .95), .07, -.15, send=.3)


def build():
    # ── intro (two bars) ──
    put(music, 0, choir([62, 65, 69], INTRO - .1, 1.2, .2), .22, send=.5)
    put(music, 0, sub(mtof(38), INTRO), .2)
    for k in range(7):
        put(sfx, .1 + k * .09 + .1, card_flick(), .18, -.6 + k * .2)
    for i, m in enumerate([62, 65, 69, 74, 77, 81, 86, 85, 81, 77, 81, 86]):
        put(music, .55 + i * .05 + .12, pizz(mtof(m)), .22, -.5 + i * .09, send=.3)
    put(sfx, .55, impact(1.2), .35)
    put(sfx, 1.5, whoosh(.6, 500, 5000, -.5, .5), .2)
    put(sfx, 2.5, pop(900), .25)
    put(sfx, 2.5, celesta(mtof(86), 1.2), .15, send=.5)
    put(sfx, INTRO - 1.9, riser(1.9), .26)
    for i in range(8):
        put(drums, INTRO - 1 + i * BEAT / 4, snare(), .08 + .03 * i)

    # ── films: two bars each ──
    phrases = [A, B]
    for b in range(2, 2 + 2 * len(FILMS)):
        groove_bar(b, section(b), phrases[((b - 2) // 4) % 2])
    for sec_start in (4, 8, 12):  # section changes get a crash
        t = INTRO + sec_start * PER
        put(sfx, t, crash(), .22, send=.3)
        put(sfx, t - 1.0, riser(1.0, 600, 8000), .14)
    put(sfx, INTRO, impact(), .55)
    put(sfx, INTRO, crash(), .25, send=.3)

    prev_day = 1
    for i, f in enumerate(FILMS):
        t0 = INTRO + i * PER
        put(sfx, t0 - .06, whoosh(.45, 500, 4200, .8, -.4, .45), .17)
        put(sfx, t0 + .3, taiko() if i % 4 == 0 else pluck_bass(mtof(45), .3), .12)
        for k, m in enumerate((93, 98, 100, 105)):
            put(sfx, t0 + .4 + k * .07, celesta(mtof(m), .5), .03, .2 * k - .3, send=.4)
        if i == 0 or f["day"] != prev_day:
            put(sfx, t0 + .1, page_flip(), .22, .2)
            put(sfx, t0 + .42, stamp(), .3)
            # calendar marker sliding across the days
            steps = f["day"] - prev_day
            for s in range(1, steps + 1):
                u = s / steps
                lo, hi = 0.0, 1.0
                for _ in range(30):
                    mid = (lo + hi) / 2
                    v = 4 * mid ** 3 if mid < .5 else 1 - (-2 * mid + 2) ** 3 / 2
                    lo, hi = (mid, hi) if v < u else (lo, mid)
                put(sfx, t0 + .1 + .6 * hi, tick(2000 + 60 * s), .045, -.6 + .04 * f["day"])
        put(sfx, t0 + .52, pop(700 + 40 * (i % 6)), .14, .4)
        put(sfx, t0 + .78, pop(1100), .06, .3)
        prev_day = f["day"]

    # ── outro ──
    for b in (len(FILMS) * 2 + 2, len(FILMS) * 2 + 3):
        groove_bar(b, 3, B)
    put(sfx, OUTRO, whoosh(.6, 300, 5000), .25)
    for k in range(len(FILMS)):
        put(sfx, OUTRO + .25 + k * .045 + .08, pop(mtof(74 + [0, 3, 5, 7, 10, 12][k % 6])), .08, -.6 + (k % 9) * .15)
    put(sfx, OUTRO + 1.2, impact(1.0), .25)
    put(sfx, OUTRO + 2.2, pop(800), .22)
    put(sfx, OUTRO + 3.3, click(), .5)
    for k, m in enumerate((90, 95)):
        put(sfx, OUTRO + 3.35 + k * .12, celesta(mtof(m), 1.5), .16, .2, send=.4)
    tf = OUTRO + 2 * BAR
    put(music, tf, choir([62, 65, 69, 74], 1.6, .02, .5), .3, send=.5)
    put(music, tf, organ(mtof(50), 1.7), .18, send=.4)
    put(music, tf, sub(mtof(38), 1.7), .35)
    put(sfx, tf, gong(), .35, send=.4)
    add_kick(tf, 1.0)
    put(drums, tf, taiko(), .5, send=.3)
    put(sfx, tf, crash(2.2), .22, send=.3)


def mixdown():
    duck = np.ones(N)
    shape = 1 - 0.45 * np.exp(-tt(0.3) / 0.08)
    for tk in kick_times:
        i = int(tk * SR)
        n = min(len(shape), N - i)
        duck[i:i + n] = np.minimum(duck[i:i + n], shape[:n])
    dry = drums.x + music.x * duck[:, None] + sfx.x
    wet = np.stack([signal.fftconvolve(verb.x[:, c], reverb_ir()[:, c])[:N] for c in range(2)], 1)
    mix = hp(dry + 0.32 * wet, 30)
    mix = norm(mix, 1.15)
    mix = np.tanh(mix) / np.tanh(1.15)  # gentle soft-clip; keeps the hits punchy
    t = np.arange(N) / SR
    mix *= np.clip((DUR - t) / 0.8, 0, 1)[:, None] ** 1.5
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
