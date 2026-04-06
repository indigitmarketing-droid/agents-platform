class RetryableError(Exception):
    """Error that can be retried (network timeout, rate limit, etc.)."""
    pass

class FatalError(Exception):
    """Error that should not be retried (invalid data, auth failure, etc.)."""
    pass

def should_retry(retry_count: int, max_retries: int = 3) -> bool:
    return retry_count < max_retries
