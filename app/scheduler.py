import asyncio
import subprocess
import logging
import psutil
import os
import shlex
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor

from .models import ScheduledTask, TaskExecution, TaskStatus, TaskType
from .database import DatabaseManager

logger = logging.getLogger(__name__)


class TaskExecutor:
    """任务执行器"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.running_processes: Dict[int, subprocess.Popen] = {}
    
    async def execute_shell_task(self, task: ScheduledTask, execution: TaskExecution) -> TaskExecution:
        """
        执行Shell任务
        
        Args:
            task: 定时任务
            execution: 执行记录
            
        Returns:
            更新后的执行记录
        """
        try:
            # 更新执行状态为运行中
            execution.status = TaskStatus.RUNNING
            execution.started_at = datetime.now()
            self.db_manager.update_execution(execution.id, {
                'status': execution.status.value,
                'started_at': execution.started_at
            })
            
            # 准备执行环境
            env = os.environ.copy()
            
            # 设置工作目录为用户主目录
            working_dir = os.path.expanduser("~")
            
            # 确保 shell 环境正确设置
            if 'SHELL' not in env:
                env['SHELL'] = '/bin/bash'
            
            # 为命令添加完整的shell环境
            # 使用 bash -l -c 来确保加载用户的完整环境
            full_command = f"bash -l -c {shlex.quote(task.command)}"
            
            logger.info(f"执行命令: {full_command}, 工作目录: {working_dir}")
            
            # 创建子进程执行命令
            process = await asyncio.create_subprocess_shell(
                full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
                env=env
            )
            
            execution.pid = process.pid
            self.running_processes[execution.id] = process
            
            try:
                # 等待进程完成，带超时
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=task.timeout_seconds
                )
                
                execution.exit_code = process.returncode
                execution.stdout = stdout.decode('utf-8', errors='ignore')
                execution.stderr = stderr.decode('utf-8', errors='ignore')
                
                # 根据退出码设置状态
                if process.returncode == 0:
                    execution.status = TaskStatus.COMPLETED
                else:
                    execution.status = TaskStatus.FAILED
                    execution.error_message = f"进程退出码: {process.returncode}"
                
            except asyncio.TimeoutError:
                # 超时，终止进程
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=5)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
                
                execution.status = TaskStatus.FAILED
                execution.error_message = f"任务执行超时 ({task.timeout_seconds}秒)"
                execution.exit_code = -1
            
            finally:
                # 清理进程记录
                if execution.id in self.running_processes:
                    del self.running_processes[execution.id]
            
            execution.completed_at = datetime.now()
            execution.duration_seconds = (execution.completed_at - execution.started_at).total_seconds()
            
        except Exception as e:
            execution.status = TaskStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now()
            if execution.started_at:
                execution.duration_seconds = (execution.completed_at - execution.started_at).total_seconds()
            logger.error(f"执行Shell任务失败 [{task.name}]: {e}")
        
        # 更新执行记录
        self.db_manager.update_execution(execution.id, {
            'status': execution.status.value,
            'completed_at': execution.completed_at,
            'duration_seconds': execution.duration_seconds,
            'exit_code': execution.exit_code,
            'stdout': execution.stdout,
            'stderr': execution.stderr,
            'error_message': execution.error_message,
            'pid': execution.pid
        })
        
        return execution
    
    
    async def execute_task(self, task: ScheduledTask) -> TaskExecution:
        """
        执行任务
        
        Args:
            task: 定时任务
            
        Returns:
            执行记录
        """
        # 创建执行记录
        execution = TaskExecution(
            task_id=task.id,
            task_name=task.name,
            command=task.command,
            status=TaskStatus.PENDING
        )
        execution = self.db_manager.create_execution(execution)
        
        logger.info(f"开始执行任务 [{task.name}] (ID: {task.id})")
        
        try:
            # 所有任务都作为Shell任务执行
            execution = await self.execute_shell_task(task, execution)
            
            # 更新任务的最后执行时间
            self.db_manager.update_task(task.id, {
                'last_run_at': execution.completed_at or datetime.now()
            })
            
            logger.info(f"任务执行完成 [{task.name}]: {execution.status.value}")
            
        except Exception as e:
            execution.status = TaskStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now()
            
            self.db_manager.update_execution(execution.id, {
                'status': execution.status.value,
                'error_message': execution.error_message,
                'completed_at': execution.completed_at
            })
            
            logger.error(f"任务执行异常 [{task.name}]: {e}")
        
        return execution
    
    def cancel_task_execution(self, execution_id: int) -> bool:
        """
        取消正在执行的任务
        
        Args:
            execution_id: 执行记录ID
            
        Returns:
            是否成功取消
        """
        if execution_id not in self.running_processes:
            return False
        
        try:
            process = self.running_processes[execution_id]
            
            # 尝试优雅终止进程树
            if hasattr(process, 'pid') and process.pid:
                try:
                    parent = psutil.Process(process.pid)
                    children = parent.children(recursive=True)
                    
                    # 终止子进程
                    for child in children:
                        child.terminate()
                    
                    # 终止主进程
                    parent.terminate()
                    
                    # 等待进程结束
                    psutil.wait_procs(children + [parent], timeout=5)
                    
                except psutil.NoSuchProcess:
                    pass
                except psutil.TimeoutExpired:
                    # 强制杀死进程
                    for child in children:
                        try:
                            child.kill()
                        except psutil.NoSuchProcess:
                            pass
                    try:
                        parent.kill()
                    except psutil.NoSuchProcess:
                        pass
            
            # 更新执行状态
            self.db_manager.update_execution(execution_id, {
                'status': TaskStatus.CANCELLED.value,
                'error_message': '任务被用户取消',
                'completed_at': datetime.now()
            })
            
            # 清理进程记录
            del self.running_processes[execution_id]
            
            logger.info(f"任务执行已取消: {execution_id}")
            return True
            
        except Exception as e:
            logger.error(f"取消任务执行失败: {e}")
            return False


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.executor = TaskExecutor(db_manager)
        
        # 配置调度器
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': AsyncIOExecutor()
        }
        job_defaults = {
            'coalesce': True,  # 合并多个相同的作业
            'max_instances': 1,  # 每个作业最多同时运行1个实例
            'misfire_grace_time': 30  # 错失触发的宽限时间
        }
        
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='Asia/Shanghai'
        )
        
        self.is_running = False
    
    async def start(self):
        """启动调度器"""
        if self.is_running:
            return
        
        logger.info("启动任务调度器...")
        self.scheduler.start()
        self.is_running = True
        
        # 加载现有任务
        await self.reload_tasks()
    
    async def stop(self):
        """停止调度器"""
        if not self.is_running:
            return
        
        logger.info("停止任务调度器...")
        self.scheduler.shutdown()
        self.is_running = False
    
    async def reload_tasks(self):
        """重新加载所有启用的任务"""
        if not self.is_running:
            return
        
        logger.info("重新加载任务...")
        
        # 清除现有作业
        self.scheduler.remove_all_jobs()
        
        # 获取所有启用的任务
        tasks = self.db_manager.get_enabled_tasks()
        
        for task in tasks:
            await self.schedule_task(task)
        
        logger.info(f"已加载 {len(tasks)} 个任务")
    
    async def schedule_task(self, task: ScheduledTask):
        """
        调度单个任务
        
        Args:
            task: 定时任务
        """
        if not self.is_running:
            return
        
        job_id = f"task_{task.id}"
        
        try:
            # 移除已存在的作业
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            
            # 确定触发器
            trigger = None
            
            if task.cron_expression:
                # 使用Cron表达式
                try:
                    # 解析Cron表达式 (秒 分 时 日 月 周)
                    parts = task.cron_expression.strip().split()
                    if len(parts) == 5:
                        # 标准5段式，添加秒段
                        parts.insert(0, '0')
                    
                    if len(parts) == 6:
                        trigger = CronTrigger(
                            second=parts[0],
                            minute=parts[1],
                            hour=parts[2],
                            day=parts[3],
                            month=parts[4],
                            day_of_week=parts[5],
                            timezone='Asia/Shanghai'
                        )
                    else:
                        logger.error(f"无效的Cron表达式: {task.cron_expression}")
                        return
                        
                except Exception as e:
                    logger.error(f"解析Cron表达式失败 [{task.name}]: {e}")
                    return
                    
            elif task.interval_seconds and task.interval_seconds > 0:
                # 使用间隔触发器
                trigger = IntervalTrigger(seconds=task.interval_seconds)
            
            if trigger:
                # 添加作业
                self.scheduler.add_job(
                    func=self._execute_task_job,
                    trigger=trigger,
                    id=job_id,
                    args=[task.id],
                    name=task.name,
                    replace_existing=True
                )
                
                # 计算下次执行时间
                job = self.scheduler.get_job(job_id)
                if job and job.next_run_time:
                    self.db_manager.update_task(task.id, {
                        'next_run_at': job.next_run_time
                    })
                
                logger.info(f"任务已调度 [{task.name}]: {trigger}")
            else:
                # 无有效触发器，清除下次执行时间
                self.db_manager.update_task(task.id, {
                    'next_run_at': None
                })
                logger.info(f"任务无调度配置，仅支持手动执行 [{task.name}]")
                
        except Exception as e:
            logger.error(f"调度任务失败 [{task.name}]: {e}")
    
    async def unschedule_task(self, task_id: int):
        """
        取消调度任务
        
        Args:
            task_id: 任务ID
        """
        job_id = f"task_{task_id}"
        
        try:
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                logger.info(f"任务调度已取消: {task_id}")
            
            # 清除下次执行时间
            self.db_manager.update_task(task_id, {'next_run_at': None})
            
        except Exception as e:
            logger.error(f"取消任务调度失败: {e}")
    
    async def _execute_task_job(self, task_id: int):
        """
        执行任务作业（调度器回调）
        
        Args:
            task_id: 任务ID
        """
        task = self.db_manager.get_task(task_id)
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return
        
        if not task.enabled:
            logger.info(f"任务已禁用，跳过执行: {task.name}")
            return
        
        # 执行任务
        await self.executor.execute_task(task)
        
        # 更新下次执行时间
        job_id = f"task_{task_id}"
        job = self.scheduler.get_job(job_id)
        if job and job.next_run_time:
            self.db_manager.update_task(task_id, {
                'next_run_at': job.next_run_time
            })
    
    async def execute_task_now(self, task_id: int) -> Optional[TaskExecution]:
        """
        立即执行任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            执行记录
        """
        task = self.db_manager.get_task(task_id)
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return None
        
        return await self.executor.execute_task(task)
    
    def get_job_info(self, task_id: int) -> Optional[Dict[str, Any]]:
        """
        获取任务的作业信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            作业信息字典
        """
        job_id = f"task_{task_id}"
        job = self.scheduler.get_job(job_id)
        
        if not job:
            return None
        
        return {
            'id': job.id,
            'name': job.name,
            'next_run_time': job.next_run_time,
            'trigger': str(job.trigger),
            'func_ref': job.func_ref,
            'args': job.args,
            'kwargs': job.kwargs
        }
    
    def get_all_jobs_info(self) -> List[Dict[str, Any]]:
        """获取所有作业信息"""
        jobs_info = []
        
        for job in self.scheduler.get_jobs():
            jobs_info.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time,
                'trigger': str(job.trigger),
                'func_ref': job.func_ref
            })
        
        return jobs_info
    
    def is_task_running(self, task_id: int) -> bool:
        """
        检查任务是否正在执行
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否正在执行
        """
        # 检查是否有正在执行的任务进程
        for exec_id, process in self.executor.running_processes.items():
            execution = self.db_manager.get_execution(exec_id)
            if execution and execution.task_id == task_id:
                return True
        return False
    
    def get_running_task_ids(self) -> List[int]:
        """获取所有正在执行的任务ID列表"""
        running_task_ids = []
        for exec_id, process in self.executor.running_processes.items():
            execution = self.db_manager.get_execution(exec_id)
            if execution and execution.task_id not in running_task_ids:
                running_task_ids.append(execution.task_id)
        return running_task_ids