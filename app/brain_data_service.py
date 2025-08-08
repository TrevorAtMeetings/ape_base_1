"""
Brain Data Service - Core correction and configuration management system
Implements the enterprise-grade two-schema architecture with golden source protection
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@dataclass
class DataCorrection:
    """Represents a data correction from the overlay system"""
    id: int
    pump_code: str
    correction_type: str
    field_path: str
    original_value: str
    corrected_value: str
    justification: str
    confidence_score: float
    status: str

@dataclass
class QualityIssue:
    """Represents a data quality issue"""
    id: int
    pump_code: str
    issue_type: str
    field_name: str
    expected_value: Optional[float]
    actual_value: Optional[float]
    severity: str
    description: str

class BrainDataService:
    """
    Core service for Brain overlay system data management.
    Provides safe, auditable access to corrections and configurations.
    """
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL is required")
        
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = psycopg2.connect(self.database_url)
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    # ============================================================================
    # DATA CORRECTION MANAGEMENT
    # ============================================================================
    
    def get_active_corrections(self, pump_code: str = None) -> List[DataCorrection]:
        """Get all active corrections, optionally filtered by pump code"""
        query = """
            SELECT id, pump_code, correction_type, field_path, 
                   original_value, corrected_value, justification, 
                   confidence_score, status
            FROM brain_overlay.data_corrections
            WHERE status = 'active'
            AND (effective_date IS NULL OR effective_date <= CURRENT_TIMESTAMP)
            AND (expiry_date IS NULL OR expiry_date > CURRENT_TIMESTAMP)
        """
        params = []
        
        if pump_code:
            query += " AND pump_code = %s"
            params.append(pump_code)
            
        query += " ORDER BY pump_code, field_path"
        
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
                
                return [
                    DataCorrection(
                        id=row['id'],
                        pump_code=row['pump_code'],
                        correction_type=row['correction_type'],
                        field_path=row['field_path'],
                        original_value=row['original_value'],
                        corrected_value=row['corrected_value'],
                        justification=row['justification'],
                        confidence_score=float(row['confidence_score']),
                        status=row['status']
                    )
                    for row in rows
                ]
    
    def propose_correction(self, pump_code: str, field_path: str, 
                          corrected_value: str, justification: str,
                          correction_type: str = 'specification',
                          original_value: str = None,
                          confidence_score: float = 1.0,
                          proposed_by: str = 'system') -> int:
        """Propose a new data correction"""
        query = """
            INSERT INTO brain_overlay.data_corrections 
            (pump_code, correction_type, field_path, original_value, 
             corrected_value, justification, confidence_score, proposed_by, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'user_correction')
            RETURNING id
        """
        
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (
                    pump_code, correction_type, field_path, original_value,
                    corrected_value, justification, confidence_score, proposed_by
                ))
                correction_id = cur.fetchone()[0]
                conn.commit()
                
                logger.info(f"Proposed correction {correction_id} for {pump_code}.{field_path}")
                return correction_id
    
    def approve_correction(self, correction_id: int, approved_by: str) -> bool:
        """Approve a pending correction"""
        query = """
            UPDATE brain_overlay.data_corrections 
            SET status = 'active', 
                approved_by = %s, 
                activated_at = CURRENT_TIMESTAMP,
                effective_date = CURRENT_TIMESTAMP
            WHERE id = %s AND status = 'pending'
        """
        
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (approved_by, correction_id))
                updated = cur.rowcount > 0
                conn.commit()
                
                if updated:
                    logger.info(f"Approved correction {correction_id} by {approved_by}")
                return updated
    
    def reject_correction(self, correction_id: int, approved_by: str, reason: str = None) -> bool:
        """Reject a pending correction"""
        query = """
            UPDATE brain_overlay.data_corrections 
            SET status = 'rejected', 
                approved_by = %s,
                deactivated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND status = 'pending'
        """
        
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (approved_by, correction_id))
                updated = cur.rowcount > 0
                conn.commit()
                
                if updated:
                    logger.info(f"Rejected correction {correction_id} by {approved_by}")
                return updated
    
    # ============================================================================
    # DATA QUALITY MANAGEMENT
    # ============================================================================
    
    def log_quality_issue(self, pump_code: str, issue_type: str, 
                         field_name: str, description: str,
                         expected_value: float = None, actual_value: float = None,
                         severity: str = 'minor', detected_by: str = 'system') -> int:
        """Log a data quality issue"""
        query = """
            INSERT INTO brain_overlay.data_quality_issues 
            (pump_code, issue_type, field_name, expected_value, actual_value,
             severity, description, detected_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (
                    pump_code, issue_type, field_name, expected_value, 
                    actual_value, severity, description, detected_by
                ))
                issue_id = cur.fetchone()[0]
                conn.commit()
                
                logger.info(f"Logged quality issue {issue_id} for {pump_code}: {description}")
                return issue_id
    
    def get_quality_issues(self, pump_code: str = None, 
                          status: str = None, severity: str = None) -> List[QualityIssue]:
        """Get quality issues with optional filtering"""
        query = """
            SELECT id, pump_code, issue_type, field_name, expected_value, 
                   actual_value, severity, description
            FROM brain_overlay.data_quality_issues
            WHERE 1=1
        """
        params = []
        
        if pump_code:
            query += " AND pump_code = %s"
            params.append(pump_code)
            
        if status:
            query += " AND status = %s"
            params.append(status)
            
        if severity:
            query += " AND severity = %s"
            params.append(severity)
            
        query += " ORDER BY severity DESC, detected_at DESC"
        
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
                
                return [
                    QualityIssue(
                        id=row['id'],
                        pump_code=row['pump_code'],
                        issue_type=row['issue_type'],
                        field_name=row['field_name'],
                        expected_value=row['expected_value'],
                        actual_value=row['actual_value'],
                        severity=row['severity'],
                        description=row['description']
                    )
                    for row in rows
                ]
    
    # ============================================================================
    # CONFIGURATION MANAGEMENT
    # ============================================================================
    
    def get_production_config(self) -> Dict[str, Any]:
        """Get the active production configuration"""
        query = """
            SELECT profile_name, scoring_config, logic_flags, correction_rules
            FROM brain_overlay.brain_configurations
            WHERE is_production = TRUE AND is_active = TRUE
            ORDER BY created_at DESC
            LIMIT 1
        """
        
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                row = cur.fetchone()
                
                if not row:
                    logger.warning("No production configuration found, using defaults")
                    return self._get_default_config()
                
                return {
                    'profile_name': row['profile_name'],
                    'scoring_config': row['scoring_config'],
                    'logic_flags': row['logic_flags'],
                    'correction_rules': row['correction_rules']
                }
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if none exists"""
        return {
            'profile_name': 'default',
            'scoring_config': {
                'bep_proximity_weight': 45,
                'efficiency_weight': 35,
                'head_margin_weight': 20,
                'npsh_weight': 0,
                'trim_penalty_factor': 2.0,
                'max_trim_percentage': 15.0
            },
            'logic_flags': {
                'enable_impeller_trimming': True,
                'strict_npsh_gates': True,
                'enforce_qbp_limits': True
            },
            'correction_rules': {
                'apply_all_active': True,
                'minimum_confidence': 0.8
            }
        }
    
    # ============================================================================
    # DECISION TRACKING
    # ============================================================================
    
    def log_decision(self, session_id: str, duty_flow: float, duty_head: float,
                    pump_rankings: List[Dict], selected_pump_code: str,
                    corrections_applied: List[int] = None,
                    processing_time_ms: int = None) -> int:
        """Log a Brain decision for audit trail"""
        query = """
            INSERT INTO brain_overlay.decision_traces 
            (session_id, duty_flow_m3hr, duty_head_m, pump_rankings, 
             selected_pump_code, corrections_applied, processing_time_ms)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (
                    session_id, duty_flow, duty_head, json.dumps(pump_rankings),
                    selected_pump_code, json.dumps(corrections_applied or []),
                    processing_time_ms
                ))
                decision_id = cur.fetchone()[0]
                conn.commit()
                
                logger.debug(f"Logged decision {decision_id} for {duty_flow}m³/hr @ {duty_head}m")
                return decision_id


