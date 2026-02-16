# Web-Based Online Examination and Result Analytics System

## Overview
Localhost-only web application with Admin, Teacher, and Student roles. Built using Node.js, Express, MySQL, EJS, Bootstrap, and Chart.js.

Key features:
- Course → Semester → Subject hierarchy managed by Admin
- Auto-generated Teacher IDs and Student Roll Numbers
- Role-based dashboards with analytics and charts
- Student profile management and exam history

## Default Accounts
- Admin: admin@college.edu / admin123
- Teacher: meera@college.edu / teacher123
- Student: amit@college.edu / student123

## Local Setup (Offline)
1. Install Node.js (LTS) and MySQL locally.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Import database:
   - Create a database and seed data using:
     ```bash
     mysql -u root -p < database/online_exam_system.sql
     ```
4. Start the server:
   ```bash
   npm start
   ```
5. Open: http://localhost:3000

## Notes
- Update MySQL credentials in config/db.js if needed.
- Admin must create courses and semesters (with subjects) before assigning teachers or registering students.
- Teacher IDs are auto-generated in the format TCH-YYYY-XXX.
- Student roll numbers are auto-generated in the format YYYY-SEM{N}-XXX.
- Questions must be added by teachers before scheduling exams (40 MCQ + 10 descriptive).
