# Mail System - Challenge Email Distribution

This folder contains the essential components for sending challenge emails to students.

## Core Files

### Essential Components
- **`test_step_by_step.py`** - Complete step-by-step test with reply waiting and evaluation
- **`send_questions.py`** - Core email sending functionality 
- **`email_reader.py`** - Email reply reading and monitoring
- **`evaluator.py`** - Response evaluation system
- **`database_utils.py`** - Database utilities for user management
- **`config.py`** - Email configuration settings
- **`utils.py`** - Utility functions for conversation tracking
- **`conversations.json`** - Data file tracking sent emails and responses

## Quick Start

1. **Configure email settings** in `.env` file:
   ```
   EMAIL=your-email@gmail.com
   PASSWORD=your-app-password
   ```

2. **Run the step-by-step test** (now includes reply waiting and evaluation):
   ```bash
   cd mail
   python test_step_by_step.py
   ```
   
   The test will:
   - Send a challenge email to a student
   - Optionally wait for the student's reply
   - Display the received response
   - Automatically evaluate the response
   - Send detailed feedback email **as a reply** in the same email thread

3. **Send a challenge to a specific user**:
   ```python
   from send_questions import send_question_from_api
   success = send_question_from_api(to="student@email.com", user_id=6)
   ```

## Key Functions

- `send_question_from_api(to, user_id)` - Send today's challenge to a user
- `get_challenge_from_api(user_id)` - Retrieve challenge data from API
- `get_student_by_id(user_id)` - Get student info from database
- `wait_for_reply(email, timeout_minutes)` - Wait for email reply from user
- `evaluate_and_display(question, response, matiere)` - Evaluate student response
- `send_feedback_email(email, evaluation, question, response, original_email)` - Send evaluation feedback as email reply

## Requirements

Make sure these dependencies are installed:
- `yagmail` - for sending emails
- `requests` - for API communication
- `python-dotenv` - for environment variables

## Key Features

### 🔗 **Email Thread Continuity**
The feedback is sent **as a reply** to the student's response email, maintaining the conversation thread:
- Uses `In-Reply-To` and `References` headers
- Subject prefixed with "Re:" 
- Same discussion thread from question → response → feedback

### 📧 **Email Flow Example**
1. **Question sent:** `Subject: 🧠 Question du jour - TCP`
2. **Student replies:** `Subject: Re: 🧠 Question du jour - TCP`  
3. **Feedback sent:** `Subject: Re: 🧠 Question du jour - TCP - 📊 Note: B (75/100)`

## Usage Example

```python
# Send today's challenge to user ID 8
from send_questions import send_question_from_api

success = send_question_from_api(
    to="student@example.com", 
    user_id=8
)
``` 