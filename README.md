# Quiz Master

A modern, full-featured **online quiz platform** built with **Python Flask**, **SQLite**, **Bootstrap 5**, and **Chart.js**.

Admins can create and manage subjects, chapters, timed MCQ quizzes, and single-correct-answer questions.  
Users can register, attempt quizzes, view scores, track performance with beautiful charts, and browse available tests.

Perfect for schools, coaching centers, self-learners, certification prep, or internal training.

## Features

### Admin Panel
- Create/edit/delete **subjects** and **chapters**
- Add/edit/delete **quizzes** with title, duration, scheduled date
- Add/edit/delete **MCQ questions** (4 options, single correct answer)
- Responsive dashboard with summary statistics
- Secure role-based access

### User Experience
- Register/login with email
- View **available quizzes** (upcoming & not attempted)
- Attempt **timed quizzes** with countdown timer
- Instant score calculation on submission
- Detailed **score history** and **performance charts** (pie, bar, line)
- Clean, mobile-responsive UI

### Tech Stack
- Backend: Flask + Flask-SQLAlchemy + Flask-Login
- Database: SQLite (easy to deploy & portable)
- Frontend: Jinja2 + Bootstrap 5 + Bootstrap Icons
- Charts: Chart.js (v4)
- Password hashing: Werkzeug
- Role-based access control

## Installation & Setup

### Prerequisites
- Python 3.8+
- pip
- Git (optional)
