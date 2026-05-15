from datetime import datetime

from flask import Blueprint, Response, flash, redirect, render_template, request, session, url_for

from controllers.security import admin_required, login_required, validate_csrf
from controllers.uploads import save_upload
from models.database import query

admin_bp = Blueprint("admin", __name__, url_prefix="/manage")


@admin_bp.before_request
def before_admin_request():
    validate_csrf()


def parse_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def choice(value, allowed, default):
    return value if value in allowed else default


def datetime_local_value(value):
    if not value:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%dT%H:%M")
    return str(value).replace(" ", "T")[:16]


@admin_bp.route("/members")
@login_required
def members():
    term = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page
    if term:
        like = f"%{term}%"
        rows = query(
            "SELECT * FROM youth_members WHERE full_name LIKE %s OR phone LIKE %s OR email LIKE %s OR skills LIKE %s ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (like, like, like, like, per_page, offset),
        )
        count = query(
            "SELECT COUNT(*) total FROM youth_members WHERE full_name LIKE %s OR phone LIKE %s OR email LIKE %s OR skills LIKE %s",
            (like, like, like, like), one=True,
        )["total"]
    else:
        rows = query("SELECT * FROM youth_members ORDER BY created_at DESC LIMIT %s OFFSET %s", (per_page, offset))
        count = query("SELECT COUNT(*) total FROM youth_members", one=True)["total"]
    total_pages = max(1, (count + per_page - 1) // per_page)
    return render_template("members/list.html", members=rows, term=term, page=page, total_pages=total_pages)


@admin_bp.route("/members/new", methods=["GET", "POST"])
@admin_required
def member_new():
    return member_form()


@admin_bp.route("/members/<int:member_id>/edit", methods=["GET", "POST"])
@admin_required
def member_edit(member_id):
    member = query("SELECT * FROM youth_members WHERE id=%s", (member_id,), one=True)
    if not member:
        flash("Member not found.", "danger")
        return redirect(url_for("admin.members"))
    return member_form(member)


def member_form(member=None):
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
        else:
            photo = save_upload(request.files.get("profile_photo"), "members")
            if member:
                sql = """UPDATE youth_members SET full_name=%s, gender=%s, age=%s, phone=%s, email=%s,
                         address=%s, education_level=%s, skills=%s, employment_status=%s"""
                params = list(data)
                if photo:
                    sql += ", profile_photo=%s"
                    params.append(photo)
                sql += " WHERE id=%s"
                params.append(member["id"])
                query(sql, tuple(params), commit=True)
                flash("Member updated.", "success")
            else:
                query(
                    """INSERT INTO youth_members
                    (full_name, gender, age, phone, email, address, education_level, skills, employment_status, profile_photo, created_by)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    data + (photo, session["user_id"]),
                    commit=True,
                )
                flash("Member added.", "success")
            return redirect(url_for("admin.members"))
    return render_template("members/form.html", member=member)


@admin_bp.route("/members/<int:member_id>")
@login_required
def member_detail(member_id):
    member = query("SELECT * FROM youth_members WHERE id=%s", (member_id,), one=True)
    if not member:
        flash("Member not found.", "danger")
        return redirect(url_for("admin.members"))
    events_attended = query(
        """SELECT e.title, e.starts_at, ea.status
           FROM event_attendance ea JOIN events e ON ea.event_id = e.id
           WHERE ea.youth_member_id=%s ORDER BY e.starts_at DESC""",
        (member_id,),
    )
    return render_template("members/detail.html", member=member, events_attended=events_attended)


@admin_bp.route("/members/<int:member_id>/delete", methods=["POST"])
@admin_required
def member_delete(member_id):
    query("DELETE FROM youth_members WHERE id=%s", (member_id,), commit=True)
    flash("Member deleted.", "info")
    return redirect(url_for("admin.members"))


@admin_bp.route("/events", methods=["GET", "POST"])
@login_required
def events():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        starts_at = request.form.get("starts_at")
        if len(title) < 3 or not starts_at:
            flash("Please enter a valid event title and start date.", "danger")
            return redirect(url_for("admin.events"))
        if session.get("role") != "admin":
            flash("Only admins can create events.", "danger")
            return redirect(url_for("admin.events"))
        image = save_upload(request.files.get("image"), "events")
        query(
            "INSERT INTO events (title, description, location, image_path, starts_at, ends_at, created_by) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (
                title,
                request.form.get("description", "").strip(),
                request.form.get("location", "").strip(),
                image,
                starts_at,
                request.form.get("ends_at") or None,
                session["user_id"],
            ),
            commit=True,
        )
        flash("Event created.", "success")
        return redirect(url_for("admin.events"))
    q = request.args.get("q", "").strip()
    if q:
        like = f"%{q}%"
        rows = query("SELECT * FROM events WHERE title LIKE %s OR location LIKE %s ORDER BY starts_at DESC", (like, like))
    else:
        rows = query("SELECT * FROM events ORDER BY starts_at DESC")
    members = query("SELECT id, full_name FROM youth_members ORDER BY full_name")
    attendee_rows = query(
        """SELECT ea.event_id, ym.full_name, ea.status
           FROM event_attendance ea JOIN youth_members ym ON ea.youth_member_id = ym.id
           ORDER BY ea.event_id, ym.full_name"""
    )
    event_attendees = {}
    for row in attendee_rows:
        event_attendees.setdefault(row["event_id"], []).append(row)
    return render_template("events.html", events=rows, members=members, event_attendees=event_attendees, edit_event=None, q=q)


@admin_bp.route("/events/<int:event_id>/register", methods=["POST"])
@login_required
def event_register(event_id):
    member_id = request.form.get("member_id")
    if not member_id:
        flash("Please choose a member.", "danger")
        return redirect(url_for("admin.events"))
    query(
        "INSERT IGNORE INTO event_attendance (event_id, youth_member_id, status) VALUES (%s,%s,'registered')",
        (event_id, member_id),
        commit=True,
    )
    flash("Event registration saved.", "success")
    return redirect(url_for("admin.events"))


@admin_bp.route("/events/<int:event_id>/attendance", methods=["POST"])
@admin_required
def event_attendance(event_id):
    member_id = request.form.get("member_id")
    status = choice(request.form.get("status"), {"registered", "attended", "absent"}, "attended")
    if not member_id:
        flash("Please choose a member.", "danger")
        return redirect(url_for("admin.events"))
    query(
        "UPDATE event_attendance SET status=%s, checked_at=NOW() WHERE event_id=%s AND youth_member_id=%s",
        (status, event_id, member_id),
        commit=True,
    )
    flash("Attendance updated.", "success")
    return redirect(url_for("admin.events"))


@admin_bp.route("/events/<int:event_id>/edit", methods=["GET", "POST"])
@admin_required
def event_edit(event_id):
    event = query("SELECT * FROM events WHERE id=%s", (event_id,), one=True)
    if not event:
        flash("Event not found.", "danger")
        return redirect(url_for("admin.events"))
    if request.method == "POST":
        image = save_upload(request.files.get("image"), "events")
        sql = "UPDATE events SET title=%s, description=%s, location=%s, starts_at=%s, ends_at=%s"
        params = [
            request.form.get("title", "").strip(),
            request.form.get("description", "").strip(),
            request.form.get("location", "").strip(),
            request.form.get("starts_at"),
            request.form.get("ends_at") or None,
        ]
        if image:
            sql += ", image_path=%s"
            params.append(image)
        sql += " WHERE id=%s"
        params.append(event_id)
        query(sql, tuple(params), commit=True)
        flash("Event updated.", "success")
        return redirect(url_for("admin.events"))
    event["starts_at_value"] = datetime_local_value(event.get("starts_at"))
    event["ends_at_value"] = datetime_local_value(event.get("ends_at"))
    attendee_rows = query("SELECT ea.event_id, ym.full_name, ea.status FROM event_attendance ea JOIN youth_members ym ON ea.youth_member_id = ym.id ORDER BY ea.event_id, ym.full_name")
    event_attendees = {}
    for row in attendee_rows:
        event_attendees.setdefault(row["event_id"], []).append(row)
    return render_template("events.html", edit_event=event, events=query("SELECT * FROM events ORDER BY starts_at DESC"), members=query("SELECT id, full_name FROM youth_members ORDER BY full_name"), event_attendees=event_attendees, q="")


@admin_bp.route("/events/<int:event_id>/delete", methods=["POST"])
@admin_required
def event_delete(event_id):
    query("DELETE FROM events WHERE id=%s", (event_id,), commit=True)
    flash("Event deleted.", "info")
    return redirect(url_for("admin.events"))


@admin_bp.route("/projects", methods=["GET", "POST"])
@login_required
def projects():
    if request.method == "POST":
        if session.get("role") != "admin":
            flash("Only admins can manage projects.", "danger")
            return redirect(url_for("admin.projects"))
        name = request.form.get("name", "").strip()
        if len(name) < 3:
            flash("Please enter a valid project name.", "danger")
            return redirect(url_for("admin.projects"))
        image = save_upload(request.files.get("image"), "projects")
        file_path = save_upload(request.files.get("file"), "projects")
        progress = clamp(parse_int(request.form.get("progress"), 0), 0, 100)
        status = choice(request.form.get("status"), {"planned", "active", "completed", "paused"}, "planned")
        query(
            "INSERT INTO projects (name, description, status, progress, image_path, file_path, created_by) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (
                name,
                request.form.get("description", "").strip(),
                status,
                progress,
                image,
                file_path,
                session["user_id"],
            ),
            commit=True,
        )
        flash("Project saved.", "success")
        return redirect(url_for("admin.projects"))
    q = request.args.get("q", "").strip()
    if q:
        like = f"%{q}%"
        rows = query("SELECT * FROM projects WHERE name LIKE %s OR description LIKE %s ORDER BY created_at DESC", (like, like))
    else:
        rows = query("SELECT * FROM projects ORDER BY created_at DESC")
    return render_template("projects.html", projects=rows, q=q)


@admin_bp.route("/projects/<int:project_id>/edit", methods=["GET", "POST"])
@admin_required
def project_edit(project_id):
    project = query("SELECT * FROM projects WHERE id=%s", (project_id,), one=True)
    if not project:
        flash("Project not found.", "danger")
        return redirect(url_for("admin.projects"))
    if request.method == "POST":
        image = save_upload(request.files.get("image"), "projects")
        file_path = save_upload(request.files.get("file"), "projects")
        name = request.form.get("name", "").strip()
        if len(name) < 3:
            flash("Please enter a valid project name.", "danger")
            return redirect(url_for("admin.project_edit", project_id=project_id))
        sql = "UPDATE projects SET name=%s, description=%s, status=%s, progress=%s"
        progress = clamp(parse_int(request.form.get("progress"), 0), 0, 100)
        status = choice(request.form.get("status"), {"planned", "active", "completed", "paused"}, "planned")
        params = [name, request.form.get("description", "").strip(), status, progress]
        if image:
            sql += ", image_path=%s"; params.append(image)
        if file_path:
            sql += ", file_path=%s"; params.append(file_path)
        sql += " WHERE id=%s"; params.append(project_id)
        query(sql, tuple(params), commit=True)
        flash("Project updated.", "success")
        return redirect(url_for("admin.projects"))
    return render_template("projects.html", edit_project=project, projects=query("SELECT * FROM projects ORDER BY created_at DESC"), q="")


@admin_bp.route("/projects/<int:project_id>/delete", methods=["POST"])
@admin_required
def project_delete(project_id):
    query("DELETE FROM projects WHERE id=%s", (project_id,), commit=True)
    flash("Project deleted.", "info")
    return redirect(url_for("admin.projects"))


@admin_bp.route("/announcements/new", methods=["POST"])
@admin_required
def announcement_new():
    title = request.form.get("title", "").strip()
    body = request.form.get("body", "").strip()
    if len(title) < 3 or len(body) < 5:
        flash("Please enter a valid announcement title and message.", "danger")
        return redirect(url_for("main.announcements"))
    query(
        "INSERT INTO announcements (title, body, priority, created_by) VALUES (%s,%s,%s,%s)",
        (
            title,
            body,
            choice(request.form.get("priority"), {"normal", "important", "urgent"}, "normal"),
            session["user_id"],
        ),
        commit=True,
    )
    flash("Announcement published.", "success")
    return redirect(url_for("main.announcements"))


@admin_bp.route("/feedback")
@admin_required
def feedback():
    rows = query("SELECT * FROM feedback ORDER BY created_at DESC")
    return render_template("feedback.html", feedback=rows)


@admin_bp.route("/reports/monthly.pdf")
@login_required
def monthly_pdf():
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    members = query("SELECT COUNT(*) total FROM youth_members", one=True)["total"]
    events = query("SELECT COUNT(*) total FROM events WHERE MONTH(starts_at)=MONTH(CURRENT_DATE()) AND YEAR(starts_at)=YEAR(CURRENT_DATE())", one=True)["total"]
    projects = query("SELECT COUNT(*) total FROM projects WHERE status='active'", one=True)["total"]

    def generate():
        from io import BytesIO

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        pdf.setTitle("Nyakabanda Youth Monthly Report")
        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(72, 790, "Nyakabanda Youth System")
        pdf.setFont("Helvetica", 12)
        pdf.drawString(72, 760, f"Monthly activity report generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        pdf.drawString(72, 720, f"Total youth members: {members}")
        pdf.drawString(72, 700, f"Events this month: {events}")
        pdf.drawString(72, 680, f"Active projects: {projects}")
        pdf.showPage()
        pdf.save()
        buffer.seek(0)
        return buffer.read()

    return Response(
        generate(),
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment; filename=nyakabanda_monthly_report.pdf"},
    )
