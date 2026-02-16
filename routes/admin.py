from flask import Blueprint, redirect, render_template, request
from werkzeug.security import generate_password_hash
from routes.helpers import generate_roll_number, generate_teacher_code, get_db, role_required
from utils import clean_form


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@role_required("admin")
def dashboard():
    db = get_db()
    try:
        students = db.fetch_one("SELECT COUNT(*) AS count FROM students")
        teachers = db.fetch_one("SELECT COUNT(*) AS count FROM teachers")
        subjects = db.fetch_one("SELECT COUNT(*) AS count FROM subjects")
        exams = db.fetch_one("SELECT COUNT(*) AS count FROM exams")
        courses_count = db.fetch_one("SELECT COUNT(*) AS count FROM courses")

        courses = db.fetch_all("SELECT id, name, code FROM courses ORDER BY name")
        semesters = db.fetch_all(
            "SELECT id, course_id, semester_number, title FROM semesters ORDER BY semester_number"
        )
        subjects_list = db.fetch_all(
            "SELECT id, semester_id, name FROM subjects ORDER BY name"
        )

        course_map = {course["id"]: {**course, "semesters": []} for course in courses}
        semester_map = {}
        for semester in semesters:
            target = course_map.get(semester["course_id"])
            if target is not None:
                item = {**semester, "subjects": []}
                target["semesters"].append(item)
                semester_map[semester["id"]] = item

        for subject in subjects_list:
            target = semester_map.get(subject["semester_id"])
            if target is not None:
                target["subjects"].append(subject)

        recent_students = db.fetch_all(
            "SELECT name, roll_number FROM students ORDER BY id DESC LIMIT 5"
        )
        recent_exams = db.fetch_all(
            "SELECT e.id, s.name AS subject_name, e.exam_date FROM exams e JOIN subjects s ON e.subject_id = s.id ORDER BY e.exam_date DESC LIMIT 5"
        )
        pass_fail = db.fetch_all(
            "SELECT status, COUNT(*) AS count FROM results GROUP BY status"
        )

        return render_template(
            "admin/dashboard.html",
            title="Admin Dashboard",
            stats={
                "students": students.get("count", 0) if students else 0,
                "teachers": teachers.get("count", 0) if teachers else 0,
                "subjects": subjects.get("count", 0) if subjects else 0,
                "exams": exams.get("count", 0) if exams else 0,
                "courses": courses_count.get("count", 0) if courses_count else 0,
            },
            structure=list(course_map.values()),
            recentStudents=recent_students,
            recentExams=recent_exams,
            pageLoading=True,
            passFail=pass_fail,
        )
    except Exception:
        return render_template(
            "admin/dashboard.html",
            title="Admin Dashboard",
            stats={"students": 0, "teachers": 0, "subjects": 0, "exams": 0, "courses": 0},
            structure=[],
            recentStudents=[],
            recentExams=[],
            pageLoading=True,
            passFail=[],
        )


@admin_bp.route("/courses")
@role_required("admin")
def courses():
    db = get_db()
    courses_list = db.fetch_all("SELECT * FROM courses ORDER BY name")
    return render_template("admin/courses.html", title="Manage Courses", courses=courses_list)


@admin_bp.route("/courses", methods=["POST"])
@role_required("admin")
def create_course():
    db = get_db()
    form = clean_form(request.form)
    db.execute("INSERT INTO courses (name, code) VALUES (%s, %s)", [form.get("name"), form.get("code")])
    return redirect("/admin/courses")


@admin_bp.route("/courses/<int:course_id>/update", methods=["POST"])
@role_required("admin")
def update_course(course_id):
    db = get_db()
    form = clean_form(request.form)
    db.execute("UPDATE courses SET name = %s, code = %s WHERE id = %s", [form.get("name"), form.get("code"), course_id])
    return redirect("/admin/courses")


@admin_bp.route("/courses/<int:course_id>/delete", methods=["POST"])
@role_required("admin")
def delete_course(course_id):
    db = get_db()
    db.execute("DELETE FROM courses WHERE id = %s", [course_id])
    return redirect("/admin/courses")


@admin_bp.route("/semesters")
@role_required("admin")
def semesters():
    db = get_db()
    courses = db.fetch_all("SELECT id, name FROM courses ORDER BY name")
    semesters_list = db.fetch_all(
        "SELECT sem.id, sem.course_id, sem.semester_number, sem.title, c.name AS course_name "
        "FROM semesters sem JOIN courses c ON sem.course_id = c.id "
        "ORDER BY c.name, sem.semester_number"
    )
    subjects = db.fetch_all("SELECT s.id, s.semester_id, s.name FROM subjects s ORDER BY s.name")

    return render_template(
        "admin/semesters.html",
        title="Manage Semesters",
        courses=courses,
        semesters=semesters_list,
        subjects=subjects,
    )


