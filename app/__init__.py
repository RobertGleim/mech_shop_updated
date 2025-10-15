from flask import Flask, request, Response, jsonify
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
import logging
import traceback

SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.yaml'


def create_app(config_name='DevelopmentConfig'):
    """Application factory"""
    app = Flask(__name__, instance_relative_config=False)

    # Load configuration from config module
    app.config.from_object(f'config.{config_name}')

    # Prevent Flask from redirecting between trailing-slash/no-trailing-slash URLs.
    # Redirects can remove Authorization headers — disabling strict slashes avoids that.
    app.url_map.strict_slashes = False

    # Initialize extensions that require the app
    db.init_app(app)
    ma.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)

    # Configure Swagger UI blueprint
    swagger_blueprint = get_swaggerui_blueprint(SWAGGER_URL, API_URL, config={'app_name': "Mechanic Shop API"})

    # === Enhanced CORS configuration ===
    cors_origins = app.config.get('CORS_ORIGINS', ["http://localhost:5173"])
    # Ensure list type
    if isinstance(cors_origins, str):
        cors_origins = [cors_origins]
    cors_supports_credentials = app.config.get('CORS_SUPPORTS_CREDENTIALS', True)
    cors_methods = app.config.get('CORS_METHODS', ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    cors_headers = app.config.get('CORS_HEADERS', ["Content-Type", "Authorization", "X-Requested-With"])

    # Enhanced CORS configuration with explicit OPTIONS handling
    # ensure 'resources' covers all endpoints so CORS rules apply consistently
    CORS(
        app,
        resources={r"/*": {"origins": cors_origins}},
        origins=cors_origins,
        supports_credentials=cors_supports_credentials,
        methods=cors_methods,
        allow_headers=cors_headers,
        expose_headers=["Content-Range", "X-Content-Range"],
        send_wildcard=False,
        automatic_options=True
    )

    # Add explicit OPTIONS handler for all routes
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            res = Response(status=200)
            res.headers['X-Content-Type-Options'] = 'nosniff'
            res.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
            res.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS,PATCH'
            res.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,X-Requested-With'
            res.headers['Access-Control-Allow-Credentials'] = 'true'
            return res

    # Ensure all real responses include CORS headers (prevents Authorization being dropped)
    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get('Origin') or '*'
        # Only echo back allowed origin or '*' (keeps responses explicit)
        if cors_origins and origin != '*' and origin in cors_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
        else:
            response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = ','.join(cors_methods)
        response.headers['Access-Control-Allow-Headers'] = ','.join(cors_headers)
        # helpful expose header
        response.headers.setdefault('Access-Control-Expose-Headers', 'Content-Range, X-Content-Range')
        return response

    # Log all incoming headers for debugging
    @app.before_request
    def log_incoming_headers():
        app.logger.debug(f"Incoming request: {request.method} {request.path}")
        app.logger.debug(f"Headers: {dict(request.headers)}")

    # Enable debug logging to console
    if not app.logger.handlers:
        logging.basicConfig(level=logging.DEBUG)
    app.logger.setLevel(logging.DEBUG if app.config.get('DEBUG') else logging.INFO)

    # Log request bodies for debug (helpful to see what the frontend sent when a 500 occurs)
    @app.before_request
    def log_request_body_for_debug():
        # Only log for non-OPTIONS mutating methods and when debugging
        if app.debug and request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            try:
                body = request.get_json(silent=True)
                if body is None:
                    # Fallback to raw data if not JSON-parsable
                    body = request.get_data(as_text=True)
                app.logger.debug("Incoming request %s %s body: %s", request.method, request.path, body)
            except Exception as e:
                app.logger.debug("Failed to parse request body for %s %s: %s", request.method, request.path, e)

    # Register blueprints
    app.register_blueprint(customers_bp, url_prefix='/customers')
    app.register_blueprint(mechanics_bp, url_prefix='/mechanics')
    app.register_blueprint(service_tickets_bp, url_prefix='/service_tickets')
    app.register_blueprint(ticket_mechanics_bp, url_prefix='/ticket_mechanics')
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    app.register_blueprint(item_descriptions_bp, url_prefix='/item_descriptions')
    app.register_blueprint(invoice_bp, url_prefix='/invoice')
    app.register_blueprint(swagger_blueprint, url_prefix=SWAGGER_URL)

    # Simple health endpoint for quick availability checks (useful from frontend /dev proxy)
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({"status": "ok"}), 200

    # Global exception handler that returns JSON and logs a traceback to assist debugging 500s
    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        app.logger.error("Unhandled exception: %s", e)
        tb = traceback.format_exc()
        app.logger.error(tb)
        # Include traceback in response only in DEBUG mode to aid local debugging
        payload = {"message": str(e), "type": type(e).__name__}
        if app.debug:
            payload["traceback"] = tb
        response = jsonify(payload)
        response.status_code = 500
        return response

    return app