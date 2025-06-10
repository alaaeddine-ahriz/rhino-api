"""Tests for matieres (subjects) API routes."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestMatieresAPI:
    """Test matieres (subjects) management functionality."""

    def test_get_matieres_as_student(self, test_users):
        """Test getting matieres list as student."""
        student_id = test_users["student"]["id"]
        response = client.get(f"/api/matieres/?user_id={student_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "matieres" in data["data"]
        assert isinstance(data["data"]["matieres"], list)
        assert data["message"] == "Matières récupérées avec succès"

    def test_get_matieres_as_teacher(self, test_users):
        """Test getting matieres list as teacher."""
        teacher_id = test_users["teacher"]["id"]
        response = client.get(f"/api/matieres/?user_id={teacher_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "matieres" in data["data"]

    def test_get_matieres_as_admin(self, test_users):
        """Test getting matieres list as admin."""
        admin_id = test_users["admin"]["id"]
        response = client.get(f"/api/matieres/?user_id={admin_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_create_matiere_as_teacher(self, test_users):
        """Test creating a new matiere as teacher."""
        teacher_id = test_users["teacher"]["id"]
        response = client.post(f"/api/matieres/?user_id={teacher_id}", json={
            "name": "NEWMATH",
            "description": "New Mathematics Course"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "matiere" in data["data"]
        assert data["data"]["matiere"]["name"] == "NEWMATH"
        assert "créée avec succès" in data["message"]

    def test_create_matiere_as_admin(self, test_users):
        """Test creating a new matiere as admin."""
        admin_id = test_users["admin"]["id"]
        response = client.post(f"/api/matieres/?user_id={admin_id}", json={
            "name": "ADMINMATH",
            "description": "Admin Mathematics Course"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_create_matiere_as_student_forbidden(self, test_users):
        """Test that students cannot create matieres."""
        student_id = test_users["student"]["id"]
        response = client.post(f"/api/matieres/?user_id={student_id}", json={
            "name": "FORBIDDEN",
            "description": "Should not be allowed"
        })
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert "permission" in data["message"].lower()

    def test_update_matiere_as_teacher(self, test_users):
        """Test updating a matiere index as teacher."""
        teacher_id = test_users["teacher"]["id"]
        response = client.post(f"/api/matieres/update?user_id={teacher_id}", json={
            "matiere": "SYD"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["matiere"] == "SYD"
        assert data["data"]["updated"] is True
        assert "mise à jour avec succès" in data["message"]

    def test_update_matiere_as_admin(self, test_users):
        """Test updating a matiere index as admin."""
        admin_id = test_users["admin"]["id"]
        response = client.post(f"/api/matieres/update?user_id={admin_id}", json={
            "matiere": "TCP"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["updated"] is True

    def test_update_matiere_as_student_forbidden(self, test_users):
        """Test that students cannot update matieres."""
        student_id = test_users["student"]["id"]
        response = client.post(f"/api/matieres/update?user_id={student_id}", json={
            "matiere": "SYD"
        })
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert "permission" in data["message"].lower()

    def test_get_matieres_invalid_user(self, clean_database):
        """Test getting matieres with invalid user ID."""
        response = client.get("/api/matieres/?user_id=999999")
        # This should fail since user doesn't exist
        assert response.status_code != 200

    def test_create_matiere_invalid_data(self, test_users):
        """Test creating matiere with invalid data."""
        teacher_id = test_users["teacher"]["id"]
        response = client.post(f"/api/matieres/?user_id={teacher_id}", json={
            "name": "",  # Empty name
            "description": "Invalid matiere"
        })
        # Should fail validation
        assert response.status_code != 200

    def test_update_matiere_invalid_data(self, test_users):
        """Test updating matiere with invalid data."""
        teacher_id = test_users["teacher"]["id"]
        response = client.post(f"/api/matieres/update?user_id={teacher_id}", json={
            "matiere": ""  # Empty matiere name
        })
        # Should fail validation
        assert response.status_code != 200 