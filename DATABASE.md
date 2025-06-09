# Database Documentation

## Overview

This project uses SQLite for data storage. The database schema includes tables for users, subjects, challenges, and related data.

## Database Files

- **`test.db`** - Active/working database used by the application
- **`sample_data.db`** - Pre-populated database with sample data for testing and development

## Sample Data

The `sample_data.db` file contains:

### Subjects (4 total)
- **SYD** - Systèmes Distribués (granularité: semaine)
- **TCP** - Transmission Communication Protocol (granularité: semaine)  
- **MATH** - Mathématiques (granularité: jour)
- **PHYS** - Physique (granularité: semaine)

### Challenges (8 total)
- **3 SYD challenges** - About distributed systems, consistency, Raft consensus
- **3 TCP challenges** - About TCP protocol, flow control, TCP vs UDP
- **1 MATH challenge** - Differential equation solving
- **1 PHYS challenge** - Gravitational force calculation

### Users (5 total)
- **admin** (admin role) - subscribed to all subjects
- **teacher1** (teacher role) - subscribed to SYD, TCP
- **student1** (student role) - subscribed to SYD
- **student2** (student role) - subscribed to TCP  
- **student3** (student role) - subscribed to SYD, TCP

### Authentication Tokens
Pre-configured tokens for testing:
- `admin_token_999` (admin user)
- `teacher_token_888` (teacher1 user)
- `student1_token_777` (student1 user)
- `student2_token_666` (student2 user)
- `student3_token_555` (student3 user)

## Usage

### Using Sample Data

To load the sample data into your working database:

```bash
# Copy sample database to active database
cp sample_data.db test.db

# Or use the utility script
PYTHONPATH=. python app/db/sample_data.py --copy-sample
```

### Database Management Commands

```bash
# Initialize empty database (create tables)
PYTHONPATH=. python app/db/init_db.py

# Show current database contents
PYTHONPATH=. python app/db/sample_data.py

# Clear all data from active database
PYTHONPATH=. python app/db/sample_data.py --clear

# Copy sample data to active database
PYTHONPATH=. python app/db/sample_data.py --copy-sample

# Show help
PYTHONPATH=. python app/db/sample_data.py --help
```

### Testing API Endpoints

With sample data loaded, you can test API endpoints:

```bash
# List all challenges
curl -X 'GET' 'http://localhost:8000/api/challenges' \
  -H 'Authorization: Bearer admin_token_999'

# List challenges for SYD subject
curl -X 'GET' 'http://localhost:8000/api/challenges?matiere=SYD' \
  -H 'Authorization: Bearer admin_token_999'

# Get challenge for a subject (distributed system)
curl -X 'GET' 'http://localhost:8000/api/challenges/next?matiere=SYD' \
  -H 'Authorization: Bearer admin_token_999'
```

## Database Schema

The main tables are:

- **`user`** - User accounts and roles
- **`matiere`** - Subjects/courses  
- **`challenge`** - Questions/challenges for subjects
- **`challengeserved`** - Tracking which challenges have been served
- **`token`** - Authentication tokens
- **`leaderboardentry`** - User scores and rankings

## Development Workflow

1. **For testing**: Use `cp sample_data.db test.db` to get consistent test data
2. **For development**: Start with empty database using `python app/db/init_db.py`
3. **For production**: Initialize empty database and let users populate data

## File Management

- Keep `sample_data.db` as the reference sample database (don't modify)
- `test.db` is the working database (can be overwritten/reset)
- Both files are in `.gitignore` to avoid conflicts 