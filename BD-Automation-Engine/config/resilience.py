"""
Tenacity retry decorators for BD-Automation-Engine.

Usage:
    from config.resilience import with_embedding_retry, with_chat_retry

    @with_embedding_retry
    def get_embedding(text):
        return openai_client.embeddings.create(...)

    @with_chat_retry
    def chat_complete(messages):
        return openai_client.chat.completions.create(...)
"""

import logging
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

logger = logging.getLogger("BD-Resilience")

# Retry on transient OpenAI / network errors
_TRANSIENT_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    OSError,
)

try:
    from openai import RateLimitError, APITimeoutError, APIConnectionError
    _TRANSIENT_EXCEPTIONS = (
        *_TRANSIENT_EXCEPTIONS,
        RateLimitError,
        APITimeoutError,
        APIConnectionError,
    )
except ImportError:
    pass


# Embedding calls: 5 attempts, exponential backoff 1s → 30s
with_embedding_retry = retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    retry=retry_if_exception_type(_TRANSIENT_EXCEPTIONS),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)

# Chat/LLM calls: 3 attempts, exponential backoff 2s → 60s
with_chat_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=60),
    retry=retry_if_exception_type(_TRANSIENT_EXCEPTIONS),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
