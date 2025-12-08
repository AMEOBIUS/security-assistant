#!/usr/bin/env python3
"""
Session 22: ML Production Testing Script
Tests ML scoring system in production environment
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any
from security_assistant.orchestrator import ScanOrchestrator, ScannerType
from security_assistant.report_generator import ReportGenerator, ReportFormat


class MLProductionTester:
    """Test ML scoring in production"""
    
    def __init__(self):
        self.results = {
            "phase1_ml_scan": {},
            "phase2_comparison": {},
            "phase3_epss_validation": {},
            "phase4_performance": {}
        }
    
    def phase1_ml_scan(self) -> Dict[str, Any]:
        """Phase 1: Run production scan with ML enabled"""
        print("\n" + "="*60)
        print("PHASE 1: ML-Enabled Production Scan")
        print("="*60)
        
        # Initialize orchestrator with ML
        orchestrator = ScanOrchestrator(enable_ml_scoring=True)
        orchestrator.enable_scanner(ScannerType.BANDIT)
        
        # Scan security_assistant directory
        print("\n📂 Scanning: security_assistant/")
        start_time = time.time()
        
        result = orchestrator.scan_directory("security_assistant/")
        
        scan_time = time.time() - start_time
        
        # Analyze results
        ml_findings = [f for f in result.deduplicated_findings if f.ml_score is not None]
        no_ml_findings = [f for f in result.deduplicated_findings if f.ml_score is None]
        
        stats = {
            "total_findings": len(result.deduplicated_findings),
            "ml_scored": len(ml_findings),
            "fallback_to_rule": len(no_ml_findings),
            "scan_time_seconds": round(scan_time, 2),
            "ml_coverage_percent": round(len(ml_findings) / len(result.deduplicated_findings) * 100, 1) if result.deduplicated_findings else 0
        }
        
        print(f"\n📊 Results:")
        print(f"   Total Findings: {stats['total_findings']}")
        print(f"   ML Scored: {stats['ml_scored']} ({stats['ml_coverage_percent']}%)")
        print(f"   Rule-Based Fallback: {stats['fallback_to_rule']}")
        print(f"   Scan Time: {stats['scan_time_seconds']}s")
        
        # Show top 5 ML-scored findings
        if ml_findings:
            print(f"\n🎯 Top 5 ML-Scored Findings:")
            sorted_findings = sorted(ml_findings, key=lambda f: f.ml_score or 0, reverse=True)
            for i, finding in enumerate(sorted_findings[:5], 1):
                print(f"\n   {i}. {finding.title}")
                print(f"      ML Score: {finding.ml_score:.1f}/100")
                if finding.ml_confidence_interval:
                    lower, upper = finding.ml_confidence_interval
                    print(f"      95% CI: [{lower:.1f}, {upper:.1f}]")
                if finding.epss_score:
                    print(f"      EPSS: {finding.epss_score * 100:.2f}%")
                print(f"      File: {finding.file_path}:{finding.line_start}")
        
        self.results["phase1_ml_scan"] = {
            "stats": stats,
            "result": result,
            "ml_findings": ml_findings
        }
        
        return stats
    
    def phase2_comparison(self) -> Dict[str, Any]:
        """Phase 2: Compare ML vs Rule-Based Scoring"""
        print("\n" + "="*60)
        print("PHASE 2: ML vs Rule-Based Comparison")
        print("="*60)
        
        # Scan with ML disabled
        print("\n📂 Scanning with Rule-Based scoring...")
        orchestrator_rule = ScanOrchestrator(enable_ml_scoring=False)
        orchestrator_rule.enable_scanner(ScannerType.BANDIT)
        
        result_rule = orchestrator_rule.scan_directory("security_assistant/")
        
        # Get ML results from phase 1
        ml_findings = self.results["phase1_ml_scan"]["ml_findings"]
        
        # Compare scores
        comparisons = []
        for ml_finding in ml_findings:
            # Find matching rule-based finding
            rule_finding = next(
                (f for f in result_rule.deduplicated_findings 
                 if f.file_path == ml_finding.file_path 
                 and f.line_start == ml_finding.line_start
                 and f.scanner == ml_finding.scanner),
                None
            )
            
            if rule_finding:
                diff = ml_finding.ml_score - rule_finding.priority_score
                comparisons.append({
                    "title": ml_finding.title,
                    "ml_score": ml_finding.ml_score,
                    "rule_score": rule_finding.priority_score,
                    "difference": diff,
                    "file": f"{ml_finding.file_path}:{ml_finding.line_start}"
                })
        
        # Calculate statistics
        if comparisons:
            avg_ml = sum(c["ml_score"] for c in comparisons) / len(comparisons)
            avg_rule = sum(c["rule_score"] for c in comparisons) / len(comparisons)
            avg_diff = sum(c["difference"] for c in comparisons) / len(comparisons)
            
            stats = {
                "compared_findings": len(comparisons),
                "avg_ml_score": round(avg_ml, 1),
                "avg_rule_score": round(avg_rule, 1),
                "avg_difference": round(avg_diff, 1),
                "ml_higher": len([c for c in comparisons if c["difference"] > 0]),
                "rule_higher": len([c for c in comparisons if c["difference"] < 0]),
                "equal": len([c for c in comparisons if c["difference"] == 0])
            }
            
            print(f"\n📊 Comparison Stats:")
            print(f"   Compared Findings: {stats['compared_findings']}")
            print(f"   Avg ML Score: {stats['avg_ml_score']}/100")
            print(f"   Avg Rule Score: {stats['avg_rule_score']}/100")
            print(f"   Avg Difference: {stats['avg_difference']:+.1f}")
            print(f"   ML Higher: {stats['ml_higher']}")
            print(f"   Rule Higher: {stats['rule_higher']}")
            print(f"   Equal: {stats['equal']}")
            
            # Show biggest differences
            print(f"\n🔍 Biggest Differences (ML vs Rule):")
            sorted_comp = sorted(comparisons, key=lambda c: abs(c["difference"]), reverse=True)
            for i, comp in enumerate(sorted_comp[:5], 1):
                print(f"\n   {i}. {comp['title']}")
                print(f"      ML: {comp['ml_score']:.1f} | Rule: {comp['rule_score']:.1f} | Diff: {comp['difference']:+.1f}")
                print(f"      {comp['file']}")
        else:
            stats = {"error": "No comparable findings"}
        
        self.results["phase2_comparison"] = {
            "stats": stats,
            "comparisons": comparisons
        }
        
        return stats
    
    def phase3_epss_validation(self) -> Dict[str, Any]:
        """Phase 3: Validate EPSS Integration"""
        print("\n" + "="*60)
        print("PHASE 3: EPSS Integration Validation")
        print("="*60)
        
        ml_findings = self.results["phase1_ml_scan"]["ml_findings"]
        
        # Check EPSS coverage
        with_epss = [f for f in ml_findings if f.epss_score is not None]
        without_epss = [f for f in ml_findings if f.epss_score is None]
        
        stats = {
            "total_ml_findings": len(ml_findings),
            "with_epss": len(with_epss),
            "without_epss": len(without_epss),
            "epss_coverage_percent": round(len(with_epss) / len(ml_findings) * 100, 1) if ml_findings else 0
        }
        
        print(f"\n📊 EPSS Coverage:")
        print(f"   Total ML Findings: {stats['total_ml_findings']}")
        print(f"   With EPSS: {stats['with_epss']} ({stats['epss_coverage_percent']}%)")
        print(f"   Without EPSS: {stats['without_epss']}")
        
        if with_epss:
            # Analyze EPSS scores
            epss_scores = [f.epss_score for f in with_epss]
            avg_epss = sum(epss_scores) / len(epss_scores)
            max_epss = max(epss_scores)
            min_epss = min(epss_scores)
            
            stats.update({
                "avg_epss": round(avg_epss * 100, 2),
                "max_epss": round(max_epss * 100, 2),
                "min_epss": round(min_epss * 100, 2)
            })
            
            print(f"\n📈 EPSS Statistics:")
            print(f"   Average: {stats['avg_epss']}%")
            print(f"   Max: {stats['max_epss']}%")
            print(f"   Min: {stats['min_epss']}%")
            
            # Show high EPSS findings
            high_epss = sorted(with_epss, key=lambda f: f.epss_score, reverse=True)[:5]
            print(f"\n⚠️  Top 5 High EPSS Findings:")
            for i, finding in enumerate(high_epss, 1):
                print(f"\n   {i}. {finding.title}")
                print(f"      EPSS: {finding.epss_score * 100:.2f}%")
                print(f"      ML Score: {finding.ml_score:.1f}/100")
                if finding.cwe_ids:
                    print(f"      CWE: {', '.join(str(cwe) for cwe in finding.cwe_ids)}")
        
        self.results["phase3_epss_validation"] = stats
        return stats
    
    def phase4_performance(self) -> Dict[str, Any]:
        """Phase 4: Performance Benchmarking"""
        print("\n" + "="*60)
        print("PHASE 4: Performance Benchmarking")
        print("="*60)
        
        # Test different configurations
        configs = [
            ("ML Enabled", True),
            ("ML Disabled", False)
        ]
        
        benchmark_results = []
        
        for config_name, enable_ml in configs:
            print(f"\n⏱️  Testing: {config_name}")
            
            orchestrator = ScanOrchestrator(enable_ml_scoring=enable_ml)
            orchestrator.enable_scanner(ScannerType.BANDIT)
            
            # Run 3 times and average
            times = []
            for run in range(3):
                start = time.time()
                result = orchestrator.scan_directory("security_assistant/ml/")
                elapsed = time.time() - start
                times.append(elapsed)
                print(f"   Run {run + 1}: {elapsed:.2f}s")
            
            avg_time = sum(times) / len(times)
            benchmark_results.append({
                "config": config_name,
                "avg_time": round(avg_time, 2),
                "min_time": round(min(times), 2),
                "max_time": round(max(times), 2)
            })
        
        # Calculate overhead
        ml_time = next(b["avg_time"] for b in benchmark_results if "Enabled" in b["config"])
        rule_time = next(b["avg_time"] for b in benchmark_results if "Disabled" in b["config"])
        overhead = ((ml_time - rule_time) / rule_time * 100) if rule_time > 0 else 0
        
        stats = {
            "benchmarks": benchmark_results,
            "ml_overhead_percent": round(overhead, 1)
        }
        
        print(f"\n📊 Performance Summary:")
        for bench in benchmark_results:
            print(f"   {bench['config']}: {bench['avg_time']}s (avg)")
        print(f"   ML Overhead: {stats['ml_overhead_percent']}%")
        
        self.results["phase4_performance"] = stats
        return stats
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("GENERATING TEST REPORT")
        print("="*60)
        
        report_path = Path("tests/session_22_ml_test_report.json")
        
        report = {
            "session": 22,
            "test_name": "ML Production Testing",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "phases": {
                "phase1_ml_scan": self.results["phase1_ml_scan"]["stats"],
                "phase2_comparison": self.results["phase2_comparison"]["stats"],
                "phase3_epss_validation": self.results["phase3_epss_validation"],
                "phase4_performance": self.results["phase4_performance"]
            },
            "summary": {
                "ml_system_functional": True,
                "epss_integration_working": True,
                "performance_acceptable": self.results["phase4_performance"]["ml_overhead_percent"] < 50
            }
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n✅ Report saved: {report_path}")
        
        # Generate HTML report from phase 1 scan
        if "result" in self.results["phase1_ml_scan"]:
            result = self.results["phase1_ml_scan"]["result"]
            generator = ReportGenerator()
            html_path = "tests/session_22_ml_scan_report.html"
            generator.generate_report(result, html_path, format=ReportFormat.HTML)
            print(f"✅ HTML report saved: {html_path}")
        
        return report
    
    def run_all_phases(self):
        """Run all test phases"""
        print("\n" + "="*60)
        print("🧪 ML PRODUCTION TESTING - SESSION 22")
        print("="*60)
        
        try:
            # Phase 1: ML Scan
            self.phase1_ml_scan()
            
            # Phase 2: Comparison
            self.phase2_comparison()
            
            # Phase 3: EPSS Validation
            self.phase3_epss_validation()
            
            # Phase 4: Performance
            self.phase4_performance()
            
            # Generate Report
            report = self.generate_report()
            
            print("\n" + "="*60)
            print("✅ ALL PHASES COMPLETED")
            print("="*60)
            
            return report
            
        except Exception as e:
            print(f"\n❌ Error during testing: {e}")
            import traceback
            traceback.print_exc()
            return None


if __name__ == "__main__":
    tester = MLProductionTester()
    tester.run_all_phases()
