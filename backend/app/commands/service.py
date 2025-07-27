# -*- coding: utf-8 -*-
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from flask import g
from backend import db
from backend.app.models import RealTimeCommand, Node, Storage
from backend.app.nodes.service import NodeService


logger = logging.getLogger(__name__)


class RealTimeCommandService:
    """实时命令服务"""
    
    def __init__(self):
        self.node_service = NodeService()
        
    def create_command(self, node_id: str, command_type: str, params: Dict[str, Any], 
                      timeout: int = 30, priority: int = 1) -> RealTimeCommand:
        """创建实时命令
        
        Args:
            node_id: 节点ID
            command_type: 命令类型
            params: 命令参数
            timeout: 超时时间（秒）
            priority: 优先级（1-5，1最高）
            
        Returns:
            RealTimeCommand: 创建的命令对象
            
        Raises:
            ValueError: 参数验证失败
        """
        # 验证节点
        node = self.node_service.get_node(node_id)
        if not self.node_service.check_node_health(node):
            raise ValueError(f"节点 {node_id} 不在线或不健康")
        
        # 验证命令类型
        valid_commands = [
            'test_connection', 'list_files', 'get_stats', 
            'download_file', 'list_buckets', 'list_objects'
        ]
        if command_type not in valid_commands:
            raise ValueError(f"不支持的命令类型: {command_type}")
        
        # 创建命令
        command = RealTimeCommand.create_command(
            node_id=node_id,
            user_id=g.user.id,
            command_type=command_type,
            params=params,
            timeout=timeout,
            priority=priority
        )
        
        logger.info(f"创建实时命令: {command.id}, 类型: {command_type}, 节点: {node_id}")
        return command
    
    def execute_command_sync(self, node_id: str, command_type: str, params: Dict[str, Any], 
                           timeout: int = 30) -> Dict[str, Any]:
        """同步执行命令（等待结果返回）
        
        Args:
            node_id: 节点ID
            command_type: 命令类型
            params: 命令参数
            timeout: 超时时间（秒）
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        # 创建命令
        command = self.create_command(node_id, command_type, params, timeout)
        
        # 等待执行结果
        return self._wait_for_result(command.id, timeout)
    
    def _wait_for_result(self, command_id: str, timeout: int) -> Dict[str, Any]:
        """等待命令执行结果
        
        Args:
            command_id: 命令ID
            timeout: 超时时间（秒）
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        start_time = time.time()
        check_interval = 0.5  # 500ms检查一次
        
        while time.time() - start_time < timeout:
            command = RealTimeCommand.query.get(command_id)
            if not command:
                return {'status': 'error', 'message': '命令不存在'}
            
            if command.status == 'completed':
                execution_time = command.get_execution_time()
                return {
                    'status': 'success',
                    'data': command.result,
                    'execution_time': execution_time,
                    'command_id': command_id
                }
            
            elif command.status == 'failed':
                return {
                    'status': 'error',
                    'message': command.error or '命令执行失败',
                    'command_id': command_id
                }
            
            elif command.status == 'timeout':
                return {
                    'status': 'timeout',
                    'message': f'命令执行超时（{timeout}秒）',
                    'command_id': command_id
                }
            
            time.sleep(check_interval)
        
        # 超时，标记命令为超时状态
        command = RealTimeCommand.query.get(command_id)
        if command and command.status in ['pending', 'executing']:
            command.mark_as_timeout()
            db.session.commit()
        
        return {
            'status': 'timeout',
            'message': f'等待命令结果超时（{timeout}秒）',
            'command_id': command_id
        }
    
    def get_pending_commands(self, node_id: str) -> List[Dict[str, Any]]:
        """获取节点待执行的命令
        
        Args:
            node_id: 节点ID
            
        Returns:
            List[Dict[str, Any]]: 待执行的命令列表
        """
        # 清理过期命令
        RealTimeCommand.cleanup_expired_commands()
        
        # 获取待执行命令
        commands = RealTimeCommand.get_pending_commands(node_id)
        return [command.to_dict() for command in commands]
    
    def update_command_status(self, command_id: str, status_data: Dict[str, Any]) -> bool:
        """更新命令状态
        
        Args:
            command_id: 命令ID
            status_data: 状态数据
            
        Returns:
            bool: 是否更新成功
        """
        try:
            command = RealTimeCommand.query.get(command_id)
            if not command:
                logger.warning(f"命令不存在: {command_id}")
                return False
            
            status = status_data.get('status')
            
            if status == 'executing':
                command.mark_as_executing()
                logger.info(f"命令开始执行: {command_id}")
                
            elif status == 'completed':
                result = status_data.get('result', {})
                command.mark_as_completed(result)
                logger.info(f"命令执行完成: {command_id}")
                
            elif status == 'failed':
                error = status_data.get('error', '未知错误')
                command.mark_as_failed(error)
                logger.error(f"命令执行失败: {command_id}, 错误: {error}")
                
            else:
                logger.warning(f"无效的命令状态: {status}")
                return False
            
            db.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"更新命令状态失败: {command_id}, 错误: {e}")
            db.session.rollback()
            return False
    
    def get_command_status(self, command_id: str) -> Optional[Dict[str, Any]]:
        """获取命令状态
        
        Args:
            command_id: 命令ID
            
        Returns:
            Optional[Dict[str, Any]]: 命令状态
        """
        command = RealTimeCommand.query.get(command_id)
        if not command:
            return None
        return command.to_dict()
    
    def cleanup_old_commands(self, days: int = 7) -> int:
        """清理旧命令
        
        Args:
            days: 保留天数
            
        Returns:
            int: 清理的命令数量
        """
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        old_commands = RealTimeCommand.query.filter(
            RealTimeCommand.created_at < cutoff_date,
            RealTimeCommand.status.in_(['completed', 'failed', 'timeout'])
        ).all()
        
        count = len(old_commands)
        for command in old_commands:
            db.session.delete(command)
        
        db.session.commit()
        logger.info(f"清理了 {count} 个旧命令")
        return count


