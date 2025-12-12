"""
CTF Challenge Mode

Gamified security challenges:
- Challenge management
- Leaderboard system
- Achievement tracking
- Progress monitoring
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from security_assistant.offensive.authorization import AuthorizationService

logger = logging.getLogger(__name__)


class CTFChallengeMode:
    """
    CTF challenge mode with gamification.
    
    Args:
        storage_path: Path to store challenge data
        auth_service: Authorization service for ToS checking
    """
    
    def __init__(
        self,
        storage_path: str = ".ctf_challenges",
        auth_service: Optional[AuthorizationService] = None
    ):
        self.storage_path = Path(storage_path)
        self.auth_service = auth_service or AuthorizationService()
        self.challenges = {}
        self.leaderboard = {}
        self.user_progress = {}
        
        # Load existing data
        self._load_data()
        
        logger.info("CTFChallengeMode initialized")
    
    def _load_data(self) -> None:
        """Load challenge data from storage."""
        if not self.storage_path.exists():
            return
        
        try:
            with open(self.storage_path) as f:
                data = json.load(f)
                self.challenges = data.get("challenges", {})
                self.leaderboard = data.get("leaderboard", {})
                self.user_progress = data.get("user_progress", {})
            
            logger.info(f"Loaded {len(self.challenges)} challenges and {len(self.leaderboard)} leaderboard entries")
        except Exception as e:
            logger.error(f"Failed to load CTF data: {e}")
    
    def _save_data(self) -> None:
        """Save challenge data to storage."""
        try:
            data = {
                "challenges": self.challenges,
                "leaderboard": self.leaderboard,
                "user_progress": self.user_progress,
                "updated_at": datetime.now().isoformat()
            }
            
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
            
            logger.info("Saved CTF challenge data")
        except Exception as e:
            logger.error(f"Failed to save CTF data: {e}")
    
    def create_challenge(
        self,
        challenge_id: str,
        title: str,
        description: str,
        category: str,
        difficulty: str,
        target_url: str,
        flags: List[str],
        points: int = 100,
        hints: Optional[List[str]] = None
    ) -> Dict[str, any]:
        """Create a new CTF challenge."""
        if not self.auth_service.check_tos_accepted():
            raise Exception("Must accept Terms of Service before creating CTF challenges")
        
        challenge = {
            "challenge_id": challenge_id,
            "title": title,
            "description": description,
            "category": category,
            "difficulty": difficulty,
            "target_url": target_url,
            "flags": flags,
            "points": points,
            "hints": hints or [],
            "created_at": datetime.now().isoformat(),
            "solved_by": [],
            "solvers": 0
        }
        
        self.challenges[challenge_id] = challenge
        self._save_data()
        
        logger.info(f"Created challenge: {title}")
        return challenge
    
    def list_challenges(
        self,
        category: Optional[str] = None,
        difficulty: Optional[str] = None
    ) -> List[Dict[str, any]]:
        """List available challenges."""
        challenges = list(self.challenges.values())
        
        if category:
            challenges = [c for c in challenges if c["category"] == category]
        
        if difficulty:
            challenges = [c for c in challenges if c["difficulty"] == difficulty]
        
        # Sort by difficulty and points
        challenges.sort(key=lambda x: (x["difficulty"], x["points"]))
        
        return challenges
    
    def get_challenge(self, challenge_id: str) -> Dict[str, any]:
        """Get challenge details."""
        if challenge_id not in self.challenges:
            raise ValueError(f"Challenge {challenge_id} not found")
        
        return self.challenges[challenge_id]
    
    def submit_flag(
        self,
        user_id: str,
        challenge_id: str,
        flag: str
    ) -> Dict[str, any]:
        """Submit flag for a challenge."""
        if challenge_id not in self.challenges:
            raise ValueError(f"Challenge {challenge_id} not found")
        
        challenge = self.challenges[challenge_id]
        
        # Check if flag is correct
        if flag not in challenge["flags"]:
            return {
                "success": False,
                "message": "Incorrect flag",
                "challenge_id": challenge_id
            }
        
        # Check if user already solved this challenge
        if user_id in challenge["solved_by"]:
            return {
                "success": False,
                "message": "Already solved",
                "challenge_id": challenge_id
            }
        
        # Update challenge
        challenge["solved_by"].append(user_id)
        challenge["solvers"] += 1
        
        # Update user progress
        if user_id not in self.user_progress:
            self.user_progress[user_id] = {
                "user_id": user_id,
                "points": 0,
                "challenges_solved": [],
                "join_date": datetime.now().isoformat()
            }
        
        user = self.user_progress[user_id]
        user["points"] += challenge["points"]
        user["challenges_solved"].append(challenge_id)
        
        # Update leaderboard
        if user_id not in self.leaderboard:
            self.leaderboard[user_id] = user["points"]
        else:
            self.leaderboard[user_id] += challenge["points"]
        
        self._save_data()
        
        logger.info(f"User {user_id} solved challenge {challenge_id}")
        
        return {
            "success": True,
            "message": "Flag accepted",
            "challenge_id": challenge_id,
            "points_earned": challenge["points"],
            "total_points": user["points"],
            "position": self.get_user_rank(user_id)
        }
    
    def get_user_progress(self, user_id: str) -> Dict[str, any]:
        """Get user progress."""
        if user_id not in self.user_progress:
            return {
                "user_id": user_id,
                "points": 0,
                "challenges_solved": [],
                "rank": "N/A"
            }
        
        user = self.user_progress[user_id]
        return {
            **user,
            "rank": self.get_user_rank(user_id)
        }
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, any]]:
        """Get leaderboard."""
        # Sort by points (descending)
        sorted_leaderboard = sorted(
            self.leaderboard.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        leaderboard = []
        for i, (user_id, points) in enumerate(sorted_leaderboard[:limit], 1):
            user = self.user_progress.get(user_id, {})
            leaderboard.append({
                "rank": i,
                "user_id": user_id,
                "points": points,
                "challenges_solved": len(user.get("challenges_solved", [])),
                "join_date": user.get("join_date", "Unknown")
            })
        
        return leaderboard
    
    def get_user_rank(self, user_id: str) -> int:
        """Get user rank."""
        if user_id not in self.leaderboard:
            return 0
        
        # Sort and find rank
        sorted_leaderboard = sorted(
            self.leaderboard.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for i, (uid, _) in enumerate(sorted_leaderboard, 1):
            if uid == user_id:
                return i
        
        return 0
    
    def get_user_stats(self, user_id: str) -> Dict[str, any]:
        """Get detailed user statistics."""
        if user_id not in self.user_progress:
            return self._get_empty_stats(user_id)
        
        user = self.user_progress[user_id]
        challenges_solved = user["challenges_solved"]
        
        # Get challenge details
        solved_challenges = []
        for challenge_id in challenges_solved:
            if challenge_id in self.challenges:
                challenge = self.challenges[challenge_id]
                solved_challenges.append({
                    "challenge_id": challenge_id,
                    "title": challenge["title"],
                    "category": challenge["category"],
                    "difficulty": challenge["difficulty"],
                    "points": challenge["points"],
                    "solved_at": challenge.get("solved_at", "Unknown")
                })
        
        # Calculate category stats
        category_stats = {}
        for challenge in solved_challenges:
            category = challenge["category"]
            category_stats[category] = category_stats.get(category, 0) + 1
        
        return {
            "user_id": user_id,
            "total_points": user["points"],
            "total_challenges": len(challenges_solved),
            "rank": self.get_user_rank(user_id),
            "join_date": user.get("join_date", "Unknown"),
            "categories": category_stats,
            "challenges": solved_challenges,
            "solved_by_difficulty": self._get_difficulty_stats(challenges_solved)
        }
    
    def _get_difficulty_stats(self, challenge_ids: List[str]) -> Dict[str, int]:
        """Get challenge difficulty statistics."""
        stats = {"easy": 0, "medium": 0, "hard": 0, "expert": 0}
        
        for challenge_id in challenge_ids:
            if challenge_id in self.challenges:
                difficulty = self.challenges[challenge_id]["difficulty"].lower()
                if difficulty in stats:
                    stats[difficulty] += 1
        
        return stats
    
    def _get_empty_stats(self, user_id: str) -> Dict[str, any]:
        """Get empty stats for new user."""
        return {
            "user_id": user_id,
            "total_points": 0,
            "total_challenges": 0,
            "rank": 0,
            "join_date": "Not joined",
            "categories": {},
            "challenges": [],
            "solved_by_difficulty": {"easy": 0, "medium": 0, "hard": 0, "expert": 0}
        }
    
    def create_achievement_system(self) -> Dict[str, any]:
        """Create achievement system."""
        achievements = {
            "beginner": {
                "name": "First Blood",
                "description": "Solve your first challenge",
                "points_required": 100,
                "reward": 50
            },
            "intermediate": {
                "name": "Challenge Master",
                "description": "Solve 5 challenges",
                "points_required": 500,
                "reward": 200
            },
            "advanced": {
                "name": "Elite Hacker",
                "description": "Solve 10 challenges across all categories",
                "points_required": 1000,
                "reward": 500
            },
            "expert": {
                "name": "Grand Master",
                "description": "Solve 20 challenges including 5 expert level",
                "points_required": 2000,
                "reward": 1000
            }
        }
        
        return achievements
    
    def generate_challenge_report(self, output_path: str = "ctf_report.json") -> str:
        """Generate challenge report."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_challenges": len(self.challenges),
            "total_users": len(self.user_progress),
            "total_points_awarded": sum(self.leaderboard.values()),
            "challenges_by_category": self._get_category_distribution(),
            "challenges_by_difficulty": self._get_difficulty_distribution(),
            "top_solvers": self.get_leaderboard(5),
            "challenges": list(self.challenges.values())
        }
        
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Generated CTF report: {output_path}")
        return output_path
    
    def _get_category_distribution(self) -> Dict[str, int]:
        """Get challenge category distribution."""
        dist = {}
        for challenge in self.challenges.values():
            category = challenge["category"]
            dist[category] = dist.get(category, 0) + 1
        return dist
    
    def _get_difficulty_distribution(self) -> Dict[str, int]:
        """Get challenge difficulty distribution."""
        dist = {"easy": 0, "medium": 0, "hard": 0, "expert": 0}
        for challenge in self.challenges.values():
            difficulty = challenge["difficulty"].lower()
            if difficulty in dist:
                dist[difficulty] += 1
        return dist
    
    def reset_challenge(self, challenge_id: str) -> Dict[str, any]:
        """Reset a challenge."""
        if challenge_id not in self.challenges:
            raise ValueError(f"Challenge {challenge_id} not found")
        
        challenge = self.challenges[challenge_id]
        challenge["solved_by"] = []
        challenge["solvers"] = 0
        
        # Remove from user progress
        for user_id in self.user_progress:
            if challenge_id in self.user_progress[user_id]["challenges_solved"]:
                self.user_progress[user_id]["challenges_solved"].remove(challenge_id)
                self.user_progress[user_id]["points"] -= challenge["points"]
        
        # Recalculate leaderboard
        self.leaderboard = {}
        for user_id, user in self.user_progress.items():
            self.leaderboard[user_id] = user["points"]
        
        self._save_data()
        
        logger.info(f"Reset challenge: {challenge_id}")
        return challenge
    
    def create_sample_challenges(self) -> List[Dict[str, any]]:
        """Create sample challenges for testing."""
        sample_challenges = [
            {
                "challenge_id": "sqli_101",
                "title": "Basic SQL Injection",
                "description": "Find the hidden database table",
                "category": "Web",
                "difficulty": "easy",
                "target_url": "http://vulnerable-lab/sqli?user_id=1",
                "flags": ["FLAG{SQLI_BASIC_101}", "FLAG{SQL_INJECTION}"],
                "points": 100,
                "hints": ["Try basic SQL injection techniques", "Look for UNION-based attacks"]
            },
            {
                "challenge_id": "xss_101",
                "title": "Reflected XSS",
                "description": "Execute JavaScript in the search field",
                "category": "Web",
                "difficulty": "medium",
                "target_url": "http://vulnerable-lab/search?q=test",
                "flags": ["FLAG{XSS_REFLECTED_101}", "FLAG{ALERT_SUCCESS}"],
                "points": 150,
                "hints": ["Try common XSS payloads", "Look for event handlers"]
            },
            {
                "challenge_id": "lfi_101",
                "title": "Local File Inclusion",
                "description": "Read the secret file",
                "category": "Web",
                "difficulty": "hard",
                "target_url": "http://vulnerable-lab/page?file=about",
                "flags": ["FLAG{LFI_READ_FILE}", "FLAG{SECRET_ACCESS}"],
                "points": 200,
                "hints": ["Try path traversal techniques", "Look for null byte attacks"]
            }
        ]
        
        created = []
        for challenge_data in sample_challenges:
            challenge = self.create_challenge(**challenge_data)
            created.append(challenge)
        
        self._save_data()
        return created
