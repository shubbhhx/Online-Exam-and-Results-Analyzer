from flask import Blueprint, g, redirect, render_template, request, session, url_for
from flask_login import login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from models import User
from routes.helpers import get_db, generate_roll_number
from utils import clean_form


auth_bp = Blueprint("auth", __name__)


def _verify_password(stored_password, provided_password):
    if stored_password is None:
        return False
    if stored_password.startswith("pbkdf2:") or stored_password.startswith("scrypt:"):
        return check_password_hash(stored_password, provided_password)
    return stored_password == provided_password


@auth_bp.route("/login", methods=["GET"])
def login():
    g.show_auth_buttons = True
    toast = None
    if request.args.get("toast"):
        toast = {
            "type": request.args.get("type", "success"),
            "message": request.args.get("toast"),
        }

    return render_template(
        "login.html",
        title="Online Examination System",
        error=None,
        showAuthButtons=True,
        toast=toast,
    )


@auth_bp.route("/login", methods=["POST"])
def login_post():
    form = clean_form(request.form)
    email = form.get("email")
    password = form.get("password")

    role_tables = [
        {"role": "admin", "table": "admins"},
        {"role": "teacher", "table": "teachers"},
        {"role": "student", "table": "students"},
    ]

    matches = []
    db = get_db()

    for entry in role_tables:
        row = db.fetch_one(
            f"SELECT * FROM {entry['table']} WHERE email = %s LIMIT 1",
            [email],
        )
        if row and _verify_password(row.get("password"), password):
            matches.append({"role": entry["role"], "user": row})

    if not matches:
        g.show_auth_buttons = True
        return render_template(
            "login.html",
            title="Online Examination System",
            error="Invalid credentials.",
            showAuthButtons=True,
        )

    if len(matches) > 1:
        g.show_auth_buttons = True
        return render_template(
            "login.html",
            title="Online Examination System",
            error="Multiple accounts found. Contact support.",
            showAuthButtons=True,
        )

    role = matches[0]["role"]
    user = matches[0]["user"]
    login_user(User(user["id"], role, user.get("name", "")))

    session["toast"] = {"type": "success", "message": "Login successful"}

    if role == "admin":
        return redirect(url_for("admin.dashboard"))
    if role == "teacher":
        return redirect(url_for("teacher.dashboard"))
    return redirect(url_for("student.dashboard"))


@auth_bp.route("/register", methods=["GET"])
def register():
    db = get_db()
    courses = db.fetch_all("SELECT id, name FROM courses ORDER BY name")
    semesters = db.fetch_all(
        "SELECT id, course_id, semester_number, title FROM semesters ORDER BY semester_number"
    )

    return render_template(
        "register.html",
        title="Student Registration",
        error=None,
        courses=courses,
        semesters=semesters,
    )


@auth_bp.route("/register", methods=["POST"])
def register_post():
    form = clean_form(request.form)
    name = form.get("name")
    email = form.get("email")
    password = form.get("password")
    course_id = form.get("course_id")
    semester_id = form.get("semester_id")
    address = form.get("address")
    phone = form.get("phone")

    db = get_db()
    existing = db.fetch_one("SELECT id FROM students WHERE email = %s", [email])
    if existing:
        courses = db.fetch_all("SELECT id, name FROM courses ORDER BY name")
        semesters = db.fetch_all(
            "SELECT id, course_id, semester_number, title FROM semesters ORDER BY semester_number"
        )
        return render_template(
            "register.html",
            title="Student Registration",
            error="Email already registered.",
            courses=courses,
            semesters=semesters,
        )

    semester_row = db.fetch_one(
        "SELECT id, course_id, semester_number FROM semesters WHERE id = %s",
        [semester_id],
    )
    if not semester_row or str(semester_row.get("course_id")) != str(course_id):
        courses = db.fetch_all("SELECT id, name FROM courses ORDER BY name")
        semesters = db.fetch_all(
            "SELECT id, course_id, semester_number, title FROM semesters ORDER BY semester_number"
        )
        return render_template(
            "register.html",
            title="Student Registration",
            error="Invalid course and semester selection.",
            courses=courses,
            semesters=semesters,
        )

    roll_number = generate_roll_number(semester_row.get("semester_number"))
    hashed = generate_password_hash(password)

    db.execute(
        "INSERT INTO students (roll_number, name, email, password, course_id, semester_id, address, phone) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        [
            roll_number,
            name,
            email,
            hashed,
            course_id,
            semester_id,
            address or None,
            phone or None,
        ],
    )

    return redirect(url_for("auth.login", toast="Registration successful", type="success"))


@auth_bp.route("/logout")
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("auth.login"))

