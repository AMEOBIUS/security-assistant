"""
GitLab Merge Request Creator.

Automates creation of MRs for security fixes.
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional

from security_assistant.orchestrator import UnifiedFinding

logger = logging.getLogger(__name__)


class GitLabMRCreator:
    """Create GitLab Merge Requests for fixes."""
    
    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize MR creator.
        
        Args:
            project_id: GitLab project ID (auto-detected if None)
        """
        self.project_id = project_id or self._detect_project_id()
    
    def _detect_project_id(self) -> str:
        """
        Detect GitLab project ID from git remote.
        
        Returns:
            Project ID (namespace/project)
        """
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                capture_output=True,
                text=True,
                check=True
            )
            remote_url = result.stdout.strip()
            
            # Parse gitlab.com/namespace/project
            if 'gitlab.com' in remote_url:
                parts = remote_url.split('gitlab.com/')[-1]
                parts = parts.replace('.git', '')
                return parts
            
            logger.warning("Not a GitLab repository")
            return ""
        except Exception as e:
            logger.warning(f"Could not detect project ID: {e}")
            return ""
    
    async def create_fix_mr(
        self,
        finding: UnifiedFinding,
        fixed_code: str,
        explanation: str,
        dry_run: bool = False
    ) -> Optional[str]:
        """
        Create MR with fix.
        
        Args:
            finding: The finding being fixed
            fixed_code: Fixed code content
            explanation: Explanation of the fix
            dry_run: If True, don't actually create MR
            
        Returns:
            MR URL if created, None otherwise
        """
        # Create branch name
        branch_name = f"security-fix/{finding.finding_id.lower().replace('_', '-')}"
        
        if dry_run:
            logger.info(f"[DRY RUN] Would create branch: {branch_name}")
            logger.info(f"[DRY RUN] Would update file: {finding.file_path}")
            logger.info("[DRY RUN] Would create MR")
            logger.info(f"[DRY RUN] Explanation: {explanation}")
            return None
        
        try:
            # Save current branch
            current_branch = self._get_current_branch()
            
            # Create branch
            self._create_branch(branch_name)
            
            # Apply fix
            self._apply_fix(finding.file_path, fixed_code)
            
            # Commit
            commit_msg = self._generate_commit_message(finding, explanation)
            self._commit_changes(commit_msg)
            
            # Push
            self._push_branch(branch_name)
            
            # Create MR
            mr_url = self._create_mr(
                branch_name,
                finding,
                explanation
            )
            
            # Return to original branch
            self._checkout_branch(current_branch)
            
            return mr_url
            
        except Exception as e:
            logger.error(f"Failed to create MR: {e}")
            # Try to return to original branch
            try:
                self._checkout_branch(current_branch)
            except Exception:
                pass
            raise
    
    def _get_current_branch(self) -> str:
        """Get current git branch."""
        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    
    def _create_branch(self, branch_name: str):
        """Create git branch."""
        subprocess.run(['git', 'checkout', '-b', branch_name], check=True)
        logger.info(f"Created branch: {branch_name}")
    
    def _checkout_branch(self, branch_name: str):
        """Checkout existing branch."""
        subprocess.run(['git', 'checkout', branch_name], check=True)
        logger.info(f"Checked out branch: {branch_name}")
    
    def _apply_fix(self, file_path: str, fixed_code: str):
        """Apply fix to file."""
        Path(file_path).write_text(fixed_code, encoding='utf-8')
        logger.info(f"Applied fix to: {file_path}")
    
    def _commit_changes(self, message: str):
        """Commit changes."""
        subprocess.run(['git', 'add', '.'], check=True)
        subprocess.run(['git', 'commit', '-m', message], check=True)
        logger.info("Committed changes")
    
    def _push_branch(self, branch_name: str):
        """Push branch to remote."""
        subprocess.run(
            ['git', 'push', '-u', 'origin', branch_name],
            check=True
        )
        logger.info(f"Pushed branch: {branch_name}")
    
    def _create_mr(
        self,
        branch_name: str,
        finding: UnifiedFinding,
        explanation: str
    ) -> str:
        """
        Create GitLab MR using glab CLI.
        
        Args:
            branch_name: Source branch
            finding: Security finding
            explanation: Fix explanation
            
        Returns:
            MR URL
        """
        title = f"🔒 Fix {finding.severity}: {finding.title}"
        description = self._generate_mr_description(finding, explanation)
        
        # Use glab CLI
        result = subprocess.run(
            [
                'glab', 'mr', 'create',
                '--title', title,
                '--description', description,
                '--label', 'security',
                '--label', 'auto-fix',
                '--source-branch', branch_name,
                '--target-branch', 'main'
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Extract MR URL from output
        output = result.stdout.strip()
        for line in output.split('\n'):
            if 'https://' in line:
                return line.strip()
        
        return output
    
    def _generate_commit_message(
        self,
        finding: UnifiedFinding,
        explanation: str
    ) -> str:
        """Generate commit message."""
        return f"""fix: {finding.title}

Severity: {finding.severity}
Scanner: {finding.scanner}
File: {finding.file_path}:{finding.line_start}

{explanation}

Auto-generated by Security Assistant
Finding ID: {finding.finding_id}
"""
    
    def _generate_mr_description(
        self,
        finding: UnifiedFinding,
        explanation: str
    ) -> str:
        """Generate MR description."""
        return f"""## 🔒 Security Fix: {finding.title}

**Severity:** {finding.severity}  
**Scanner:** {finding.scanner}  
**Category:** {finding.category}  
**File:** `{finding.file_path}:{finding.line_start}`

### 📋 Vulnerability Description

{finding.description}

### 🛠️ Fix Applied

{explanation}

### ✅ Checklist

- [ ] Code review completed
- [ ] Tests passing
- [ ] No functionality broken
- [ ] Security verified

---

🤖 *This MR was automatically generated by Security Assistant*  
Finding ID: `{finding.finding_id}`
"""
