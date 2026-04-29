import pytest
from pytest_httpx import HTTPXMock
from apps.workers.setting_agent.elevenlabs_client import (
    ElevenLabsClient,
    ElevenLabsError,
)


def test_trigger_call_returns_conversation_data(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.elevenlabs.io/v1/convai/twilio/outbound_call",
        json={
            "success": True,
            "message": "Call initiated",
            "conversation_id": "conv_abc123",
            "callSid": "CA111222333",
        },
    )
    client = ElevenLabsClient(api_key="test_key")
    result = client.trigger_outbound_call(
        agent_id="agent_xxx",
        agent_phone_number_id="phn_yyy",
        to_number="+15551234567",
    )
    assert result["conversation_id"] == "conv_abc123"
    assert result["callSid"] == "CA111222333"


def test_trigger_call_sends_correct_payload(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.elevenlabs.io/v1/convai/twilio/outbound_call",
        json={"success": True, "conversation_id": "x", "callSid": "y"},
    )
    client = ElevenLabsClient(api_key="test_key")
    client.trigger_outbound_call(
        agent_id="agent_xxx",
        agent_phone_number_id="phn_yyy",
        to_number="+15551234567",
    )
    request = httpx_mock.get_request()
    assert request.headers["xi-api-key"] == "test_key"
    body = request.read()
    assert b'"agent_id"' in body
    assert b'"agent_xxx"' in body
    assert b'"+15551234567"' in body


def test_trigger_call_raises_on_success_false(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.elevenlabs.io/v1/convai/twilio/outbound_call",
        json={"success": False, "message": "agent not found"},
    )
    client = ElevenLabsClient(api_key="test_key")
    with pytest.raises(ElevenLabsError):
        client.trigger_outbound_call(
            agent_id="agent_bad",
            agent_phone_number_id="phn_yyy",
            to_number="+15551234567",
        )


def test_trigger_call_raises_on_http_error(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.elevenlabs.io/v1/convai/twilio/outbound_call",
        status_code=500,
    )
    client = ElevenLabsClient(api_key="test_key")
    with pytest.raises(ElevenLabsError):
        client.trigger_outbound_call(
            agent_id="agent_xxx",
            agent_phone_number_id="phn_yyy",
            to_number="+15551234567",
        )


def test_get_conversation(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.elevenlabs.io/v1/convai/conversations/conv_abc",
        json={
            "conversation_id": "conv_abc",
            "status": "done",
            "transcript": [{"role": "agent", "message": "Hello"}],
        },
    )
    client = ElevenLabsClient(api_key="test_key")
    result = client.get_conversation("conv_abc")
    assert result["status"] == "done"
