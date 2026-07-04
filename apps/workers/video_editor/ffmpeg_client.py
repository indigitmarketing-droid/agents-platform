"""FFmpeg-based video editing API.

Thin, pure wrappers around the ``ffmpeg`` / ``ffprobe`` binaries. Every editing
function takes explicit input/output paths, builds an argument list, shells out
via :func:`_run`, and returns the output path. No global state, no I/O beyond
subprocess + temp files, so each function is easy to unit-test by patching
:func:`_run`.

Two families of operations:

* **Editing existing videos** – trim, concat, crop, resize, convert, compress,
  set_speed, add_watermark, add_subtitles, extract_audio, extract_thumbnail.
* **Generating from a template** – generate_slideshow (build a promo video from
  a set of images + optional soundtrack) and add_text (burn-in captions/titles).

The binaries are resolved from the ``FFMPEG_BIN`` / ``FFPROBE_BIN`` env vars so
deployments can pin a specific build; they default to ``ffmpeg`` / ``ffprobe``
on ``PATH``.
"""
import json
import logging
import os
import subprocess
import tempfile
from fractions import Fraction

logger = logging.getLogger(__name__)

FFMPEG_BIN = os.environ.get("FFMPEG_BIN", "ffmpeg")
FFPROBE_BIN = os.environ.get("FFPROBE_BIN", "ffprobe")

DEFAULT_TIMEOUT = 600  # seconds; rendering can be slow

_POSITIONS = {
    "top-left": "{m}:{m}",
    "top-right": "W-w-{m}:{m}",
    "bottom-left": "{m}:H-h-{m}",
    "bottom-right": "W-w-{m}:H-h-{m}",
    "center": "(W-w)/2:(H-h)/2",
}


class FFmpegError(Exception):
    """ffmpeg/ffprobe exited non-zero or produced unusable output."""


class FFmpegNotFoundError(FFmpegError):
    """The ffmpeg/ffprobe binary is not installed / not on PATH."""


def _run(cmd: list[str], timeout: int = DEFAULT_TIMEOUT) -> subprocess.CompletedProcess:
    """Run a command, raising :class:`FFmpegError` on failure."""
    logger.debug("Running: %s", " ".join(cmd))
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as e:
        raise FFmpegNotFoundError(
            f"Binary not found: {cmd[0]!r}. Install ffmpeg (e.g. `apt-get install ffmpeg`)."
        ) from e
    except subprocess.TimeoutExpired as e:
        raise FFmpegError(f"Command timed out after {timeout}s: {cmd[0]}") from e
    if proc.returncode != 0:
        raise FFmpegError(
            f"{cmd[0]} exited {proc.returncode}: {proc.stderr.strip()[-800:]}"
        )
    return proc


# --------------------------------------------------------------------------- #
# Inspection
# --------------------------------------------------------------------------- #
def probe(path: str) -> dict:
    """Return normalized metadata for ``path`` using ffprobe."""
    proc = _run(
        [
            FFPROBE_BIN,
            "-v", "error",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(path),
        ],
        timeout=60,
    )
    try:
        raw = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as e:
        raise FFmpegError(f"ffprobe returned invalid JSON for {path}: {e}") from e

    streams = raw.get("streams", [])
    fmt = raw.get("format", {})
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)

    return {
        "duration": _to_float(fmt.get("duration")),
        "size_bytes": _to_int(fmt.get("size")),
        "width": video.get("width") if video else None,
        "height": video.get("height") if video else None,
        "fps": _parse_fps(video.get("r_frame_rate")) if video else None,
        "video_codec": video.get("codec_name") if video else None,
        "audio_codec": audio.get("codec_name") if audio else None,
        "has_audio": audio is not None,
    }


def has_audio(path: str) -> bool:
    """True if ``path`` contains at least one audio stream."""
    return probe(path)["has_audio"]


