# 故障排查指南

## 常见问题诊断

### 1. WOL功能问题

#### 问题：WOL包发送后设备无法唤醒

**可能原因**：
1. 目标设备未开启WOL功能
2. 网络配置问题
3. MAC地址错误
4. 容器网络权限不足

**排查步骤**：

1. **验证设备WOL支持**：
```bash
# 在目标设备上检查网卡WOL设置
ethtool eth0 | grep "Wake-on"
# 应该显示: Wake-on: g (支持魔术包)

# 启用WOL (如果未启用)
sudo ethtool -s eth0 wol g
```

2. **验证MAC地址**：
```bash
# 获取正确的MAC地址
ip link show eth0
# 或
cat /sys/class/net/eth0/address
```

3. **检查Docker网络配置**：
```bash
# 确认使用host网络模式
docker inspect server-manager | grep NetworkMode

# 确认容器有NET_RAW权限
docker inspect server-manager | grep CapAdd
```

4. **手动测试WOL包**：
```bash
# 在主机上测试WOL
wakeonlan 00:11:22:33:44:55

# 或使用Python脚本测试
python3 -c "
import socket
mac = '00:11:22:33:44:55'
data = b'\xff' * 6 + bytes.fromhex(mac.replace(':', '')) * 16
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.sendto(data, ('255.255.255.255', 9))
sock.close()
print('WOL packet sent')
"
```

#### 问题：WOL包发送成功但API返回错误

**排查步骤**：

1. **检查API日志**：
```bash
docker logs server-manager | grep -i wol
```

2. **验证设备存在**：
```bash
curl -X GET http://localhost:8000/api/devices/{device_id}
```

3. **检查网络权限**：
```bash
# 容器内测试网络权限
docker exec -it server-manager python -c "
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
print('Network permissions OK')
"
```

### 2. 任务执行问题

#### 问题：任务创建成功但不执行

**可能原因**：
1. 调度器未启动
2. Cron表达式错误
3. 任务被禁用
4. 系统时区问题

**排查步骤**：

1. **检查调度器状态**：
```bash
curl http://localhost:8000/api/status | jq '.scheduler'
```

2. **验证Cron表达式**：
```bash
# 使用在线工具或Python验证
python3 -c "
from apscheduler.triggers.cron import CronTrigger
trigger = CronTrigger.from_crontab('0 */5 * * *')  # 每5分钟
print('Cron expression is valid')
"
```

3. **检查任务状态**：
```bash
curl http://localhost:8000/api/tasks/{task_id} | jq '.enabled'
```

4. **验证时区设置**：
```bash
# 容器内时区
docker exec server-manager date
docker exec server-manager cat /etc/timezone

# 比较系统时区
date
```

#### 问题：任务执行超时或失败

**排查步骤**：

1. **查看执行日志**：
```bash
curl http://localhost:8000/api/tasks/{task_id}/executions | jq '.[0]'
```

2. **手动测试命令**：
```bash
# 进入容器手动执行
docker exec -it server-manager /bin/bash
cd /app
bash -c "your_command_here"
```

3. **检查资源限制**：
```bash
# 容器资源使用
docker stats server-manager

# 系统资源
docker exec server-manager df -h
docker exec server-manager free -m
```

4. **调整超时设置**：
```bash
# 增加任务超时时间
curl -X PUT http://localhost:8000/api/tasks/{task_id} \
  -H "Content-Type: application/json" \
  -d '{"timeout_seconds": 600}'
```

### 3. Web界面问题

#### 问题：无法访问Web界面

**排查步骤**：

1. **检查服务状态**：
```bash
# 容器是否运行
docker ps | grep server-manager

# 服务是否监听
docker exec server-manager netstat -tlnp | grep 8000
```

2. **检查端口映射**：
```bash
docker port server-manager
```

3. **测试API接口**：
```bash
# 本地测试
curl -v http://localhost:8000/health

# 远程测试
curl -v http://your-server-ip:8000/health
```

4. **检查防火墙**：
```bash
# Ubuntu/Debian
sudo ufw status

# CentOS/RHEL
sudo firewall-cmd --list-all

# 检查iptables
sudo iptables -L -n | grep 8000
```

#### 问题：JavaScript错误

**排查步骤**：

1. **浏览器开发者工具**：
   - 按F12打开开发者工具
   - 查看Console标签页的错误信息
   - 检查Network标签页的请求状态

