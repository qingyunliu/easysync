import os
import sys
import signal
import logging
import argparse
from typing import Dict, Any
from .core.agent import ProxyAgent
from .config.settings import Settings

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='EasySync Agent')
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--log-level', type=str, default='INFO', help='日志级别')
    return parser.parse_args()

def setup_logging(log_level: str):
    """设置日志"""
    # 创建日志目录
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # 设置日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)
    
    # 设置控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # 设置文件处理器
    file_handler = logging.FileHandler(
        os.path.join(log_dir, 'agent.log'),
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

def handle_signal(signum, frame):
    """处理信号"""
    logging.info(f"Received signal {signum}")
    if hasattr(handle_signal, 'agent'):
        handle_signal.agent.stop()
    sys.exit(0)

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    
    # 设置日志
    setup_logging(args.log_level)
    
    # 加载配置
    settings = Settings(args.config)
    config = settings.get_config()
    
    # 注册信号处理
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGQUIT, handle_signal)
    
    try:
        # 创建代理
        agent = ProxyAgent(config)
        handle_signal.agent = agent  # 保存agent引用用于信号处理
        
        # 启动代理
        agent.start()
        
        # 等待代理运行
        agent.wait()
        
    except Exception as e:
        logging.error(f"Error in main: {e}")
        sys.exit(1)
    finally:
        # 停止代理
        try:
            if 'agent' in locals():
                agent.stop()
        except Exception as e:
            logging.error(f"Error stopping agent: {e}")

if __name__ == '__main__':
    main() 