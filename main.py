#!/usr/bin/env python3
"""
服务器管理系统主程序入口
支持WOL和定时任务管理的Web应用
"""

import os
import sys
import asyncio
import logging
import argparse
from pathlib import Path

import uvicorn

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.api import create_app


def setup_logging(log_level: str = "INFO", log_file: str = None):
    """配置日志系统"""
    # 创建logs目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 配置日志格式
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 设置日志级别
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # 配置根日志器
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[
            # 控制台输出
            logging.StreamHandler(sys.stdout),
            # 文件输出
            logging.FileHandler(
                log_file or log_dir / "server_manager.log",
                encoding='utf-8'
            )
        ]
    )
    
    # 设置特定库的日志级别
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="服务器管理系统 - WOL和定时任务管理",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s                          # 使用默认配置启动
  %(prog)s --host 0.0.0.0 --port 8080  # 指定监听地址和端口
  %(prog)s --data-dir ./my_data     # 指定数据目录
  %(prog)s --log-level DEBUG        # 启用调试日志
        """
    )
    
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="服务器监听地址 (默认: 127.0.0.1)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="服务器监听端口 (默认: 8000)"
    )
    
    parser.add_argument(
        "--data-dir",
        default="data",
        help="数据存储目录 (默认: data)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志级别 (默认: INFO)"
    )
    
    parser.add_argument(
        "--log-file",
        help="日志文件路径 (默认: logs/server_manager.log)"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="启用代码热重载 (开发模式)"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="工作进程数量 (默认: 1)"
    )
    
    return parser.parse_args()


def check_requirements():
    """检查运行环境和依赖"""
    try:
        import yaml
        import fastapi
        import uvicorn
        import tinydb
        import wakeonlan
        import apscheduler
        import psutil
    except ImportError as e:
        print(f"错误: 缺少必要的依赖包 {e.name}")
        print("请运行以下命令安装依赖:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("错误: 需要Python 3.7或更高版本")
        sys.exit(1)


def create_directories(data_dir: str):
    """创建必要的目录结构"""
    directories = [
        data_dir,
        "logs",
        "static/js",
        "static/css",
        "templates"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 检查运行环境
    check_requirements()
    
    # 创建必要目录
    create_directories(args.data_dir)
    
    # 配置日志
    setup_logging(args.log_level, args.log_file)
    logger = logging.getLogger(__name__)
    
    logger.info("="*60)
    logger.info("服务器管理系统启动")
    logger.info("="*60)
    logger.info(f"监听地址: {args.host}:{args.port}")
    logger.info(f"数据目录: {args.data_dir}")
    logger.info(f"日志级别: {args.log_level}")
    logger.info(f"工作进程: {args.workers}")
    
    # 创建FastAPI应用
    app = create_app(args.data_dir)
    
    # 配置uvicorn参数
    uvicorn_config = {
        "host": args.host,
        "port": args.port,
        "log_level": args.log_level.lower(),
        "access_log": True,
        "workers": args.workers if not args.reload else 1,
        "reload": args.reload,
        "app": app
    }
    
    if args.reload:
        logger.info("开发模式: 启用代码热重载")
        uvicorn_config["reload_dirs"] = ["."]
        uvicorn_config["reload_excludes"] = ["data", "logs", "*.yaml", "*.log"]
    
    # 启动服务器
    try:
        logger.info("启动Web服务器...")
        logger.info(f"访问地址: http://{args.host}:{args.port}")
        
        # 使用uvicorn运行服务器
        uvicorn.run(**uvicorn_config)
        
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务器...")
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        sys.exit(1)
    finally:
        logger.info("服务器已关闭")


if __name__ == "__main__":
    main()