2. **检查静态文件**：
```bash
# 验证静态文件存在
docker exec server-manager ls -la /app/static/

# 测试静态文件访问
curl http://localhost:8000/static/js/dashboard.js
```

3. **CSP策略问题**：
   - 查看浏览器Console的CSP错误
   - 临时禁用CSP进行测试

### 4. 数据存储问题

#### 问题：数据丢失或损坏

**排查步骤**：

1. **检查数据文件**：
```bash
# 查看数据文件
docker exec server-manager ls -la /app/data/
docker exec server-manager cat /app/data/devices.yaml
```

2. **验证YAML格式**：
```bash
# 使用Python验证YAML
docker exec server-manager python -c "
import yaml
with open('/app/data/devices.yaml', 'r') as f:
    data = yaml.safe_load(f)
print('YAML format is valid')
print(f'Records: {len(data.get(\"_default\", {}))}')
"
```

3. **恢复备份**：
```bash
# 从备份恢复数据
docker run --rm \
  -v server-manager-data:/target \
  -v /path/to/backup:/backup \
  alpine tar xzf /backup/data_backup.tar.gz -C /target
```

#### 问题：数据文件权限错误

**排查步骤**：

1. **检查文件权限**：
```bash
docker exec server-manager ls -la /app/data/
```

2. **修复权限**：
```bash
docker exec server-manager chown -R app:app /app/data/
docker exec server-manager chmod -R 644 /app/data/*.yaml
```

### 5. 性能问题

#### 问题：响应速度慢

**排查步骤**：

1. **检查资源使用**：
```bash
# 容器资源监控
docker stats server-manager

# 详细资源信息
docker exec server-manager cat /proc/meminfo
docker exec server-manager cat /proc/cpuinfo
```

2. **分析慢查询**：
```bash
# 启用DEBUG日志
docker exec server-manager python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
"

# 查看详细日志
docker logs server-manager | tail -100
```

3. **优化建议**：
   - 增加容器内存限制
   - 使用SSD存储数据卷
   - 定期清理执行记录

#### 问题：内存泄漏

**监控命令**：
```bash
# 持续监控内存使用
watch docker stats server-manager

# 内存使用趋势
docker exec server-manager cat /proc/{PID}/status | grep VmRSS
```

## 调试工具和技巧

### 1. 日志分析

#### 实时日志监控
```bash
# 实时查看所有日志
docker logs -f server-manager

# 过滤特定类型的日志
docker logs server-manager 2>&1 | grep ERROR
docker logs server-manager 2>&1 | grep "task_id"

# 日志级别过滤
docker logs server-manager 2>&1 | grep -E "(ERROR|WARNING)"
```

#### 日志格式化
```bash
# 使用jq格式化JSON日志
docker logs server-manager 2>&1 | grep "^{" | jq '.'

# 提取特定字段
docker logs server-manager 2>&1 | grep "task execution" | jq '.task_id, .status'
```

### 2. API调试

#### 健康检查脚本
```bash
#!/bin/bash
# health_check.sh

BASE_URL="http://localhost:8000"

echo "=== System Health Check ==="

# 基础健康检查
echo -n "Health endpoint: "
curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health"
echo

# API端点测试
echo -n "Devices API: "
curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/devices"
echo

echo -n "Tasks API: "
curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/tasks"
echo

echo -n "Status API: "
curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/status"
echo

# 响应时间测试
echo "=== Response Time Test ==="
curl -w "Time: %{time_total}s\n" -o /dev/null -s "$BASE_URL/api/status"
```

#### API测试脚本
```python
#!/usr/bin/env python3
# api_test.py

import requests
import json
import time

BASE_URL = "http://localhost:8000/api"

def test_api():
    # 测试设备API
    print("Testing Devices API...")
    response = requests.get(f"{BASE_URL}/devices")
    print(f"GET /devices: {response.status_code}")
    
    # 测试任务API
    print("Testing Tasks API...")
    response = requests.get(f"{BASE_URL}/tasks")
    print(f"GET /tasks: {response.status_code}")
    
    # 测试状态API
    print("Testing Status API...")
    start_time = time.time()
    response = requests.get(f"{BASE_URL}/status")
    end_time = time.time()
    print(f"GET /status: {response.status_code} ({end_time - start_time:.3f}s)")
    
    if response.status_code == 200:
        status = response.json()
        print(f"Server uptime: {status['server']['uptime']}")
        print(f"CPU usage: {status['system']['cpu_usage']}%")
        print(f"Memory usage: {status['system']['memory']['percent']}%")

if __name__ == "__main__":
    test_api()
```

