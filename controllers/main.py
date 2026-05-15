import os

from flask import Blueprint, Response, current_app, flash, redirect, render_template, request, session, url_for, send_from_directory

from controllers.security import login_required, validate_csrf
from controllers.uploads import save_upload
from models.database import query, query_optional

main_bp = Blueprint("main", __name__)


@main_bp.before_request
def before_main_request():
    validate_csrf()


@main_bp.app_context_processor
def inject_globals():
    from controllers.security import csrf_token

    return {"csrf_token": csrf_token}


@main_bp.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)


def parse_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def choice(value, allowed, default):
    return value if value in allowed else default


@main_bp.route("/")
def home():
    announcements = query_optional("SELECT * FROM announcements ORDER BY created_at DESC LIMIT 3", default=[])
    events = query_optional("SELECT * FROM events ORDER BY starts_at DESC LIMIT 3", default=[])
    return render_template("home.html", announcements=announcements, events=events)


@main_bp.route("/join", methods=["GET", "POST"])
def public_member_register():
    if request.method == "POST":
        age = parse_int(request.form.get("age"), 0)
        data = (
            request.form.get("full_name", "").strip(),
            choice(request.form.get("gender"), {"Female", "Male", "Other"}, "Other"),
            age,
            request.form.get("phone", "").strip(),
            request.form.get("email", "").strip(),
            request.form.get("address", "").strip(),
            request.form.get("education_level", "").strip(),
            request.form.get("skills", "").strip(),
            request.form.get("employment_status", "").strip(),
        )
        if len(data[0]) < 3 or data[2] < 12:
            flash("Please enter a valid name and age.", "danger")
            return render_template("members/public_register.html")

        photo = save_upload(request.files.get("profile_photo"), "members")
        query(
            """INSERT INTO youth_members
            (full_name, gender, age, phone, email, address, education_level, skills, employment_status, profile_photo, created_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NULL)""",
            data + (photo,),
            commit=True,
        )
        flash("Registration submitted successfully. Thank you for joining.", "success")
        return redirect(url_for("main.public_member_register"))
    return render_template("members/public_register.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    stats = {
        "members": query("SELECT COUNT(*) total FROM youth_members", one=True)["total"],
        "events": query("SELECT COUNT(*) total FROM events", one=True)["total"],
        "projects": query("SELECT COUNT(*) total FROM projects", one=True)["total"],
        "active_users": query("SELECT COUNT(*) total FROM users WHERE active=1", one=True)["total"],
    }
    gender_rows = query("SELECT gender label, COUNT(*) value FROM youth_members GROUP BY gender")
    project_rows = query("SELECT status label, COUNT(*) value FROM projects GROUP BY status")
    events = query("SELECT * FROM events ORDER BY starts_at DESC LIMIT 5")
    announcements = query("SELECT * FROM announcements ORDER BY created_at DESC LIMIT 5")
    return render_template(
        "dashboard.html",
        stats=stats,
        gender_rows=gender_rows,
        project_rows=project_rows,
        events=events,
        announcements=announcements,
    )


@main_bp.route("/announcements")
@login_required
def announcements():
    rows = query("SELECT * FROM announcements ORDER BY created_at DESC")
    return render_template("announcements.html", announcements=rows)


@main_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()
        category = choice(request.form.get("category"), {"contact", "feedback"}, "feedback")
        if len(name) < 2 or len(subject) < 3 or len(message) < 10:
            flash("Please complete the form with a clear message.", "danger")
        else:
            query(
                "INSERT INTO feedback (name, email, subject, message, category) VALUES (%s, %s, %s, %s, %s)",
                (name, email, subject, message, category),
                commit=True,
            )
            flash("Thank you. Your message has been received.", "success")
            return redirect(url_for("main.contact"))
    return render_template("contact.html")


@main_bp.route("/exports/members.csv")
@login_required
def export_members_csv():
    rows = query("SELECT full_name, gender, age, phone, email, address, education_level, skills, employment_status FROM youth_members ORDER BY full_name")
    header = "Full name,Gender,Age,Phone,Email,Address,Education level,Skills,Employment status\n"
    lines = [header]
    for row in rows:
        values = [str(row.get(key, "") or "").replace('"', '""') for key in row.keys()]
        lines.append(",".join(f'"{value}"' for value in values) + "\n")
    return Response(
        "".join(lines),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=nyakabanda_youth_members.csv"},
    )
