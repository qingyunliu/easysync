import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

class TaskState:
    """任务状态类"""
    
    def __init__(self, state_dir: str):
        self.state_dir = state_dir
        self.logger = logging.getLogger('TaskState')
        self._ensure_state_dir()
        
    def _ensure_state_dir(self):
        """确保状态目录存在"""
        os.makedirs(self.state_dir, exist_ok=True)
        
    def _get_state_file(self, task_id: str) -> str:
        """获取状态文件路径
        
        Args:
            task_id: 任务ID
            
        Returns:
            str: 状态文件路径
        """
        return os.path.join(self.state_dir, f"{task_id}.json")
        
    def save_state(self, task_id: str, state: Dict[str, Any]):
        """保存任务状态
        
        Args:
            task_id: 任务ID
            state: 任务状态
        """
        try:
            state_file = self._get_state_file(task_id)
            state['updated_at'] = datetime.utcnow().isoformat()
            
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=4)
                
        except Exception as e:
            self.logger.error(f"Error saving task state: {e}")
            
    def load_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """加载任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Dict[str, Any]]: 任务状态
        """
        try:
            state_file = self._get_state_file(task_id)
            if not os.path.exists(state_file):
                return None
                
            with open(state_file, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            self.logger.error(f"Error loading task state: {e}")
            return None
            
    def delete_state(self, task_id: str):
        """删除任务状态
        
        Args:
            task_id: 任务ID
        """
        try:
            state_file = self._get_state_file(task_id)
            if os.path.exists(state_file):
                os.remove(state_file)
                
        except Exception as e:
            self.logger.error(f"Error deleting task state: {e}")
            
    def list_states(self) -> List[Dict[str, Any]]:
        """列出所有任务状态
        
        Returns:
            List[Dict[str, Any]]: 任务状态列表
        """
        states = []
        try:
            for filename in os.listdir(self.state_dir):
                if filename.endswith('.json'):
                    task_id = filename[:-5]
                    state = self.load_state(task_id)
                    if state:
                        states.append(state)
                        
        except Exception as e:
            self.logger.error(f"Error listing task states: {e}")
            
        return states
        
    def cleanup_old_states(self, max_age_days: int = 7):
        """清理旧的任务状态
        
        Args:
            max_age_days: 最大保留天数
        """
        try:
            now = datetime.utcnow()
            for filename in os.listdir(self.state_dir):
                if filename.endswith('.json'):
                    state_file = os.path.join(self.state_dir, filename)
                    state = self.load_state(filename[:-5])
                    if state:
                        updated_at = datetime.fromisoformat(state['updated_at'].replace('Z', '+00:00'))
                        age_days = (now - updated_at).days
                        if age_days > max_age_days:
                            os.remove(state_file)
                            
        except Exception as e:
            self.logger.error(f"Error cleaning up old states: {e}") 