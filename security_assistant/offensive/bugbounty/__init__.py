"""
Bug Bounty Integration Module

Provides integration with bug bounty platforms:
- HackerOne API
- Bugcrowd API
- Vulnerability submission
- Bounty tracking
- Reporting
"""

from security_assistant.offensive.bugbounty.bugcrowd import BugcrowdClient
from security_assistant.offensive.bugbounty.hackerone import HackerOneClient
from security_assistant.offensive.bugbounty.submission import BugBountySubmission
from security_assistant.offensive.bugbounty.tracking import BountyTracker

__all__ = [
    "HackerOneClient",
    "BugcrowdClient", 
    "BugBountySubmission",
    "BountyTracker"
]
