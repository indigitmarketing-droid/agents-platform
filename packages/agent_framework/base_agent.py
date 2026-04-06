import asyncio
import logging
from abc import ABC, abstractmethod
from packages.agent_framework.event_emitter import EventEmitter
from packages.agent_framework.retry import RetryableError, FatalError, should_retry

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    MAX_RETRIES = 3
    HEARTBEAT_INTERVAL = 30
    RETRY_CHECK_INTERVAL = 60
    RETRY_STALE_SECONDS = 120

    def __init__(self, agent_id: str, supabase_client):
        self.agent_id = agent_id
        self._client = supabase_client
        self._emitter = EventEmitter(client=supabase_client, agent_id=agent_id)
        self._running = False

    @abstractmethod
    async def handle_event(self, event: dict) -> list[dict]:
        ...

    async def process_event(self, event: dict) -> None:
        event_id = event.get("id", "unknown")
        event_type = event.get("type", "unknown")
        logger.info(f"[{self.agent_id}] Processing event {event_id}: {event_type}")

        try:
            await self._emitter.set_status("working")
            await (
                self._client.table("events")
                .update({"status": "processing"})
                .eq("id", event_id)
                .execute()
            )
            new_events = await self.handle_event(event)
            for new_event in new_events:
                await self._emitter.emit(
                    event_type=new_event["type"],
                    payload=new_event["payload"],
                    target_agent=new_event.get("target_agent"),
                )
            await (
                self._client.table("events")
                .update({"status": "completed", "processed_at": "now()"})
                .eq("id", event_id)
                .execute()
            )
            await self._emitter.set_status("idle")
            logger.info(f"[{self.agent_id}] Completed event {event_id}")
        except RetryableError as e:
            retry_count = event.get("retry_count", 0) + 1
            if should_retry(retry_count, self.MAX_RETRIES):
                logger.warning(f"[{self.agent_id}] Retryable error on {event_id} (attempt {retry_count}): {e}")
                await (
                    self._client.table("events")
                    .update({"status": "pending", "retry_count": retry_count, "error": str(e)})
                    .eq("id", event_id)
                    .execute()
                )
            else:
                logger.error(f"[{self.agent_id}] Max retries reached for {event_id}: {e}")
                await self._mark_dead_letter(event_id, str(e))
            await self._emitter.set_status("idle")
        except (FatalError, Exception) as e:
            logger.error(f"[{self.agent_id}] Fatal error on {event_id}: {e}")
            await self._mark_dead_letter(event_id, str(e))
            await self._emitter.set_status("error")

    async def _mark_dead_letter(self, event_id: str, error: str) -> None:
        await (
            self._client.table("events")
            .update({"status": "dead_letter", "error": error})
            .eq("id", event_id)
            .execute()
        )
        await self._emitter.emit(
            event_type="system.error",
            payload={"agent_id": self.agent_id, "error": error, "event_id": event_id},
        )

    async def _heartbeat_loop(self) -> None:
        while self._running:
            try:
                await self._emitter.send_heartbeat()
            except Exception as e:
                logger.error(f"[{self.agent_id}] Heartbeat failed: {e}")
            await asyncio.sleep(self.HEARTBEAT_INTERVAL)

    async def _poll_events(self) -> None:
        while self._running:
            try:
                result = await (
                    self._client.table("events")
                    .select("*")
                    .eq("target_agent", self.agent_id)
                    .eq("status", "pending")
                    .order("created_at")
                    .limit(10)
                    .execute()
                )
                for event in result.data or []:
                    await self.process_event(event)
            except Exception as e:
                logger.error(f"[{self.agent_id}] Poll error: {e}")
            await asyncio.sleep(2)

    async def start(self) -> None:
        self._running = True
        logger.info(f"[{self.agent_id}] Starting agent")
        await self._emitter.set_status("idle")
        await self._emitter.send_heartbeat()
        await self._emitter.emit(
            event_type="system.agent_online",
            payload={"agent_id": self.agent_id},
        )
        await asyncio.gather(
            self._heartbeat_loop(),
            self._poll_events(),
        )

    async def stop(self) -> None:
        self._running = False
        await self._emitter.set_status("offline")
        logger.info(f"[{self.agent_id}] Agent stopped")
