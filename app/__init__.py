from flask import Flask, app 
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


swagger_blueprint = get_swaggerui_blueprint(SWAGGER_URL, API_URL, config={'app_name': "Mechanic Shop API"})

cors_origins = app.config.get('CORS_ORIGINS', ["http://localhost:5173"])
cors_supports_credentials = app.config.get('CORS_SUPPORTS_CREDENTIALS', True)
cors_methods = app.config.get('CORS_METHODS', ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
cors_headers = app.config.get('CORS_HEADERS', ["Content-Type", "Authorization", "X-Requested-With"])


def create_app(config_name):
    
    app = Flask(__name__)
    app.config.from_object(f'config.{config_name}')
    # Allow requests from your frontend
    CORS(
        app,
        resources={r"/*": {"origins": cors_origins}},
        supports_credentials=cors_supports_credentials,
        methods=cors_methods,
        allow_headers=cors_headers
)
    
    
    db.init_app(app)
    ma.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)
    
    
    app.register_blueprint(customers_bp, url_prefix='/customers')
    app.register_blueprint(mechanics_bp, url_prefix='/mechanics')
    app.register_blueprint(service_tickets_bp, url_prefix='/service_tickets')
    app.register_blueprint(ticket_mechanics_bp, url_prefix='/ticket_mechanics')
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    app.register_blueprint(item_descriptions_bp, url_prefix='/item_descriptions')
    app.register_blueprint(invoice_bp, url_prefix='/invoice')
    app.register_blueprint(swagger_blueprint, url_prefix=SWAGGER_URL)
   
    
    
    return app


