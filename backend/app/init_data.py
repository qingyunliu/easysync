"""
应用数据初始化模块
在应用启动时自动初始化必要的基础数据
"""

import logging
from backend import db

logger = logging.getLogger(__name__)


def init_alert_data():
    """初始化告警系统数据"""
    try:
        from .alerts.alerts_data import init_all_alert_data
        init_all_alert_data()
        logger.info("告警系统数据初始化完成")
        return True
    except Exception as e:
        logger.warning(f"告警系统数据初始化失败: {str(e)}")
        return False


def init_notification_data():
    """初始化通知系统数据"""
    try:
        # 这里可以添加通知系统的初始化逻辑
        # 比如默认的通知模板、通知渠道等
        logger.info("通知系统数据初始化完成")
        return True
    except Exception as e:
        logger.warning(f"通知系统数据初始化失败: {str(e)}")
        return False


def init_system_data():
    """初始化系统基础数据"""
    try:
        # 这里可以添加系统基础数据的初始化逻辑
        # 比如默认配置、系统参数等
        logger.info("系统基础数据初始化完成")
        return True
    except Exception as e:
        logger.warning(f"系统基础数据初始化失败: {str(e)}")
        return False


def init_all_data():
    """初始化所有数据"""
    logger.info("开始初始化应用数据...")
    
    results = {
        'alert_data': init_alert_data(),
        'notification_data': init_notification_data(),
        'system_data': init_system_data()
    }
    
    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    
    logger.info(f"数据初始化完成: {success_count}/{total_count} 项成功")
    
    return results 