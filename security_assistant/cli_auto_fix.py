"""
Auto-fix command for CLI.
"""

import asyncio
import json
import logging
from pathlib import Path

from security_assistant.config import load_config
from security_assistant.integrations.gitlab_mr_creator import GitLabMRCreator
from security_assistant.orchestrator import ScannerType, UnifiedFinding
from security_assistant.services.fix_generator import FixGenerator
from security_assistant.services.llm_service import LLMService


def cmd_auto_fix(args) -> int:
    """
    Auto-fix findings and create MR.

    Args:
        args: Command-line arguments

    Returns:
        Exit code
    """
    try:
        # Load config
        config = load_config(config_file=args.config, use_env=True)
        
        # Initialize services
        llm_service = LLMService(config)
        fix_generator = FixGenerator(llm_service)
        mr_creator = GitLabMRCreator()
        
        # Check LLM availability
        if not asyncio.run(llm_service.is_available()):
            logging.error("LLM service not available. Configure SA_LLM__* environment variables.")
            logging.error(f"Current provider: {config.llm.provider}")
            return 1
        
        # Load findings
        report_path = Path(args.report)
        if not report_path.exists():
            logging.error(f"Report not found: {report_path}")
            return 1
        
        with open(report_path, encoding="utf-8") as f:
            data = json.load(f)
        
        # Find target finding
        target_finding = None
        
        # Try to find in results array
        if "results" in data and isinstance(data["results"], list):
            for result in data.get('results', []):
                for f in result.get('findings', []):
                    if f.get('id') == args.finding_id or f.get('finding_id') == args.finding_id:
                        target_finding = UnifiedFinding(
                            finding_id=f.get('id') or f.get('finding_id'),
                            scanner=ScannerType(f.get('scanner', 'bandit')),
                            severity=f.get('severity', 'MEDIUM'),
                            category=f.get('category', 'security'),
                            file_path=f.get('file', f.get('file_path', '')),
                            line_start=f.get('line_start', 0),
                            line_end=f.get('line_end', 0),
                            title=f.get('title', ''),
                            description=f.get('description', ''),
                            code_snippet=f.get('code_snippet', '')
                        )
                        break
                if target_finding:
                    break
        
        # Try flat findings array
        if not target_finding and "findings" in data:
            for f in data.get('findings', []):
                if f.get('id') == args.finding_id or f.get('finding_id') == args.finding_id:
                    target_finding = UnifiedFinding(
                        finding_id=f.get('id') or f.get('finding_id'),
                        scanner=ScannerType(f.get('scanner', 'bandit')),
                        severity=f.get('severity', 'MEDIUM'),
                        category=f.get('category', 'security'),
                        file_path=f.get('file', f.get('file_path', '')),
                        line_start=f.get('line_start', 0),
                        line_end=f.get('line_end', 0),
                        title=f.get('title', ''),
                        description=f.get('description', ''),
                        code_snippet=f.get('code_snippet', '')
                    )
                    break
        
        if not target_finding:
            logging.error(f"Finding not found: {args.finding_id}")
            logging.info("Available findings:")
            
            # List available findings
            if "results" in data:
                for result in data.get('results', []):
                    for f in result.get('findings', []):
                        print(f"  - {f.get('id', f.get('finding_id'))}: {f.get('title')}")
            elif "findings" in data:
                for f in data.get('findings', []):
                    print(f"  - {f.get('id', f.get('finding_id'))}: {f.get('title')}")
            
            return 1
        
        # Generate fix
        print("\nGenerating fix for: " + target_finding.title)
        print("File: " + target_finding.file_path + ":" + str(target_finding.line_start))
        print("Severity: " + str(target_finding.severity))
        print("Strategy: " + args.strategy + "\n")
        
        fixed_code, explanation = asyncio.run(
            fix_generator.generate_fix(target_finding, args.strategy)
        )
        
        print("Fix generated!\n")
        print("="*50)
        print("EXPLANATION:")
        print("="*50)
        print(explanation)
        print("="*50 + "\n")
        
        if args.dry_run:
            print("[DRY RUN] Fix preview:")
            print("="*50)
            print(fixed_code)
            print("="*50)
            print("\n[DRY RUN] No changes made. Use --create-mr to apply fix.")
            return 0
        
        # Create MR
        if args.create_mr:
            print("\nCreating GitLab MR...")
            mr_url = asyncio.run(
                mr_creator.create_fix_mr(
                    target_finding,
                    fixed_code,
                    explanation,
                    dry_run=args.dry_run
                )
            )
            
            if mr_url:
                print(f"MR created: {mr_url}")
            else:
                print("MR creation completed")
        else:
            # Just apply fix locally
            print("\nApplying fix to " + target_finding.file_path + "...")
            Path(target_finding.file_path).write_text(fixed_code, encoding='utf-8')
            print("Fix applied! Review changes and commit manually.")
        
        return 0
        
    except FileNotFoundError as e:
        logging.error(f"Error: {e}")
        return 1
    except ValueError as e:
        logging.error(f"Invalid LLM response: {e}")
        return 1
    except Exception as e:
        logging.error(f"Auto-fix failed: {e}")
        if hasattr(args, 'verbose') and args.verbose:
            logging.exception("Exception details:")
        return 1
