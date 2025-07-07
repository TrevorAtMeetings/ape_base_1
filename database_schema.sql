-- PostgreSQL Database Schema for Pump Selection System
-- This reflects the actual current database structure

-- Processed Files Table (tracks which files have been processed)
CREATE TABLE IF NOT EXISTS processed_files (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Pumps Table (main pump catalog)
CREATE TABLE IF NOT EXISTS pumps (
    id SERIAL PRIMARY KEY,
    pump_code VARCHAR(100) NOT NULL UNIQUE,
    manufacturer VARCHAR(100),
    pump_type VARCHAR(50),
    series VARCHAR(50),
    application_category VARCHAR(100),
    construction_standard VARCHAR(50),
    impeller_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Pump Specifications Table (detailed specifications for each pump)
CREATE TABLE IF NOT EXISTS pump_specifications (
    id SERIAL PRIMARY KEY,
    pump_id INTEGER NOT NULL REFERENCES pumps(id) ON DELETE CASCADE,
    test_speed_rpm INTEGER,
    max_flow_m3hr NUMERIC(10,2),
    max_head_m NUMERIC(10,2),
    max_power_kw NUMERIC(10,2),
    bep_flow_m3hr NUMERIC(10,2),
    bep_head_m NUMERIC(10,2),
    npshr_at_bep NUMERIC(8,2),
    min_impeller_diameter_mm NUMERIC(8,2),
    max_impeller_diameter_mm NUMERIC(8,2),
    min_speed_rpm INTEGER,
    max_speed_rpm INTEGER,
    variable_speed BOOLEAN,
    variable_diameter BOOLEAN,
    UNIQUE(pump_id)
);

-- Pump Curves Table (performance curves for each pump)
CREATE TABLE IF NOT EXISTS pump_curves (
    id SERIAL PRIMARY KEY,
    pump_id INTEGER NOT NULL REFERENCES pumps(id) ON DELETE CASCADE,
    impeller_diameter_mm NUMERIC(8,2) NOT NULL
);

-- Pump Performance Points Table (individual data points for each curve)
CREATE TABLE IF NOT EXISTS pump_performance_points (
    id SERIAL PRIMARY KEY,
    curve_id INTEGER NOT NULL REFERENCES pump_curves(id) ON DELETE CASCADE,
    operating_point INTEGER NOT NULL,
    flow_rate NUMERIC(10,2),
    head NUMERIC(10,2),
    efficiency NUMERIC(5,2),
    npshr NUMERIC(8,2),
    UNIQUE(curve_id, operating_point)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_pump_curves_pump_id ON pump_curves(pump_id);
CREATE INDEX IF NOT EXISTS idx_pump_performance_points_curve_id ON pump_performance_points(curve_id);
CREATE INDEX IF NOT EXISTS idx_pump_specifications_pump_id ON pump_specifications(pump_id);
CREATE INDEX IF NOT EXISTS idx_pumps_pump_code ON pumps(pump_code);

-- Sample data insertion (example)
-- INSERT INTO pumps (pump_code, manufacturer, pump_type, series, application_category, construction_standard, impeller_type) 
-- VALUES ('100-200 2F', 'APE PUMPS', 'END SUCTION', '2F', 'WATER SUPPLY', 'BS', 'RADIAL');

-- INSERT INTO pump_specifications (pump_id, test_speed_rpm, max_flow_m3hr, max_head_m, bep_flow_m3hr, bep_head_m, min_impeller_diameter_mm, max_impeller_diameter_mm, variable_speed, variable_diameter)
-- VALUES (1, 1450, 194.8, 15.0, 137.22, 14.03, 184.0, 217.0, TRUE, TRUE);

-- INSERT INTO pump_curves (pump_id, impeller_diameter_mm)
-- VALUES (1, 184.0);

-- INSERT INTO pump_performance_points (curve_id, operating_point, flow_rate, head, efficiency, npshr)
-- VALUES 
--     (1, 1, 0.0, 9.3, 0.0, 2.4),
--     (1, 2, 57.1, 9.1, 60.0, 2.4),
--     (1, 3, 67.3, 9.0, 65.0, 2.5),
--     (1, 4, 100.7, 7.9, 70.0, 3.7),
--     (1, 5, 125.9, 6.3, 65.0, 5.7),
--     (1, 6, 133.1, 5.7, 62.0, 6.3); 