import logging
from datetime import datetime
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
    """审计服务类"""
    
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