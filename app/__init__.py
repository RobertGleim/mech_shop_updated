from flask import Flask
import os
from .models import db
from .extenstions import ma, limiter, cache
from .blueprints.customers import customers_bp
from .blueprints.mechanics import mechanics_bp
from .blueprints.service_tickets import service_tickets_bp
from .blueprints.ticket_mechanics import ticket_mechanics_bp
from .blueprints.inventory import inventory_bp
from .blueprints.item_descriptions import item_descriptions_bp
from .blueprints.invoice import invoice_bp
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS

SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.yaml'


def create_app(config_name='DevelopmentConfig'):
    """Application factory

    Creates the Flask app, loads configuration, initializes extensions and
    registers blueprints. CORS is configured inside the factory so app.config
    is available (avoids import-time access to app.config).
    """
    app = Flask(__name__, instance_relative_config=False)

    # Load configuration from config module
    app.config.from_object(f'config.{config_name}')

    # Initialize extensions that require the app
    db.init_app(app)
    ma.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)

    # Configure Swagger UI blueprint
    swagger_blueprint = get_swaggerui_blueprint(SWAGGER_URL, API_URL, config={'app_name': "Mechanic Shop API"})

    # === CORS configuration ===
    cors_origins = app.config.get('CORS_ORIGINS', ["http://localhost:5173"])
    # Ensure list type
    if isinstance(cors_origins, str):
        cors_origins = [cors_origins]
    cors_supports_credentials = app.config.get('CORS_SUPPORTS_CREDENTIALS', True)
    cors_methods = app.config.get('CORS_METHODS', ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    cors_headers = app.config.get('CORS_HEADERS', ["Content-Type", "Authorization", "X-Requested-With"])

    # Check if we should allow all localhost addresses
    allow_local = os.environ.get('ALLOW_LOCALHOST_CORS', os.environ.get('ALLOW_DEV_CORS', ''))
    # Auto-enable localhost for common development scenarios
    is_development = (
        app.debug or 
        os.environ.get('FLASK_ENV') == 'development' or
        os.environ.get('RENDER') is None  # Not on Render = likely local development
    )
    
    if str(allow_local).lower() in ('1', 'true', 'yes') or is_development:
        # Add specific localhost origins that work better than regex
        localhost_origins = [
            "http://localhost:3000", "http://127.0.0.1:3000",
            "http://localhost:5173", "http://127.0.0.1:5173", 
            "http://localhost:8080", "http://127.0.0.1:8080",
            "http://localhost:4173", "http://127.0.0.1:4173",
            "https://localhost:3000", "https://127.0.0.1:3000",
            "https://localhost:5173", "https://127.0.0.1:5173"
        ]
        for origin in localhost_origins:
            if origin not in cors_origins:
                cors_origins.append(origin)

    CORS(
        app,
        origins=cors_origins,
        supports_credentials=cors_supports_credentials,
        methods=cors_methods,
        allow_headers=cors_headers
    )
    # ==========================

    # Register blueprints
    app.register_blueprint(customers_bp, url_prefix='/customers')
    app.register_blueprint(mechanics_bp, url_prefix='/mechanics')
    app.register_blueprint(service_tickets_bp, url_prefix='/service_tickets')
    app.register_blueprint(ticket_mechanics_bp, url_prefix='/ticket_mechanics')
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    app.register_blueprint(item_descriptions_bp, url_prefix='/item_descriptions')
    app.register_blueprint(invoice_bp, url_prefix='/invoice')
    app.register_blueprint(swagger_blueprint, url_prefix=SWAGGER_URL)

    return app



