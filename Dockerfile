# 使用Python 3.10作为基础镜像
FROM python:3.10-slim

# 构建参数
ARG BUILDTIME
ARG VERSION
ARG REVISION

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 添加镜像标签
LABEL org.opencontainers.image.title="Server Manager" \
      org.opencontainers.image.description="基于FastAPI的Web应用，提供局域网唤醒(WOL)和定时任务管理功能" \
      org.opencontainers.image.created="${BUILDTIME}" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${REVISION}" \
      org.opencontainers.image.vendor="Claude AI Assistant" \
      org.opencontainers.image.licenses="MIT" \
      maintainer="Claude AI Assistant"

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    iputils-ping \
    rsync \
    openssh-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p data logs static templates

# 暴露端口
EXPOSE 8000

# 设置健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/status || exit 1

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

USER app

# 启动命令
CMD ["python", "main.py", "--host", "0.0.0.0", "--port", "8000"]