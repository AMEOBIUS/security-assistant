"""
Bounty Tracking Module

Tracks bug bounty submissions and rewards:
- Submission status monitoring
- Bounty calculation
- Reward tracking
- Reporting and analytics
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from security_assistant.offensive.authorization import AuthorizationService

logger = logging.getLogger(__name__)


class BountyTracker:
    """
    Bug bounty tracker.
    
    Args:
        storage_path: Path to store tracking data
        auth_service: Authorization service for ToS checking
    """
    
    def __init__(
        self,
        storage_path: str = ".bounty_tracker",
        auth_service: Optional[AuthorizationService] = None
    ):
        self.storage_path = Path(storage_path)
        self.auth_service = auth_service or AuthorizationService()
        self.submissions = {}
        
        # Load existing data
        self._load_data()
        
        logger.info(f"BountyTracker initialized with {len(self.submissions)} tracked submissions")
    
    def _load_data(self) -> None:
        """Load tracking data from storage."""
        if not self.storage_path.exists():
            return
        
        try:
            with open(self.storage_path) as f:
                data = json.load(f)
                self.submissions = data.get("submissions", {})
            
            logger.info(f"Loaded {len(self.submissions)} submissions from storage")
        except Exception as e:
            logger.error(f"Failed to load bounty tracking data: {e}")
    
    def _save_data(self) -> None:
        """Save tracking data to storage."""
        try:
            data = {
                "submissions": self.submissions,
                "updated_at": datetime.now().isoformat()
            }
            
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved {len(self.submissions)} submissions to storage")
        except Exception as e:
            logger.error(f"Failed to save bounty tracking data: {e}")
    
    def track_submission(
        self,
        submission_id: str,
        platform: str,
        program: str,
        title: str,
        severity: str,
        status: str = "submitted",
        bounty_amount: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Track a new bug bounty submission."""
        if not self.auth_service.check_tos_accepted():
            raise Exception("Must accept Terms of Service before tracking bug bounty submissions")
        
        submission = {
            "submission_id": submission_id,
            "platform": platform,
            "program": program,
            "title": title,
            "severity": severity,
            "status": status,
            "bounty_amount": bounty_amount,
            "submitted_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.submissions[submission_id] = submission
        self._save_data()
        
        logger.info(f"Tracking submission {submission_id} on {platform}")
        return submission
    
    def update_status(
        self,
        submission_id: str,
        status: str,
        bounty_amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """Update submission status."""
        if submission_id not in self.submissions:
            raise ValueError(f"Submission {submission_id} not found")
        
        submission = self.submissions[submission_id]
        submission["status"] = status
        submission["updated_at"] = datetime.now().isoformat()
        
        if bounty_amount is not None:
            submission["bounty_amount"] = bounty_amount
        
        self._save_data()
        
        logger.info(f"Updated submission {submission_id} to status: {status}")
        return submission
    
    def add_note(self, submission_id: str, note: str) -> Dict[str, Any]:
        """Add note to submission."""
        if submission_id not in self.submissions:
            raise ValueError(f"Submission {submission_id} not found")
        
        submission = self.submissions[submission_id]
        notes = submission.get("notes", [])
        notes.append({
            "timestamp": datetime.now().isoformat(),
            "note": note
        })
        submission["notes"] = notes
        submission["updated_at"] = datetime.now().isoformat()
        
        self._save_data()
        
        logger.info(f"Added note to submission {submission_id}")
        return submission
    
    def get_submission(self, submission_id: str) -> Dict[str, Any]:
        """Get submission details."""
        if submission_id not in self.submissions:
            raise ValueError(f"Submission {submission_id} not found")
        
        return self.submissions[submission_id]
    
    def list_submissions(
        self,
        platform: Optional[str] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List tracked submissions with optional filters."""
        submissions = list(self.submissions.values())
        
        if platform:
            submissions = [s for s in submissions if s["platform"] == platform]
        
        if status:
            submissions = [s for s in submissions if s["status"] == status]
        
        if severity:
            submissions = [s for s in submissions if s["severity"] == severity]
        
        # Sort by updated_at (newest first)
        submissions.sort(key=lambda x: x["updated_at"], reverse=True)
        
        return submissions
    
    def get_stats(self) -> Dict[str, Any]:
        """Get bounty tracking statistics."""
        total_submissions = len(self.submissions)
        
        if total_submissions == 0:
            return {
                "total_submissions": 0,
                "total_bounties": 0,
                "average_bounty": 0,
                "by_platform": {},
                "by_severity": {},
                "by_status": {}
            }
        
        # Calculate statistics
        total_bounties = sum(
            s["bounty_amount"] for s in self.submissions.values() 
            if s.get("bounty_amount") is not None
        )
        
        bounty_count = sum(
            1 for s in self.submissions.values() 
            if s.get("bounty_amount") is not None
        )
        
        average_bounty = total_bounties / bounty_count if bounty_count > 0 else 0
        
        # By platform
        by_platform = {}
        for submission in self.submissions.values():
            platform = submission["platform"]
            by_platform[platform] = by_platform.get(platform, 0) + 1
        
        # By severity
        by_severity = {}
        for submission in self.submissions.values():
            severity = submission["severity"]
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        # By status
        by_status = {}
        for submission in self.submissions.values():
            status = submission["status"]
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            "total_submissions": total_submissions,
            "total_bounties": total_bounties,
            "average_bounty": average_bounty,
            "bounty_count": bounty_count,
            "by_platform": by_platform,
            "by_severity": by_severity,
            "by_status": by_status
        }
    
    def generate_report(self, output_path: str = "bounty_report.json") -> str:
        """Generate bounty tracking report."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "stats": self.get_stats(),
            "submissions": self.list_submissions()
        }
        
        output_path = Path(output_path)
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Generated bounty report: {output_path}")
        return str(output_path)
    
    def export_to_csv(self, output_path: str = "bounty_tracking.csv") -> str:
        """Export tracking data to CSV."""
        import csv
        
        output_path = Path(output_path)
        
        with open(output_path, "w", newline='') as f:
            fieldnames = [
                "submission_id", "platform", "program", "title", "severity",
                "status", "bounty_amount", "submitted_at", "updated_at"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            for submission in self.list_submissions():
                row = {key: submission.get(key, "") for key in fieldnames}
                writer.writerow(row)
        
        logger.info(f"Exported bounty tracking to CSV: {output_path}")
        return str(output_path)
    
    def clear_data(self) -> None:
        """Clear all tracking data."""
        self.submissions = {}
        self._save_data()
        logger.info("Cleared all bounty tracking data")
