from flask import Blueprint, redirect, render_template, request
from flask_login import current_user

from routes.helpers import get_db, role_required
from utils import clean_form


teacher_bp = Blueprint("teacher", __name__, url_prefix="/teacher")


@teacher_bp.route("/dashboard")
@role_required("teacher")
def dashboard():
    db = get_db()
    subjects = db.fetch_all(
        "SELECT s.id, s.name, c.name AS course_name, sem.semester_number, "
        "COALESCE(SUM(CASE WHEN q.question_type = 'MCQ' THEN 1 END), 0) AS mcq_count, "
        "COALESCE(SUM(CASE WHEN q.question_type = 'DESCRIPTIVE' THEN 1 END), 0) AS desc_count "
        "FROM teacher_subjects ts "
        "JOIN subjects s ON ts.subject_id = s.id "
        "JOIN semesters sem ON s.semester_id = sem.id "
        "JOIN courses c ON sem.course_id = c.id "
        "LEFT JOIN question_bank q ON q.subject_id = s.id AND q.teacher_id = ts.teacher_id "
        "WHERE ts.teacher_id = %s "
        "GROUP BY s.id, s.name, c.name, sem.semester_number "
        "ORDER BY s.name",
        [current_user.id],
    )
    pending = db.fetch_one(
        "SELECT COUNT(*) AS count FROM student_answers sa "
        "JOIN exams e ON sa.exam_id = e.id "
        "WHERE sa.question_type = 'DESCRIPTIVE' AND sa.evaluated = 0 AND e.teacher_id = %s",
        [current_user.id],
    )

    return render_template(
        "teacher/dashboard.html",
        title="Teacher Dashboard",
        subjects=subjects,
        pendingEvaluations=pending.get("count", 0) if pending else 0,
        pageLoading=True,
    )


@teacher_bp.route("/subjects")
@role_required("teacher")
def subjects():
    db = get_db()
    subjects_list = db.fetch_all(
        "SELECT s.id, s.name, c.name AS course_name, sem.semester_number "
        "FROM teacher_subjects ts "
        "JOIN subjects s ON ts.subject_id = s.id "
        "JOIN semesters sem ON s.semester_id = sem.id "
        "JOIN courses c ON sem.course_id = c.id "
        "WHERE ts.teacher_id = %s",
        [current_user.id],
    )
    return render_template("teacher/subjects.html", title="Assigned Subjects", subjects=subjects_list)


@teacher_bp.route("/questions")
@role_required("teacher")
def questions():
    db = get_db()
    subjects_list = db.fetch_all(
        "SELECT s.id, s.name "
        "FROM teacher_subjects ts JOIN subjects s ON ts.subject_id = s.id "
        "WHERE ts.teacher_id = %s",
        [current_user.id],
    )

    questions_list = db.fetch_all(
        "SELECT q.*, s.name AS subject_name "
        "FROM question_bank q JOIN subjects s ON q.subject_id = s.id "
        "WHERE q.teacher_id = %s ORDER BY q.id DESC",
        [current_user.id],
    )

    return render_template(
        "teacher/questions.html",
        title="Question Bank",
        subjects=subjects_list,
        questions=questions_list,
        error=request.args.get("error"),
    )


@teacher_bp.route("/questions/<int:question_id>/edit")
@role_required("teacher")
def question_edit(question_id):
    db = get_db()
    question = db.fetch_one(
        "SELECT q.*, s.name AS subject_name FROM question_bank q JOIN subjects s ON q.subject_id = s.id WHERE q.id = %s AND q.teacher_id = %s",
        [question_id, current_user.id],
    )

    if not question:
        return redirect("/teacher/questions")

    return render_template("teacher/question_edit.html", title="Edit Question", question=question)


@teacher_bp.route("/questions", methods=["POST"])
@role_required("teacher")
def create_question():
    db = get_db()
    form = clean_form(request.form)

    counts = db.fetch_all(
        "SELECT question_type, COUNT(*) AS count FROM question_bank WHERE subject_id = %s GROUP BY question_type",
        [form.get("subject_id")],
    )

    mcq_count = next((row["count"] for row in counts if row["question_type"] == "MCQ"), 0)
    desc_count = next((row["count"] for row in counts if row["question_type"] == "DESCRIPTIVE"), 0)

    if form.get("question_type") == "MCQ" and mcq_count >= 40:
        return redirect("/teacher/questions?error=MCQ%20limit%20reached")

    if form.get("question_type") == "DESCRIPTIVE" and desc_count >= 10:
        return redirect("/teacher/questions?error=Descriptive%20limit%20reached")

    db.execute(
        "INSERT INTO question_bank (subject_id, teacher_id, question_type, question_text, option_a, option_b, option_c, option_d, correct_option) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        [
            form.get("subject_id"),
            current_user.id,
            form.get("question_type"),
            form.get("question_text"),
            form.get("option_a") or None,
            form.get("option_b") or None,
            form.get("option_c") or None,
            form.get("option_d") or None,
            form.get("correct_option") or None,
        ],
    )

    return redirect("/teacher/questions")


