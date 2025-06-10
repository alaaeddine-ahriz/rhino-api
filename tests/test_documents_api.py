"""Tests for documents API routes."""
import pytest
from fastapi.testclient import TestClient
from io import BytesIO
from app.main import app

client = TestClient(app)


class TestDocumentsAPI:
    """Test documents management functionality."""

    def setup_method(self):
        """Set up test users and test data."""
        # Create student user
        response = client.post("/api/users/register", json={
            "username": "doc_student",
            "email": "docstudent@test.com",
            "role": "student",
            "subscriptions": ["SYD"]
        })
        self.student_id = response.json()["data"]["user_id"]
        
        # Create teacher user
        response = client.post("/api/users/register", json={
            "username": "doc_teacher",
            "email": "docteacher@test.com",
            "role": "teacher",
            "subscriptions": ["SYD", "TCP"]
        })
        self.teacher_id = response.json()["data"]["user_id"]
        
        # Create admin user
        response = client.post("/api/users/register", json={
            "username": "doc_admin",
            "email": "docadmin@test.com",
            "role": "admin",
            "subscriptions": []
        })
        self.admin_id = response.json()["data"]["user_id"]

    def test_get_documents_as_student(self):
        """Test getting documents list as student."""
        response = client.get(f"/api/matieres/SYD/documents?user_id={self.student_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "documents" in data["data"]
        assert "count" in data["data"]
        assert isinstance(data["data"]["documents"], list)

    def test_get_documents_as_teacher(self):
        """Test getting documents list as teacher."""
        response = client.get(f"/api/matieres/TCP/documents?user_id={self.teacher_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "documents" in data["data"]

    def test_get_documents_invalid_user(self):
        """Test getting documents with invalid user."""
        response = client.get("/api/matieres/SYD/documents?user_id=999999")
        assert response.status_code != 200

    def test_upload_document_as_teacher(self):
        """Test uploading document as teacher."""
        # Create a test file
        test_content = b"This is a test document content for SYD course."
        test_file = ("test_document.txt", BytesIO(test_content), "text/plain")
        
        response = client.post(
            f"/api/matieres/SYD/documents?user_id={self.teacher_id}",
            files={"file": test_file},
            data={"is_exam": "false"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "document" in data["data"]
        assert data["data"]["matiere"] == "SYD"

    def test_upload_document_as_admin(self):
        """Test uploading document as admin."""
        test_content = b"Admin uploaded document for TCP course."
        test_file = ("admin_document.txt", BytesIO(test_content), "text/plain")
        
        response = client.post(
            f"/api/matieres/TCP/documents?user_id={self.admin_id}",
            files={"file": test_file},
            data={"is_exam": "true"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_upload_document_as_student_forbidden(self):
        """Test that students cannot upload documents."""
        test_content = b"Student should not be able to upload this."
        test_file = ("forbidden.txt", BytesIO(test_content), "text/plain")
        
        response = client.post(
            f"/api/matieres/SYD/documents?user_id={self.student_id}",
            files={"file": test_file},
            data={"is_exam": "false"}
        )
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert "permission" in data["message"].lower()

    def test_upload_empty_document(self):
        """Test uploading an empty document."""
        test_file = ("empty.txt", BytesIO(b""), "text/plain")
        
        response = client.post(
            f"/api/matieres/SYD/documents?user_id={self.teacher_id}",
            files={"file": test_file},
            data={"is_exam": "false"}
        )
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "empty" in data["message"].lower()

    def test_delete_document_as_teacher(self):
        """Test deleting document as teacher."""
        # First upload a document
        test_content = b"Document to be deleted."
        test_file = ("to_delete.txt", BytesIO(test_content), "text/plain")
        
        upload_response = client.post(
            f"/api/matieres/SYD/documents?user_id={self.teacher_id}",
            files={"file": test_file},
            data={"is_exam": "false"}
        )
        
        if upload_response.status_code == 200:
            document_id = upload_response.json()["data"]["document"]["id"]
            
            # Now delete it
            delete_response = client.delete(
                f"/api/matieres/SYD/documents/{document_id}?user_id={self.teacher_id}"
            )
            assert delete_response.status_code == 200
            data = delete_response.json()
            assert data["success"] is True

    def test_delete_document_as_student_forbidden(self):
        """Test that students cannot delete documents."""
        response = client.delete(
            f"/api/matieres/SYD/documents/fake_id?user_id={self.student_id}"
        )
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert "permission" in data["message"].lower()

    def test_delete_nonexistent_document(self):
        """Test deleting a non-existent document."""
        response = client.delete(
            f"/api/matieres/SYD/documents/nonexistent_id?user_id={self.teacher_id}"
        )
        # Should return 404 or 400 depending on implementation
        assert response.status_code in [400, 404]

    def test_get_document_content(self):
        """Test getting document content."""
        # First upload a document
        test_content = b"Content to retrieve."
        test_file = ("content_test.txt", BytesIO(test_content), "text/plain")
        
        upload_response = client.post(
            f"/api/matieres/SYD/documents?user_id={self.teacher_id}",
            files={"file": test_file},
            data={"is_exam": "false"}
        )
        
        if upload_response.status_code == 200:
            document_id = upload_response.json()["data"]["document"]["id"]
            
            # Get document content
            content_response = client.get(
                f"/api/matieres/SYD/documents/{document_id}/content?user_id={self.student_id}"
            )
            assert content_response.status_code == 200
            data = content_response.json()
            assert data["success"] is True
            assert "content" in data["data"]

    def test_reindex_documents_as_teacher(self):
        """Test reindexing documents as teacher."""
        response = client.post(
            f"/api/matieres/SYD/documents/reindex?user_id={self.teacher_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "processed_count" in data["data"]
        assert "success_count" in data["data"]
        assert "failed_count" in data["data"]

    def test_reindex_documents_as_student_forbidden(self):
        """Test that students cannot reindex documents."""
        response = client.post(
            f"/api/matieres/SYD/documents/reindex?user_id={self.student_id}"
        )
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert "permission" in data["message"].lower() 