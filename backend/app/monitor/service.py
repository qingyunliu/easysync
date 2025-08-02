import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from backend import db
from backend.app.models import MonitorData, Alert, AlertRule, Node
from backend.app.notifications.services import NotificationService
from .errors import MonitorNotFoundError, MonitorValidationError, MonitorOperationError, AlertRuleError

logger = logging.getLogger(__name__)

class MonitorService:
    """监控服务类"""
    
    def __init__(self):
        self.metrics_retention_days = 30  # 指标保留天数
        self.alert_retention_days = 90    # 告警保留天数
        self.notification_service = NotificationService()
        
    def save_metrics(self, node_id: str, metrics: Dict[str, Any]) -> None:
        """保存监控指标
        
        Args:
            node_id: 节点ID
            metrics: 监控指标
            
        Raises:
            MonitorValidationError: 数据验证失败
        """
        try:
            # 验证指标数据
            self._validate_metrics(metrics)
            
            # 创建监控记录
            monitor = MonitorData(
                node_id=node_id,
                data=metrics,
                timestamp=datetime.utcnow()
            )
            
            db.session.add(monitor)
            db.session.commit()
            
            # 检查告警规则
            self._check_alert_rules(node_id, metrics)
            
            logger.info(f"Metrics saved for node: {node_id}")
            
            # 发送通知
            self.notification_service.send_notification(
                'info',
                f'监控指标已保存',
                f'节点 {node_id} 的监控指标已成功保存',
                metadata={
                    'node_id': node_id,
                    'metrics_count': len(metrics),
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to save metrics for node {node_id}: {str(e)}")
            self.notification_service.send_notification(
                'error',
                f'监控指标保存失败',
                f'节点 {node_id} 的监控指标保存失败: {str(e)}',
                metadata={
                    'node_id': node_id,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            raise
        
    def get_node_stats(self, node_id: str) -> Dict[str, Any]:
        """获取节点统计信息
        
        Args:
            node_id: 节点ID
            
        Returns:
            Dict[str, Any]: 统计信息
            
        Raises:
            MonitorNotFoundError: 节点不存在
        """
        node = Node.query.get(node_id)
        if not node:
            raise MonitorNotFoundError(f"Node not found: {node_id}")
            
        # 获取最近24小时的指标
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)
        
        metrics = MonitorData.query.filter(
            MonitorData.node_id == node_id,
            MonitorData.timestamp >= start_time,
            MonitorData.timestamp <= end_time
        ).all()
        
        # 计算统计信息
        stats = {
            'cpu': self._calculate_stats([m.data.get('cpu', {}) for m in metrics]),
            'memory': self._calculate_stats([m.data.get('memory', {}) for m in metrics]),
            'disk': self._calculate_stats([m.data.get('disk', {}) for m in metrics]),
            'network': self._calculate_stats([m.data.get('network', {}) for m in metrics])
        }
        
        return stats
        
    def get_node_history(self, node_id: str, duration: str = '24h') -> List[Dict[str, Any]]:
        """获取节点历史数据
        
        Args:
            node_id: 节点ID
            duration: 时间范围（24h, 7d, 30d）
            
        Returns:
            List[Dict[str, Any]]: 历史数据
            
        Raises:
            MonitorNotFoundError: 节点不存在
        """
        node = Node.query.get(node_id)
        if not node:
            raise MonitorNotFoundError(f"Node not found: {node_id}")
            
        # 计算时间范围
        end_time = datetime.utcnow()
        if duration == '24h':
            start_time = end_time - timedelta(hours=24)
        elif duration == '7d':
            start_time = end_time - timedelta(days=7)
        elif duration == '30d':
            start_time = end_time - timedelta(days=30)
        else:
            raise MonitorValidationError(f"Invalid duration: {duration}")
            
        # 获取历史数据
        metrics = MonitorData.query.filter(
            MonitorData.node_id == node_id,
            MonitorData.timestamp >= start_time,
            MonitorData.timestamp <= end_time
        ).order_by(MonitorData.timestamp.asc()).all()
        
        return [m.to_dict() for m in metrics]
        
    def create_alert_rule(self, rule_data: Dict[str, Any]) -> AlertRule:
        """创建告警规则
        
        Args:
            rule_data: 规则数据
            
        Returns:
            AlertRule: 告警规则对象
            
        Raises:
            AlertRuleError: 规则创建失败
        """
        try:
            # 验证规则数据
            self._validate_alert_rule(rule_data)
            
            # 创建规则
            rule = AlertRule(
                name=rule_data['name'],
                description=rule_data.get('description'),
                metric=rule_data['metric'],
                operator=rule_data['operator'],
                threshold=rule_data['threshold'],
                duration=rule_data.get('duration', 300),
                severity=rule_data.get('severity', 'warning'),
                enabled=rule_data.get('enabled', True)
            )
            
            db.session.add(rule)
            db.session.commit()
            
            logger.info(f"Alert rule created: {rule.id}")
            
            # 发送通知
            self.notification_service.send_notification(
                'success',
                f'告警规则已创建',
                f'新的告警规则 "{rule.name}" 已成功创建',
                metadata={
                    'rule_id': rule.id,
                    'rule_name': rule.name,
                    'metric': rule.metric,
                    'threshold': rule.threshold,
                    'severity': rule.severity,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            return rule
            
        except Exception as e:
            logger.error(f"Failed to create alert rule: {str(e)}")
            self.notification_service.send_notification(
                'error',
                f'告警规则创建失败',
                f'创建告警规则失败: {str(e)}',
                metadata={
                    'rule_data': rule_data,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            raise
        
    def check_alert_rules(self, node_id: str, metrics: Dict[str, Any]) -> List[Alert]:
        """检查告警规则
        
        Args:
            node_id: 节点ID
            metrics: 监控指标
            
        Returns:
            List[Alert]: 触发的告警列表
        """
        alerts = []
        rules = AlertRule.query.filter_by(enabled=True).all()
        
        for rule in rules:
            if self._evaluate_rule(rule, metrics):
                # 创建告警
                alert = Alert(
                    node_id=node_id,
                    rule_id=rule.id,
                    metric=rule.metric,
                    value=metrics.get(rule.metric, {}).get('value'),
                    threshold=rule.threshold,
                    severity=rule.severity
                )
                
                db.session.add(alert)
                alerts.append(alert)
                
                # 发送告警通知
                self.notification_service.send_notification(
                    'warning' if rule.severity == 'warning' else 'error',
                    f'触发告警: {rule.name}',
                    f'节点 {node_id} 触发告警规则 "{rule.name}": {rule.metric} {rule.operator} {rule.threshold}',
                    metadata={
                        'node_id': node_id,
                        'rule_id': rule.id,
                        'rule_name': rule.name,
                        'metric': rule.metric,
                        'current_value': metrics.get(rule.metric, {}).get('value'),
                        'threshold': rule.threshold,
                        'severity': rule.severity,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
                
        if alerts:
            db.session.commit()
            logger.info(f"Alerts created for node: {node_id}, count: {len(alerts)}")
            
            # 发送批量告警通知
            self.notification_service.send_notification(
                'warning',
                f'批量告警触发',
                f'节点 {node_id} 触发了 {len(alerts)} 个告警',
                metadata={
                    'node_id': node_id,
                    'alert_count': len(alerts),
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
        return alerts
        
    def collect_system_metrics(self, user_id: str = None) -> Dict[str, Any]:
        """收集系统监控指标"""
        try:
            # 获取系统指标
            from backend.app.utils.utils import get_system_metrics
            system_metrics = get_system_metrics()
            
            # 创建监控数据记录
            monitor_data = MonitorData.create_monitor_data(
                user_id=user_id,
                node_id=None,
                client_id=None,
                data=system_metrics
            )
            
            logger.info(f"系统监控数据收集成功: {monitor_data.id}")
            return system_metrics
            
        except Exception as e:
            logger.error(f"系统监控数据收集失败: {str(e)}")
            db.session.rollback()
            raise MonitorOperationError(f"系统监控数据收集失败: {str(e)}")
    
    def get_system_metrics_history(self, user_id: str, start_time: datetime = None, 
                                 end_time: datetime = None, limit: int = 24) -> List[Dict[str, Any]]:
        """获取系统监控历史数据"""
        try:
            # 构建查询
            query = MonitorData.query.filter_by(
                user_id=user_id,
                node_id=None,
                client_id=None
            )
            
            # 时间范围过滤
            if start_time:
                query = query.filter(MonitorData.timestamp >= start_time)
            if end_time:
                query = query.filter(MonitorData.timestamp <= end_time)
            
            # 按时间排序并限制数量
            query = query.order_by(MonitorData.timestamp.desc()).limit(limit)
            
            # 执行查询
            monitor_data = query.all()
            
            # 处理返回数据
            result = []
            for data in monitor_data:
                data_dict = data.to_dict()
                if data_dict['data']:
                    system_data = data_dict['data'].get('system', {})
                    result.append({
                        'timestamp': data_dict['timestamp'],
                        'cpu_usage': system_data.get('cpu_usage', 0),
                        'memory_usage': system_data.get('memory_usage', 0),
                        'disk_usage': system_data.get('disk_usage', 0),
                        'network_in': system_data.get('network_in', 0),
                        'network_out': system_data.get('network_out', 0),
                        'load_average': system_data.get('load_average', 0)
                    })
            
            # 按时间正序排列
            result.reverse()
            return result
            
        except Exception as e:
            logger.error(f"获取系统监控历史数据失败: {str(e)}")
            raise MonitorOperationError(f"获取系统监控历史数据失败: {str(e)}")
    
    def get_system_current_status(self, user_id: str) -> Dict[str, Any]:
        """获取当前系统状态"""
        try:
            # 获取最新的系统监控数据
            latest_data = MonitorData.query.filter_by(
                user_id=user_id,
                node_id=None,
                client_id=None
            ).order_by(MonitorData.timestamp.desc()).first()
            
            if not latest_data or not latest_data.data:
                # 如果没有数据，返回实时系统指标
                from backend.app.utils.utils import get_system_metrics
                system_metrics = get_system_metrics()
                return {
                    'timestamp': datetime.utcnow().isoformat(),
                    'cpu_usage': system_metrics.get('cpu_usage', 0),
                    'memory_usage': system_metrics.get('memory_usage', 0),
                    'disk_usage': system_metrics.get('disk_usage', 0),
                    'network_in': system_metrics.get('network_in', 0),
                    'network_out': system_metrics.get('network_out', 0),
                    'load_average': system_metrics.get('load_avg', [0, 0, 0])[0] if system_metrics.get('load_avg') else 0
                }
            
            # 返回最新的监控数据
            system_data = latest_data.data.get('system', {})
            return {
                'timestamp': latest_data.timestamp.isoformat(),
                'cpu_usage': system_data.get('cpu_usage', 0),
                'memory_usage': system_data.get('memory_usage', 0),
                'disk_usage': system_data.get('disk_usage', 0),
                'network_in': system_data.get('network_in', 0),
                'network_out': system_data.get('network_out', 0),
                'load_average': system_data.get('load_average', 0)
            }
            
        except Exception as e:
            logger.error(f"获取当前系统状态失败: {str(e)}")
            raise MonitorOperationError(f"获取当前系统状态失败: {str(e)}")
        
    def _validate_metrics(self, metrics: Dict[str, Any]) -> None:
        """验证监控指标
        
        Args:
            metrics: 监控指标
            
        Raises:
            MonitorValidationError: 验证失败
        """
        required_fields = ['cpu', 'memory', 'disk', 'network']
        if not all(field in metrics for field in required_fields):
            raise MonitorValidationError("Missing required metrics")
            
    def _validate_alert_rule(self, rule_data: Dict[str, Any]) -> None:
        """验证告警规则
        
        Args:
            rule_data: 规则数据
            
        Raises:
            AlertRuleError: 验证失败
        """
        required_fields = ['name', 'metric', 'operator', 'threshold']
        if not all(field in rule_data for field in required_fields):
            raise AlertRuleError("Missing required fields")
            
        valid_operators = ['>', '>=', '<', '<=', '==', '!=']
        if rule_data['operator'] not in valid_operators:
            raise AlertRuleError(f"Invalid operator: {rule_data['operator']}")
            
    def _calculate_stats(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算统计信息
        
        Args:
            metrics: 指标列表
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        if not metrics:
            return {}
            
        values = [m.get('value', 0) for m in metrics if 'value' in m]
        if not values:
            return {}
            
        return {
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'current': values[-1] if values else 0
        }
        
    def _evaluate_rule(self, rule: AlertRule, metrics: Dict[str, Any]) -> bool:
        """评估告警规则
        
        Args:
            rule: 告警规则
            metrics: 监控指标
            
        Returns:
            bool: 是否触发告警
        """
        value = metrics.get(rule.metric, {}).get('value', 0)
        
        if rule.operator == '>':
            return value > rule.threshold
        elif rule.operator == '>=':
            return value >= rule.threshold
        elif rule.operator == '<':
            return value < rule.threshold
        elif rule.operator == '<=':
            return value <= rule.threshold
        elif rule.operator == '==':
            return value == rule.threshold
        elif rule.operator == '!=':
            return value != rule.threshold
            
        return False 