class BrainDataAccessor:
    """
    Enhanced data accessor that applies Brain overlay corrections in-memory
    """
    
    def __init__(self, pump_repository, brain_data_service: BrainDataService):
        self.pump_repo = pump_repository
        self.brain_service = brain_data_service
        self._correction_cache = {}
        self._cache_timestamp = None
    
    def get_enhanced_pump(self, pump_code: str) -> Dict[str, Any]:
        """
        Get pump data with active corrections applied in-memory
        Never modifies the golden source data
        """
        # 1. Load raw pump from golden source
        raw_pump = self.pump_repo.get_pump_by_code(pump_code)
        if not raw_pump:
            return None
        
        # 2. Get active corrections for this pump
        corrections = self._get_cached_corrections(pump_code)
        
        if not corrections:
            # No corrections needed, return original data
            return raw_pump
        
        # 3. Apply corrections in-memory (never write back to database)
        enhanced_pump = self._apply_corrections(raw_pump, corrections)
        
        # 4. Log which corrections were applied
        logger.debug(f"Applied {len(corrections)} corrections to pump {pump_code}")
        
        return enhanced_pump
    
    def _get_cached_corrections(self, pump_code: str) -> List[DataCorrection]:
        """Get corrections with caching for performance"""
        cache_key = f"corrections_{pump_code}"
        
        # Check cache (refresh every 5 minutes)
        if (self._cache_timestamp and 
            (datetime.now() - self._cache_timestamp).seconds < 300 and
            cache_key in self._correction_cache):
            return self._correction_cache[cache_key]
        
        # Refresh from database
        corrections = self.brain_service.get_active_corrections(pump_code)
        self._correction_cache[cache_key] = corrections
        self._cache_timestamp = datetime.now()
        
        return corrections
    
    def _apply_corrections(self, pump_data: Dict, corrections: List[DataCorrection]) -> Dict:
        """Apply corrections to pump data in-memory"""
        enhanced_pump = pump_data.copy()
        
        for correction in corrections:
            try:
                # Parse field path and apply correction
                field_path = correction.field_path
                corrected_value = self._parse_corrected_value(correction.corrected_value)
                
                # Apply correction based on field path
                if field_path.startswith('specifications.'):
                    spec_field = field_path.replace('specifications.', '')
                    if 'specifications' in enhanced_pump:
                        enhanced_pump['specifications'][spec_field] = corrected_value
                elif field_path in enhanced_pump:
                    enhanced_pump[field_path] = corrected_value
                else:
                    # Handle nested field paths
                    self._set_nested_value(enhanced_pump, field_path, corrected_value)
                
                logger.debug(f"Applied correction: {field_path} = {corrected_value}")
                
            except Exception as e:
                logger.warning(f"Failed to apply correction {correction.id}: {e}")
        
        return enhanced_pump
    
    def _parse_corrected_value(self, value_str: str) -> Union[float, int, str, bool]:
        """Parse corrected value to appropriate type"""
        try:
            # Try float first
            if '.' in value_str:
                return float(value_str)
            # Then integer
            return int(value_str)
        except ValueError:
            # Handle boolean
            if value_str.lower() in ['true', 'false']:
                return value_str.lower() == 'true'
            # Return as string
            return value_str
    
    def _set_nested_value(self, obj: Dict, path: str, value: Any):
        """Set value in nested dictionary using dot notation"""
        keys = path.split('.')
        current = obj
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value