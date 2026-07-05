#!/usr/bin/env python3
"""
mute_scatti.py — silence specified time ranges in a video's audio.

Applies a sample-precise mute with short cosine ramps at each edge (so the
mute itself never clicks), then remuxes with the untouched video stream.
Operates in the FILE's own timeline, so run it on the final render.

Usage:
    python mute_scatti.py IN.mp4 OUT.mp4 6.78-6.97 7.39-7.44 [--ramp 0.006]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile

import numpy as np
from scipy.io import wavfile


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("infile")
    ap.add_argument("outfile")
    ap.add_argument("regions", nargs="+", help="ranges like 6.78-6.97 (seconds)")
    ap.add_argument("--ramp", type=float, default=0.006, help="edge ramp (s)")
    a = ap.parse_args()

    ranges = []
    for r in a.regions:
        lo, hi = (float(v) for v in r.split("-"))
        ranges.append((lo, hi))

    with tempfile.TemporaryDirectory() as tmp:
        wav_in, wav_out = f"{tmp}/in.wav", f"{tmp}/out.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", a.infile, "-vn",
                        "-ac", "2", "-ar", "48000", "-c:a", "pcm_s16le", wav_in],
                       check=True)
        sr, y = wavfile.read(wav_in)
        y = y.astype(np.float32)
        n = y.shape[0]
        t = np.arange(n) / sr
        env = np.ones(n, dtype=np.float32)
        for lo, hi in ranges:
            g = np.ones(n, dtype=np.float32)
            g[(t >= lo) & (t <= hi)] = 0.0
            m = (t >= lo - a.ramp) & (t < lo)
            g[m] = 0.5 * (1 + np.cos(np.pi * (t[m] - (lo - a.ramp)) / a.ramp))
            m = (t > hi) & (t <= hi + a.ramp)
            g[m] = 0.5 * (1 + np.cos(np.pi * (1 - (t[m] - hi) / a.ramp)))
            env *= g
        out = (y * env[:, None]).clip(-32768, 32767).astype(np.int16)
        wavfile.write(wav_out, sr, out)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", a.infile,
                        "-i", wav_out, "-map", "0:v", "-map", "1:a",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                        a.outfile], check=True)
    print(f"Muted {len(ranges)} region(s) -> {a.outfile}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
