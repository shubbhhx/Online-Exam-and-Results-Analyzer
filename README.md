# Web-Based Online Examination and Result Analytics System

A role-based online exam platform built with **Node.js, Express, MySQL, EJS, and Bootstrap**, featuring secure authentication, randomized question selection, descriptive answer evaluation, and performance analytics dashboards for **Admin, Teacher, and Student** users.

---

## 📌 Overview
This is a **localhost-only web application** with three roles:

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

## 🔐 Default Accounts
| Role | Email | Password |
|------|-------|----------|
| Admin | admin@college.edu | admin123 |
| Teacher | meera@college.edu | teacher123 |
| Student | amit@college.edu | student123 |

---

## ⚙️ Local Setup (Offline)

### 1️⃣ Install Requirements
- Install **Node.js (LTS)**  
- Install **MySQL** locally  

### 2️⃣ Install Dependencies
```bash
npm install
