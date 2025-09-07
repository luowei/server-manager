import os
import logging
from datetime import datetime
from tinydb import TinyDB, Query
from tinydb.operations import increment
from typing import List, Optional, Dict, Any
from .storage import YAMLStorage
from .models import WOLDevice, ScheduledTask, TaskExecution, TaskStatus


logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, data_dir: str = "data"):
        """
        初始化数据库管理器
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # 初始化各个数据表
        self.devices_db = TinyDB(
            os.path.join(data_dir, "devices.yaml"),
            storage=YAMLStorage
        )
        self.tasks_db = TinyDB(
            os.path.join(data_dir, "tasks.yaml"),
            storage=YAMLStorage
        )
        self.executions_db = TinyDB(
            os.path.join(data_dir, "executions.yaml"),
            storage=YAMLStorage
        )
        
        # 初始化计数器表用于生成ID
        self.counters_db = TinyDB(
            os.path.join(data_dir, "counters.yaml"),
            storage=YAMLStorage
        )
        
        self._init_counters()
    
    def _parse_datetime(self, dt_value):
        """安全地解析日期时间值"""
        if dt_value is None:
            return None
        if isinstance(dt_value, datetime):
            return dt_value
        if isinstance(dt_value, str):
            return datetime.fromisoformat(dt_value)
        return dt_value
    
    def _init_counters(self):
        """初始化计数器"""
        Counter = Query()
        
        for table_name in ['devices', 'tasks', 'executions']:
            if not self.counters_db.search(Counter.table == table_name):
                self.counters_db.insert({'table': table_name, 'count': 0})
    
    def _get_next_id(self, table_name: str) -> int:
        """获取下一个ID"""
        Counter = Query()
        self.counters_db.update(increment('count'), Counter.table == table_name)
        counter = self.counters_db.search(Counter.table == table_name)[0]
        return counter['count']
    
    # WOL设备管理
    def create_device(self, device: WOLDevice) -> WOLDevice:
        """创建WOL设备"""
        device.id = self._get_next_id('devices')
        device.created_at = datetime.now()
        device.updated_at = datetime.now()
        
        device_dict = device.dict()
        device_dict['created_at'] = device.created_at.isoformat()
        device_dict['updated_at'] = device.updated_at.isoformat()
        
        self.devices_db.insert(device_dict)
        return device
    
    def get_device(self, device_id: int) -> Optional[WOLDevice]:
        """获取WOL设备"""
        Device = Query()
        result = self.devices_db.search(Device.id == device_id)
        if result:
            device_dict = result[0].copy()
            device_dict['created_at'] = self._parse_datetime(device_dict['created_at'])
            device_dict['updated_at'] = self._parse_datetime(device_dict['updated_at'])
            return WOLDevice(**device_dict)
        return None
    
    def get_all_devices(self) -> List[WOLDevice]:
        """获取所有WOL设备"""
        devices = []
        for device_dict in self.devices_db.all():
            device_dict = device_dict.copy()
            device_dict['created_at'] = self._parse_datetime(device_dict['created_at'])
            device_dict['updated_at'] = self._parse_datetime(device_dict['updated_at'])
            devices.append(WOLDevice(**device_dict))
        return devices
    
    def update_device(self, device_id: int, updates: Dict[str, Any]) -> bool:
        """更新WOL设备"""
        Device = Query()
        updates['updated_at'] = datetime.now().isoformat()
        return len(self.devices_db.update(updates, Device.id == device_id)) > 0
    
    def delete_device(self, device_id: int) -> bool:
        """删除WOL设备"""
        Device = Query()
        return len(self.devices_db.remove(Device.id == device_id)) > 0
    
    # 定时任务管理
    def create_task(self, task: ScheduledTask) -> ScheduledTask:
        """创建定时任务"""
        task.id = self._get_next_id('tasks')
        task.created_at = datetime.now()
        task.updated_at = datetime.now()
        
        task_dict = task.dict()
        task_dict['created_at'] = task.created_at.isoformat()
        task_dict['updated_at'] = task.updated_at.isoformat()
        if task_dict.get('last_run_at'):
            task_dict['last_run_at'] = task.last_run_at.isoformat()
        if task_dict.get('next_run_at'):
            task_dict['next_run_at'] = task.next_run_at.isoformat()
        
        self.tasks_db.insert(task_dict)
        return task
    
    def get_task(self, task_id: int) -> Optional[ScheduledTask]:
        """获取定时任务"""
        Task = Query()
        result = self.tasks_db.search(Task.id == task_id)
        if result:
            task_dict = result[0].copy()
            task_dict['created_at'] = self._parse_datetime(task_dict['created_at'])
            task_dict['updated_at'] = self._parse_datetime(task_dict['updated_at'])
            if task_dict.get('last_run_at'):
                task_dict['last_run_at'] = self._parse_datetime(task_dict['last_run_at'])
            if task_dict.get('next_run_at'):
                task_dict['next_run_at'] = self._parse_datetime(task_dict['next_run_at'])
            return ScheduledTask(**task_dict)
        return None
    
    def get_all_tasks(self) -> List[ScheduledTask]:
        """获取所有定时任务"""
        tasks = []
        for task_dict in self.tasks_db.all():
            task_dict = task_dict.copy()
            task_dict['created_at'] = self._parse_datetime(task_dict['created_at'])
            task_dict['updated_at'] = self._parse_datetime(task_dict['updated_at'])
            if task_dict.get('last_run_at'):
                task_dict['last_run_at'] = self._parse_datetime(task_dict['last_run_at'])
            if task_dict.get('next_run_at'):
                task_dict['next_run_at'] = self._parse_datetime(task_dict['next_run_at'])
            tasks.append(ScheduledTask(**task_dict))
        return tasks
    
    def get_enabled_tasks(self) -> List[ScheduledTask]:
        """获取所有启用的定时任务"""
        Task = Query()
        tasks = []
        for task_dict in self.tasks_db.search(Task.enabled == True):
            task_dict = task_dict.copy()
            task_dict['created_at'] = self._parse_datetime(task_dict['created_at'])
            task_dict['updated_at'] = self._parse_datetime(task_dict['updated_at'])
            if task_dict.get('last_run_at'):
                task_dict['last_run_at'] = self._parse_datetime(task_dict['last_run_at'])
            if task_dict.get('next_run_at'):
                task_dict['next_run_at'] = self._parse_datetime(task_dict['next_run_at'])
            tasks.append(ScheduledTask(**task_dict))
        return tasks
    
    def update_task(self, task_id: int, updates: Dict[str, Any]) -> bool:
        """更新定时任务"""
        Task = Query()
        updates['updated_at'] = datetime.now().isoformat()
        if 'last_run_at' in updates and isinstance(updates['last_run_at'], datetime):
            updates['last_run_at'] = updates['last_run_at'].isoformat()
        if 'next_run_at' in updates and isinstance(updates['next_run_at'], datetime):
            updates['next_run_at'] = updates['next_run_at'].isoformat()
        return len(self.tasks_db.update(updates, Task.id == task_id)) > 0
    
    def delete_task(self, task_id: int) -> bool:
        """删除定时任务"""
        Task = Query()
        # 同时删除相关的执行记录
        Execution = Query()
        self.executions_db.remove(Execution.task_id == task_id)
        return len(self.tasks_db.remove(Task.id == task_id)) > 0
    
    # 任务执行记录管理
    def create_execution(self, execution: TaskExecution) -> TaskExecution:
        """创建任务执行记录"""
        execution.id = self._get_next_id('executions')
        execution.created_at = datetime.now()
        
        exec_dict = execution.dict()
        exec_dict['created_at'] = execution.created_at.isoformat()
        if exec_dict.get('started_at'):
            exec_dict['started_at'] = execution.started_at.isoformat()
        if exec_dict.get('completed_at'):
            exec_dict['completed_at'] = execution.completed_at.isoformat()
        
        self.executions_db.insert(exec_dict)
        return execution
    
    def update_execution(self, execution_id: int, updates: Dict[str, Any]) -> bool:
        """更新任务执行记录"""
        Execution = Query()
        if 'started_at' in updates and isinstance(updates['started_at'], datetime):
            updates['started_at'] = updates['started_at'].isoformat()
        if 'completed_at' in updates and isinstance(updates['completed_at'], datetime):
            updates['completed_at'] = updates['completed_at'].isoformat()
        return len(self.executions_db.update(updates, Execution.id == execution_id)) > 0
    
    def get_executions_by_task(self, task_id: int, limit: int = 50) -> List[TaskExecution]:
        """获取指定任务的执行记录"""
        Execution = Query()
        executions = []
        results = self.executions_db.search(Execution.task_id == task_id)
        # 按创建时间倒序排列
        results.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        for exec_dict in results[:limit]:
            exec_dict = exec_dict.copy()
            exec_dict['created_at'] = self._parse_datetime(exec_dict['created_at'])
            if exec_dict.get('started_at'):
                exec_dict['started_at'] = self._parse_datetime(exec_dict['started_at'])
            if exec_dict.get('completed_at'):
                exec_dict['completed_at'] = self._parse_datetime(exec_dict['completed_at'])
            executions.append(TaskExecution(**exec_dict))
        return executions
    
    def get_execution(self, execution_id: int) -> Optional[TaskExecution]:
        """根据ID获取单个执行记录"""
        Execution = Query()
        result = self.executions_db.get(Execution.id == execution_id)
        if result:
            result = result.copy()
            result['created_at'] = self._parse_datetime(result['created_at'])
            if result.get('started_at'):
                result['started_at'] = self._parse_datetime(result['started_at'])
            if result.get('completed_at'):
                result['completed_at'] = self._parse_datetime(result['completed_at'])
            return TaskExecution(**result)
        return None
    
    def get_all_executions(
        self, 
        limit: int = 100,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[TaskExecution]:
        """获取所有任务执行记录"""
        executions = []
        results = self.executions_db.all()
        
        # 过滤搜索
        if search:
            search_lower = search.lower()
            results = [
                r for r in results 
                if search_lower in r.get('task_name', '').lower() or
                   search_lower in r.get('command', '').lower() or
                   search_lower in (r.get('stdout', '') or '').lower() or
                   search_lower in (r.get('stderr', '') or '').lower()
            ]
        
        # 排序
        reverse = sort_order.lower() == "desc"
        if sort_by == "started_at":
            results.sort(key=lambda x: x.get('started_at') or '', reverse=reverse)
        elif sort_by == "task_name":
            results.sort(key=lambda x: x.get('task_name', ''), reverse=reverse)
        elif sort_by == "status":
            results.sort(key=lambda x: x.get('status', ''), reverse=reverse)
        else:  # default: created_at
            results.sort(key=lambda x: x.get('created_at', ''), reverse=reverse)
        
        for exec_dict in results[:limit]:
            exec_dict = exec_dict.copy()
            
            # 确保created_at字段存在
            if 'created_at' in exec_dict:
                exec_dict['created_at'] = self._parse_datetime(exec_dict['created_at'])
            else:
                # 如果缺少created_at，使用当前时间
                exec_dict['created_at'] = datetime.now()
                
            if exec_dict.get('started_at'):
                exec_dict['started_at'] = self._parse_datetime(exec_dict['started_at'])
            if exec_dict.get('completed_at'):
                exec_dict['completed_at'] = self._parse_datetime(exec_dict['completed_at'])
            
            try:
                executions.append(TaskExecution(**exec_dict))
            except Exception as e:
                logger.error(f"解析执行记录失败: {e}, 记录: {exec_dict}")
                continue
        return executions
    
    def delete_executions_by_filter(
        self,
        search: Optional[str] = None,
        task_name: Optional[str] = None
    ) -> int:
        """根据过滤条件删除执行记录"""
        Execution = Query()
        
        # 如果没有任何过滤条件，删除所有记录
        if not search and not task_name:
            all_records = self.executions_db.all()
            deleted_count = len(all_records)
            if deleted_count > 0:
                self.executions_db.truncate()  # 清空所有记录
            return deleted_count
        
        if search:
            search_lower = search.lower()
            # 这里需要通过遍历来实现复杂搜索条件
            to_delete = []
            for record in self.executions_db.all():
                if (search_lower in record.get('task_name', '').lower() or
                    search_lower in record.get('command', '').lower() or
                    search_lower in (record.get('stdout', '') or '').lower() or
                    search_lower in (record.get('stderr', '') or '').lower()):
                    to_delete.append(record.doc_id)
            
            # 删除匹配的记录
            deleted_count = 0
            for doc_id in to_delete:
                if self.executions_db.remove(doc_ids=[doc_id]):
                    deleted_count += 1
            return deleted_count
        
        if task_name:
            return len(self.executions_db.remove(Execution.task_name == task_name))
        
        return 0
    
    def cleanup_old_executions(self, days: int = 30):
        """清理旧的执行记录"""
        from datetime import timedelta
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        Execution = Query()
        self.executions_db.remove(Execution.created_at < cutoff_date)
    
    def close(self):
        """关闭数据库连接"""
        self.devices_db.close()
        self.tasks_db.close()
        self.executions_db.close()
        self.counters_db.close()