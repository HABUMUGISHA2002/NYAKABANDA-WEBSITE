from flask import Flask, render_template

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

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
