"""
Entry point voor Flask.
Lokale dev:  python3 run.py
Productie:   gunicorn -w 2 -b 127.0.0.1:5000 run:app
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
