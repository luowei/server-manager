import os
import yaml
from enum import Enum
from datetime import datetime
from typing import Dict, Any, Optional
from tinydb.storages import Storage


class YAMLStorage(Storage):
    """
    Custom YAML storage for TinyDB
    """
    
    def __init__(self, path: str):
        """
        Initialize YAML storage
        
        Args:
            path: Path to the YAML file
        """
        self.path = path
        self._ensure_dir_exists()
    
    def _ensure_dir_exists(self):
        """Ensure the directory exists"""
        directory = os.path.dirname(self.path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
    
    def read(self) -> Optional[Dict[str, Any]]:
        """
        Read data from YAML file
        
        Returns:
            Dictionary containing the data or None if file doesn't exist
        """
        if not os.path.exists(self.path):
            return None
        
        try:
            with open(self.path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
                return data if data is not None else {}
        except (yaml.YAMLError, FileNotFoundError):
            return {}
    
    def _serialize_data(self, obj):
        """递归序列化数据，处理枚举和日期时间对象"""
        if isinstance(obj, dict):
            return {key: self._serialize_data(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_data(item) for item in obj]
        elif isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj
    
    def write(self, data: Dict[str, Any]):
        """
        Write data to YAML file
        
        Args:
            data: Dictionary containing the data to write
        """
        self._ensure_dir_exists()
        
        # 序列化数据，处理枚举和日期时间对象
        serialized_data = self._serialize_data(data)
        
        with open(self.path, 'w', encoding='utf-8') as file:
            yaml.safe_dump(serialized_data, file, default_flow_style=False, 
                          allow_unicode=True, sort_keys=False)
    
    def close(self):
        """Close storage (no-op for YAML files)"""
        pass