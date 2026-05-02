"""Tests for Stripe Checkout creation."""
import os
from unittest.mock import patch, MagicMock
import pytest

from apps.workers.setting_agent.stripe_client import create_stripe_checkout


def _sample_site():
    return {"id": "site-uuid", "slug": "mario-pizza"}


def _sample_lead():
    return {"id": "lead-uuid", "company_name": "Mario Pizza", "email": "mario@example.com"}


@patch("apps.workers.setting_agent.stripe_client.stripe")
def test_create_stripe_checkout_returns_url_and_session_id(mock_stripe):
    mock_session = MagicMock()
    mock_session.url = "https://checkout.stripe.com/c/pay/cs_test_123"
    mock_session.id = "cs_test_123"
    mock_stripe.checkout.Session.create.return_value = mock_session

    with patch.dict(os.environ, {
        "STRIPE_SECRET_KEY": "sk_test_xxx",
        "STRIPE_PRICE_ID": "price_xxx",
        "CUSTOMER_DASHBOARD_URL": "https://customer-dashboard-ashen.vercel.app",
    }):
        url, session_id = create_stripe_checkout(_sample_site(), _sample_lead())

    assert url == "https://checkout.stripe.com/c/pay/cs_test_123"
    assert session_id == "cs_test_123"

    mock_stripe.checkout.Session.create.assert_called_once()
    call_kwargs = mock_stripe.checkout.Session.create.call_args.kwargs
    assert call_kwargs["mode"] == "payment"
    assert call_kwargs["line_items"][0]["price"] == "price_xxx"
    assert call_kwargs["line_items"][0]["quantity"] == 1
    assert call_kwargs["customer_email"] == "mario@example.com"
    assert call_kwargs["metadata"] == {"site_id": "site-uuid", "lead_id": "lead-uuid"}
    assert "{CHECKOUT_SESSION_ID}" in call_kwargs["success_url"]


@patch("apps.workers.setting_agent.stripe_client.stripe")
def test_create_stripe_checkout_propagates_stripe_error(mock_stripe):
    mock_stripe.checkout.Session.create.side_effect = Exception("Stripe API down")
    with patch.dict(os.environ, {
        "STRIPE_SECRET_KEY": "sk_test_xxx",
        "STRIPE_PRICE_ID": "price_xxx",
        "CUSTOMER_DASHBOARD_URL": "https://customer-dashboard-ashen.vercel.app",
    }):
        with pytest.raises(Exception, match="Stripe API down"):
            create_stripe_checkout(_sample_site(), _sample_lead())
