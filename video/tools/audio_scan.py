#!/usr/bin/env python3
"""
audio_scan.py — objective audio-defect detector.

Scans an audio/video file for the kinds of glitches that read as an audible
"scatto" and classifies each one, so a fix can be chosen in one shot instead
of by trial and error.

Detectors (all psychoacoustically motivated):
  - click      : isolated broadband impulse, very short (<~5ms), high treble.
  - pop/thump  : short, loud, LOW-frequency transient (mic bump / handling).
  - loud_burst : sustained span markedly louder than the local median level.
  - dropout    : mid-phrase fall to near-silence flanked by speech.
  - seam       : abrupt timbre change (spectral-centroid / HF-ratio step) with
                 no matching level spike — an edit seam between takes.
  - clipping   : samples pinned at full scale.

Each event is scored for *audibility* (a defect in a quiet spot is more
audible than one masked by loud speech) and paired with a concrete fix.

Usage:
    python audio_scan.py <file> [--from S] [--to S] [--json] [--top N]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

import numpy as np
from scipy.ndimage import uniform_filter1d
from scipy.signal import stft

SR = 48000


def load_audio(path: str, t0: float | None, t1: float | None) -> np.ndarray:
    """Decode to mono float32 [-1,1] at SR via ffmpeg."""
    cmd = ["ffmpeg", "-v", "error"]
    if t0 is not None:
        cmd += ["-ss", str(t0)]
    if t1 is not None:
        cmd += ["-to", str(t1)]
    cmd += ["-i", path, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0


def db(x: np.ndarray) -> np.ndarray:
    return 20.0 * np.log10(np.maximum(np.abs(x), 1e-9))


def analyze(x: np.ndarray, base: float) -> list[dict]:
    n = len(x)
    if n < SR // 10:
        return []

    # ---- STFT features (frame ~43ms, hop ~5.3ms) --------------------------
    nper, hop = 2048, 256
    f, t, Z = stft(x, fs=SR, nperseg=nper, noverlap=nper - hop, boundary=None)
    mag = np.abs(Z)                      # [freq, frame]
    tsec = base + t                      # absolute time per frame
    energy = mag.sum(axis=0) + 1e-9
    hf_ratio = mag[f >= 5000].sum(axis=0) / energy              # treble fraction
    frame_rms = np.sqrt((mag ** 2).sum(axis=0))
    rdb = db(frame_rms)
    floor = np.percentile(rdb, 5)        # noise floor estimate
    peak_lvl = np.percentile(rdb, 95)
    active = rdb > (floor + 12)          # frames carrying real signal

    events: list[dict] = []

    def audibility(ts: float) -> float:
        """0..1: a defect is MORE audible when its neighbourhood is quiet
        (little masking). 1 = fully exposed, ~0.2 = buried under loud speech."""
        i = int(np.clip((ts - base) * SR / hop, 0, len(rdb) - 1))
        w = max(3, int(0.25 * SR / hop))
        neigh = np.concatenate([rdb[max(0, i - w):i], rdb[i + 1:i + w + 1]])
        loud = np.median(neigh) if neigh.size else floor
        masking = np.clip((loud - floor) / (peak_lvl - floor + 1e-9), 0, 1)
        return float(np.clip(1.0 - 0.85 * masking, 0.1, 1.0))

    # The single most reliable glitch signature is ABRUPTNESS: a real recording
    # is band-limited, so genuine sound changes over >=15-20ms. A click, pop or
    # splice changes in a few ms. Every detector below keys on that, never on
    # absolute loudness/brightness (which normal speech varies freely).

    # ---- 1) clicks, pops & short broadband bursts ------------------------
    # Prediction error vs a band-limited estimate of each sample. Genuine
    # recordings are band-limited, so a concentrated cluster of high error is
    # a splice/click/burst. We separate it from a fricative (also broadband)
    # by requiring it to be markedly LOUDER than the surrounding speech —
    # fricatives sit at speech level, glitches jump above it.
    pred = np.empty_like(x)
    pred[1:-1] = 0.5 * (x[:-2] + x[2:])
    pred[0], pred[-1] = x[0], x[-1]
    err = np.abs(x - pred)
    loc = np.sqrt(uniform_filter1d(x * x, size=int(0.004 * SR)) + 1e-9)
    score = err / (loc + 1e-6)
    density = uniform_filter1d((score > 3.0).astype(np.float32),
                               size=int(0.008 * SR))
    for s, e in _runs(density > 0.33):
        dur = (e - s) / SR
        if dur > 0.045:                                 # too long -> fricative
            continue
        c = (s + e) // 2
        ts = base + c / SR
        j = int(np.clip(c / hop, 0, len(hf_ratio) - 1))
        span_lvl = float(db(np.max(np.abs(x[s:e + 1]))))
        w = int(0.25 * SR)
        neigh = np.concatenate([x[max(0, s - w):s], x[e + 1:e + 1 + w]])
        loc_lvl = float(np.median(db(neigh))) if neigh.size else floor
        excess = span_lvl - loc_lvl
        sharp = float(np.max(score[s:e + 1]))
        if dur <= 0.006:
            typ = "pop" if hf_ratio[j] < 0.12 else "click"
        elif excess >= 6.0:
            typ = "burst"                               # loud broadband splice
        else:
            continue                                    # fricative
        events.append({
            "t": round(ts, 4), "t_end": round(base + e / SR, 4), "type": typ,
            "metric": {"sharpness": round(sharp, 1),
                       "excess_db": round(excess, 1),
                       "dur_ms": round(dur * 1000),
                       "hf_ratio": round(float(hf_ratio[j]), 3)},
            "audib": round(audibility(ts), 2),
        })

    # ---- 3) dropout: mid-phrase fall to near-silence ---------------------
    quiet = rdb < (floor + 8)
    for s, e in _runs(quiet):
        dur = t[e] - t[s]
        if not (0.04 <= dur <= 0.4):
            continue
        w = max(2, int(0.12 * SR / hop))
        if active[max(0, s - w):s].any() and active[e + 1:e + 1 + w].any():
            ts = float(tsec[s])
            events.append({
                "t": round(ts, 4), "t_end": round(float(tsec[e]), 4),
                "type": "dropout",
                "metric": {"dur_ms": round(float(dur * 1000)),
                           "floor_db": round(float(np.min(rdb[s:e + 1])), 1)},
                "audib": round(audibility(ts), 2),
            })

    # ---- 4) clipping ------------------------------------------------------
    for s, e in _runs(np.abs(x) > 0.985):
        if e - s >= 3:
            ts = base + s / SR
            events.append({
                "t": round(ts, 4), "t_end": round(base + e / SR, 4),
                "type": "clipping", "metric": {"samples": int(e - s)},
                "audib": 1.0,
            })

    # de-duplicate: keep the strongest event within any 25ms cluster
    events = _dedupe(events, 0.025)
    for ev in events:
        ev["severity"] = round(_severity(ev), 3)
        ev["fix"] = _fix(ev)
    events.sort(key=lambda e: (-e["severity"], e["t"]))
    return events


def _dedupe(events: list[dict], win: float) -> list[dict]:
    rank = {"clipping": 5, "click": 4, "pop": 4, "burst": 3,
            "level_step": 2, "dropout": 1}
    events = sorted(events, key=lambda e: e["t"])
    kept: list[dict] = []
    for ev in events:
        hit = next((k for k in kept if abs(k["t"] - ev["t"]) <= win), None)
        if hit is None:
            kept.append(ev)
        elif rank[ev["type"]] > rank[hit["type"]]:
            kept[kept.index(hit)] = ev
    return kept


def _runs(mask: np.ndarray):
    """Yield (start, end) inclusive index ranges of True runs."""
    idx = np.flatnonzero(mask)
    if idx.size == 0:
        return
    brk = np.flatnonzero(np.diff(idx) > 1)
    starts = np.concatenate([[0], brk + 1])
    ends = np.concatenate([brk, [len(idx) - 1]])
    for s, e in zip(starts, ends):
        yield int(idx[s]), int(idx[e])


def _severity(ev: dict) -> float:
    m = ev["metric"]
    t = ev["type"]
    if t in ("click", "pop"):
        base = 0.9 * min(1.0, m["sharpness"] / 14.0)
    elif t == "clipping":
        base = 0.85
    elif t == "burst":
        base = min(0.9, 0.35 + m["excess_db"] / 22.0)
    elif t == "dropout":
        base = min(0.75, 0.25 + m["dur_ms"] / 320.0)
    else:
        base = 0.4
    return float(np.clip(base * ev["audib"], 0, 1))


def _fix(ev: dict) -> dict:
    t, te = ev["t"], ev["t_end"]
    c = (t + te) / 2
    if ev["type"] == "click":
        return {"action": "notch",
                "ffmpeg": _notch(c, 0.012, 0.85),
                "note": "smooth Gaussian volume notch on the impulse"}
    if ev["type"] == "pop":
        return {"action": "highpass+notch",
                "ffmpeg": f"highpass=f=90, {_notch(c, 0.02, 0.7)}",
                "note": "remove sub-bass thump + tame the transient"}
    if ev["type"] in ("burst", "level_step"):
        return {"action": "notch",
                "ffmpeg": _notch(c, 0.014, 0.6),
                "note": "smooth the abrupt level step at the seam"}
    if ev["type"] == "dropout":
        return {"action": "fill_or_trim",
                "ffmpeg": None,
                "note": "bridge the gap (low ambient bed) or trim a/v together"}
    if ev["type"] == "seam":
        return {"action": "crossfade",
                "ffmpeg": None,
                "note": "short spectral crossfade / EQ-match across the seam"}
    if ev["type"] == "clipping":
        return {"action": "declip", "ffmpeg": "adeclip",
                "note": "restore clipped samples"}
    return {"action": "review", "ffmpeg": None, "note": ""}


def _notch(center: float, sigma: float, depth: float) -> str:
    return (f"volume=volume='1-{depth}*exp(-pow((t-{center:.3f})/{sigma}\\,2))'"
            ":eval=frame")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("file")
    ap.add_argument("--from", dest="t0", type=float, default=None)
    ap.add_argument("--to", dest="t1", type=float, default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--top", type=int, default=12)
    a = ap.parse_args()

    x = load_audio(a.file, a.t0, a.t1)
    base = a.t0 or 0.0
    events = analyze(x, base)[: a.top]

    if a.json:
        print(json.dumps(events, indent=2))
        return 0

    # one-line verdict so the fix is obvious at a glance
    counts: dict[str, int] = {}
    for ev in events:
        counts[ev["type"]] = counts.get(ev["type"], 0) + 1
    impulsive = sum(counts.get(k, 0) for k in ("click", "pop", "clipping"))
    parts = ", ".join(f"{v}×{k}" for k, v in sorted(counts.items())) or "none"
    if impulsive == 0:
        verdict = ("No clicks/pops/clipping. Clean band-limited speech — any "
                   "'scatto' is a jump-cut splice (abrupt level/timbre change "
                   "at an edit), not a removable click.")
    else:
        verdict = f"{impulsive} impulsive defect(s) found — removable."
    print(f"VERDICT: {verdict}")
    print(f"detected: {parts}\n")

    if not events:
        print("No significant audio defects detected.")
        return 0
    print(f"{'#':>2}  {'time':>8}  {'type':<10} {'sev':>4} {'aud':>4}  detail / fix")
    print("-" * 92)
    for i, ev in enumerate(events, 1):
        span = f"{ev['t']:.3f}" + (f"-{ev['t_end']:.3f}" if ev["t_end"] > ev["t"] else "")
        detail = ", ".join(f"{k}={v}" for k, v in ev["metric"].items())
        print(f"{i:>2}  {span:>8}  {ev['type']:<10} {ev['severity']:>4.2f} "
              f"{ev['audib']:>4.2f}  {detail}")
        print(f"{'':>30}↳ {ev['fix']['action']}: {ev['fix']['note']}")
        if ev["fix"]["ffmpeg"]:
            print(f"{'':>30}  af: {ev['fix']['ffmpeg']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
