"""
Explain command implementation.

AI-powered security finding explanations:
- Natural language explanations
- Remediation guidance
- Impact assessment
"""

import json
from pathlib import Path

try:
    import asyncio
except ImportError:
    asyncio = None

from security_assistant.ci.base import (
    get_logger,
    print_error,
    print_info,
    print_success,
)
from security_assistant.config import load_config
from security_assistant.orchestrator import UnifiedFinding
from security_assistant.services.llm_service import LLMService


def cmd_explain(args):
    """
    Explain security findings using AI.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    try:
        # Load configuration
        config = load_config()
        logger = get_logger(__name__)
        
        # Initialize LLM service
        llm_service = LLMService(config)
        if not asyncio or not asyncio.run(llm_service.is_available()):
            print_error("❌ AI service not available")
            print_info("Please configure LLM provider and API key in config")
            return 1
        
        print_info(f"🤖 AI explanations enabled (Provider: {config.llm.provider})")
        
        # Load findings
        findings = []
        if args.findings_file:
            findings_file = Path(args.findings_file)
            if not findings_file.exists():
                print_error(f"❌ Findings file not found: {args.findings_file}")
                return 1
            
            with open(findings_file) as f:
                findings_data = json.load(f)
            
            # Convert data to UnifiedFinding objects
            for target_result in findings_data.get("results", []):
                for finding_data in target_result.get("findings", []):
                    finding = UnifiedFinding(
                        finding_id=finding_data["id"],
                        scanner=finding_data["scanner"],
                        severity=finding_data["severity"],
                        category=finding_data["category"],
                        file_path=finding_data["file"],
                        line_start=finding_data["line_start"],
                        line_end=finding_data["line_end"],
                        title=finding_data["title"],
                        description=finding_data["description"],
                        priority_score=finding_data["priority_score"],
                        cwe_ids=finding_data.get("cwe_ids", []),
                        owasp_categories=finding_data.get("owasp_categories", []),
                        fix_available=finding_data.get("fix_available", False)
                    )
                    findings.append(finding)
        
        elif args.finding:
            # Create manual finding for explanation
            finding = UnifiedFinding(
                finding_id="manual-1",
                scanner="manual",
                severity=args.severity or "HIGH",
                category="Security",
                file_path=args.file or "example.py",
                line_start=args.line or 10,
                line_end=args.line or 10,
                title=args.finding,
                description=f"Manual finding explanation for: {args.finding}",
                fix_available=False,
                priority_score=80
            )
            findings.append(finding)
        
        elif args.vulnerability:
            # Parse vulnerability string into finding
            parts = args.vulnerability.split(":")
            title = parts[0] if len(parts) > 1 else "Security Vulnerability"
            file_path = parts[1] if len(parts) > 1 else "example.py"
            line_start = int(parts[2]) if len(parts) > 2 else 0
            
            finding = UnifiedFinding(
                finding_id="manual-1",
                scanner="manual",
                severity=args.severity or "HIGH",
                category="Security",
                file_path=file_path,
                line_start=line_start,
                line_end=line_start,
                title=title,
                description=f"Manual vulnerability: {args.vulnerability}",
                fix_available=False,
                priority_score=85
            )
            findings.append(finding)
        
        if not findings:
            print_error("❌ No findings provided for explanation")
            print_info("Use --findings, --file, --vulnerability, or run scan first")
            return 1
        
        # Explain findings
        print_info(f"🧠 Explaining {len(findings)} findings with AI...")
        
        for i, finding in enumerate(findings[:args.limit if args.limit else len(findings)], 1):
            print(f"\n{i}. {finding.title} ({finding.severity.value})")
            print(f"   File: {finding.file_path}:{finding.line_start}")
            print("-" * 40)
            
            try:
                explanation = asyncio.run(llm_service.explain_finding(finding))
                print(explanation)
                print("-" * 50)
                
                if args.save:
                    # Save explanation to file
                    safe_title = "".join(c for c in finding.title if c.isalnum() or c in "-_")[:30]
                    expl_file = Path(config.report.output_dir) / f"explanation_{finding.finding_id}_{safe_title}.txt"
                    expl_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(expl_file, "w") as f:
                        f.write(f"Finding: {finding.title}\n")
                        f.write(f"File: {finding.file_path}\n")
                        f.write(f"Line: {finding.line_start}\n")
                        f.write(f"Severity: {finding.severity.value}\n")
                        f.write("\n" + "=" * 50 + "\n")
                        f.write(explanation)
                    print_info(f"    Saved to: {expl_file.name}")
                
            except Exception as e:
                logger.error(f"Failed to explain {finding.title}: {e}")
        
        print_success(f"✅ Explained {len(findings)} findings")
        return 0

    except Exception as e:
        logger = get_logger(__name__)
        print_error(f"❌ Explanation failed: {e}")
        if args.verbose:
            logger.debug("Exception details:", exc_info=True)
        return 1
