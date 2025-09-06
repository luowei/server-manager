# 部署指南

## 部署方式概览

本项目支持多种部署方式，适用于不同的使用场景：

1. **Docker容器化部署** (推荐) - 适合生产环境
2. **直接运行部署** - 适合开发和测试环境
3. **Docker Compose部署** - 适合复杂配置需求
4. **容器编排部署** - 适合大规模部署

## Docker容器化部署

### 1. 基础Docker部署

#### 构建镜像
```bash
# 从源代码构建
git clone <项目地址>
cd server_manager
docker build -t server-manager:latest .

# 或使用预构建镜像 (如果已发布到Docker Hub)
docker pull your-username/server-manager:latest
```

#### 运行容器

**推荐配置 (host网络支持WOL)**:
```bash
docker run -d \
  --name server-manager \
  --restart unless-stopped \
  --network host \
  --cap-add NET_RAW \
  -e SM_PORT=8000 \
  -e SM_LOG_LEVEL=INFO \
  -e TZ=Asia/Shanghai \
  -v server-manager-data:/app/data \
  -v server-manager-logs:/app/logs \
  server-manager:latest
```

**标准端口映射配置**:
```bash
docker run -d \
  --name server-manager \
  --restart unless-stopped \
  -p 8000:8000 \
  -e SM_PORT=8000 \
  -e SM_LOG_LEVEL=INFO \
  -e TZ=Asia/Shanghai \
  -v server-manager-data:/app/data \
  -v server-manager-logs:/app/logs \
  server-manager:latest
```

### 2. 环境变量配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `SM_PORT` | `8000` | Web服务监听端口 |
| `SM_HOST` | `0.0.0.0` | 服务监听地址 |
| `SM_LOG_LEVEL` | `INFO` | 日志级别 (DEBUG/INFO/WARNING/ERROR) |
| `SM_ENV` | `production` | 运行环境 |
| `TZ` | `UTC` | 时区设置 |
| `SM_TIMEZONE` | `Asia/Shanghai` | 应用时区 |
| `SM_WOL_PORT` | `9` | WOL广播端口 |
| `SM_WOL_TIMEOUT` | `3` | WOL超时时间(秒) |
| `SM_TASK_TIMEOUT` | `300` | 任务默认超时时间(秒) |
| `SM_TASK_MAX_RETRIES` | `0` | 任务默认最大重试次数 |
| `SM_LOG_RETENTION_DAYS` | `30` | 日志保留天数 |

### 3. 数据卷管理

```bash
# 创建命名卷
docker volume create server-manager-data
docker volume create server-manager-logs

# 查看卷信息
docker volume inspect server-manager-data

# 备份数据卷
docker run --rm \
  -v server-manager-data:/source:ro \
  -v $(pwd):/backup \
  alpine tar czf /backup/backup.tar.gz -C /source .

# 恢复数据卷
docker run --rm \
  -v server-manager-data:/target \
  -v $(pwd):/backup \
  alpine tar xzf /backup/backup.tar.gz -C /target
```

## Docker Compose部署

### 1. 创建docker-compose.yml

```yaml
version: '3.8'

services:
  server-manager:
    build: .
    # 或使用预构建镜像
    # image: your-username/server-manager:latest
    container_name: server-manager
    restart: unless-stopped
    
    # 推荐使用host网络以支持WOL
    network_mode: host
    cap_add:
      - NET_RAW
    
    # 或使用端口映射
    # ports:
    #   - "8000:8000"
    
    environment:
      - SM_PORT=8000
      - SM_LOG_LEVEL=INFO
      - SM_ENV=production
      - TZ=Asia/Shanghai
      - SM_TIMEZONE=Asia/Shanghai
      - SM_WOL_PORT=9
      - SM_WOL_TIMEOUT=3
      - SM_TASK_TIMEOUT=300
      - SM_LOG_RETENTION_DAYS=30
    
    volumes:
      - server-manager-data:/app/data
      - server-manager-logs:/app/logs
      # 可选: 挂载配置文件
      # - ./config:/app/config:ro
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  server-manager-data:
    driver: local
  server-manager-logs:
    driver: local

# 可选: 如果需要特定网络配置
# networks:
#   server-manager-net:
#     driver: bridge
```

### 2. 环境变量文件

创建 `.env` 文件:
```bash
# 服务配置
SM_PORT=8000
SM_HOST=0.0.0.0
SM_LOG_LEVEL=INFO
SM_ENV=production

# 时区配置
TZ=Asia/Shanghai
SM_TIMEZONE=Asia/Shanghai

# WOL配置
SM_WOL_PORT=9
SM_WOL_TIMEOUT=3

# 任务配置
SM_TASK_TIMEOUT=300
SM_TASK_MAX_RETRIES=0
SM_LOG_RETENTION_DAYS=30

# 数据库配置 (预留)
# SM_DATA_DIR=/app/data
# SM_BACKUP_ENABLED=true
# SM_BACKUP_INTERVAL=24h
```

### 3. 运行和管理

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 更新镜像并重启
docker-compose pull
docker-compose up -d --force-recreate
```

## 直接运行部署

### 1. 系统要求

- Python 3.7+
- pip包管理器
- 足够的网络权限发送WOL包

### 2. 安装部署

```bash
# 克隆代码
git clone <项目地址>
cd server_manager

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 运行应用
python main.py --host 0.0.0.0 --port 8000
```

### 3. 系统服务配置

#### Linux (systemd)

创建服务文件 `/etc/systemd/system/server-manager.service`:
```ini
[Unit]
Description=Server Manager
After=network.target

