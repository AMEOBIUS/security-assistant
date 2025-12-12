"""
Batch Fix Service.

Handles multiple fixes in a single MR.
"""

import logging
from pathlib import Path
from typing import Dict, List, Tuple

from security_assistant.integrations.gitlab_mr_creator import GitLabMRCreator
from security_assistant.orchestrator import UnifiedFinding
from security_assistant.services.fix_generator import FixGenerator
from security_assistant.services.test_generator import PytestTestGenerator

logger = logging.getLogger(__name__)


class BatchFixResult:
    """Result of batch fix operation."""
    
    def __init__(self):
        self.successful_fixes: List[Tuple[UnifiedFinding, str, str]] = []
        self.failed_fixes: List[Tuple[UnifiedFinding, Exception]] = []
        self.generated_tests: Dict[str, str] = {}
    
    @property
    def success_count(self) -> int:
        return len(self.successful_fixes)
    
    @property
    def failure_count(self) -> int:
        return len(self.failed_fixes)
    
    @property
    def total_count(self) -> int:
        return self.success_count + self.failure_count


class BatchFixService:
    """Handle batch fixing of multiple findings."""
    
    def __init__(
        self,
        fix_generator: FixGenerator,
        test_generator: PytestTestGenerator,
        mr_creator: GitLabMRCreator
    ):
        """
        Initialize batch fix service.
        
        Args:
            fix_generator: Fix generator instance
            test_generator: Test generator instance
            mr_creator: MR creator instance
        """
        self.fix_generator = fix_generator
        self.test_generator = test_generator
        self.mr_creator = mr_creator
    
    async def batch_fix(
        self,
        findings: List[UnifiedFinding],
        strategy: str = "safe",
        generate_tests: bool = False,
        dry_run: bool = False
    ) -> BatchFixResult:
        """
        Fix multiple findings.
        
        Args:
            findings: List of findings to fix
            strategy: Fix strategy
            generate_tests: Generate tests for fixes
            dry_run: Preview without applying
            
        Returns:
            BatchFixResult with success/failure info
        """
        result = BatchFixResult()
        
        for finding in findings:
            try:
                # Generate fix
                fixed_code, explanation = await self.fix_generator.generate_fix(
                    finding,
                    strategy
                )
                
                result.successful_fixes.append((finding, fixed_code, explanation))
                
                # Generate test if requested
                if generate_tests:
                    test_code, test_path = await self.test_generator.generate_test(
                        finding,
                        fixed_code
                    )
                    result.generated_tests[test_path] = test_code
                
            except Exception as e:
                logger.error(f"Failed to fix {finding.finding_id}: {e}")
                result.failed_fixes.append((finding, e))
        
        return result
    
    async def create_batch_mr(
        self,
        batch_result: BatchFixResult,
        category: str = "Security Fixes",
        dry_run: bool = False
    ) -> str:
        """
        Create single MR with all fixes.
        
        Args:
            batch_result: Result from batch_fix
            category: Category name for MR title
            dry_run: Preview without creating
            
        Returns:
            MR URL
        """
        if dry_run:
            logger.info(f"[DRY RUN] Would create MR with {batch_result.success_count} fixes")
            return ""
        
        # Create branch
        branch_name = f"security-fix/batch-{category.lower().replace(' ', '-')}"
        
        # Get current branch
        import subprocess
        current_branch = subprocess.run(
            ['git', 'branch', '--show-current'],
            capture_output=True,
            text=True,
            check=True
        ).stdout.strip()
        
        # Create branch
        subprocess.run(['git', 'checkout', '-b', branch_name], check=True)
        
        # Apply all fixes
        for finding, fixed_code, _explanation in batch_result.successful_fixes:
            Path(finding.file_path).write_text(fixed_code, encoding='utf-8')
        
        # Apply all tests
        for test_path, test_code in batch_result.generated_tests.items():
            Path(test_path).write_text(test_code, encoding='utf-8')
        
        # Commit
        commit_msg = self._generate_batch_commit_message(batch_result, category)
        subprocess.run(['git', 'add', '.'], check=True)
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
        
        # Push
        subprocess.run(['git', 'push', '-u', 'origin', branch_name], check=True)
        
        # Create MR
        title = f"Security: Fix {batch_result.success_count} {category}"
        description = self._generate_batch_mr_description(batch_result, category)
        
        result = subprocess.run(
            [
                'glab', 'mr', 'create',
                '--title', title,
                '--description', description,
                '--label', 'security',
                '--label', 'auto-fix',
                '--label', 'batch',
                '--source-branch', branch_name,
                '--target-branch', 'main'
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Return to original branch
        subprocess.run(['git', 'checkout', current_branch], check=True)
        
        # Extract MR URL
        for line in result.stdout.split('\n'):
            if 'https://' in line:
                return line.strip()
        
        return result.stdout.strip()
    
    def _generate_batch_commit_message(
        self,
        batch_result: BatchFixResult,
        category: str
    ) -> str:
        """Generate commit message for batch fix."""
        
        lines = [
            f"fix: {category} ({batch_result.success_count} fixes)",
            "",
            "Fixed findings:"
        ]
        
        for finding, _fixed_code, _explanation in batch_result.successful_fixes:
            lines.append(f"- {finding.finding_id}: {finding.title}")
        
        if batch_result.generated_tests:
            lines.append("")
            lines.append(f"Generated {len(batch_result.generated_tests)} tests")
        
        lines.extend([
            "",
            "Auto-generated by Security Assistant"
        ])
        
        return "\n".join(lines)
    
    def _generate_batch_mr_description(
        self,
        batch_result: BatchFixResult,
        category: str
    ) -> str:
        """Generate MR description for batch fix."""
        
        lines = [
            f"## Security Fixes: {category}",
            "",
            f"**Fixes Applied:** {batch_result.success_count}",
            f"**Tests Generated:** {len(batch_result.generated_tests)}",
            "",
            "### Fixed Vulnerabilities",
            ""
        ]
        
        for finding, _fixed_code, explanation in batch_result.successful_fixes:
            lines.extend([
                f"#### {finding.finding_id}: {finding.title}",
                f"- **Severity:** {finding.severity.value}",
                f"- **File:** `{finding.file_path}:{finding.line_start}`",
                f"- **Fix:** {explanation}",
                ""
            ])
        
        if batch_result.failed_fixes:
            lines.extend([
                "### Failed Fixes",
                ""
            ])
            for finding, error in batch_result.failed_fixes:
                lines.append(f"- {finding.finding_id}: {str(error)}")
            lines.append("")
        
        lines.extend([
            "### Checklist",
            "",
            "- [ ] All tests passing",
            "- [ ] Code review completed",
            "- [ ] No functionality broken",
            "- [ ] Security verified",
            "",
            "---",
            "",
            "🤖 *This MR was automatically generated by Security Assistant*"
        ])
        
        return "\n".join(lines)
