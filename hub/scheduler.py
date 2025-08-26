"""
Maya Control Plane Scheduler

Task scheduling and background job management for Maya control plane operations.
Handles campaign scheduling, content publishing, and periodic maintenance tasks.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
import uuid
from enum import Enum
from dataclasses import dataclass, field

from celery import Celery
from celery.schedules import crontab
import structlog

from stubs.schemas import Campaign, Post, Event
from hub.logger import get_logger


logger = get_logger("scheduler")


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class ScheduledTask:
    """Represents a scheduled task"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    function: str = ""
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    scheduled_time: datetime = field(default_factory=datetime.utcnow)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class MayaScheduler:
    """Advanced scheduler for Maya control plane operations"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self.celery_app = self._create_celery_app()
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        
        logger.info("Maya Scheduler initialized", redis_url=redis_url)
    
    def _create_celery_app(self) -> Celery:
        """Create and configure Celery application"""
        app = Celery('maya-scheduler')
        
        app.conf.update(
            broker_url=self.redis_url,
            result_backend=self.redis_url,
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            timezone='UTC',
            enable_utc=True,
            task_track_started=True,
            task_time_limit=30 * 60,  # 30 minutes
            task_soft_time_limit=25 * 60,  # 25 minutes
            worker_prefetch_multiplier=1,
            task_acks_late=True,
            worker_disable_rate_limits=False,
            task_compression='gzip',
            result_compression='gzip',
        )
        
        # Configure periodic tasks
        app.conf.beat_schedule = {
            'process-scheduled-campaigns': {
                'task': 'maya.scheduler.process_scheduled_campaigns',
                'schedule': crontab(minute='*/5'),  # Every 5 minutes
            },
            'cleanup-completed-tasks': {
                'task': 'maya.scheduler.cleanup_completed_tasks',
                'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
            },
            'health-check': {
                'task': 'maya.scheduler.health_check',
                'schedule': crontab(minute='*/1'),  # Every minute
            },
        }
        
        return app
    
    def schedule_task(self, task: ScheduledTask) -> str:
        """Schedule a new task"""
        self.tasks[task.id] = task
        
        # Calculate delay until scheduled time
        delay = (task.scheduled_time - datetime.utcnow()).total_seconds()
        
        if delay <= 0:
            # Execute immediately
            self._execute_task_async(task)
        else:
            # Schedule for later execution
            self.celery_app.send_task(
                'maya.scheduler.execute_scheduled_task',
                args=[task.id],
                countdown=delay,
                priority=task.priority.value
            )
        
        logger.info("Task scheduled", 
                   task_id=task.id, 
                   task_name=task.name,
                   scheduled_time=task.scheduled_time.isoformat(),
                   delay_seconds=delay)
        
        return task.id
    
    def _execute_task_async(self, task: ScheduledTask):
        """Execute task asynchronously"""
        async_task = asyncio.create_task(self._execute_task(task))
        self.running_tasks[task.id] = async_task
    
    async def _execute_task(self, task: ScheduledTask):
        """Execute a scheduled task"""
        task.status = TaskStatus.RUNNING
        task.updated_at = datetime.utcnow()
        
        try:
            logger.info("Executing task", 
                       task_id=task.id, 
                       task_name=task.name,
                       function=task.function)
            
            # Route to appropriate execution function
            if task.function == "execute_campaign_on_platform":
                await self._execute_campaign_on_platform(*task.args)
            elif task.function == "publish_post":
                await self._publish_post(*task.args)
            elif task.function == "sync_metrics":
                await self._sync_metrics(*task.args)
            else:
                logger.warning("Unknown task function", function=task.function)
            
            task.status = TaskStatus.COMPLETED
            logger.info("Task completed successfully", task_id=task.id)
            
        except Exception as e:
            task.retry_count += 1
            
            if task.retry_count <= task.max_retries:
                task.status = TaskStatus.PENDING
                # Schedule retry with exponential backoff
                retry_delay = 2 ** task.retry_count * 60  # 2, 4, 8 minutes
                retry_time = datetime.utcnow() + timedelta(seconds=retry_delay)
                task.scheduled_time = retry_time
                
                logger.warning("Task failed, scheduling retry",
                             task_id=task.id,
                             retry_count=task.retry_count,
                             retry_time=retry_time.isoformat(),
                             error=str(e))
                
                # Reschedule
                self.celery_app.send_task(
                    'maya.scheduler.execute_scheduled_task',
                    args=[task.id],
                    countdown=retry_delay
                )
            else:
                task.status = TaskStatus.FAILED
                logger.error("Task failed permanently",
                           task_id=task.id,
                           retry_count=task.retry_count,
                           error=str(e))
        
        finally:
            task.updated_at = datetime.utcnow()
            if task.id in self.running_tasks:
                del self.running_tasks[task.id]
    
    async def _execute_campaign_on_platform(self, campaign_data: Dict[str, Any], platform: str):
        """Execute campaign on specific platform"""
        # This would integrate with the orchestrator and adapters
        logger.info("Executing campaign on platform",
                   campaign_id=campaign_data.get('id'),
                   platform=platform)
        
        # Placeholder for actual implementation
        await asyncio.sleep(1)  # Simulate work
    
    async def _publish_post(self, post_data: Dict[str, Any]):
        """Publish a single post"""
        logger.info("Publishing post", post_id=post_data.get('id'))
        
        # Placeholder for actual implementation
        await asyncio.sleep(1)  # Simulate work
    
    async def _sync_metrics(self, platform: str):
        """Sync metrics from platform"""
        logger.info("Syncing metrics", platform=platform)
        
        # Placeholder for actual implementation
        await asyncio.sleep(1)  # Simulate work
    
    def get_scheduler_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        status_counts = {}
        priority_counts = {}
        
        for task in self.tasks.values():
            status_counts[task.status.value] = status_counts.get(task.status.value, 0) + 1
            priority_counts[task.priority.value] = priority_counts.get(task.priority.value, 0) + 1
        
        return {
            "total_tasks": len(self.tasks),
            "running_tasks": len(self.running_tasks),
            "status_breakdown": status_counts,
            "priority_breakdown": priority_counts,
            "scheduler_uptime": datetime.utcnow().isoformat()
        }


# Global scheduler instance
scheduler = MayaScheduler()