@admin_bp.route("/semesters", methods=["POST"])
@role_required("admin")
def create_semester():
    db = get_db()
    form = clean_form(request.form)
    subject_list = [item.strip() for item in (form.get("subjects") or "").replace("\r", "\n").split("\n")]
    subject_list = [item for item in subject_list if item]

    conn = db.transaction()
    if conn is None:
        return redirect("/admin/semesters")

    try:
        conn.begin()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO semesters (course_id, semester_number, title) VALUES (%s, %s, %s)",
                [form.get("course_id"), form.get("semester_number"), form.get("title")],
            )
            semester_id = cursor.lastrowid
            for name in subject_list:
                cursor.execute("INSERT INTO subjects (semester_id, name) VALUES (%s, %s)", [semester_id, name])
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        conn.close()

    return redirect("/admin/semesters")


@admin_bp.route("/semesters/<int:semester_id>/update", methods=["POST"])
@role_required("admin")
def update_semester(semester_id):
    db = get_db()
    form = clean_form(request.form)
    db.execute(
        "UPDATE semesters SET semester_number = %s, title = %s WHERE id = %s",
        [form.get("semester_number"), form.get("title"), semester_id],
    )
    return redirect("/admin/semesters")


@admin_bp.route("/semesters/<int:semester_id>/delete", methods=["POST"])
@role_required("admin")
def delete_semester(semester_id):
    db = get_db()
    db.execute("DELETE FROM semesters WHERE id = %s", [semester_id])
    return redirect("/admin/semesters")


@admin_bp.route("/students")
@role_required("admin")
def students():
    db = get_db()
    students_list = db.fetch_all(
        "SELECT st.*, c.name AS course_name, sem.semester_number "
        "FROM students st "
        "JOIN courses c ON st.course_id = c.id "
        "JOIN semesters sem ON st.semester_id = sem.id "
        "ORDER BY st.id DESC"
    )
    courses = db.fetch_all("SELECT id, name FROM courses ORDER BY name")
    semesters_list = db.fetch_all(
        "SELECT id, course_id, semester_number, title FROM semesters ORDER BY semester_number"
    )

    return render_template(
        "admin/students.html",
        title="Manage Students",
        students=students_list,
        courses=courses,
        semesters=semesters_list,
    )


@admin_bp.route("/students", methods=["POST"])
@role_required("admin")
def create_student():
    db = get_db()
    form = clean_form(request.form)
    semester_row = db.fetch_one(
        "SELECT semester_number, course_id FROM semesters WHERE id = %s",
        [form.get("semester_id")],
    )

    if not semester_row or str(semester_row.get("course_id")) != str(form.get("course_id")):
        return redirect("/admin/students")

    roll_number = generate_roll_number(semester_row.get("semester_number"))
    hashed = generate_password_hash(form.get("password"))
    db.execute(
        "INSERT INTO students (roll_number, name, email, password, course_id, semester_id) VALUES (%s, %s, %s, %s, %s, %s)",
        [roll_number, form.get("name"), form.get("email"), hashed, form.get("course_id"), form.get("semester_id")],
    )
    return redirect("/admin/students")


@admin_bp.route("/students/<int:student_id>/update", methods=["POST"])
@role_required("admin")
def update_student(student_id):
    db = get_db()
    form = clean_form(request.form)
    semester_row = db.fetch_one(
        "SELECT semester_number, course_id FROM semesters WHERE id = %s",
        [form.get("semester_id")],
    )

    if not semester_row:
        return redirect("/admin/students")

    db.execute(
        "UPDATE students SET name = %s, email = %s, semester_id = %s, course_id = %s WHERE id = %s",
        [form.get("name"), form.get("email"), form.get("semester_id"), semester_row.get("course_id"), student_id],
    )
    return redirect("/admin/students")


@admin_bp.route("/students/<int:student_id>/delete", methods=["POST"])
@role_required("admin")
def delete_student(student_id):
    db = get_db()
    db.execute("DELETE FROM students WHERE id = %s", [student_id])
    return redirect("/admin/students")


@admin_bp.route("/teachers")
@role_required("admin")
def teachers():
    db = get_db()
    teachers_list = db.fetch_all("SELECT * FROM teachers ORDER BY id DESC")
    return render_template("admin/teachers.html", title="Manage Teachers", teachers=teachers_list)


@admin_bp.route("/teachers", methods=["POST"])
@role_required("admin")
def create_teacher():
    db = get_db()
    form = clean_form(request.form)
    teacher_code = generate_teacher_code()
    hashed = generate_password_hash(form.get("password"))
    db.execute(
        "INSERT INTO teachers (teacher_code, name, email, password, department, phone) VALUES (%s, %s, %s, %s, %s, %s)",
        [teacher_code, form.get("name"), form.get("email"), hashed, form.get("department"), form.get("phone") or None],
    )
    return redirect("/admin/teachers")


@admin_bp.route("/teachers/<int:teacher_id>/update", methods=["POST"])
@role_required("admin")
def update_teacher(teacher_id):
    db = get_db()
    form = clean_form(request.form)
    db.execute(
        "UPDATE teachers SET name = %s, email = %s, department = %s, phone = %s WHERE id = %s",
        [form.get("name"), form.get("email"), form.get("department"), form.get("phone") or None, teacher_id],
    )
    return redirect("/admin/teachers")