# 存储相关的实时命令服务
class StorageRealTimeService:
    """存储实时服务"""
    
    def __init__(self):
        self.command_service = RealTimeCommandService()
    
    def test_connection_realtime(self, storage_id: str, node_id: str) -> Dict[str, Any]:
        """实时测试存储连接
        
        Args:
            storage_id: 存储ID
            node_id: 节点ID
            
        Returns:
            Dict[str, Any]: 测试结果
        """
        storage = Storage.query.get(storage_id)
        if not storage:
            return {'status': 'error', 'message': '存储不存在'}
        
        # 构建测试参数
        params = {
            'storage_config': {
                'id': storage.id,
                'name': storage.name,
                'type': storage.type,
                'config': storage.config
            }
        }
        
        # 执行实时命令
        return self.command_service.execute_command_sync(
            node_id=node_id,
            command_type='test_connection',
            params=params,
            timeout=30
        )
    
    def get_storage_stats_realtime(self, storage_id: str, node_id: str = None) -> Dict[str, Any]:
        """实时获取存储统计信息
        
        Args:
            storage_id: 存储ID
            node_id: 节点ID（可选，如果不指定则使用存储绑定的节点）
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        storage = Storage.query.get(storage_id)
        if not storage:
            return {'status': 'error', 'message': '存储不存在'}
        
        # 确定使用的节点
        target_node_id = node_id or storage.node_id
        if not target_node_id:
            return {'status': 'error', 'message': '存储未绑定节点'}
        
        # 构建参数
        params = {
            'storage_config': {
                'id': storage.id,
                'name': storage.name,
                'type': storage.type,
                'config': storage.config
            }
        }
        
        # 执行实时命令
        return self.command_service.execute_command_sync(
            node_id=target_node_id,
            command_type='get_stats',
            params=params,
            timeout=30
        )
    
    def list_files_realtime(self, storage_id: str, path: str = '', page: int = 1, 
                          page_size: int = 20, node_id: str = None) -> Dict[str, Any]:
        """实时获取文件列表
        
        Args:
            storage_id: 存储ID
            path: 路径
            page: 页码
            page_size: 每页大小
            node_id: 节点ID（可选）
            
        Returns:
            Dict[str, Any]: 文件列表
        """
        storage = Storage.query.get(storage_id)
        if not storage:
            return {'status': 'error', 'message': '存储不存在'}
        
        # 确定使用的节点
        target_node_id = node_id or storage.node_id
        if not target_node_id:
            return {'status': 'error', 'message': '存储未绑定节点'}
        
        # 构建参数
        params = {
            'storage_config': {
                'id': storage.id,
                'name': storage.name,
                'type': storage.type,
                'config': storage.config
            },
            'path': path,
            'page': page,
            'page_size': page_size
        }
        
        # 根据存储类型选择命令
        command_type = 'list_files'
        if storage.type in ['s3', 'obs']:
            command_type = 'list_objects'
        
        # 执行实时命令
        return self.command_service.execute_command_sync(
            node_id=target_node_id,
            command_type=command_type,
            params=params,
            timeout=30
        )
    
    def list_buckets_realtime(self, storage_id: str, page: int = 1, page_size: int = 20, 
                            node_id: str = None) -> Dict[str, Any]:
        """实时获取存储桶列表（仅适用于S3/OBS）
        
        Args:
            storage_id: 存储ID
            page: 页码
            page_size: 每页大小
            node_id: 节点ID（可选）
            
        Returns:
            Dict[str, Any]: 存储桶列表
        """
        storage = Storage.query.get(storage_id)
        if not storage:
            return {'status': 'error', 'message': '存储不存在'}
        
        if storage.type not in ['s3', 'obs']:
            return {'status': 'error', 'message': '该存储类型不支持存储桶操作'}
        
        # 确定使用的节点
        target_node_id = node_id or storage.node_id
        if not target_node_id:
            return {'status': 'error', 'message': '存储未绑定节点'}
        
        # 构建参数
        params = {
            'storage_config': {
                'id': storage.id,
                'name': storage.name,
                'type': storage.type,
                'config': storage.config
            },
            'page': page,
            'page_size': page_size
        }
        
        # 执行实时命令
        return self.command_service.execute_command_sync(
            node_id=target_node_id,
            command_type='list_buckets',
            params=params,
            timeout=30
        )
    
    def download_file_realtime(self, storage_id: str, file_path: str, bucket: str = '', 
                             node_id: str = None) -> Dict[str, Any]:
        """实时下载文件
        
        Args:
            storage_id: 存储ID
            file_path: 文件路径
            bucket: 存储桶（S3/OBS用）
            node_id: 节点ID（可选）
            
        Returns:
            Dict[str, Any]: 下载结果
        """
        storage = Storage.query.get(storage_id)
        if not storage:
            return {'status': 'error', 'message': '存储不存在'}
        
        # 确定使用的节点
        target_node_id = node_id or storage.node_id
        if not target_node_id:
            return {'status': 'error', 'message': '存储未绑定节点'}
        
        # 构建参数
        params = {
            'storage_config': {
                'id': storage.id,
                'name': storage.name,
                'type': storage.type,
                'config': storage.config
            },
            'file_path': file_path,
            'bucket': bucket
        }
        
        # 执行实时命令（下载可能耗时较长）
        return self.command_service.execute_command_sync(
            node_id=target_node_id,
            command_type='download_file',
            params=params,
            timeout=60  # 下载允许更长时间
        )