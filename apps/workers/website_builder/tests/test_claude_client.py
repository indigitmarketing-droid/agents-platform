import os
import pytest
from unittest.mock import patch
from apps.workers.website_builder.claude_client import create_anthropic_client


def test_create_client_uses_anthropic_api_key_env():
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key-123"}):
        client = create_anthropic_client()
        assert client is not None


def test_create_client_raises_when_env_missing():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(KeyError):
            create_anthropic_client()
