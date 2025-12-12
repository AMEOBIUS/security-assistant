"""
Report command implementation.

Generates security reports in various formats:
- HTML
- Markdown  
- JSON
- SARIF
"""

from pathlib import Path

from security_assistant.ci.base import (
    get_logger,
    print_error,
    print_info,
    print_success,
)


def cmd_report(args):
    """
    Generate security reports.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    try:
        from security_assistant.config import ReportFormat, load_config
        from security_assistant.report_generator import ReportGenerator
        
        # Load configuration
        config = load_config(config_file=args.config, use_env=not args.no_env)
        logger = get_logger(__name__)

        # Check if results exist
        results_file = Path(config.report.output_dir) / "scan-results.json"
        if not results_file.exists():
            print_error("❌ No scan results found")
            print_info("Run 'security-assistant scan' first to generate data")
            return 1

        # Load results
        import json
        with open(results_file) as f:
            results_data = json.load(f)

        if not results_data.get("results"):
            print_error("❌ No scan data found in results")
            return 1

        # Determine formats
        if args.format:
            formats_str = args.format
            formats = [ReportFormat(f.strip()) for f in formats_str.split(",")]
        else:
            formats = config.report.formats or [ReportFormat.HTML, ReportFormat.JSON]

        # Generate reports
        report_generator = ReportGenerator()
        print_info(f"📄 Generating {len(formats)} report format(s)...")
        
        # Generate reports from bulk results
        # Create bulk result structure
        class BulkResult:
            def __init__(self, results_data):
                self.results = {}
                for target_result in results_data.get("results", []):
                    class TargetResult:
                        def __init__(self, data):
                            self.target = data["target"]
                            self.findings = data.get("findings", [])
                            # Reconstruct finding objects
                    tr = TargetResult(target_result)
                    self.results[tr.target] = tr
                    
            def get(self):
                return self.results
        
        bulk_result = BulkResult(results_data)
        output_dir = Path(config.report.output_dir)
        
        for fmt in formats:
            fmt_val = str(fmt).upper()
            print_info(f"  Generating {fmt_val} report...")
            report_generator.generate_bulk_report(
                bulk_result, str(output_dir), formats=[fmt_val]
            )
        
        print_success(f"✅ Reports generated in: {output_dir}")
        return 0

    except Exception as e:
        logger = get_logger(__name__)
        print_error(f"❌ Report generation failed: {e}")
        if args.verbose:
            logger.debug("Exception details:", exc_info=True)
        return 1
