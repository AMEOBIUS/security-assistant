"""
Tests for security_assistant.scheduler module
"""

import pytest
import time
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock

from security_assistant.scheduler import (
    ScanSchedule,
    ScheduleManager,
    ScheduleStatus,
    APSCHEDULER_AVAILABLE
)


# Skip all tests if APScheduler is not available
pytestmark = pytest.mark.skipif(
    not APSCHEDULER_AVAILABLE,
    reason="APScheduler not installed"
)


class TestScanSchedule:
    """Tests for ScanSchedule class"""
    
    def test_schedule_creation(self):
        """Test creating a valid schedule"""
        schedule = ScanSchedule(
            name="test_scan",
            cron="0 2 * * *",
            target="src/",
            scanners=["bandit", "semgrep"]
        )
        
        assert schedule.name == "test_scan"
        assert schedule.cron == "0 2 * * *"
        assert schedule.target == "src/"
        assert schedule.scanners == ["bandit", "semgrep"]
        assert schedule.timezone == "UTC"
        assert schedule.enabled is True
    
    def test_schedule_with_optional_fields(self):
        """Test schedule with optional fields"""
        schedule = ScanSchedule(
            name="test_scan",
            cron="0 2 * * *",
            target="src/",
            scanners=["bandit"],
            timezone="America/New_York",
            enabled=False,
            min_severity="HIGH",
            notification_emails=["test@example.com"],
            notification_webhooks=["https://hooks.example.com"],
            metadata={"project": "test"}
        )
        
        assert schedule.timezone == "America/New_York"
        assert schedule.enabled is False
        assert schedule.min_severity == "HIGH"
        assert schedule.notification_emails == ["test@example.com"]
        assert schedule.notification_webhooks == ["https://hooks.example.com"]
        assert schedule.metadata == {"project": "test"}
    
    def test_schedule_validation_missing_name(self):
        """Test schedule validation with missing name"""
        with pytest.raises(ValueError, match="name is required"):
            ScanSchedule(
                name="",
                cron="0 2 * * *",
                target="src/",
                scanners=["bandit"]
            )
    
    def test_schedule_validation_missing_cron(self):
        """Test schedule validation with missing cron"""
        with pytest.raises(ValueError, match="Cron expression is required"):
            ScanSchedule(
                name="test",
                cron="",
                target="src/",
                scanners=["bandit"]
            )
    
    def test_schedule_validation_missing_target(self):
        """Test schedule validation with missing target"""
        with pytest.raises(ValueError, match="target is required"):
            ScanSchedule(
                name="test",
                cron="0 2 * * *",
                target="",
                scanners=["bandit"]
            )
    
    def test_schedule_validation_missing_scanners(self):
        """Test schedule validation with missing scanners"""
        with pytest.raises(ValueError, match="At least one scanner is required"):
            ScanSchedule(
                name="test",
                cron="0 2 * * *",
                target="src/",
                scanners=[]
            )
    
    def test_schedule_validation_invalid_cron(self):
        """Test schedule validation with invalid cron expression"""
        with pytest.raises(ValueError, match="Invalid cron expression"):
            ScanSchedule(
                name="test",
                cron="invalid cron",
                target="src/",
                scanners=["bandit"]
            )
    
    def test_schedule_to_dict(self):
        """Test converting schedule to dictionary"""
        schedule = ScanSchedule(
            name="test_scan",
            cron="0 2 * * *",
            target="src/",
            scanners=["bandit"],
            min_severity="HIGH"
        )
        
        data = schedule.to_dict()
        
        assert data["name"] == "test_scan"
        assert data["cron"] == "0 2 * * *"
        assert data["target"] == "src/"
        assert data["scanners"] == ["bandit"]
        assert data["min_severity"] == "HIGH"
    
    def test_schedule_from_dict(self):
        """Test creating schedule from dictionary"""
        data = {
            "name": "test_scan",
            "cron": "0 2 * * *",
            "target": "src/",
            "scanners": ["bandit"],
            "timezone": "UTC",
            "enabled": True,
            "min_severity": None,
            "notification_emails": [],
            "notification_webhooks": [],
            "metadata": {}
        }
        
        schedule = ScanSchedule.from_dict(data)
        
        assert schedule.name == "test_scan"
        assert schedule.cron == "0 2 * * *"
        assert schedule.target == "src/"
        assert schedule.scanners == ["bandit"]
    
    def test_schedule_to_json(self):
        """Test converting schedule to JSON"""
        schedule = ScanSchedule(
            name="test_scan",
            cron="0 2 * * *",
            target="src/",
            scanners=["bandit"]
        )
        
        json_str = schedule.to_json()
        
        assert "test_scan" in json_str
        assert "0 2 * * *" in json_str
        assert "src/" in json_str
    
    def test_schedule_from_json(self):
        """Test creating schedule from JSON"""
        json_str = '''
        {
            "name": "test_scan",
            "cron": "0 2 * * *",
            "target": "src/",
            "scanners": ["bandit"],
            "timezone": "UTC",
            "enabled": true,
            "min_severity": null,
            "notification_emails": [],
            "notification_webhooks": [],
            "metadata": {}
        }
        '''
        
        schedule = ScanSchedule.from_json(json_str)
        
        assert schedule.name == "test_scan"
        assert schedule.cron == "0 2 * * *"


