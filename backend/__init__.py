from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from celery import Celery
import os
import logging
from dotenv import load_dotenv
from flask_socketio import SocketIO

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 初始化扩展
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
celery = Celery()

# 创建SocketIO实例
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode='threading',
    logger=True,
    engineio_logger=True,
    path='/ws/socket.io'  # 修改为正确的 WebSocket 路径
)

def create_app(config_name=None):
    """创建并配置 Flask 应用实例"""
    app = Flask(__name__)
    
    # 配置加载
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    # 从配置类加载配置
    from backend.app.config import config
    app.config.from_object(config[config_name])
    
    # 确保上传目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'avatars'), exist_ok=True)
    
    # 配置静态文件服务
    @app.route('/uploads/avatars/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], 'avatars'), filename)
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # 配置 CORS
    # 从环境变量获取允许的源，默认为开发环境的设置
    allowed_origins = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000').split(',')
    
    # 配置 CORS
    CORS(app, 
         resources={
             r"/api/*": {
                 "origins": allowed_origins,
                 "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                 "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
                 "expose_headers": ["Content-Range", "X-Content-Range"],
                 "supports_credentials": True,
                 "max_age": 86400  # 预检请求缓存时间，单位秒
             },
             r"/uploads/*": {  # 添加对静态文件路由的CORS支持
                 "origins": allowed_origins,
                 "methods": ["GET"],
                 "supports_credentials": True
             }
         },
         supports_credentials=True,
         automatic_options=True)  # 自动处理 OPTIONS 请求
    
    # 初始化Celery
    celery.conf.update(app.config)
    
    # 初始化WebSocket
    from .app.websocket import init_websocket
    init_websocket(app)
    
    # 注册蓝图
    from .app.auth import auth_bp
    from .app.users import users_bp
    from .app.storages import storages_bp
    from .app.sync import sync_bp
    from .app.tasks import tasks_bp
    from .app.notifications import notifications_bp
    from .app.dashboard import dashboard_bp
    from .app.clients import clients_bp
    from .app.monitor import monitor_bp
    from .app.nodes import nodes_bp
    from .app.agent_api import agent_bp
    from .app.settings import settings_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(storages_bp, url_prefix='/api/storages')
    app.register_blueprint(sync_bp, url_prefix='/api/sync')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(clients_bp, url_prefix='/api/clients')
    app.register_blueprint(monitor_bp, url_prefix='/api/monitor')
    app.register_blueprint(nodes_bp, url_prefix='/api/nodes')
    app.register_blueprint(agent_bp, url_prefix='/api/agent')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')

    # 注册错误处理
    from .app.errors import register_error_handlers
    register_error_handlers(app)
    
    # 创建数据库表
    try:
        with app.app_context():
            db.create_all()
            logger.debug("数据库表创建成功")
    except Exception as e:
        logger.error(f"数据库连接失败: {str(e)}")
        # 在开发环境中，我们可以继续运行，但在生产环境中应该退出
        if os.getenv('FLASK_ENV') == 'production':
            raise
    
    return app

__version__ = '0.1.0'
__all__ = ['create_app', 'db', 'celery', 'socketio'] 