"""Tests for the FFmpeg client. `_run` is patched so no real ffmpeg is needed."""
import json
import subprocess
from unittest.mock import patch, MagicMock

import pytest

from apps.workers.video_editor import ffmpeg_client as fc


def _capture_run():
    """Patch fc._run and return the mock so tests can inspect the built command."""
    return patch.object(fc, "_run", return_value=MagicMock(stdout="", stderr="", returncode=0))


def _cmd_of(mock_run) -> list[str]:
    return mock_run.call_args.args[0]


# --------------------------------------------------------------------------- #
# probe
# --------------------------------------------------------------------------- #
def test_probe_parses_ffprobe_json():
    probe_json = json.dumps({
        "format": {"duration": "12.5", "size": "1048576"},
        "streams": [
            {"codec_type": "video", "codec_name": "h264", "width": 1920, "height": 1080, "r_frame_rate": "30000/1001"},
            {"codec_type": "audio", "codec_name": "aac"},
        ],
    })
    with patch.object(fc, "_run", return_value=MagicMock(stdout=probe_json)):
        meta = fc.probe("in.mp4")
    assert meta["duration"] == 12.5
    assert meta["size_bytes"] == 1048576
    assert meta["width"] == 1920 and meta["height"] == 1080
    assert meta["video_codec"] == "h264"
    assert meta["audio_codec"] == "aac"
    assert meta["has_audio"] is True
    assert round(meta["fps"], 2) == 29.97


def test_probe_no_audio_stream():
    probe_json = json.dumps({
        "format": {"duration": "5.0", "size": "100"},
        "streams": [{"codec_type": "video", "codec_name": "h264", "width": 640, "height": 480, "r_frame_rate": "25/1"}],
    })
    with patch.object(fc, "_run", return_value=MagicMock(stdout=probe_json)):
        meta = fc.probe("in.mp4")
    assert meta["has_audio"] is False
    assert meta["audio_codec"] is None
    assert meta["fps"] == 25.0


# --------------------------------------------------------------------------- #
# editing operations
# --------------------------------------------------------------------------- #
def test_trim_default_reencodes_seeking_after_input():
    with _capture_run() as run:
        out = fc.trim("in.mp4", "out.mp4", start=5, duration=10)
    cmd = _cmd_of(run)
    assert out == "out.mp4"
    # accurate cut: seek after -i, re-encode
    assert cmd.index("-i") < cmd.index("-ss")
    assert "-t" in cmd and cmd[cmd.index("-t") + 1] == "10"
    assert "libx264" in cmd


def test_trim_end_computes_duration():
    with _capture_run() as run:
        fc.trim("in.mp4", "out.mp4", start=2, end=7)
    cmd = _cmd_of(run)
    assert cmd[cmd.index("-t") + 1] == "5.0"


def test_trim_fast_seeks_before_input():
    with _capture_run() as run:
        fc.trim("in.mp4", "out.mp4", start=5, duration=3, fast=True)
    cmd = _cmd_of(run)
    # fast seek: -ss must come before -i
    assert cmd.index("-ss") < cmd.index("-i")
    assert "copy" in cmd


def test_trim_fast_omits_ss_at_zero_start():
    with _capture_run() as run:
        fc.trim("in.mp4", "out.mp4", start=0, duration=3, fast=True)
    cmd = _cmd_of(run)
    # `-ss 0` before input can drop all packets, so it must be omitted
    assert "-ss" not in cmd
    assert "copy" in cmd


def test_resize_default_height_is_even_auto():
    with _capture_run() as run:
        fc.resize("in.mp4", "out.mp4", width=1280)
    cmd = _cmd_of(run)
    assert "scale=1280:-2" in cmd


def test_crop_builds_filter():
    with _capture_run() as run:
        fc.crop("in.mp4", "out.mp4", width=200, height=100, x=10, y=20)
    assert "crop=200:100:10:20" in _cmd_of(run)


def test_convert_no_codecs_copies():
    with _capture_run() as run:
        fc.convert("in.mov", "out.mp4")
    cmd = _cmd_of(run)
    assert "-c" in cmd and "copy" in cmd


def test_convert_with_codecs():
    with _capture_run() as run:
        fc.convert("in.mov", "out.webm", video_codec="libvpx-vp9", audio_codec="libopus")
    cmd = _cmd_of(run)
    assert "libvpx-vp9" in cmd and "libopus" in cmd


def test_compress_uses_crf_and_preset():
    with _capture_run() as run:
        fc.compress("in.mp4", "out.mp4", crf=30, preset="slow")
    cmd = _cmd_of(run)
    assert cmd[cmd.index("-crf") + 1] == "30"
    assert cmd[cmd.index("-preset") + 1] == "slow"


