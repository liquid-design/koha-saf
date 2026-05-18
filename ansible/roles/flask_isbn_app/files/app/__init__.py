"""
Flask application factory.

Houdt het current_app pattern uit de bestaande deploy zodat routes.py
@app.route decorators kan blijven gebruiken zonder Blueprint-conversie.
"""

import os
from flask import Flask


def create_app():
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )

    # Secret key voor flash messages. In productie via env var.
    app.config["SECRET_KEY"] = os.environ.get(
        "FLASK_SECRET_KEY", "dev-only-not-secure-change-in-production"
    )

    with app.app_context():
        from . import routes  # noqa: F401

    return app