@admin_bp.route("/teachers/<int:teacher_id>/delete", methods=["POST"])
@role_required("admin")
def delete_teacher(teacher_id):
    db = get_db()
    db.execute("DELETE FROM teachers WHERE id = %s", [teacher_id])
    return redirect("/admin/teachers")


@admin_bp.route("/subjects")
@role_required("admin")
def subjects():
    db = get_db()
    subjects_list = db.fetch_all(
        "SELECT s.id, s.name, sem.semester_number, c.name AS course_name "
        "FROM subjects s "
        "JOIN semesters sem ON s.semester_id = sem.id "
        "JOIN courses c ON sem.course_id = c.id "
        "ORDER BY c.name, sem.semester_number, s.name"
    )
    return render_template("admin/subjects.html", title="Subjects", subjects=subjects_list)


@admin_bp.route("/assignments")
@role_required("admin")
def assignments():
    db = get_db()
    teachers_list = db.fetch_all("SELECT id, name, teacher_code FROM teachers")
    subjects_list = db.fetch_all(
        "SELECT s.id, s.name, sem.semester_number, c.name AS course_name "
        "FROM subjects s "
        "JOIN semesters sem ON s.semester_id = sem.id "
        "JOIN courses c ON sem.course_id = c.id "
        "ORDER BY c.name, sem.semester_number, s.name"
    )
    assignments_list = db.fetch_all(
        "SELECT ts.id, t.name AS teacher_name, t.teacher_code, s.name AS subject_name, sem.semester_number, c.name AS course_name "
        "FROM teacher_subjects ts "
        "JOIN teachers t ON ts.teacher_id = t.id "
        "JOIN subjects s ON ts.subject_id = s.id "
        "JOIN semesters sem ON s.semester_id = sem.id "
        "JOIN courses c ON sem.course_id = c.id "
        "ORDER BY ts.id DESC"
    )

    return render_template(
        "admin/assignments.html",
        title="Assign Teachers",
        teachers=teachers_list,
        subjects=subjects_list,
        assignments=assignments_list,
        error=request.args.get("error"),
    )


@admin_bp.route("/assignments", methods=["POST"])
@role_required("admin")
def create_assignment():
    db = get_db()
    form = clean_form(request.form)
    existing = db.fetch_one(
        "SELECT id FROM teacher_subjects WHERE subject_id = %s",
        [form.get("subject_id")],
    )
    if existing:
        return redirect("/admin/assignments?error=Subject%20already%20assigned")

    db.execute(
        "INSERT INTO teacher_subjects (teacher_id, subject_id) VALUES (%s, %s)",
        [form.get("teacher_id"), form.get("subject_id")],
    )
    return redirect("/admin/assignments")


@admin_bp.route("/assignments/<int:assignment_id>/delete", methods=["POST"])
@role_required("admin")
def delete_assignment(assignment_id):
    db = get_db()
    db.execute("DELETE FROM teacher_subjects WHERE id = %s", [assignment_id])
    return redirect("/admin/assignments")


@admin_bp.route("/questions")
@role_required("admin")
def questions():
    db = get_db()
    questions_list = db.fetch_all(
        "SELECT q.id, q.question_type, q.question_text, s.name AS subject_name, t.name AS teacher_name "
        "FROM question_bank q "
        "JOIN subjects s ON q.subject_id = s.id "
        "JOIN teachers t ON q.teacher_id = t.id "
        "ORDER BY q.id DESC"
    )
    return render_template("admin/questions.html", title="Question Bank", questions=questions_list)


@admin_bp.route("/exams")
@role_required("admin")
def exams():
    db = get_db()
    exams_list = db.fetch_all(
        "SELECT e.id, s.name AS subject_name, t.name AS teacher_name, e.exam_date, e.duration_minutes "
        "FROM exams e "
        "JOIN subjects s ON e.subject_id = s.id "
        "JOIN teachers t ON e.teacher_id = t.id "
        "ORDER BY e.exam_date DESC"
    )
    return render_template("admin/exams.html", title="Monitor Exams", exams=exams_list)


@admin_bp.route("/results")
@role_required("admin")
def results():
    db = get_db()
    results_list = db.fetch_all(
        "SELECT r.id, st.name AS student_name, s.name AS subject_name, r.total_marks, r.percentage, r.status "
        "FROM results r "
        "JOIN students st ON r.student_id = st.id "
        "JOIN subjects s ON r.subject_id = s.id "
        "ORDER BY r.id DESC"
    )
    return render_template("admin/results.html", title="Exam Results", results=results_list)


@admin_bp.route("/analytics")
@role_required("admin")
def analytics():
    db = get_db()
    pass_fail = db.fetch_all(
        "SELECT status, COUNT(*) AS count FROM results GROUP BY status"
    )
    subject_perf = db.fetch_all(
        "SELECT s.name AS subject_name, AVG(r.percentage) AS avg_percent "
        "FROM results r JOIN subjects s ON r.subject_id = s.id GROUP BY s.name"
    )

    return render_template(
        "admin/analytics.html",
        title="Analytics",
        passFail=pass_fail,
        subjectPerf=subject_perf,
    )

