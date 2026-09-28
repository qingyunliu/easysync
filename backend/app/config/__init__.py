# 配置文件初始化
from .default import Config, DevelopmentConfig, TestingConfig, ProductionConfig

# 配置字典
config = {
    'default': Config,
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
} 