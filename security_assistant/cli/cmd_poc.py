"""
PoC command implementation.

Generates proof-of-concept exploits:
- Exploit templates
- Payload generation
- Vulnerability reproduction
"""

from pathlib import Path

from security_assistant.ci.base import (
    get_logger,
    print_error,
    print_info,
    print_success,
)


def cmd_poc(args):
    """
    Generate proof-of-concept exploit code.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    try:
        from security_assistant.config import load_config
        from security_assistant.orchestrator import UnifiedFinding
        from security_assistant.poc_generator import POCGenerator
        
        # Load configuration
        config = load_config(config_file=args.config, use_env=not args.no_env)
        logger = get_logger(__name__)
        
        # Create POC generator
        generator = POCGenerator(config)
        
        # Load findings if needed
        findings = []
        if args.findings_file:
            findings_file = Path(args.findings_file)
            if not findings_file.exists():
                print_error(f"❌ Findings file not found: {args.findings_file}")
                return 1
            
            import json
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
            
            print_info(f"📋 Loaded {len(findings)} findings from {args.findings_file}")
        elif args.vulnerability:
            # Create manual finding
            finding = UnifiedFinding(
                finding_id="manual-1",
                scanner="manual",
                severity="HIGH",
                category="Security",
                file_path=args.file or "example.py",
                line_start=args.line or 10,
                line_end=args.line or 10,
                title=args.vulnerability,
                description="Manual security vulnerability description",
                fix_available=False,
                priority_score=90
            )
            findings.append(finding)
            print_info(f"📋 Created manual finding: {args.vulnerability}")
        
        if not findings:
            print_error("❌ No findings provided")
            print_info("Use --vulnerability, --file, or run scan first")
            return 1
        
        # Generate POCs
        print_info(f"🔧 Generating PoC exploits for {len(findings)} findings...")
        
        for finding in findings:
            try:
                poc_code = generator.generate_poc(finding, template=args.template)
                
                # Save to file
                safe_title = "".join(c for c in finding.title if c.isalnum() or c in "-_")[:50]
                poc_file = Path(config.report.output_dir) / f"poc_{finding.finding_id}_{safe_title}.py"
                poc_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(poc_file, "w") as f:
                    f.write(poc_code)
                
                print_info(f"  {finding.title} → {poc_file.name}")
                
            except Exception as e:
                logger.error(f"Failed to generate PoC for {finding.title}: {e}")
        
        print_success(f"✅ Generated {len(findings)} PoC exploits")
        return 0

    except Exception as e:
        logger = get_logger(__name__)
        print_error(f"❌ PoC generation failed: {e}")
        if args.verbose:
            logger.debug("Exception details:", exc_info=True)
        return 1
