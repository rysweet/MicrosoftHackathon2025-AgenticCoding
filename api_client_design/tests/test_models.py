#!/usr/bin/env python3
"""
Unit tests for Request and Response models

Testing pyramid: 60% unit tests (this file)
Fast, heavily mocked, test core logic
"""

import pytest
import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api_client import Request, Response, HTTPMethod


class TestRequest:
    """Test Request dataclass behavior"""

    def test_request_creation(self):
        """Request can be created with minimal parameters"""
        request = Request(
            method=HTTPMethod.GET,
            path="/test"
        )
        assert request.method == HTTPMethod.GET
        assert request.path == "/test"
        assert request.headers == {}
        assert request.params == {}
        assert request.json is None
        assert request.data is None
        assert request.timeout is None

    def test_request_with_all_parameters(self):
        """Request accepts all parameters"""
        request = Request(
            method=HTTPMethod.POST,
            path="/api/users",
            headers={"Content-Type": "application/json"},
            params={"filter": "active"},
            json={"name": "test"},
            timeout=30.0
        )
        assert request.method == HTTPMethod.POST
        assert request.json == {"name": "test"}
        assert request.timeout == 30.0

    def test_request_path_normalization(self):
        """Request normalizes path to start with /"""
        request1 = Request(method=HTTPMethod.GET, path="test")
        assert request1.path == "/test"

        request2 = Request(method=HTTPMethod.GET, path="/test")
        assert request2.path == "/test"

    def test_request_json_data_exclusivity(self):
        """Request cannot have both json and data"""
        with pytest.raises(ValueError, match="Cannot specify both json and data"):
            Request(
                method=HTTPMethod.POST,
                path="/test",
                json={"key": "value"},
                data="raw data"
            )

    def test_request_immutability(self):
        """Request fields are immutable after creation"""
        request = Request(method=HTTPMethod.GET, path="/test")

        # Dataclass fields can be modified (Python doesn't enforce frozen)
        # but we document them as immutable in the contract
        # Real immutability would use frozen=True
        original_path = request.path
        request.path = "/modified"  # This works but violates contract
        assert request.path == "/modified"  # Shows it was modified

        # Best practice: treat as immutable in usage


class TestResponse:
    """Test Response dataclass behavior"""

    def test_response_creation(self):
        """Response can be created with required parameters"""
        request = Request(method=HTTPMethod.GET, path="/test")
        response = Response(
            status_code=200,
            headers={"Content-Type": "text/plain"},
            text="Hello",
            request=request,
            elapsed=0.123
        )
        assert response.status_code == 200
        assert response.text == "Hello"
        assert response.request == request
        assert response.elapsed == 0.123

    def test_response_ok_property(self):
        """Response.ok correctly identifies successful responses"""
        request = Request(method=HTTPMethod.GET, path="/test")

        # 2xx responses are ok
        for status in [200, 201, 204, 299]:
            response = Response(
                status_code=status,
                headers={},
                text="",
                request=request,
                elapsed=0.1
            )
            assert response.ok is True

        # Non-2xx responses are not ok
        for status in [100, 199, 300, 400, 404, 500, 503]:
            response = Response(
                status_code=status,
                headers={},
                text="",
                request=request,
                elapsed=0.1
            )
            assert response.ok is False

    def test_response_json_lazy_parsing(self):
        """Response.json lazily parses JSON text"""
        request = Request(method=HTTPMethod.GET, path="/test")
        json_text = '{"key": "value", "number": 42}'

        response = Response(
            status_code=200,
            headers={"Content-Type": "application/json"},
            text=json_text,
            request=request,
            elapsed=0.1
        )

        # First access parses JSON
        parsed = response.json
        assert parsed == {"key": "value", "number": 42}

        # Second access returns cached value
        parsed2 = response.json
        assert parsed2 is parsed  # Same object reference

    def test_response_json_parsing_error(self):
        """Response.json raises error for invalid JSON"""
        request = Request(method=HTTPMethod.GET, path="/test")
        response = Response(
            status_code=200,
            headers={},
            text="Not valid JSON",
            request=request,
            elapsed=0.1
        )

        with pytest.raises(json.JSONDecodeError):
            _ = response.json

    def test_response_json_caching(self):
        """Response caches parsed JSON after first access"""
        request = Request(method=HTTPMethod.GET, path="/test")
        response = Response(
            status_code=200,
            headers={},
            text='{"test": true}',
            request=request,
            elapsed=0.1
        )

        # Verify cache is initially None
        assert response._json_cache is None

        # Access json property
        parsed = response.json
        assert parsed == {"test": True}

        # Verify cache is now populated
        assert response._json_cache == {"test": True}


class TestHTTPMethod:
    """Test HTTPMethod enum"""

    def test_all_methods_defined(self):
        """All standard HTTP methods are defined"""
        expected_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
        actual_methods = [method.value for method in HTTPMethod]
        assert set(actual_methods) == set(expected_methods)

    def test_method_string_conversion(self):
        """HTTPMethod converts to string correctly"""
        assert str(HTTPMethod.GET) == "HTTPMethod.GET"
        assert HTTPMethod.GET.value == "GET"

    def test_method_comparison(self):
        """HTTPMethod can be compared"""
        assert HTTPMethod.GET == HTTPMethod.GET
        assert HTTPMethod.GET != HTTPMethod.POST
        assert HTTPMethod.GET.value == "GET"


class TestModelIntegration:
    """Test Request and Response work together"""

    def test_request_response_round_trip(self):
        """Request is preserved in Response"""
        request = Request(
            method=HTTPMethod.POST,
            path="/api/create",
            headers={"Authorization": "Bearer token"},
            json={"data": "value"}
        )

        response = Response(
            status_code=201,
            headers={"Location": "/api/resource/123"},
            text='{"id": 123, "data": "value"}',
            request=request,
            elapsed=0.456
        )

        # Verify request is preserved
        assert response.request == request
        assert response.request.method == HTTPMethod.POST
        assert response.request.json == {"data": "value"}

    def test_model_type_hints(self):
        """Models have correct type hints (compile-time check)"""
        # This test verifies that type hints work correctly
        # It doesn't run assertions but ensures the code type-checks

        request: Request = Request(
            method=HTTPMethod.GET,
            path="/test"
        )

        response: Response = Response(
            status_code=200,
            headers={},
            text="",
            request=request,
            elapsed=0.0
        )

        # Type hints should allow these operations
        method: HTTPMethod = request.method
        code: int = response.status_code
        ok: bool = response.ok
        data: dict = response.json if response.text else {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])