# 技术栈详解

## 后端技术栈

### 1. Web框架 - FastAPI
**版本**: 0.104.1+  
**选择理由**:
- 现代化的异步Web框架
- 自动生成OpenAPI文档
- 高性能异步处理
- 优秀的类型注解支持

**核心特性**:
- RESTful API设计
- Pydantic数据验证
- 异步请求处理
- 自动API文档生成

### 2. ASGI服务器 - Uvicorn
**版本**: 0.24.0+  
**配置选项**:
- 支持多进程worker
- 热重载开发模式
- SSL/TLS支持
- 自定义日志配置

### 3. 数据库 - TinyDB
**版本**: 4.8.0+  
**自定义存储**: YAMLStorage  
**特点**:
- 轻量级嵌入式数据库
- 纯Python实现
- 支持查询和索引
- 自定义存储后端

**存储结构**:
```yaml
# data/devices.yaml - WOL设备
_default:
  '1':
    id: 1
    name: "设备名称"
    hostname: "host.example.com"
    ip_address: "192.168.1.100"
    mac_address: "00:11:22:33:44:55"

# data/tasks.yaml - 定时任务
_default:
  '1':
    id: 1
    name: "任务名称"
    task_type: "shell"
    command: "echo 'Hello World'"
    enabled: true
    cron_expression: "0 */5 * * * *"
```

### 4. 任务调度 - APScheduler
**版本**: 3.10.4+  
**调度器类型**: AsyncIOScheduler  
**支持触发器**:
- CronTrigger: Cron表达式调度
- IntervalTrigger: 间隔时间调度
- DateTrigger: 单次执行调度

**配置示例**:
```python
scheduler = AsyncIOScheduler(
    job_defaults={
        'coalesce': True,
        'max_instances': 1,
        'misfire_grace_time': 30
    }
)
```

### 5. 数据验证 - Pydantic
**版本**: 2.5.0+  
**核心模型**:
- BaseModel数据验证
- 类型注解支持
- 自动序列化/反序列化
- 数据验证错误处理

### 6. 系统监控 - psutil
**版本**: 5.9.6+  
**监控功能**:
- CPU使用率
- 内存使用情况
- 磁盘空间统计
- 网络接口状态

## 前端技术栈

### 1. UI框架 - Bootstrap 5
**版本**: 5.1.3  
**特性**:
- 响应式栅格系统
- 现代化组件库
- 移动端优先设计
- CSS自定义属性支持

**主要组件**:
- Navigation (导航栏)
- Cards (卡片布局)
- Modals (模态框)
- Forms (表单)
- Tables (数据表格)

### 2. 图标库 - Bootstrap Icons
**版本**: 1.7.2  
**使用方式**: 本地静态文件  
**图标数量**: 1600+ SVG图标

### 3. 代码编辑器 - CodeMirror
**版本**: 5.65.2  
**功能特性**:
- Shell脚本语法高亮
- 行号显示
- 代码折叠
- 自动缩进
- 搜索替换

**配置选项**:
```javascript
CodeMirror.fromTextArea(textarea, {
    mode: 'shell',
    theme: 'default',
    lineNumbers: true,
    indentUnit: 2,
    tabSize: 2
});
```

### 4. JavaScript架构
**架构模式**: 模块化单页应用  
**核心功能**:
- AJAX异步请求
- DOM操作和事件处理
- 实时状态更新
- 响应式交互

**主要模块**:
```javascript
// 核心API客户端
class APIClient {
    async get(url) { /* ... */ }
    async post(url, data) { /* ... */ }
    async put(url, data) { /* ... */ }
    async delete(url) { /* ... */ }
}

// 页面管理器
class PageManager {
    switchTab(tabName) { /* ... */ }
    updateUI() { /* ... */ }
}
```

## 网络协议实现

### 1. Wake-on-LAN (WOL)
**实现方式**: 原生Python UDP套接字  
**协议细节**:
- 魔术包格式: 6字节0xFF + 16次MAC地址
- 广播端口: 9 (可配置)
- 支持有线和无线网络

**代码实现**:
```python
def create_magic_packet(mac_address: str) -> bytes:
    # 创建魔术包
    mac_bytes = bytes.fromhex(mac_address.replace(':', ''))
    return b'\xff' * 6 + mac_bytes * 16
```

### 2. ICMP Ping
**实现方式**: 系统ping命令调用  
**超时设置**: 3秒默认超时  
**跨平台支持**: Windows/Linux/macOS

## 安全特性

### 1. Content Security Policy (CSP)
```html
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; 
               script-src 'self' 'unsafe-inline'; 
               style-src 'self' 'unsafe-inline';">
```

### 2. 输入验证
- Pydantic模型验证
- XSS防护
- SQL注入防护（TinyDB天然防护）
- 文件路径验证

### 3. 权限控制
- 容器化部署隔离
- 最小权限原则
- 网络访问控制

## 配置管理

### 1. 环境变量
```bash
SM_PORT=8000              # 服务端口
SM_LOG_LEVEL=INFO         # 日志级别
SM_ENV=production         # 运行环境
TZ=Asia/Shanghai          # 时区设置
SM_WOL_PORT=9            # WOL端口
SM_WOL_TIMEOUT=3         # WOL超时
SM_TASK_TIMEOUT=300      # 任务超时
```

### 2. 配置文件
- `main.py`: 启动配置
- `app/api.py`: API路由配置
- `Dockerfile`: 容器配置
- `requirements.txt`: 依赖管理

## 日志系统

### 1. 日志配置
- 格式: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- 输出: 控制台 + 文件
- 级别: DEBUG/INFO/WARNING/ERROR
- 编码: UTF-8

### 2. 日志文件
- 主日志: `logs/server_manager.log`
- 任务日志: 集成到主日志
- 日志轮转: 按需实现

## 性能优化

### 1. 异步处理
- FastAPI异步路由
- 非阻塞任务执行
- 异步数据库操作

### 2. 资源优化
- 静态文件本地化
- CSS/JS文件压缩
- 图片优化

### 3. 缓存策略
- 浏览器缓存控制
- API响应缓存
- 静态资源缓存