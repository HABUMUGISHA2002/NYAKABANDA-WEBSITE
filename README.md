# Nyakabanda Youth System

A modern Flask, MySQL, HTML, CSS, and vanilla JavaScript youth management system for Nyakabanda sector/youth organization.

## Features

- Registration, login, logout, password hashing, roles, forgot password page, and CSRF protection
- Dashboard statistics with JavaScript charts
- Youth member CRUD, search, profile photo uploads, CSV export
- Event creation, calendar-style listings, registration, and attendance status support
- Project/activity tracking with progress and uploads
- Announcements, feedback/contact storage, PDF monthly reports
- Responsive sidebar/navbar, dark/light mode, animations, cards, tables, and mobile layout

## Setup

1. Create and activate a virtual environment.
2. Install packages:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and update your MySQL credentials.
4. Create tables and an admin user:

```bash
python setup_database.py
```

5. Run the application:

```bash
python app.py
```

The app will be available at `http://127.0.0.1:5000`.
