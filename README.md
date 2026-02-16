# Web-Based Online Examination and Result Analytics System

A role-based online exam platform built with **Flask, MySQL, Jinja2, and Bootstrap**, featuring secure authentication, randomized question selection, descriptive answer evaluation, and performance analytics dashboards for **Admin, Teacher, and Student** users.

---

## Overview
This application supports three roles:

- **Admin** – manages courses, semesters, subjects, teachers, and students
- **Teacher** – creates questions, schedules exams, evaluates descriptive answers
- **Student** – attends exams, views results, and tracks performance

### Key Features
- Course → Semester → Subject hierarchy managed by Admin
- Auto-generated **Teacher IDs** and **Student Roll Numbers**
- Secure role-based authentication & dashboards
- Randomized MCQ selection + descriptive answer evaluation
- Performance analytics with charts (Chart.js)
- Student profile management and exam history

---

## Default Accounts
| Role | Email | Password |
|------|-------|----------|
| Admin | admin@college.edu | admin123 |
| Teacher | meera@college.edu | teacher123 |
| Student | amit@college.edu | student123 |

---

## Local Setup (Windows)

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
flask run
```

Set your environment variables in `.env` (copy from `.env.example`).

---

## Deployment (GitHub → Render → Railway MySQL)

### 1) Push to GitHub
- Initialize a repository, commit, and push this project to GitHub.

### 2) Create MySQL on Railway
- Create a Railway project with a MySQL database.
- Copy the `DATABASE_URL` (recommended) or set `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_PORT`.

### 3) Create a Render Web Service
- New Web Service → connect GitHub repo.
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Environment variables (Render dashboard):
  - `SESSION_SECRET=your_strong_secret`
  - `DATABASE_URL=...` (recommended)
  - `DB_SSL=true` (if Railway SSL is required)
  - `LOG_LEVEL=INFO`
  - `PORT` is set automatically by Render

### 4) Verify
- Open the Render logs and confirm the app starts without DB errors.

