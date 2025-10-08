#!/usr/bin/env python3
"""Example demonstrating context manager usage with ProxyManager."""

from pathlib import Path

from amplihack.proxy.config import ProxyConfig  # noqa
from amplihack.proxy.manager import ProxyManager  # noqa


def demo_context_manager():
    """Demonstrate using ProxyManager as a context manager."""

    # Load proxy configuration
    config_path = Path("azure.env")
    proxy_config = ProxyConfig(config_path)

    # Use context manager for automatic cleanup
    with ProxyManager(proxy_config) as proxy:
        print(f"Proxy running at: {proxy.get_proxy_url()}")  # noqa: T201 (print)

        # Your code here - proxy is automatically started
        # and will be stopped when exiting the context

        # Check if proxy is running
        if proxy.is_running():
            print("Proxy is active and ready")  # noqa: T201 (print)

        # Do work with the proxy...
        # The proxy will automatically stop when we exit this block

    print("Proxy has been automatically stopped")  # noqa: T201 (print)


def demo_traditional_usage():
    """Demonstrate traditional start/stop usage."""

    config_path = Path("azure.env")
    proxy_config = ProxyConfig(config_path)
    proxy_manager = ProxyManager(proxy_config)

    try:
        # Start proxy
        if proxy_manager.start_proxy():
            print(f"Proxy started at: {proxy_manager.get_proxy_url()}")  # noqa: T201 (print)

            # Do work with proxy...

        else:
            print("Failed to start proxy")  # noqa: T201 (print)
    finally:
        # Always clean up
        proxy_manager.stop_proxy()
        print("Proxy stopped")  # noqa: T201 (print)


if __name__ == "__main__":
    print("Context Manager Usage:")  # noqa: T201 (print)
    print("-" * 40)  # noqa: T201 (print)
    demo_context_manager()

    print("\n\nTraditional Usage:")  # noqa: T201 (print)
    print("-" * 40)  # noqa: T201 (print)
    demo_traditional_usage()
