from backend import create_app
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = create_app()

if __name__ == '__main__':
    logger.info('Starting HTTP server...')
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True,
        use_reloader=True
    )