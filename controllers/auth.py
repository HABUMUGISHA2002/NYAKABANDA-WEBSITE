import secrets
from datetime import datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from controllers.security import login_required, validate_csrf
from models.database import query

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.before_request
def before_auth_request():
    validate_csrf()


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if len(full_name) < 3 or "@" not in email or len(password) < 8:
            flash("Use a valid name, email, and password with at least 8 characters.", "danger")
            return render_template("auth/register.html")
        existing = query("SELECT id FROM users WHERE email=%s", (email,), one=True)
        if existing:
            flash("An account with that email already exists.", "danger")
            return render_template("auth/register.html")
        query(
            "INSERT INTO users (full_name, email, password_hash, role) VALUES (%s, %s, %s, 'user')",
            (full_name, email, generate_password_hash(password)),
            commit=True,
        )
        flash("Account created. You can now sign in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = query("SELECT * FROM users WHERE email=%s AND active=1", (email,), one=True)
        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html")
        session.clear()
        session["user_id"] = user["id"]
        session["full_name"] = user["full_name"]
        session["role"] = user["role"]
        flash("Welcome back.", "success")
        return redirect(url_for("main.dashboard"))
    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("main.home"))


@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")
        user = query("SELECT id, password_hash FROM users WHERE id=%s", (session["user_id"],), one=True)
        if not user or not check_password_hash(user["password_hash"], current_password):
            flash("Current password is incorrect.", "danger")
            return render_template("auth/change_password.html")
        if len(new_password) < 8:
            flash("New password must be at least 8 characters.", "danger")
            return render_template("auth/change_password.html")
        if new_password != confirm_password:
            flash("New passwords do not match.", "danger")
            return render_template("auth/change_password.html")
        query(
            "UPDATE users SET password_hash=%s WHERE id=%s",
            (generate_password_hash(new_password), user["id"]),
            commit=True,
        )
        flash("Password changed successfully.", "success")
        return redirect(url_for("main.dashboard"))
    return render_template("auth/change_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = query("SELECT id, reset_expires FROM users WHERE reset_token=%s", (token,), one=True)
    if not user:
        flash("Invalid or expired reset link.", "danger")
        return redirect(url_for("auth.forgot_password"))
    if user["reset_expires"] and datetime.utcnow() > user["reset_expires"]:
        flash("Reset link has expired. Request a new one.", "danger")
        return redirect(url_for("auth.forgot_password"))
    if request.method == "POST":
        password = request.form.get("password", "")
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return render_template("auth/reset_password.html", token=token)
        query(
            "UPDATE users SET password_hash=%s, reset_token=NULL, reset_expires=NULL WHERE id=%s",
            (generate_password_hash(password), user["id"]),
            commit=True,
        )
        flash("Password updated. You can now sign in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/reset_password.html", token=token)


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    reset_token = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = query("SELECT id FROM users WHERE email=%s", (email,), one=True)
        if user:
            reset_token = secrets.token_urlsafe(24)
            expires = datetime.utcnow() + timedelta(hours=1)
            query(
                "UPDATE users SET reset_token=%s, reset_expires=%s WHERE id=%s",
                (reset_token, expires, user["id"]),
                commit=True,
            )
        flash("If that email exists, a password reset link has been prepared.", "info")
    return render_template("auth/forgot_password.html", reset_token=reset_token)
