# 配置文件初始化
from .default import Config

# 配置字典
config = {
    'default': Config,
    'development': Config,
    'production': Config,
    'testing': Config
} 