@teacher_bp.route("/questions/<int:question_id>/update", methods=["POST"])
@role_required("teacher")
def update_question(question_id):
    db = get_db()
    form = clean_form(request.form)
    db.execute(
        "UPDATE question_bank SET question_text = %s, option_a = %s, option_b = %s, option_c = %s, option_d = %s, correct_option = %s WHERE id = %s AND teacher_id = %s",
        [
            form.get("question_text"),
            form.get("option_a") or None,
            form.get("option_b") or None,
            form.get("option_c") or None,
            form.get("option_d") or None,
            form.get("correct_option") or None,
            question_id,
            current_user.id,
        ],
    )

    return redirect("/teacher/questions")


@teacher_bp.route("/questions/<int:question_id>/delete", methods=["POST"])
@role_required("teacher")
def delete_question(question_id):
    db = get_db()
    db.execute(
        "DELETE FROM question_bank WHERE id = %s AND teacher_id = %s",
        [question_id, current_user.id],
    )
    return redirect("/teacher/questions")


@teacher_bp.route("/schedule")
@role_required("teacher")
def schedule():
    db = get_db()
    subjects_list = db.fetch_all(
        "SELECT s.id, s.name "
        "FROM teacher_subjects ts JOIN subjects s ON ts.subject_id = s.id "
        "WHERE ts.teacher_id = %s",
        [current_user.id],
    )

    exams_list = db.fetch_all(
        "SELECT e.id, s.name AS subject_name, e.exam_date, e.duration_minutes "
        "FROM exams e JOIN subjects s ON e.subject_id = s.id "
        "WHERE e.teacher_id = %s ORDER BY e.exam_date DESC",
        [current_user.id],
    )

    return render_template(
        "teacher/schedule.html",
        title="Schedule Exams",
        subjects=subjects_list,
        exams=exams_list,
        error=request.args.get("error"),
    )


@teacher_bp.route("/schedule", methods=["POST"])
@role_required("teacher")
def schedule_post():
    db = get_db()
    form = clean_form(request.form)

    mcq_count = db.fetch_one(
        "SELECT COUNT(*) AS count FROM question_bank WHERE subject_id = %s AND question_type = 'MCQ'",
        [form.get("subject_id")],
    )
    desc_count = db.fetch_one(
        "SELECT COUNT(*) AS count FROM question_bank WHERE subject_id = %s AND question_type = 'DESCRIPTIVE'",
        [form.get("subject_id")],
    )

    if (mcq_count or {}).get("count", 0) < 40 or (desc_count or {}).get("count", 0) < 10:
        return redirect("/teacher/schedule?error=Question%20bank%20incomplete")

    db.execute(
        "INSERT INTO exams (subject_id, teacher_id, exam_date, duration_minutes) VALUES (%s, %s, %s, %s)",
        [form.get("subject_id"), current_user.id, form.get("exam_date"), form.get("duration_minutes")],
    )

    return redirect("/teacher/schedule")


@teacher_bp.route("/evaluate")
@role_required("teacher")
def evaluate():
    db = get_db()
    answers = db.fetch_all(
        "SELECT sa.id, sa.answer_text, sa.marks_awarded, st.name AS student_name, s.name AS subject_name, e.id AS exam_id "
        "FROM student_answers sa "
        "JOIN students st ON sa.student_id = st.id "
        "JOIN exams e ON sa.exam_id = e.id "
        "JOIN subjects s ON e.subject_id = s.id "
        "WHERE sa.question_type = 'DESCRIPTIVE' AND sa.evaluated = 0 AND e.teacher_id = %s",
        [current_user.id],
    )

    return render_template("teacher/evaluate.html", title="Evaluate Descriptive", answers=answers)


@teacher_bp.route("/evaluate/<int:answer_id>", methods=["POST"])
@role_required("teacher")
def evaluate_post(answer_id):
    db = get_db()
    form = clean_form(request.form)

    answer = db.fetch_one("SELECT exam_id, student_id FROM student_answers WHERE id = %s", [answer_id])
    db.execute(
        "UPDATE student_answers SET marks_awarded = %s, evaluated = 1 WHERE id = %s",
        [form.get("marks_awarded"), answer_id],
    )

    if answer:
        totals = db.fetch_one(
            "SELECT SUM(marks_awarded) AS total FROM student_answers WHERE exam_id = %s AND student_id = %s",
            [answer.get("exam_id"), answer.get("student_id")],
        )

        total_marks = (totals or {}).get("total") or 0
        percentage = round((float(total_marks) / 25) * 100, 2)
        status = "Pass" if percentage >= 40 else "Fail"

        db.execute(
            "UPDATE results SET total_marks = %s, percentage = %s, status = %s WHERE exam_id = %s AND student_id = %s",
            [total_marks, percentage, status, answer.get("exam_id"), answer.get("student_id")],
        )

    return redirect("/teacher/evaluate")


@teacher_bp.route("/results")
@role_required("teacher")
def results():
    db = get_db()
    results_list = db.fetch_all(
        "SELECT r.id, st.name AS student_name, s.name AS subject_name, r.total_marks, r.percentage, r.status "
        "FROM results r "
        "JOIN students st ON r.student_id = st.id "
        "JOIN subjects s ON r.subject_id = s.id "
        "JOIN exams e ON r.exam_id = e.id "
        "WHERE e.teacher_id = %s ORDER BY r.id DESC",
        [current_user.id],
    )

    return render_template("teacher/results.html", title="Student Results", results=results_list)