# --------------------------------------------------------------------------- #
# Editing existing videos
# --------------------------------------------------------------------------- #
def trim(
    input_path: str,
    output_path: str,
    *,
    start: float = 0,
    duration: float | None = None,
    end: float | None = None,
    fast: bool = False,
) -> str:
    """Cut a segment starting at ``start`` (seconds).

    Provide either ``duration`` or ``end`` (both in seconds). By default the cut
    is re-encoded so it is frame-accurate for any input. ``fast=True`` instead
    stream-copies: much faster, but the cut snaps to the nearest keyframe (the
    real start/duration may differ on long-GOP sources).
    """
    if duration is None and end is not None:
        duration = float(end) - float(start)
    cmd = [FFMPEG_BIN, "-y"]
    if fast:
        # seek before -i for a fast (keyframe-aligned) cut. `-ss 0` before the
        # input can drop all packets on some containers, so omit it at start 0.
        if not _is_zero(start):
            cmd += ["-ss", str(start)]
        cmd += ["-i", str(input_path)]
        if duration is not None:
            cmd += ["-t", str(duration)]
        cmd += ["-c", "copy"]
    else:
        # seek after -i and re-encode for a frame-accurate cut
        cmd += ["-i", str(input_path), "-ss", str(start)]
        if duration is not None:
            cmd += ["-t", str(duration)]
        cmd += ["-c:v", "libx264", "-c:a", "aac"]
    cmd += [str(output_path)]
    _run(cmd)
    return str(output_path)


def concat(input_paths: list[str], output_path: str) -> str:
    """Concatenate videos end-to-end (re-encoded to H.264/AAC).

    Uses the concat demuxer. Inputs should share resolution / fps — normalize
    mismatched clips first with :func:`resize` / :func:`convert`.
    """
    if not input_paths:
        raise ValueError("concat requires at least one input path")
    list_path = _write_concat_list(input_paths)
    try:
        cmd = [
            FFMPEG_BIN, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_path,
            "-c:v", "libx264",
            "-c:a", "aac",
            "-movflags", "+faststart",
            str(output_path),
        ]
        _run(cmd)
    finally:
        _cleanup(list_path)
    return str(output_path)


def crop(input_path: str, output_path: str, *, width: int, height: int, x: int = 0, y: int = 0) -> str:
    """Crop a ``width`` x ``height`` rectangle at offset ``(x, y)``."""
    cmd = [
        FFMPEG_BIN, "-y",
        "-i", str(input_path),
        "-vf", f"crop={int(width)}:{int(height)}:{int(x)}:{int(y)}",
        "-c:a", "copy",
        str(output_path),
    ]
    _run(cmd)
    return str(output_path)


def resize(input_path: str, output_path: str, *, width: int, height: int | None = None) -> str:
    """Scale to ``width``. ``height=None`` preserves aspect ratio (even dims)."""
    h = -2 if height is None else int(height)
    cmd = [
        FFMPEG_BIN, "-y",
        "-i", str(input_path),
        "-vf", f"scale={int(width)}:{h}",
        "-c:a", "copy",
        str(output_path),
    ]
    _run(cmd)
    return str(output_path)


def convert(
    input_path: str,
    output_path: str,
    *,
    video_codec: str | None = None,
    audio_codec: str | None = None,
) -> str:
    """Convert container/codecs. With no codecs given, stream-copies."""
    cmd = [FFMPEG_BIN, "-y", "-i", str(input_path)]
    if video_codec is None and audio_codec is None:
        cmd += ["-c", "copy"]
    else:
        cmd += ["-c:v", video_codec or "copy", "-c:a", audio_codec or "copy"]
    cmd += [str(output_path)]
    _run(cmd)
    return str(output_path)


def compress(input_path: str, output_path: str, *, crf: int = 28, preset: str = "medium") -> str:
    """Re-encode with H.264 CRF to reduce file size (higher crf = smaller)."""
    cmd = [
        FFMPEG_BIN, "-y",
        "-i", str(input_path),
        "-c:v", "libx264",
        "-crf", str(int(crf)),
        "-preset", preset,
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        str(output_path),
    ]
    _run(cmd)
    return str(output_path)


