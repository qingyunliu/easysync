import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///easysync.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1小时
    JWT_REFRESH_TOKEN_EXPIRES = 604800  # 7天
    
    # CORS配置
    CORS_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '*')
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
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', 'mysql+pymysql://root:123456@localhost:3306/easysync')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'connect_args': {
            'connect_timeout': 10,
            'read_timeout': 10,
            'write_timeout': 10
        }
    }
    
    # Redis配置
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # Celery配置
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL

    # 配置文件目录
    CONFIG_DIR = os.environ.get('CONFIG_DIR', '/tmp/easysync')
    
    # 同步配置
    SYNC_TEMP_DIR = os.environ.get('SYNC_TEMP_DIR', '/tmp/easysync')
    MAX_CONCURRENT_TASKS = int(os.environ.get('MAX_CONCURRENT_TASKS', 5))
    SYNC_CHUNK_SIZE = int(os.environ.get('SYNC_CHUNK_SIZE', 1024 * 1024))  # 1MB
    
    # 存储配置
    OBS_CONFIG_PATH = os.environ.get('OBS_CONFIG_PATH', '/etc/easysync/rclone.conf')
    NFS_MOUNT_BASE = os.environ.get('NFS_MOUNT_BASE', '/mnt/easysync')

    # EasySync Agent 配置
    EASYSYNC_AGENT_VERSION = os.environ.get('EASYSYNC_AGENT_VERSION', '1.0.0')
    EASYSYNC_AGENT_INSTALL_PATH = os.environ.get('EASYSYNC_AGENT_INSTALL_PATH', '/opt/easysync/agent')
    EASYSYNC_AGENT_CONFIG_PATH = os.environ.get('EASYSYNC_AGENT_CONFIG_PATH', '/opt/easysync/agent/config.yaml')
    EASYSYNC_AGENT_LOG_PATH = os.environ.get('EASYSYNC_AGENT_LOG_PATH', '/var/log/easysync/')
    EASYSYNC_AGENT_BACKUP_PATH = os.environ.get('EASYSYNC_AGENT_BACKUP_PATH', '/opt/easysync/agent/backup')
    
    # EasySync Proxy 配置
    EASYSYNC_PROXY_VERSION = os.environ.get('EASYSYNC_PROXY_VERSION', '1.0.0')
    EASYSYNC_PROXY_INSTALL_PATH = os.environ.get('EASYSYNC_PROXY_INSTALL_PATH', '/opt/easysync/proxy')
    EASYSYNC_PROXY_CONFIG_PATH = os.environ.get('EASYSYNC_PROXY_CONFIG_PATH', '/opt/easysync/proxy/config/config.json')
    EASYSYNC_PROXY_LOG_PATH = os.environ.get('EASYSYNC_PROXY_LOG_PATH', '/var/log/easysync/')
    EASYSYNC_PROXY_BACKUP_PATH = os.environ.get('EASYSYNC_PROXY_BACKUP_PATH', '/opt/easysync/proxy/backup')
    
    # 监控配置
    PROMETHEUS_METRICS_PORT = int(os.environ.get('PROMETHEUS_METRICS_PORT', 9090))
    
    # 邮件SMTP配置
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtpdm.aliyun.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 465))
    SMTP_USER = os.environ.get('SMTP_USER', 'support@email.oneprocloud.com')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '5gYwbReCqB3wQbXf24MJ')
    # 是否使用TLS
    SMTP_USE_TLS = os.environ.get('SMTP_USE_TLS', 'true').lower() == 'true'
    SMTP_FROM = os.environ.get('SMTP_FROM', 'support@email.oneprocloud.com')
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', 'mysql+pymysql://root:123456@localhost:3306/easysync_dev')

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL', 'mysql+pymysql://root:123456@localhost:3306/easysync_test')

class ProductionConfig(Config):
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
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