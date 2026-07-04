"""Tests for the VideoEditorAgent event handling (ffmpeg_client patched out)."""
from unittest.mock import MagicMock, patch

import pytest

from apps.workers.video_editor.main import VideoEditorAgent
from apps.workers.video_editor.ffmpeg_client import FFmpegError


SAMPLE_META = {"duration": 10.0, "width": 1920, "height": 1080, "has_audio": True}


def make_supabase_client():
    client = MagicMock()
    update_chain = MagicMock()
    update_chain.eq.return_value = update_chain
    update_chain.execute = MagicMock()

    def table_factory(_name):
        t = MagicMock()
        t.update.return_value = update_chain
        t.insert.return_value = MagicMock(execute=MagicMock(return_value=MagicMock(data=[{"id": "x"}])))
        return t

    client.table.side_effect = table_factory
    return client


@pytest.fixture
def agent():
    return VideoEditorAgent(supabase_client=make_supabase_client())


@pytest.mark.asyncio
async def test_ignores_unknown_event_types(agent):
    result = await agent.handle_event({"id": "e1", "type": "scraping.lead_found", "payload": {}})
    assert result == []


@pytest.mark.asyncio
async def test_edit_trim_emits_started_and_ready(agent):
    event = {
        "id": "e1",
        "type": "video.edit_requested",
        "payload": {
            "job_id": "job-1",
            "operation": "trim",
            "params": {"start": 2, "duration": 5},
            "input_path": "/in/clip.mp4",
            "output_path": "/out/clip_trim.mp4",
        },
    }
    with patch("apps.workers.video_editor.main.ffmpeg_client") as fc:
        fc.trim.return_value = "/out/clip_trim.mp4"
        fc.probe.return_value = SAMPLE_META
        events = await agent.handle_event(event)

    types = [e["type"] for e in events]
    assert types == ["video.processing_started", "video.ready"]
    ready = events[1]
    assert ready["payload"]["job_id"] == "job-1"
    assert ready["payload"]["output_path"] == "/out/clip_trim.mp4"
    assert ready["payload"]["operation"] == "trim"
    assert ready["payload"]["metadata"] == SAMPLE_META
    fc.trim.assert_called_once()
    _, kwargs = fc.trim.call_args
    assert kwargs["start"] == 2 and kwargs["duration"] == 5


@pytest.mark.asyncio
async def test_edit_ready_targets_reply_to(agent):
    event = {
        "id": "e1",
        "type": "video.edit_requested",
        "payload": {
            "job_id": "job-1",
            "operation": "compress",
            "input_path": "/in/clip.mp4",
            "output_path": "/out/clip.mp4",
            "reply_to": "builder",
        },
    }
    with patch("apps.workers.video_editor.main.ffmpeg_client") as fc:
        fc.compress.return_value = "/out/clip.mp4"
        fc.probe.return_value = SAMPLE_META
        events = await agent.handle_event(event)
    ready = next(e for e in events if e["type"] == "video.ready")
    assert ready["target_agent"] == "builder"


@pytest.mark.asyncio
async def test_concat_uses_input_paths(agent):
    event = {
        "id": "e1",
        "type": "video.edit_requested",
        "payload": {
            "job_id": "job-1",
            "operation": "concat",
            "input_paths": ["/in/a.mp4", "/in/b.mp4"],
            "output_path": "/out/joined.mp4",
        },
    }
    with patch("apps.workers.video_editor.main.ffmpeg_client") as fc:
        fc.concat.return_value = "/out/joined.mp4"
        fc.probe.return_value = SAMPLE_META
        await agent.handle_event(event)
    fc.concat.assert_called_once_with(["/in/a.mp4", "/in/b.mp4"], "/out/joined.mp4")


@pytest.mark.asyncio
async def test_generate_slideshow_emits_ready(agent):
    event = {
        "id": "e1",
        "type": "video.generate_requested",
        "payload": {
            "job_id": "promo-1",
            "template": "slideshow",
            "images": ["/img/1.jpg", "/img/2.jpg"],
            "audio": "/audio/track.mp3",
            "options": {"duration_per_image": 4, "resolution": [1080, 1920], "fps": 30},
            "output_path": "/out/promo.mp4",
        },
    }
    with patch("apps.workers.video_editor.main.ffmpeg_client") as fc:
        fc.generate_slideshow.return_value = "/out/promo.mp4"
        fc.probe.return_value = SAMPLE_META
        events = await agent.handle_event(event)

    assert [e["type"] for e in events] == ["video.processing_started", "video.ready"]
    ready = events[1]
    assert ready["payload"]["template"] == "slideshow"
    _, kwargs = fc.generate_slideshow.call_args
    assert kwargs["resolution"] == (1080, 1920)
    assert kwargs["audio_path"] == "/audio/track.mp3"


@pytest.mark.asyncio
async def test_unknown_operation_raises_fatal(agent):
    from packages.agent_framework import FatalError
    event = {
        "id": "e1",
        "type": "video.edit_requested",
        "payload": {"job_id": "j", "operation": "explode", "input_path": "/in.mp4"},
    }
    with patch("apps.workers.video_editor.main.ffmpeg_client"):
        with pytest.raises(FatalError, match="Invalid video job"):
            await agent.handle_event(event)


@pytest.mark.asyncio
async def test_missing_input_raises_fatal(agent):
    from packages.agent_framework import FatalError
    event = {
        "id": "e1",
        "type": "video.edit_requested",
        "payload": {"job_id": "j", "operation": "trim"},
    }
    with patch("apps.workers.video_editor.main.ffmpeg_client"):
        with pytest.raises(FatalError, match="Invalid video job"):
            await agent.handle_event(event)


@pytest.mark.asyncio
async def test_ffmpeg_error_raises_fatal(agent):
    event = {
        "id": "e1",
        "type": "video.edit_requested",
        "payload": {"job_id": "j", "operation": "trim", "input_path": "/in.mp4", "output_path": "/out.mp4"},
    }
    with patch("apps.workers.video_editor.main.ffmpeg_client") as fc:
        fc.trim.side_effect = FFmpegError("bad input")
        from packages.agent_framework import FatalError
        with pytest.raises(FatalError, match="FFmpeg failed"):
            await agent.handle_event(event)


@pytest.mark.asyncio
async def test_default_output_path_generated(tmp_path):
    agent = VideoEditorAgent(supabase_client=make_supabase_client())
    agent._output_dir = str(tmp_path)
    event = {
        "id": "e1",
        "type": "video.edit_requested",
        "payload": {"job_id": "job-9", "operation": "trim", "input_path": "/in.mp4"},
    }
    with patch("apps.workers.video_editor.main.ffmpeg_client") as fc:
        fc.trim.side_effect = lambda inp, out, **kw: out
        fc.probe.return_value = SAMPLE_META
        events = await agent.handle_event(event)
    out = events[1]["payload"]["output_path"]
    assert out == str(tmp_path / "job-9_trim.mp4")
