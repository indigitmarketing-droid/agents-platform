"""Anthropic SDK client factory."""
import os
from anthropic import Anthropic


def create_anthropic_client() -> Anthropic:
    """Create Anthropic client from ANTHROPIC_API_KEY env var."""
    api_key = os.environ["ANTHROPIC_API_KEY"]
    return Anthropic(api_key=api_key)
