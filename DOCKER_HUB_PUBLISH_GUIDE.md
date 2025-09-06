# Docker Hub 发布指南

本文档详细说明如何将服务器管理系统镜像发布到 Docker Hub，包括镜像构建、标签管理、发布流程和自动化配置。

## 前置准备

### 1. Docker Hub 账号配置

#### 创建 Docker Hub 账号
1. 访问 [Docker Hub](https://hub.docker.com/) 
2. 注册账号或使用现有账号登录
3. 记录用户名，后续将用于镜像标签

#### 本地 Docker 登录
```bash
# 登录 Docker Hub
docker login

# 输入用户名和密码
Username: your-username
Password: your-password

# 验证登录状态
docker info | grep Username
```

### 2. 访问令牌配置（推荐）

为了提高安全性，建议使用访问令牌而非密码：

1. 登录 Docker Hub
2. 进入 Account Settings > Security
3. 点击 "New Access Token"
4. 创建令牌并保存

```bash
# 使用访问令牌登录
docker login -u your-username -p your-access-token
```

## 镜像构建和标签

### 1. 构建多架构镜像

#### 启用 Docker Buildx
```bash
# 创建新的 builder 实例
docker buildx create --name server-manager-builder --use

# 启动 builder
docker buildx inspect --bootstrap

# 验证支持的平台
docker buildx ls
```

#### 多架构构建命令
```bash
# 构建多架构镜像（AMD64 + ARM64）
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag your-username/server-manager:latest \
  --tag your-username/server-manager:v1.2.0 \
  --push .

# 仅构建 AMD64 架构
docker buildx build \
  --platform linux/amd64 \
  --tag your-username/server-manager:latest \
  --push .
```

### 2. 版本标签管理

#### 标签命名规范
```bash
# 主要版本标签
your-username/server-manager:v1.2.0    # 具体版本
your-username/server-manager:v1.2      # 次要版本
your-username/server-manager:v1        # 主要版本
your-username/server-manager:latest    # 最新版本

# 特殊标签
your-username/server-manager:dev       # 开发版本
your-username/server-manager:beta      # 测试版本
your-username/server-manager:stable    # 稳定版本
```

#### 添加多个标签
```bash
# 方法一：构建时添加多个标签
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag your-username/server-manager:latest \
  --tag your-username/server-manager:v1.2.0 \
  --tag your-username/server-manager:v1.2 \
  --tag your-username/server-manager:stable \
  --push .

# 方法二：为现有镜像添加标签
docker tag your-username/server-manager:v1.2.0 your-username/server-manager:latest
docker tag your-username/server-manager:v1.2.0 your-username/server-manager:v1.2
docker tag your-username/server-manager:v1.2.0 your-username/server-manager:stable
```

## 发布流程

### 1. 手动发布

#### 完整发布流程
```bash
#!/bin/bash
# publish.sh - 手动发布脚本

set -e

# 配置变量
DOCKER_USERNAME="your-username"
IMAGE_NAME="server-manager"
VERSION="v1.2.0"

echo "=== 开始发布 ${IMAGE_NAME}:${VERSION} ==="

# 1. 构建镜像
echo "1. 构建多架构镜像..."
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION} \
  --tag ${DOCKER_USERNAME}/${IMAGE_NAME}:latest \
  --push .

# 2. 验证发布
echo "2. 验证镜像发布..."
docker buildx imagetools inspect ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}

# 3. 测试镜像
echo "3. 测试镜像运行..."
docker run --rm ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION} python --version

echo "=== 发布完成 ==="
```

#### 执行发布
```bash
# 设置执行权限
chmod +x publish.sh

# 执行发布
./publish.sh
```

### 2. 版本管理发布

#### 语义化版本发布脚本
```bash
#!/bin/bash
# semantic_publish.sh

set -e

VERSION=$1
if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version> (e.g., v1.2.0)"
    exit 1
fi

# 解析版本号
MAJOR=$(echo $VERSION | sed 's/v\([0-9]*\)\.\([0-9]*\)\.\([0-9]*\)/\1/')
MINOR=$(echo $VERSION | sed 's/v\([0-9]*\)\.\([0-9]*\)\.\([0-9]*\)/\2/')
PATCH=$(echo $VERSION | sed 's/v\([0-9]*\)\.\([0-9]*\)\.\([0-9]*\)/\3/')

DOCKER_USERNAME="your-username"
IMAGE_NAME="server-manager"

echo "发布版本: $VERSION (Major: $MAJOR, Minor: $MINOR, Patch: $PATCH)"

# 构建并推送镜像
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION} \
  --tag ${DOCKER_USERNAME}/${IMAGE_NAME}:v${MAJOR}.${MINOR} \
  --tag ${DOCKER_USERNAME}/${IMAGE_NAME}:v${MAJOR} \
  --tag ${DOCKER_USERNAME}/${IMAGE_NAME}:latest \
  --push .

echo "版本 $VERSION 发布完成！"
```

### 3. 镜像验证

#### 发布后验证脚本
```bash
#!/bin/bash
# verify_publish.sh

DOCKER_USERNAME="your-username"
IMAGE_NAME="server-manager"
VERSION="v1.2.0"

echo "=== 验证镜像发布 ==="

# 1. 检查镜像信息
echo "1. 检查镜像详情..."
docker buildx imagetools inspect ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}

# 2. 拉取并测试镜像
echo "2. 拉取镜像..."
docker pull ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}

# 3. 运行基本测试
echo "3. 运行基本测试..."
docker run --rm ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION} python -c "
import sys
print(f'Python version: {sys.version}')

# 测试主要依赖
try:
    import fastapi
    import uvicorn
    import tinydb
    import yaml
    print('Dependencies check: PASS')
except ImportError as e:
    print(f'Dependencies check: FAIL - {e}')
    sys.exit(1)

print('Image verification: SUCCESS')
"

echo "=== 验证完成 ==="
```

## 自动化发布

### 1. GitHub Actions 配置

#### 工作流配置文件
创建 `.github/workflows/docker-publish.yml`:

```yaml
name: Docker Build and Push

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: docker.io
  IMAGE_NAME: server-manager

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Log in to Docker Hub
      if: github.event_name != 'pull_request'
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ secrets.DOCKER_USERNAME }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
          type=semver,pattern={{major}}
          type=raw,value=latest,enable={{is_default_branch}}

    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        platforms: linux/amd64,linux/arm64
        push: ${{ github.event_name != 'pull_request' }}
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

    - name: Update Docker Hub description
      if: github.event_name != 'pull_request'
      uses: peter-evans/dockerhub-description@v3
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
        repository: ${{ secrets.DOCKER_USERNAME }}/${{ env.IMAGE_NAME }}
        readme-filepath: ./README.md
```

#### GitHub Secrets 配置
在 GitHub 仓库设置中添加以下 Secrets：

```
DOCKER_USERNAME: your-docker-hub-username
DOCKER_PASSWORD: your-docker-hub-access-token
```

### 2. 版本发布触发

#### 创建 Git 标签
```bash
# 创建版本标签
git tag -a v1.2.0 -m "Release version 1.2.0"

# 推送标签到远程仓库
git push origin v1.2.0

# 推送所有标签
git push origin --tags
```

#### 自动化版本发布脚本
```bash
#!/bin/bash
# release.sh - 自动化版本发布

set -e

VERSION=$1
if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version> (e.g., v1.2.0)"
    exit 1
fi

# 确保工作目录清洁
if [[ -n $(git status --porcelain) ]]; then
    echo "Error: Working directory is not clean"
    exit 1
fi

# 更新版本信息
echo "更新版本信息到 $VERSION"
# 这里可以添加更新版本号的逻辑，比如更新 __version__ 文件

# 提交版本更新
git add -A
git commit -m "Release $VERSION" || echo "No changes to commit"

# 创建标签
git tag -a $VERSION -m "Release $VERSION"

# 推送到远程
git push origin main
git push origin $VERSION

echo "版本 $VERSION 发布流程已启动，请在 GitHub Actions 中查看构建状态"
```

## Docker Hub 仓库配置

### 1. 仓库设置

#### 仓库描述模板
```markdown
# Server Manager - 服务器管理系统

一个基于 FastAPI 的 Web 应用，提供局域网唤醒 (WOL) 和定时任务管理功能。

## 快速开始

```bash
# 使用 host 网络运行 (推荐，支持 WOL)
docker run -d \
  --name server-manager \
  --network host \
  --cap-add NET_RAW \
  -e SM_PORT=8000 \
  -e TZ=Asia/Shanghai \
  -v server-manager-data:/app/data \
  -v server-manager-logs:/app/logs \
  your-username/server-manager:latest

# 访问 Web 界面
open http://localhost:8000
```

## 主要特性

- 🌐 WOL 设备管理和远程唤醒
- ⏰ 定时任务调度和执行
- 📱 响应式 Web 界面
- 🐳 Docker 容器化部署
- 📝 详细的执行日志记录

## 文档链接

- [完整文档](https://github.com/your-username/server-manager)
- [Docker Hub](https://hub.docker.com/r/your-username/server-manager)
- [GitHub Issues](https://github.com/your-username/server-manager/issues)

## 支持的架构

- linux/amd64
- linux/arm64
```

### 2. Webhook 配置

#### 自动构建配置
1. 在 Docker Hub 仓库设置中启用自动构建
2. 连接 GitHub 仓库
3. 配置构建规则：

```yaml
# 构建规则配置
Source Type: Tag
Source: /^v([0-9.]+)$/
Docker Tag: {\1}
Build Context: /
```

## 高级配置

### 1. 多阶段构建优化

#### 优化的 Dockerfile
```dockerfile
# 多阶段构建，减小镜像大小
FROM python:3.10-slim as builder

# 安装构建依赖
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 生产阶段
FROM python:3.10-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    iputils-ping \
    rsync \
    openssh-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 创建应用用户
RUN groupadd -r app && useradd -r -g app app

# 设置工作目录
WORKDIR /app

# 复制 Python 依赖
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# 复制应用代码
COPY --chown=app:app . .

# 创建数据和日志目录
RUN mkdir -p /app/data /app/logs && \
    chown -R app:app /app/data /app/logs

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:${SM_PORT:-8000}/health || exit 1

# 切换到应用用户
USER app

# 暴露端口
EXPOSE ${SM_PORT:-8000}

# 启动命令
ENTRYPOINT ["python", "main.py"]
CMD ["--host", "0.0.0.0", "--port", "8000"]
```

### 2. 镜像大小优化

#### 镜像分析和优化
```bash
# 分析镜像层大小
docker history your-username/server-manager:latest

# 使用 dive 工具分析镜像
docker run --rm -it \
  -v /var/run/docker.sock:/var/run/docker.sock \
  wagoodman/dive:latest your-username/server-manager:latest

# 清理构建缓存
docker buildx prune -f
```

### 3. 安全扫描

#### 漏洞扫描
```bash
# 使用 Trivy 扫描漏洞
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image your-username/server-manager:latest

# 使用 Snyk 扫描
snyk container test your-username/server-manager:latest
```

## 故障排除

### 1. 构建失败

#### 常见问题
```bash
# 问题1: 平台不支持
Error: multiple platforms feature is currently not supported for docker driver

# 解决方案: 使用 buildx
docker buildx create --use
docker buildx build --platform linux/amd64,linux/arm64 ...

# 问题2: 推送权限不足
Error: unauthorized: authentication required

# 解决方案: 重新登录
docker logout
docker login
```

### 2. 发布验证

#### 验证检查清单
```bash
# ✅ 镜像存在且可拉取
docker pull your-username/server-manager:latest

# ✅ 多架构支持
docker buildx imagetools inspect your-username/server-manager:latest

# ✅ 标签正确
docker images | grep server-manager

# ✅ 容器正常启动
docker run --rm your-username/server-manager:latest --help

# ✅ 健康检查通过
docker run -d --name test-sm your-username/server-manager:latest
sleep 30
docker exec test-sm curl -f http://localhost:8000/health
docker rm -f test-sm
```

## 发布清单

### 发布前检查
- [ ] 代码质量检查通过
- [ ] 单元测试通过
- [ ] 安全扫描无高危漏洞
- [ ] 文档更新完成
- [ ] 版本号正确
- [ ] Change Log 更新

### 发布流程
- [ ] 创建 Git 标签
- [ ] 自动构建触发
- [ ] 多架构镜像构建成功
- [ ] 镜像推送到 Docker Hub
- [ ] 发布验证通过
- [ ] 文档仓库更新

### 发布后验证
- [ ] Docker Hub 页面信息正确
- [ ] 镜像可正常拉取
- [ ] 容器启动正常
- [ ] 功能测试通过
- [ ] 用户反馈收集

## 联系方式

如有发布相关问题，请：

1. 查看 [GitHub Issues](https://github.com/your-username/server-manager/issues)
2. 提交新的 Issue
3. 发送邮件至维护者

---

**注意**: 请将文档中的 `your-username` 替换为您的实际 Docker Hub 用户名。