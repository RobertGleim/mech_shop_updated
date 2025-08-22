

class DevelopmentConfig:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///mechanic_shop.db'
    DEBUG = True
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300
    
class TestingConfig:
    pass

class ProductionConfig:    
    pass