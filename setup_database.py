import os
from getpass import getpass

import mysql.connector
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()


def connect(database=None):
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        database=database,
    )


def run_schema():
    with open("schema.sql", "r", encoding="utf-8") as file:
        schema = file.read()
    conn = connect()
    cursor = conn.cursor()
    for statement in [item.strip() for item in schema.split(";") if item.strip()]:
        cursor.execute(statement)
    conn.commit()
    cursor.close()
    conn.close()


def create_admin():
    database = os.getenv("MYSQL_DATABASE", "nyakabanda_youth_system")
    full_name = input("Admin full name [System Administrator]: ").strip() or "System Administrator"
    email = input("Admin email [admin@nyakabanda.rw]: ").strip().lower() or "admin@nyakabanda.rw"
    password = getpass("Admin password: ")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")

    conn = connect(database)
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO users (full_name, email, password_hash, role)
           VALUES (%s, %s, %s, 'admin')
           ON DUPLICATE KEY UPDATE full_name=VALUES(full_name), password_hash=VALUES(password_hash), role='admin'""",
        (full_name, email, generate_password_hash(password)),
    )
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Admin account ready: {email}")


if __name__ == "__main__":
    run_schema()
    create_admin()
