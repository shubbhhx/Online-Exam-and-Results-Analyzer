from datetime import datetime

from flask import Blueprint, redirect, render_template, request, session
from flask_login import current_user

from routes.helpers import get_db, role_required
from utils import clean_form


student_bp = Blueprint("student", __name__, url_prefix="/student")


@student_bp.route("/dashboard")
@role_required("student")
def dashboard():
    db = get_db()
    student = db.fetch_one(
        "SELECT st.*, c.name AS course_name, sem.semester_number, sem.title AS semester_title "
        "FROM students st "
        "JOIN courses c ON st.course_id = c.id "
        "JOIN semesters sem ON st.semester_id = sem.id "
        "WHERE st.id = %s",
        [current_user.id],
    )

    subjects = db.fetch_all(
        "SELECT s.id, s.name, c.name AS course_name, sem.semester_number "
        "FROM subjects s "
        "JOIN semesters sem ON s.semester_id = sem.id "
        "JOIN courses c ON sem.course_id = c.id "
        "WHERE s.semester_id = %s ORDER BY s.name",
        [student.get("semester_id") if student else None],
    )

    exams = db.fetch_all(
        "SELECT e.id, s.name AS subject_name, e.exam_date, e.duration_minutes, "
        "CASE WHEN r.id IS NULL THEN 'Not Started' ELSE r.status END AS status, r.id AS result_id "
        "FROM exams e "
        "JOIN subjects s ON e.subject_id = s.id "
        "LEFT JOIN results r ON r.exam_id = e.id AND r.student_id = %s "
        "WHERE s.semester_id = %s ORDER BY e.exam_date DESC",
        [current_user.id, student.get("semester_id") if student else None],
    )

    subject_perf = db.fetch_all(
        "SELECT s.name AS subject_name, r.percentage "
        "FROM results r JOIN subjects s ON r.subject_id = s.id "
        "WHERE r.student_id = %s",
        [current_user.id],
    )

    return render_template(
        "student/dashboard.html",
        title="Student Dashboard",
        student=student,
        subjects=subjects,
        exams=exams,
        pageLoading=True,
        subjectPerf=subject_perf,
    )


@student_bp.route("/exams/<int:exam_id>/start")
@role_required("student")
def start_exam(exam_id):
    db = get_db()
    exam = db.fetch_one(
        "SELECT e.*, s.name AS subject_name, s.semester_id FROM exams e JOIN subjects s ON e.subject_id = s.id WHERE e.id = %s",
        [exam_id],
    )

    if not exam:
        return redirect("/student/dashboard")

    student = db.fetch_one("SELECT * FROM students WHERE id = %s", [current_user.id])
    if not student or student.get("semester_id") != exam.get("semester_id"):
        return redirect("/student/dashboard")

    if exam.get("exam_date") and exam.get("exam_date") > datetime.now():
        return redirect("/student/dashboard")

    mcqs = db.fetch_all(
        "SELECT * FROM question_bank WHERE subject_id = %s AND question_type = 'MCQ' ORDER BY RAND() LIMIT 23",
        [exam.get("subject_id")],
    )
    descs = db.fetch_all(
        "SELECT * FROM question_bank WHERE subject_id = %s AND question_type = 'DESCRIPTIVE' ORDER BY RAND() LIMIT 2",
        [exam.get("subject_id")],
    )

    session["exam_questions"] = {
        "examId": exam.get("id"),
        "mcqIds": [q["id"] for q in mcqs],
        "descIds": [q["id"] for q in descs],
    }

    return render_template("student/exam.html", title="Exam", exam=exam, mcqs=mcqs, descs=descs)


