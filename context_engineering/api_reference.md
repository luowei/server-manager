# API 参考文档

## API 基础信息

**Base URL**: `http://localhost:8000/api`  
**认证方式**: 无需认证 (内网使用)  
**数据格式**: JSON  
**编码**: UTF-8  

## WOL 设备管理 API

### 获取所有设备
```http
GET /api/devices
```

**响应示例**:
```json
[
  {
    "id": 1,
    "name": "办公电脑",
    "hostname": "office-pc.local",
    "ip_address": "192.168.1.100",
    "mac_address": "00:11:22:33:44:55",
    "description": "主办公电脑",
    "created_at": "2025-09-06T20:53:54.575309",
    "updated_at": "2025-09-06T23:53:02.600542",
    "status": "online"
  }
]
```

### 获取单个设备
```http
GET /api/devices/{device_id}
```

**路径参数**:
- `device_id` (int): 设备ID

**响应**: 同上单个设备对象

### 创建设备
```http
POST /api/devices
```

**请求体**:
```json
{
  "name": "新设备",
  "hostname": "new-device.local",
  "ip_address": "192.168.1.101",
  "mac_address": "00:11:22:33:44:66",
  "description": "新添加的设备"
}
```

**必填字段**: `name`, `mac_address`  
**响应**: 创建的设备对象

### 更新设备
```http
PUT /api/devices/{device_id}
```

**请求体**: 同创建设备  
**响应**: 更新后的设备对象

### 删除设备
```http
DELETE /api/devices/{device_id}
```

**响应**: 
```json
{"message": "设备删除成功"}
```

### 发送WOL包
```http
POST /api/wol/wake
```

**请求体**:
```json
{
  "device_id": 1
}
```

**响应**:
```json
{
  "message": "WOL包发送成功",
  "device_name": "办公电脑"
}
```

### Ping设备
```http
POST /api/wol/ping/{device_id}
```

**响应**:
```json
{
  "device_id": 1,
  "status": "online",
  "response_time": 12.5,
  "message": "设备在线"
}
```

## 定时任务管理 API

### 获取所有任务
```http
GET /api/tasks
```

**响应示例**:
```json
[
  {
    "id": 1,
    "name": "系统备份",
    "task_type": "shell",
    "command": "/usr/local/bin/backup.sh",
    "description": "每日系统备份",
    "enabled": true,
    "cron_expression": "0 0 2 * * *",
    "interval_seconds": null,
    "timeout_seconds": 300,
    "max_retries": 0,
    "source_path": null,
    "target_path": null,
    "target_host": null,
    "created_at": "2025-09-06T20:53:54.575309",
    "updated_at": "2025-09-06T23:53:02.600542",
    "last_run_at": "2025-09-06T23:53:02.566509",
    "next_run_at": "2025-09-07T02:00:00+08:00"
  }
]
```

### 获取单个任务
```http
GET /api/tasks/{task_id}
```

### 创建任务
```http
POST /api/tasks
```

**请求体**:
```json
{
  "name": "新任务",
  "task_type": "shell",
  "command": "echo 'Hello World'",
  "description": "测试任务",
  "enabled": true,
  "cron_expression": "0 */5 * * * *",
  "timeout_seconds": 300,
  "max_retries": 0
}
```

**任务类型**:
- `shell`: Shell脚本任务

**调度配置** (二选一或都不选):
- `cron_expression`: Cron表达式调度
- `interval_seconds`: 间隔时间调度
- 都不填: 仅手动执行

**Cron表达式格式**: `秒 分 时 日 月 周`
- `0 */5 * * * *`: 每5分钟执行
- `0 0 2 * * *`: 每天2点执行
- `0 0 0 * * 1`: 每周一0点执行

### 更新任务
```http
PUT /api/tasks/{task_id}
```

### 删除任务
```http
DELETE /api/tasks/{task_id}
```

### 立即执行任务
```http
POST /api/tasks/{task_id}/execute
```

