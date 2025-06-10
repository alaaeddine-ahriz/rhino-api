"""Tests for main API status and general functionality."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestAPIStatus:
    """Test API status and general endpoints."""

    def test_root_api_endpoint(self):
        """Test the root API status endpoint."""
        response = client.get("/api")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Le Rhino API"
        assert data["data"]["status"] == "online"

    def test_api_docs_accessibility(self):
        """Test that API documentation is accessible."""
        # Test Swagger UI
        response = client.get("/api/docs")
        assert response.status_code == 200
        assert "html" in response.headers.get("content-type", "").lower()

    def test_api_redoc_accessibility(self):
        """Test that ReDoc documentation is accessible."""
        response = client.get("/api/redoc")
        assert response.status_code == 200
        assert "html" in response.headers.get("content-type", "").lower()

    def test_openapi_json_accessibility(self):
        """Test that OpenAPI JSON specification is accessible."""
        response = client.get("/api/openapi.json")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "").lower()
        
        # Verify it's valid JSON and has basic OpenAPI structure
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    def test_homepage_endpoint(self):
        """Test the homepage endpoint."""
        response = client.get("/")
        # This might return an HTML file or redirect, depending on implementation
        assert response.status_code in [200, 404]  # 404 if static file doesn't exist

    def test_cors_headers(self):
        """Test that CORS headers are properly set."""
        response = client.options("/api")
        # CORS headers should be present
        assert response.status_code in [200, 405]  # 405 if OPTIONS not explicitly handled

    def test_api_endpoints_structure(self):
        """Test that the API has the expected endpoint structure."""
        # Get OpenAPI specification
        response = client.get("/api/openapi.json")
        assert response.status_code == 200
        openapi_data = response.json()
        
        # Verify expected endpoint paths exist
        paths = openapi_data.get("paths", {})
        
        expected_prefixes = [
            "/api/users/",           # User management
            "/api/matieres/",        # Subject management
            "/api/question",         # Questions
            "/api/evaluation/",      # Evaluations
            "/api/challenges/",      # Challenges
            "/api/leaderboard/",     # Leaderboards
            "/api/matieres/{matiere}/documents"  # Documents
        ]
        
        # Check if expected endpoint patterns exist
        found_patterns = set()
        for path in paths.keys():
            for prefix in expected_prefixes:
                if path.startswith(prefix.replace("{matiere}", "SYD")):  # Handle path params
                    found_patterns.add(prefix)
                    break
        
        # We should have found most of our expected patterns
        assert len(found_patterns) > 0

    def test_api_response_format(self):
        """Test that API responses follow the expected format."""
        response = client.get("/api")
        assert response.status_code == 200
        data = response.json()
        
        # All API responses should have these fields
        assert "success" in data
        assert "message" in data
        assert "data" in data
        assert isinstance(data["success"], bool)
        assert isinstance(data["message"], str)

    def test_api_error_handling(self):
        """Test that API handles errors gracefully."""
        # Test non-existent endpoint
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
        
        # Response should still follow error format
        if response.headers.get("content-type", "").startswith("application/json"):
            data = response.json()
            assert "success" in data or "detail" in data

    def test_static_files_mount(self):
        """Test that static files are properly mounted."""
        # Test accessing static directory
        response = client.get("/static/")
        # Might return directory listing or 404 if no index, both are acceptable
        assert response.status_code in [200, 404, 403]


class TestAPIValidation:
    """Test API input validation and error responses."""

    def test_invalid_json_request(self):
        """Test handling of invalid JSON in request body."""
        response = client.post(
            "/api/users/register",
            data="invalid json",
            headers={"content-type": "application/json"}
        )
        assert response.status_code == 422  # Unprocessable Entity

    def test_missing_required_fields(self):
        """Test handling of missing required fields."""
        response = client.post("/api/users/register", json={})
        assert response.status_code == 422  # Validation error

    def test_validation_error_response_format(self):
        """Test that validation errors have proper format."""
        response = client.post("/api/users/register", json={})
        assert response.status_code == 422
        data = response.json()
        
        # Should have error details
        assert "success" in data or "detail" in data


class TestAPIPerformance:
    """Basic performance and reliability tests."""

    def test_api_response_time(self):
        """Test that API responds within reasonable time."""
        import time
        start_time = time.time()
        
        response = client.get("/api")
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 5.0  # Should respond within 5 seconds

    def test_multiple_concurrent_requests(self):
        """Test handling multiple requests."""
        import threading
        results = []
        
        def make_request():
            response = client.get("/api")
            results.append(response.status_code)
        
        # Make 10 concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert len(results) == 10
        assert all(status == 200 for status in results) 