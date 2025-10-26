# Chicken Singer

A FastAPI web application that transforms audio files into "chicken" versions using an external ML worker service.

## Overview

Chicken Singer allows users to upload songs (MP3/WAV format, up to 45 seconds) which are then processed by an external worker service to create "chicken" versions. The app includes user authentication, job tracking, and integration with S3-compatible object storage.

## Recent Changes

- **2025-10-26**: Initial project setup
  - Created FastAPI backend with SQLModel ORM
  - Set up PostgreSQL database connection
  - Implemented user authentication with bcrypt and session management
  - Created admin panel for user management
  - Built job queue system for audio processing
  - Integrated S3 storage for audio files
  - Added responsive UI with chicken-themed design

## Project Architecture

### Backend Structure
- **main.py** - FastAPI application with routes and endpoints
- **models.py** - SQLModel database models (User, Job)
- **auth.py** - Authentication utilities (password hashing, session management)
- **s3utils.py** - S3/object storage integration

### Frontend Structure
- **templates/** - Jinja2 HTML templates
  - base.html - Base template with header/footer
  - index.html - Home page with job submission and history
  - login.html - Login page
  - admin_users.html - Admin panel for user management
- **static/style.css** - Custom CSS styling

### Database Models

**User Table:**
- id (primary key)
- email (unique, indexed)
- password_hash
- role (user/admin)
- is_active
- created_at

**Job Table:**
- id (primary key)
- user_id (indexed)
- status (queued/processing/done/error)
- input_filename
- input_duration_sec
- output_s3_url
- error_message
- created_at
- completed_at

## Environment Variables

### Required Secrets
- `SESSION_SECRET` - Session encryption key for cookie signing
- `DATABASE_URL` - PostgreSQL connection string (auto-configured by Replit)
- `WORKER_URL` - External ML worker endpoint URL
- `WORKER_API_KEY` - API key for worker authentication

### S3 Storage (Optional)
- `S3_BUCKET` - S3 bucket name
- `S3_REGION` - AWS region
- `S3_KEY` - AWS access key ID
- `S3_SECRET` - AWS secret access key

## Default Admin Account

Email: `admin@chickensinger.com`  
Password: `admin123`

**Important:** Change this password in production!

## Features

### User Features
- Email/password authentication with secure sessions
- Upload audio files (MP3/WAV, ≤45 seconds)
- View job processing status
- Download processed "chicken" songs
- View complete job history

### Admin Features
- Create new user accounts
- Manage user roles (user/admin)
- View all users in the system

### Technical Features
- PostgreSQL database with SQLModel ORM
- Secure password hashing with bcrypt
- Session-based authentication with signed cookies
- Asynchronous job processing via external worker
- S3-compatible object storage integration
- Responsive card-based UI design
- Error handling and status tracking

## Development

The server runs on port 5000 and is configured to restart automatically when code changes are detected.

### Running Locally
```bash
uvicorn main:app --host 0.0.0.0 --port 5000
```

### Database
The application uses PostgreSQL in production (via DATABASE_URL) with automatic table creation on startup.

## External Worker Integration

The application expects a worker service with the following API:

**Endpoint:** `POST /infer`  
**Headers:** `X-API-Key: <WORKER_API_KEY>`  
**Body:** multipart/form-data
- `job_id` - Job identifier
- `user_id` - User identifier
- `s3_prefix` - S3 key prefix for output
- `audio` - Audio file

**Expected Response:**
```json
{
  "ok": true,
  "output_s3_url": "https://...",
  "duration_sec": 30.5
}
```

## Future Enhancements

- Real-time job status updates (WebSockets/polling)
- Audio preview player in browser
- Job cancellation and retry functionality
- Usage analytics dashboard for admins
- Batch processing for multiple files
- User password reset functionality
- Email notifications for completed jobs