[Service]
Type=simple
User=server-manager
Group=server-manager
WorkingDirectory=/opt/server-manager
Environment=PATH=/opt/server-manager/venv/bin
ExecStart=/opt/server-manager/venv/bin/python main.py --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

# 安全配置
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/opt/server-manager/data /opt/server-manager/logs

[Install]
WantedBy=multi-user.target
```

启用服务:
```bash
sudo systemctl daemon-reload
sudo systemctl enable server-manager
sudo systemctl start server-manager
sudo systemctl status server-manager
```

#### Windows (NSSM)

```cmd
# 下载并安装 NSSM
nssm install "Server Manager" "C:\server-manager\venv\Scripts\python.exe" "main.py --host 0.0.0.0 --port 8000"
nssm set "Server Manager" AppDirectory "C:\server-manager"
nssm start "Server Manager"
```

### 4. 反向代理配置

#### Nginx配置
```nginx
upstream server_manager {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL配置
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    # 安全headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    location / {
        proxy_pass http://server_manager;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持 (预留)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # 静态文件缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        proxy_pass http://server_manager;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## 容器编排部署

### 1. Kubernetes部署

#### Deployment配置
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: server-manager
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: server-manager
  template:
    metadata:
      labels:
        app: server-manager
    spec:
      containers:
      - name: server-manager
        image: your-username/server-manager:latest
        ports:
        - containerPort: 8000
        env:
        - name: SM_PORT
          value: "8000"
        - name: SM_LOG_LEVEL
          value: "INFO"
        - name: TZ
          value: "Asia/Shanghai"
        volumeMounts:
        - name: data-volume
          mountPath: /app/data
        - name: logs-volume
          mountPath: /app/logs
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: data-volume
        persistentVolumeClaim:
          claimName: server-manager-data-pvc
      - name: logs-volume
        persistentVolumeClaim:
          claimName: server-manager-logs-pvc
```

#### Service配置
```yaml
apiVersion: v1
kind: Service
metadata:
  name: server-manager-service
spec:
  selector:
    app: server-manager
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

#### PVC配置
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: server-manager-data-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: server-manager-logs-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

## 安全配置

### 1. 防火墙配置

#### iptables规则
```bash
# 允许Web服务端口
iptables -A INPUT -p tcp --dport 8000 -j ACCEPT

# 允许WOL端口 (UDP 9)
iptables -A OUTPUT -p udp --dport 9 -j ACCEPT

# 保存规则
iptables-save > /etc/iptables/rules.v4
```

#### ufw (Ubuntu)
```bash
# 启用防火墙
ufw enable

# 允许SSH
ufw allow ssh

# 允许Web服务
ufw allow 8000/tcp

# 允许WOL
ufw allow out 9/udp
```

### 2. SSL/TLS配置

#### 自签名证书 (测试用)
```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

#### Let's Encrypt (生产用)
```bash
# 安装certbot
sudo apt-get install certbot

# 获取证书
sudo certbot certonly --standalone -d your-domain.com

# 自动续期
sudo crontab -e
# 添加: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 监控和日志

### 1. 健康检查

```bash
# HTTP健康检查
curl -f http://localhost:8000/health || exit 1

# Docker健康检查
docker run --rm \
  --network container:server-manager \
  curlimages/curl:latest \
  curl -f http://localhost:8000/health
```

### 2. 日志管理

#### 日志轮转配置
```bash
# /etc/logrotate.d/server-manager
/opt/server-manager/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 server-manager server-manager
    postrotate
        systemctl reload server-manager
    endscript
}
```

#### 日志聚合 (ELK Stack)
```yaml
# filebeat.yml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/lib/docker/volumes/server-manager-logs/_data/*.log
  fields:
    service: server-manager
  fields_under_root: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]

setup.kibana:
  host: "kibana:5601"
```

## 备份和恢复

### 1. 数据备份

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/server-manager"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 备份Docker卷
docker run --rm \
  -v server-manager-data:/source:ro \
  -v "$BACKUP_DIR":/backup \
  alpine tar czf "/backup/data_$DATE.tar.gz" -C /source .

docker run --rm \
  -v server-manager-logs:/source:ro \
  -v "$BACKUP_DIR":/backup \
  alpine tar czf "/backup/logs_$DATE.tar.gz" -C /source .

# 清理旧备份 (保留7天)
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete

echo "备份完成: $BACKUP_DIR"
```

### 2. 自动备份

```bash
# crontab -e
# 每天凌晨2点备份
0 2 * * * /opt/server-manager/scripts/backup.sh
```

## 故障排除

### 1. 常见问题

1. **WOL功能不工作**:
   - 检查网络模式是否为host
   - 确认容器有NET_RAW权限
   - 验证目标设备支持WOL

2. **任务执行失败**:
   - 检查命令路径和权限
   - 验证超时设置
   - 查看执行日志

3. **无法访问Web界面**:
   - 检查端口映射
   - 验证防火墙规则
   - 确认服务状态

### 2. 调试命令

```bash
# 查看容器日志
docker logs -f server-manager

# 进入容器调试
docker exec -it server-manager /bin/bash

# 检查进程状态
docker exec server-manager ps aux

# 检查网络连接
docker exec server-manager netstat -tlnp

# 测试API接口
curl -v http://localhost:8000/api/status
```