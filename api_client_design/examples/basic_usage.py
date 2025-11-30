#!/usr/bin/env python3
"""
Basic usage examples for the REST API Client Library

These examples demonstrate the core functionality without complexity.
Each example is self-contained and runnable.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from api_client import APIClient, HTTPError, TimeoutError


def example_simple_get():
    """Simple GET request example"""
    print("=== Simple GET Request ===")

    client = APIClient("https://jsonplaceholder.typicode.com")

    # Get a single post
    response = client.get("/posts/1")
    print(f"Status: {response.status_code}")
    print(f"Title: {response.json['title']}")
    print()


def example_get_with_params():
    """GET request with query parameters"""
    print("=== GET with Parameters ===")

    client = APIClient("https://jsonplaceholder.typicode.com")

    # Get posts for a specific user
    response = client.get("/posts", params={"userId": "1"})
    posts = response.json
    print(f"Found {len(posts)} posts for user 1")
    print(f"First post title: {posts[0]['title']}")
    print()


def example_post_json():
    """POST request with JSON body"""
    print("=== POST with JSON ===")

    client = APIClient("https://jsonplaceholder.typicode.com")

    # Create a new post
    new_post = {
        "title": "My New Post",
        "body": "This is the post content",
        "userId": 1
    }

    response = client.post("/posts", json=new_post)
    created = response.json
    print(f"Created post with ID: {created['id']}")
    print(f"Response status: {response.status_code}")
    print()


def example_put_update():
    """PUT request to update resource"""
    print("=== PUT Update ===")

    client = APIClient("https://jsonplaceholder.typicode.com")

    # Update an existing post
    updated_data = {
        "id": 1,
        "title": "Updated Title",
        "body": "Updated content",
        "userId": 1
    }

    response = client.put("/posts/1", json=updated_data)
    print(f"Update status: {response.status_code}")
    print(f"Updated title: {response.json['title']}")
    print()


def example_delete():
    """DELETE request example"""
    print("=== DELETE Request ===")

    client = APIClient("https://jsonplaceholder.typicode.com")

    # Delete a post
    response = client.delete("/posts/1")
    print(f"Delete status: {response.status_code}")
    print(f"Response OK: {response.ok}")
    print()


def example_custom_headers():
    """Request with custom headers"""
    print("=== Custom Headers ===")

    client = APIClient(
        base_url="https://httpbin.org",
        default_headers={
            "User-Agent": "MyApp/1.0",
            "X-Custom-Header": "CustomValue"
        }
    )

    # Headers are included in all requests
    response = client.get("/headers")
    headers_echo = response.json["headers"]
    print(f"User-Agent: {headers_echo.get('User-Agent')}")
    print(f"Custom Header: {headers_echo.get('X-Custom-Header')}")
    print()


def example_error_handling():
    """Error handling examples"""
    print("=== Error Handling ===")

    client = APIClient("https://httpbin.org")

    # Handle 404 error
    try:
        response = client.get("/status/404")
    except HTTPError as e:
        print(f"HTTP Error: {e.status_code} - {e.message}")

    # Handle timeout (simulated)
    client_with_timeout = APIClient(
        base_url="https://httpbin.org",
        timeout=0.001  # Very short timeout
    )

    try:
        response = client_with_timeout.get("/delay/5")
    except TimeoutError as e:
        print(f"Timeout Error: {e.message}")

    print()


def example_response_properties():
    """Working with response properties"""
    print("=== Response Properties ===")

    client = APIClient("https://httpbin.org")

    response = client.get("/get", params={"test": "value"})

    # Access various response properties
    print(f"Status Code: {response.status_code}")
    print(f"Is OK: {response.ok}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Response Time: {response.elapsed:.3f} seconds")
    print(f"Request Method: {response.request.method}")
    print(f"Request Path: {response.request.path}")
    print()


if __name__ == "__main__":
    # Run all examples
    print("REST API Client - Basic Usage Examples\n")
    print("=" * 50)

    examples = [
        example_simple_get,
        example_get_with_params,
        example_post_json,
        example_put_update,
        example_delete,
        example_custom_headers,
        example_response_properties,
        # example_error_handling,  # Skip to avoid actual errors in demo
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"Example failed: {e}\n")

    print("=" * 50)
    print("Examples completed!")