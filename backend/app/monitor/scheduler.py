import logging
import threading
import time
from datetime import datetime
from typing import Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from backend import db
from backend.app.models import User
from .service import MonitorService

logger = logging.getLogger(__name__)

class MonitorScheduler:
    """系统监控调度器"""
    
    def __init__(self):
        self.running = False
        self.scheduler = BackgroundScheduler()
        self.monitor_service = MonitorService()
        self.app = None  # Flask应用实例
        
    def start(self):
        """启动监控调度器"""
        if self.running:
            return
            
        try:
            # 启动APScheduler
            if not self.scheduler.running:
                self.scheduler.start()
            
            # 添加系统监控数据收集任务
            self.scheduler.add_job(
                func=self._collect_system_metrics,
                trigger=IntervalTrigger(seconds=10),
                id='system_monitoring_collection',
                name='系统监控数据收集',
                replace_existing=True
            )
            
            self.running = True
            logger.info("系统监控调度器已启动")
            
        except Exception as e:
            logger.error(f"启动系统监控调度器失败: {str(e)}")
            
    def stop(self):
        """停止监控调度器"""
        if not self.running:
            return
            
        try:
            # 停止APScheduler
            if self.scheduler.running:
                self.scheduler.shutdown()
                
            self.running = False
            logger.info("系统监控调度器已停止")
            
        except Exception as e:
            logger.error(f"停止系统监控调度器失败: {str(e)}")
            
    def _collect_system_metrics(self):
        """收集系统监控指标"""
        try:
            with self.app.app_context():
                # 获取所有活跃用户
                active_users = User.query.filter_by(is_active=True).all()
                
                for user in active_users:
                    try:
                        self.monitor_service.collect_system_metrics(user.id)
                        logger.info(f"用户 {user.username} 的系统监控数据收集成功")
                    except Exception as e:
                        logger.error(f"用户 {user.username} 的系统监控数据收集失败: {str(e)}")
                        
        except Exception as e:
            logger.error(f"系统监控数据收集任务失败: {str(e)}")
            
    def get_scheduler_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        return {
            'running': self.running,
            'scheduler_running': self.scheduler.running,
            'jobs': [job.id for job in self.scheduler.get_jobs()]
        }

# 全局监控调度器实例
monitor_scheduler = MonitorScheduler() 