def test_watermark_bottom_right_position():
    with _capture_run() as run:
        fc.add_watermark("in.mp4", "logo.png", "out.mp4", position="bottom-right", margin=15)
    cmd = _cmd_of(run)
    fx = cmd[cmd.index("-filter_complex") + 1]
    assert fx == "overlay=W-w-15:H-h-15"


def test_watermark_rejects_bad_position():
    with pytest.raises(ValueError):
        fc.add_watermark("in.mp4", "logo.png", "out.mp4", position="middle")


def test_subtitles_burn_uses_vf():
    with _capture_run() as run:
        fc.add_subtitles("in.mp4", "subs.srt", "out.mp4", burn=True)
    cmd = _cmd_of(run)
    vf = cmd[cmd.index("-vf") + 1]
    assert vf.startswith("subtitles=")


def test_subtitles_soft_mux():
    with _capture_run() as run:
        fc.add_subtitles("in.mp4", "subs.srt", "out.mp4", burn=False)
    cmd = _cmd_of(run)
    assert "mov_text" in cmd
    assert "-vf" not in cmd


def test_extract_audio():
    with _capture_run() as run:
        fc.extract_audio("in.mp4", "out.mp3")
    cmd = _cmd_of(run)
    assert "-vn" in cmd and "libmp3lame" in cmd


def test_extract_thumbnail():
    with _capture_run() as run:
        fc.extract_thumbnail("in.mp4", "thumb.jpg", timestamp=3)
    cmd = _cmd_of(run)
    assert cmd[cmd.index("-frames:v") + 1] == "1"


def test_speed_with_audio_maps_both_streams():
    with _capture_run() as run, patch.object(fc, "has_audio", return_value=True):
        fc.set_speed("in.mp4", "out.mp4", factor=2.0)
    cmd = _cmd_of(run)
    fx = cmd[cmd.index("-filter_complex") + 1]
    assert "setpts=0.500000*PTS" in fx
    assert "atempo=2.0" in fx
    assert cmd.count("-map") == 2


def test_speed_without_audio_disables_audio():
    with _capture_run() as run, patch.object(fc, "has_audio", return_value=False):
        fc.set_speed("in.mp4", "out.mp4", factor=0.5)
    cmd = _cmd_of(run)
    assert "-an" in cmd


def test_speed_rejects_non_positive():
    with pytest.raises(ValueError):
        fc.set_speed("in.mp4", "out.mp4", factor=0)


def test_atempo_chain_beyond_range():
    # 4x needs two chained atempo=2.0 filters (each capped at 2.0)
    chain = fc._atempo_chain(4.0)
    assert chain.count("atempo=2.0") == 2


# --------------------------------------------------------------------------- #
# concat & generation (list-file based)
# --------------------------------------------------------------------------- #
def test_concat_writes_list_and_runs():
    with _capture_run() as run:
        fc.concat(["a.mp4", "b.mp4"], "out.mp4")
    cmd = _cmd_of(run)
    assert "-f" in cmd and "concat" in cmd
    assert "libx264" in cmd


def test_concat_requires_inputs():
    with pytest.raises(ValueError):
        fc.concat([], "out.mp4")


def test_generate_slideshow_with_audio():
    with _capture_run() as run:
        fc.generate_slideshow(["1.jpg", "2.jpg"], "out.mp4", audio_path="song.mp3", resolution=(1280, 720), fps=24)
    cmd = _cmd_of(run)
    vf = cmd[cmd.index("-vf") + 1]
    assert "scale=1280:720" in vf and "fps=24" in vf
    assert "-shortest" in cmd
    assert "song.mp3" in cmd


def test_generate_slideshow_requires_images():
    with pytest.raises(ValueError):
        fc.generate_slideshow([], "out.mp4")


def test_add_text_escapes_and_builds_drawtext():
    with _capture_run() as run:
        fc.add_text("in.mp4", "out.mp4", text="Hi: there")
    cmd = _cmd_of(run)
    vf = cmd[cmd.index("-vf") + 1]
    assert vf.startswith("drawtext=")
    assert "Hi\\: there" in vf


# --------------------------------------------------------------------------- #
# _run error handling
# --------------------------------------------------------------------------- #
def test_run_raises_ffmpeg_error_on_nonzero():
    completed = subprocess.CompletedProcess(args=["ffmpeg"], returncode=1, stdout="", stderr="boom")
    with patch("subprocess.run", return_value=completed):
        with pytest.raises(fc.FFmpegError, match="boom"):
            fc._run(["ffmpeg", "-version"])


def test_run_raises_not_found_when_binary_missing():
    with patch("subprocess.run", side_effect=FileNotFoundError()):
        with pytest.raises(fc.FFmpegNotFoundError):
            fc._run(["ffmpeg", "-version"])
