# 服务器管理系统

一个基于FastAPI的Web应用，提供局域网唤醒(WOL)和定时任务管理功能。

## 功能特性

### WOL设备管理
- 支持通过hostname、IP地址或MAC地址添加唤醒设备
- 设备信息的增删查改功能
- 实时设备状态检测(在线/离线)
- WOL魔术包发送功能
- 设备Ping测试功能

### 定时任务管理
- 支持Shell脚本任务执行，带语法高亮编辑器
- 支持Cron表达式和间隔时间两种调度方式
- 支持手动执行模式（无调度配置时仅支持手动执行）
- 任务的启用/禁用二状态控制
- 详细的任务执行状态和日志查看
- 任务立即执行功能
- 执行记录搜索、排序和删除功能

### 数据存储
- 使用TinyDB作为嵌入式数据库
- 自定义YAMLStorage以YAML格式存储数据
- 支持数据的持久化和版本控制

### Web界面
- 基于Bootstrap 5的完全响应式Web界面
- 支持桌面端和移动端优化显示
- CodeMirror集成的Shell脚本语法高亮编辑器
- 实时状态更新和操作反馈
- 完整的设备和任务管理功能
- 优化的执行日志查看界面（75%页面高度，紧凑布局）
- 智能的执行记录搜索和批量删除功能
- Content Security Policy安全策略支持

## 系统要求

- Python 3.7+
- Linux/macOS/Windows系统
- 网络访问权限(发送WOL包)

## 安装步骤

### 方式一：Docker 运行 (推荐)

#### 使用 Docker 直接运行

1. 克隆项目
```bash
git clone <项目地址>
cd server_manager
```

2. 构建 Docker 镜像
```bash
docker build -t server-manager .
```

3. 运行 Docker 容器 (推荐使用 host 网络支持 WOL 功能)
```bash
# 基本运行
docker run -d \
  --name server-manager \
  --network host \
  --cap-add NET_RAW \
  -e SM_PORT=8000 \
  -e TZ=Asia/Shanghai \
  -v server-manager-data:/app/data \
  -v server-manager-logs:/app/logs \
  server-manager

# 或者使用端口映射模式 (WOL 功能可能受限)
docker run -d \
  --name server-manager \
  -p 8000:8000 \
  -e SM_PORT=8000 \
  -e TZ=Asia/Shanghai \
  -v server-manager-data:/app/data \
  -v server-manager-logs:/app/logs \
  server-manager
```

4. 访问应用
- Web界面: http://localhost:8000
- API文档: http://localhost:8000/docs

5. 容器管理命令
```bash
# 查看容器状态
docker ps

# 查看日志
docker logs -f server-manager

# 停止容器
docker stop server-manager

# 删除容器
docker rm server-manager

# 删除镜像
docker rmi server-manager
```

#### 使用 Docker Compose 运行

1. 克隆项目
```bash
git clone <项目地址>
cd server_manager
```

2. 配置环境变量 (可选)
```bash
cp .env.example .env
# 编辑 .env 文件，根据需要修改配置
```

3. 使用 docker-compose 启动
```bash
docker-compose up -d
```

4. 访问应用
- Web界面: http://localhost:8000
- API文档: http://localhost:8000/docs

### 方式二：直接运行

1. 克隆项目或下载代码
```bash
git clone <项目地址>
cd server_manager
```

2. 创建虚拟环境(推荐)
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 启动应用
```bash
python main.py
```

## 使用说明

### 基础使用

1. 启动应用后访问 http://127.0.0.1:8000
2. 在"WOL设备"页面添加需要管理的设备
3. 在"定时任务"页面创建自动化任务：
   - 使用语法高亮编辑器编写Shell命令
   - 设置Cron表达式或间隔时间进行定时调度
   - 或留空调度配置创建仅手动执行的任务
4. 在"执行记录"页面查看任务执行历史：
   - 使用搜索功能筛选特定记录
   - 点击"删除结果"删除搜索到的记录
   - 点击"清空所有"删除全部执行记录
5. 在"系统状态"页面监控系统运行状态

### Docker 配置选项

#### 环境变量配置

```bash
# 基础配置
SM_PORT=8000                    # Web服务端口
SM_LOG_LEVEL=INFO              # 日志级别
SM_ENV=production              # 运行环境

# 时区配置
TZ=Asia/Shanghai               # 容器时区
SM_TIMEZONE=Asia/Shanghai      # 应用时区

# WOL配置
SM_WOL_PORT=9                  # WOL端口
SM_WOL_TIMEOUT=3               # WOL超时时间

# 任务配置
SM_TASK_TIMEOUT=300            # 任务超时时间(秒)
SM_TASK_MAX_RETRIES=0          # 任务最大重试次数
SM_LOG_RETENTION_DAYS=30       # 日志保留天数
```

#### Docker命令示例

```bash
# 构建镜像
docker build -t server-manager .

# 运行容器 (使用host网络支持WOL)
docker run -d \
  --name server-manager \
  --network host \
  --cap-add NET_RAW \
  -e SM_PORT=8000 \
  -e TZ=Asia/Shanghai \
  -v server-manager-data:/app/data \
  -v server-manager-logs:/app/logs \
  server-manager

# 查看日志
docker logs -f server-manager

# 停止容器
docker stop server-manager
```

### 命令行参数 (直接运行)

```bash
# 查看帮助
python main.py --help

# 指定监听地址和端口
python main.py --host 0.0.0.0 --port 8080

# 指定数据目录
python main.py --data-dir ./my_data

# 启用调试模式
python main.py --log-level DEBUG --reload
```

## 配置说明

### WOL设备配置
- **设备名称**: 设备的友好名称
- **主机名**: 设备的主机名(可选)
- **IP地址**: 设备的IP地址(可选)
- **MAC地址**: 设备的MAC地址(必需)
- **描述**: 设备描述信息(可选)

