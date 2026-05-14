import functools
import secrets

from flask import abort, flash, redirect, request, session, url_for


def csrf_token():
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


def validate_csrf():
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        token = request.form.get("_csrf_token") or request.headers.get("X-CSRF-Token")
        if not token or token != session.get("_csrf_token"):
            abort(400, description="Invalid CSRF token")


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("auth.login"))
        if session.get("role") != "admin":
            abort(403)
        return view(*args, **kwargs)

    return wrapped