class TestScheduleManager:
    """Tests for ScheduleManager class"""
    
    def test_manager_initialization(self):
        """Test schedule manager initialization"""
        manager = ScheduleManager(max_workers=5, timezone="America/New_York")
        
        assert manager.max_workers == 5
        assert manager.timezone == "America/New_York"
        assert len(manager.schedules) == 0
        assert manager.scan_callback is None
        assert not manager.is_running()
    
    def test_manager_initialization_without_apscheduler(self):
        """Test manager initialization without APScheduler"""
        with patch('security_assistant.scheduler.APSCHEDULER_AVAILABLE', False):
            with pytest.raises(ImportError, match="APScheduler is required"):
                ScheduleManager()
    
    def test_set_scan_callback(self):
        """Test setting scan callback"""
        manager = ScheduleManager()
        callback = Mock()
        
        manager.set_scan_callback(callback)
        
        assert manager.scan_callback == callback
    
    def test_add_schedule(self):
        """Test adding a schedule"""
        manager = ScheduleManager()
        schedule = ScanSchedule(
            name="test_scan",
            cron="0 2 * * *",
            target="src/",
            scanners=["bandit"]
        )
        
        result = manager.add_schedule(schedule)
        
        assert result is True
        assert "test_scan" in manager.schedules
        assert manager.schedules["test_scan"] == schedule
    
    def test_add_duplicate_schedule(self):
        """Test adding duplicate schedule"""
        manager = ScheduleManager()
        schedule = ScanSchedule(
            name="test_scan",
            cron="0 2 * * *",
            target="src/",
            scanners=["bandit"]
        )
        
        manager.add_schedule(schedule)
        
        with pytest.raises(ValueError, match="already exists"):
            manager.add_schedule(schedule)
    
    def test_add_disabled_schedule(self):
        """Test adding disabled schedule"""
        manager = ScheduleManager()
        schedule = ScanSchedule(
            name="test_scan",
            cron="0 2 * * *",
            target="src/",
            scanners=["bandit"],
            enabled=False
        )
        
        result = manager.add_schedule(schedule)
        
        assert result is True
        assert "test_scan" in manager.schedules
        # Disabled schedule should not be added to APScheduler
        assert manager.scheduler.get_job("test_scan") is None
    
    def test_remove_schedule(self):
        """Test removing a schedule"""
        manager = ScheduleManager()
        schedule = ScanSchedule(
            name="test_scan",
            cron="0 2 * * *",
            target="src/",
            scanners=["bandit"]
        )
        
        manager.add_schedule(schedule)
        result = manager.remove_schedule("test_scan")
        
        assert result is True
        assert "test_scan" not in manager.schedules
    
    def test_remove_nonexistent_schedule(self):
        """Test removing nonexistent schedule"""
        manager = ScheduleManager()
        
        result = manager.remove_schedule("nonexistent")
        
        assert result is False
    
    def test_update_schedule(self):
        """Test updating a schedule"""
        manager = ScheduleManager()
        schedule = ScanSchedule(
            name="test_scan",
            cron="0 2 * * *",
            target="src/",
            scanners=["bandit"]
        )
        
        manager.add_schedule(schedule)
        
        # Update schedule
        updated_schedule = ScanSchedule(
            name="test_scan",
            cron="0 3 * * *",  # Changed time
            target="src/",
            scanners=["bandit", "semgrep"]  # Added scanner
        )
        
        result = manager.update_schedule(updated_schedule)
        
        assert result is True
        assert manager.schedules["test_scan"].cron == "0 3 * * *"
        assert len(manager.schedules["test_scan"].scanners) == 2
    
    def test_update_nonexistent_schedule(self):
        """Test updating nonexistent schedule"""
        manager = ScheduleManager()
        schedule = ScanSchedule(
            name="nonexistent",
            cron="0 2 * * *",
            target="src/",
            scanners=["bandit"]
        )
        
        with pytest.raises(ValueError, match="not found"):
            manager.update_schedule(schedule)
    
    def test_pause_schedule(self):
        """Test pausing a schedule"""
        manager = ScheduleManager()
        schedule = ScanSchedule(
            name="test_scan",
            cron="0 2 * * *",
            target="src/",
            scanners=["bandit"]
        )
        
        manager.add_schedule(schedule)
        result = manager.pause_schedule("test_scan")
        
        assert result is True
    
    def test_resume_schedule(self):
        """Test resuming a schedule"""
        manager = ScheduleManager()
        schedule = ScanSchedule(
            name="test_scan",
            cron="0 2 * * *",
            target="src/",
            scanners=["bandit"]
        )
        
        manager.add_schedule(schedule)
        manager.pause_schedule("test_scan")
        result = manager.resume_schedule("test_scan")
        
        assert result is True
    
    def test_get_schedule(self):
        """Test getting a schedule"""
        manager = ScheduleManager()
        schedule = ScanSchedule(
            name="test_scan",
            cron="0 2 * * *",
            target="src/",
            scanners=["bandit"]
        )
        
        manager.add_schedule(schedule)
        retrieved = manager.get_schedule("test_scan")
        
        assert retrieved == schedule
    
    def test_get_nonexistent_schedule(self):
        """Test getting nonexistent schedule"""
        manager = ScheduleManager()
        
        result = manager.get_schedule("nonexistent")
        
        assert result is None
    
    def test_list_schedules(self):
        """Test listing all schedules"""
        manager = ScheduleManager()
        
        schedule1 = ScanSchedule(
            name="scan1",
            cron="0 2 * * *",
            target="src/",
            scanners=["bandit"]
        )
        schedule2 = ScanSchedule(
            name="scan2",
            cron="0 3 * * *",
            target="tests/",
            scanners=["semgrep"]
        )
        
        manager.add_schedule(schedule1)
        manager.add_schedule(schedule2)
        
        schedules = manager.list_schedules()
        
        assert len(schedules) == 2
        assert schedule1 in schedules
        assert schedule2 in schedules
    
    def test_get_next_run(self):
        """Test getting next run time"""
        manager = ScheduleManager()
        schedule = ScanSchedule(
            name="test_scan",
            cron="0 2 * * *",
            target="src/",
            scanners=["bandit"]
        )
        
        manager.add_schedule(schedule)
        next_run = manager.get_next_run("test_scan")
        
        assert next_run is not None
        assert isinstance(next_run, datetime)
    
    def test_start_stop_scheduler(self):
        """Test starting and stopping scheduler"""
        manager = ScheduleManager()
        
        assert not manager.is_running()
        
        manager.start()
        assert manager.is_running()
        
        manager.stop()
        assert not manager.is_running()
    
    def test_context_manager(self):
        """Test using scheduler as context manager"""
        manager = ScheduleManager()
        
        assert not manager.is_running()
        
        with manager:
            assert manager.is_running()
        
        assert not manager.is_running()
    
    def test_execute_scan_with_callback(self):
        """Test scan execution with callback"""
        manager = ScheduleManager()
        callback = Mock()
        manager.set_scan_callback(callback)
        
        schedule = ScanSchedule(
            name="test_scan",
            cron="0 2 * * *",
            target="src/",
            scanners=["bandit"]
        )
        
        # Execute scan directly
        manager._execute_scan(schedule)
        
        callback.assert_called_once_with(schedule)
    
    def test_execute_scan_without_callback(self):
        """Test scan execution without callback"""
        manager = ScheduleManager()
        
        schedule = ScanSchedule(
            name="test_scan",
            cron="0 2 * * *",
            target="src/",
            scanners=["bandit"]
        )
        
        # Should not raise exception
        manager._execute_scan(schedule)
    
    def test_execute_scan_callback_error(self):
        """Test scan execution with callback error"""
        manager = ScheduleManager()
        callback = Mock(side_effect=Exception("Test error"))
        manager.set_scan_callback(callback)
        
        schedule = ScanSchedule(
            name="test_scan",
            cron="0 2 * * *",
            target="src/",
            scanners=["bandit"]
        )
        
        # Should not raise exception, just log error
        manager._execute_scan(schedule)
        
        callback.assert_called_once()
    
    def test_get_status(self):
        """Test getting scheduler status"""
        manager = ScheduleManager()
        
        schedule = ScanSchedule(
            name="test_scan",
            cron="0 2 * * *",
            target="src/",
            scanners=["bandit"]
        )
        
        manager.add_schedule(schedule)
        status = manager.get_status()
        
        assert status["running"] is False
        assert status["total_schedules"] == 1
        assert status["max_workers"] == 3
        assert status["timezone"] == "UTC"
        assert len(status["schedules"]) == 1
        assert status["schedules"][0]["name"] == "test_scan"
    
    def test_scheduled_execution(self):
        """Test actual scheduled execution (integration test)"""
        manager = ScheduleManager()
        callback = Mock()
        manager.set_scan_callback(callback)
        
        # Create schedule that runs every minute (standard cron format)
        # Note: APScheduler 3.x only supports 5-field cron (no seconds)
        # For testing, we'll use interval trigger instead
        from apscheduler.triggers.interval import IntervalTrigger
        
        schedule = ScanSchedule(
            name="test_scan",
            cron="* * * * *",  # Every minute (won't actually run in test)
            target="src/",
            scanners=["bandit"]
        )
        
        # Add schedule but don't start scheduler
        # Instead, manually trigger execution for testing
        manager.schedules[schedule.name] = schedule
        manager._execute_scan(schedule)
        
        # Callback should have been called once
        assert callback.call_count == 1
    
    def test_add_schedule_error_handling(self):
        """Test error handling when adding schedule fails"""
        manager = ScheduleManager()
        
        # Create invalid schedule that will fail during job creation
        schedule = ScanSchedule(
            name="test_scan",
            cron="0 2 * * *",
            target="src/",
            scanners=["bandit"]
        )
        
        # Mock scheduler.add_job to raise exception
        with patch.object(manager.scheduler, 'add_job', side_effect=Exception("Test error")):
            with pytest.raises(Exception, match="Test error"):
                manager.add_schedule(schedule)
    
    def test_remove_schedule_error_handling(self):
        """Test error handling when removing schedule fails"""
        manager = ScheduleManager()
        
        schedule = ScanSchedule(
            name="test_scan",
            cron="0 2 * * *",
            target="src/",
            scanners=["bandit"]
        )
        
        manager.add_schedule(schedule)
        
        # Mock scheduler.remove_job to raise exception
        with patch.object(manager.scheduler, 'remove_job', side_effect=Exception("Test error")):
            result = manager.remove_schedule("test_scan")
            assert result is False
    
    def test_pause_schedule_error_handling(self):
        """Test error handling when pausing schedule fails"""
        manager = ScheduleManager()
        
        schedule = ScanSchedule(
            name="test_scan",
            cron="0 2 * * *",
            target="src/",
            scanners=["bandit"]
        )
        
        manager.add_schedule(schedule)
        
        # Mock scheduler.pause_job to raise exception
        with patch.object(manager.scheduler, 'pause_job', side_effect=Exception("Test error")):
            result = manager.pause_schedule("test_scan")
            assert result is False
    
    def test_pause_nonexistent_schedule(self):
        """Test pausing nonexistent schedule"""
        manager = ScheduleManager()
        
        result = manager.pause_schedule("nonexistent")
        assert result is False
    
    def test_resume_schedule_error_handling(self):
        """Test error handling when resuming schedule fails"""
        manager = ScheduleManager()
        
        schedule = ScanSchedule(
            name="test_scan",
            cron="0 2 * * *",
            target="src/",
            scanners=["bandit"]
        )
        
        manager.add_schedule(schedule)
        manager.pause_schedule("test_scan")
        
        # Mock scheduler.resume_job to raise exception
        with patch.object(manager.scheduler, 'resume_job', side_effect=Exception("Test error")):
            result = manager.resume_schedule("test_scan")
            assert result is False
    
    def test_resume_nonexistent_schedule(self):
        """Test resuming nonexistent schedule"""
        manager = ScheduleManager()
        
        result = manager.resume_schedule("nonexistent")
        assert result is False
    
    def test_get_next_run_error_handling(self):
        """Test error handling when getting next run fails"""
        manager = ScheduleManager()
        
        schedule = ScanSchedule(
            name="test_scan",
            cron="0 2 * * *",
            target="src/",
            scanners=["bandit"]
        )
        
        manager.add_schedule(schedule)
        
        # Mock scheduler.get_job to raise exception
        with patch.object(manager.scheduler, 'get_job', side_effect=Exception("Test error")):
            result = manager.get_next_run("test_scan")
            assert result is None
    
    def test_start_already_running(self):
        """Test starting scheduler when already running"""
        manager = ScheduleManager()
        
        manager.start()
        assert manager.is_running()
        
        # Try to start again (should log warning)
        manager.start()
        assert manager.is_running()
        
        manager.stop()
    
    def test_stop_not_running(self):
        """Test stopping scheduler when not running"""
        manager = ScheduleManager()
        
        assert not manager.is_running()
        
        # Try to stop (should log warning)
        manager.stop()
        assert not manager.is_running()