@student_bp.route("/exams/<int:exam_id>/submit", methods=["POST"])
@role_required("student")
def submit_exam(exam_id):
    db = get_db()
    if not session.get("exam_questions") or session["exam_questions"].get("examId") != exam_id:
        return redirect("/student/dashboard")

    mcq_ids = session["exam_questions"].get("mcqIds", [])
    desc_ids = session["exam_questions"].get("descIds", [])

    total_marks = 0
    for question_id in mcq_ids:
        answer = request.form.get(f"mcq_{question_id}")
        question = db.fetch_one("SELECT correct_option FROM question_bank WHERE id = %s", [question_id])
        is_correct = question and answer == question.get("correct_option")
        marks = 1 if is_correct else 0
        total_marks += marks

        db.execute(
            "INSERT INTO student_answers (exam_id, student_id, question_id, question_type, answer_text, marks_awarded, evaluated) VALUES (%s, %s, %s, 'MCQ', %s, %s, 1)",
            [exam_id, current_user.id, question_id, answer or None, marks],
        )

    for question_id in desc_ids:
        answer = request.form.get(f"desc_{question_id}")
        db.execute(
            "INSERT INTO student_answers (exam_id, student_id, question_id, question_type, answer_text, marks_awarded, evaluated) VALUES (%s, %s, %s, 'DESCRIPTIVE', %s, 0, 0)",
            [exam_id, current_user.id, question_id, answer or None],
        )

    exam = db.fetch_one("SELECT subject_id FROM exams WHERE id = %s", [exam_id])

    db.execute(
        "INSERT INTO results (exam_id, student_id, subject_id, total_marks, percentage, status) VALUES (%s, %s, %s, %s, %s, %s)",
        [
            exam_id,
            current_user.id,
            (exam or {}).get("subject_id"),
            total_marks,
            round((float(total_marks) / 25) * 100, 2),
            "Pending",
        ],
    )

    session["exam_questions"] = None
    return redirect("/student/history?toast=Exam%20submitted&type=success")


@student_bp.route("/history")
@role_required("student")
def history():
    db = get_db()
    results = db.fetch_all(
        "SELECT r.id, s.name AS subject_name, r.total_marks, r.percentage, r.status "
        "FROM results r JOIN subjects s ON r.subject_id = s.id "
        "WHERE r.student_id = %s ORDER BY r.id DESC",
        [current_user.id],
    )

    toast = None
    if request.args.get("toast"):
        toast = {
            "type": request.args.get("type", "success"),
            "message": request.args.get("toast"),
        }

    return render_template("student/history.html", title="Exam History", results=results, toast=toast)


@student_bp.route("/results/<int:result_id>")
@role_required("student")
def result(result_id):
    db = get_db()
    result_item = db.fetch_one(
        "SELECT r.*, s.name AS subject_name FROM results r JOIN subjects s ON r.subject_id = s.id WHERE r.id = %s AND r.student_id = %s",
        [result_id, current_user.id],
    )

    if not result_item:
        return redirect("/student/history")

    return render_template("student/result.html", title="Result", result=result_item)


@student_bp.route("/analytics")
@role_required("student")
def analytics():
    db = get_db()
    subject_perf = db.fetch_all(
        "SELECT s.name AS subject_name, r.percentage "
        "FROM results r JOIN subjects s ON r.subject_id = s.id "
        "WHERE r.student_id = %s",
        [current_user.id],
    )

    return render_template("student/analytics.html", title="Performance Analytics", subjectPerf=subject_perf)


@student_bp.route("/profile")
@role_required("student")
def profile():
    db = get_db()
    student = db.fetch_one(
        "SELECT st.*, c.name AS course_name, sem.semester_number, sem.title AS semester_title "
        "FROM students st "
        "JOIN courses c ON st.course_id = c.id "
        "JOIN semesters sem ON st.semester_id = sem.id "
        "WHERE st.id = %s",
        [current_user.id],
    )

    toast = None
    if request.args.get("toast"):
        toast = {
            "type": request.args.get("type", "success"),
            "message": request.args.get("toast"),
        }

    return render_template(
        "student/profile.html",
        title="Student Profile",
        student=student,
        toast=toast,
    )


@student_bp.route("/profile", methods=["POST"])
@role_required("student")
def profile_post():
    db = get_db()
    form = clean_form(request.form)
    db.execute(
        "UPDATE students SET name = %s, email = %s, address = %s, phone = %s WHERE id = %s",
        [form.get("name"), form.get("email"), form.get("address") or None, form.get("phone") or None, current_user.id],
    )
    return redirect("/student/profile?toast=Profile%20updated&type=success")

