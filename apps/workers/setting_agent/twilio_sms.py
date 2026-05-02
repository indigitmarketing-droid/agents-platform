"""Twilio SMS sender."""
import os
import logging
from twilio.rest import Client as TwilioClient

logger = logging.getLogger(__name__)


def send_sms(to: str, body: str) -> str:
    """Send SMS via Twilio. Returns Twilio message SID."""
    client = TwilioClient(
        os.environ["TWILIO_ACCOUNT_SID"],
        os.environ["TWILIO_AUTH_TOKEN"],
    )
    message = client.messages.create(
        from_=os.environ["TWILIO_PHONE_NUMBER"],
        to=to,
        body=body,
    )
    logger.info(f"SMS sent: to={to} sid={message.sid}")
    return message.sid
