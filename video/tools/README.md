# audio_scan.py — objective audio-defect detector

Scans an audio/video file for the glitches that read as an audible "scatto"
and **classifies** each one, so a fix can be picked in one shot instead of by
trial and error.

```bash
python tools/audio_scan.py public/easyDent.mp4              # full scan
python tools/audio_scan.py public/easyDent.mp4 --from 6.4 --to 7.6   # a window
python tools/audio_scan.py public/easyDent.mp4 --json       # machine-readable
```

It prints a one-line **VERDICT** (e.g. "no clicks — any scatto is a jump-cut
splice") plus a ranked table of events with a recommended fix (and, where
applicable, the exact `ffmpeg -af` snippet).

## What it detects

| type | what it is | how it's told apart from normal speech |
|------|------------|----------------------------------------|
| `click` | isolated broadband impulse (<6 ms) | prediction-error spike vs a band-limited estimate |
| `pop` | short **low-frequency** thump (mic bump) | same, but low treble |
| `burst` | 6–45 ms broadband transient at a splice | high error **and** louder than the local speech |
| `dropout` | mid-phrase fall to near-silence | quiet run flanked by speech on both sides |
| `clipping` | samples pinned at full scale | `|x| > 0.985` |

The guiding principle: a real recording is band-limited, so genuine sound
changes over ≥15–20 ms. Only **abruptness** (a few-ms change) marks a glitch —
never absolute loudness or brightness, which normal speech varies freely.
That's why fricatives and loud syllables are *not* flagged.

Requires `ffmpeg`, `numpy`, `scipy`.
