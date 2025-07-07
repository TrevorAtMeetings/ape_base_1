#!/usr/bin/env python3
"""
Performance Data Integrity Audit
Validates pump performance curves, efficiency calculations, and engineering data
"""

import json
import numpy as np
import logging
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceIssue:
    """Performance data validation issue"""
    pump_code: str
    curve_id: str
    issue_type: str
    description: str
    severity: str = "WARNING"
    data_points: List[Dict] = field(default_factory=list)

class PerformanceDataAuditor:
    """Audits performance curve data for engineering validity"""
    
    def __init__(self, catalog_path: str = "data/ape_catalog_database.json"):
        self.catalog_path = catalog_path
        self.issues = []
        
    def load_catalog(self) -> Dict[str, Any]:
        """Load catalog database"""
        with open(self.catalog_path, 'r') as f:
            return json.load(f)
    
    def validate_performance_curve(self, pump_code: str, curve: Dict[str, Any]) -> List[PerformanceIssue]:
        """Validate individual performance curve for engineering correctness"""
        issues = []
        curve_id = curve.get('curve_id', 'unknown')
        points = curve.get('performance_points', [])
        
        if len(points) < 3:
            issues.append(PerformanceIssue(
                pump_code=pump_code,
                curve_id=curve_id,
                issue_type="INSUFFICIENT_DATA_POINTS",
                description=f"Curve has only {len(points)} points, minimum 3 required",
                severity="ERROR"
            ))
            return issues
        
        flows = [p.get('flow_m3hr', 0) for p in points]
        heads = [p.get('head_m', 0) for p in points]
        efficiencies = [p.get('efficiency_pct', 0) for p in points]
        
        # Check for monotonic flow increase
        if not all(flows[i] <= flows[i+1] for i in range(len(flows)-1)):
            issues.append(PerformanceIssue(
                pump_code=pump_code,
                curve_id=curve_id,
                issue_type="NON_MONOTONIC_FLOW",
                description="Flow values are not monotonically increasing",
                severity="ERROR",
                data_points=[{"flows": flows}]
            ))
        
        # Check for reasonable head-flow relationship (head should generally decrease with increasing flow)
        head_trend_violations = 0
        for i in range(len(heads)-1):
            if heads[i] < heads[i+1]:  # Head increasing with flow
                head_trend_violations += 1
        
        if head_trend_violations > len(heads) * 0.3:  # More than 30% violations
            issues.append(PerformanceIssue(
                pump_code=pump_code,
                curve_id=curve_id,
                issue_type="UNUSUAL_HEAD_TREND",
                description=f"Head increases with flow in {head_trend_violations} of {len(heads)} points",
                severity="WARNING",
                data_points=[{"heads": heads, "flows": flows}]
            ))
        
        # Check efficiency values
        max_efficiency = max(efficiencies) if efficiencies else 0
        if max_efficiency > 95:
            issues.append(PerformanceIssue(
                pump_code=pump_code,
                curve_id=curve_id,
                issue_type="UNREALISTIC_EFFICIENCY",
                description=f"Maximum efficiency {max_efficiency}% exceeds realistic limit of 95%",
                severity="ERROR"
            ))
        
        if max_efficiency < 30:
            issues.append(PerformanceIssue(
                pump_code=pump_code,
                curve_id=curve_id,
                issue_type="LOW_EFFICIENCY",
                description=f"Maximum efficiency {max_efficiency}% is unusually low",
                severity="WARNING"
            ))
        
        # Check for zero efficiency at zero flow (should be zero)
        if flows[0] == 0 and efficiencies[0] != 0:
            issues.append(PerformanceIssue(
                pump_code=pump_code,
                curve_id=curve_id,
                issue_type="NON_ZERO_EFFICIENCY_AT_ZERO_FLOW",
                description=f"Efficiency at zero flow is {efficiencies[0]}%, should be 0%",
                severity="WARNING"
            ))
        
        # Check for reasonable flow range
        max_flow = max(flows)
        if max_flow > 10000:  # Very high flow for typical pumps
            issues.append(PerformanceIssue(
                pump_code=pump_code,
                curve_id=curve_id,
                issue_type="EXTREME_FLOW_VALUE",
                description=f"Maximum flow {max_flow} m³/hr is extremely high",
                severity="WARNING"
            ))
        
        # Check for reasonable head range
        max_head = max(heads)
        if max_head > 1000:  # Very high head for typical pumps
            issues.append(PerformanceIssue(
                pump_code=pump_code,
                curve_id=curve_id,
                issue_type="EXTREME_HEAD_VALUE",
                description=f"Maximum head {max_head} m is extremely high",
                severity="WARNING"
            ))
        
        return issues
    
    def validate_bep_calculation(self, pump_code: str, curves: List[Dict[str, Any]]) -> List[PerformanceIssue]:
        """Validate Best Efficiency Point calculations"""
        issues = []
        
        for curve in curves:
            points = curve.get('performance_points', [])
            if len(points) < 3:
                continue
                
            efficiencies = [p.get('efficiency_pct', 0) for p in points]
            flows = [p.get('flow_m3hr', 0) for p in points]
            heads = [p.get('head_m', 0) for p in points]
            
            # Find BEP
            max_eff_idx = efficiencies.index(max(efficiencies))
            bep_flow = flows[max_eff_idx]
            bep_head = heads[max_eff_idx]
            bep_eff = efficiencies[max_eff_idx]
            
            # Check if BEP is at reasonable position (not at extremes)
            if max_eff_idx == 0 or max_eff_idx == len(points) - 1:
                issues.append(PerformanceIssue(
                    pump_code=pump_code,
                    curve_id=curve.get('curve_id', 'unknown'),
                    issue_type="BEP_AT_CURVE_EXTREME",
                    description=f"BEP occurs at curve extreme (point {max_eff_idx+1} of {len(points)})",
                    severity="WARNING",
                    data_points=[{"bep_flow": bep_flow, "bep_head": bep_head, "bep_efficiency": bep_eff}]
                ))
        
        return issues
    
    def validate_impeller_scaling(self, pump_code: str, curves: List[Dict[str, Any]]) -> List[PerformanceIssue]:
        """Validate impeller diameter scaling relationships"""
        issues = []
        
        if len(curves) < 2:
            return issues
        
        # Check if curves follow affinity laws for different impeller diameters
        curve_data = []
        for curve in curves:
            imp_dia = curve.get('impeller_diameter_mm', 0)
            points = curve.get('performance_points', [])
            if points and imp_dia > 0:
                max_flow = max(p.get('flow_m3hr', 0) for p in points)
                max_head = max(p.get('head_m', 0) for p in points)
                curve_data.append((imp_dia, max_flow, max_head))
        
        if len(curve_data) >= 2:
            curve_data.sort()  # Sort by impeller diameter
            
            for i in range(1, len(curve_data)):
                d1, q1, h1 = curve_data[i-1]
                d2, q2, h2 = curve_data[i]
                
                # Affinity laws: Q2/Q1 = (D2/D1), H2/H1 = (D2/D1)²
                expected_flow_ratio = d2 / d1
                expected_head_ratio = (d2 / d1) ** 2
                
                actual_flow_ratio = q2 / q1 if q1 > 0 else 0
                actual_head_ratio = h2 / h1 if h1 > 0 else 0
                
                flow_error = abs(actual_flow_ratio - expected_flow_ratio) / expected_flow_ratio * 100
                head_error = abs(actual_head_ratio - expected_head_ratio) / expected_head_ratio * 100
                
                if flow_error > 15:  # More than 15% deviation from affinity laws
                    issues.append(PerformanceIssue(
                        pump_code=pump_code,
                        curve_id=f"Scaling_{d1}mm_to_{d2}mm",
                        issue_type="AFFINITY_LAW_VIOLATION_FLOW",
                        description=f"Flow scaling deviates {flow_error:.1f}% from affinity laws",
                        severity="WARNING",
                        data_points=[{
                            "diameter_1": d1, "diameter_2": d2,
                            "expected_ratio": expected_flow_ratio,
                            "actual_ratio": actual_flow_ratio
                        }]
                    ))
                
                if head_error > 20:  # More than 20% deviation from affinity laws
                    issues.append(PerformanceIssue(
                        pump_code=pump_code,
                        curve_id=f"Scaling_{d1}mm_to_{d2}mm",
                        issue_type="AFFINITY_LAW_VIOLATION_HEAD",
                        description=f"Head scaling deviates {head_error:.1f}% from affinity laws",
                        severity="WARNING",
                        data_points=[{
                            "diameter_1": d1, "diameter_2": d2,
                            "expected_ratio": expected_head_ratio,
                            "actual_ratio": actual_head_ratio
                        }]
                    ))
        
        return issues
    
    def run_performance_audit(self) -> Dict[str, Any]:
        """Run comprehensive performance data audit"""
        logger.info("Starting performance data audit...")
        
        catalog_data = self.load_catalog()
        pump_models = catalog_data.get('pump_models', [])
        
        total_curves = 0
        total_points = 0
        
        for pump_model in pump_models:
            pump_code = pump_model.get('pump_code', 'Unknown')
            curves = pump_model.get('curves', [])
            
            total_curves += len(curves)
            
            # Validate each curve
            for curve in curves:
                points = curve.get('performance_points', [])
                total_points += len(points)
                
                curve_issues = self.validate_performance_curve(pump_code, curve)
                self.issues.extend(curve_issues)
            
            # Validate BEP calculations
            bep_issues = self.validate_bep_calculation(pump_code, curves)
            self.issues.extend(bep_issues)
            
            # Validate impeller scaling
            scaling_issues = self.validate_impeller_scaling(pump_code, curves)
            self.issues.extend(scaling_issues)
        
        # Generate summary
        issue_counts = {}
        severity_counts = {"ERROR": 0, "WARNING": 0}
        
        for issue in self.issues:
            issue_type = issue.issue_type
            severity = issue.severity
            
            issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
            severity_counts[severity] += 1
        
        performance_score = max(0, 100 - (severity_counts["ERROR"] * 5 + severity_counts["WARNING"] * 1))
        
        summary = {
            "audit_timestamp": "2025-06-17T09:15:00",
            "total_pumps": len(pump_models),
            "total_curves": total_curves,
            "total_data_points": total_points,
            "total_issues": len(self.issues),
            "performance_quality_score": performance_score,
            "error_issues": severity_counts["ERROR"],
            "warning_issues": severity_counts["WARNING"],
            "issue_breakdown": issue_counts,
            "issues": [
                {
                    "pump_code": issue.pump_code,
                    "curve_id": issue.curve_id,
                    "type": issue.issue_type,
                    "description": issue.description,
                    "severity": issue.severity
                }
                for issue in self.issues[:50]  # Top 50 issues
            ]
        }
        
        logger.info(f"Performance audit complete: {len(self.issues)} issues found")
        return summary

def main():
    """Run performance data audit"""
    auditor = PerformanceDataAuditor()
    results = auditor.run_performance_audit()
    
    print("\n" + "="*60)
    print("PERFORMANCE DATA AUDIT RESULTS")
    print("="*60)
    print(f"Total pumps: {results['total_pumps']}")
    print(f"Total curves: {results['total_curves']}")
    print(f"Total data points: {results['total_data_points']}")
    print(f"Performance quality score: {results['performance_quality_score']:.1f}%")
    print(f"Total issues: {results['total_issues']}")
    print(f"Error issues: {results['error_issues']}")
    print(f"Warning issues: {results['warning_issues']}")
    
    print(f"\nIssue breakdown:")
    for issue_type, count in results['issue_breakdown'].items():
        print(f"  {issue_type}: {count}")
    
    # Save detailed report
    with open("performance_audit_report.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed report saved to performance_audit_report.json")
    
    if results['error_issues'] == 0 and results['warning_issues'] < 10:
        print("\n✅ Performance data quality is excellent")
    elif results['error_issues'] == 0:
        print("\n⚠️  Performance data quality is good with minor issues")
    else:
        print(f"\n⚠️  Performance data has {results['error_issues']} critical issues")
    
    return results

if __name__ == "__main__":
    main()