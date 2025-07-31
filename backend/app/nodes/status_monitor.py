# -*- coding: utf-8 -*-
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
from backend import db
from backend.app.models import Node

logger = logging.getLogger(__name__)

class NodeStatusMonitor:
    """节点状态监控器"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.app = None  # Flask应用实例
        self.check_interval = 60  # 检查间隔（秒）
        self.heartbeat_timeout = 90  # 心跳超时时间（秒）
        self.agent_timeout = 120  # Agent超时时间（秒）
        
    def start(self):
        """启动状态监控器"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run_monitor)
        self.thread.daemon = True
        self.thread.start()
        logger.info("节点状态监控器已启动")
        
    def stop(self):
        """停止状态监控器"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("节点状态监控器已停止")
        
    def _run_monitor(self):
        """运行监控循环"""
        while self.running:
            try:
                self._check_all_nodes_status()
            except Exception as e:
                logger.error(f"节点状态检查出错: {e}")
                
            time.sleep(self.check_interval)
            
    def _check_all_nodes_status(self):
        """检查所有节点状态"""
        try:
            with self.app.app_context():
                nodes = Node.query.all()
                
                for node in nodes:
                    self._update_node_status(node)
                    
                # 批量提交状态更新
                db.session.commit()
                
        except Exception as e:
            logger.error(f"检查节点状态失败: {e}")
            db.session.rollback()
            
    def _update_node_status(self, node: Node):
        """更新单个节点状态"""
        now = datetime.utcnow()
        status_changed = False
        
        # 检查心跳状态
        if node.last_heartbeat:
            time_since_heartbeat = now - node.last_heartbeat
            heartbeat_timeout = time_since_heartbeat.total_seconds() > self.heartbeat_timeout
            
            # 更新节点在线状态
            if heartbeat_timeout and node.status == 'online':
                node.status = 'offline'
                status_changed = True
                logger.warning(f"节点 {node.id} ({node.name}) 心跳超时，状态更新为offline")
            elif not heartbeat_timeout and node.status == 'offline':
                node.status = 'online'
                status_changed = True
                logger.info(f"节点 {node.id} ({node.name}) 心跳恢复，状态更新为online")
                
            # 更新Agent状态
            agent_timeout = time_since_heartbeat.total_seconds() > self.agent_timeout
            if agent_timeout and node.agent_status in ['running', 'active']:
                node.agent_status = 'inactive'
                status_changed = True
                logger.warning(f"节点 {node.id} ({node.name}) Agent超时，状态更新为inactive")
        else:
            # 没有心跳记录，设置为离线
            if node.status != 'offline':
                node.status = 'offline'
                status_changed = True
                logger.warning(f"节点 {node.id} ({node.name}) 无心跳记录，状态更新为offline")
                
            if node.agent_status != 'inactive':
                node.agent_status = 'inactive'
                status_changed = True
                logger.warning(f"节点 {node.id} ({node.name}) Agent状态更新为inactive")
        
        if status_changed:
            logger.info(f"节点 {node.id} ({node.name}) 状态更新: status={node.status}, agent_status={node.agent_status}")
            
    def get_node_health_info(self, node_id: str) -> Dict[str, Any]:
        """获取节点健康信息"""
        try:
            node = Node.query.get(node_id)
            if not node:
                return {'error': '节点不存在'}
                
            now = datetime.utcnow()
            health_info = {
                'node_id': node.id,
                'name': node.name,
                'status': node.status,
                'agent_status': node.agent_status,
                'last_heartbeat': node.last_heartbeat.isoformat() if node.last_heartbeat else None,
                'is_healthy': self._is_node_healthy(node),
                'uptime_seconds': 0
            }
            
            if node.last_heartbeat:
                time_since_heartbeat = now - node.last_heartbeat
                health_info['time_since_last_heartbeat'] = time_since_heartbeat.total_seconds()
                health_info['heartbeat_status'] = 'normal' if time_since_heartbeat.total_seconds() < self.heartbeat_timeout else 'timeout'
            else:
                health_info['time_since_last_heartbeat'] = None
                health_info['heartbeat_status'] = 'no_heartbeat'
                
            return health_info
            
        except Exception as e:
            logger.error(f"获取节点健康信息失败: {e}")
            return {'error': str(e)}
            
    def _is_node_healthy(self, node: Node) -> bool:
        """判断节点是否健康"""
        if not node.last_heartbeat:
            return False
            
        time_since_heartbeat = datetime.utcnow() - node.last_heartbeat
        return time_since_heartbeat.total_seconds() < self.heartbeat_timeout
        
    def force_check_node(self, node_id: str) -> Dict[str, Any]:
        """强制检查单个节点状态"""
        try:
            node = Node.query.get(node_id)
            if not node:
                return {'error': '节点不存在'}
                
            old_status = node.status
            old_agent_status = node.agent_status
            
            self._update_node_status(node)
            db.session.commit()
            
            return {
                'success': True,
                'node_id': node_id,
                'old_status': old_status,
                'new_status': node.status,
                'old_agent_status': old_agent_status,
                'new_agent_status': node.agent_status,
                'status_changed': old_status != node.status or old_agent_status != node.agent_status
            }
            
        except Exception as e:
            logger.error(f"强制检查节点状态失败: {e}")
            db.session.rollback()
            return {'error': str(e)}

# 全局实例
_status_monitor = None

def get_status_monitor() -> NodeStatusMonitor:
    """获取节点状态监控器实例"""
    global _status_monitor
    if _status_monitor is None:
        _status_monitor = NodeStatusMonitor()
    return _status_monitor