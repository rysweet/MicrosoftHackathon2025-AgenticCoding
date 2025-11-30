"""Main API client implementation.

Thread-safe HTTP client with retry and rate limiting.
"""

import time
import logging
import threading
from typing import Dict, Any, Optional, Union
from urllib.parse import urljoin
import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime

from .models import Request, Response
from .exceptions import (
    APIException,
    NetworkException,
    TimeoutException,
    RateLimitException,
    ValidationException,
    ServerException
)
from .config import APIClientConfig, RetryConfig, RateLimitConfig

logger = logging.getLogger(__name__)


class RateLimiter:
    """Thread-safe token bucket rate limiter.

    Internal class for rate limiting implementation.
    """

    def __init__(self, config: RateLimitConfig) -> None:
        """Initialize rate limiter.

        Args:
            config: Rate limit configuration
        """
        self.config = config
        self.tokens = float(config.burst_size)
        self.last_refill = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self, timeout: Optional[float] = None) -> bool:
        """Acquire a token for making a request.

        Args:
            timeout: Maximum time to wait for token

        Returns:
            True if token acquired, False if timeout
        """
        start_time = time.monotonic()
        timeout = timeout or 60.0

        while True:
            with self._lock:
                self._refill()

                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return True

            # Calculate wait time
            wait_time = self.config.refill_period
            elapsed = time.monotonic() - start_time

            if elapsed + wait_time > timeout:
                return False

            time.sleep(min(wait_time, 0.1))  # Sleep in small increments

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_refill

        if elapsed > self.config.refill_period:
            tokens_to_add = elapsed / self.config.refill_period
            self.tokens = min(
                self.tokens + tokens_to_add,
                float(self.config.burst_size)
            )
            self.last_refill = now


