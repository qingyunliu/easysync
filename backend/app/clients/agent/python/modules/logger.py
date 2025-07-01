import os
import logging
import logging.handlers
from typing import Optional
from pathlib import Path
from datetime import datetime

class LogManager:
    def __init__(self, log_dir: str = "logs", log_file: str = "agent.log",
                 max_size: int = 10 * 1024 * 1024, backup_count: int = 5,
                 level: str = "INFO"):

        self.log_dir = Path(log_dir)
        self.log_file = log_file
        self.max_size = max_size
        self.backup_count = backup_count
        self.level = getattr(logging, level.upper())
        
        # 确保日志目录存在
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置根日志记录器
        self._setup_root_logger()
        
    def _setup_root_logger(self):
        """配置根日志记录器"""
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 创建文件处理器
        log_file = self.log_dir / self.log_file
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.max_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # 配置根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(self.level)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的日志记录器"""
        return logging.getLogger(name)
        
    def set_level(self, level: str):
        """设置日志级别"""
        self.level = getattr(logging, level.upper())
        logging.getLogger().setLevel(self.level)
        
    def add_file_handler(self, name: str, filename: str):
        """为指定日志记录器添加文件处理器"""
        logger = logging.getLogger(name)
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 创建文件处理器
        log_file = self.log_dir / filename
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.max_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        
    def remove_file_handler(self, name: str, filename: str):
        """移除指定日志记录器的文件处理器"""
        logger = logging.getLogger(name)
        log_file = self.log_dir / filename
        
        for handler in logger.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                if handler.baseFilename == str(log_file):
                    logger.removeHandler(handler)
                    break 