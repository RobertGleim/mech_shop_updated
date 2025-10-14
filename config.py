import os

class DevelopmentConfig:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///mechanic_shop.db'
    DEBUG = True
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300

    # CORS settings (development)
    # Allow your Vite dev server and localhost
    CORS_ORIGINS = [
        os.environ.get('CORS_ORIGIN_DEV1', 'http://localhost:5173'),
        os.environ.get('CORS_ORIGIN_DEV2', 'http://127.0.0.1:5173'),
    ]
    CORS_SUPPORTS_CREDENTIALS = True
    CORS_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    CORS_HEADERS = ["Content-Type", "Authorization", "X-Requested-With"]

class TestingConfig:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test_mechanic_shop.db'
    DEBUG = True
    CACHE_TYPE = "SimpleCache"

    # For tests it's often convenient to allow dev origins
    CORS_ORIGINS = [
        os.environ.get('CORS_ORIGIN_TEST', 'http://localhost:5173')
    ]
    CORS_SUPPORTS_CREDENTIALS = True
    CORS_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    CORS_HEADERS = ["Content-Type", "Authorization", "X-Requested-With"]

class ProductionConfig:
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or 'sqlite:///mechanic_shop.db'
    CACHE_TYPE = "SimpleCache"

    # Production: allow your production API domain for all endpoints including /api/docs
    CORS_ORIGINS = [
        origin for origin in [
            'https://mech-shop-api.onrender.com',
            os.environ.get('CORS_ORIGIN_PROD', 'https://your-production-frontend.example.com'),
            # Allow additional origins via environment variable
            os.environ.get('CORS_ORIGIN_ADDITIONAL')
        ] if origin
    ]
    
    # Dynamic localhost handling is done in app/__init__.py based on ALLOW_DEV_CORS
    # This keeps production config clean while allowing flexible development
    CORS_SUPPORTS_CREDENTIALS = os.environ.get('ALLOW_DEV_CORS', '').lower() in ('1', 'true', 'yes')
        
    CORS_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    CORS_HEADERS = ["Content-Type", "Authorization", "X-Requested-With", "Accept"]