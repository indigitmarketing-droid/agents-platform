# Video Editor Agent

Server-side video editing and generation for the platform, powered by **FFmpeg**.

Like the other workers it is event-driven: it polls the Supabase `events` table
for events targeted at `video_editor`, runs the requested FFmpeg operation, and
emits result events. The pure FFmpeg wrappers live in
[`ffmpeg_client.py`](./ffmpeg_client.py) and can also be imported and used
directly as a library.

## Requirements

The `ffmpeg` and `ffprobe` binaries must be on `PATH` (override with the
`FFMPEG_BIN` / `FFPROBE_BIN` env vars). On Debian/Ubuntu:

```bash
apt-get install -y ffmpeg
```

Relevant env vars (see `.env.example`):

- `VIDEO_OUTPUT_DIR` — where outputs are written when a job omits `output_path`
  (default `/tmp/agents-video-output`).

## Running

```bash
python -m apps.workers.video_editor.main
```

## Events

### Consumed

**`video.edit_requested`** — run one operation on existing media.

```jsonc
{
  "job_id": "clip-7",              // optional; falls back to the event id
  "operation": "trim",             // required
  "params": { "start": 0, "duration": 10 },
  "input_path": "/media/in.mp4",   // single-input operations
  "input_paths": ["/a.mp4", "/b.mp4"], // concat only
  "output_path": "/media/out.mp4", // optional; auto-generated if omitted
  "reply_to": "builder"            // optional; target_agent of video.ready
}
```

**`video.generate_requested`** — render a video from a template.

```jsonc
{
  "job_id": "promo-42",
  "template": "slideshow",         // currently the only template
  "images": ["/img/1.jpg", "/img/2.jpg"],  // required
  "audio": "/audio/track.mp3",     // optional soundtrack
  "options": { "duration_per_image": 3.0, "resolution": [1080, 1920], "fps": 30 },
  "output_path": "/media/promo.mp4",
  "reply_to": "builder"
}
```

### Emitted

- **`video.processing_started`** — `{ job_id }`
- **`video.ready`** — `{ job_id, output_path, operation | template, metadata }`
  where `metadata` is the ffprobe summary (`duration`, `width`, `height`,
  `fps`, `video_codec`, `audio_codec`, `has_audio`, `size_bytes`).

Invalid payloads and FFmpeg failures raise `FatalError`, so the base agent
routes them to the dead-letter queue instead of retrying a deterministic
failure.

## Operations (`params`)

| operation           | params                                                        |
| ------------------- | ------------------------------------------------------------- |
| `trim`              | `start`, `duration` \| `end`, `fast` (keyframe copy)          |
| `concat`            | *(uses `input_paths`)*                                        |
| `crop`              | `width`, `height`, `x`, `y`                                   |
| `resize`            | `width`, `height` (omit to keep aspect ratio)                 |
| `convert`           | `video_codec`, `audio_codec` (omit both to stream-copy)       |
| `compress`          | `crf` (default 28), `preset`                                  |
| `speed`             | `factor` (>1 faster, <1 slower)                               |
| `watermark`         | `watermark_path`, `position`, `margin`                        |
| `subtitles`         | `subtitles_path`, `burn` (default true)                       |
| `extract_audio`     | `codec` (default `libmp3lame`)                                |
| `extract_thumbnail` | `timestamp` (seconds or `HH:MM:SS`)                           |
| `text`              | `text`, `fontsize`, `fontcolor`                               |

`watermark` positions: `top-left`, `top-right`, `bottom-left`,
`bottom-right`, `center`.

> **Note on `trim`:** the default is a frame-accurate re-encode. Pass
> `"fast": true` for a much faster stream copy that snaps to the nearest
> keyframe (start/duration may be approximate on long-GOP sources).

## Library usage

```python
from apps.workers.video_editor import ffmpeg_client as fc

fc.generate_slideshow(["1.jpg", "2.jpg"], "promo.mp4",
                      audio_path="track.mp3", resolution=(1080, 1920))
fc.trim("promo.mp4", "cut.mp4", start=0, duration=5)
meta = fc.probe("cut.mp4")   # -> {"duration": 5.0, "width": 1080, ...}
```

## Tests

```bash
python -m pytest apps/workers/video_editor/tests/
```

Tests patch `subprocess` / `ffmpeg_client`, so they run without the FFmpeg
binaries installed.
