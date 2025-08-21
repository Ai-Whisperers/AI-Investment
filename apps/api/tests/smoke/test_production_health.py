"""
Smoke tests for production health monitoring.
These tests run against the live production environment to ensure critical functionality.
"""

import os
from datetime import datetime, timedelta

import pytest
import requests


@pytest.mark.smoke
class TestProductionHealth:
    """Quick health checks for production environment."""

    @pytest.fixture
    def api_url(self):
        """Get production API URL from environment."""
        return os.getenv("PRODUCTION_URL", "https://waardhaven-api.onrender.com")

    def test_api_health_check(self, api_url):
        """Test that API is responding to health checks."""
        response = requests.get(f"{api_url}/health", timeout=5)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "timestamp" in data

    def test_database_connectivity(self, api_url):
        """Test that database is connected and responding."""
        response = requests.get(f"{api_url}/api/v1/diagnostics/database-status", timeout=5)

        assert response.status_code == 200
        data = response.json()
        assert data.get("connected") == True or data.get("status") == "healthy"
        assert "tables" in data

    def test_cache_status(self, api_url):
        """Test that cache layer is operational."""
        response = requests.get(f"{api_url}/api/v1/diagnostics/cache-status", timeout=5)

        assert response.status_code == 200
        data = response.json()
        # Cache might be disconnected but API should still work
        assert data["status"] in ["connected", "disconnected"]

    def test_authentication_endpoint(self, api_url):
        """Test that authentication endpoint is accessible."""
        # Test login endpoint exists (not actual login)
        response = requests.options(f"{api_url}/api/v1/auth/login", timeout=5)
        assert response.status_code in [200, 204]

        # Test that protected endpoint returns 401 without auth
        response = requests.get(f"{api_url}/api/v1/auth/me", timeout=5)
        assert response.status_code == 401

    def test_critical_api_endpoints(self, api_url):
        """Test that critical API endpoints are accessible."""
        critical_endpoints = [
            "/api/v1/portfolio",
            "/api/v1/index",
            "/api/v1/strategy",
            "/api/v1/market"
        ]

        for endpoint in critical_endpoints:
            # Use OPTIONS to check endpoint exists without auth
            response = requests.options(f"{api_url}{endpoint}", timeout=5)
            assert response.status_code in [200, 204], f"Endpoint {endpoint} not accessible"

    def test_market_data_freshness(self, api_url):
        """Test that market data is being updated."""
        response = requests.get(f"{api_url}/api/v1/diagnostics/refresh-status", timeout=5)

        if response.status_code == 200:
            data = response.json()

            # Check if data is fresh (updated within last 24 hours)
            if "last_successful" in data:
                last_update = datetime.fromisoformat(data["last_successful"])
                age = datetime.now() - last_update
                assert age < timedelta(hours=24), f"Data is {age.total_seconds()/3600:.1f} hours old"

    def test_response_times(self, api_url):
        """Test that API response times are acceptable."""
        endpoints = [
            "/health",
            "/api/v1/diagnostics/database-status"
        ]

        for endpoint in endpoints:
            response = requests.get(f"{api_url}{endpoint}", timeout=5)

            # Response time should be under 2 seconds
            assert response.elapsed.total_seconds() < 2.0, \
                f"Endpoint {endpoint} took {response.elapsed.total_seconds():.2f}s"

    def test_error_handling(self, api_url):
        """Test that API handles errors gracefully."""
        # Test 404 handling
        response = requests.get(f"{api_url}/api/v1/nonexistent", timeout=5)
        assert response.status_code == 404
        assert "detail" in response.json()

        # Test invalid request handling
        response = requests.post(
            f"{api_url}/api/v1/auth/login",
            json={"invalid": "data"},
            timeout=5
        )
        assert response.status_code in [400, 422]

    def test_cors_headers(self, api_url):
        """Test that CORS headers are properly configured."""
        response = requests.options(
            f"{api_url}/api/v1/portfolio",
            headers={"Origin": "https://waardhaven.com"},
            timeout=5
        )

        # Check CORS headers
        assert "Access-Control-Allow-Origin" in response.headers or \
               "access-control-allow-origin" in response.headers

    @pytest.mark.critical
    def test_data_integrity(self, api_url):
        """Test that critical data integrity checks pass."""
        response = requests.get(f"{api_url}/api/v1/diagnostics/data-integrity", timeout=5)

        if response.status_code == 200:
            data = response.json()

            # Check for data integrity issues
            if "issues" in data:
                assert len(data["issues"]) == 0, f"Data integrity issues found: {data['issues']}"

            # Check for orphaned records
            if "orphaned_records" in data:
                assert data["orphaned_records"] == 0, "Orphaned records detected"

    def test_ssl_certificate(self, api_url):
        """Test that SSL certificate is valid."""
        if api_url.startswith("https://"):
            # This will fail if certificate is invalid
            response = requests.get(api_url, timeout=5, verify=True)
            assert response.status_code < 500

    @pytest.mark.performance
    def test_concurrent_requests(self, api_url):
        """Test that API handles concurrent requests."""
        import concurrent.futures

        def make_request():
            return requests.get(f"{api_url}/health", timeout=5)

        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All should succeed
        assert all(r.status_code == 200 for r in results)

        # Response times should be reasonable even under load
        avg_time = sum(r.elapsed.total_seconds() for r in results) / len(results)
        assert avg_time < 3.0, f"Average response time {avg_time:.2f}s under load"