def set_speed(input_path: str, output_path: str, *, factor: float) -> str:
    """Change playback speed. ``factor`` > 1 speeds up, < 1 slows down."""
    if factor <= 0:
        raise ValueError("speed factor must be > 0")
    video_filter = f"[0:v]setpts={1 / factor:.6f}*PTS[v]"
    if has_audio(input_path):
        audio_filter = f"[0:a]{_atempo_chain(factor)}[a]"
        cmd = [
            FFMPEG_BIN, "-y",
            "-i", str(input_path),
            "-filter_complex", f"{video_filter};{audio_filter}",
            "-map", "[v]", "-map", "[a]",
            str(output_path),
        ]
    else:
        cmd = [
            FFMPEG_BIN, "-y",
            "-i", str(input_path),
            "-filter_complex", video_filter,
            "-map", "[v]", "-an",
            str(output_path),
        ]
    _run(cmd)
    return str(output_path)


def add_watermark(
    input_path: str,
    watermark_path: str,
    output_path: str,
    *,
    position: str = "bottom-right",
    margin: int = 10,
) -> str:
    """Overlay an image (logo/watermark) at a named ``position``."""
    if position not in _POSITIONS:
        raise ValueError(f"position must be one of {sorted(_POSITIONS)}")
    xy = _POSITIONS[position].format(m=int(margin))
    cmd = [
        FFMPEG_BIN, "-y",
        "-i", str(input_path),
        "-i", str(watermark_path),
        "-filter_complex", f"overlay={xy}",
        str(output_path),
    ]
    _run(cmd)
    return str(output_path)


def add_subtitles(
    input_path: str,
    subtitles_path: str,
    output_path: str,
    *,
    burn: bool = True,
) -> str:
    """Add subtitles. ``burn=True`` renders them into the picture; otherwise
    they are muxed as a soft (toggleable) subtitle track."""
    if burn:
        escaped = _escape_filter_path(str(subtitles_path))
        cmd = [
            FFMPEG_BIN, "-y",
            "-i", str(input_path),
            "-vf", f"subtitles={escaped}",
            "-c:a", "copy",
            str(output_path),
        ]
    else:
        cmd = [
            FFMPEG_BIN, "-y",
            "-i", str(input_path),
            "-i", str(subtitles_path),
            "-c", "copy",
            "-c:s", "mov_text",
            str(output_path),
        ]
    _run(cmd)
    return str(output_path)


def extract_audio(input_path: str, output_path: str, *, codec: str = "libmp3lame") -> str:
    """Extract the audio track to ``output_path`` (default MP3)."""
    cmd = [
        FFMPEG_BIN, "-y",
        "-i", str(input_path),
        "-vn",
        "-acodec", codec,
        str(output_path),
    ]
    _run(cmd)
    return str(output_path)


def extract_thumbnail(input_path: str, output_path: str, *, timestamp: str | float = 1.0) -> str:
    """Grab a single frame at ``timestamp`` (seconds or HH:MM:SS) as an image."""
    cmd = [
        FFMPEG_BIN, "-y",
        "-ss", str(timestamp),
        "-i", str(input_path),
        "-frames:v", "1",
        "-q:v", "2",
        str(output_path),
    ]
    _run(cmd)
    return str(output_path)


