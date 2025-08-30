-- Brain Overlay Schema for Enterprise-Grade Data Corrections and Configuration Management
-- This schema provides a safe overlay system for the golden source database
-- All corrections are applied in-memory without modifying the original data

-- Create the brain_overlay schema
CREATE SCHEMA IF NOT EXISTS brain_overlay;

-- Set search path to include both schemas
-- SET search_path TO brain_overlay, public;

-- ============================================================================
-- DATA QUALITY AND CORRECTIONS TABLES
-- ============================================================================

-- Data quality issue detection and tracking
CREATE TABLE brain_overlay.data_quality_issues (
    id SERIAL PRIMARY KEY,
    pump_code VARCHAR(100) NOT NULL,
    pump_id INTEGER REFERENCES public.pumps(id),
    issue_type VARCHAR(50) NOT NULL, -- 'bep_mismatch', 'efficiency_outlier', 'missing_curve', 'specification_error'
    field_name VARCHAR(100), -- specific field that has the issue
    expected_value NUMERIC(12,4), -- what the value should be
    actual_value NUMERIC(12,4), -- what the value currently is
    severity VARCHAR(20) NOT NULL DEFAULT 'minor', -- 'critical', 'major', 'minor'
    description TEXT,
    source_reference TEXT, -- reference to source document or calculation
    detected_by VARCHAR(100), -- user or system that detected the issue
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_by VARCHAR(100),
    reviewed_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'open', -- 'open', 'in_review', 'resolved', 'false_positive'
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data correction overlay system - the core of the brain intelligence
CREATE TABLE brain_overlay.data_corrections (
    id SERIAL PRIMARY KEY,
    pump_code VARCHAR(100) NOT NULL,
    pump_id INTEGER REFERENCES public.pumps(id),
    correction_type VARCHAR(50) NOT NULL, -- 'specification', 'performance', 'calculation', 'curve_data'
    field_path VARCHAR(200) NOT NULL, -- JSON path to field (e.g., 'bep_head_m', 'curves.max_impeller.efficiency_at_bep')
    table_name VARCHAR(100), -- which golden source table is affected
    record_id INTEGER, -- specific record ID in golden source
    original_value TEXT, -- original value from golden source
    corrected_value TEXT NOT NULL, -- corrected value to apply
    value_type VARCHAR(20) DEFAULT 'numeric', -- 'numeric', 'text', 'boolean', 'json'
    justification TEXT NOT NULL, -- detailed explanation for the correction
    source VARCHAR(100) NOT NULL, -- 'manufacturer_datasheet', 'calculation_error', 'interpolation_fix', 'user_correction'
    confidence_score NUMERIC(3,2) DEFAULT 1.0, -- 0.0 to 1.0 confidence in correction
    impact_assessment TEXT, -- expected impact of the correction
    proposed_by VARCHAR(100) NOT NULL,
    approved_by VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'active', 'rejected', 'superseded', 'test_only'
    effective_date TIMESTAMP, -- when correction becomes active
    expiry_date TIMESTAMP, -- when correction should be reviewed again
    test_results JSONB, -- results from testing this correction
    related_issue_id INTEGER REFERENCES brain_overlay.data_quality_issues(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activated_at TIMESTAMP,
    deactivated_at TIMESTAMP
);

-- ============================================================================
-- BRAIN CONFIGURATION MANAGEMENT
-- ============================================================================

-- Brain configuration profiles for different scenarios
CREATE TABLE brain_overlay.brain_configurations (
    id SERIAL PRIMARY KEY,
    profile_name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(200),
    description TEXT,
    category VARCHAR(50) DEFAULT 'general', -- 'general', 'high_efficiency', 'low_npsh', 'custom'
    scoring_config JSONB NOT NULL, -- Complete scoring weights and parameters
    logic_flags JSONB, -- Feature toggles and behavior flags
    correction_rules JSONB, -- Rules for which corrections to apply
    validation_rules JSONB, -- Custom validation rules for this profile
    use_case_description TEXT, -- when to use this configuration
    is_active BOOLEAN DEFAULT FALSE,
    is_default BOOLEAN DEFAULT FALSE,
    is_production BOOLEAN DEFAULT FALSE,
    requires_approval BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(100) NOT NULL,
    approved_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    last_used_at TIMESTAMP
);

-- Configuration change history for audit trail
CREATE TABLE brain_overlay.configuration_history (
    id SERIAL PRIMARY KEY,
    configuration_id INTEGER REFERENCES brain_overlay.brain_configurations(id),
    change_type VARCHAR(50), -- 'created', 'updated', 'activated', 'deactivated'
    field_changed VARCHAR(100),
    old_value JSONB,
    new_value JSONB,
    reason TEXT,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- DECISION TRACKING AND AUDIT TRAIL
-- ============================================================================

-- Comprehensive decision audit trail
CREATE TABLE brain_overlay.decision_traces (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    trace_type VARCHAR(50) DEFAULT 'selection', -- 'selection', 'comparison', 'validation'
    duty_flow_m3hr NUMERIC(10,3) NOT NULL,
    duty_head_m NUMERIC(10,3) NOT NULL,
    additional_parameters JSONB, -- fluid properties, temperature, etc.
    brain_config_id INTEGER REFERENCES brain_overlay.brain_configurations(id),
    config_snapshot JSONB, -- snapshot of configuration at decision time
    corrections_applied JSONB, -- array of correction IDs that were applied
    data_quality_flags JSONB, -- any data quality issues encountered
    pump_rankings JSONB NOT NULL, -- complete ranking with scores
    selected_pump_code VARCHAR(100),
    selection_reason TEXT,
    decision_factors JSONB, -- detailed scoring breakdown for each pump
    processing_time_ms INTEGER,
    warnings JSONB, -- any warnings or cautions raised
    user_context JSONB, -- user info, IP, etc. for audit purposes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance analysis results for comparison
CREATE TABLE brain_overlay.performance_analyses (
    id SERIAL PRIMARY KEY,
    decision_trace_id INTEGER REFERENCES brain_overlay.decision_traces(id),
    pump_code VARCHAR(100) NOT NULL,
    analysis_type VARCHAR(50), -- 'efficiency', 'npsh', 'power', 'lifecycle_cost'
    calculated_values JSONB, -- all calculated performance values
    manufacturer_values JSONB, -- claimed manufacturer values
    variance_analysis JSONB, -- differences between calculated and claimed
    confidence_metrics JSONB, -- confidence in calculations
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- MANUFACTURER COMPARISON DATA
-- ============================================================================

-- External manufacturer selection data for comparison and learning
CREATE TABLE brain_overlay.manufacturer_selections (
    id SERIAL PRIMARY KEY,
    source_type VARCHAR(20) NOT NULL, -- 'manual', 'pdf_extract', 'csv_import', 'api_import'
    manufacturer_name VARCHAR(100),
    document_reference VARCHAR(255), -- reference to source document
    duty_flow_m3hr NUMERIC(10,3) NOT NULL,
    duty_head_m NUMERIC(10,3) NOT NULL,
    fluid_properties JSONB, -- viscosity, temperature, specific gravity
    application_context TEXT, -- building, industry, specific use case
    selected_pump_model VARCHAR(100) NOT NULL,
    claimed_efficiency NUMERIC(5,2),
    claimed_power_kw NUMERIC(10,3),
    claimed_npsh_m NUMERIC(8,2),
    claimed_impeller_diameter_mm NUMERIC(8,2),
    operating_speed_rpm INTEGER,
    additional_specs JSONB, -- any other specifications
    selection_rationale TEXT, -- manufacturer's stated reason for selection
    document_path VARCHAR(500), -- path to source document
    extraction_confidence NUMERIC(3,2), -- AI extraction confidence (0-1)
    verification_status VARCHAR(20) DEFAULT 'unverified', -- 'unverified', 'verified', 'disputed'
    verified_by VARCHAR(100),
    verified_at TIMESTAMP,
    notes TEXT,
    entered_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Comparison results between Brain and manufacturer selections
CREATE TABLE brain_overlay.selection_comparisons (
    id SERIAL PRIMARY KEY,
    manufacturer_selection_id INTEGER REFERENCES brain_overlay.manufacturer_selections(id),
    brain_decision_trace_id INTEGER REFERENCES brain_overlay.decision_traces(id),
    comparison_type VARCHAR(50) DEFAULT 'standard', -- 'standard', 'detailed', 'ml_analysis'
    brain_selection JSONB NOT NULL, -- Brain's complete selection result
    manufacturer_selection JSONB NOT NULL, -- manufacturer's selection data
    delta_analysis JSONB NOT NULL, -- structured comparison results
    agreement_score NUMERIC(5,2), -- 0-100 score of how well they agree
    key_differences JSONB, -- most significant differences
    explanation TEXT, -- AI-generated explanation of differences
    learning_insights JSONB, -- insights for improving Brain logic
    follow_up_actions JSONB, -- recommended actions based on comparison
    analyst_notes TEXT,
    analyzed_by VARCHAR(100),
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Data quality and corrections indexes
CREATE INDEX idx_data_quality_pump_code ON brain_overlay.data_quality_issues(pump_code);
CREATE INDEX idx_data_quality_status ON brain_overlay.data_quality_issues(status);
CREATE INDEX idx_data_quality_severity ON brain_overlay.data_quality_issues(severity);

CREATE INDEX idx_corrections_pump_code ON brain_overlay.data_corrections(pump_code);
CREATE INDEX idx_corrections_status ON brain_overlay.data_corrections(status);
CREATE INDEX idx_corrections_type ON brain_overlay.data_corrections(correction_type);

-- Configuration and decision tracking indexes
CREATE INDEX idx_brain_config_active ON brain_overlay.brain_configurations(is_active);
CREATE INDEX idx_brain_config_production ON brain_overlay.brain_configurations(is_production);

CREATE INDEX idx_decision_traces_session ON brain_overlay.decision_traces(session_id);
CREATE INDEX idx_decision_traces_duty ON brain_overlay.decision_traces(duty_flow_m3hr, duty_head_m);
CREATE INDEX idx_decision_traces_pump ON brain_overlay.decision_traces(selected_pump_code);
CREATE INDEX idx_decision_traces_created ON brain_overlay.decision_traces(created_at);

-- Manufacturer comparison indexes
CREATE INDEX idx_manufacturer_selections_duty ON brain_overlay.manufacturer_selections(duty_flow_m3hr, duty_head_m);
CREATE INDEX idx_manufacturer_selections_manufacturer ON brain_overlay.manufacturer_selections(manufacturer_name);
CREATE INDEX idx_selection_comparisons_agreement ON brain_overlay.selection_comparisons(agreement_score);

-- ============================================================================
-- VIEWS FOR EASY ACCESS
-- ============================================================================

-- Active corrections view
CREATE VIEW brain_overlay.active_corrections AS
SELECT 
    pump_code,
    correction_type,
    field_path,
    corrected_value,
    justification,
    confidence_score,
    activated_at
FROM brain_overlay.data_corrections 
WHERE status = 'active' 
AND (effective_date IS NULL OR effective_date <= CURRENT_TIMESTAMP)
AND (expiry_date IS NULL OR expiry_date > CURRENT_TIMESTAMP);

-- Data quality summary view
CREATE VIEW brain_overlay.data_quality_summary AS
SELECT 
    pump_code,
    COUNT(*) as total_issues,
    COUNT(*) FILTER (WHERE severity = 'critical') as critical_issues,
    COUNT(*) FILTER (WHERE severity = 'major') as major_issues,
    COUNT(*) FILTER (WHERE severity = 'minor') as minor_issues,
    COUNT(*) FILTER (WHERE status = 'open') as open_issues,
    MAX(detected_at) as last_issue_detected
FROM brain_overlay.data_quality_issues 
GROUP BY pump_code;

-- Production configuration view
CREATE VIEW brain_overlay.production_config AS
SELECT * FROM brain_overlay.brain_configurations 
WHERE is_production = TRUE AND is_active = TRUE 
LIMIT 1;

-- ============================================================================
-- INITIAL DATA SETUP
-- ============================================================================

-- Insert default production configuration
INSERT INTO brain_overlay.brain_configurations (
    profile_name, 
    display_name,
    description,
    category,
    scoring_config,
    logic_flags,
    correction_rules,
    is_default,
    is_production,
    is_active,
    created_by
) VALUES (
    'production_default',
    'Production Default Configuration',
    'Default production configuration based on current Brain system settings',
    'general',
    '{
        "bep_proximity_weight": 45,
        "efficiency_weight": 35,
        "head_margin_weight": 20,
        "npsh_weight": 0,
        "trim_penalty_factor": 2.0,
        "max_trim_percentage": 15.0,
        "bep_optimal_range": [0.95, 1.05],
        "efficiency_brackets": {
            "excellent": 85.0,
            "good": 75.0,
            "fair": 65.0,
            "minimum": 40.0
        }
    }',
    '{
        "enable_impeller_trimming": true,
        "enable_speed_variation": false,
        "strict_npsh_gates": true,
        "enforce_qbp_limits": true,
        "use_affinity_laws": true
    }',
    '{
        "apply_all_active": true,
        "minimum_confidence": 0.8,
        "require_approval": true
    }',
    true,
    true,
    true,
    'system'
);

-- Grant appropriate permissions
GRANT USAGE ON SCHEMA brain_overlay TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA brain_overlay TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA brain_overlay TO postgres;