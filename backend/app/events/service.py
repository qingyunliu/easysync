"""
事件服务模块
负责处理系统事件的创建、存储和告警触发
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from backend import db
from backend.app.models.event import Event
from backend.app.alerts.evaluator import AlertEvaluator
from backend.app.alerts.services import AlertService

logger = logging.getLogger(__name__)

class EventService:
    """事件服务类"""
    
    def __init__(self):
        self.alert_evaluator = AlertEvaluator()
        self.alert_service = AlertService()
    
    def create_event(self, user_id: str, event_type: str, event_action: str, 
                    event_result: str, message: str = None, details: Dict[str, Any] = None,
                    client_id: str = None, node_id: str = None) -> Event:
        """
        创建事件并触发告警
        
        Args:
            user_id: 用户ID
            event_type: 事件类型
            event_action: 事件动作
            event_result: 事件结果
            message: 事件消息
            details: 事件详情
            client_id: 客户端ID（可选）
            node_id: 节点ID（可选）
            
        Returns:
            Event: 创建的事件对象
        """
        try:
            # 创建事件
            event = Event.create_event(
                user_id=user_id,
                client_id=client_id,
                node_id=node_id,
                event_type=event_type,
                event_action=event_action,
                event_result=event_result,
                message=message,
                details=details
            )
            
            # 评估告警策略
            triggered_alerts = self.alert_evaluator.evaluate_event(event)
            
            # 处理触发的告警
            for alert_info in triggered_alerts:
                policy = alert_info['policy']
                triggered_at = alert_info['triggered_at']
                
                # 创建告警实例
                alert_instance = self.alert_evaluator.create_alert_instance(
                    policy, event=event, triggered_at=triggered_at
                )
                
                if alert_instance:
                    # 发送通知
                    self.alert_service._send_notifications(policy, alert_instance)
            
            logger.info(f"Event created: {event.id}, triggered {len(triggered_alerts)} alerts")
            return event
            
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            raise
    
    def create_user_event(self, user_id: str, event_action: str, event_result: str,
                         message: str = None, details: Dict[str, Any] = None) -> Event:
        """创建用户相关事件"""
        return self.create_event(
            user_id=user_id,
            event_type='user',
            event_action=event_action,
            event_result=event_result,
            message=message,
            details=details
        )
    
    def create_storage_event(self, user_id: str, event_action: str, event_result: str,
                           message: str = None, details: Dict[str, Any] = None,
                           client_id: str = None, node_id: str = None) -> Event:
        """创建存储相关事件"""
        return self.create_event(
            user_id=user_id,
            event_type='storage',
            event_action=event_action,
            event_result=event_result,
            message=message,
            details=details,
            client_id=client_id,
            node_id=node_id
        )
    
    def create_agent_event(self, user_id: str, event_action: str, event_result: str,
                          message: str = None, details: Dict[str, Any] = None,
                          node_id: str = None) -> Event:
        """创建代理相关事件"""
        return self.create_event(
            user_id=user_id,
            event_type='agent',
            event_action=event_action,
            event_result=event_result,
            message=message,
            details=details,
            node_id=node_id
        )
    
    def create_client_event(self, user_id: str, event_action: str, event_result: str,
                           message: str = None, details: Dict[str, Any] = None,
                           client_id: str = None) -> Event:
        """创建客户端相关事件"""
        return self.create_event(
            user_id=user_id,
            event_type='client',
            event_action=event_action,
            event_result=event_result,
            message=message,
            details=details,
            client_id=client_id
        )
    
    def create_task_event(self, user_id: str, event_action: str, event_result: str,
                         message: str = None, details: Dict[str, Any] = None,
                         client_id: str = None, node_id: str = None) -> Event:
        """创建任务相关事件"""
        return self.create_event(
            user_id=user_id,
            event_type='task',
            event_action=event_action,
            event_result=event_result,
            message=message,
            details=details,
            client_id=client_id,
            node_id=node_id
        )
    
    def create_system_event(self, user_id: str, event_action: str, event_result: str,
                           message: str = None, details: Dict[str, Any] = None) -> Event:
        """创建系统相关事件"""
        return self.create_event(
            user_id=user_id,
            event_type='system',
            event_action=event_action,
            event_result=event_result,
            message=message,
            details=details
        )
    
    def get_events(self, user_id: str = None, event_type: str = None, 
                  event_action: str = None, event_result: str = None,
                  start_time: datetime = None, end_time: datetime = None,
                  page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """
        获取事件列表
        
        Args:
            user_id: 用户ID过滤
            event_type: 事件类型过滤
            event_action: 事件动作过滤
            event_result: 事件结果过滤
            start_time: 开始时间
            end_time: 结束时间
            page: 页码
            per_page: 每页数量
            
        Returns:
            Dict: 包含事件列表和分页信息
        """
        try:
            query = Event.query
            
            # 应用过滤条件
            if user_id:
                query = query.filter(Event.user_id == user_id)
            if event_type:
                query = query.filter(Event.event_type == event_type)
            if event_action:
                query = query.filter(Event.event_action == event_action)
            if event_result:
                query = query.filter(Event.event_result == event_result)
            if start_time:
                query = query.filter(Event.timestamp >= start_time)
            if end_time:
                query = query.filter(Event.timestamp <= end_time)
            
            # 分页
            total = query.count()
            events = query.order_by(Event.timestamp.desc()).offset((page - 1) * per_page).limit(per_page).all()
            
            return {
                'events': [event.to_dict() for event in events],
                'total': total,
                'current_page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
            
        except Exception as e:
            logger.error(f"Error getting events: {e}")
            return {'events': [], 'total': 0, 'current_page': page, 'per_page': per_page, 'total_pages': 0}
    
    def get_event_statistics(self, user_id: str = None, time_range: str = '24h') -> Dict[str, Any]:
        """
        获取事件统计信息
        
        Args:
            user_id: 用户ID
            time_range: 时间范围 (24h, 7d, 30d)
            
        Returns:
            Dict: 事件统计信息
        """
        try:
            from datetime import timedelta
            
            # 计算时间范围
            now = datetime.utcnow()
            if time_range == '24h':
                start_time = now - timedelta(hours=24)
            elif time_range == '7d':
                start_time = now - timedelta(days=7)
            elif time_range == '30d':
                start_time = now - timedelta(days=30)
            else:
                start_time = now - timedelta(hours=24)
            
            query = Event.query.filter(Event.timestamp >= start_time)
            if user_id:
                query = query.filter(Event.user_id == user_id)
            
            # 按事件类型统计
            type_stats = {}
            type_counts = db.session.query(Event.event_type, db.func.count(Event.id)).filter(
                Event.timestamp >= start_time
            ).group_by(Event.event_type).all()
            
            for event_type, count in type_counts:
                type_stats[event_type] = count
            
            # 按事件结果统计
            result_stats = {}
            result_counts = db.session.query(Event.event_result, db.func.count(Event.id)).filter(
                Event.timestamp >= start_time
            ).group_by(Event.event_result).all()
            
            for event_result, count in result_counts:
                result_stats[event_result] = count
            
            return {
                'total_events': query.count(),
                'event_types': type_stats,
                'event_results': result_stats,
                'time_range': time_range
            }
            
        except Exception as e:
            logger.error(f"Error getting event statistics: {e}")
            return {}


# 全局事件服务实例
event_service = EventService() 