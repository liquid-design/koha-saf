from flask import Flask

def create_app():
    app = Flask(__name__)

    with app.app_context():
        # routes importeren zodat ze geregistreerd worden
        from . import routes

    return app
