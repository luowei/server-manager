from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    SHELL = "shell"


class TaskRuntimeStatus(str, Enum):
    """任务运行时状态枚举"""
    DISABLED = "disabled"     # 禁用
    ENABLED_STOPPED = "enabled_stopped"   # 启用但停止
    ENABLED_RUNNING = "enabled_running"   # 启用且运行中


class WOLDevice(BaseModel):
    """Wake-on-LAN设备模型"""
    id: Optional[int] = None
    name: str = Field(..., description="设备名称")
    hostname: Optional[str] = Field(None, description="主机名")
    ip_address: Optional[str] = Field(None, description="IP地址或CIDR")
    mac_address: str = Field(..., description="MAC地址")
    description: Optional[str] = Field(None, description="设备描述")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @validator('mac_address')
    def validate_mac_address(cls, v):
        """验证MAC地址格式"""
        if v:
            # 移除分隔符并转换为大写
            mac = v.replace(':', '').replace('-', '').replace('.', '').upper()
            if len(mac) != 12:
                raise ValueError('MAC地址格式错误')
            # 重新格式化为标准格式
            return ':'.join([mac[i:i+2] for i in range(0, 12, 2)])
        return v
    
    @validator('ip_address')
    def validate_ip_address(cls, v):
        """验证IP地址或CIDR格式"""
        if v:
            import ipaddress
            try:
                # 尝试解析为IP地址或网络地址
                if '/' in v:
                    # CIDR格式
                    ipaddress.ip_network(v, strict=False)
                else:
                    # 纯IP地址，默认为/24
                    ipaddress.ip_address(v)
                return v
            except ValueError:
                raise ValueError('IP地址或CIDR格式错误')
        return v
    
    @validator('hostname')
    def validate_hostname(cls, v):
        """验证主机名格式，支持mDNS格式(.local, .lan)"""
        if v:
            # 简单的主机名验证，允许mDNS格式
            v = v.strip()
            if not v:
                return None
            # 允许标准主机名和mDNS格式(.local, .lan等)
            import re
            # 主机名可以包含字母、数字、连字符和点号
            if re.match(r'^[a-zA-Z0-9.-]+$', v):
                return v
            else:
                raise ValueError('主机名格式错误')
        return v
    
    def get_display_address(self) -> str:
        """获取用于显示的主机名或IP地址
        
        优先级：
        1. 主机名（支持mDNS格式如.local, .lan）
        2. IP地址
        3. '-'（无信息）
        """
        if self.hostname:
            return self.hostname
        elif self.ip_address:
            # 如果是CIDR格式，只显示IP部分
            if '/' in self.ip_address:
                return self.ip_address.split('/')[0]
            return self.ip_address
        else:
            return '-'
    
    def is_mdns_hostname(self) -> bool:
        """检查是否为mDNS主机名格式"""
        if not self.hostname:
            return False
        return self.hostname.endswith('.local') or self.hostname.endswith('.lan')


class ScheduledTask(BaseModel):
    """定时任务模型"""
    id: Optional[int] = None
    name: str = Field(..., description="任务名称")
    task_type: TaskType = Field(TaskType.SHELL, description="任务类型")
    command: str = Field(..., description="要执行的命令")
    description: Optional[str] = Field(None, description="任务描述")
    
    # 调度配置
    enabled: bool = Field(True, description="是否启用")
    cron_expression: Optional[str] = Field(None, description="Cron表达式")
    interval_seconds: Optional[int] = Field(None, description="间隔秒数")
    
    # 执行配置
    timeout_seconds: int = Field(300, description="超时时间(秒)")
    max_retries: int = Field(0, description="最大重试次数")
    
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_run_at: Optional[datetime] = Field(None, description="上次执行时间")
    next_run_at: Optional[datetime] = Field(None, description="下次执行时间")


class TaskResponse(ScheduledTask):
    """任务响应模型，包含运行时状态"""
    runtime_status: TaskRuntimeStatus = Field(..., description="运行时状态")


class TaskExecution(BaseModel):
    """任务执行记录模型"""
    id: Optional[int] = None
    task_id: int = Field(..., description="任务ID")
    task_name: str = Field(..., description="任务名称")
    status: TaskStatus = Field(TaskStatus.PENDING, description="执行状态")
    
    # 执行信息
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    duration_seconds: Optional[float] = Field(None, description="执行时长(秒)")
    
    # 执行结果
    exit_code: Optional[int] = Field(None, description="退出码")
    stdout: Optional[str] = Field(None, description="标准输出")
    stderr: Optional[str] = Field(None, description="错误输出")
    error_message: Optional[str] = Field(None, description="错误信息")
    
    # 元数据
    pid: Optional[int] = Field(None, description="进程ID")
    command: str = Field(..., description="执行的命令")
    created_at: datetime = Field(default_factory=datetime.now)


class WOLRequest(BaseModel):
    """唤醒请求模型"""
    device_id: Optional[int] = None
    mac_address: Optional[str] = None
    ip_address: Optional[str] = Field(None, description="广播IP地址")
    port: int = Field(9, description="WOL端口")


class TaskCreateRequest(BaseModel):
    """创建任务请求模型"""
    name: str
    task_type: TaskType = TaskType.SHELL
    command: str
    description: Optional[str] = None
    enabled: bool = True
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    timeout_seconds: int = 300
    max_retries: int = 0


class TaskUpdateRequest(BaseModel):
    """更新任务请求模型"""
    name: Optional[str] = None
    task_type: Optional[TaskType] = None
    command: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    timeout_seconds: Optional[int] = None
    max_retries: Optional[int] = None


class ApiResponse(BaseModel):
    """API响应模型"""
    success: bool
    message: str
    data: Optional[Any] = None