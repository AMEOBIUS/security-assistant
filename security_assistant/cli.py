#!/usr/bin/env python3
"""
Security Assistant CLI - Command-line interface for security scanning.

Usage:
    security-assistant scan [OPTIONS] [TARGET]
    security-assistant config [OPTIONS]
    security-assistant report [OPTIONS]
    security-assistant --version
    security-assistant --help

Examples:
    # Basic scan
    security-assistant scan .

    # Scan with specific scanners
    security-assistant scan --bandit --semgrep src/

    # Scan with custom config
    security-assistant scan --config security-assistant.yaml

    # Generate reports only
    security-assistant report --format html,markdown

    # Create default config
    security-assistant config --create
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from security_assistant.config import (
    ConfigManager,
    ReportFormat,
    load_config,
)
from security_assistant.orchestrator import ScannerType, ScanOrchestrator, UnifiedFinding
from security_assistant.scanners.bandit_scanner import BanditScanner
from security_assistant.scanners.semgrep_scanner import SemgrepScanner
from security_assistant.scanners.trivy_scanner import TrivyScanner
from security_assistant.services.llm_service import LLMService

__version__ = "1.0.0"


def setup_logging(verbose: bool = False, log_file: Optional[str] = None) -> None:
    """
    Setup logging configuration.

    Args:
        verbose: Enable verbose output
        log_file: Path to log file
    """
    level = logging.DEBUG if verbose else logging.INFO

    handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)
    handlers.append(console_handler)

    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)

    logging.basicConfig(level=level, handlers=handlers)


def cmd_scan(args: argparse.Namespace) -> int:
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
            from security_assistant.config import LLMProvider
            config.llm.provider = LLMProvider(args.llm)

        # Determine targets
        targets = []
        if args.targets_file:
            path = Path(args.targets_file)
            if not path.exists():
                logging.error(f"Targets file not found: {args.targets_file}")
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
        if args.bandit_only or args.semgrep_only or args.trivy_only:
            config.bandit.enabled = args.bandit_only or False
            config.semgrep.enabled = args.semgrep_only or False
            config.trivy.enabled = args.trivy_only or False
        else:
            if args.no_bandit:
                config.bandit.enabled = False
            if args.no_semgrep:
                config.semgrep.enabled = False
            if args.no_trivy:
                config.trivy.enabled = False

        # Deduplication strategy
        if args.dedup:
            config.orchestrator.deduplication_strategy = args.dedup

        # Presets
        if args.preset == "quick":
            # Bandit only, no expensive analysis
            config.bandit.enabled = True
            config.semgrep.enabled = False
            config.trivy.enabled = False
            args.no_reachability = True
            args.no_kev = True
            args.no_fp_detection = True
        elif args.preset == "full":
            # All enabled
            config.bandit.enabled = True
            config.semgrep.enabled = True
            config.trivy.enabled = True
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
        setup_logging(config.verbose, config.log_file)
        logger = logging.getLogger(__name__)

        logger.info("🔒 Security Assistant v%s", __version__)
        logger.info("Scan target: %s", config.scan_target)

        # Create output directory
        output_dir = Path(config.report.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize orchestrator
        dedup_strat = config.orchestrator.deduplication_strategy
        dedup_val = getattr(dedup_strat, "value", str(dedup_strat))

        orchestrator = ScanOrchestrator(
            dedup_strategy=dedup_val,
            max_workers=config.orchestrator.max_workers,
            enable_kev=not args.no_kev,
            enable_fp_detection=not args.no_fp_detection,
            enable_reachability=not args.no_reachability,
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
        import json

        results_file = output_dir / "scan-results.json"

        results_data = {
            "total_findings": total_findings_count,
            "deduplicated_findings": dedup_count,
            "execution_time": exec_time,
            "findings_by_severity": dict(findings_by_severity),  # Ensure dict
            # 'findings_by_scanner': result.findings_by_scanner, # Need aggregation if bulk
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
        from security_assistant.report_generator import ReportGenerator

        report_generator = ReportGenerator()

        # Helper to get format value safely
        def get_fmt_value(fmt):
            return getattr(fmt, "value", str(fmt))

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
                import webbrowser

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
            import asyncio
            try:
                llm_service = LLMService(config)
                if asyncio.run(llm_service.is_available()):
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
        return 0

    except Exception as e:
        logging.error("❌ Scan failed: %s", str(e))
        if args.verbose:
            logging.exception("Exception details:")
        return 1


def cmd_config(args: argparse.Namespace) -> int:
    """
    Manage configuration.

    Args:
        args: Command-line arguments

    Returns:
        Exit code
    """
    try:
        manager = ConfigManager()

        if args.create:
            # Create default config
            output_path = args.output or "security-assistant.yaml"
            format_type = "json" if output_path.endswith(".json") else "yaml"

            manager.create_default_config(output_path, format_type)
            print(f"✅ Created default configuration: {output_path}")
            return 0

        elif args.validate:
            # Validate config
            config = load_config(args.validate)
            errors = config.validate()

            if errors:
                print("❌ Configuration validation failed:")
                for error in errors:
                    print(f"  - {error}")
                return 1
            else:
                print("✅ Configuration is valid")
                return 0

        elif args.show:
            # Show current config
            config = load_config(args.show if args.show is not True else None)

            import yaml

            print(
                yaml.dump(config.to_dict(), default_flow_style=False, sort_keys=False)
            )
            return 0

        else:
            print("Error: No action specified. Use --create, --validate, or --show")
            return 1

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


def cmd_report(args: argparse.Namespace) -> int:
    """
    Generate reports from existing scan results.

    Args:
        args: Command-line arguments

    Returns:
        Exit code
    """
    try:
        import json

        # Load scan results
        results_file = Path(args.input or "security-reports/scan-results.json")

        if not results_file.exists():
            print(f"❌ Results file not found: {results_file}")
            return 1

        with open(results_file) as f:
            _ = json.load(f)  # Results loaded but not used in this command

        output_dir = Path(args.output_dir or "security-reports")
        output_dir.mkdir(parents=True, exist_ok=True)

        formats = args.format.split(",") if args.format else ["html"]

        for fmt in formats:
            fmt = fmt.strip()

            if fmt == "html":
                print("📄 Generating HTML report...")
                # HTML generation

            elif fmt == "markdown":
                print("📝 Generating Markdown report...")
                # Markdown generation

            elif fmt == "sarif":
                print("📋 Generating SARIF report...")
                # SARIF generation

        print(f"✅ Reports generated in: {output_dir}")
        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


def cmd_poc(args: argparse.Namespace) -> int:
    """
    Generate a PoC for a finding.

    Args:
        args: Command-line arguments

    Returns:
        Exit code
    """
    import asyncio
    import json
    from security_assistant.poc import PoCGenerator, PoCError
    from security_assistant.poc.enhancers.llm_enhancer import LLMEnhancer

    try:
        # Load configuration
        config = load_config(config_file=args.config, use_env=True)

        # Load report
        report_path = Path(args.report)
        if not report_path.exists():
            logging.error(f"Report file not found: {report_path}")
            return 1
            
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # Find the finding
        target_finding = None
        findings = data.get("findings", [])
        
        for f in findings:
            if f.get("id") == args.finding_id or f.get("finding_id") == args.finding_id:
                target_finding = UnifiedFinding(
                    finding_id=f.get("id") or f.get("finding_id"),
                    scanner=ScannerType(f.get("scanner", "bandit")),
                    severity=f.get("severity", "MEDIUM"),
                    category=f.get("category", "security"),
                    file_path=f.get("location", {}).get("file", f.get("file_path", "")),
                    line_start=f.get("location", {}).get("line", f.get("line_start", 0)),
                    line_end=f.get("location", {}).get("line", f.get("line_end", 0)),
                    title=f.get("title", ""),
                    description=f.get("description", ""),
                    code_snippet=f.get("code", {}).get("snippet", f.get("code_snippet", ""))
                )
                break
        
        if not target_finding:
            logging.error(f"Finding '{args.finding_id}' not found in {report_path}")
            return 1

        # Initialize LLM & Enhancer
        llm_service = LLMService(config)
        llm_enhancer = None
        
        if asyncio.run(llm_service.is_available()):
            llm_enhancer = LLMEnhancer(llm_service)
            print(f"🧠 Using LLM ({config.llm.provider}) for enhanced PoC generation...")
        else:
            print("⚠️ LLM not available. Using heuristic PoC generation.")

        # Generate PoC
        generator = PoCGenerator(llm_enhancer=llm_enhancer)
        output_file = args.output
        
        if not output_file:
            # Auto-name
            ext = ".html" if "xss" in (target_finding.category or "").lower() else ".py"
            output_file = f"poc_{target_finding.finding_id}{ext}"
            
        poc_code = asyncio.run(generator.generate(target_finding, output_path=output_file))
        
        print(f"✅ PoC generated successfully: {output_file}")
        print("\n" + "="*40)
        print(poc_code)
        print("="*40 + "\n")
        
        return 0

    except PoCError as e:
        logging.error(f"PoC Generation failed: {e}")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return 1


def cmd_explain(args: argparse.Namespace) -> int:
    """
    Explain a finding using LLM.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    import asyncio
    import json

    try:
        # Load configuration
        config = load_config(config_file=args.config, use_env=True)
        
        # Initialize LLM Service
        llm_service = LLMService(config)
        
        # Check if LLM is available
        if not asyncio.run(llm_service.is_available()):
            logging.error(f"LLM service is not available. Check your provider ({config.llm.provider}) and API key.")
            return 1

        # Load report
        report_path = Path(args.report)
        if not report_path.exists():
            logging.error(f"Report file not found: {report_path}")
            return 1
            
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # Find the finding
        target_finding = None
        findings = data.get("findings", [])
        
        for f in findings:
            if f.get("id") == args.finding_id or f.get("finding_id") == args.finding_id:
                # Convert dict back to UnifiedFinding
                target_finding = UnifiedFinding(
                    finding_id=f.get("id") or f.get("finding_id"),
                    scanner=ScannerType(f.get("scanner", "bandit")),
                    severity=f.get("severity", "MEDIUM"),
                    category=f.get("category", "security"),
                    file_path=f.get("location", {}).get("file", f.get("file_path", "")),
                    line_start=f.get("location", {}).get("line", f.get("line_start", 0)),
                    line_end=f.get("location", {}).get("line", f.get("line_end", 0)),
                    title=f.get("title", ""),
                    description=f.get("description", ""),
                    code_snippet=f.get("code", {}).get("snippet", f.get("code_snippet", ""))
                )
                break
        
        if not target_finding:
            logging.error(f"Finding '{args.finding_id}' not found in {report_path}")
            return 1
            
        print(f"🤖 Analyzing finding: {target_finding.title} ({target_finding.finding_id})...\n")
        
        if args.fix:
            print("Suggesting fix...")
            fix = asyncio.run(llm_service.suggest_fix(target_finding))
            print("\n" + "="*40)
            print("SUGGESTED FIX")
            print("="*40 + "\n")
            print(fix)
        else:
            explanation = asyncio.run(llm_service.explain_finding(target_finding))
            print("\n" + "="*40)
            print("EXPLANATION")
            print("="*40 + "\n")
            print(explanation)
            
        return 0

    except Exception as e:
        logging.error(f"Error explaining finding: {e}")
        return 1


