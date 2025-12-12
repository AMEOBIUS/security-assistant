"""
Scan command implementation.

Handles security scanning functionality:
- Target processing
- Configuration management
- Scanner orchestration
- Report generation
"""

import json
import webbrowser
from pathlib import Path

try:
    import asyncio
except ImportError:
    asyncio = None

from security_assistant.ci.base import get_logger
from security_assistant.cli.base import print_error, print_success
from security_assistant.config import LLMProvider, ReportFormat, load_config
from security_assistant.orchestrator import (
    ScannerType,
    ScanOrchestrator,
)
from security_assistant.report_generator import ReportGenerator
from security_assistant.scanners.bandit_scanner import BanditScanner
from security_assistant.scanners.nuclei_scanner import NucleiScanner
from security_assistant.scanners.semgrep_scanner import SemgrepScanner
from security_assistant.scanners.trivy_scanner import TrivyScanner
from security_assistant.services.llm_service import LLMService


def cmd_scan(args):
    """
    Execute security scan.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    try:
        # Load configuration
        config = load_config(config_file=args.config, use_env=not args.no_env)

        # Override LLM settings
        if getattr(args, 'llm', None):
            config.llm.provider = LLMProvider(args.llm)

        # Determine targets
        targets = []
        if args.targets_file:
            path = Path(args.targets_file)
            if not path.exists():
                print_error(f"Targets file not found: {args.targets_file}")
                return 1
            with open(path) as f:
                targets = [
                    line.strip()
                    for line in f
                    if line.strip() and not line.startswith("#")
                ]

        # Add CLI targets
        if args.target:
            if isinstance(args.target, list):
                targets.extend(args.target)
            else:
                targets.append(args.target)

        # Remove duplicates and defaults if multiple inputs
        if not targets:
            targets = ["."]

        # Deduplicate
        targets = list(set(targets))

        # Update config (primary target is the first one for single-target legacy support)
        config.scan_target = targets[0]

        if args.verbose:
            config.verbose = True
        if args.output_dir:
            config.report.output_dir = args.output_dir

        # Scanner enablement from CLI
        if args.bandit_only or args.semgrep_only or args.trivy_only or args.nuclei_only:
            config.bandit.enabled = args.bandit_only or False
            config.semgrep.enabled = args.semgrep_only or False
            config.trivy.enabled = args.trivy_only or False
            config.nuclei.enabled = args.nuclei_only or False
        else:
            if args.no_bandit:
                config.bandit.enabled = False
            if args.no_semgrep:
                config.semgrep.enabled = False
            if args.no_trivy:
                config.trivy.enabled = False
            if args.no_nuclei:
                config.nuclei.enabled = False

        # Deduplication strategy
        if args.dedup:
            config.orchestrator.deduplication_strategy = args.dedup

        # Presets
        if args.preset == "quick":
            # Bandit only, no expensive analysis
            config.bandit.enabled = True
            config.semgrep.enabled = False
            config.trivy.enabled = False
            config.nuclei.enabled = False
            args.no_reachability = True
            args.no_kev = True
            args.no_fp_detection = True
        elif args.preset == "full":
            # All enabled
            config.bandit.enabled = True
            config.semgrep.enabled = True
            config.trivy.enabled = True
            config.nuclei.enabled = True
            # Ensure analysis features are on (unless explicitly disabled)
            if not args.no_reachability:
                args.no_reachability = False
            if not args.no_kev:
                args.no_kev = False
            if not args.no_fp_detection:
                args.no_fp_detection = False
        elif args.preset == "ci":
            # Optimized for CI/CD
            config.report.formats = [ReportFormat.SARIF, ReportFormat.JSON]
            config.thresholds.fail_on_critical = True
            # Use what's configured or default

        # Report formats
        if args.format:
            formats = [ReportFormat(f.strip()) for f in args.format.split(",")]
            config.report.formats = formats

        # Thresholds
        if args.fail_on_critical is not None:
            config.thresholds.fail_on_critical = args.fail_on_critical
        if args.fail_on_high is not None:
            config.thresholds.fail_on_high = args.fail_on_high

        # Setup logging
        from security_assistant.cli.base import setup_logging
        setup_logging(config.verbose, config.log_file)
        logger = get_logger(__name__)

        logger.info("🔒 Security Assistant v1.0.0")
        logger.info("Scan target: %s", config.scan_target)

        # Create output directory
        output_dir = Path(config.report.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize LLM Service (for AI features)
        llm_service = None
        try:
            temp_llm = LLMService(config)
            if asyncio and asyncio.run(temp_llm.is_available()):
                llm_service = temp_llm
                logger.info(f"✓ AI features enabled (Provider: {config.llm.provider})")
        except Exception as e:
            logger.warning(f"Failed to initialize AI features: {e}")

        # Initialize orchestrator
        dedup_strat = config.orchestrator.deduplication_strategy
        dedup_val = str(dedup_strat)

        orchestrator = ScanOrchestrator(
            dedup_strategy=dedup_val,
            max_workers=config.orchestrator.max_workers,
            enable_kev=not args.no_kev,
            enable_fp_detection=not args.no_fp_detection,
            enable_reachability=not args.no_reachability,
            llm_service=llm_service,
        )

        # Enable scanners
        enabled_scanners = []

        if config.bandit.enabled:
            logger.info("✓ Enabling Bandit scanner")
            orchestrator.enable_scanner(ScannerType.BANDIT, BanditScanner())
            enabled_scanners.append("Bandit")

        if config.semgrep.enabled:
            logger.info("✓ Enabling Semgrep scanner")
            orchestrator.enable_scanner(ScannerType.SEMGREP, SemgrepScanner())
            enabled_scanners.append("Semgrep")

        if config.trivy.enabled:
            logger.info("✓ Enabling Trivy scanner")
            orchestrator.enable_scanner(ScannerType.TRIVY, TrivyScanner())
            enabled_scanners.append("Trivy")

        if config.nuclei.enabled:
            logger.info("✓ Enabling Nuclei scanner")
            orchestrator.enable_scanner(ScannerType.NUCLEI, NucleiScanner())
            enabled_scanners.append("Nuclei")

        if not enabled_scanners:
            logger.error("❌ No scanners enabled")
            return 1

        logger.info("Enabled scanners: %s", ", ".join(enabled_scanners))

        # Run scan
        if len(targets) == 1:
            target_path = Path(targets[0])
            logger.info("🔍 Starting security scan of %s...", targets[0])

            if target_path.is_file():
                result = orchestrator.scan_file(targets[0])
            else:
                result = orchestrator.scan_directory(targets[0])

            # Wrap in list for consistent reporting
            results = [result]
            total_findings_count = len(result.all_findings)
            dedup_count = len(result.deduplicated_findings)
            exec_time = result.execution_time_seconds
            findings_by_severity = result.findings_by_severity
        else:
            # Bulk scan
            logger.info("🔍 Starting bulk security scan of %d targets...", len(targets))
            bulk_result = orchestrator.scan_multiple_targets(targets)

            # Aggregate stats
            results = list(bulk_result.results.values())
            total_findings_count = bulk_result.total_findings
            dedup_count = sum(len(r.deduplicated_findings) for r in results)
            exec_time = bulk_result.total_execution_time

            # Aggregate severity
            findings_by_severity = {}
            for r in results:
                for sev, count in r.findings_by_severity.items():
                    findings_by_severity[sev] = findings_by_severity.get(sev, 0) + count

        # Save results
        results_file = output_dir / "scan-results.json"

        results_data = {
            "total_findings": total_findings_count,
            "deduplicated_findings": dedup_count,
            "execution_time": exec_time,
            "findings_by_severity": dict(findings_by_severity),
            "targets": targets,
            "results": [],
        }

        for result in results:
            target_data = {
                "target": result.target,
                "findings": [
                    {
                        "id": f.finding_id,
                        "scanner": f.scanner,
                        "severity": f.severity.value,
                        "category": f.category,
                        "file": f.file_path,
                        "line_start": f.line_start,
                        "line_end": f.line_end,
                        "title": f.title,
                        "description": f.description,
                        "priority_score": f.priority_score,
                        "cwe_ids": f.cwe_ids,
                        "owasp_categories": f.owasp_categories,
                        "fix_available": f.fix_available,
                    }
                    for f in result.deduplicated_findings
                ],
            }
            results_data["results"].append(target_data)

        with open(results_file, "w") as f:
            json.dump(results_data, f, indent=2)

        logger.info("✅ Scan complete!")
        logger.info("Total findings: %d", total_findings_count)
        logger.info("Deduplicated findings: %d", dedup_count)
        logger.info("Execution time: %.2fs", exec_time)
        logger.info("")
        logger.info("Findings by severity:")
        for severity, count in sorted(findings_by_severity.items()):
            logger.info("  %s: %d", severity, count)

        # Generate reports
        report_generator = ReportGenerator()

        # Helper to get format value safely
        def get_fmt_value(fmt):
            return str(fmt)

        if len(targets) == 1:
            for fmt in config.report.formats:
                fmt_val = get_fmt_value(fmt)
                logger.info(f"📄 Generating {fmt_val.upper()} report...")
                output_file = output_dir / f"report.{fmt_val}"
                report_generator.generate_report(
                    results[0], str(output_file), format=fmt_val
                )
        else:
            # Bulk reports
            formats = [get_fmt_value(fmt) for fmt in config.report.formats]
            logger.info(f"📄 Generating bulk reports ({', '.join(formats)})...")
            report_generator.generate_bulk_report(
                bulk_result, str(output_dir), formats=formats
            )

            # Individual reports
            logger.info("📄 Generating individual reports...")
            for target_result in results:
                target_name = Path(target_result.target).name
                if not target_name:  # handle '.' or root
                    target_name = "root"

                target_report_dir = output_dir / "targets" / target_name
                target_report_dir.mkdir(parents=True, exist_ok=True)

                for fmt in config.report.formats:
                    fmt_val = get_fmt_value(fmt)
                    output_file = target_report_dir / f"report.{fmt_val}"
                    report_generator.generate_report(
                        target_result, str(output_file), format=fmt_val
                    )

        logger.info("")
        logger.info("Reports saved to: %s", output_dir)

        # Auto-open report
        if args.open:
            try:
                # Look for HTML report
                html_report = list(output_dir.glob("*.html"))
                if html_report:
                    logger.info(f"Opening report: {html_report[0]}")
                    webbrowser.open(html_report[0].absolute().as_uri())
                else:
                    logger.warning("No HTML report found to open.")
            except Exception as e:
                logger.warning(f"Failed to open report: {e}")

        # Check thresholds
        critical_count = findings_by_severity.get("CRITICAL", 0)
        high_count = findings_by_severity.get("HIGH", 0)

        if config.thresholds.fail_on_critical and critical_count > 0:
            logger.error(
                "❌ Scan failed: %d critical findings detected", critical_count
            )
            return 1

        if config.thresholds.fail_on_high and high_count > 0:
            logger.error(
                "❌ Scan failed: %d high severity findings detected", high_count
            )
            return 1

        # LLM Explanation if requested
        if getattr(args, 'explain', False) and dedup_count > 0:
            try:
                llm_service = LLMService(config)
                if asyncio and asyncio.run(llm_service.is_available()):
                    # Explain top priority findings
                    critical_findings = []
                    for result in results:
                        for f in result.deduplicated_findings:
                            if f.severity.value in ["CRITICAL", "HIGH"]:
                                critical_findings.append(f)
                    
                    # Sort by priority
                    critical_findings.sort(key=lambda x: x.priority_score, reverse=True)
                    
                    if critical_findings:
                        logger.info(f"\n🧠 Explaining top {min(3, len(critical_findings))} findings using {config.llm.provider}...")
                        print("\n" + "="*50)
                        
                        for finding in critical_findings[:3]:
                            print(f"\nFinding: {finding.title} ({finding.severity.value})")
                            print(f"File: {finding.file_path}:{finding.line_start}")
                            print("-" * 30)
                            
                            explanation = asyncio.run(llm_service.explain_finding(finding))
                            print(explanation)
                            print("-" * 50)
            except Exception as e:
                logger.error(f"Failed to explain findings: {e}")

        logger.info("✅ No blocking findings detected")
        print_success("Scan completed successfully!")
        return 0

    except Exception as e:
        logger = get_logger(__name__)
        print_error(f"❌ Scan failed: {str(e)}")
        if args.verbose:
            logger.debug("Exception details:", exc_info=True)
        return 1
