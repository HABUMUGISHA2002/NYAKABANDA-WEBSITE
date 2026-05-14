import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-change-me")
    MYSQL_HOST = os.getenv("MYSQL_HOST") or os.getenv("MYSQLHOST", "localhost")
    MYSQL_USER = os.getenv("MYSQL_USER") or os.getenv("MYSQLUSER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD") or os.getenv("MYSQLPASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE") or os.getenv("MYSQLDATABASE", "nyakabanda_youth_system")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT") or os.getenv("MYSQLPORT", "3306"))
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", os.path.join(os.getcwd(), "uploads"))
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024
