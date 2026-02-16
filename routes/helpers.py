from functools import wraps

from flask import current_app, redirect, render_template, url_for
from flask_login import current_user


def get_db():
    return current_app.extensions["db"]


def role_required(role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))
            if role and current_user.role != role:
                return render_template("forbidden.html", title="Access Denied"), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def generate_teacher_code():
    db = get_db()
    year = __import__("datetime").datetime.now().year
    prefix = f"TCH-{year}-"
    row = db.fetch_one(
        "SELECT teacher_code FROM teachers WHERE teacher_code LIKE %s ORDER BY teacher_code DESC LIMIT 1",
        [f"{prefix}%"],
    )

    next_number = 1
    if row and row.get("teacher_code"):
        last_code = row["teacher_code"]
        try:
            last_number = int(last_code.split("-")[-1])
            next_number = last_number + 1
        except ValueError:
            next_number = 1

    return f"{prefix}{str(next_number).zfill(3)}"


def generate_roll_number(semester_number):
    db = get_db()
    year = __import__("datetime").datetime.now().year
    prefix = f"{year}-SEM{semester_number}-"
    row = db.fetch_one(
        "SELECT roll_number FROM students WHERE roll_number LIKE %s ORDER BY roll_number DESC LIMIT 1",
        [f"{prefix}%"],
    )

    next_number = 1
    if row and row.get("roll_number"):
        last_roll = row["roll_number"]
        try:
            last_number = int(last_roll.split("-")[-1])
            next_number = last_number + 1
        except ValueError:
            next_number = 1

    return f"{prefix}{str(next_number).zfill(3)}"
