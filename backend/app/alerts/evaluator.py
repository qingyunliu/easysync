import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import and_, or_, desc
from backend import db
from backend.app.models.alert import AlertPolicy, AlertInstance
from backend.app.models.monitor import MonitorData
from backend.app.models.event import Event
from backend.app.models.node import Node
from backend.app.models.client import Client

logger = logging.getLogger(__name__)


class AlertEvaluator:
    """告警评估器 - 评估监控数据和事件是否触发告警策略"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def evaluate_monitor_data(self, monitor_data: MonitorData) -> List[Dict[str, Any]]:
        """评估监控数据，返回触发的告警策略"""
        triggered_alerts = []
        
        try:
            # 获取所有启用的资源告警策略
            policies = AlertPolicy.query.filter(
                AlertPolicy.enabled == True,
                AlertPolicy.policy_type == 'resource'
            ).all()
            
            for policy in policies:
                if self._evaluate_resource_policy(policy, monitor_data):
                    triggered_alerts.append({
                        'policy': policy,
                        'monitor_data': monitor_data,
                        'triggered_at': datetime.utcnow()
                    })
            
            return triggered_alerts
            
        except Exception as e:
            self.logger.error(f"Error evaluating monitor data: {e}")
            return []
    
    def evaluate_event(self, event: Event) -> List[Dict[str, Any]]:
        """评估事件，返回触发的告警策略"""
        triggered_alerts = []
        
        try:
            # 获取所有启用的事件告警策略
            policies = AlertPolicy.query.filter(
                AlertPolicy.enabled == True,
                AlertPolicy.policy_type == 'event'
            ).all()
            
            for policy in policies:
                if self._evaluate_event_policy(policy, event):
                    triggered_alerts.append({
                        'policy': policy,
                        'event': event,
                        'triggered_at': datetime.utcnow()
                    })
            
            return triggered_alerts
            
        except Exception as e:
            self.logger.error(f"Error evaluating event: {e}")
            return []
    
    def _evaluate_resource_policy(self, policy: AlertPolicy, monitor_data: MonitorData) -> bool:
        """评估资源告警策略"""
        try:
            # 检查资源类型匹配
            if policy.resource_type == 'Nodes' and not monitor_data.node_id:
                return False
            elif policy.resource_type == 'Clients' and not monitor_data.client_id:
                return False
            elif policy.resource_type == 'System' and (monitor_data.node_id or monitor_data.client_id):
                return False
            
            # 检查监控资源匹配
            if policy.monitored_resources:
                resource_id = monitor_data.node_id or monitor_data.client_id
                if resource_id not in policy.monitored_resources:
                    return False
            
            # 检查告警条目
            if not policy.alert_items:
                return False
            
            # 检查触发规则
            for alert_item in policy.alert_items:
                if self._check_trigger_rule(policy, monitor_data, alert_item):
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error evaluating resource policy: {e}")
            return False
    
    def _evaluate_event_policy(self, policy: AlertPolicy, event: Event) -> bool:
        """评估事件告警策略"""
        try:
            # 检查事件类型匹配
            if policy.event_type and policy.event_type != event.event_type:
                return False
            
            # 检查事件动作匹配
            if policy.event_actions and event.event_action not in policy.event_actions:
                return False
            
            # 检查事件结果匹配
            if policy.event_results and event.event_result not in policy.event_results:
                return False
            
            # 检查监控资源匹配
            if policy.monitored_resources:
                resource_id = event.node_id or event.client_id
                if resource_id and resource_id not in policy.monitored_resources:
                    return False
            
            # 检查频率限制（可选）
            if not self._check_event_frequency_limit(policy, event):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error evaluating event policy: {e}")
            return False
    
    def _check_event_frequency_limit(self, policy: AlertPolicy, event: Event) -> bool:
        """检查事件频率限制"""
        try:
            # 获取策略配置的频率限制
            frequency_limit = policy.trigger_rules.get('frequency_limit', {})
            if not frequency_limit:
                return True
            
            time_window = frequency_limit.get('time_window', 3600)  # 默认1小时
            max_count = frequency_limit.get('max_count', 10)  # 默认最多10次
            
            # 计算时间窗口
            end_time = event.timestamp
            start_time = end_time - timedelta(seconds=time_window)
            
            # 查询时间窗口内的事件数量
            query = Event.query.filter(
                Event.event_type == event.event_type,
                Event.event_action == event.event_action,
                Event.event_result == event.event_result,
                Event.timestamp >= start_time,
                Event.timestamp <= end_time
            )
            
            # 如果指定了资源，则按资源过滤
            if event.node_id:
                query = query.filter(Event.node_id == event.node_id)
            elif event.client_id:
                query = query.filter(Event.client_id == event.client_id)
            
            count = query.count()
            
            # 如果超过限制，则不触发告警
            if count > max_count:
                self.logger.debug(f"Event frequency limit exceeded: {count}/{max_count} in {time_window}s")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking event frequency limit: {e}")
            return True
    
    def _check_trigger_rule(self, policy: AlertPolicy, monitor_data: MonitorData, alert_item: str) -> bool:
        """检查触发规则"""
        try:
            trigger_rules = policy.trigger_rules.get(alert_item, {})
            if not trigger_rules:
                return False
            
            # 获取当前值
            current_value = self._get_metric_value(monitor_data, alert_item)
            if current_value is None:
                return False
            
            # 检查阈值条件
            operator = trigger_rules.get('operator', '>')
            threshold = trigger_rules.get('threshold', 0)
            duration = trigger_rules.get('duration', 0)  # 持续时间（秒）
            
            # 检查当前值是否满足条件
            if not self._check_threshold(current_value, operator, threshold):
                return False
            
            # 如果设置了持续时间，需要检查历史数据
            if duration > 0:
                return self._check_duration_condition(policy, monitor_data, alert_item, operator, threshold, duration)
            else:
                return True
                
        except Exception as e:
            self.logger.error(f"Error checking trigger rule: {e}")
            return False
    
    def _get_metric_value(self, monitor_data: MonitorData, alert_item: str) -> Optional[float]:
        """获取指标值"""
        try:
            data = monitor_data.data
            if not data:
                return None
            
            # 根据告警条目获取对应的指标值
            if alert_item == 'CPU':
                return data.get('cpu', {}).get('percent')
            elif alert_item == '内存':
                return data.get('memory', {}).get('percent')
            elif alert_item == '磁盘':
                return data.get('disk', {}).get('percent')
            elif alert_item == '网络':
                # 网络指标可能需要计算
                network_data = data.get('network', {})
                if network_data:
                    return network_data.get('bytes_sent', 0) + network_data.get('bytes_recv', 0)
            elif alert_item == '进程':
                return data.get('system', {}).get('process_count')
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting metric value: {e}")
            return None
    
    def _check_threshold(self, current_value: float, operator: str, threshold: float) -> bool:
        """检查阈值条件"""
        try:
            if operator == '>':
                return current_value > threshold
            elif operator == '>=':
                return current_value >= threshold
            elif operator == '<':
                return current_value < threshold
            elif operator == '<=':
                return current_value <= threshold
            elif operator == '==':
                return current_value == threshold
            elif operator == '!=':
                return current_value != threshold
            else:
                self.logger.warning(f"Unknown operator: {operator}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error checking threshold: {e}")
            return False
    
    def _check_duration_condition(self, policy: AlertPolicy, monitor_data: MonitorData, 
                                 alert_item: str, operator: str, threshold: float, duration: int) -> bool:
        """检查持续时间条件"""
        try:
            # 计算检查时间范围
            end_time = monitor_data.timestamp
            start_time = end_time - timedelta(seconds=duration)
            
            # 获取历史监控数据
            resource_id = monitor_data.node_id or monitor_data.client_id
            if monitor_data.node_id:
                history_data = MonitorData.query.filter(
                    and_(
                        MonitorData.node_id == monitor_data.node_id,
                        MonitorData.timestamp >= start_time,
                        MonitorData.timestamp <= end_time
                    )
                ).order_by(MonitorData.timestamp.asc()).all()
            else:
                history_data = MonitorData.query.filter(
                    and_(
                        MonitorData.client_id == monitor_data.client_id,
                        MonitorData.timestamp >= start_time,
                        MonitorData.timestamp <= end_time
                    )
                ).order_by(MonitorData.timestamp.asc()).all()
            
            # 检查是否在持续时间内都满足条件
            for data_point in history_data:
                value = self._get_metric_value(data_point, alert_item)
                if value is None:
                    continue
                
                if not self._check_threshold(value, operator, threshold):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking duration condition: {e}")
            return False
    
    def create_alert_instance(self, policy: AlertPolicy, monitor_data: MonitorData = None, 
                            event: Event = None, triggered_at: datetime = None) -> Optional[AlertInstance]:
        """创建告警实例"""
        try:
            if monitor_data:
                return self._create_resource_alert_instance(policy, monitor_data, triggered_at)
            elif event:
                return self._create_event_alert_instance(policy, event, triggered_at)
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating alert instance: {e}")
            return None
    
    def _create_resource_alert_instance(self, policy: AlertPolicy, monitor_data: MonitorData, 
                                      triggered_at: datetime) -> Optional[AlertInstance]:
        """创建资源告警实例"""
        try:
            # 生成告警指纹（用于去重）
            fingerprint = self._generate_resource_fingerprint(policy, monitor_data)
            
            # 检查是否已存在相同的告警实例
            existing_instance = AlertInstance.query.filter(
                and_(
                    AlertInstance.policy_id == policy.id,
                    AlertInstance.fingerprint == fingerprint,
                    AlertInstance.status == 'firing'
                )
            ).first()
            
            if existing_instance:
                # 更新现有实例
                existing_instance.notification_count += 1
                existing_instance.last_notification_at = datetime.utcnow()
                db.session.commit()
                return existing_instance
            
            # 创建新的告警实例
            instance = AlertInstance(
                policy_id=policy.id,
                alert_name=policy.name,
                severity=policy.level,
                metric_name=policy.alert_items[0] if policy.alert_items else 'unknown',
                current_value=self._get_metric_value(monitor_data, policy.alert_items[0]) if policy.alert_items else 0,
                threshold_value=policy.trigger_rules.get(policy.alert_items[0], {}).get('threshold', 0) if policy.alert_items else 0,
                starts_at=triggered_at,
                fingerprint=fingerprint,
                status='firing'
            )
            
            db.session.add(instance)
            db.session.commit()
            
            self.logger.info(f"Created resource alert instance: {instance.id} for policy: {policy.name}")
            return instance
            
        except Exception as e:
            self.logger.error(f"Error creating resource alert instance: {e}")
            db.session.rollback()
            return None
    
    def _create_event_alert_instance(self, policy: AlertPolicy, event: Event, 
                                   triggered_at: datetime) -> Optional[AlertInstance]:
        """创建事件告警实例"""
        try:
            import hashlib
            
            # 生成告警指纹
            fingerprint_data = {
                'policy_id': policy.id,
                'event_type': event.event_type,
                'event_action': event.event_action,
                'event_result': event.event_result,
                'resource_id': event.node_id or event.client_id
            }
            fingerprint_str = str(fingerprint_data)
            fingerprint = hashlib.md5(fingerprint_str.encode()).hexdigest()
            
            # 检查是否已存在相同的告警实例
            existing_instance = AlertInstance.query.filter(
                and_(
                    AlertInstance.policy_id == policy.id,
                    AlertInstance.fingerprint == fingerprint,
                    AlertInstance.status == 'firing'
                )
            ).first()
            
            if existing_instance:
                # 更新现有实例
                existing_instance.notification_count += 1
                existing_instance.last_notification_at = datetime.utcnow()
                db.session.commit()
                return existing_instance
            
            # 创建新的告警实例
            instance = AlertInstance(
                policy_id=policy.id,
                alert_name=policy.name,
                severity=policy.level,
                metric_name=f"{event.event_type}.{event.event_action}",
                current_value=0,  # 事件告警没有数值
                threshold_value=0,
                starts_at=triggered_at,
                fingerprint=fingerprint,
                status='firing',
                labels={
                    'event_type': event.event_type,
                    'event_action': event.event_action,
                    'event_result': event.event_result
                },
                annotations={
                    'message': event.message,
                    'details': event.details
                }
            )
            
            db.session.add(instance)
            db.session.commit()
            
            self.logger.info(f"Created event alert instance: {instance.id} for policy: {policy.name}")
            return instance
            
        except Exception as e:
            self.logger.error(f"Error creating event alert instance: {e}")
            db.session.rollback()
            return None
    
    def _generate_resource_fingerprint(self, policy: AlertPolicy, monitor_data: MonitorData) -> str:
        """生成资源告警指纹"""
        import hashlib
        
        # 构建指纹字符串
        fingerprint_data = {
            'policy_id': policy.id,
            'resource_id': monitor_data.node_id or monitor_data.client_id,
            'alert_items': policy.alert_items,
            'trigger_rules': policy.trigger_rules
        }
        
        # 生成哈希
        fingerprint_str = str(fingerprint_data)
        return hashlib.md5(fingerprint_str.encode()).hexdigest()
    
    def resolve_alert_instance(self, policy: AlertPolicy, monitor_data: MonitorData = None, 
                             event: Event = None) -> bool:
        """解决告警实例（当条件不再满足时）"""
        try:
            if monitor_data:
                return self._resolve_resource_alert_instance(policy, monitor_data)
            elif event:
                return self._resolve_event_alert_instance(policy, event)
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error resolving alert instance: {e}")
            return False
    
    def _resolve_resource_alert_instance(self, policy: AlertPolicy, monitor_data: MonitorData) -> bool:
        """解决资源告警实例"""
        try:
            fingerprint = self._generate_resource_fingerprint(policy, monitor_data)
            
            instance = AlertInstance.query.filter(
                and_(
                    AlertInstance.policy_id == policy.id,
                    AlertInstance.fingerprint == fingerprint,
                    AlertInstance.status == 'firing'
                )
            ).first()
            
            if instance:
                instance.status = 'resolved'
                instance.ends_at = datetime.utcnow()
                instance.resolved_at = datetime.utcnow()
                db.session.commit()
                
                self.logger.info(f"Resolved resource alert instance: {instance.id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error resolving resource alert instance: {e}")
            db.session.rollback()
            return False
    
    def _resolve_event_alert_instance(self, policy: AlertPolicy, event: Event) -> bool:
        """解决事件告警实例"""
        try:
            import hashlib
            
            fingerprint_data = {
                'policy_id': policy.id,
                'event_type': event.event_type,
                'event_action': event.event_action,
                'event_result': event.event_result,
                'resource_id': event.node_id or event.client_id
            }
            fingerprint_str = str(fingerprint_data)
            fingerprint = hashlib.md5(fingerprint_str.encode()).hexdigest()
            
            instance = AlertInstance.query.filter(
                and_(
                    AlertInstance.policy_id == policy.id,
                    AlertInstance.fingerprint == fingerprint,
                    AlertInstance.status == 'firing'
                )
            ).first()
            
            if instance:
                instance.status = 'resolved'
                instance.ends_at = datetime.utcnow()
                instance.resolved_at = datetime.utcnow()
                db.session.commit()
                
                self.logger.info(f"Resolved event alert instance: {instance.id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error resolving event alert instance: {e}")
            db.session.rollback()
            return False 