### 3. 容器调试

#### 进入容器调试
```bash
# 进入运行中的容器
docker exec -it server-manager /bin/bash

# 如果bash不可用，尝试sh
docker exec -it server-manager /bin/sh

# 以root用户进入
docker exec -u root -it server-manager /bin/bash
```

#### 容器状态检查
```bash
# 容器详细信息
docker inspect server-manager

# 容器进程
docker exec server-manager ps aux

# 网络配置
docker exec server-manager ip addr show
docker exec server-manager netstat -tlnp

# 文件系统
docker exec server-manager df -h
docker exec server-manager mount
```

### 4. 性能监控

#### 资源监控脚本
```bash
#!/bin/bash
# monitor.sh

CONTAINER_NAME="server-manager"
LOG_FILE="/tmp/server-manager-monitor.log"

while true; do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    stats=$(docker stats --no-stream --format "table {{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" $CONTAINER_NAME | tail -n 1)
    echo "$timestamp $stats" >> $LOG_FILE
    sleep 60
done
```

#### 数据库性能监控
```python
#!/usr/bin/env python3
# db_monitor.py

import time
import yaml
import os

DATA_DIR = "/app/data"

def monitor_db_performance():
    while True:
        stats = {}
        
        for filename in os.listdir(DATA_DIR):
            if filename.endswith('.yaml'):
                filepath = os.path.join(DATA_DIR, filename)
                file_size = os.path.getsize(filepath)
                
                with open(filepath, 'r') as f:
                    data = yaml.safe_load(f)
                    record_count = len(data.get('_default', {}))
                
                stats[filename] = {
                    'size': file_size,
                    'records': record_count
                }
        
        print(f"DB Stats: {stats}")
        time.sleep(300)  # 5分钟检查一次

if __name__ == "__main__":
    monitor_db_performance()
```

## 紧急恢复程序

### 1. 服务恢复

```bash
#!/bin/bash
# emergency_recovery.sh

echo "=== Emergency Recovery Procedure ==="

# 1. 停止当前容器
echo "Stopping current container..."
docker stop server-manager
docker rm server-manager

# 2. 备份当前数据
echo "Backing up current data..."
docker run --rm \
  -v server-manager-data:/source:ro \
  -v $(pwd):/backup \
  alpine tar czf /backup/emergency_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /source .

# 3. 重新启动服务
echo "Restarting service..."
docker run -d \
  --name server-manager \
  --restart unless-stopped \
  --network host \
  --cap-add NET_RAW \
  -e SM_PORT=8000 \
  -e TZ=Asia/Shanghai \
  -v server-manager-data:/app/data \
  -v server-manager-logs:/app/logs \
  server-manager:latest

# 4. 验证服务状态
echo "Verifying service status..."
sleep 10
curl -f http://localhost:8000/health && echo "Service recovered successfully" || echo "Recovery failed"
```

### 2. 数据恢复

```bash
#!/bin/bash
# data_recovery.sh

BACKUP_FILE=$1
if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    exit 1
fi

echo "=== Data Recovery Procedure ==="

# 1. 停止服务
docker stop server-manager

# 2. 备份当前数据
docker run --rm \
  -v server-manager-data:/source:ro \
  -v $(pwd):/backup \
  alpine tar czf /backup/pre_recovery_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /source .

# 3. 清空数据卷
docker run --rm \
  -v server-manager-data:/target \
  alpine rm -rf /target/*

# 4. 恢复数据
docker run --rm \
  -v server-manager-data:/target \
  -v $(pwd):/backup \
  alpine tar xzf /backup/$BACKUP_FILE -C /target

# 5. 重启服务
docker start server-manager

echo "Data recovery completed"
```

## 联系支持

如果以上排查步骤无法解决问题，请收集以下信息：

1. **系统环境**：
   - 操作系统版本
   - Docker版本
   - 容器运行配置

2. **错误信息**：
   - 完整的错误日志
   - 浏览器Console错误
   - API响应信息

3. **复现步骤**：
   - 问题出现的具体操作
   - 期望结果和实际结果
   - 问题出现频率

4. **配置信息**：
   - 环境变量设置
   - 网络配置
   - 数据卷配置