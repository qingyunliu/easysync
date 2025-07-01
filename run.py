from backend import create_app, socketio
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = create_app()

if __name__ == '__main__':
    logger.info('Starting WebSocket server...')
    socketio.run(
        app,
        host='0.0.0.0',
        port=5001,
        debug=True,
        use_reloader=False,  # 禁用重载器，避免重复初始化
        log_output=True,
        allow_unsafe_werkzeug=True
    ) 