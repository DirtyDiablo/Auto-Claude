"""
LLM API retry decorators with exponential backoff.

Usage:
    from utils.llm_retry import anthropic_retry, openai_retry

    @anthropic_retry
    def call_claude(prompt: str):
        return client.messages.create(...)

    @openai_retry
    def get_embedding(text: str):
        return client.embeddings.create(...)
"""

import structlog
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

logger = structlog.get_logger(__name__)

# Try to import API exception classes
try:
    from anthropic import APIError, APIConnectionError, RateLimitError
    ANTHROPIC_EXCEPTIONS = (APIError, APIConnectionError, RateLimitError)
except ImportError:
    ANTHROPIC_EXCEPTIONS = (ConnectionError, TimeoutError)

try:
    from openai import OpenAIError, APIError as OpenAIAPIError, RateLimitError as OpenAIRateLimitError
    OPENAI_EXCEPTIONS = (OpenAIError, OpenAIAPIError, OpenAIRateLimitError)
except ImportError:
    OPENAI_EXCEPTIONS = (ConnectionError, TimeoutError)


def log_retry(retry_state):
    """Log retry attempts with structured logging."""
    exception = retry_state.outcome.exception()
    logger.warning(
        "llm_api_retry",
        attempt=retry_state.attempt_number,
        exception_type=type(exception).__name__,
        exception_msg=str(exception)[:200],
        wait_seconds=retry_state.next_action.sleep if retry_state.next_action else 0,
    )


# Decorator for Anthropic Claude API calls
anthropic_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception_type(ANTHROPIC_EXCEPTIONS),
    before_sleep=log_retry,
    reraise=True,
)

# Decorator for OpenAI API calls (embeddings, chat)
openai_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception_type(OPENAI_EXCEPTIONS),
    before_sleep=log_retry,
    reraise=True,
)

# Generic retry for any API call
api_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, IOError)),
    before_sleep=log_retry,
    reraise=True,
)


def with_retry(max_attempts: int = 3, min_wait: int = 1, max_wait: int = 30):
    """
    Configurable retry decorator factory.

    Usage:
        @with_retry(max_attempts=5, min_wait=2, max_wait=120)
        def my_api_call():
            ...
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type((Exception,)),
        before_sleep=log_retry,
        reraise=True,
    )
