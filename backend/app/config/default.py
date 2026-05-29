import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-2025'
    
    # 数据库配置 - 优先使用环境变量，否则使用SQLite
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///easysync.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
    }
    
    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-2025'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES_HOURS', 1)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES_DAYS', 7)))
    
    # CORS配置
    CORS_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173')
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization']
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads')
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # 安全配置
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1小时
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = 'easysync.log'
    
    # Redis配置 - 可选
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # 配置目录
    CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config')
    
    # 通知配置文件
    NOTIFICATION_CONFIG_FILE = os.environ.get('NOTIFICATION_CONFIG_FILE', os.path.join(CONFIG_DIR, 'notification_config.json'))
    SYSTEM_NOTIFICATION_SETTINGS_FILE = os.environ.get('SYSTEM_NOTIFICATION_SETTINGS_FILE', os.path.join(CONFIG_DIR, 'system_notification_settings.json'))
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///easysync_dev.db'

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL', 'sqlite:///easysync_test.db')

class ProductionConfig(Config):
    # 生产环境使用更严格的token过期时间
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES_MINUTES', 30)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES_DAYS', 3)))
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # 生产环境安全校验
        secret_key = app.config.get('SECRET_KEY')
        jwt_secret = app.config.get('JWT_SECRET_KEY')
        cors_origins = app.config.get('CORS_ORIGINS')

        if not secret_key or secret_key == 'dev-secret-key-2025':
            raise ValueError('SECURITY: SECRET_KEY must be set in production and not use default')
        if not jwt_secret or jwt_secret == 'jwt-secret-key-2025':
            raise ValueError('SECURITY: JWT_SECRET_KEY must be set in production and not use default')
        if cors_origins == '*' or (isinstance(cors_origins, str) and cors_origins.strip() == '*'):
            raise ValueError('SECURITY: CORS_ALLOWED_ORIGINS must not be * in production')

        # 生产环境日志处理
        import logging
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            cls.LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(cls.LOG_FORMAT))
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}