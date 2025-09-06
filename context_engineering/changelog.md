# 更新日志

## v1.2.0 (2025-09-06)

### 🎉 重大更新

#### 新功能
- ✨ **CodeMirror代码编辑器集成**
  - Shell脚本语法高亮支持
  - 行号显示和代码折叠
  - 自动缩进和代码补全
  - 优化的编辑体验

- 📱 **完整移动端响应式支持**
  - 移动端优化的导航界面
  - 触摸友好的交互设计
  - 自适应布局优化
  - 移动端专用菜单系统

- 🔧 **手动执行模式**
  - 支持无调度配置的任务创建
  - 仅手动执行的任务管理
  - 灵活的任务调度策略

- 🔍 **智能执行记录管理**
  - 执行记录搜索功能
  - 批量删除和清空功能
  - 智能删除按钮文本显示
  - 搜索结果高亮显示

#### 界面优化
- 🎨 **执行日志查看优化**
  - 75%页面高度的日志显示区域
  - 紧凑的日志内容布局
  - 减少不必要的空白空间
  - 优化的滚动和显示体验

- 🖥️ **桌面端界面改进**
  - 修复导航栏选择器问题
  - 优化侧边栏导航体验
  - 改进页面切换动画
  - 统一的UI组件风格

- 📱 **移动端导航体验**
  - 响应式汉堡菜单
  - 触摸优化的按钮设计
  - 移动端友好的表单界面
  - 自适应的模态框大小

#### 技术改进
- 🔒 **安全策略增强**
  - Content Security Policy (CSP) 支持
  - 移除内联事件处理器
  - XSS防护机制优化
  - 安全的JavaScript事件处理

- 📦 **静态资源本地化**
  - 所有CDN资源本地化部署
  - 消除外部依赖，提升加载速度
  - 离线环境支持
  - 资源版本锁定，确保稳定性

- ⚡ **任务调度逻辑优化**
  - 简化任务状态为启用/禁用
  - 支持手动执行模式
  - 优化调度器性能
  - 改进错误处理机制

#### 开发工具
- 🐳 **Docker容器化支持**
  - 完整的Dockerfile配置
  - Docker Compose支持
  - 多架构镜像支持
  - 生产就绪的容器配置

- 📝 **Context Engineering文档**
  - 完整的项目上下文文档
  - AI助手开发指南
  - 技术栈详细说明
  - 故障排查手册

### 🐛 Bug修复

- 修复JavaScript tab切换错误
- 解决CodeMirror编辑器行号重叠问题
- 修复执行记录清空逻辑错误
- 解决移动端样式显示问题
- 修复CSP策略冲突问题

### 🔧 技术细节

#### 依赖更新
```
Bootstrap: 5.1.3 (本地化)
Bootstrap Icons: 1.7.2 (本地化)  
CodeMirror: 5.65.2 (本地化)
FontAwesome: 移除，使用Bootstrap Icons替代
```

#### API变更
- 任务状态字段简化 (`enabled` boolean)
- 执行记录搜索API优化
- 系统状态API信息丰富化

#### 数据库架构
- 优化YAML存储结构
- 改进数据序列化性能
- 增强数据一致性验证

---

## v1.1.0 (2025-09-05)

### 新功能
- 🌐 **WOL设备管理**
  - 设备增删查改功能
  - 实时状态检测
  - WOL魔术包发送
  - Ping连通性测试

- ⏰ **定时任务系统**
  - Cron表达式调度
  - 间隔时间调度
  - Shell脚本任务执行
  - 任务启用/禁用控制

- 📊 **执行记录追踪**
  - 详细执行日志
  - 执行状态监控
  - 错误信息记录
  - 执行时间统计

- 💾 **数据持久化**
  - TinyDB嵌入式数据库
  - YAML格式数据存储
  - 自定义存储后端
  - 数据版本控制支持

### 技术实现
- FastAPI异步Web框架
- APScheduler任务调度
- Bootstrap 4 响应式界面
- 原生WOL协议实现

