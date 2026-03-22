"""
auth_routes.py — Flask Blueprint for login, signup, OTP, logout.
Uses PostgreSQL (Supabase) — no sqlite3 anywhere.
"""

import os
import random
import psycopg2  # type: ignore
import psycopg2.extras  # type: ignore
from functools import wraps
from dotenv import load_dotenv  # type: ignore
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

auth_bp = Blueprint("auth", __name__)


def get_conn():
    return psycopg2.connect(
        os.environ["DATABASE_URL"],
        sslmode="require",
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


def init_admin_table():
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS admins (
            id         SERIAL PRIMARY KEY,
            name       TEXT NOT NULL,
            email      TEXT UNIQUE NOT NULL,
            phone      TEXT,
            password   TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    conn.commit()
    conn.close()


init_admin_table()


def validate_password(pw):
    errors = []
    if len(pw) < 8:
        errors.append("Password must be at least 8 characters.")
    if not any(c.isupper() for c in pw):
        errors.append("Password must contain at least one uppercase letter.")
    if not any(c.isdigit() for c in pw):
        errors.append("Password must contain at least one number.")
    if not any(c in "!@#$%^&*" for c in pw):
        errors.append(
            "Password must contain at least one special character (!@#$%^&*)."
        )
    return errors


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "info")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template("login.html")

        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM admins WHERE email = %s", (email,))
        admin = c.fetchone()
        conn.close()

        if admin and check_password_hash(admin["password"], password):
            session["user_id"] = admin["id"]
            session["user_name"] = admin["name"]
            session["user_email"] = admin["email"]
            session["role"] = "admin"
            flash(f"Welcome back, {admin['name']}!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid email or password. Please try again.", "danger")

    return render_template("login.html")


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not all([name, email, phone, password, confirm]):
            flash("All fields are required.", "danger")
            return render_template("signup.html", step=1)

        if len(phone) != 10 or not phone.isdigit():
            flash("Phone number must be exactly 10 digits.", "danger")
            return render_template("signup.html", step=1)

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("signup.html", step=1)

        errs = validate_password(password)
        if errs:
            for err in errs:
                flash(err, "danger")
            return render_template("signup.html", step=1)

        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT id FROM admins WHERE email = %s", (email,))
        existing = c.fetchone()
        conn.close()

        if existing:
            flash("An admin account with this email already exists.", "danger")
            return render_template("signup.html", step=1)

        otp = random.randint(100000, 999999)
        print(f"\n{'='*40}\n  OTP for {email}: {otp}\n{'='*40}\n")

        session["signup_otp"] = str(otp)
        session["signup_data"] = {
            "name": name,
            "email": email,
            "phone": phone,
            "password": generate_password_hash(password),
        }
        flash(f"OTP sent! (Demo: {otp} — check terminal)", "info")
        return render_template("signup.html", step=2)

    session.pop("signup_otp", None)
    session.pop("signup_data", None)
    return render_template("signup.html", step=1)


@auth_bp.route("/signup/verify", methods=["POST"])
def signup_verify():
    entered_otp = request.form.get("otp", "").strip()
    stored_otp = session.get("signup_otp")
    signup_data = session.get("signup_data")

    if not stored_otp or not signup_data:
        flash("Session expired. Please start signup again.", "danger")
        return redirect(url_for("auth.signup"))

    if entered_otp != stored_otp:
        flash("Incorrect OTP. Please try again.", "danger")
        return render_template("signup.html", step=2)

    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute(
            "INSERT INTO admins (name, email, phone, password) VALUES (%s, %s, %s, %s)",
            (
                signup_data["name"],
                signup_data["email"],
                signup_data["phone"],
                signup_data["password"],
            ),
        )
        conn.commit()
        conn.close()
    except psycopg2.errors.UniqueViolation:
        flash("An account with this email already exists.", "danger")
        return redirect(url_for("auth.signup"))

    session.pop("signup_otp", None)
    session.pop("signup_data", None)
    flash(f"Account created! Welcome, {signup_data['name']} 🎉", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("auth.login"))
