"""Tests for Twilio SMS sending."""
import os
from unittest.mock import patch, MagicMock
import pytest

from apps.workers.setting_agent.twilio_sms import send_sms


@patch("apps.workers.setting_agent.twilio_sms.TwilioClient")
def test_send_sms_invokes_twilio(mock_client_cls):
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.sid = "SM_test_123"
    mock_client.messages.create.return_value = mock_message
    mock_client_cls.return_value = mock_client

    with patch.dict(os.environ, {
        "TWILIO_ACCOUNT_SID": "AC_test",
        "TWILIO_AUTH_TOKEN": "token_test",
        "TWILIO_PHONE_NUMBER": "+16627075199",
    }):
        sid = send_sms(to="+393477544532", body="Hello")

    assert sid == "SM_test_123"
    mock_client_cls.assert_called_once_with("AC_test", "token_test")
    mock_client.messages.create.assert_called_once_with(
        from_="+16627075199",
        to="+393477544532",
        body="Hello",
    )


@patch("apps.workers.setting_agent.twilio_sms.TwilioClient")
def test_send_sms_propagates_twilio_error(mock_client_cls):
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = Exception("Twilio 500")
    mock_client_cls.return_value = mock_client

    with patch.dict(os.environ, {
        "TWILIO_ACCOUNT_SID": "AC_test",
        "TWILIO_AUTH_TOKEN": "token_test",
        "TWILIO_PHONE_NUMBER": "+16627075199",
    }):
        with pytest.raises(Exception, match="Twilio 500"):
            send_sms(to="+393477544532", body="Hello")
