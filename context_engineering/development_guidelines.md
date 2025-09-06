# 开发规范指南

## 代码规范

### 1. Python 代码规范

#### 代码风格
- 遵循 PEP 8 标准
- 使用 4 空格缩进，不使用 Tab
- 行长度限制为 88 字符 (Black 格式化标准)
- 使用 UTF-8 编码

#### 命名规范
```python
# 类名: PascalCase
class DeviceManager:
    pass

# 函数名和变量名: snake_case
def get_device_status():
    device_count = 0

# 常量名: UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 300

# 私有成员: 前缀下划线
def _internal_method(self):
    self._private_var = "value"
```

#### 类型注解
```python
from typing import Optional, List, Dict, Any

def create_task(
    name: str,
    command: str,
    cron_expression: Optional[str] = None,
    enabled: bool = True
) -> Dict[str, Any]:
    """创建新任务"""
    return {"id": 1, "name": name}
```

#### 错误处理
```python
import logging

logger = logging.getLogger(__name__)

try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"操作失败: {e}")
    raise
except Exception as e:
    logger.exception("未知错误")
    raise
```

### 2. JavaScript 代码规范

#### 代码风格
```javascript
// 使用 const/let，避免 var
const API_BASE_URL = '/api';
let currentTab = 'devices';

// 函数命名: camelCase
function updateDeviceStatus(deviceId, status) {
    // 实现
}

// 类命名: PascalCase
class APIClient {
    constructor() {
        this.baseURL = API_BASE_URL;
    }
}
```

#### 异步处理
```javascript
// 优先使用 async/await
async function fetchDevices() {
    try {
        const response = await fetch('/api/devices');
        return await response.json();
    } catch (error) {
        console.error('获取设备失败:', error);
        throw error;
    }
}

// 避免回调地狱
// ❌ 不推荐
$.get('/api/devices', function(data) {
    $.get('/api/tasks', function(tasks) {
        // 嵌套回调
    });
});

// ✅ 推荐
const devices = await fetchDevices();
const tasks = await fetchTasks();
```

### 3. CSS/HTML 规范

#### CSS 组织
```css
/* 使用 BEM 命名法 */
.device-card { }
.device-card__header { }
.device-card__body { }
.device-card--offline { }

/* 移动端优先 */
.navigation {
    display: block;
}

@media (min-width: 768px) {
    .navigation {
        display: flex;
    }
}
```

## 架构设计原则

### 1. 单一职责原则
每个模块只负责一个功能领域：
- `wol.py`: WOL协议实现
- `scheduler.py`: 任务调度
- `database.py`: 数据库操作
- `api.py`: API路由

### 2. 依赖注入
```python
class TaskScheduler:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def schedule_task(self, task: Task):
        # 使用注入的数据库管理器
        await self.db_manager.save_task(task)
```

### 3. 错误处理策略
```python
# 自定义异常类
class ServerManagerException(Exception):
    """服务器管理系统基础异常"""
    pass

class DeviceNotFoundException(ServerManagerException):
    """设备未找到异常"""
    pass

class TaskExecutionException(ServerManagerException):
    """任务执行异常"""
    pass
```

## 开发工作流

### 1. 功能开发流程

1. **需求分析**
   - 明确功能需求和用户场景
   - 设计API接口和数据模型
   - 评估技术实现方案

2. **后端开发**
   ```python
   # 1. 定义数据模型
   class Device(BaseModel):
       name: str
       mac_address: str
       ip_address: Optional[str] = None
   
   # 2. 实现业务逻辑
   async def create_device(device: Device) -> Dict[str, Any]:
       # 业务逻辑实现
       pass
   
   # 3. 添加API端点
   @app.post("/api/devices")
   async def create_device_endpoint(device: Device):
       return await create_device(device)
   ```

3. **前端开发**
   ```javascript
   // 1. API客户端
   async function createDevice(deviceData) {
       return await apiClient.post('/api/devices', deviceData);
   }
   
   // 2. UI交互
   function handleDeviceCreate() {
       // 表单验证和提交
   }
   
   // 3. 状态更新
   function updateDeviceList() {
       // 刷新设备列表
   }
   ```

