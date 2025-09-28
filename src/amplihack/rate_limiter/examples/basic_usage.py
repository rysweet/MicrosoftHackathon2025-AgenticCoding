#!/usr/bin/env python3
"""Basic usage examples for the rate limiter module."""

import asyncio
import time
from typing import Any, Dict

from .. import RateLimitConfig, RateLimiter, rate_limit


async def example_basic_usage():
    """Basic rate limiting example."""
    print("=== Basic Rate Limiting Example ===")

    # Create rate limiter with default config
    limiter = RateLimiter()

    async def api_call(data: str) -> Dict[str, Any]:
        """Simulate an API call."""
        await asyncio.sleep(0.1)  # Simulate network delay
        return {"status": "success", "data": data}

    # Execute with rate limiting protection
    result = await limiter.execute(lambda: api_call("test data"))
    print(f"Result: {result}")


async def example_with_config():
    """Rate limiting with custom configuration."""
    print("\n=== Custom Configuration Example ===")

    config = RateLimitConfig(
        initial_tokens=5,  # Start with 5 tokens
        refill_rate=30,  # 30 tokens per minute (0.5/second)
        max_retries=3,  # Maximum 3 retries
        initial_delay=1.0,  # Start with 1 second delay
        max_delay=10.0,  # Cap at 10 seconds
        jitter_factor=0.2,  # 20% jitter
    )

    limiter = RateLimiter(config)

    async def rate_limited_api():
        """API that might hit rate limits."""
        # Simulate occasional rate limit errors
        import random

        if random.random() < 0.3:  # 30% chance of rate limit
            raise Exception("429 Too Many Requests")
        return {"message": "API call successful"}

    # Custom retry predicate
    def should_retry(error: Exception) -> bool:
        return "429" in str(error) or "rate limit" in str(error).lower()

    try:
        result = await limiter.execute(
            rate_limited_api,
            tokens=2.0,  # This call requires 2 tokens
            retry_on=should_retry,
        )
        print(f"Success: {result}")
    except Exception as e:
        print(f"Failed: {e}")


def example_progress_callback():
    """Example with progress callback."""
    print("\n=== Progress Callback Example ===")

    def progress_callback(update):
        """Handle progress updates."""
        message = update.format_message()
        print(f"Progress: {message}")

    async def demo_with_progress():
        config = RateLimitConfig(max_retries=3, initial_delay=1.0, jitter_factor=0)
        limiter = RateLimiter(config)

        attempt_count = 0

        async def flaky_api():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise Exception("Rate limit exceeded")
            return "Success after retries"

        return await limiter.execute(
            flaky_api, progress_callback=progress_callback, retry_on=lambda e: True
        )

    result = asyncio.run(demo_with_progress())
    print(f"Final result: {result}")


def example_decorator():
    """Example using the rate_limit decorator."""
    print("\n=== Decorator Example ===")

    # Apply rate limiting to a function
    @rate_limit(tokens=1.5)
    async def fetch_user_data(user_id: int):
        """Fetch user data with rate limiting."""
        await asyncio.sleep(0.1)  # Simulate API call
        return {"user_id": user_id, "name": f"User{user_id}"}

    @rate_limit(tokens=3.0)
    def process_data(data: str) -> str:
        """Process data with rate limiting (sync function)."""
        time.sleep(0.05)  # Simulate processing
        return data.upper()

    async def demo_decorators():
        # Async function with rate limiting
        user_data = await fetch_user_data(123)
        print(f"User data: {user_data}")

        # Sync function with rate limiting
        processed = process_data("hello world")
        print(f"Processed: {processed}")

    asyncio.run(demo_decorators())


async def example_token_management():
    """Example showing token consumption and refill."""
    print("\n=== Token Management Example ===")

    config = RateLimitConfig(
        initial_tokens=10,
        refill_rate=60,  # 1 token per second
        max_retries=1,
    )
    limiter = RateLimiter(config)

    async def small_request():
        return "small"

    async def large_request():
        return "large"

    print("Initial stats:", limiter.get_stats())

    # Make several requests with different token costs
    print("\nMaking requests...")
    for i in range(3):
        result = await limiter.execute(small_request, tokens=1.0)
        print(f"Small request {i + 1}: {result}")
        stats = limiter.get_stats()
        tokens = stats["token_bucket"]["tokens_available"]
        print(f"  Tokens remaining: {tokens:.1f}")

    # Try a large request
    try:
        result = await limiter.execute(large_request, tokens=8.0)
        print(f"Large request: {result}")
    except Exception as e:
        print(f"Large request failed: {e}")

    print("\nFinal stats:", limiter.get_stats())


async def example_concurrent_requests():
    """Example with concurrent requests."""
    print("\n=== Concurrent Requests Example ===")

    config = RateLimitConfig(initial_tokens=5, refill_rate=0)  # No refill for demo
    limiter = RateLimiter(config)

    async def api_request(request_id: int):
        """Simulate API request."""
        await asyncio.sleep(0.1)
        return f"Response {request_id}"

    async def make_request(request_id: int):
        """Make a rate-limited request."""
        try:
            result = await limiter.execute(lambda: api_request(request_id), tokens=1.0)
            print(f"✓ Request {request_id}: {result}")
            return True
        except Exception as e:
            print(f"✗ Request {request_id} failed: {e}")
            return False

    # Launch concurrent requests (more than available tokens)
    print(f"Launching 8 concurrent requests with {config.initial_tokens} tokens...")
    tasks = [make_request(i) for i in range(8)]
    results = await asyncio.gather(*tasks)

    successful = sum(results)
    print(f"Successful requests: {successful}/{len(tasks)}")


async def main():
    """Run all examples."""
    print("Rate Limiter Examples")
    print("====================")

    await example_basic_usage()
    await example_with_config()
    example_progress_callback()
    example_decorator()
    await example_token_management()
    await example_concurrent_requests()

    print("\n=== All Examples Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
