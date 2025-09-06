"""
服务器管理系统配置文件
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """应用配置类"""
    
    # 基础配置
    APP_NAME = "Server Manager"
    APP_VERSION = "1.0.0"
    APP_DESCRIPTION = "局域网唤醒和定时任务管理系统"
    
    # 服务器配置
    HOST = os.getenv("SM_HOST", "127.0.0.1")
    PORT = int(os.getenv("SM_PORT", "8000"))
    
    # 数据存储配置
    DATA_DIR = os.getenv("SM_DATA_DIR", "data")
    LOGS_DIR = os.getenv("SM_LOGS_DIR", "logs")
    
    # 数据库配置
    DEVICES_DB_FILE = "devices.yaml"
    TASKS_DB_FILE = "tasks.yaml"
    EXECUTIONS_DB_FILE = "executions.yaml"
    COUNTERS_DB_FILE = "counters.yaml"
    
    # 调度器配置
    SCHEDULER_TIMEZONE = os.getenv("SM_TIMEZONE", "Asia/Shanghai")
    SCHEDULER_COALESCE = True
    SCHEDULER_MAX_INSTANCES = 1
    SCHEDULER_MISFIRE_GRACE_TIME = 30
    
    # WOL配置
    WOL_DEFAULT_PORT = int(os.getenv("SM_WOL_PORT", "9"))
    WOL_TIMEOUT = int(os.getenv("SM_WOL_TIMEOUT", "3"))
    
    # 任务执行配置
    TASK_DEFAULT_TIMEOUT = int(os.getenv("SM_TASK_TIMEOUT", "300"))
    TASK_MAX_RETRIES = int(os.getenv("SM_TASK_MAX_RETRIES", "0"))
    TASK_LOG_RETENTION_DAYS = int(os.getenv("SM_LOG_RETENTION_DAYS", "30"))
    
    # 日志配置
    LOG_LEVEL = os.getenv("SM_LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    # 安全配置
    CORS_ORIGINS = ["*"]  # 生产环境应该设置具体的域名
    
    # API配置
    API_PREFIX = "/api"
    DOCS_URL = "/docs"
    REDOC_URL = "/redoc"
    
    @classmethod
    def get_data_path(cls, filename: str) -> str:
        """获取数据文件的完整路径"""
        return os.path.join(cls.DATA_DIR, filename)
    
    @classmethod
    def get_log_path(cls, filename: str) -> str:
        """获取日志文件的完整路径"""
        return os.path.join(cls.LOGS_DIR, filename)
    
    @classmethod
    def ensure_directories(cls):
        """确保必要的目录存在"""
        directories = [
            cls.DATA_DIR,
            cls.LOGS_DIR,
            "static/js",
            "static/css", 
            "templates"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """将配置转换为字典"""
        config_dict = {}
        for key in dir(cls):
            if not key.startswith('_') and not callable(getattr(cls, key)):
                config_dict[key] = getattr(cls, key)
        return config_dict


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    HOST = "127.0.0.1"
    

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    LOG_LEVEL = "INFO"
    HOST = "0.0.0.0"
    CORS_ORIGINS = ["http://localhost", "http://127.0.0.1"]


class TestingConfig(Config):
    """测试环境配置"""
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    DATA_DIR = "test_data"
    LOGS_DIR = "test_logs"


# 根据环境变量选择配置
CONFIG_MAP = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}

def get_config() -> Config:
    """获取当前环境的配置"""
    env = os.getenv('SM_ENV', 'development').lower()
    return CONFIG_MAP.get(env, DevelopmentConfig)


# 当前配置实例
current_config = get_config()