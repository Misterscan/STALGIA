from flask import Flask
from flask_cors import CORS
import os
from .config import BASE_DIR

def create_app():
    app = Flask(__name__, static_folder=os.path.join(BASE_DIR, 'static'))
    CORS(app)

    # Register blueprints
    from .routes.api import api_bp
    app.register_blueprint(api_bp)

    return app