**响应**:
```json
{
  "message": "任务执行已启动",
  "execution_id": "exec_123456"
}
```

### 切换任务状态
```http
POST /api/tasks/{task_id}/toggle
```

**响应**:
```json
{
  "message": "任务已启用",
  "enabled": true
}
```

## 执行记录 API

### 获取所有执行记录
```http
GET /api/executions
```

**查询参数**:
- `task_id` (int, 可选): 筛选指定任务的执行记录
- `status` (str, 可选): 筛选执行状态 (`success`, `failure`, `running`)
- `limit` (int, 可选): 限制返回数量，默认100
- `search` (str, 可选): 搜索关键词

**响应示例**:
```json
[
  {
    "id": 1,
    "task_id": 1,
    "task_name": "系统备份",
    "status": "success",
    "start_time": "2025-09-06T23:53:02.566509",
    "end_time": "2025-09-06T23:53:05.123456",
    "duration": 2.557,
    "exit_code": 0,
    "stdout": "备份完成\n文件数量: 1234\n",
    "stderr": "",
    "error_message": null
  }
]
```

### 获取任务执行记录
```http
GET /api/tasks/{task_id}/executions
```

**响应**: 指定任务的执行记录列表

### 删除执行记录
```http
DELETE /api/executions
```

**请求体**:
```json
{
  "search": "备份",
  "task_id": 1
}
```

**行为**:
- 如果提供了搜索条件，删除匹配的记录
- 如果没有提供任何条件，清空所有记录

**响应**:
```json
{
  "message": "已删除 5 条执行记录"
}
```

## 系统状态 API

### 获取系统状态
```http
GET /api/status
```

**响应**:
```json
{
  "server": {
    "status": "running",
    "uptime": "2 days, 5:30:15",
    "version": "1.2.0",
    "python_version": "3.10.12",
    "start_time": "2025-09-04T18:22:47.123456"
  },
  "system": {
    "platform": "Linux",
    "cpu_count": 8,
    "cpu_usage": 15.2,
    "memory": {
      "total": 16777216000,
      "available": 12884901888,
      "percent": 23.2
    },
    "disk": {
      "total": 1000204886016,
      "used": 450000000000,
      "free": 550204886016,
      "percent": 45.0
    }
  },
  "database": {
    "devices_count": 5,
    "tasks_count": 12,
    "executions_count": 156,
    "data_size": "2.1 MB"
  },
  "scheduler": {
    "status": "running",
    "active_jobs": 3,
    "next_run": "2025-09-07T02:00:00+08:00"
  }
}
```

### 系统维护
```http
POST /api/maintenance/cleanup
```

**请求体**:
```json
{
  "days": 30
}
```

**功能**: 清理指定天数前的执行记录

**响应**:
```json
{
  "message": "清理完成",
  "deleted_count": 25,
  "days": 30
}
```

## Web界面路由

### 主界面
```http
GET /
```
返回主要的单页应用界面

### API文档
```http
GET /docs
```
Swagger UI 自动生成的API文档

```http
GET /redoc
```
ReDoc 格式的API文档

## WebSocket (未实现)

预留用于实时状态更新的WebSocket端点:

```http
WS /ws/status
```

## 错误响应格式

所有API错误都返回统一格式:

```json
{
  "detail": "错误描述",
  "error_code": "DEVICE_NOT_FOUND",
  "timestamp": "2025-09-07T00:07:02.354232"
}
```

**常见HTTP状态码**:
- `200`: 成功
- `201`: 创建成功
- `400`: 请求参数错误
- `404`: 资源不存在
- `422`: 数据验证失败
- `500`: 服务器内部错误

## 数据模型定义

### Device Model
```python
class Device(BaseModel):
    name: str
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: str
    description: Optional[str] = None
```

### Task Model
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
```

### Execution Model
```python
class TaskExecution(BaseModel):
    task_id: int
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    exit_code: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    error_message: Optional[str] = None
```