"""Tests for questions API routes."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestQuestionsAPI:
    """Test questions management functionality."""

    def setup_method(self):
        """Set up test users."""
        # Create student user
        response = client.post("/api/users/register", json={
            "username": "question_student",
            "email": "qstudent@test.com",
            "role": "student",
            "subscriptions": ["SYD", "TCP"]
        })
        self.student_id = response.json()["data"]["user_id"]
        
        # Create teacher user
        response = client.post("/api/users/register", json={
            "username": "question_teacher",
            "email": "qteacher@test.com",
            "role": "teacher",
            "subscriptions": ["SYD", "TCP"]
        })
        self.teacher_id = response.json()["data"]["user_id"]

    def test_ask_question_as_student(self):
        """Test asking a question as student."""
        response = client.post(f"/api/question?user_id={self.student_id}", json={
            "query": "What is the OSI model in networking?",
            "matiere": "SYD",
            "context": "networking fundamentals"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "user_info" in data["data"]
        assert data["data"]["user_info"]["user_id"] == str(self.student_id)

    def test_ask_question_as_teacher(self):
        """Test asking a question as teacher."""
        response = client.post(f"/api/question?user_id={self.teacher_id}", json={
            "query": "Explain the TCP handshake process",
            "matiere": "TCP",
            "context": "transport layer protocols"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "user_info" in data["data"]
        assert data["data"]["user_info"]["user_id"] == str(self.teacher_id)

    def test_ask_question_minimal_data(self):
        """Test asking question with minimal required data."""
        response = client.post(f"/api/question?user_id={self.student_id}", json={
            "query": "What is HTTP?",
            "matiere": "SYD"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_ask_question_invalid_user(self):
        """Test asking question with invalid user."""
        response = client.post("/api/question?user_id=999999", json={
            "query": "Test question",
            "matiere": "SYD"
        })
        assert response.status_code != 200

    def test_ask_question_empty_query(self):
        """Test asking question with empty query."""
        response = client.post(f"/api/question?user_id={self.student_id}", json={
            "query": "",
            "matiere": "SYD"
        })
        # Should fail validation
        assert response.status_code != 200

    def test_ask_question_invalid_matiere(self):
        """Test asking question with invalid matiere."""
        response = client.post(f"/api/question?user_id={self.student_id}", json={
            "query": "Test question",
            "matiere": ""
        })
        # Should fail validation
        assert response.status_code != 200

    def test_generate_reflection_question_as_student(self):
        """Test generating reflection question as student."""
        response = client.post(f"/api/question/reflection?user_id={self.student_id}", json={
            "matiere": "SYD",
            "concept_cle": "OSI model layers"
        })
        assert response.status_code == 200
        data = response.json()
        # Note: The response format might vary based on implementation
        # Check for basic structure
        assert "success" in data
        if data["success"]:
            assert "user_info" in data["data"]
            assert data["data"]["user_info"]["user_id"] == str(self.student_id)

    def test_generate_reflection_question_as_teacher(self):
        """Test generating reflection question as teacher."""
        response = client.post(f"/api/question/reflection?user_id={self.teacher_id}", json={
            "matiere": "TCP",
            "concept_cle": "TCP congestion control"
        })
        assert response.status_code == 200
        data = response.json()
        assert "success" in data

    def test_generate_reflection_question_minimal_data(self):
        """Test generating reflection question with minimal data."""
        response = client.post(f"/api/question/reflection?user_id={self.student_id}", json={
            "matiere": "SYD",
            "concept_cle": "routing"
        })
        assert response.status_code == 200

    def test_generate_reflection_question_invalid_user(self):
        """Test generating reflection question with invalid user."""
        response = client.post("/api/question/reflection?user_id=999999", json={
            "matiere": "SYD",
            "concept_cle": "test concept"
        })
        assert response.status_code != 200

    def test_generate_reflection_question_empty_concept(self):
        """Test generating reflection question with empty concept."""
        response = client.post(f"/api/question/reflection?user_id={self.student_id}", json={
            "matiere": "SYD",
            "concept_cle": ""
        })
        # Should fail validation
        assert response.status_code != 200

    def test_generate_reflection_question_empty_matiere(self):
        """Test generating reflection question with empty matiere."""
        response = client.post(f"/api/question/reflection?user_id={self.student_id}", json={
            "matiere": "",
            "concept_cle": "test concept"
        })
        # Should fail validation
        assert response.status_code != 200

    def test_ask_complex_question(self):
        """Test asking a more complex question."""
        response = client.post(f"/api/question?user_id={self.teacher_id}", json={
            "query": "Compare and contrast the advantages and disadvantages of TCP versus UDP protocols in terms of reliability, performance, and use cases. Provide specific examples of applications that would benefit from each protocol.",
            "matiere": "TCP",
            "context": "Advanced transport layer protocols comparison for network engineering course"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_generate_reflection_advanced_concept(self):
        """Test generating reflection question for advanced concept."""
        response = client.post(f"/api/question/reflection?user_id={self.teacher_id}", json={
            "matiere": "SYD",
            "concept_cle": "Software Defined Networking (SDN) architecture and OpenFlow protocol"
        })
        assert response.status_code == 200
        data = response.json()
        assert "success" in data 