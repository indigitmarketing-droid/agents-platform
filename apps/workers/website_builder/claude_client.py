"""Anthropic SDK client factory."""
import os
from anthropic import Anthropic


def create_anthropic_client() -> Anthropic:
    """Create an Anthropic client using ANTHROPIC_API_KEY env var.

    Raises:
        KeyError: if ANTHROPIC_API_KEY is not set.
    """
    api_key = os.environ["ANTHROPIC_API_KEY"]
    return Anthropic(api_key=api_key)
