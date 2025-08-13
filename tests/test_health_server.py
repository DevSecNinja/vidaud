"""Test health server functionality."""

import json
import logging
import time
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.health_server import HealthServer


class TestHealthServer:
    """Test HealthServer class."""

    def test_init_default_port(self):
        """Test HealthServer initialization with default port."""
        server = HealthServer()

        assert server.port == 8080
        assert isinstance(server.logger, logging.Logger)
        assert server.app.title == "vidaud Health Check"
        assert isinstance(server.start_time, datetime)

    def test_init_custom_port(self):
        """Test HealthServer initialization with custom port."""
        custom_port = 9000
        server = HealthServer(port=custom_port)

        assert server.port == custom_port
        assert server.app.title == "vidaud Health Check"

    def test_start_time_is_recent(self):
        """Test that start_time is set to a recent datetime."""
        before_creation = datetime.now(UTC)
        server = HealthServer()
        after_creation = datetime.now(UTC)

        assert before_creation <= server.start_time <= after_creation

    @pytest.mark.asyncio
    async def test_health_check_endpoint(self):
        """Test health check endpoint returns correct data."""
        server = HealthServer()

        # Mock the start time to a known value for predictable testing
        test_start_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
        server.start_time = test_start_time

        with patch("src.health_server.datetime") as mock_datetime:
            # Mock current time to be 10 seconds after start time
            current_time = test_start_time + timedelta(seconds=10)
            mock_datetime.now.return_value = current_time

            response = await server.health_check()

            assert response.status_code == 200

            # Parse the response content
            content = json.loads(response.body.decode())

            assert content["status"] == "healthy"
            assert content["timestamp"] == current_time.isoformat()
            assert content["uptime_seconds"] == 10.0

    @pytest.mark.asyncio
    async def test_health_check_uptime_calculation(self):
        """Test that uptime is calculated correctly over time."""
        server = HealthServer()

        # Set a known start time
        test_start_time = datetime(2025, 1, 1, 12, 0, 0)
        server.start_time = test_start_time

        # Test different uptime scenarios
        test_cases = [
            (timedelta(seconds=0), 0.0),
            (timedelta(seconds=30), 30.0),
            (timedelta(minutes=5), 300.0),
            (timedelta(hours=1), 3600.0),
            (timedelta(days=1), 86400.0),
        ]

        for time_delta, expected_uptime in test_cases:
            with patch("src.health_server.datetime") as mock_datetime:
                current_time = test_start_time + time_delta
                mock_datetime.now.return_value = current_time

                response = await server.health_check()
                content = json.loads(response.body.decode())

                assert content["uptime_seconds"] == expected_uptime

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self):
        """Test metrics endpoint returns correct data."""
        server = HealthServer()

        # Mock the start time to a known value
        test_start_time = datetime(2025, 1, 1, 12, 0, 0)
        server.start_time = test_start_time

        with patch("src.health_server.datetime") as mock_datetime:
            # Mock current time to be 25 seconds after start time
            current_time = test_start_time + timedelta(seconds=25)
            mock_datetime.now.return_value = current_time

            response = await server.metrics()

            assert response.status_code == 200

            # Parse the response content
            content = json.loads(response.body.decode())

            assert content["status"] == "running"
            assert content["uptime_seconds"] == 25.0
            assert content["start_time"] == test_start_time.isoformat()
            assert content["current_time"] == current_time.isoformat()

    @pytest.mark.asyncio
    async def test_metrics_consistent_with_health_check(self):
        """Test that metrics and health check return consistent uptime."""
        server = HealthServer()

        # Mock the start time
        test_start_time = datetime(2025, 1, 1, 12, 0, 0)
        server.start_time = test_start_time

        with patch("src.health_server.datetime") as mock_datetime:
            current_time = test_start_time + timedelta(seconds=42)
            mock_datetime.now.return_value = current_time

            health_response = await server.health_check()
            metrics_response = await server.metrics()

            health_content = json.loads(health_response.body.decode())
            metrics_content = json.loads(metrics_response.body.decode())

            assert health_content["uptime_seconds"] == metrics_content["uptime_seconds"]
            assert health_content["uptime_seconds"] == 42.0

    @pytest.mark.asyncio
    async def test_start_method_configuration(self):
        """Test that start method configures uvicorn correctly."""
        server = HealthServer(port=9001)

        with patch("src.health_server.uvicorn.Server") as mock_server_class:
            mock_server_instance = AsyncMock()
            mock_server_class.return_value = mock_server_instance

            with patch("src.health_server.uvicorn.Config") as mock_config_class:
                mock_config_instance = MagicMock()
                mock_config_class.return_value = mock_config_instance

                await server.start()

                # Verify Config was called with correct parameters
                mock_config_class.assert_called_once_with(
                    server.app,
                    host="0.0.0.0",
                    port=9001,
                    log_level="warning",
                    access_log=False,
                )

                # Verify Server was created with the config
                mock_server_class.assert_called_once_with(mock_config_instance)

                # Verify server.serve() was called
                mock_server_instance.serve.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_method_logging(self):
        """Test that start method logs the correct message."""
        server = HealthServer(port=8888)

        with patch("src.health_server.uvicorn.Server") as mock_server_class:
            mock_server_instance = AsyncMock()
            mock_server_class.return_value = mock_server_instance

            with patch.object(server.logger, "info") as mock_log_info:
                await server.start()

                mock_log_info.assert_called_once_with(
                    "Starting health server on port 8888"
                )

    def test_fastapi_routes_registered(self):
        """Test that FastAPI routes are properly registered."""
        server = HealthServer()

        # Get the routes from the FastAPI app
        routes = server.app.routes

        # Filter to get only the API routes (exclude OpenAPI routes)
        api_routes = [
            route
            for route in routes
            if hasattr(route, "path") and hasattr(route, "methods")
        ]

        # Check that we have the expected routes
        route_paths = [route.path for route in api_routes]
        assert "/health" in route_paths
        assert "/metrics" in route_paths

    def test_fastapi_app_configuration(self):
        """Test that FastAPI app is configured correctly."""
        server = HealthServer()

        assert server.app.title == "vidaud Health Check"
        assert hasattr(server.app, "routes")