### 定时任务配置

#### Shell任务
```bash
# 示例: 每天凌晨2点执行系统备份
命令: /usr/local/bin/backup.sh
Cron表达式: 0 0 2 * * *

# 示例: 仅手动执行的任务（不填写调度配置）
命令: echo "手动执行的任务"
Cron表达式: (留空)
间隔秒数: (留空)
```

#### Shell命令编辑器
- 支持语法高亮显示
- 行号显示
- 自动缩进和代码补全
- 支持多行Shell脚本编写

#### Cron表达式格式
```
格式: 秒 分 时 日 月 周
示例:
0 0 * * * *     # 每小时
0 */5 * * * *   # 每5分钟
0 0 2 * * *     # 每天2点
0 0 0 * * 1     # 每周一0点
0 0 0 1 * *     # 每月1号0点
```

## 目录结构

```
server_manager/
├── app/                    # 应用核心代码
│   ├── __init__.py
│   ├── api.py             # FastAPI路由和API
│   ├── database.py        # 数据库管理
│   ├── models.py          # 数据模型
│   ├── scheduler.py       # 任务调度器
│   ├── storage.py         # 存储后端
│   └── wol.py            # WOL功能模块
├── static/                # 静态文件
│   ├── css/              # 样式文件
│   │   ├── bootstrap.min.css        # Bootstrap框架
│   │   ├── bootstrap-icons.css      # Bootstrap图标
│   │   └── codemirror/              # CodeMirror编辑器样式
│   └── js/               # JavaScript文件
│       ├── bootstrap.bundle.min.js  # Bootstrap脚本
│       ├── codemirror/              # CodeMirror编辑器脚本
│       └── dashboard.js             # 前端主要逻辑
├── templates/             # HTML模板
│   └── dashboard.html     # 主界面模板
├── data/                  # 数据存储目录
│   ├── devices.yaml       # 设备数据
│   ├── tasks.yaml         # 任务数据
│   ├── executions.yaml    # 执行记录
│   └── counters.yaml      # 计数器
├── logs/                  # 日志目录
├── config.py              # 配置文件
├── main.py               # 主程序入口
├── requirements.txt       # Python依赖
└── README.md             # 说明文档
```

## API文档

启动应用后，可访问以下地址查看API文档:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

### 主要API端点

#### WOL设备管理
- `GET /api/devices` - 获取所有设备
- `POST /api/devices` - 创建设备
- `GET /api/devices/{id}` - 获取指定设备
- `PUT /api/devices/{id}` - 更新设备
- `DELETE /api/devices/{id}` - 删除设备
- `POST /api/wol/wake` - 发送WOL包
- `POST /api/wol/ping/{id}` - Ping设备

#### 定时任务管理
- `GET /api/tasks` - 获取所有任务
- `POST /api/tasks` - 创建任务
- `GET /api/tasks/{id}` - 获取指定任务
- `PUT /api/tasks/{id}` - 更新任务
- `DELETE /api/tasks/{id}` - 删除任务
- `POST /api/tasks/{id}/execute` - 立即执行任务
- `POST /api/tasks/{id}/toggle` - 启用/禁用任务

#### 执行记录
- `GET /api/executions` - 获取所有执行记录
- `GET /api/tasks/{id}/executions` - 获取任务执行记录

#### 系统管理
- `GET /api/status` - 获取系统状态
- `POST /api/maintenance/cleanup` - 清理旧日志

## 故障排除

### 常见问题

1. **WOL包发送失败**
   - 检查MAC地址格式是否正确
   - 确认网络权限允许发送广播包
   - 检查目标设备是否支持WOL功能

2. **任务执行失败**
   - 检查命令路径和权限
   - 查看执行日志中的错误信息
   - 确认超时时间设置合理

3. **无法访问Web界面**
   - 检查防火墙设置
   - 确认端口没有被其他程序占用
   - 查看应用启动日志

### 日志查看

```bash
# 查看应用日志
tail -f logs/server_manager.log

# 查看特定级别日志
grep "ERROR" logs/server_manager.log
```

## 开发说明

### 开发环境搭建

1. 安装开发依赖
```bash
pip install -r requirements.txt
```

2. 启动开发服务器
```bash
python main.py --reload --log-level DEBUG
```

### 代码结构说明

- `app/models.py`: 定义所有数据模型
- `app/database.py`: 数据库操作接口
- `app/wol.py`: WOL功能实现
- `app/scheduler.py`: 任务调度和执行
- `app/api.py`: Web API路由
- `app/storage.py`: 自定义YAML存储

## 许可证

MIT License

## 更新日志

### v1.2.0 (2025-09-06)
**新功能：**
- 🎨 添加CodeMirror代码编辑器，支持Shell脚本语法高亮
- 📱 完整的移动端响应式支持
- 🔧 支持手动执行模式（无调度配置的任务）
- 🔍 执行记录智能搜索和批量删除功能
- 🛡️ Content Security Policy安全策略支持

**界面优化：**
- 优化执行日志查看页面，75%页面高度，紧凑布局
- 改进移动端导航体验
- 修复CodeMirror编辑器行号重叠问题
- 智能删除按钮文本（根据搜索状态显示"删除结果"或"清空所有"）

**技术改进：**
- 所有静态资源本地化，不再依赖CDN
- 简化任务状态为启用/禁用两状态
- 优化任务调度逻辑
- 移除内联事件处理器，提升安全性

### v1.1.0
- 基础WOL设备管理功能
- 定时任务调度系统
- 执行记录查看
- Docker容器化支持

### v1.0.0
- 初始版本发布

## 贡献

欢迎提交Bug报告和功能请求！