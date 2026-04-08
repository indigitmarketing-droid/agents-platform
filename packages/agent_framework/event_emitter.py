from datetime import datetime, timezone


class EventEmitter:
    def __init__(self, client, agent_id: str):
        self._client = client
        self._agent_id = agent_id

    def emit(self, event_type: str, payload: dict, target_agent: str | None = None) -> dict:
        row = {
            "type": event_type,
            "source_agent": self._agent_id,
            "target_agent": target_agent,
            "payload": payload,
            "status": "pending",
            "retry_count": 0,
        }
        result = self._client.table("events").insert(row).execute()
        return result.data[0] if result.data else {}

    def send_heartbeat(self) -> None:
        now = datetime.now(timezone.utc).isoformat()
        (
            self._client.table("agents")
            .update({"last_heartbeat": now, "status": "idle"})
            .eq("id", self._agent_id)
            .execute()
        )

    def set_status(self, status: str) -> None:
        (
            self._client.table("agents")
            .update({"status": status})
            .eq("id", self._agent_id)
            .execute()
        )