class TestHealthServerIntegration:
    """Integration tests using FastAPI TestClient."""

    def test_health_endpoint_via_test_client(self):
        """Test health endpoint using FastAPI TestClient."""
        server = HealthServer()
        client = TestClient(server.app)

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], (int, float))
        assert data["uptime_seconds"] >= 0

    def test_metrics_endpoint_via_test_client(self):
        """Test metrics endpoint using FastAPI TestClient."""
        server = HealthServer()
        client = TestClient(server.app)

        response = client.get("/metrics")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "running"
        assert "uptime_seconds" in data
        assert "start_time" in data
        assert "current_time" in data
        assert isinstance(data["uptime_seconds"], (int, float))
        assert data["uptime_seconds"] >= 0

    def test_nonexistent_endpoint(self):
        """Test that nonexistent endpoints return 404."""
        server = HealthServer()
        client = TestClient(server.app)

        response = client.get("/nonexistent")

        assert response.status_code == 404

    def test_health_endpoint_multiple_calls(self):
        """Test that health endpoint can be called multiple times."""
        server = HealthServer()
        client = TestClient(server.app)

        # Make multiple calls
        responses = [client.get("/health") for _ in range(3)]

        # All should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"

    def test_metrics_endpoint_multiple_calls(self):
        """Test that metrics endpoint can be called multiple times."""
        server = HealthServer()
        client = TestClient(server.app)

        # Make multiple calls
        responses = [client.get("/metrics") for _ in range(3)]

        # All should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "running"

    def test_uptime_increases_over_time(self):
        """Test that uptime increases over multiple calls."""
        server = HealthServer()
        client = TestClient(server.app)

        # Get initial uptime
        first_response = client.get("/health")
        first_data = first_response.json()
        first_uptime = first_data["uptime_seconds"]

        # Wait a tiny bit (this is a unit test, so minimal wait)
        time.sleep(0.01)

        # Get second uptime
        second_response = client.get("/health")
        second_data = second_response.json()
        second_uptime = second_data["uptime_seconds"]

        # Second uptime should be greater than first
        assert second_uptime > first_uptime

    def test_timestamp_format(self):
        """Test that timestamp is in correct ISO format."""
        server = HealthServer()
        client = TestClient(server.app)

        response = client.get("/health")
        data = response.json()

        # Verify timestamp can be parsed as ISO format
        timestamp_str = data["timestamp"]
        parsed_timestamp = datetime.fromisoformat(timestamp_str)
        assert isinstance(parsed_timestamp, datetime)

    def test_start_time_format_in_metrics(self):
        """Test that start_time in metrics is in correct ISO format."""
        server = HealthServer()
        client = TestClient(server.app)

        response = client.get("/metrics")
        data = response.json()

        # Verify start_time can be parsed as ISO format
        start_time_str = data["start_time"]
        parsed_start_time = datetime.fromisoformat(start_time_str)
        assert isinstance(parsed_start_time, datetime)

        # Verify current_time can be parsed as ISO format
        current_time_str = data["current_time"]
        parsed_current_time = datetime.fromisoformat(current_time_str)
        assert isinstance(parsed_current_time, datetime)
