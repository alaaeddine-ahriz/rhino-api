"""Tests for leaderboard API routes."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestLeaderboardAPI:
    """Test leaderboard functionality."""

    def setup_method(self):
        """Set up test users."""
        # Create student user
        response = client.post("/api/users/register", json={
            "username": "leaderboard_student",
            "email": "lbstudent@test.com",
            "role": "student",
            "subscriptions": ["SYD", "TCP"]
        })
        self.student_id = response.json()["data"]["user_id"]
        
        # Create teacher user
        response = client.post("/api/users/register", json={
            "username": "leaderboard_teacher",
            "email": "lbteacher@test.com",
            "role": "teacher",
            "subscriptions": ["SYD", "TCP"]
        })
        self.teacher_id = response.json()["data"]["user_id"]
        
        # Create admin user
        response = client.post("/api/users/register", json={
            "username": "leaderboard_admin",
            "email": "lbadmin@test.com",
            "role": "admin",
            "subscriptions": []
        })
        self.admin_id = response.json()["data"]["user_id"]

    def test_calculate_leaderboard_as_teacher(self):
        """Test calculating leaderboard as teacher."""
        response = client.post(f"/api/leaderboard/calcule?user_id={self.teacher_id}", json={
            "challenge_id": "SYD-001",
            "matiere": "SYD"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "user_info" in data["data"]
        assert data["data"]["user_info"]["user_id"] == str(self.teacher_id)
        assert data["data"]["user_info"]["username"] == "leaderboard_teacher"

    def test_calculate_leaderboard_as_admin(self):
        """Test calculating leaderboard as admin."""
        response = client.post(f"/api/leaderboard/calcule?user_id={self.admin_id}", json={
            "challenge_id": "TCP-001",
            "matiere": "TCP"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "user_info" in data["data"]
        assert data["data"]["user_info"]["user_id"] == str(self.admin_id)

    def test_calculate_leaderboard_as_student_forbidden(self):
        """Test that students cannot calculate leaderboards."""
        response = client.post(f"/api/leaderboard/calcule?user_id={self.student_id}", json={
            "challenge_id": "SYD-002",
            "matiere": "SYD"
        })
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert "permission" in data["message"].lower()

    def test_calculate_leaderboard_invalid_user(self):
        """Test calculating leaderboard with invalid user."""
        response = client.post("/api/leaderboard/calcule?user_id=999999", json={
            "challenge_id": "SYD-003",
            "matiere": "SYD"
        })
        assert response.status_code != 200

    def test_calculate_leaderboard_empty_challenge_id(self):
        """Test calculating leaderboard with empty challenge ID."""
        response = client.post(f"/api/leaderboard/calcule?user_id={self.teacher_id}", json={
            "challenge_id": "",
            "matiere": "SYD"
        })
        # Should fail validation
        assert response.status_code != 200

    def test_calculate_leaderboard_empty_matiere(self):
        """Test calculating leaderboard with empty matiere."""
        response = client.post(f"/api/leaderboard/calcule?user_id={self.teacher_id}", json={
            "challenge_id": "SYD-004",
            "matiere": ""
        })
        # Should fail validation
        assert response.status_code != 200

    def test_calculate_leaderboard_different_matieres(self):
        """Test calculating leaderboards for different subjects."""
        # Test SYD leaderboard
        syd_response = client.post(f"/api/leaderboard/calcule?user_id={self.teacher_id}", json={
            "challenge_id": "SYD-LEADERBOARD-001",
            "matiere": "SYD"
        })
        assert syd_response.status_code == 200
        syd_data = syd_response.json()
        assert syd_data["success"] is True
        
        # Test TCP leaderboard
        tcp_response = client.post(f"/api/leaderboard/calcule?user_id={self.teacher_id}", json={
            "challenge_id": "TCP-LEADERBOARD-001",
            "matiere": "TCP"
        })
        assert tcp_response.status_code == 200
        tcp_data = tcp_response.json()
        assert tcp_data["success"] is True

    def test_calculate_leaderboard_nonexistent_challenge(self):
        """Test calculating leaderboard for non-existent challenge."""
        response = client.post(f"/api/leaderboard/calcule?user_id={self.teacher_id}", json={
            "challenge_id": "NONEXISTENT-999",
            "matiere": "SYD"
        })
        # Should handle gracefully - might return empty leaderboard or error
        assert response.status_code in [200, 400, 404]

    def test_calculate_leaderboard_multiple_requests(self):
        """Test calculating leaderboard multiple times for same challenge."""
        challenge_data = {
            "challenge_id": "SYD-MULTI-001",
            "matiere": "SYD"
        }
        
        # First request
        response1 = client.post(f"/api/leaderboard/calcule?user_id={self.teacher_id}", json=challenge_data)
        assert response1.status_code == 200
        
        # Second request (should work consistently)
        response2 = client.post(f"/api/leaderboard/calcule?user_id={self.teacher_id}", json=challenge_data)
        assert response2.status_code == 200
        
        # Both should be successful
        assert response1.json()["success"] is True
        assert response2.json()["success"] is True

    def test_calculate_leaderboard_with_special_challenge_id(self):
        """Test calculating leaderboard with special characters in challenge ID."""
        response = client.post(f"/api/leaderboard/calcule?user_id={self.teacher_id}", json={
            "challenge_id": "SYD-SPECIAL_CHARS-2024@01",
            "matiere": "SYD"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_calculate_leaderboard_case_sensitivity(self):
        """Test calculating leaderboard with different case variations."""
        # Test lowercase matiere
        response1 = client.post(f"/api/leaderboard/calcule?user_id={self.teacher_id}", json={
            "challenge_id": "test-case-001",
            "matiere": "syd"
        })
        assert response1.status_code == 200
        
        # Test uppercase matiere
        response2 = client.post(f"/api/leaderboard/calcule?user_id={self.teacher_id}", json={
            "challenge_id": "test-case-002",
            "matiere": "SYD"
        })
        assert response2.status_code == 200

    def test_calculate_leaderboard_admin_permissions(self):
        """Test that admin has full access to leaderboard calculations."""
        # Admin should be able to calculate leaderboards for any subject
        subjects = ["SYD", "TCP", "MATH", "PHYSICS"]
        
        for i, subject in enumerate(subjects):
            response = client.post(f"/api/leaderboard/calcule?user_id={self.admin_id}", json={
                "challenge_id": f"{subject}-ADMIN-{i:03d}",
                "matiere": subject
            })
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["user_info"]["username"] == "leaderboard_admin"

    def test_calculate_leaderboard_teacher_multiple_subjects(self):
        """Test teacher calculating leaderboards for multiple subjects."""
        # Teacher should be able to calculate leaderboards for subscribed subjects
        subjects = ["SYD", "TCP"]
        
        for i, subject in enumerate(subjects):
            response = client.post(f"/api/leaderboard/calcule?user_id={self.teacher_id}", json={
                "challenge_id": f"{subject}-TEACHER-{i:03d}",
                "matiere": subject
            })
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True 