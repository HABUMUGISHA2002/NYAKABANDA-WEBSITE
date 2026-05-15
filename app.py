import mysql.connector
from flask import Flask, redirect, render_template, url_for
from werkzeug.exceptions import RequestEntityTooLarge

from config import Config
from controllers.auth import auth_bp
from controllers.main import main_bp
from controllers.admin import admin_bp
from models.database import init_app as init_db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    init_db(app)
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    @app.route("/login")
    def login_alias():
        return redirect(url_for("auth.login"))

    @app.route("/register")
    def register_alias():
        return redirect(url_for("auth.register"))

    @app.route("/logout")
    def logout_alias():
        return redirect(url_for("auth.logout"))

    @app.route("/events")
    def events_alias():
        return redirect(url_for("admin.events"))

    @app.route("/projects")
    def projects_alias():
        return redirect(url_for("admin.projects"))

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(400)
    def bad_request(e):
        return render_template("errors/400.html"), 400

    @app.errorhandler(405)
    def method_not_allowed(e):
        return render_template("errors/400.html"), 405

    @app.errorhandler(RequestEntityTooLarge)
    def file_too_large(e):
        return render_template("errors/400.html"), 413

    @app.errorhandler(mysql.connector.Error)
    def database_error(e):
        app.logger.exception("Database error")
        return render_template("errors/500.html"), 500

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
