from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Optional, Dict, Any
import os
import logging
from datetime import datetime

from .models import (
    WOLDevice, ScheduledTask, TaskExecution, WOLRequest,
    TaskCreateRequest, TaskUpdateRequest, ApiResponse,
    TaskStatus, TaskType
)
from .database import DatabaseManager
from .scheduler import TaskScheduler
from .wol import WOLManager

logger = logging.getLogger(__name__)


class ServerManagerAPI:
    """服务器管理API"""
    
    def __init__(self, data_dir: str = "data"):
        self.app = FastAPI(
            title="Server Manager",
            description="局域网唤醒和任务调度管理系统",
            version="1.0.0"
        )
        
        # 初始化组件
        self.db_manager = DatabaseManager(data_dir)
        self.scheduler = TaskScheduler(self.db_manager)
        self.wol_manager = WOLManager()
        
        # 配置静态文件和模板
        if os.path.exists("static"):
            self.app.mount("/static", StaticFiles(directory="static"), name="static")
        
        if os.path.exists("templates"):
            self.templates = Jinja2Templates(directory="templates")
        else:
            self.templates = None
        
        # 注册路由
        self._register_routes()
        
        # 启动事件
        @self.app.on_event("startup")
        async def startup_event():
            await self.scheduler.start()
            logger.info("Server Manager API 启动完成")
        
        # 关闭事件
        @self.app.on_event("shutdown")
        async def shutdown_event():
            await self.scheduler.stop()
            self.db_manager.close()
            logger.info("Server Manager API 关闭完成")
    
    
    def _register_routes(self):
        """注册所有路由"""
        
        # 前端页面路由
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard(request: Request):
            if self.templates:
                return self.templates.TemplateResponse("dashboard.html", {"request": request})
            return HTMLResponse("<h1>Server Manager Dashboard</h1><p>请配置模板目录</p>")
        
        # WOL设备管理API
        @self.app.post("/api/devices", response_model=ApiResponse)
        async def create_device(device_data: WOLDevice):
            try:
                device = self.db_manager.create_device(device_data)
                return ApiResponse(success=True, message="设备创建成功", data=device.dict())
            except Exception as e:
                logger.error(f"创建设备失败: {e}")
                return ApiResponse(success=False, message=str(e))
        
        @self.app.get("/api/devices", response_model=ApiResponse)
        async def get_all_devices():
            try:
                devices = self.db_manager.get_all_devices()
                # 为每个设备添加优化的显示地址
                device_data = []
                for device in devices:
                    device_dict = device.dict()
                    # 添加优化的显示地址字段
                    device_dict['display_address'] = device.get_display_address()
                    device_dict['is_mdns'] = device.is_mdns_hostname()
                    device_data.append(device_dict)
                
                return ApiResponse(
                    success=True, 
                    message="获取设备列表成功", 
                    data=device_data
                )
            except Exception as e:
                logger.error(f"获取设备列表失败: {e}")
                return ApiResponse(success=False, message=str(e))
        
        @self.app.get("/api/devices/{device_id}", response_model=ApiResponse)
        async def get_device(device_id: int):
            try:
                device = self.db_manager.get_device(device_id)
                if not device:
                    return ApiResponse(success=False, message="设备不存在")
                return ApiResponse(success=True, message="获取设备成功", data=device.dict())
            except Exception as e:
                logger.error(f"获取设备失败: {e}")
                return ApiResponse(success=False, message=str(e))
        
        @self.app.put("/api/devices/{device_id}", response_model=ApiResponse)
        async def update_device(device_id: int, device_data: WOLDevice):
            try:
                updates = device_data.dict(exclude_unset=True, exclude={'id', 'created_at'})
                if self.db_manager.update_device(device_id, updates):
                    return ApiResponse(success=True, message="设备更新成功")
                return ApiResponse(success=False, message="设备不存在")
            except Exception as e:
                logger.error(f"更新设备失败: {e}")
                return ApiResponse(success=False, message=str(e))
        
        @self.app.delete("/api/devices/{device_id}", response_model=ApiResponse)
        async def delete_device(device_id: int):
            try:
                if self.db_manager.delete_device(device_id):
                    return ApiResponse(success=True, message="设备删除成功")
                return ApiResponse(success=False, message="设备不存在")
            except Exception as e:
                logger.error(f"删除设备失败: {e}")
                return ApiResponse(success=False, message=str(e))
        
        # WOL唤醒API
        @self.app.post("/api/wol/wake", response_model=ApiResponse)
        async def wake_device(wol_request: WOLRequest):
            try:
                # 获取设备信息
                if wol_request.device_id:
                    device = self.db_manager.get_device(wol_request.device_id)
                    if not device:
                        return ApiResponse(success=False, message="设备不存在")
                    mac_address = device.mac_address
                    ip_address = wol_request.ip_address or device.ip_address
                else:
                    if not wol_request.mac_address:
                        return ApiResponse(success=False, message="必须提供设备ID或MAC地址")
                    mac_address = wol_request.mac_address
                    ip_address = wol_request.ip_address
                
                # 发送WOL包
                success = self.wol_manager.send_wol_packet(
                    mac_address, 
                    ip_address, 
                    wol_request.port
                )
                
                if success:
                    return ApiResponse(success=True, message="WOL包发送成功")
                else:
                    return ApiResponse(success=False, message="WOL包发送失败")
                    
            except Exception as e:
                logger.error(f"唤醒设备失败: {e}")
                return ApiResponse(success=False, message=str(e))
        
        @self.app.post("/api/wol/ping/{device_id}", response_model=ApiResponse)
        async def ping_device(device_id: int):
            try:
                device = self.db_manager.get_device(device_id)
                if not device:
                    return ApiResponse(success=False, message="设备不存在")
                
                # 按优先级确定ping目标：mDNS主机名 -> 普通主机名 -> IP地址/CIDR
                target = None
                
                # 优先使用主机名（包括mDNS）
                if device.hostname:
                    target = device.hostname
                # 如果没有主机名，使用IP地址
                elif device.ip_address:
                    # 如果是CIDR格式，提取IP地址部分
                    if '/' in device.ip_address:
                        target = device.ip_address.split('/')[0]
                    else:
                        target = device.ip_address
                
                if not target:
                    return ApiResponse(success=False, message="设备无主机名或IP地址")
                
                is_online = self.wol_manager.ping_host(target)
                return ApiResponse(
                    success=True, 
                    message="Ping完成", 
                    data={"online": is_online, "target": target}
                )
                
            except Exception as e:
                logger.error(f"Ping设备失败: {e}")
                return ApiResponse(success=False, message=str(e))
        
        # 定时任务管理API
        @self.app.post("/api/tasks", response_model=ApiResponse)
        async def create_task(request: Request):
            try:
                # 先获取原始请求数据进行调试
                request_body = await request.body()
                logger.info(f"创建任务请求数据: {request_body.decode()}")
                
                # 解析为TaskCreateRequest模型
                import json
                from pydantic import ValidationError
                try:
                    raw_data = json.loads(request_body.decode())
                    task_data = TaskCreateRequest(**raw_data)
                    logger.info(f"解析后的任务数据: {task_data.dict()}")
                except ValidationError as ve:
                    logger.error(f"任务数据验证失败: {ve}")
                    return ApiResponse(success=False, message=f"数据验证失败: {ve}")
                
                task = ScheduledTask(**task_data.dict())
                task = self.db_manager.create_task(task)
                
                # 如果任务启用，添加到调度器
                if task.enabled:
                    await self.scheduler.schedule_task(task)
                
                return ApiResponse(success=True, message="任务创建成功", data=task.dict())
            except Exception as e:
                logger.error(f"创建任务失败: {e}")
                return ApiResponse(success=False, message=str(e))
        
        @self.app.get("/api/tasks", response_model=ApiResponse)
        async def get_all_tasks():
            try:
                tasks = self.db_manager.get_all_tasks()
                return ApiResponse(
                    success=True, 
                    message="获取任务列表成功", 
                    data=[task.dict() for task in tasks]
                )
            except Exception as e:
                logger.error(f"获取任务列表失败: {e}")
                return ApiResponse(success=False, message=str(e))
        
        @self.app.get("/api/tasks/{task_id}", response_model=ApiResponse)
        async def get_task(task_id: int):
            try:
                task = self.db_manager.get_task(task_id)
                if not task:
                    return ApiResponse(success=False, message="任务不存在")
                return ApiResponse(success=True, message="获取任务成功", data=task.dict())
            except Exception as e:
                logger.error(f"获取任务失败: {e}")
                return ApiResponse(success=False, message=str(e))
        
        @self.app.put("/api/tasks/{task_id}", response_model=ApiResponse)
        async def update_task(task_id: int, task_data: TaskUpdateRequest):
            try:
                updates = task_data.dict(exclude_unset=True)
                if self.db_manager.update_task(task_id, updates):
                    # 重新调度任务
                    task = self.db_manager.get_task(task_id)
                    if task:
                        await self.scheduler.unschedule_task(task_id)
                        if task.enabled:
                            await self.scheduler.schedule_task(task)
                    
                    return ApiResponse(success=True, message="任务更新成功")
                return ApiResponse(success=False, message="任务不存在")
            except Exception as e:
                logger.error(f"更新任务失败: {e}")
                return ApiResponse(success=False, message=str(e))
        
        @self.app.delete("/api/tasks/{task_id}", response_model=ApiResponse)
        async def delete_task(task_id: int):
            try:
                # 先取消调度
                await self.scheduler.unschedule_task(task_id)
                
                if self.db_manager.delete_task(task_id):
                    return ApiResponse(success=True, message="任务删除成功")
                return ApiResponse(success=False, message="任务不存在")
            except Exception as e:
                logger.error(f"删除任务失败: {e}")
                return ApiResponse(success=False, message=str(e))
        
        @self.app.post("/api/tasks/{task_id}/execute", response_model=ApiResponse)
        async def execute_task_now(task_id: int, background_tasks: BackgroundTasks):
            try:
                task = self.db_manager.get_task(task_id)
                if not task:
                    return ApiResponse(success=False, message="任务不存在")
                
                # 在后台执行任务
                background_tasks.add_task(self.scheduler.execute_task_now, task_id)
                return ApiResponse(success=True, message="任务已开始执行")
                
            except Exception as e:
                logger.error(f"执行任务失败: {e}")
                return ApiResponse(success=False, message=str(e))
        
        @self.app.post("/api/tasks/{task_id}/toggle", response_model=ApiResponse)
        async def toggle_task(task_id: int):
            try:
                task = self.db_manager.get_task(task_id)
                if not task:
                    return ApiResponse(success=False, message="任务不存在")
                
                new_status = not task.enabled
                self.db_manager.update_task(task_id, {'enabled': new_status})
                
                # 更新调度
                await self.scheduler.unschedule_task(task_id)
                if new_status:
                    task.enabled = new_status
                    await self.scheduler.schedule_task(task)
                
                status_text = "启用" if new_status else "禁用"
                return ApiResponse(success=True, message=f"任务已{status_text}")
                
            except Exception as e:
                logger.error(f"切换任务状态失败: {e}")
                return ApiResponse(success=False, message=str(e))
        
        # 任务执行记录API
        @self.app.get("/api/tasks/{task_id}/executions", response_model=ApiResponse)
        async def get_task_executions(task_id: int, limit: int = 50):
            try:
                executions = self.db_manager.get_executions_by_task(task_id, limit)
                return ApiResponse(
                    success=True, 
                    message="获取执行记录成功", 
                    data=[execution.dict() for execution in executions]
                )
            except Exception as e:
                logger.error(f"获取执行记录失败: {e}")
                return ApiResponse(success=False, message=str(e))
        
        @self.app.get("/api/executions", response_model=ApiResponse)
        async def get_all_executions(
            limit: int = 100,
            search: Optional[str] = None,
            sort_by: str = "created_at",
            sort_order: str = "desc"
        ):
            try:
                executions = self.db_manager.get_all_executions(
                    limit=limit, 
                    search=search,
                    sort_by=sort_by,
                    sort_order=sort_order
                )
                return ApiResponse(
                    success=True, 
                    message="获取所有执行记录成功", 
                    data=[execution.dict() for execution in executions]
                )
            except Exception as e:
                logger.error(f"获取所有执行记录失败: {e}")
                return ApiResponse(success=False, message=str(e))
        
        @self.app.delete("/api/executions", response_model=ApiResponse)
        async def delete_filtered_executions(
            search: Optional[str] = None,
            task_name: Optional[str] = None
        ):
            try:
                deleted_count = self.db_manager.delete_executions_by_filter(
                    search=search, 
                    task_name=task_name
                )
                return ApiResponse(
                    success=True, 
                    message=f"已删除{deleted_count}条执行记录"
                )
            except Exception as e:
                logger.error(f"删除执行记录失败: {e}")
                return ApiResponse(success=False, message=str(e))
        
        # 系统状态API
        @self.app.get("/api/status", response_model=ApiResponse)
        async def get_system_status():
            try:
                import psutil
                import platform
                from datetime import datetime
                import asyncio
                
                # 使用并发获取所有数据以提升性能
                async def get_jobs_info():
                    return self.scheduler.get_all_jobs_info()
                
                async def get_db_counts():
                    return {
                        'device_count': self.db_manager.get_device_count(),
                        'task_count': self.db_manager.get_task_count(),
                        'enabled_task_count': self.db_manager.get_enabled_task_count()
                    }
                
                async def get_system_resources():
                    # 使用无阻塞方式获取CPU使用率
                    cpu_percent = psutil.cpu_percent(interval=0.1) or psutil.cpu_percent()
                    memory = psutil.virtual_memory()
                    disk = psutil.disk_usage('/')
                    network = psutil.net_io_counters()
                    
                    return {
                        'cpu_percent': cpu_percent,
                        'memory': memory,
                        'disk': disk,
                        'network': network
                    }
                
                async def get_system_times():
                    boot_time = datetime.fromtimestamp(psutil.boot_time())
                    current_time = datetime.now()
                    uptime = current_time - boot_time
                    
                    return {
                        'boot_time': boot_time,
                        'current_time': current_time,
                        'uptime': uptime
                    }
                
                # 并发执行所有数据获取任务
                jobs_info, db_counts, system_resources, system_times = await asyncio.gather(
                    get_jobs_info(),
                    get_db_counts(),
                    get_system_resources(),
                    get_system_times()
                )
                
                return ApiResponse(
                    success=True,
                    message="获取系统状态成功",
                    data={
                        "server": {
                            "status": "running",
                            "uptime": str(system_times['uptime']).split('.')[0],  # 去掉微秒
                            "version": "1.3.0",
                            "python_version": platform.python_version(),
                            "platform": platform.system(),
                            "architecture": platform.machine()
                        },
                        "system": {
                            "cpu_usage": round(system_resources['cpu_percent'], 1),
                            "cpu_count": psutil.cpu_count(),
                            "memory": {
                                "total": system_resources['memory'].total,
                                "available": system_resources['memory'].available,
                                "used": system_resources['memory'].used,
                                "percent": round(system_resources['memory'].percent, 1)
                            },
                            "disk": {
                                "total": system_resources['disk'].total,
                                "used": system_resources['disk'].used,
                                "free": system_resources['disk'].free,
                                "percent": round((system_resources['disk'].used / (system_resources['disk'].used + system_resources['disk'].free)) * 100, 1)
                            },
                            "network": {
                                "bytes_sent": system_resources['network'].bytes_sent,
                                "bytes_recv": system_resources['network'].bytes_recv,
                                "packets_sent": system_resources['network'].packets_sent,
                                "packets_recv": system_resources['network'].packets_recv
                            }
                        },
                        "scheduler": {
                            "running": self.scheduler.is_running,
                            "active_jobs": len(jobs_info),
                            "jobs": jobs_info
                        },
                        "database": {
                            "device_count": db_counts['device_count'],
                            "task_count": db_counts['task_count'],
                            "enabled_task_count": db_counts['enabled_task_count'],
                            "execution_count": self.db_manager.get_execution_count()
                        }
                    }
                )
            except Exception as e:
                logger.error(f"获取系统状态失败: {e}")
                return ApiResponse(success=False, message=str(e))
        
        # 日志清理API
        @self.app.post("/api/maintenance/cleanup", response_model=ApiResponse)
        async def cleanup_old_logs(days: int = 30):
            try:
                self.db_manager.cleanup_old_executions(days)
                return ApiResponse(success=True, message=f"已清理{days}天前的执行记录")
            except Exception as e:
                logger.error(f"清理日志失败: {e}")
                return ApiResponse(success=False, message=str(e))


def create_app(data_dir: str = "data") -> FastAPI:
    """创建FastAPI应用实例"""
    api = ServerManagerAPI(data_dir)
    return api.app