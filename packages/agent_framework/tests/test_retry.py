import pytest
from packages.agent_framework.retry import should_retry, RetryableError, FatalError

def test_should_retry_when_under_max():
    assert should_retry(retry_count=0, max_retries=3) is True
    assert should_retry(retry_count=2, max_retries=3) is True

def test_should_not_retry_at_max():
    assert should_retry(retry_count=3, max_retries=3) is False

def test_should_not_retry_over_max():
    assert should_retry(retry_count=5, max_retries=3) is False

def test_retryable_error_is_exception():
    with pytest.raises(RetryableError):
        raise RetryableError("temporary failure")

def test_fatal_error_is_exception():
    with pytest.raises(FatalError):
        raise FatalError("permanent failure")
