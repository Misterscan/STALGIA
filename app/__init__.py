from flask import Flask
from flask_cors import CORS
from flasgger import Swagger
import os
from .config import BASE_DIR

def create_app():
    app = Flask(__name__, static_folder=os.path.join(BASE_DIR, 'static'), static_url_path='')
    CORS(app)
    
    # Initialize Swagger UI
    swagger = Swagger(app, template={
        "info": {
            "title": "STALGIA API",
            "description": "API for STALGIA music generation using musicpy and Gemini API.",
            "version": "1.3.0"
        }
    })

    # Register blueprints
    from .routes.api import api_bp
    app.register_blueprint(api_bp)

    @app.route('/')
    def index():
        return app.send_static_file('new-index.html')

    return app
