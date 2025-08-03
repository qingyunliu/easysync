import logging
from datetime import datetime
from typing import Dict, Any, Optional
from backend import db
from backend.app.models.event import Event
from backend.app.alerts.evaluator import AlertEvaluator
from backend.app.alerts.services import AlertService

logger = logging.getLogger(__name__)


class EventService:
    """事件处理服务"""
    
    def __init__(self):
        self.evaluator = AlertEvaluator()
        self.alert_service = AlertService()
    
    def create_event(self, user_id: str, event_type: str, event_action: str, 
                    event_result: str, message: str = None, details: Dict[str, Any] = None,
                    client_id: str = None, node_id: str = None) -> Optional[Event]:
        """创建事件记录"""
        try:
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
            
            # 评估事件告警策略
            self._evaluate_event_alerts(event)
            
            logger.info(f"Event created: {event_type}.{event_action}.{event_result}")
            return event
            
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            return None
    
    def _evaluate_event_alerts(self, event: Event):
        """评估事件告警策略"""
        try:
            # 使用新的告警评估器评估事件
            triggered_alerts = self.evaluator.evaluate_event(event)
            
            for alert_info in triggered_alerts:
                policy = alert_info['policy']
                triggered_at = alert_info['triggered_at']
                
                # 创建告警实例
                alert_instance = self.evaluator.create_alert_instance(
                    policy=policy,
                    event=event,
                    triggered_at=triggered_at
                )
                
                if alert_instance:
                    # 发送通知
                    self.alert_service._send_notifications(policy, alert_instance)
                    logger.info(f"Event alert triggered: {policy.name} for event {event.event_type}.{event.event_action}.{event.event_result}")
                        
        except Exception as e:
            logger.error(f"Error evaluating event alerts: {e}")
    
    def get_events(self, user_id: str, event_type: str = None, 
                   event_action: str = None, event_result: str = None,
                   start_time: datetime = None, end_time: datetime = None,
                   page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """获取事件列表"""
        try:
            query = Event.query.filter(Event.user_id == user_id)
            
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
    
    def get_event_statistics(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """获取事件统计信息"""
        try:
            from datetime import timedelta
            start_time = datetime.utcnow() - timedelta(days=days)
            
            # 按事件类型统计
            type_stats = db.session.query(
                Event.event_type,
                db.func.count(Event.id).label('count')
            ).filter(
                Event.user_id == user_id,
                Event.timestamp >= start_time
            ).group_by(Event.event_type).all()
            
            # 按事件结果统计
            result_stats = db.session.query(
                Event.event_result,
                db.func.count(Event.id).label('count')
            ).filter(
                Event.user_id == user_id,
                Event.timestamp >= start_time
            ).group_by(Event.event_result).all()
            
            # 按时间统计
            time_stats = db.session.query(
                db.func.date(Event.timestamp).label('date'),
                db.func.count(Event.id).label('count')
            ).filter(
                Event.user_id == user_id,
                Event.timestamp >= start_time
            ).group_by(db.func.date(Event.timestamp)).order_by(db.func.date(Event.timestamp)).all()
            
            return {
                'type_statistics': [{'type': stat.event_type, 'count': stat.count} for stat in type_stats],
                'result_statistics': [{'result': stat.event_result, 'count': stat.count} for stat in result_stats],
                'time_statistics': [{'date': stat.date.isoformat(), 'count': stat.count} for stat in time_stats]
            }
            
        except Exception as e:
            logger.error(f"Error getting event statistics: {e}")
            return {'type_statistics': [], 'result_statistics': [], 'time_statistics': []}
    
    def get_event_alert_statistics(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """获取事件告警统计信息"""
        try:
            from datetime import timedelta
            from backend.app.models.alert import AlertInstance
            
            start_time = datetime.utcnow() - timedelta(days=days)
            
            # 获取事件告警实例统计
            alert_stats = db.session.query(
                AlertInstance.alert_name,
                AlertInstance.severity,
                db.func.count(AlertInstance.id).label('count')
            ).filter(
                AlertInstance.starts_at >= start_time,
                AlertInstance.labels.contains({'event_type': {'$exists': True}})
            ).group_by(AlertInstance.alert_name, AlertInstance.severity).all()
            
            # 按严重程度统计
            severity_stats = db.session.query(
                AlertInstance.severity,
                db.func.count(AlertInstance.id).label('count')
            ).filter(
                AlertInstance.starts_at >= start_time,
                AlertInstance.labels.contains({'event_type': {'$exists': True}})
            ).group_by(AlertInstance.severity).all()
            
            return {
                'alert_statistics': [{'name': stat.alert_name, 'severity': stat.severity, 'count': stat.count} for stat in alert_stats],
                'severity_statistics': [{'severity': stat.severity, 'count': stat.count} for stat in severity_stats]
            }
            
        except Exception as e:
            logger.error(f"Error getting event alert statistics: {e}")
            return {'alert_statistics': [], 'severity_statistics': []} 