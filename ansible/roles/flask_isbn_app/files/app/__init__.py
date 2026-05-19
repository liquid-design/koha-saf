"""
Flask application factory.

Houdt het current_app pattern uit de bestaande deploy zodat routes.py
@app.route decorators kan blijven gebruiken zonder Blueprint-conversie.

Security:
- SECRET_KEY wordt uit een file gelezen (systemd LoadCredential), niet uit
  een env var. Dat houdt de key uit /proc/<pid>/environ.
- CSRF-bescherming via Flask-WTF op alle POST-routes.
- Rate limiting via Flask-Limiter, vooral om externe SRU-bronnen
  (KB-NL, BnF, LoC...) te beschermen tegen misbruik.
- Sessie-cookies zijn Secure + HttpOnly + SameSite=Strict.
"""

import os
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per hour"],
    headers_enabled=True,
)


def _load_secret_key() -> str:
    """
    Laad de Flask secret key.

    Priority:
      1. FLASK_SECRET_KEY_FILE env var (door systemd LoadCredential gezet)
      2. FLASK_SECRET_KEY env var (legacy / dev)
      3. fallback warning-string (dev-only)

    Het file-based pad heeft voorrang omdat dat de key uit /proc/<pid>/environ
    houdt — een aanvaller met read-access op de procfs van de service kan
    dan nog steeds geen sessies kapen.
    """
    key_file = os.environ.get("FLASK_SECRET_KEY_FILE")
    if key_file and os.path.exists(key_file):
        with open(key_file, "r") as fh:
            key = fh.read().strip()
            if key:
                return key

    env_key = os.environ.get("FLASK_SECRET_KEY")
    if env_key:
        return env_key

    # Productie-deploys mogen hier nooit komen — de Ansible-rol genereert
    # de secret bij eerste install. Als dit toch gehit wordt, faalt CSRF
    # bij elke restart (nieuwe key = oude tokens ongeldig), wat ons attendeert.
    return "dev-only-not-secure-change-in-production"


def create_app():
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )

    # ---- Security config ----
    app.config["SECRET_KEY"] = _load_secret_key()

    # Sessie-cookies: Strict SameSite breekt geen flow want we hebben
    # geen externe POSTs naar deze app. Secure=True is veilig want
    # Apache redirect HTTP -> HTTPS.
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Strict"

    # CSRF tokens: 1 uur geldig is voldoende voor de catalogiseer-flow.
    app.config["WTF_CSRF_TIME_LIMIT"] = 3600

    # Achter Apache reverse proxy: gebruik X-Forwarded-* voor IP-detection
    # zodat rate-limiter de echte client-IP ziet, niet 127.0.0.1.
    # Apache stuurt X-Forwarded-For automatisch via ProxyPreserveHost niet,
    # daarom expliciet in vhost gezet (zie scan-vhost.conf.j2).
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    # ---- Extensions ----
    csrf.init_app(app)
    limiter.init_app(app)

    with app.app_context():
        from . import routes  # noqa: F401

    return app
