# Docker Hub 自动发布设置指南

本文档详细说明如何配置GitHub Actions来自动构建和发布Docker镜像到Docker Hub和GitHub Container Registry。

## 🔧 前置准备

### 1. Docker Hub 配置

1. **注册Docker Hub账号**
   - 访问 [Docker Hub](https://hub.docker.com/) 并注册账号
   - 记录你的用户名，如：`yourusername`

2. **生成Access Token**
   - 登录Docker Hub，进入 [Security Settings](https://hub.docker.com/settings/security)
   - 点击 "New Access Token"
   - 输入Token名称（如：`github-actions`）
   - 选择权限：`Read, Write, Delete`
   - 复制生成的Token（只会显示一次）

### 2. GitHub Repository 配置

1. **设置Repository Secrets**
   - 进入你的GitHub仓库
   - 点击 `Settings` -> `Secrets and variables` -> `Actions`
   - 添加以下Secrets：

   ```
   DOCKERHUB_USERNAME: 你的Docker Hub用户名
   DOCKERHUB_TOKEN: 上面生成的Access Token
   ```

2. **启用GitHub Packages**
   - 确保仓库启用了GitHub Packages权限
   - 工作流会自动使用 `GITHUB_TOKEN` 发布到 `ghcr.io`

## 🚀 自动化流程说明

### 触发条件

工作流会在以下情况自动触发：

1. **推送到主分支** (`main`, `develop`)
   - 构建并推送 `latest` 标签的镜像
   - 推送到两个Registry

2. **创建版本标签** (`v*`)
   - 构建并推送版本化的镜像
   - 同时更新 `latest` 标签

3. **Pull Request**
   - 仅构建镜像，不推送（用于验证）

4. **创建Release**
   - 专门的发布流程
   - 生成部署文件和脚本

### 镜像标签策略

- **开发分支**: `main`, `develop`
- **版本标签**: `v1.2.1`, `1.2.1`, `1.2`, `1`
- **Latest标签**: 总是指向最新的稳定版本

### 支持的架构

- `linux/amd64` (x86_64)
- `linux/arm64` (ARM64, Apple Silicon)

## 📦 发布的镜像位置

构建成功后，Docker镜像将发布到：

1. **Docker Hub**
   ```bash
   docker pull yourusername/server-manager:latest
   docker pull yourusername/server-manager:v1.2.1
   ```

2. **GitHub Container Registry**
   ```bash
   docker pull ghcr.io/yourusername/server-manager:latest
   docker pull ghcr.io/yourusername/server-manager:v1.2.1
   ```

## 🔍 验证发布

### 1. 检查GitHub Actions

- 进入仓库的 `Actions` 标签
- 查看工作流运行状态
- 检查构建日志确认无错误

### 2. 验证Docker Hub

- 访问 `https://hub.docker.com/r/yourusername/server-manager`
- 确认新的tag已经出现
- 检查镜像大小和层数

### 3. 验证GitHub Packages

- 进入仓库页面，点击右侧的 `Packages`
- 查看 `server-manager` package
- 确认版本和标签正确

## 🏃‍♂️ 使用发布的镜像

### 基础运行命令

```bash
# 使用Docker Hub镜像
docker run -d \
  --name server-manager \
  --network host \
  --cap-add NET_RAW \
  -e SM_PORT=8000 \
  -e TZ=Asia/Shanghai \
  -v server-manager-data:/app/data \
  -v server-manager-logs:/app/logs \
  yourusername/server-manager:latest

# 使用GitHub Container Registry镜像
docker run -d \
  --name server-manager \
  --network host \
  --cap-add NET_RAW \
  -e SM_PORT=8000 \
  -e TZ=Asia/Shanghai \
  -v server-manager-data:/app/data \
  -v server-manager-logs:/app/logs \
  ghcr.io/yourusername/server-manager:latest
```

### 使用Docker Compose

发布的Release中包含 `docker-compose.yml` 文件：

```bash
# 下载compose文件
wget https://github.com/yourusername/server-manager/releases/latest/download/docker-compose.yml

# 启动服务
docker-compose up -d
```

### 使用便捷脚本

发布的Release中包含 `docker-run.sh` 脚本：

```bash
# 下载运行脚本
wget https://github.com/yourusername/server-manager/releases/latest/download/docker-run.sh

# 运行脚本
chmod +x docker-run.sh
./docker-run.sh
```

## 🐛 故障排除

### 1. 构建失败

**检查构建日志**：
- 进入GitHub Actions页面
- 点击失败的工作流
- 查看详细的错误信息

**常见问题**：
- Docker Hub认证失败：检查Secrets配置
- 构建超时：优化Dockerfile，使用构建缓存
- 依赖安装失败：检查requirements.txt

### 2. 推送失败

**权限问题**：
- 确认Docker Hub Token权限正确
- 检查仓库名称拼写

**网络问题**：
- GitHub Actions偶尔网络不稳定
- 重新运行工作流通常可解决

### 3. 镜像拉取失败

**检查镜像标签**：
```bash
# 列出所有可用标签
docker search yourusername/server-manager
```

**使用正确的Registry**：
```bash
# Docker Hub (默认)
docker pull yourusername/server-manager:latest

# GitHub Container Registry
docker pull ghcr.io/yourusername/server-manager:latest
```

## 📋 最佳实践

1. **版本管理**
   - 使用语义化版本号（如：v1.2.1）
   - 主要更新递增主版本号
   - 功能更新递增次版本号
   - Bug修复递增修订版本号

2. **安全考虑**
   - 定期更新Docker Hub Token
   - 不要在代码中硬编码敏感信息
   - 使用非root用户运行容器

3. **性能优化**
   - 利用GitHub Actions缓存
   - 优化Dockerfile层数
   - 使用多阶段构建减小镜像大小

4. **监控和维护**
   - 定期检查工作流执行状态
   - 监控镜像大小变化
   - 及时清理旧版本镜像

## 🔄 手动发布流程

如需手动触发发布：

1. **创建版本标签**
   ```bash
   git tag -a v1.2.1 -m "Release version 1.2.1"
   git push origin v1.2.1
   ```

2. **创建GitHub Release**
   - 进入仓库的 `Releases` 页面
   - 点击 "Create a new release"
   - 选择刚创建的标签
   - 填写Release说明
   - 点击 "Publish release"

3. **验证自动发布**
   - 检查Actions工作流执行
   - 确认Docker镜像已发布
   - 验证Release附件生成

---

配置完成后，每次推送代码或创建Release时，都会自动构建和发布Docker镜像，大大简化了部署流程！