# --------------------------------------------------------------------------- #
# Generation from a template
# --------------------------------------------------------------------------- #
def generate_slideshow(
    image_paths: list[str],
    output_path: str,
    *,
    duration_per_image: float = 3.0,
    audio_path: str | None = None,
    resolution: tuple[int, int] = (1920, 1080),
    fps: int = 30,
) -> str:
    """Build a slideshow video from a list of images, scaled/padded to
    ``resolution`` and optionally set to a soundtrack.

    Useful as an FFmpeg-native "template" renderer, e.g. an automatic promo
    reel from a business's photos.
    """
    if not image_paths:
        raise ValueError("generate_slideshow requires at least one image")
    w, h = int(resolution[0]), int(resolution[1])
    list_path = _write_image_list(image_paths, duration_per_image)
    try:
        vf = (
            f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,"
            f"format=yuv420p,fps={int(fps)}"
        )
        cmd = [FFMPEG_BIN, "-y", "-f", "concat", "-safe", "0", "-i", list_path]
        if audio_path:
            cmd += ["-i", str(audio_path), "-shortest"]
        cmd += ["-vf", vf, "-c:v", "libx264", "-movflags", "+faststart"]
        if audio_path:
            cmd += ["-c:a", "aac", "-b:a", "192k"]
        cmd += [str(output_path)]
        _run(cmd)
    finally:
        _cleanup(list_path)
    return str(output_path)


def add_text(
    input_path: str,
    output_path: str,
    *,
    text: str,
    fontsize: int = 48,
    fontcolor: str = "white",
    x: str = "(w-text_w)/2",
    y: str = "h-100",
    box: bool = True,
    fontfile: str | None = None,
) -> str:
    """Burn a text overlay (title/caption) onto the video via drawtext."""
    parts = [
        f"text='{_escape_drawtext(text)}'",
        f"fontsize={int(fontsize)}",
        f"fontcolor={fontcolor}",
        f"x={x}",
        f"y={y}",
    ]
    if box:
        parts += ["box=1", "boxcolor=black@0.5", "boxborderw=12"]
    if fontfile:
        parts.append(f"fontfile={_escape_filter_path(fontfile)}")
    cmd = [
        FFMPEG_BIN, "-y",
        "-i", str(input_path),
        "-vf", "drawtext=" + ":".join(parts),
        "-c:a", "copy",
        str(output_path),
    ]
    _run(cmd)
    return str(output_path)


# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #
def _atempo_chain(factor: float) -> str:
    """Build a chain of atempo filters (each valid only in [0.5, 2.0])."""
    parts: list[str] = []
    f = float(factor)
    while f > 2.0:
        parts.append("atempo=2.0")
        f /= 2.0
    while f < 0.5:
        parts.append("atempo=0.5")
        f /= 0.5
    parts.append(f"atempo={f:.6f}")
    return ",".join(parts)


def _write_concat_list(input_paths: list[str]) -> str:
    fd, path = tempfile.mkstemp(suffix=".txt", prefix="concat_")
    with os.fdopen(fd, "w") as f:
        for p in input_paths:
            f.write(f"file '{os.path.abspath(str(p))}'\n")
    return path


def _write_image_list(image_paths: list[str], duration_per_image: float) -> str:
    fd, path = tempfile.mkstemp(suffix=".txt", prefix="slideshow_")
    with os.fdopen(fd, "w") as f:
        for p in image_paths:
            abspath = os.path.abspath(str(p))
            f.write(f"file '{abspath}'\n")
            f.write(f"duration {float(duration_per_image)}\n")
        # concat demuxer drops the last image's duration unless it is repeated
        f.write(f"file '{os.path.abspath(str(image_paths[-1]))}'\n")
    return path


def _cleanup(path: str) -> None:
    try:
        os.remove(path)
    except OSError:
        pass


def _escape_drawtext(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace("%", "\\%")
    )


def _escape_filter_path(path: str) -> str:
    # Escape characters special to the filtergraph parser.
    return path.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def _is_zero(value) -> bool:
    try:
        return float(value) == 0
    except (TypeError, ValueError):
        return False


def _to_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_fps(rate: str | None) -> float | None:
    if not rate:
        return None
    try:
        return float(Fraction(rate)) if rate != "0/0" else None
    except (ValueError, ZeroDivisionError):
        return None
