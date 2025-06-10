# API Tests

This directory contains comprehensive tests for the Le Rhino API. The tests cover all major functionality including user management, document handling, challenges, evaluations, and more.

## Test Structure

### Test Files

- `test_auth_api.py` - User registration and subscription management tests
- `test_matieres_api.py` - Subject (matière) management tests  
- `test_documents_api.py` - Document upload, retrieval, and management tests
- `test_questions_api.py` - Question asking and reflection question generation tests
- `test_challenges_api.py` - Challenge creation, retrieval, and response submission tests
- `test_evaluations_api.py` - Response evaluation and feedback tests
- `test_leaderboard_api.py` - Leaderboard calculation tests
- `test_api_status.py` - General API status and functionality tests
- `test_users_api.py` - Legacy user management tests (original file)

### Configuration Files

- `conftest.py` - Shared pytest fixtures and configuration
- `pytest.ini` - Pytest configuration and test markers

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test File
```bash
pytest tests/test_auth_api.py
```

### Run Tests by Category
```bash
# Run only authentication tests
pytest -m auth

# Run only document management tests  
pytest -m documents

# Run only challenge tests
pytest -m challenges

# Run only permission/role tests
pytest -m permissions
```

### Run Tests with Coverage
```bash
pytest --cov=app --cov-report=html
```

### Run Tests Verbosely
```bash
pytest -v
```

### Run Specific Test Method
```bash
pytest tests/test_auth_api.py::TestUserRegistration::test_register_user_success
```

## Test Categories

### Authentication & User Management
- User registration with various data combinations
- Subscription management (update, retrieve, clear)
- Email uniqueness validation
- Role-based access control

### Subject Management  
- Listing available subjects
- Creating new subjects (teacher/admin only)
- Updating subject indexes
- Permission verification by role

### Document Management
- Document upload for different subjects
- File validation (empty files, supported formats)
- Document listing and retrieval
- Document deletion
- Content retrieval
- Bulk re-indexing
- Permission controls

### Questions & RAG
- Question asking with various complexity levels
- Context-aware question processing
- Reflection question generation
- Subject-specific question handling

### Challenges
- Today's challenge retrieval
- Challenge creation and management
- Response submission and validation
- Challenge filtering by subject
- User subscription-based challenge serving

### Evaluations
- Student response evaluation
- Multi-criteria evaluation
- Accuracy assessment
- Partial credit handling
- Subject-specific evaluation

### Leaderboards
- Leaderboard calculation for challenges
- Role-based access (teacher/admin only)
- Multiple subject support
- Error handling for non-existent challenges

### API Status & General
- API health and status endpoints
- Documentation accessibility
- Error handling and validation
- Response format consistency
- Performance testing

## Test Data Management

### Database Setup
Tests use a clean database for each test run:
- Removes existing `test.db`
- Copies `sample_data.db` to `test.db` for fresh start
- Each test function gets a clean database state

### Test Users
Common test users are created with different roles:
- **Student**: Has subscriptions to SYD and TCP subjects
- **Teacher**: Can create/manage content, has subject subscriptions  
- **Admin**: Full access to all functionality

### Sample Data
Tests include realistic sample data:
- Network engineering questions and concepts
- Proper challenge references (e.g., "SYD-001")
- Valid document content and metadata

## Best Practices

### Test Isolation
- Each test runs with a clean database
- Tests don't depend on other tests
- Setup and teardown handled automatically

### Error Testing
- Tests cover both success and failure scenarios
- Invalid input validation
- Permission denial testing
- Non-existent resource handling

### Realistic Data
- Tests use domain-appropriate data (networking concepts)
- Proper French/English mixed terminology
- Valid subject codes (SYD, TCP, etc.)

### Comprehensive Coverage
- All API endpoints tested
- Different user roles tested
- Edge cases and error conditions covered
- Input validation thoroughly tested

## Debugging Tests

### Run Single Test with Output
```bash
pytest tests/test_auth_api.py::TestUserRegistration::test_register_user_success -v -s
```

### Run with Python Debugger
```bash
pytest --pdb tests/test_auth_api.py::TestUserRegistration::test_register_user_success
```

### Check Test Coverage
```bash
pytest --cov=app --cov-report=term-missing
```

## Adding New Tests

When adding new API endpoints or functionality:

1. Create tests in the appropriate test file
2. Use existing fixtures from `conftest.py`
3. Follow naming conventions (`test_*`)
4. Add appropriate markers for categorization
5. Test both success and failure scenarios
6. Include permission/role testing where applicable

Example test structure:
```python
def test_new_endpoint_success(self):
    """Test successful operation."""
    response = client.post("/api/new-endpoint", json={"data": "value"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

def test_new_endpoint_forbidden(self):
    """Test permission denial."""
    response = client.post(f"/api/new-endpoint?user_id={self.student_id}")
    assert response.status_code == 403
``` 