---

## v1.0.0 (2025-09-01)

### 初始发布
- 🚀 **基础架构搭建**
  - FastAPI Web框架集成
  - TinyDB数据库配置
  - 基础API接口设计
  - HTML模板系统

- 🔧 **核心功能实现**
  - WOL设备基础管理
  - 简单任务调度
  - 基础Web界面
  - 日志系统配置

### 技术选型
- Python 3.7+ 作为主要开发语言
- FastAPI 作为Web框架
- TinyDB 作为轻量级数据库
- Bootstrap 作为前端UI框架

---

## 版本规划

### v1.3.0 (计划中)

#### 预期功能
- 🔐 **用户认证系统**
  - 基础用户登录
  - 会话管理
  - 权限控制

- 📡 **WebSocket实时通信**
  - 实时状态推送
  - 任务执行进度
  - 系统状态监控

- 📈 **监控和告警**
  - 任务执行监控
  - 系统资源监控
  - 邮件/webhook告警

- 🔧 **高级任务类型**
  - HTTP请求任务
  - 文件传输任务
  - 数据备份任务

### v1.4.0 (计划中)

#### 预期功能
- 🌍 **国际化支持**
  - 多语言界面
  - 时区自动检测
  - 本地化配置

- 📊 **数据分析**
  - 执行统计图表
  - 性能分析报告
  - 趋势预测

- 🔌 **插件系统**
  - 任务类型扩展
  - 自定义触发器
  - 第三方集成

### v2.0.0 (长期规划)

#### 重大更新
- 🏗️ **微服务架构**
  - 服务拆分和解耦
  - 容器编排支持
  - 高可用部署

- 🔄 **集群支持**
  - 多节点部署
  - 负载均衡
  - 故障转移

- 🛡️ **企业级安全**
  - LDAP/AD集成
  - RBAC权限模型
  - 审计日志

---

## 迁移指南

### 从 v1.1.x 升级到 v1.2.0

#### 数据迁移
```bash
# 备份现有数据
docker run --rm \
  -v server-manager-data:/source:ro \
  -v $(pwd):/backup \
  alpine tar czf /backup/v1.1_backup.tar.gz -C /source .

# 升级容器
docker pull server-manager:v1.2.0
docker stop server-manager
docker rm server-manager

# 启动新版本
docker run -d \
  --name server-manager \
  --network host \
  --cap-add NET_RAW \
  -v server-manager-data:/app/data \
  -v server-manager-logs:/app/logs \
  server-manager:v1.2.0
```

#### 配置更新
- 任务状态字段自动迁移
- CSS样式文件本地化
- JavaScript文件更新

### 从 v1.0.x 升级到 v1.1.0

#### 数据库架构更新
```python
# 数据迁移脚本
def migrate_v1_0_to_v1_1():
    # 添加新字段到现有任务
    for task in tasks_db.all():
        if 'enabled' not in task:
            tasks_db.update({'enabled': True}, doc_ids=[task.doc_id])
        if 'last_run_at' not in task:
            tasks_db.update({'last_run_at': None}, doc_ids=[task.doc_id])
```

---

## 兼容性说明

### 系统要求
- **Python**: 3.7+ (推荐 3.9+)
- **操作系统**: Linux/macOS/Windows
- **Docker**: 20.10+ (容器部署)
- **浏览器**: Chrome 90+, Firefox 88+, Safari 14+

### API兼容性
- v1.2.0 向后兼容 v1.1.x API
- 新增字段使用默认值
- 废弃字段保持支持

### 数据兼容性
- YAML数据格式保持兼容
- 自动数据迁移支持
- 备份恢复机制完善

---

## 贡献者

感谢以下贡献者的努力：

- **Claude AI Assistant** - 主要开发者
- **社区用户** - 功能建议和问题反馈
- **测试用户** - 功能测试和验证

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](../LICENSE) 文件。