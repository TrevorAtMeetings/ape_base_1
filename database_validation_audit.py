#!/usr/bin/env python3
"""
Comprehensive Database Validation Audit System
Validates APE catalog database against authentic source data files
"""

import json
import os
import re
import logging
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ValidationIssue:
    """Represents a data validation issue"""
    pump_code: str
    issue_type: str
    field: str
    expected: Any
    actual: Any
    severity: str = "WARNING"  # WARNING, ERROR, CRITICAL
    source_file: str = ""
    description: str = ""

@dataclass
class ValidationReport:
    """Complete validation report"""
    total_pumps_checked: int = 0
    total_issues_found: int = 0
    critical_issues: int = 0
    error_issues: int = 0
    warning_issues: int = 0
    issues: List[ValidationIssue] = field(default_factory=list)
    missing_source_files: List[str] = field(default_factory=list)
    orphaned_database_entries: List[str] = field(default_factory=list)
    data_integrity_score: float = 0.0
    
    def add_issue(self, issue: ValidationIssue):
        """Add validation issue and update counters"""
        self.issues.append(issue)
        self.total_issues_found += 1
        
        if issue.severity == "CRITICAL":
            self.critical_issues += 1
        elif issue.severity == "ERROR":
            self.error_issues += 1
        else:
            self.warning_issues += 1
    
    def calculate_integrity_score(self):
        """Calculate overall data integrity score (0-100)"""
        if self.total_pumps_checked == 0:
            self.data_integrity_score = 0.0
            return
        
        # Weight issues by severity
        weighted_issues = (
            self.critical_issues * 3.0 +
            self.error_issues * 2.0 +
            self.warning_issues * 1.0
        )
        
        max_possible_score = self.total_pumps_checked * 3.0
        score = max(0, (max_possible_score - weighted_issues) / max_possible_score * 100)
        self.data_integrity_score = round(score, 2)

