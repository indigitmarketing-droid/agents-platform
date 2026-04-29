"""HTTP client wrapper for ElevenLabs Conversational AI."""
import logging
import httpx

logger = logging.getLogger(__name__)


class ElevenLabsError(Exception):
    """Raised when ElevenLabs API returns error or unexpected response."""


class ElevenLabsClient:
    BASE_URL = "https://api.elevenlabs.io/v1"

    def __init__(self, api_key: str, timeout_seconds: float = 30.0):
        self._api_key = api_key
        self._timeout = timeout_seconds

    def trigger_outbound_call(
        self,
        agent_id: str,
        agent_phone_number_id: str,
        to_number: str,
    ) -> dict:
        """Trigger outbound call via ElevenLabs+Twilio integration."""
        headers = {"xi-api-key": self._api_key, "Content-Type": "application/json"}
        body = {
            "agent_id": agent_id,
            "agent_phone_number_id": agent_phone_number_id,
            "to_number": to_number,
        }
        try:
            response = httpx.post(
                f"{self.BASE_URL}/convai/twilio/outbound_call",
                json=body,
                headers=headers,
                timeout=self._timeout,
            )
        except httpx.HTTPError as e:
            raise ElevenLabsError(f"HTTP error calling ElevenLabs: {e}") from e

        if response.status_code >= 500:
            raise ElevenLabsError(f"ElevenLabs server error {response.status_code}: {response.text}")
        if response.status_code >= 400:
            raise ElevenLabsError(f"ElevenLabs client error {response.status_code}: {response.text}")

        data = response.json()
        if not data.get("success"):
            raise ElevenLabsError(f"Outbound call failed: {data}")
        return data

    def get_conversation(self, conversation_id: str) -> dict:
        """Fetch conversation details (used by orphan cleanup)."""
        headers = {"xi-api-key": self._api_key}
        try:
            response = httpx.get(
                f"{self.BASE_URL}/convai/conversations/{conversation_id}",
                headers=headers,
                timeout=self._timeout,
            )
        except httpx.HTTPError as e:
            raise ElevenLabsError(f"HTTP error: {e}") from e
        if response.status_code >= 400:
            raise ElevenLabsError(f"ElevenLabs error {response.status_code}: {response.text}")
        return response.json()


def create_elevenlabs_client() -> ElevenLabsClient:
    """Factory using ELEVENLABS_API_KEY env var."""
    import os
    api_key = os.environ["ELEVENLABS_API_KEY"]
    return ElevenLabsClient(api_key=api_key)
