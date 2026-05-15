import os
import re

import mysql.connector
from mysql.connector import errorcode
from flask import current_app, g
from werkzeug.security import generate_password_hash


def _connection_config(app, include_database=True):
    config = {
        "host": app.config["MYSQL_HOST"],
        "user": app.config["MYSQL_USER"],
        "password": app.config["MYSQL_PASSWORD"],
        "port": app.config["MYSQL_PORT"],
    }
    if include_database:
        config["database"] = app.config["MYSQL_DATABASE"]
    return config


def _quote_identifier(value):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", value or ""):
        raise ValueError("MYSQL_DATABASE contains unsupported characters.")
    return f"`{value}`"


def get_db():
    if "db" not in g:
        g.db = mysql.connector.connect(**_connection_config(current_app))
    return g.db


def query(sql, params=None, one=False, commit=False):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params or ())
        if commit:
            conn.commit()
            return cursor.lastrowid
        rows = cursor.fetchall()
        return (rows[0] if rows else None) if one else rows
    except Exception:
        if commit:
            conn.rollback()
        raise
    finally:
        cursor.close()


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def ensure_uploads(app):
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    for folder in ("members", "projects", "events", "reports"):
        os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], folder), exist_ok=True)


def ensure_database(app):
    database = _quote_identifier(app.config["MYSQL_DATABASE"])
    conn = mysql.connector.connect(**_connection_config(app, include_database=False))
    cursor = conn.cursor()
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def ensure_schema(app):
    schema_path = os.path.join(app.root_path, "schema.sql")
    if not os.path.exists(schema_path):
        return
    with app.app_context():
        conn = get_db()
        cursor = conn.cursor()
        with open(schema_path, "r", encoding="utf-8") as file:
            statements = [item.strip() for item in file.read().split(";") if item.strip()]
        for statement in statements:
            upper_statement = statement.upper()
            if upper_statement.startswith("CREATE DATABASE") or upper_statement.startswith("USE "):
                continue
            cursor.execute(statement)
        conn.commit()
        cursor.close()


def ensure_columns(app):
    with app.app_context():
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE events ADD COLUMN image_path VARCHAR(255) AFTER location")
            conn.commit()
        except mysql.connector.Error as error:
            if error.errno not in (errorcode.ER_DUP_FIELDNAME, errorcode.ER_NO_SUCH_TABLE):
                raise
        finally:
            cursor.close()


def ensure_admin(app):
    email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    password = os.getenv("ADMIN_PASSWORD", "")
    full_name = os.getenv("ADMIN_FULL_NAME", "System Administrator").strip() or "System Administrator"
    if not email or len(password) < 8:
        return
    with app.app_context():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO users (full_name, email, password_hash, role)
               VALUES (%s, %s, %s, 'admin')
               ON DUPLICATE KEY UPDATE full_name=VALUES(full_name), role='admin'""",
            (full_name, email, generate_password_hash(password)),
        )
        conn.commit()
        cursor.close()


def init_app(app):
    app.teardown_appcontext(close_db)
    ensure_uploads(app)
    try:
        ensure_database(app)
        ensure_schema(app)
        ensure_columns(app)
        ensure_admin(app)
        app.config["DATABASE_READY"] = True
    except mysql.connector.Error:
        app.config["DATABASE_READY"] = False
        app.logger.exception(
            "Database setup skipped. Check MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, "
            "MYSQL_DATABASE, and MYSQL_PORT environment variables."
        )
