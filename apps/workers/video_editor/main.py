"""Video Editor Agent.

Event-driven worker that performs server-side video editing/generation with
FFmpeg. It consumes two event types targeted at ``video_editor``:

* ``video.edit_requested``     – run one editing operation on existing media.
* ``video.generate_requested`` – render a video from a template (slideshow).

For each job it emits ``video.processing_started`` and, on success,
``video.ready`` carrying the output path and probed metadata. Invalid payloads
and FFmpeg failures raise :class:`FatalError` so the base agent routes them to
the dead-letter queue rather than retrying a deterministic failure.
"""
import asyncio
import logging
import os

from dotenv import load_dotenv

from packages.agent_framework import BaseAgent, FatalError
from packages.agent_framework.supabase_client import create_supabase_client

from apps.workers.video_editor import ffmpeg_client
from apps.workers.video_editor.ffmpeg_client import FFmpegError

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_DIR = "/tmp/agents-video-output"

# operation -> default output file extension
_EDIT_EXTENSIONS = {
    "extract_audio": ".mp3",
    "extract_thumbnail": ".jpg",
}


class VideoEditorAgent(BaseAgent):
    """Edits and generates videos in response to platform events."""

    HANDLED = ("video.edit_requested", "video.generate_requested")

    def __init__(self, **kwargs):
        super().__init__(agent_id="video_editor", **kwargs)
        self._output_dir = os.environ.get("VIDEO_OUTPUT_DIR", DEFAULT_OUTPUT_DIR)

    async def handle_event(self, event: dict) -> list[dict]:
        event_type = event.get("type")
        if event_type not in self.HANDLED:
            logger.debug(f"Ignoring event type: {event_type}")
            return []

        payload = event.get("payload", {})
        job_id = payload.get("job_id") or event.get("id", "unknown")
        reply_to = payload.get("reply_to")

        new_events: list[dict] = [{
            "type": "video.processing_started",
            "target_agent": None,
            "payload": {"job_id": job_id},
        }]

        try:
            # Offload the blocking FFmpeg work so the heartbeat loop keeps running.
            if event_type == "video.edit_requested":
                result = await asyncio.to_thread(self._run_edit, job_id, payload)
            else:
                result = await asyncio.to_thread(self._run_generate, job_id, payload)
        except (KeyError, ValueError) as e:
            raise FatalError(f"Invalid video job {job_id}: {e}")
        except FFmpegError as e:
            raise FatalError(f"FFmpeg failed for job {job_id}: {e}")

        logger.info(f"Video job {job_id} ready: {result['output_path']}")
        new_events.append({
            "type": "video.ready",
            "target_agent": reply_to,
            "payload": {"job_id": job_id, **result},
        })
        return new_events

    # ------------------------------------------------------------------ #
    # Editing existing media
    # ------------------------------------------------------------------ #
    def _run_edit(self, job_id: str, payload: dict) -> dict:
        operation = payload["operation"]
        params = payload.get("params", {})
        ext = _EDIT_EXTENSIONS.get(operation, ".mp4")
        out = self._resolve_output(payload, job_id, operation, ext)

        if operation == "trim":
            ffmpeg_client.trim(
                self._require_input(payload), out,
                start=params.get("start", 0),
                duration=params.get("duration"),
                end=params.get("end"),
                fast=params.get("fast", False),
            )
        elif operation == "concat":
            ffmpeg_client.concat(self._require_inputs(payload), out)
        elif operation == "crop":
            ffmpeg_client.crop(
                self._require_input(payload), out,
                width=params["width"], height=params["height"],
                x=params.get("x", 0), y=params.get("y", 0),
            )
        elif operation == "resize":
            ffmpeg_client.resize(
                self._require_input(payload), out,
                width=params["width"], height=params.get("height"),
            )
        elif operation == "convert":
            ffmpeg_client.convert(
                self._require_input(payload), out,
                video_codec=params.get("video_codec"),
                audio_codec=params.get("audio_codec"),
            )
        elif operation == "compress":
            ffmpeg_client.compress(
                self._require_input(payload), out,
                crf=params.get("crf", 28), preset=params.get("preset", "medium"),
            )
        elif operation == "speed":
            ffmpeg_client.set_speed(
                self._require_input(payload), out, factor=params["factor"],
            )
        elif operation == "watermark":
            ffmpeg_client.add_watermark(
                self._require_input(payload), params["watermark_path"], out,
                position=params.get("position", "bottom-right"),
                margin=params.get("margin", 10),
            )
        elif operation == "subtitles":
            ffmpeg_client.add_subtitles(
                self._require_input(payload), params["subtitles_path"], out,
                burn=params.get("burn", True),
            )
        elif operation == "extract_audio":
            ffmpeg_client.extract_audio(
                self._require_input(payload), out,
                codec=params.get("codec", "libmp3lame"),
            )
        elif operation == "extract_thumbnail":
            ffmpeg_client.extract_thumbnail(
                self._require_input(payload), out,
                timestamp=params.get("timestamp", 1.0),
            )
        elif operation == "text":
            ffmpeg_client.add_text(
                self._require_input(payload), out,
                text=params["text"],
                fontsize=params.get("fontsize", 48),
                fontcolor=params.get("fontcolor", "white"),
            )
        else:
            raise ValueError(f"Unknown operation: {operation!r}")

        return {"operation": operation, "output_path": out, "metadata": ffmpeg_client.probe(out)}

    # ------------------------------------------------------------------ #
    # Generation from a template
    # ------------------------------------------------------------------ #
    def _run_generate(self, job_id: str, payload: dict) -> dict:
        template = payload.get("template", "slideshow")
        if template != "slideshow":
            raise ValueError(f"Unknown template: {template!r}")

        images = payload.get("images")
        if not images:
            raise ValueError("template 'slideshow' requires a non-empty 'images' list")

        options = payload.get("options", {})
        out = self._resolve_output(payload, job_id, "generate", ".mp4")
        resolution = options.get("resolution", [1920, 1080])

        ffmpeg_client.generate_slideshow(
            images, out,
            duration_per_image=options.get("duration_per_image", 3.0),
            audio_path=payload.get("audio"),
            resolution=(resolution[0], resolution[1]),
            fps=options.get("fps", 30),
        )
        return {"template": template, "output_path": out, "metadata": ffmpeg_client.probe(out)}

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _require_input(payload: dict) -> str:
        path = payload.get("input_path")
        if not path:
            raise ValueError("missing 'input_path'")
        return path

    @staticmethod
    def _require_inputs(payload: dict) -> list[str]:
        paths = payload.get("input_paths")
        if not paths:
            raise ValueError("missing 'input_paths'")
        return paths

    def _resolve_output(self, payload: dict, job_id: str, operation: str, default_ext: str) -> str:
        out = payload.get("output_path")
        if not out:
            out = os.path.join(self._output_dir, f"{job_id}_{operation}{default_ext}")
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        return out


async def main():
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    client = create_supabase_client()
    agent = VideoEditorAgent(supabase_client=client)
    try:
        await agent.start()
    except KeyboardInterrupt:
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())
