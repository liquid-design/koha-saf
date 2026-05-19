"""
Entry point voor Flask.
Lokale dev:  FLASK_DEBUG=1 python3 run.py
Productie:   gunicorn -w 2 -b 127.0.0.1:5000 run:app

debug=True NOOIT hardcoderen: Werkzeug debug-mode = remote code execution
zodra de PIN bekend is. We laten het via env var sturen zodat een per
ongeluk gestarte `python3 run.py` op de prod-server geen debug-server opent.
"""

import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    # 127.0.0.1 is in productie achter Apache reverse proxy; dev-runs ook lokaal.
    app.run(host="127.0.0.1", port=5000, debug=debug)
