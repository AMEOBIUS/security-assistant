"""
Example: Scheduled Security Scans

This example demonstrates how to use the ScheduleManager to automate
security scans on a schedule.

Features demonstrated:
- Creating scan schedules with cron expressions
- Setting up scan callbacks
- Managing multiple schedules
- Starting/stopping the scheduler
- Getting schedule status
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from security_assistant.scheduler import ScheduleManager, ScanSchedule
from security_assistant.orchestrator import ScanOrchestrator
from security_assistant.report_generator import ReportGenerator, ReportFormat

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def scan_callback(schedule: ScanSchedule):
    """
    Callback function executed when a scheduled scan runs.
    
    Args:
        schedule: The ScanSchedule that triggered this execution
    """
    logger.info(f"Starting scheduled scan: {schedule.name}")
    logger.info(f"Target: {schedule.target}")
    logger.info(f"Scanners: {', '.join(schedule.scanners)}")
    
    try:
        # Create orchestrator
        orchestrator = ScanOrchestrator()
        
        # Enable requested scanners
        for scanner_name in schedule.scanners:
            orchestrator.enable_scanner(scanner_name)
        
        # Run scan
        logger.info(f"Scanning {schedule.target}...")
        result = orchestrator.scan_directory(schedule.target)
        
        # Log results
        logger.info(f"Scan complete: {result.total_findings} findings")
        logger.info(f"  Critical: {result.critical_count}")
        logger.info(f"  High: {result.high_count}")
        logger.info(f"  Medium: {result.medium_count}")
        logger.info(f"  Low: {result.low_count}")
        
        # Generate report
        report_dir = Path("reports") / "scheduled"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = report_dir / f"{schedule.name}_latest.html"
        
        generator = ReportGenerator()
        generator.generate_report(
            result,
            str(report_path),
            format=ReportFormat.HTML,
            title=f"Scheduled Scan: {schedule.name}"
        )
        
        logger.info(f"Report generated: {report_path}")
        
        # Send notifications if configured
        if schedule.notification_emails:
            logger.info(f"Would send email to: {', '.join(schedule.notification_emails)}")
            # TODO: Implement email notification
        
        if schedule.notification_webhooks:
            logger.info(f"Would send webhook to: {', '.join(schedule.notification_webhooks)}")
            # TODO: Implement webhook notification
        
    except Exception as e:
        logger.error(f"Scan failed: {e}", exc_info=True)
        raise


def example_1_basic_schedule():
    """Example 1: Basic daily scan schedule"""
    print("\n" + "="*70)
    print("Example 1: Basic Daily Scan Schedule")
    print("="*70)
    
    # Create schedule manager
    manager = ScheduleManager()
    
    # Set scan callback
    manager.set_scan_callback(scan_callback)
    
    # Create a daily scan schedule (2 AM UTC)
    schedule = ScanSchedule(
        name="daily_scan",
        cron="0 2 * * *",  # 2 AM daily
        target="security_assistant/",
        scanners=["bandit", "semgrep"]
    )
    
    # Add schedule
    manager.add_schedule(schedule)
    
    # Get next run time
    next_run = manager.get_next_run("daily_scan")
    print(f"\nSchedule created: {schedule.name}")
    print(f"Cron: {schedule.cron}")
    print(f"Next run: {next_run}")
    
    # Get status
    status = manager.get_status()
    print(f"\nScheduler status:")
    print(f"  Running: {status['running']}")
    print(f"  Total schedules: {status['total_schedules']}")
    
    # Clean up
    manager.stop()


def example_2_multiple_schedules():
    """Example 2: Multiple scan schedules"""
    print("\n" + "="*70)
    print("Example 2: Multiple Scan Schedules")
    print("="*70)
    
    manager = ScheduleManager()
    manager.set_scan_callback(scan_callback)
    
    # Quick scan every 6 hours
    quick_scan = ScanSchedule(
        name="quick_scan",
        cron="0 */6 * * *",  # Every 6 hours
        target="security_assistant/",
        scanners=["bandit"]
    )
    
    # Full scan weekly (Sunday 2 AM)
    full_scan = ScanSchedule(
        name="full_scan",
        cron="0 2 * * 0",  # Sunday 2 AM
        target=".",
        scanners=["bandit", "semgrep", "trivy"]
    )
    
    # Add schedules
    manager.add_schedule(quick_scan)
    manager.add_schedule(full_scan)
    
    # List all schedules
    print("\nConfigured schedules:")
    for schedule in manager.list_schedules():
        next_run = manager.get_next_run(schedule.name)
        print(f"\n  {schedule.name}:")
        print(f"    Cron: {schedule.cron}")
        print(f"    Target: {schedule.target}")
        print(f"    Scanners: {', '.join(schedule.scanners)}")
        print(f"    Next run: {next_run}")
    
    manager.stop()


def example_3_with_notifications():
    """Example 3: Schedule with notifications"""
    print("\n" + "="*70)
    print("Example 3: Schedule with Notifications")
    print("="*70)
    
    manager = ScheduleManager()
    manager.set_scan_callback(scan_callback)
    
    # Production scan with notifications
    schedule = ScanSchedule(
        name="production_scan",
        cron="0 3 * * *",  # 3 AM daily
        target="security_assistant/",
        scanners=["bandit", "semgrep"],
        min_severity="HIGH",
        notification_emails=["security@example.com", "devops@example.com"],
        notification_webhooks=["https://hooks.slack.com/services/YOUR/WEBHOOK/URL"]
    )
    
    manager.add_schedule(schedule)
    
    print(f"\nSchedule created: {schedule.name}")
    print(f"Notifications:")
    print(f"  Emails: {', '.join(schedule.notification_emails)}")
    print(f"  Webhooks: {', '.join(schedule.notification_webhooks)}")
    
    manager.stop()


def example_4_pause_resume():
    """Example 4: Pause and resume schedules"""
    print("\n" + "="*70)
    print("Example 4: Pause and Resume Schedules")
    print("="*70)
    
    manager = ScheduleManager()
    manager.set_scan_callback(scan_callback)
    
    schedule = ScanSchedule(
        name="test_scan",
        cron="0 2 * * *",
        target="security_assistant/",
        scanners=["bandit"]
    )
    
    manager.add_schedule(schedule)
    print(f"\nSchedule added: {schedule.name}")
    
    # Pause schedule
    manager.pause_schedule("test_scan")
    print("Schedule paused")
    
    # Resume schedule
    manager.resume_schedule("test_scan")
    print("Schedule resumed")
    
    manager.stop()


def example_5_update_schedule():
    """Example 5: Update existing schedule"""
    print("\n" + "="*70)
    print("Example 5: Update Existing Schedule")
    print("="*70)
    
    manager = ScheduleManager()
    manager.set_scan_callback(scan_callback)
    
    # Original schedule
    schedule = ScanSchedule(
        name="test_scan",
        cron="0 2 * * *",
        target="security_assistant/",
        scanners=["bandit"]
    )
    
    manager.add_schedule(schedule)
    print(f"\nOriginal schedule:")
    print(f"  Cron: {schedule.cron}")
    print(f"  Scanners: {', '.join(schedule.scanners)}")
    
    # Update schedule
    updated_schedule = ScanSchedule(
        name="test_scan",
        cron="0 3 * * *",  # Changed time
        target="security_assistant/",
        scanners=["bandit", "semgrep"]  # Added scanner
    )
    
    manager.update_schedule(updated_schedule)
    print(f"\nUpdated schedule:")
    print(f"  Cron: {updated_schedule.cron}")
    print(f"  Scanners: {', '.join(updated_schedule.scanners)}")
    
    manager.stop()


def example_6_context_manager():
    """Example 6: Using scheduler as context manager"""
    print("\n" + "="*70)
    print("Example 6: Context Manager Usage")
    print("="*70)
    
    schedule = ScanSchedule(
        name="test_scan",
        cron="0 2 * * *",
        target="security_assistant/",
        scanners=["bandit"]
    )
    
    # Use context manager for automatic start/stop
    with ScheduleManager() as manager:
        manager.set_scan_callback(scan_callback)
        manager.add_schedule(schedule)
        
        print(f"\nScheduler running: {manager.is_running()}")
        print(f"Schedules: {len(manager.list_schedules())}")
    
    print("Scheduler automatically stopped")


def example_7_manual_trigger():
    """Example 7: Manually trigger a scheduled scan"""
    print("\n" + "="*70)
    print("Example 7: Manual Trigger")
    print("="*70)
    
    manager = ScheduleManager()
    manager.set_scan_callback(scan_callback)
    
    schedule = ScanSchedule(
        name="test_scan",
        cron="0 2 * * *",
        target="security_assistant/",
        scanners=["bandit"]
    )
    
    print("\nManually triggering scan...")
    
    # Manually execute scan (without adding to scheduler)
    try:
        scan_callback(schedule)
        print("Scan completed successfully")
    except Exception as e:
        print(f"Scan failed: {e}")
    
    manager.stop()


def example_8_schedule_persistence():
    """Example 8: Save and load schedules"""
    print("\n" + "="*70)
    print("Example 8: Schedule Persistence")
    print("="*70)
    
    # Create schedule
    schedule = ScanSchedule(
        name="daily_scan",
        cron="0 2 * * *",
        target="security_assistant/",
        scanners=["bandit", "semgrep"],
        notification_emails=["security@example.com"]
    )
    
    # Save to JSON
    json_str = schedule.to_json()
    print("\nSchedule as JSON:")
    print(json_str)
    
    # Load from JSON
    loaded_schedule = ScanSchedule.from_json(json_str)
    print(f"\nLoaded schedule: {loaded_schedule.name}")
    print(f"Cron: {loaded_schedule.cron}")
    print(f"Scanners: {', '.join(loaded_schedule.scanners)}")


def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("Scheduled Security Scans Examples")
    print("="*70)
    
    try:
        example_1_basic_schedule()
        example_2_multiple_schedules()
        example_3_with_notifications()
        example_4_pause_resume()
        example_5_update_schedule()
        example_6_context_manager()
        # example_7_manual_trigger()  # Commented out - actually runs scan
        example_8_schedule_persistence()
        
        print("\n" + "="*70)
        print("All examples completed successfully!")
        print("="*70)
        
    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