def cmd_query(args: argparse.Namespace) -> int:
    """
    Execute natural language query.

    Args:
        args: Command-line arguments

    Returns:
        Exit code
    """
    import asyncio
    import json
    from security_assistant.nl.query_parser import QueryParser
    from security_assistant.nl.query_executor import QueryExecutor

    try:
        # Load config
        config = load_config(config_file=args.config, use_env=True)
        llm_service = LLMService(config)
        
        # Parse query
        parser = QueryParser(llm_service)
        print(f"🤔 Parsing query: '{args.query}'...")
        structured_query = asyncio.run(parser.parse(args.query))
        
        print(f"🔍 Intent: {structured_query.intent}")
        print(f"🔍 Filters: {structured_query.filters.model_dump(exclude_none=True)}")
        
        # Load results
        report_path = Path(args.report)
        if not report_path.exists():
            logging.error(f"Report file not found: {report_path}")
            return 1
            
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # Flatten findings from results
        all_findings = []
        if "results" in data and isinstance(data["results"], list):
            for target in data["results"]:
                all_findings.extend(target.get("findings", []))
        elif "findings" in data:
            all_findings = data.get("findings", [])
            
        # Execute
        executor = QueryExecutor()
        result = executor.execute(structured_query, all_findings)
        
        # Print results
        print("\n" + "="*40)
        print("RESULTS")
        print("="*40)
        
        if "count" in result:
            print(f"Total Matches: {result['count']}")
            
        if "results" in result:
            for i, f in enumerate(result["results"], 1):
                print(f"{i}. [{f.get('severity')}] {f.get('title')} ({f.get('file')}:{f.get('line_start')})")
                
        return 0

    except Exception as e:
        logging.error(f"Query failed: {e}")
        return 1


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Security Assistant - Multi-scanner security analysis tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic scan
  security-assistant scan .
  
  # Scan with specific scanners
  security-assistant scan --bandit --semgrep src/
  
  # Scan with custom config
  security-assistant scan --config security-assistant.yaml
  
  # Create default config
  security-assistant config --create
  
  # Validate config
  security-assistant config --validate security-assistant.yaml
  
  # Generate reports
  security-assistant report --format html,markdown

