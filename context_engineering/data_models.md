# 数据模型设计

## 存储架构

### 存储引擎
- **数据库**: TinyDB (嵌入式文档数据库)
- **存储格式**: YAML (自定义YAMLStorage)
- **数据目录**: `data/`
- **文件编码**: UTF-8

### 数据文件结构
```
data/
├── devices.yaml      # WOL设备数据
├── tasks.yaml        # 定时任务数据
├── executions.yaml   # 执行记录数据
└── counters.yaml     # ID计数器
```

## 核心数据模型

### 1. Device (WOL设备)

#### Pydantic模型定义
```python
from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime

class Device(BaseModel):
    name: str
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: str
    description: Optional[str] = None
    
    @validator('mac_address')
    def validate_mac_address(cls, v):
        # 验证MAC地址格式
        import re
        pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
        if not re.match(pattern, v):
            raise ValueError('无效的MAC地址格式')
        return v.upper().replace('-', ':')

class DeviceInDB(Device):
    id: int
    created_at: datetime
    updated_at: datetime
```

#### YAML存储示例
```yaml
_default:
  '1':
    id: 1
    name: "办公电脑"
    hostname: "office-pc.local"
    ip_address: "192.168.1.100"
    mac_address: "00:11:22:33:44:55"
    description: "主办公电脑"
    created_at: "2025-09-06T20:53:54.575309"
    updated_at: "2025-09-06T23:53:02.600542"
  '2':
    id: 2
    name: "媒体服务器"
    hostname: null
    ip_address: "192.168.1.200"
    mac_address: "00:11:22:33:44:66"
    description: "NAS存储服务器"
    created_at: "2025-09-06T21:15:30.123456"
    updated_at: "2025-09-06T21:15:30.123456"
```

#### 字段说明
- `id`: 唯一标识符，自增整数
- `name`: 设备友好名称，必填
- `hostname`: 设备主机名，可选
- `ip_address`: IP地址，可选但推荐填写
- `mac_address`: MAC地址，必填，用于WOL
- `description`: 设备描述，可选
- `created_at`: 创建时间戳
- `updated_at`: 最后更新时间戳

### 2. Task (定时任务)

#### Pydantic模型定义
```python
class Task(BaseModel):
    name: str
    task_type: str = "shell"
    command: str
    description: Optional[str] = None
    enabled: bool = True
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    timeout_seconds: int = 300
    max_retries: int = 0
    source_path: Optional[str] = None
    target_path: Optional[str] = None
    target_host: Optional[str] = None
    
    @validator('cron_expression')
    def validate_cron_expression(cls, v):
        if v is None:
            return v
        # 验证Cron表达式格式 (6字段: 秒 分 时 日 月 周)
        import re
        pattern = r'^(\*|([0-5]?[0-9])) (\*|([0-5]?[0-9])) (\*|([0-1]?[0-9]|2[0-3])) (\*|([0-2]?[0-9]|3[0-1])) (\*|([0-9]|1[0-2])) (\*|[0-6])$'
        if not re.match(pattern, v):
            raise ValueError('无效的Cron表达式格式')
        return v

class TaskInDB(Task):
    id: int
    created_at: datetime
    updated_at: datetime
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
```

#### YAML存储示例
```yaml
_default:
  '1':
    id: 4
    name: "hello"
    task_type: "shell"
    command: "echo \"Hello World\""
    description: "打印 hello"
    enabled: true
    cron_expression: null
    interval_seconds: 30
    timeout_seconds: 300
    max_retries: 0
    source_path: null
    target_path: null
    target_host: null
    created_at: "2025-09-06T20:53:54.575309"
    updated_at: "2025-09-06T23:53:02.600542"
    last_run_at: "2025-09-06T23:53:02.566509"
    next_run_at: "2025-09-06T23:53:31.323580+08:00"
  '2':
    id: 5
    name: "系统备份"
    task_type: "shell"
    command: "/usr/local/bin/backup.sh"
    description: "每日系统备份"
    enabled: false
    cron_expression: "0 0 2 * * *"
    interval_seconds: null
    timeout_seconds: 600
    max_retries: 2
    source_path: null
    target_path: null
    target_host: null
    created_at: "2025-09-06T21:13:00.466289"
    updated_at: "2025-09-06T23:23:47.711284"
    last_run_at: "2025-09-06T23:23:47.672965"
    next_run_at: null
```

