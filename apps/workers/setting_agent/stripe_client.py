"""Stripe Checkout session creator."""
import os
import logging
import stripe

logger = logging.getLogger(__name__)


def create_stripe_checkout(site: dict, lead: dict) -> tuple[str, str]:
    """Create a Stripe Checkout Session. Returns (url, session_id)."""
    stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
    dashboard_url = os.environ["CUSTOMER_DASHBOARD_URL"]
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[{
            "price": os.environ["STRIPE_PRICE_ID"],
            "quantity": 1,
        }],
        success_url=f"{dashboard_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{dashboard_url}/payment-cancel",
        customer_email=lead.get("email"),
        metadata={
            "site_id": site["id"],
            "lead_id": lead["id"],
        },
        payment_intent_data={
            "metadata": {"site_id": site["id"], "lead_id": lead["id"]},
        },
    )
    logger.info(f"Stripe Checkout created: site={site['id']} session={session.id}")
    return session.url, session.id