4. **测试验证**
   - 单元测试
   - 集成测试
   - 用户界面测试

### 2. Git 工作流

```bash
# 功能分支开发
git checkout -b feature/add-device-management
git add .
git commit -m "feat: 添加设备管理功能

- 实现设备CRUD操作
- 添加设备状态监控
- 优化设备列表UI"

# 代码审查后合并
git checkout main
git merge feature/add-device-management
```

#### 提交信息规范
```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型(type)**:
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具变动

## 测试策略

### 1. 后端测试
```python
import pytest
from fastapi.testclient import TestClient
from app.api import app

client = TestClient(app)

def test_create_device():
    response = client.post("/api/devices", json={
        "name": "Test Device",
        "mac_address": "00:11:22:33:44:55"
    })
    assert response.status_code == 200
    assert response.json()["name"] == "Test Device"

def test_invalid_mac_address():
    response = client.post("/api/devices", json={
        "name": "Test Device",
        "mac_address": "invalid-mac"
    })
    assert response.status_code == 422
```

### 2. 前端测试
```javascript
// 使用Jest进行单元测试
describe('APIClient', () => {
    test('should fetch devices successfully', async () => {
        const mockFetch = jest.fn().mockResolvedValue({
            json: () => Promise.resolve([{id: 1, name: 'Device 1'}])
        });
        global.fetch = mockFetch;
        
        const client = new APIClient();
        const devices = await client.get('/api/devices');
        
        expect(devices).toHaveLength(1);
        expect(devices[0].name).toBe('Device 1');
    });
});
```

## 性能优化指南

### 1. 后端优化
```python
# 异步处理
async def batch_ping_devices(devices: List[Device]):
    tasks = [ping_device(device) for device in devices]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results

# 数据库查询优化
def get_devices_with_status():
    # 减少数据库查询次数
    devices = db.all()
    # 批量处理而非逐个处理
    return [add_status(device) for device in devices]
```

### 2. 前端优化
```javascript
// 防抖处理
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 搜索输入防抖
const debouncedSearch = debounce(searchDevices, 300);

// DOM操作优化
function updateDeviceList(devices) {
    const fragment = document.createDocumentFragment();
    devices.forEach(device => {
        fragment.appendChild(createDeviceElement(device));
    });
    deviceContainer.appendChild(fragment);
}
```

## 安全开发规范

### 1. 输入验证
```python
from pydantic import validator

class Task(BaseModel):
    command: str
    
    @validator('command')
    def validate_command(cls, v):
        # 禁止危险命令
        dangerous_commands = ['rm -rf', 'format', 'del']
        if any(cmd in v.lower() for cmd in dangerous_commands):
            raise ValueError('不允许执行危险命令')
        return v
```

### 2. 错误信息处理
```python
# ❌ 暴露敏感信息
try:
    execute_command(command)
except Exception as e:
    return {"error": str(e)}  # 可能暴露系统信息

# ✅ 安全的错误处理
try:
    execute_command(command)
except Exception as e:
    logger.error(f"命令执行失败: {e}")
    return {"error": "命令执行失败"}  # 通用错误信息
```

### 3. XSS防护
```javascript
// HTML内容转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 使用textContent而非innerHTML
element.textContent = userInput;  // 安全
element.innerHTML = userInput;    // 危险
```

## 部署和运维

### 1. 环境配置
```python
# 配置管理
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    port: int = 8000
    log_level: str = "INFO"
    data_dir: str = "data"
    
    class Config:
        env_prefix = "SM_"
        env_file = ".env"
```

### 2. 健康检查
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.2.0"
    }
```

### 3. 监控和日志
```python
# 结构化日志
import structlog

logger = structlog.get_logger()

logger.info(
    "任务执行完成",
    task_id=task.id,
    duration=execution_time,
    status="success"
)
```