#### 字段说明
- `id`: 唯一标识符
- `name`: 任务名称
- `task_type`: 任务类型，目前支持"shell"
- `command`: 要执行的命令
- `description`: 任务描述
- `enabled`: 是否启用
- `cron_expression`: Cron表达式，与interval_seconds二选一
- `interval_seconds`: 间隔秒数，与cron_expression二选一
- `timeout_seconds`: 超时时间
- `max_retries`: 最大重试次数
- `source_path`: 源路径（预留字段）
- `target_path`: 目标路径（预留字段）
- `target_host`: 目标主机（预留字段）
- `last_run_at`: 最后执行时间
- `next_run_at`: 下次执行时间

### 3. TaskExecution (执行记录)

#### Pydantic模型定义
```python
class TaskExecution(BaseModel):
    task_id: int
    task_name: str
    status: str  # "running", "success", "failure"
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None  # 执行时长(秒)
    exit_code: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    error_message: Optional[str] = None
    
    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ['running', 'success', 'failure']
        if v not in allowed_statuses:
            raise ValueError(f'状态必须是: {allowed_statuses}')
        return v

class TaskExecutionInDB(TaskExecution):
    id: int
```

#### YAML存储示例
```yaml
_default:
  '1':
    id: 1
    task_id: 4
    task_name: "hello"
    status: "success"
    start_time: "2025-09-06T23:53:02.566509"
    end_time: "2025-09-06T23:53:02.612345"
    duration: 0.045836
    exit_code: 0
    stdout: "Hello World\n"
    stderr: ""
    error_message: null
  '2':
    id: 2
    task_id: 5
    task_name: "系统备份"
    status: "failure"
    start_time: "2025-09-06T23:23:47.672965"
    end_time: "2025-09-06T23:23:52.123456"
    duration: 4.450491
    exit_code: 1
    stdout: "开始备份...\n"
    stderr: "错误: 磁盘空间不足\n"
    error_message: "命令执行失败，退出码: 1"
```

#### 状态说明
- `running`: 正在执行
- `success`: 执行成功 (exit_code == 0)
- `failure`: 执行失败 (exit_code != 0 或异常)

## 辅助数据结构

### 1. Counter (ID计数器)

```yaml
# data/counters.yaml
devices: 2
tasks: 5
executions: 150
```

用于生成自增ID，确保数据唯一性。

### 2. 系统配置 (预留)

```yaml
# data/settings.yaml (未实现)
system:
  timezone: "Asia/Shanghai"
  log_level: "INFO"
  max_execution_history: 1000
  
wol:
  port: 9
  timeout: 3
  broadcast_address: "255.255.255.255"

tasks:
  default_timeout: 300
  max_retries: 3
  executor_pool_size: 5
```

## 数据关系

### 关系图
```
Device (1) -----(0..n) WOLExecution (预留)
Task (1) ------(0..n) TaskExecution
```

### 外键关系
- `TaskExecution.task_id` → `Task.id`
- 删除Task时级联删除相关的TaskExecution记录

## 数据迁移和版本管理

### 版本标识
```yaml
# data/metadata.yaml
version: "1.2.0"
schema_version: 2
last_migration: "2025-09-06T20:00:00"
```

### 迁移脚本示例
```python
def migrate_v1_to_v2():
    """从v1.0迁移到v2.0"""
    # 添加新字段
    for task in tasks_db.all():
        if 'enabled' not in task:
            tasks_db.update({'enabled': True}, doc_ids=[task.doc_id])
    
    # 更新schema版本
    metadata_db.upsert({'schema_version': 2}, Query().type == 'schema')
```

## 数据验证规则

### 输入验证
1. **MAC地址**: 必须符合 XX:XX:XX:XX:XX:XX 格式
2. **IP地址**: 必须是有效的IPv4地址（可选）
3. **Cron表达式**: 6字段格式验证
4. **命令安全**: 禁止包含危险命令

### 数据约束
1. **唯一性**: 设备MAC地址唯一，任务名称唯一
2. **长度限制**: 
   - 名称: 1-100字符
   - 描述: 最大1000字符
   - 命令: 最大10000字符
3. **数值范围**:
   - timeout_seconds: 1-3600
   - interval_seconds: 1-86400
   - max_retries: 0-10

## 性能优化

### 索引策略
```python
# TinyDB查询优化
from tinydb import Query

Device = Query()

# 常用查询索引
devices_db.search(Device.mac_address == mac)  # MAC地址查询
tasks_db.search(Device.enabled == True)       # 启用任务查询
executions_db.search(Device.task_id == task_id)  # 任务执行记录查询
```

### 数据清理
```python
def cleanup_old_executions(days=30):
    """清理旧的执行记录"""
    cutoff_date = datetime.now() - timedelta(days=days)
    executions_db.remove(Query().start_time < cutoff_date.isoformat())
```

### 批量操作
```python
def batch_update_tasks(updates):
    """批量更新任务"""
    for task_id, update_data in updates.items():
        tasks_db.update(update_data, doc_ids=[task_id])
```