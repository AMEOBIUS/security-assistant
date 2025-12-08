"""
Scheduled Security Scans Module

This module provides cron-based scheduling for automated security scans.
Uses APScheduler for robust scheduling with timezone support.

Example:
    >>> from security_assistant.scheduler import ScheduleManager, ScanSchedule
    >>>
    >>> # Create schedule manager
    >>> manager = ScheduleManager()
    >>>
    >>> # Create a daily scan schedule
    >>> schedule = ScanSchedule(
    ...     name="daily_scan",
    ...     cron="0 2 * * *",  # 2 AM daily
    ...     target="src/",
    ...     scanners=["bandit", "semgrep"]
    ... )
    >>>
    >>> # Add schedule
    >>> manager.add_schedule(schedule)
    >>>
    >>> # Start scheduler
    >>> manager.start()
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

try:
    from apscheduler.executors.pool import ThreadPoolExecutor
    from apscheduler.jobstores.memory import MemoryJobStore
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger

    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    BackgroundScheduler = None
    CronTrigger = None


logger = logging.getLogger(__name__)


class ScheduleStatus(Enum):
    """Schedule status enumeration"""

    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class ScanSchedule:
    """
    Represents a scheduled security scan configuration.

    Attributes:
        name: Unique schedule name
        cron: Cron expression (e.g., "0 2 * * *" for 2 AM daily)
        target: Scan target (directory or file path)
        scanners: List of scanner names to use
        timezone: Timezone for schedule (default: UTC)
        enabled: Whether schedule is enabled
        min_severity: Minimum severity to report
        notification_emails: Email addresses for notifications
        notification_webhooks: Webhook URLs for notifications
        metadata: Additional metadata
    """

    name: str
    cron: str
    target: str
    scanners: List[str]
    timezone: str = "UTC"
    enabled: bool = True
    min_severity: Optional[str] = None
    notification_emails: List[str] = field(default_factory=list)
    notification_webhooks: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate schedule after initialization"""
        if not self.name:
            raise ValueError("Schedule name is required")
        if not self.cron:
            raise ValueError("Cron expression is required")
        if not self.target:
            raise ValueError("Scan target is required")
        if not self.scanners:
            raise ValueError("At least one scanner is required")

        # Validate cron expression
        self._validate_cron()

    def _validate_cron(self):
        """Validate cron expression format"""
        if not APSCHEDULER_AVAILABLE:
            logger.warning("APScheduler not available, skipping cron validation")
            return

        try:
            # Try to create a CronTrigger to validate
            CronTrigger.from_crontab(self.cron, timezone=self.timezone)
        except Exception as e:
            raise ValueError(f"Invalid cron expression '{self.cron}': {e}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert schedule to dictionary"""
        return {
            "name": self.name,
            "cron": self.cron,
            "target": self.target,
            "scanners": self.scanners,
            "timezone": self.timezone,
            "enabled": self.enabled,
            "min_severity": self.min_severity,
            "notification_emails": self.notification_emails,
            "notification_webhooks": self.notification_webhooks,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScanSchedule":
        """Create schedule from dictionary"""
        return cls(**data)

    def to_json(self) -> str:
        """Convert schedule to JSON string"""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ScanSchedule":
        """Create schedule from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)


class ScheduleManager:
    """
    Manages scheduled security scans using APScheduler.

    Features:
        - Cron-based scheduling
        - Timezone support
        - Multiple schedules
        - Start/stop/pause control
        - Next run calculation
        - Job history tracking

    Example:
        >>> manager = ScheduleManager()
        >>> schedule = ScanSchedule(
        ...     name="daily_scan",
        ...     cron="0 2 * * *",
        ...     target="src/",
        ...     scanners=["bandit"]
        ... )
        >>> manager.add_schedule(schedule)
        >>> manager.start()
    """

    def __init__(
        self,
        max_workers: int = 3,
        timezone: str = "UTC",
        job_defaults: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize schedule manager.

        Args:
            max_workers: Maximum number of concurrent scan jobs
            timezone: Default timezone for schedules
            job_defaults: Default job configuration
        """
        if not APSCHEDULER_AVAILABLE:
            raise ImportError(
                "APScheduler is required for scheduling. "
                "Install with: pip install apscheduler>=3.11.1"
            )

        self.max_workers = max_workers
        self.timezone = timezone
        self.schedules: Dict[str, ScanSchedule] = {}
        self.scan_callback: Optional[Callable] = None

        # Configure APScheduler
        jobstores = {"default": MemoryJobStore()}

        executors = {"default": ThreadPoolExecutor(max_workers)}

        defaults = job_defaults or {
            "coalesce": True,  # Combine missed runs
            "max_instances": 1,  # One instance per job
            "misfire_grace_time": 300,  # 5 minutes grace period
        }

        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=defaults,
            timezone=timezone,
        )

        logger.info(
            f"ScheduleManager initialized with {max_workers} workers, "
            f"timezone={timezone}"
        )

    def set_scan_callback(self, callback: Callable):
        """
        Set callback function for scan execution.

        Args:
            callback: Function to call when scan is triggered
                     Should accept (schedule: ScanSchedule) -> None
        """
        self.scan_callback = callback
        logger.info("Scan callback registered")

    def add_schedule(self, schedule: ScanSchedule) -> bool:
        """
        Add a new scan schedule.

        Args:
            schedule: ScanSchedule configuration

        Returns:
            True if schedule was added successfully

        Raises:
            ValueError: If schedule with same name exists
        """
        if schedule.name in self.schedules:
            raise ValueError(f"Schedule '{schedule.name}' already exists")

        if not schedule.enabled:
            logger.info(f"Schedule '{schedule.name}' added but disabled")
            self.schedules[schedule.name] = schedule
            return True

        try:
            # Create cron trigger
            trigger = CronTrigger.from_crontab(
                schedule.cron, timezone=schedule.timezone
            )

            # Add job to scheduler
            self.scheduler.add_job(
                func=self._execute_scan,
                trigger=trigger,
                args=[schedule],
                id=schedule.name,
                name=f"Scan: {schedule.name}",
                replace_existing=True,
            )

            self.schedules[schedule.name] = schedule
            logger.info(
                f"Schedule '{schedule.name}' added: {schedule.cron} "
                f"(next run: {self.get_next_run(schedule.name)})"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to add schedule '{schedule.name}': {e}")
            raise

    def remove_schedule(self, name: str) -> bool:
        """
        Remove a scan schedule.

        Args:
            name: Schedule name

        Returns:
            True if schedule was removed
        """
        if name not in self.schedules:
            logger.warning(f"Schedule '{name}' not found")
            return False

        try:
            # Remove job from scheduler
            self.scheduler.remove_job(name)
            del self.schedules[name]
            logger.info(f"Schedule '{name}' removed")
            return True
        except Exception as e:
            logger.error(f"Failed to remove schedule '{name}': {e}")
            return False

    def update_schedule(self, schedule: ScanSchedule) -> bool:
        """
        Update an existing schedule.

        Args:
            schedule: Updated ScanSchedule configuration

        Returns:
            True if schedule was updated
        """
        if schedule.name not in self.schedules:
            raise ValueError(f"Schedule '{schedule.name}' not found")

        # Remove old schedule and add new one
        self.remove_schedule(schedule.name)
        return self.add_schedule(schedule)

    def pause_schedule(self, name: str) -> bool:
        """
        Pause a schedule (temporarily disable).

        Args:
            name: Schedule name

        Returns:
            True if schedule was paused
        """
        if name not in self.schedules:
            logger.warning(f"Schedule '{name}' not found")
            return False

        try:
            self.scheduler.pause_job(name)
            logger.info(f"Schedule '{name}' paused")
            return True
        except Exception as e:
            logger.error(f"Failed to pause schedule '{name}': {e}")
            return False

    def resume_schedule(self, name: str) -> bool:
        """
        Resume a paused schedule.

        Args:
            name: Schedule name

        Returns:
            True if schedule was resumed
        """
        if name not in self.schedules:
            logger.warning(f"Schedule '{name}' not found")
            return False

        try:
            self.scheduler.resume_job(name)
            logger.info(f"Schedule '{name}' resumed")
            return True
        except Exception as e:
            logger.error(f"Failed to resume schedule '{name}': {e}")
            return False

    def get_schedule(self, name: str) -> Optional[ScanSchedule]:
        """
        Get schedule by name.

        Args:
            name: Schedule name

        Returns:
            ScanSchedule or None if not found
        """
        return self.schedules.get(name)

    def list_schedules(self) -> List[ScanSchedule]:
        """
        List all schedules.

        Returns:
            List of ScanSchedule objects
        """
        return list(self.schedules.values())

    def get_next_run(self, name: str) -> Optional[datetime]:
        """
        Get next run time for a schedule.

        Args:
            name: Schedule name

        Returns:
            Next run datetime or None
        """
        try:
            job = self.scheduler.get_job(name)
            if job:
                # APScheduler 3.x uses trigger.get_next_fire_time()
                from datetime import datetime as dt

                now = dt.now(job.trigger.timezone)
                return job.trigger.get_next_fire_time(None, now)
            return None
        except Exception as e:
            logger.error(f"Failed to get next run for '{name}': {e}")
            return None

    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info(f"Scheduler started with {len(self.schedules)} schedule(s)")
        else:
            logger.warning("Scheduler is already running")

    def stop(self, wait: bool = True):
        """
        Stop the scheduler.

        Args:
            wait: Wait for running jobs to complete
        """
        if self.scheduler.running:
            self.scheduler.shutdown(wait=wait)
            logger.info("Scheduler stopped")
        else:
            logger.warning("Scheduler is not running")

    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self.scheduler.running

    def _execute_scan(self, schedule: ScanSchedule):
        """
        Execute a scheduled scan.

        Args:
            schedule: ScanSchedule to execute
        """
        logger.info(f"Executing scheduled scan: {schedule.name}")

        if self.scan_callback:
            try:
                self.scan_callback(schedule)
                logger.info(f"Scan '{schedule.name}' completed successfully")
            except Exception as e:
                logger.error(f"Scan '{schedule.name}' failed: {e}", exc_info=True)
        else:
            logger.warning(
                f"No scan callback registered, skipping scan '{schedule.name}'"
            )

    def get_status(self) -> Dict[str, Any]:
        """
        Get scheduler status.

        Returns:
            Dictionary with scheduler status information
        """
        jobs = []
        for name, schedule in self.schedules.items():
            job = self.scheduler.get_job(name)
            next_run = self.get_next_run(name)
            jobs.append(
                {
                    "name": name,
                    "enabled": schedule.enabled,
                    "cron": schedule.cron,
                    "target": schedule.target,
                    "scanners": schedule.scanners,
                    "next_run": next_run.isoformat() if next_run else None,
                    "paused": next_run is None if job else False,
                }
            )

        return {
            "running": self.is_running(),
            "total_schedules": len(self.schedules),
            "max_workers": self.max_workers,
            "timezone": self.timezone,
            "schedules": jobs,
        }

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()