class APIClient:
    """Thread-safe REST API client.

    Main client class for making HTTP requests.
    All methods are thread-safe.
    """

    def __init__(self, config: Union[APIClientConfig, str]) -> None:
        """Initialize API client.

        Args:
            config: APIClientConfig or base URL string
        """
        if isinstance(config, str):
            config = APIClientConfig(base_url=config)

        self.config = config
        self._rate_limiter = None
        self._lock = threading.Lock()

        if config.rate_limit_config:
            self._rate_limiter = RateLimiter(config.rate_limit_config)

        logger.info(f"APIClient initialized for {config.base_url}")

    def request(self, request: Request) -> Response:
        """Execute HTTP request with retry and rate limiting.

        Thread-safe method for executing requests.

        Args:
            request: Request object

        Returns:
            Response object

        Raises:
            APIException: On request failure
        """
        # Apply rate limiting
        if self._rate_limiter:
            timeout = request.timeout or self.config.timeout
            if not self._rate_limiter.acquire(timeout):
                raise RateLimitException(
                    "Rate limit timeout - could not acquire token",
                    retry_after=self._rate_limiter.config.refill_period
                )

        # Execute with retries
        last_exception = None
        retry_config = self.config.retry_config

        for attempt in range(retry_config.max_retries + 1):
            try:
                if attempt > 0:
                    backoff = retry_config.calculate_backoff(attempt)
                    logger.info(f"Retry {attempt}/{retry_config.max_retries} after {backoff:.1f}s")
                    time.sleep(backoff)

                return self._execute_request(request)

            except (ServerException, NetworkException, TimeoutException) as e:
                last_exception = e

                # Check if should retry
                if attempt < retry_config.max_retries:
                    if isinstance(e, ServerException) and e.status_code:
                        if not retry_config.should_retry(e.status_code):
                            raise
                    continue
                raise

            except Exception as e:
                # Non-retryable error
                raise

        # All retries exhausted
        if last_exception:
            raise last_exception

    def _execute_request(self, request: Request) -> Response:
        """Execute single HTTP request.

        Internal method for executing a single request.

        Args:
            request: Request object

        Returns:
            Response object

        Raises:
            Various APIException subclasses
        """
        # Build full URL
        url = urljoin(self.config.base_url, request.path)

        # Add query parameters
        if request.params:
            query_string = urllib.parse.urlencode(request.params)
            url = f"{url}?{query_string}"

        # Prepare headers
        headers = {**self.config.headers, **(request.headers or {})}

        # Prepare body
        body = None
        if request.json_data is not None:
            body = json.dumps(request.json_data).encode("utf-8")
            headers.setdefault("Content-Type", "application/json")
        elif request.data is not None:
            body = request.data

        # Create urllib request
        urllib_request = urllib.request.Request(
            url,
            data=body,
            headers=headers,
            method=request.method
        )

        # Execute request
        timeout = request.timeout or self.config.timeout
        start_time = time.monotonic()

        try:
            with urllib.request.urlopen(urllib_request, timeout=timeout) as response:
                elapsed = time.monotonic() - start_time

                # Read response
                content = response.read()
                response_headers = dict(response.headers)

                # Parse JSON if applicable
                json_data = None
                text = None
                content_type = response_headers.get("Content-Type", "")

                if "application/json" in content_type:
                    try:
                        text = content.decode("utf-8")
                        json_data = json.loads(text)
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        text = content.decode("utf-8", errors="replace")
                else:
                    text = content.decode("utf-8", errors="replace")

                return Response(
                    status_code=response.status,
                    headers=response_headers,
                    json_data=json_data,
                    text=text,
                    elapsed=elapsed,
                    request=request,
                    timestamp=datetime.now()
                )

        except urllib.error.HTTPError as e:
            elapsed = time.monotonic() - start_time

            # Read error response
            content = e.read()
            text = content.decode("utf-8", errors="replace")
            json_data = None

            try:
                json_data = json.loads(text)
            except json.JSONDecodeError:
                pass

            response = Response(
                status_code=e.code,
                headers=dict(e.headers),
                json_data=json_data,
                text=text,
                elapsed=elapsed,
                request=request,
                timestamp=datetime.now()
            )

            # Raise appropriate exception
            if e.code == 429:
                retry_after = e.headers.get("Retry-After")
                if retry_after:
                    try:
                        retry_after = float(retry_after)
                    except ValueError:
                        retry_after = None

                raise RateLimitException(
                    f"Rate limit exceeded: {e.code}",
                    retry_after=retry_after,
                    response=response
                )
            elif 400 <= e.code < 500:
                raise ValidationException(
                    f"Client error: {e.code}",
                    status_code=e.code,
                    response=response
                )
            elif e.code >= 500:
                raise ServerException(
                    f"Server error: {e.code}",
                    status_code=e.code,
                    response=response
                )

        except urllib.error.URLError as e:
            if isinstance(e.reason, TimeoutError):
                raise TimeoutException(
                    f"Request timeout after {timeout}s",
                    timeout=timeout
                )
            else:
                raise NetworkException(
                    f"Network error: {e.reason}",
                    original_error=e
                )

        except TimeoutError:
            raise TimeoutException(
                f"Request timeout after {timeout}s",
                timeout=timeout
            )

        except Exception as e:
            raise NetworkException(
                f"Unexpected error: {str(e)}",
                original_error=e
            )

    # Convenience methods

    def get(self, path: str, **kwargs: Any) -> Response:
        """Execute GET request.

        Args:
            path: Request path
            **kwargs: Additional request parameters

        Returns:
            Response object
        """
        request = Request(method="GET", path=path, **kwargs)
        return self.request(request)

    def post(self, path: str, json_data: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Response:
        """Execute POST request.

        Args:
            path: Request path
            json_data: JSON body data
            **kwargs: Additional request parameters

        Returns:
            Response object
        """
        request = Request(method="POST", path=path, json_data=json_data, **kwargs)
        return self.request(request)

    def put(self, path: str, json_data: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Response:
        """Execute PUT request.

        Args:
            path: Request path
            json_data: JSON body data
            **kwargs: Additional request parameters

        Returns:
            Response object
        """
        request = Request(method="PUT", path=path, json_data=json_data, **kwargs)
        return self.request(request)

    def patch(self, path: str, json_data: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Response:
        """Execute PATCH request.

        Args:
            path: Request path
            json_data: JSON body data
            **kwargs: Additional request parameters

        Returns:
            Response object
        """
        request = Request(method="PATCH", path=path, json_data=json_data, **kwargs)
        return self.request(request)

    def delete(self, path: str, **kwargs: Any) -> Response:
        """Execute DELETE request.

        Args:
            path: Request path
            **kwargs: Additional request parameters

        Returns:
            Response object
        """
        request = Request(method="DELETE", path=path, **kwargs)
        return self.request(request)