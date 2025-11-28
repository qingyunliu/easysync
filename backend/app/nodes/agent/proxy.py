import os
import sys
import signal
import logging
import argparse
import importlib
from typing import Dict, Any


def _resolve_package_imports():
    package_root = __package__

    if not package_root:
        package_dir = os.path.dirname(os.path.abspath(__file__))
        package_root = os.path.basename(package_dir)
        parent_dir = os.path.dirname(package_dir)

        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        if package_dir not in sys.path:
            sys.path.insert(0, package_dir)

    core_agent = importlib.import_module(f"{package_root}.core.agent")
    config_settings = importlib.import_module(f"{package_root}.config.settings")
    utils_logger = importlib.import_module(f"{package_root}.utils.logger")

    return core_agent.ProxyAgent, config_settings.Settings, utils_logger.init_logging


ProxyAgent, Settings, init_logging = _resolve_package_imports()

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='EasySync Agent')
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--log-level', type=str, help='日志级别 (默认从配置文件获取)')
    return parser.parse_args()

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
    
    # 加载配置
    settings = Settings(args.config)
    config = settings.get_config()
    
    # 日志级别优先级：命令行参数 > 配置文件 > 默认值
    # 只有当用户明确指定了 --log-level 参数时才使用命令行值
    if args.log_level is not None:
        log_level = args.log_level
    else:
        log_level = config.get('log_level', 'INFO')
    
    # 设置日志配置
    log_config = {
        'log_dir': config.get('log_dir', 'logs'),
        'log_level': log_level
    }
    
    # 初始化日志系统
    init_logging(log_config)
    
    # 获取logger用于记录启动信息
    logger = logging.getLogger(__name__)
    logger.info(f"使用日志级别: {log_level}")
    
    # 注册信号处理
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGQUIT, handle_signal)
    
    try:
        # 创建代理
        agent = ProxyAgent(config)
        handle_signal.agent = agent
        
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