import os
from flask import Flask


def create_app():
    app = Flask(__name__)

    # Secret key voor flash messages. In productie zet je dit als env var.
    app.config["SECRET_KEY"] = os.environ.get(
        "FLASK_SECRET_KEY", "dev-only-not-secure-change-in-production"
    )

    with app.app_context():
        from . import routes  # noqa: F401

    return app
