"""Tests for evaluations API routes."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestEvaluationsAPI:
    """Test evaluations functionality."""

    def setup_method(self):
        """Set up test users."""
        # Create student user
        response = client.post("/api/users/register", json={
            "username": "eval_student",
            "email": "evalstudent@test.com",
            "role": "student",
            "subscriptions": ["SYD", "TCP"]
        })
        self.student_id = response.json()["data"]["user_id"]
        
        # Create teacher user
        response = client.post("/api/users/register", json={
            "username": "eval_teacher",
            "email": "evalteacher@test.com",
            "role": "teacher",
            "subscriptions": ["SYD", "TCP"]
        })
        self.teacher_id = response.json()["data"]["user_id"]

    def test_evaluate_response_as_student(self):
        """Test evaluating a response as student."""
        response = client.post(f"/api/evaluation/response?user_id={self.student_id}", json={
            "question": "What is the OSI model and how many layers does it have?",
            "reponse_etudiant": "The OSI model is a conceptual framework with 7 layers: Physical, Data Link, Network, Transport, Session, Presentation, and Application.",
            "reponse_attendue": "The OSI (Open Systems Interconnection) model is a conceptual framework that standardizes network communication into 7 layers.",
            "matiere": "SYD",
            "criteres": ["accuracy", "completeness", "clarity"]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "user_info" in data["data"]
        assert data["data"]["user_info"]["user_id"] == str(self.student_id)

    def test_evaluate_response_as_teacher(self):
        """Test evaluating a response as teacher."""
        response = client.post(f"/api/evaluation/response?user_id={self.teacher_id}", json={
            "question": "Explain the TCP three-way handshake process.",
            "reponse_etudiant": "TCP handshake involves SYN, SYN-ACK, and ACK packets to establish a connection.",
            "reponse_attendue": "The TCP three-way handshake consists of: 1) Client sends SYN, 2) Server responds with SYN-ACK, 3) Client sends ACK to establish connection.",
            "matiere": "TCP",
            "criteres": ["technical_accuracy", "step_by_step_explanation"]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "user_info" in data["data"]
        assert data["data"]["user_info"]["user_id"] == str(self.teacher_id)

    def test_evaluate_response_minimal_data(self):
        """Test evaluating response with minimal required data."""
        response = client.post(f"/api/evaluation/response?user_id={self.student_id}", json={
            "question": "What is HTTP?",
            "reponse_etudiant": "HTTP is HyperText Transfer Protocol.",
            "reponse_attendue": "HTTP is a protocol for transferring web content.",
            "matiere": "SYD"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_evaluate_response_with_criteria(self):
        """Test evaluating response with specific criteria."""
        response = client.post(f"/api/evaluation/response?user_id={self.teacher_id}", json={
            "question": "Describe the differences between TCP and UDP.",
            "reponse_etudiant": "TCP is reliable and connection-oriented, UDP is fast but unreliable.",
            "reponse_attendue": "TCP provides reliable, ordered delivery with error checking and flow control, while UDP is faster but provides no guarantees.",
            "matiere": "TCP",
            "criteres": [
                "technical_accuracy",
                "comparison_quality", 
                "use_case_understanding",
                "protocol_characteristics"
            ]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_evaluate_response_invalid_user(self):
        """Test evaluating response with invalid user."""
        response = client.post("/api/evaluation/response?user_id=999999", json={
            "question": "Test question",
            "reponse_etudiant": "Test answer",
            "reponse_attendue": "Expected answer",
            "matiere": "SYD"
        })
        assert response.status_code != 200

    def test_evaluate_response_empty_question(self):
        """Test evaluating response with empty question."""
        response = client.post(f"/api/evaluation/response?user_id={self.student_id}", json={
            "question": "",
            "reponse_etudiant": "Some answer",
            "reponse_attendue": "Expected answer",
            "matiere": "SYD"
        })
        # Should fail validation
        assert response.status_code != 200

    def test_evaluate_response_empty_student_answer(self):
        """Test evaluating response with empty student answer."""
        response = client.post(f"/api/evaluation/response?user_id={self.student_id}", json={
            "question": "What is DNS?",
            "reponse_etudiant": "",
            "reponse_attendue": "DNS is Domain Name System",
            "matiere": "SYD"
        })
        # Should fail validation
        assert response.status_code != 200

    def test_evaluate_response_empty_expected_answer(self):
        """Test evaluating response with empty expected answer."""
        response = client.post(f"/api/evaluation/response?user_id={self.student_id}", json={
            "question": "What is DNS?",
            "reponse_etudiant": "DNS translates domain names to IP addresses",
            "reponse_attendue": "",
            "matiere": "SYD"
        })
        # Should fail validation
        assert response.status_code != 200

    def test_evaluate_response_invalid_matiere(self):
        """Test evaluating response with invalid matiere."""
        response = client.post(f"/api/evaluation/response?user_id={self.student_id}", json={
            "question": "Test question",
            "reponse_etudiant": "Test answer",
            "reponse_attendue": "Expected answer",
            "matiere": ""
        })
        # Should fail validation
        assert response.status_code != 200

    def test_evaluate_complex_response(self):
        """Test evaluating a complex technical response."""
        response = client.post(f"/api/evaluation/response?user_id={self.teacher_id}", json={
            "question": "Explain how BGP (Border Gateway Protocol) works and why it's critical for internet routing. Include discussion of AS (Autonomous Systems) and route advertisement.",
            "reponse_etudiant": "BGP is a path vector protocol used between autonomous systems. Each AS has a unique number and BGP routers exchange routing information. BGP uses TCP port 179 and maintains session state. It advertises network prefixes and AS paths to prevent loops.",
            "reponse_attendue": "BGP is the internet's routing protocol that operates between Autonomous Systems (AS). It's a path vector protocol that prevents loops by including the full AS path. BGP speakers exchange route advertisements via TCP connections, maintaining routing tables and implementing policies for route selection and advertisement.",
            "matiere": "SYD",
            "criteres": [
                "protocol_understanding",
                "autonomous_systems_concept",
                "loop_prevention_mechanism",
                "route_advertisement_process",
                "technical_accuracy",
                "depth_of_explanation"
            ]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_evaluate_incorrect_response(self):
        """Test evaluating an incorrect response."""
        response = client.post(f"/api/evaluation/response?user_id={self.student_id}", json={
            "question": "What port does HTTPS use?",
            "reponse_etudiant": "HTTPS uses port 80 like HTTP.",
            "reponse_attendue": "HTTPS uses port 443 for secure web communications.",
            "matiere": "SYD",
            "criteres": ["factual_accuracy", "protocol_knowledge"]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # The evaluation should detect the incorrect information

    def test_evaluate_partial_response(self):
        """Test evaluating a partially correct response."""
        response = client.post(f"/api/evaluation/response?user_id={self.student_id}", json={
            "question": "List the first four layers of the OSI model and their functions.",
            "reponse_etudiant": "1. Physical layer - handles electrical signals. 2. Data Link layer - frames and error detection.",
            "reponse_attendue": "1. Physical - electrical/optical transmission, 2. Data Link - framing and error detection, 3. Network - routing and addressing, 4. Transport - end-to-end delivery and flow control.",
            "matiere": "SYD",
            "criteres": ["completeness", "accuracy", "layer_understanding"]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_evaluate_response_different_subjects(self):
        """Test evaluating responses for different subjects."""
        # Test SYD subject
        syd_response = client.post(f"/api/evaluation/response?user_id={self.student_id}", json={
            "question": "What is subnetting?",
            "reponse_etudiant": "Subnetting divides a network into smaller subnetworks.",
            "reponse_attendue": "Subnetting is the practice of dividing a network into smaller subnetworks to improve performance and security.",
            "matiere": "SYD"
        })
        assert syd_response.status_code == 200
        
        # Test TCP subject
        tcp_response = client.post(f"/api/evaluation/response?user_id={self.student_id}", json={
            "question": "What is flow control in TCP?",
            "reponse_etudiant": "Flow control prevents the sender from overwhelming the receiver.",
            "reponse_attendue": "Flow control in TCP uses the sliding window mechanism to prevent the sender from transmitting data faster than the receiver can process it.",
            "matiere": "TCP"
        })
        assert tcp_response.status_code == 200 