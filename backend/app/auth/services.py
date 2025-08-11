import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from werkzeug.security import check_password_hash
from backend import db
from backend.app.models import AuditLog, User

logger = logging.getLogger(__name__)

class AuthService:
    """认证服务类"""
    
    def authenticate(self, username: str, password: str) -> User:
        """验证用户凭据"""
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            return user
        return None
        
    def authenticate_by_email(self, email: str, password: str) -> 'User':
        """通过邮箱验证用户凭据"""
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            return user
        return None
        
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """修改用户密码"""
        user = User.query.get(user_id)
        if not user or not check_password_hash(user.password_hash, old_password):
            return False
            
        user.set_password(new_password)
        db.session.commit()
        return True 

class AuditService:
    """审计服务类 - 专注于用户行为追踪和合规审计"""
    
    # 审计操作类型
    AUDIT_ACTIONS = {
        'user': ['login', 'logout', 'password_change', 'profile_update', 'register'],
        'storage': ['create', 'delete', 'update', 'test_connection', 'mount', 'unmount'],
        'task': ['create', 'delete', 'update', 'cancel', 'retry', 'assign', 'start', 'pause'],
        'client': ['create', 'delete', 'update', 'connect', 'disconnect'],
        'node': ['create', 'delete', 'update', 'register', 'unregister'],
        'system': ['config_change', 'backup', 'restore', 'maintenance']
    }
    
    # 安全风险模式
    SECURITY_RISK_PATTERNS = {
        'login': {
            'multiple_failed_attempts': {
                'threshold': 5,
                'time_window': 300,  # 5分钟
                'risk_level': 'medium'
            },
            'unusual_ip': {
                'risk_level': 'low'
            }
        },
        'delete': {
            'bulk_operation': {
                'threshold': 10,
                'risk_level': 'medium'
            },
            'critical_resource': {
                'risk_level': 'high'
            }
        },
        'update': {
            'permission_change': {
                'risk_level': 'high'
            },
            'config_change': {
                'risk_level': 'medium'
            }
        }
    }
    
    @staticmethod
    def log_operation(
        user_id: Optional[str],
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        result: str = 'success'
    ) -> Optional[AuditLog]:
        """记录操作审计日志
        
        Args:
            user_id: 用户ID，可以为None（如登录失败时）
            action: 操作类型 (create, update, delete, read, etc.)
            resource_type: 资源类型 (user, node, storage, task, client, etc.)
            resource_id: 资源ID
            resource_name: 资源名称
            details: 详细信息
            result: 操作结果 (success, failed)
            
        Returns:
            AuditLog: 创建的审计日志对象，如果user_id为None则返回None
        """
        # 如果user_id为None，跳过审计日志记录
        if user_id is None:
            logger.warning(f"Skipping audit log for {action} on {resource_type} - user_id is None")
            return None
            
        try:
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_name=resource_name,
                details=details or {},
                result=result
            )
            
            db.session.add(audit_log)
            db.session.commit()
            
            logger.info(f"Audit log created: {action} on {resource_type} by user {user_id}")
            return audit_log
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create audit log: {e}")
            # 不抛出异常，避免影响主业务流程
            return None
    
    @staticmethod
    def log_user_operation(action, resource_type, resource_id, resource_name, details=None, user_id=None):
        """记录用户操作审计日志"""
        try:
            # 验证操作类型
            if not AuditService.is_valid_audit_action(action, resource_type):
                logger.warning(f"Invalid audit action: {action} for resource_type: {resource_type}")
                return None
            
            # 创建审计日志
            audit_log = AuditService.log_operation(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_name=resource_name,
                details=details
            )
            
            # 检查是否存在安全风险
            if AuditService.is_security_risk(audit_log):
                AuditService.create_security_event(audit_log)
            
            logger.info(f"User operation logged: {action} on {resource_type} - {resource_name}")
            return audit_log
            
        except Exception as e:
            logger.error(f"Error logging user operation: {e}")
            return None
    
    @staticmethod
    def is_valid_audit_action(action, resource_type):
        """验证是否为有效的审计操作"""
        return (action in AuditService.AUDIT_ACTIONS.get(resource_type, []) or
                action in ['view', 'export', 'download'])  # 通用操作
    
    @staticmethod
    def is_security_risk(audit_log):
        """判断审计日志是否存在安全风险"""
        try:
            action = audit_log.action
            resource_type = audit_log.resource_type
            details = audit_log.details or {}
            
            # 检查是否匹配风险模式
            if action in AuditService.SECURITY_RISK_PATTERNS:
                patterns = AuditService.SECURITY_RISK_PATTERNS[action]
                
                for pattern_name, pattern_config in patterns.items():
                    if AuditService.check_risk_pattern(audit_log, pattern_name, pattern_config):
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking security risk: {e}")
            return False
    
    @staticmethod
    def check_risk_pattern(audit_log, pattern_name, pattern_config):
        """检查具体的风险模式"""
        try:
            if pattern_name == 'multiple_failed_attempts':
                return AuditService.check_failed_attempts(audit_log, pattern_config)
            elif pattern_name == 'bulk_operation':
                return AuditService.check_bulk_operation(audit_log, pattern_config)
            elif pattern_name == 'permission_change':
                return AuditService.check_permission_change(audit_log, pattern_config)
            elif pattern_name == 'unusual_ip':
                return AuditService.check_unusual_ip(audit_log, pattern_config)
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking risk pattern {pattern_name}: {e}")
            return False
    
    @staticmethod
    def check_failed_attempts(audit_log, config):
        """检查多次失败尝试"""
        try:
            if audit_log.action != 'login' or audit_log.result != 'failed':
                return False
            
            # 检查最近时间窗口内的失败次数
            time_window = config.get('time_window', 300)
            threshold = config.get('threshold', 5)
            
            start_time = datetime.utcnow() - timedelta(seconds=time_window)
            
            failed_count = AuditLog.query.filter(
                AuditLog.user_id == audit_log.user_id,
                AuditLog.action == 'login',
                AuditLog.result == 'failed',
                AuditLog.created_at >= start_time
            ).count()
            
            return failed_count >= threshold
            
        except Exception as e:
            logger.error(f"Error checking failed attempts: {e}")
            return False
    
    @staticmethod
    def check_bulk_operation(audit_log, config):
        """检查批量操作"""
        try:
            if audit_log.action != 'delete':
                return False
            
            # 检查是否删除大量资源
            threshold = config.get('threshold', 10)
            details = audit_log.details or {}
            
            # 从详情中获取删除的资源数量
            deleted_count = details.get('deleted_count', 1)
            
            return deleted_count >= threshold
            
        except Exception as e:
            logger.error(f"Error checking bulk operation: {e}")
            return False
    
    @staticmethod
    def check_permission_change(audit_log, config):
        """检查权限变更"""
        try:
            if audit_log.action != 'update':
                return False
            
            details = audit_log.details or {}
            additional_info = details.get('additional_info', {})
            
            # 检查是否涉及权限变更
            return ('role' in additional_info or 
                   'permissions' in additional_info or 
                   'is_admin' in additional_info)
            
        except Exception as e:
            logger.error(f"Error checking permission change: {e}")
            return False
    
    @staticmethod
    def check_unusual_ip(audit_log, config):
        """检查异常IP"""
        try:
            if audit_log.action != 'login':
                return False
            
            details = audit_log.details or {}
            ip_address = details.get('ip_address')
            
            if not ip_address:
                return False
            
            # 这里可以实现IP白名单检查
            # 暂时返回False，可以根据实际需求实现
            return False
            
        except Exception as e:
            logger.error(f"Error checking unusual IP: {e}")
            return False
    
    @staticmethod
    def create_security_event(audit_log):
        """创建安全事件"""
        try:
            # 确定风险级别
            risk_level = AuditService.determine_risk_level(audit_log)
            
            # 创建安全事件
            from backend.app.events.service import EventService
            EventService.record_system_event(
                event_type='system',
                event_action='security_alert',
                event_result='warning',
                message=f'检测到可疑操作: {audit_log.action} on {audit_log.resource_type}',
                details={
                    'audit_log_id': audit_log.id,
                    'risk_level': risk_level,
                    'user_id': audit_log.user_id,
                    'resource_type': audit_log.resource_type,
                    'resource_name': audit_log.resource_name
                },
                user_id=audit_log.user_id
            )
            
            logger.warning(f"Security event created for audit log: {audit_log.id}")
            
        except Exception as e:
            logger.error(f"Error creating security event: {e}")
    
    @staticmethod
    def determine_risk_level(audit_log):
        """确定风险级别"""
        try:
            action = audit_log.action
            
            # 高风险操作
            high_risk_actions = ['delete', 'permission_change']
            if action in high_risk_actions:
                return 'high'
            
            # 中风险操作
            medium_risk_actions = ['bulk_operation', 'config_change']
            if action in medium_risk_actions:
                return 'medium'
            
            # 低风险操作
            return 'low'
            
        except Exception as e:
            logger.error(f"Error determining risk level: {e}")
            return 'low'
    
    @staticmethod
    def log_login(user_id: Optional[str], ip: str, user_agent: str) -> Optional[AuditLog]:
        """记录登录审计日志"""
        return AuditService.log_operation(
            user_id=user_id,
            action='login',
            resource_type='user',
            resource_id=user_id,
            details={
                'ip': ip,
                'user_agent': user_agent,
                'login_time': datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def log_logout(user_id: Optional[str], ip: str, user_agent: str) -> Optional[AuditLog]:
        """记录登出审计日志"""
        return AuditService.log_operation(
            user_id=user_id,
            action='logout',
            resource_type='user',
            resource_id=user_id,
            details={
                'ip': ip,
                'user_agent': user_agent,
                'logout_time': datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def log_user_operation(
        user_id: Optional[str],
        action: str,
        target_user_id: Optional[str],
        target_username: Optional[str],
        details: Optional[Dict[str, Any]] = None,
        result: str = 'success'
    ) -> Optional[AuditLog]:
        """记录用户相关操作"""
        return AuditService.log_operation(
            user_id=user_id,
            action=action,
            resource_type='user',
            resource_id=target_user_id,
            resource_name=target_username,
            details=details,
            result=result
        )
    
    @staticmethod
    def log_storage_operation(
        user_id: Optional[str],
        action: str,
        storage_id: Optional[str],
        storage_name: Optional[str],
        details: Optional[Dict[str, Any]] = None,
        result: str = 'success'
    ) -> Optional[AuditLog]:
        """记录存储相关操作"""
        return AuditService.log_operation(
            user_id=user_id,
            action=action,
            resource_type='storage',
            resource_id=storage_id,
            resource_name=storage_name,
            details=details,
            result=result
        )
    
    @staticmethod
    def log_node_operation(
        user_id: Optional[str],
        action: str,
        node_id: Optional[str],
        node_name: Optional[str],
        details: Optional[Dict[str, Any]] = None,
        result: str = 'success'
    ) -> Optional[AuditLog]:
        """记录节点相关操作"""
        return AuditService.log_operation(
            user_id=user_id,
            action=action,
            resource_type='node',
            resource_id=node_id,
            resource_name=node_name,
            details=details,
            result=result
        )
    
    @staticmethod
    def log_task_operation(
        user_id: Optional[str],
        action: str,
        task_id: Optional[str],
        task_name: Optional[str],
        details: Optional[Dict[str, Any]] = None,
        result: str = 'success'
    ) -> Optional[AuditLog]:
        """记录任务相关操作"""
        return AuditService.log_operation(
            user_id=user_id,
            action=action,
            resource_type='task',
            resource_id=task_id,
            resource_name=task_name,
            details=details,
            result=result
        )
    
    @staticmethod
    def log_client_operation(
        user_id: Optional[str],
        action: str,
        client_id: Optional[str],
        client_name: Optional[str],
        details: Optional[Dict[str, Any]] = None,
        result: str = 'success'
    ) -> Optional[AuditLog]:
        """记录客户端相关操作"""
        return AuditService.log_operation(
            user_id=user_id,
            action=action,
            resource_type='client',
            resource_id=client_id,
            resource_name=client_name,
            details=details,
            result=result
        )
    
    @staticmethod
    def get_audit_logs_by_user(user_id, start_time=None, end_time=None, limit=100):
        """获取指定用户的审计日志"""
        try:
            query = AuditLog.query.filter_by(user_id=user_id)
            
            if start_time:
                query = query.filter(AuditLog.created_at >= start_time)
            if end_time:
                query = query.filter(AuditLog.created_at <= end_time)
            
            query = query.order_by(AuditLog.created_at.desc()).limit(limit)
            return query.all()
            
        except Exception as e:
            logger.error(f"Error getting audit logs by user: {e}")
            return []
    
    @staticmethod
    def get_audit_logs_by_resource(resource_type, resource_id, start_time=None, end_time=None, limit=100):
        """获取指定资源的审计日志"""
        try:
            query = AuditLog.query.filter_by(
                resource_type=resource_type,
                resource_id=resource_id
            )
            
            if start_time:
                query = query.filter(AuditLog.created_at >= start_time)
            if end_time:
                query = query.filter(AuditLog.created_at <= end_time)
            
            query = query.order_by(AuditLog.created_at.desc()).limit(limit)
            return query.all()
            
        except Exception as e:
            logger.error(f"Error getting audit logs by resource: {e}")
            return []
    
    @staticmethod
    def get_audit_statistics(hours=24):
        """获取审计日志统计信息"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            # 按操作类型统计
            action_stats = db.session.query(
                AuditLog.action,
                db.func.count(AuditLog.id).label('count')
            ).filter(
                AuditLog.created_at >= start_time
            ).group_by(AuditLog.action).all()
            
            # 按资源类型统计
            resource_stats = db.session.query(
                AuditLog.resource_type,
                db.func.count(AuditLog.id).label('count')
            ).filter(
                AuditLog.created_at >= start_time
            ).group_by(AuditLog.resource_type).all()
            
            # 按结果统计
            result_stats = db.session.query(
                AuditLog.result,
                db.func.count(AuditLog.id).label('count')
            ).filter(
                AuditLog.created_at >= start_time
            ).group_by(AuditLog.result).all()
            
            return {
                'by_action': {stat.action: stat.count for stat in action_stats},
                'by_resource': {stat.resource_type: stat.count for stat in resource_stats},
                'by_result': {stat.result: stat.count for stat in result_stats},
                'total': sum(stat.count for stat in action_stats)
            }
            
        except Exception as e:
            logger.error(f"Error getting audit statistics: {e}")
            return {'by_action': {}, 'by_resource': {}, 'by_result': {}, 'total': 0}
    
    @staticmethod
    def cleanup_old_audit_logs(days=365):
        """清理旧审计日志数据"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            deleted_count = AuditLog.query.filter(AuditLog.created_at < cutoff_date).delete()
            db.session.commit()
            
            logger.info(f"Cleaned up {deleted_count} old audit logs (older than {days} days)")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old audit logs: {e}")
            db.session.rollback()
            return 0 