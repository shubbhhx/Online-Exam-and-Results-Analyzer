import atexit
import logging
import os
import secrets
from datetime import datetime

from flask import Flask, abort, g, redirect, render_template, request, session, url_for
from flask_login import LoginManager, current_user
from flask_session import Session
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config
from db import Database
from models import User
from routes.admin import admin_bp
from routes.auth import auth_bp
from routes.student import student_bp
from routes.teacher import teacher_bp


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static", static_url_path="/static")
    app.config.from_object(Config())

    logging.basicConfig(level=getattr(logging, app.config.get("LOG_LEVEL", "INFO")))

    env = (app.config.get("FLASK_ENV") or "").lower()
    if env == "production":
        app.config.setdefault("SESSION_TYPE", "filesystem")
        app.config.setdefault("SESSION_FILE_DIR", "/tmp/flask_session")
        app.config.setdefault("SESSION_USE_SIGNER", True)
        app.config.setdefault("SESSION_COOKIE_SECURE", True)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    Session(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    db = Database(app.config)
    app.extensions["db"] = db

    def _close_db():
        db.close()

    atexit.register(_close_db)

    @login_manager.user_loader
    def load_user(user_id):
        try:
            role, raw_id = user_id.split(":", 1)
        except ValueError:
            return None
        table = {
            "admin": "admins",
            "teacher": "teachers",
            "student": "students",
        }.get(role)
        if not table:
            return None

        row = db.fetch_one(f"SELECT id, name FROM {table} WHERE id = %s", [raw_id])
        if not row:
            return None
        return User(row["id"], role, row.get("name", ""))

    @app.before_request
    def set_defaults():
        g.show_auth_buttons = False
        if "_csrf_token" not in session:
            session["_csrf_token"] = secrets.token_urlsafe(32)

        if request.method in {"POST", "PUT", "DELETE"}:
            token = request.form.get("_csrf") or request.headers.get("X-CSRF-Token")
            if not token or token != session.get("_csrf_token"):
                abort(403)

    @app.context_processor
    def inject_globals():
        toast = session.pop("toast", None)
        return {
            "user": current_user if current_user.is_authenticated else None,
            "pageLoading": getattr(g, "page_loading", False),
            "csrf_token": session.get("_csrf_token"),
            "showAuthButtons": getattr(g, "show_auth_buttons", False),
            "toast": toast,
        }

    @app.template_filter("format_datetime")
    def format_datetime(value):
        if not value:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, datetime):
            return value.strftime("%m/%d/%Y, %I:%M:%S %p")
        return str(value)

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(student_bp)

    @app.route("/")
    def index():
        return redirect(url_for("auth.login"))

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("not_found.html", title="Not Found"), 404

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("forbidden.html", title="Forbidden"), 403

    @app.errorhandler(500)
    def server_error(_error):
        return "Internal Server Error", 500

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
else:
    app = create_app()