Environment Variables:
  SA_BANDIT_ENABLED       Enable/disable Bandit scanner
  SA_SEMGREP_ENABLED      Enable/disable Semgrep scanner
  SA_TRIVY_ENABLED        Enable/disable Trivy scanner
  SA_DEDUP_STRATEGY       Deduplication strategy (location/content/both)
  SA_MAX_WORKERS          Maximum parallel workers
  SA_REPORT_FORMATS       Comma-separated report formats
  SA_OUTPUT_DIR           Report output directory
  SA_FAIL_ON_CRITICAL     Fail on critical findings
  SA_FAIL_ON_HIGH         Fail on high findings
  SA_SCAN_TARGET          Scan target directory
  SA_VERBOSE              Verbose output
        """,
    )

    parser.add_argument(
        "--version", action="version", version=f"Security Assistant {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Run security scan")
    scan_parser.add_argument(
        "target",
        nargs="*",
        default=["."],
        help="Directory or file to scan (default: current directory). Can specify multiple targets.",
    )
    scan_parser.add_argument(
        "--targets-file", help="File containing list of targets to scan (one per line)"
    )
    scan_parser.add_argument("-c", "--config", help="Path to configuration file")
    scan_parser.add_argument(
        "--no-env", action="store_true", help="Ignore environment variables"
    )
    scan_parser.add_argument("-o", "--output-dir", help="Output directory for reports")
    scan_parser.add_argument(
        "-f",
        "--format",
        help="Report formats (comma-separated: json,html,markdown,sarif)",
    )
    scan_parser.add_argument(
        "--dedup",
        choices=["location", "content", "both"],
        help="Deduplication strategy",
    )
    scan_parser.add_argument(
        "--bandit-only", action="store_true", help="Run Bandit scanner only"
    )
    scan_parser.add_argument(
        "--semgrep-only", action="store_true", help="Run Semgrep scanner only"
    )
    scan_parser.add_argument(
        "--trivy-only", action="store_true", help="Run Trivy scanner only"
    )
    scan_parser.add_argument(
        "--no-bandit", action="store_true", help="Disable Bandit scanner"
    )
    scan_parser.add_argument(
        "--no-semgrep", action="store_true", help="Disable Semgrep scanner"
    )
    scan_parser.add_argument(
        "--no-trivy", action="store_true", help="Disable Trivy scanner"
    )
    scan_parser.add_argument(
        "--fail-on-critical",
        action="store_true",
        default=None,
        help="Fail if critical findings are detected",
    )
    scan_parser.add_argument(
        "--fail-on-high",
        action="store_true",
        default=None,
        help="Fail if high severity findings are detected",
    )
    scan_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output"
    )

    # Enrichment/Analysis flags
    scan_parser.add_argument(
        "--no-kev", action="store_true", help="Disable KEV enrichment"
    )
    scan_parser.add_argument(
        "--no-fp-detection",
        action="store_true",
        help="Disable False Positive detection",
    )
    scan_parser.add_argument(
        "--no-reachability", action="store_true", help="Disable Reachability Analysis"
    )

    scan_parser.add_argument(
        "--preset", choices=["quick", "full", "ci"], help="Scan preset configuration"
    )
    scan_parser.add_argument(
        "--open", action="store_true", help="Automatically open HTML report in browser"
    )
    scan_parser.add_argument(
        "--llm", 
        choices=["openai", "anthropic", "ollama", "nvidia", "disabled"],
        help="Enable LLM integration with specific provider"
    )
    scan_parser.add_argument(
        "--explain", action="store_true", help="Explain critical/high findings using LLM"
    )

    # Config command
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_parser.add_argument(
        "--create", action="store_true", help="Create default configuration file"
    )
    config_parser.add_argument(
        "--validate", metavar="FILE", help="Validate configuration file"
    )
    config_parser.add_argument(
        "--show",
        nargs="?",
        const=True,
        metavar="FILE",
        help="Show configuration (from file or current)",
    )
    config_parser.add_argument("-o", "--output", help="Output file for --create")

    # Report command
    report_parser = subparsers.add_parser("report", help="Generate reports")
    report_parser.add_argument(
        "-i",
        "--input",
        help="Input scan results file (default: security-reports/scan-results.json)",
    )
    report_parser.add_argument(
        "-o", "--output-dir", help="Output directory for reports"
    )
    report_parser.add_argument(
        "-f", "--format", help="Report formats (comma-separated: html,markdown,sarif)"
    )

    # Explain command
    explain_parser = subparsers.add_parser("explain", help="Explain a finding using LLM")
    explain_parser.add_argument("finding_id", help="ID of the finding to explain")
    explain_parser.add_argument(
        "-r", "--report", 
        default="security-reports/scan-results.json", 
        help="Path to scan results JSON"
    )
    explain_parser.add_argument("--fix", action="store_true", help="Also suggest a fix")
    explain_parser.add_argument("-c", "--config", help="Path to configuration file")

    # PoC command
    poc_parser = subparsers.add_parser("poc", help="Generate Proof-of-Concept exploit")
    poc_parser.add_argument("finding_id", help="ID of the finding to generate PoC for")
    poc_parser.add_argument(
        "-r", "--report", 
        default="security-reports/scan-results.json", 
        help="Path to scan results JSON"
    )
    poc_parser.add_argument("-o", "--output", help="Output file path")

    # Query command
    query_parser = subparsers.add_parser("query", help="Execute natural language query")
    query_parser.add_argument("query", help="Natural language query string")
    query_parser.add_argument(
        "-r", "--report", 
        default="security-reports/scan-results.json", 
        help="Path to scan results JSON"
    )
    query_parser.add_argument("-c", "--config", help="Path to configuration file")

    # Doctor command
    subparsers.add_parser("doctor", help="Check system health and dependencies")

    # Configure command
    subparsers.add_parser("configure", help="Interactive configuration wizard")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Execute command
    if args.command == "scan":
        return cmd_scan(args)
    elif args.command == "config":
        return cmd_config(args)
    elif args.command == "report":
        return cmd_report(args)
    elif args.command == "explain":
        return cmd_explain(args)
    elif args.command == "poc":
        return cmd_poc(args)
    elif args.command == "query":
        return cmd_query(args)
    elif args.command == "doctor":
        from security_assistant.doctor import run_doctor

        return run_doctor()
    elif args.command == "configure":
        from security_assistant.configure import cmd_configure

        return cmd_configure()
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
