"""Tests for challenges API routes."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestChallengesAPI:
    """Test challenges management functionality."""

    def setup_method(self):
        """Set up test users."""
        # Create student user
        response = client.post("/api/users/register", json={
            "username": "challenge_student",
            "email": "cstudent@test.com",
            "role": "student",
            "subscriptions": ["SYD", "TCP"]
        })
        self.student_id = response.json()["data"]["user_id"]
        
        # Create teacher user
        response = client.post("/api/users/register", json={
            "username": "challenge_teacher",
            "email": "cteacher@test.com",
            "role": "teacher",
            "subscriptions": ["SYD", "TCP"]
        })
        self.teacher_id = response.json()["data"]["user_id"]

    def test_get_today_challenge_as_student(self):
        """Test getting today's challenge as student."""
        response = client.get(f"/api/challenges/today?user_id={self.student_id}")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "message" in data
        assert "data" in data
        
        # If successful, check challenge structure
        if data["success"]:
            assert "challenge" in data["data"]
            assert "user_subscriptions" in data["data"]

    def test_get_today_challenge_as_teacher(self):
        """Test getting today's challenge as teacher."""
        response = client.get(f"/api/challenges/today?user_id={self.teacher_id}")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data

    def test_get_today_challenge_invalid_user(self):
        """Test getting today's challenge with invalid user."""
        response = client.get("/api/challenges/today?user_id=999999")
        assert response.status_code != 200

    def test_get_challenges_list_as_student(self):
        """Test getting challenges list as student."""
        response = client.get(f"/api/challenges?user_id={self.student_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Challenges récupérés avec succès"

    def test_get_challenges_list_with_filter(self):
        """Test getting challenges list filtered by matiere."""
        response = client.get(f"/api/challenges?user_id={self.student_id}&matiere=SYD")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_challenges_list_as_teacher(self):
        """Test getting challenges list as teacher."""
        response = client.get(f"/api/challenges?user_id={self.teacher_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_create_challenge_as_teacher(self):
        """Test creating a new challenge as teacher."""
        response = client.post(f"/api/challenges?user_id={self.teacher_id}", json={
            "ref": "SYD-TEST-001",
            "question": "Explain the difference between a router and a switch in networking.",
            "matiere": "SYD",
            "date": "2024-06-10",
            "type": "knowledge"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "challenge" in data["data"]
        assert data["data"]["challenge"]["ref"] == "SYD-TEST-001"

    def test_create_challenge_as_student_forbidden(self):
        """Test that students cannot create challenges."""
        response = client.post(f"/api/challenges?user_id={self.student_id}", json={
            "ref": "FORBIDDEN-001",
            "question": "This should not be allowed",
            "matiere": "SYD",
            "date": "2024-06-10"
        })
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert "permission" in data["message"].lower()

    def test_create_challenge_invalid_data(self):
        """Test creating challenge with invalid data."""
        response = client.post(f"/api/challenges?user_id={self.teacher_id}", json={
            "ref": "",  # Empty ref
            "question": "Valid question",
            "matiere": "SYD",
            "date": "2024-06-10"
        })
        # Should fail validation
        assert response.status_code != 200

    def test_submit_challenge_response_as_student(self):
        """Test submitting a challenge response as student."""
        # First create a challenge
        create_response = client.post(f"/api/challenges?user_id={self.teacher_id}", json={
            "ref": "SYD-RESPONSE-001",
            "question": "What is DHCP?",
            "matiere": "SYD",
            "date": "2024-06-10"
        })
        
        if create_response.status_code == 200:
            challenge_id = create_response.json()["data"]["challenge"]["id"]
            
            # Submit response
            response = client.post(
                f"/api/challenges/{challenge_id}/response?user_id={self.student_id}",
                json={
                    "user_id": self.student_id,
                    "response": "DHCP stands for Dynamic Host Configuration Protocol. It automatically assigns IP addresses to devices on a network."
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "submission" in data["data"]
            assert data["data"]["submission"]["challenge_id"] == challenge_id

    def test_submit_challenge_response_as_teacher(self):
        """Test submitting a challenge response as teacher."""
        # First create a challenge
        create_response = client.post(f"/api/challenges?user_id={self.teacher_id}", json={
            "ref": "TCP-TEACHER-001",
            "question": "Explain TCP congestion control",
            "matiere": "TCP",
            "date": "2024-06-10"
        })
        
        if create_response.status_code == 200:
            challenge_id = create_response.json()["data"]["challenge"]["id"]
            
            # Submit response
            response = client.post(
                f"/api/challenges/{challenge_id}/response?user_id={self.teacher_id}",
                json={
                    "user_id": self.teacher_id,
                    "response": "TCP congestion control includes slow start, congestion avoidance, fast retransmit, and fast recovery algorithms."
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_submit_response_invalid_challenge(self):
        """Test submitting response to non-existent challenge."""
        response = client.post(
            f"/api/challenges/nonexistent/response?user_id={self.student_id}",
            json={
                "user_id": self.student_id,
                "response": "This challenge doesn't exist"
            }
        )
        # Should return error
        assert response.status_code != 200

    def test_submit_response_invalid_user(self):
        """Test submitting response with invalid user."""
        response = client.post(
            "/api/challenges/some_id/response?user_id=999999",
            json={
                "user_id": 999999,
                "response": "Invalid user response"
            }
        )
        assert response.status_code != 200

    def test_submit_empty_response(self):
        """Test submitting empty response."""
        # First create a challenge
        create_response = client.post(f"/api/challenges?user_id={self.teacher_id}", json={
            "ref": "SYD-EMPTY-001",
            "question": "Test question for empty response",
            "matiere": "SYD",
            "date": "2024-06-10"
        })
        
        if create_response.status_code == 200:
            challenge_id = create_response.json()["data"]["challenge"]["id"]
            
            # Submit empty response
            response = client.post(
                f"/api/challenges/{challenge_id}/response?user_id={self.student_id}",
                json={
                    "user_id": self.student_id,
                    "response": ""
                }
            )
            # Should fail validation
            assert response.status_code != 200

    def test_get_challenge_leaderboard(self):
        """Test getting challenge leaderboard."""
        # First create a challenge
        create_response = client.post(f"/api/challenges?user_id={self.teacher_id}", json={
            "ref": "SYD-LEADERBOARD-001",
            "question": "Explain NAT (Network Address Translation)",
            "matiere": "SYD",
            "date": "2024-06-10"
        })
        
        if create_response.status_code == 200:
            challenge_id = create_response.json()["data"]["challenge"]["id"]
            
            # Get leaderboard
            response = client.get(f"/api/challenges/{challenge_id}/leaderboard?user_id={self.student_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "leaderboard" in data["data"]

    def test_get_user_without_subscriptions(self):
        """Test getting today's challenge for user without subscriptions."""
        # Create user without subscriptions
        response = client.post("/api/users/register", json={
            "username": "no_subs_user",
            "email": "nosubs@test.com",
            "role": "student",
            "subscriptions": []
        })
        user_id = response.json()["data"]["user_id"]
        
        # Try to get today's challenge
        response = client.get(f"/api/challenges/today?user_id={user_id}")
        assert response.status_code == 200
        data = response.json()
        # Should return appropriate message about no subscriptions
        if not data["success"]:
            assert "abonnements" in data["message"].lower() or "subscription" in data["message"].lower() 