class DatabaseValidator:
    """Comprehensive database validation system"""
    
    def __init__(self, catalog_path: str = "data/ape_catalog_database.json", 
                 source_dir: str = "data/pump_data"):
        self.catalog_path = catalog_path
        self.source_dir = source_dir
        self.report = ValidationReport()
        
    def load_source_data(self, pump_code: str) -> Dict[str, Any]:
        """Load and parse source data file for a pump"""
        # Convert pump code to various filename patterns
        patterns = [
            pump_code.lower().replace('/', '_').replace(' ', '_').replace('(', '').replace(')', ''),
            pump_code.lower().replace('/', '_').replace(' ', '_').replace('-', '_'),
            pump_code.lower().replace(' ', '_').replace('/', '_'),
            pump_code.lower().replace(' ', '').replace('/', '_')
        ]
        
        for pattern in patterns:
            filepath = os.path.join(self.source_dir, pattern + '.txt')
            if os.path.exists(filepath):
                return self._parse_source_file(filepath)
        
        return {}
    
    def _parse_source_file(self, filepath: str) -> Dict[str, Any]:
        """Parse source data file with error handling"""
        try:
            with open(filepath, 'r') as f:
                content = f.read().strip()
                
                # Fix common JSON formatting issues
                if content.endswith(',\n}') or content.endswith(',}'):
                    content = content.replace(',\n}', '\n}').replace(',}', '}')
                
                if content.startswith('{') and content.endswith('}'):
                    return json.loads(content)
                    
        except json.JSONDecodeError:
            # Extract data using regex if JSON parsing fails
            try:
                return self._extract_data_with_regex(content)
            except Exception:
                pass
        except Exception:
            pass
        
        return {}
    
    def _extract_data_with_regex(self, content: str) -> Dict[str, Any]:
        """Extract pump data using regex patterns"""
        data = {}
        
        # Key field patterns
        patterns = {
            'objPump.pPumpCode': r'"objPump\.pPumpCode":"([^"]*)"',
            'objPump.pSuppName': r'"objPump\.pSuppName":"([^"]*)"',
            'objPump.pFilter3': r'"objPump\.pFilter3":"([^"]*)"',
            'objPump.pFilter4': r'"objPump\.pFilter4":"([^"]*)"',
            'objPump.pFilter7': r'"objPump\.pFilter7":"([^"]*)"',
            'objPump.pMaxQ': r'"objPump\.pMaxQ":"([^"]*)"',
            'objPump.pMaxH': r'"objPump\.pMaxH":"([^"]*)"',
            'objPump.pBEPFlowStd': r'"objPump\.pBEPFlowStd":"([^"]*)"',
            'objPump.pBEPHeadStd': r'"objPump\.pBEPHeadStd":"([^"]*)"',
            'objPump.pMinImpD': r'"objPump\.pMinImpD":"([^"]*)"',
            'objPump.pMaxImpD': r'"objPump\.pMaxImpD":"([^"]*)"',
            'objPump.pPumpTestSpeed': r'"objPump\.pPumpTestSpeed":"([^"]*)"',
            'objPump.pHeadCurvesNo': r'"objPump\.pHeadCurvesNo":"([^"]*)"'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, content)
            if match:
                data[key] = match.group(1)
        
        return data
    
    def validate_pump_specifications(self, pump_model: Dict[str, Any], 
                                   source_data: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate pump specifications against source data"""
        issues = []
        pump_code = pump_model.get('pump_code', 'Unknown')
        
        # Validate max flow
        if 'objPump.pMaxQ' in source_data:
            try:
                source_max_flow = float(source_data['objPump.pMaxQ'])
                db_max_flow = pump_model.get('specifications', {}).get('max_flow_m3hr', 0)
                
                if abs(source_max_flow - db_max_flow) > 0.1:
                    issues.append(ValidationIssue(
                        pump_code=pump_code,
                        issue_type="SPECIFICATION_MISMATCH",
                        field="max_flow_m3hr",
                        expected=source_max_flow,
                        actual=db_max_flow,
                        severity="ERROR",
                        description=f"Max flow mismatch: expected {source_max_flow}, got {db_max_flow}"
                    ))
            except (ValueError, TypeError):
                pass
        
        # Validate max head
        if 'objPump.pMaxH' in source_data:
            try:
                source_max_head = float(source_data['objPump.pMaxH'])
                db_max_head = pump_model.get('specifications', {}).get('max_head_m', 0)
                
                if abs(source_max_head - db_max_head) > 0.1:
                    issues.append(ValidationIssue(
                        pump_code=pump_code,
                        issue_type="SPECIFICATION_MISMATCH",
                        field="max_head_m",
                        expected=source_max_head,
                        actual=db_max_head,
                        severity="ERROR",
                        description=f"Max head mismatch: expected {source_max_head}, got {db_max_head}"
                    ))
            except (ValueError, TypeError):
                pass
        
        # Validate impeller diameters
        if 'objPump.pMinImpD' in source_data and 'objPump.pMaxImpD' in source_data:
            try:
                source_min_imp = float(source_data['objPump.pMinImpD'])
                source_max_imp = float(source_data['objPump.pMaxImpD'])
                
                specs = pump_model.get('specifications', {})
                db_min_imp = specs.get('min_impeller_mm', 0)
                db_max_imp = specs.get('max_impeller_mm', 0)
                
                if abs(source_min_imp - db_min_imp) > 0.1:
                    issues.append(ValidationIssue(
                        pump_code=pump_code,
                        issue_type="SPECIFICATION_MISMATCH",
                        field="min_impeller_mm",
                        expected=source_min_imp,
                        actual=db_min_imp,
                        severity="WARNING",
                        description=f"Min impeller diameter mismatch"
                    ))
                
                if abs(source_max_imp - db_max_imp) > 0.1:
                    issues.append(ValidationIssue(
                        pump_code=pump_code,
                        issue_type="SPECIFICATION_MISMATCH",
                        field="max_impeller_mm",
                        expected=source_max_imp,
                        actual=db_max_imp,
                        severity="WARNING",
                        description=f"Max impeller diameter mismatch"
                    ))
            except (ValueError, TypeError):
                pass
        
        # Validate test speed
        if 'objPump.pPumpTestSpeed' in source_data:
            try:
                source_speed = float(source_data['objPump.pPumpTestSpeed'])
                db_speed = pump_model.get('specifications', {}).get('test_speed_rpm', 0)
                
                if abs(source_speed - db_speed) > 10:  # Allow 10 RPM tolerance
                    issues.append(ValidationIssue(
                        pump_code=pump_code,
                        issue_type="SPECIFICATION_MISMATCH",
                        field="test_speed_rpm",
                        expected=source_speed,
                        actual=db_speed,
                        severity="WARNING",
                        description=f"Test speed mismatch: expected {source_speed}, got {db_speed}"
                    ))
            except (ValueError, TypeError):
                pass
        
        return issues
    
    def validate_pump_type(self, pump_model: Dict[str, Any], 
                          source_data: Dict[str, Any]) -> Optional[ValidationIssue]:
        """Validate pump type classification"""
        pump_code = pump_model.get('pump_code', 'Unknown')
        current_type = pump_model.get('pump_type', '')
        
        # Determine correct type from source
        filter3 = source_data.get('objPump.pFilter3', '').upper()
        filter4 = source_data.get('objPump.pFilter4', '').upper()
        
        expected_type = self._determine_correct_pump_type(filter3, filter4, pump_code)
        
        if expected_type != current_type:
            return ValidationIssue(
                pump_code=pump_code,
                issue_type="PUMP_TYPE_MISMATCH",
                field="pump_type",
                expected=expected_type,
                actual=current_type,
                severity="ERROR",
                description=f"Pump type mismatch: source indicates {expected_type}, database has {current_type}"
            )
        
        return None
    
    def _determine_correct_pump_type(self, filter3: str, filter4: str, pump_code: str) -> str:
        """Determine correct pump type from source data"""
        if filter3 == 'HSC':
            return 'HSC'
        elif 'VTP' in filter4 or 'VTP' in pump_code:
            return 'VTP'
        elif 'ALE' in filter4 or 'BLE' in filter4:
            return 'AXIAL_FLOW'
        elif any(stage in pump_code.upper() for stage in ['2P', '3P', '4P', '6P', '8P', '2 STAGE', '3 STAGE']):
            return 'MULTISTAGE'
        elif 'HIGH_SPEED' in filter3 or pump_code.upper().endswith(' HSC'):
            return 'HIGH_SPEED_CENTRIFUGAL'
        else:
            return 'END_SUCTION'
    
    def validate_curve_data(self, pump_model: Dict[str, Any], 
                           source_data: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate performance curve data"""
        issues = []
        pump_code = pump_model.get('pump_code', 'Unknown')
        
        # Check curve count
        if 'objPump.pHeadCurvesNo' in source_data:
            try:
                source_curve_count = int(source_data['objPump.pHeadCurvesNo'])
                db_curve_count = len(pump_model.get('curves', []))
                
                if source_curve_count != db_curve_count:
                    issues.append(ValidationIssue(
                        pump_code=pump_code,
                        issue_type="CURVE_COUNT_MISMATCH",
                        field="curves",
                        expected=source_curve_count,
                        actual=db_curve_count,
                        severity="ERROR",
                        description=f"Curve count mismatch: expected {source_curve_count}, got {db_curve_count}"
                    ))
            except (ValueError, TypeError):
                pass
        
        return issues
    
    def run_comprehensive_audit(self) -> ValidationReport:
        """Run complete database validation audit"""
        logger.info("Starting comprehensive database validation audit...")
        
        # Load catalog database
        try:
            with open(self.catalog_path, 'r') as f:
                catalog_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load catalog database: {e}")
            return self.report
        
        pump_models = catalog_data.get('pump_models', [])
        self.report.total_pumps_checked = len(pump_models)
        
        logger.info(f"Validating {len(pump_models)} pump models...")
        
        # Validate each pump
        for i, pump_model in enumerate(pump_models):
            pump_code = pump_model.get('pump_code', f'Unknown_{i}')
            
            if i % 50 == 0:
                logger.info(f"Progress: {i}/{len(pump_models)} pumps validated")
            
            # Load source data
            source_data = self.load_source_data(pump_code)
            
            if not source_data:
                self.report.missing_source_files.append(pump_code)
                self.report.add_issue(ValidationIssue(
                    pump_code=pump_code,
                    issue_type="MISSING_SOURCE_FILE",
                    field="source_file",
                    expected="Source file exists",
                    actual="Source file not found",
                    severity="CRITICAL",
                    description="No source data file found for pump"
                ))
                continue
            
            # Validate pump specifications
            spec_issues = self.validate_pump_specifications(pump_model, source_data)
            for issue in spec_issues:
                self.report.add_issue(issue)
            
            # Validate pump type
            type_issue = self.validate_pump_type(pump_model, source_data)
            if type_issue:
                self.report.add_issue(type_issue)
            
            # Validate curve data
            curve_issues = self.validate_curve_data(pump_model, source_data)
            for issue in curve_issues:
                self.report.add_issue(issue)
        
        # Calculate integrity score
        self.report.calculate_integrity_score()
        
        logger.info("Database validation audit complete")
        return self.report
    
    def generate_validation_report(self, output_file: str = "database_validation_report.json"):
        """Generate detailed validation report"""
        report_data = {
            "audit_timestamp": datetime.now().isoformat(),
            "summary": {
                "total_pumps_checked": self.report.total_pumps_checked,
                "total_issues_found": self.report.total_issues_found,
                "data_integrity_score": self.report.data_integrity_score,
                "critical_issues": self.report.critical_issues,
                "error_issues": self.report.error_issues,
                "warning_issues": self.report.warning_issues
            },
            "missing_source_files": self.report.missing_source_files,
            "orphaned_database_entries": self.report.orphaned_database_entries,
            "issues_by_type": {},
            "issues_by_severity": {
                "CRITICAL": [],
                "ERROR": [],
                "WARNING": []
            },
            "top_issues": []
        }
        
        # Group issues by type
        for issue in self.report.issues:
            issue_type = issue.issue_type
            if issue_type not in report_data["issues_by_type"]:
                report_data["issues_by_type"][issue_type] = []
            
            issue_dict = {
                "pump_code": issue.pump_code,
                "field": issue.field,
                "expected": issue.expected,
                "actual": issue.actual,
                "description": issue.description
            }
            
            report_data["issues_by_type"][issue_type].append(issue_dict)
            report_data["issues_by_severity"][issue.severity].append(issue_dict)
        
        # Save report
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Validation report saved to {output_file}")
        return report_data

def main():
    """Run database validation audit"""
    validator = DatabaseValidator()
    report = validator.run_comprehensive_audit()
    
    print("\n" + "="*60)
    print("DATABASE VALIDATION AUDIT RESULTS")
    print("="*60)
    print(f"Total pumps checked: {report.total_pumps_checked}")
    print(f"Total issues found: {report.total_issues_found}")
    print(f"Data integrity score: {report.data_integrity_score:.1f}%")
    print(f"Critical issues: {report.critical_issues}")
    print(f"Error issues: {report.error_issues}")
    print(f"Warning issues: {report.warning_issues}")
    print(f"Missing source files: {len(report.missing_source_files)}")
    
    if report.critical_issues > 0:
        print(f"\n⚠️  CRITICAL ISSUES DETECTED - Database integrity compromised")
    elif report.error_issues > 0:
        print(f"\n⚠️  ERRORS DETECTED - Data quality issues found")
    elif report.warning_issues > 0:
        print(f"\n⚠️  WARNINGS - Minor data inconsistencies found")
    else:
        print(f"\n✅ Database validation passed - No issues detected")
    
    # Generate detailed report
    validator.generate_validation_report()
    
    return report

if __name__ == "__main__":
    main()