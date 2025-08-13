--
-- PostgreSQL database dump
--

-- Dumped from database version 16.9
-- Dumped by pg_dump version 16.9

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: admin_config; Type: SCHEMA; Schema: -; Owner: neondb_owner
--

CREATE SCHEMA admin_config;


ALTER SCHEMA admin_config OWNER TO neondb_owner;

--
-- Name: brain_overlay; Type: SCHEMA; Schema: -; Owner: neondb_owner
--

CREATE SCHEMA brain_overlay;


ALTER SCHEMA brain_overlay OWNER TO neondb_owner;

--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: neondb_owner
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
                    BEGIN
                        NEW.updated_at = CURRENT_TIMESTAMP;
                        RETURN NEW;
                    END;
                    $$;


ALTER FUNCTION public.update_updated_at_column() OWNER TO neondb_owner;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: application_profiles; Type: TABLE; Schema: admin_config; Owner: neondb_owner
--

CREATE TABLE admin_config.application_profiles (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    bep_weight double precision DEFAULT 40.0 NOT NULL,
    efficiency_weight double precision DEFAULT 30.0 NOT NULL,
    head_margin_weight double precision DEFAULT 15.0 NOT NULL,
    npsh_weight double precision DEFAULT 15.0 NOT NULL,
    bep_optimal_min double precision DEFAULT 0.95 NOT NULL,
    bep_optimal_max double precision DEFAULT 1.05 NOT NULL,
    min_acceptable_efficiency double precision DEFAULT 40.0 NOT NULL,
    excellent_efficiency double precision DEFAULT 85.0 NOT NULL,
    good_efficiency double precision DEFAULT 75.0 NOT NULL,
    fair_efficiency double precision DEFAULT 65.0 NOT NULL,
    optimal_head_margin_max double precision DEFAULT 5.0 NOT NULL,
    acceptable_head_margin_max double precision DEFAULT 10.0 NOT NULL,
    npsh_excellent_margin double precision DEFAULT 3.0 NOT NULL,
    npsh_good_margin double precision DEFAULT 1.5 NOT NULL,
    npsh_minimum_margin double precision DEFAULT 0.5 NOT NULL,
    speed_variation_penalty_factor double precision DEFAULT 15.0 NOT NULL,
    trimming_penalty_factor double precision DEFAULT 10.0 NOT NULL,
    max_acceptable_trim_pct double precision DEFAULT 75.0 NOT NULL,
    top_recommendation_threshold double precision DEFAULT 70.0 NOT NULL,
    acceptable_option_threshold double precision DEFAULT 50.0 NOT NULL,
    near_miss_count integer DEFAULT 5 NOT NULL,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_by character varying(100),
    CONSTRAINT weights_total_100 CHECK ((abs(((((bep_weight + efficiency_weight) + head_margin_weight) + npsh_weight) - (100.0)::double precision)) < (0.01)::double precision))
);


ALTER TABLE admin_config.application_profiles OWNER TO neondb_owner;

--
-- Name: application_profiles_id_seq; Type: SEQUENCE; Schema: admin_config; Owner: neondb_owner
--

CREATE SEQUENCE admin_config.application_profiles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE admin_config.application_profiles_id_seq OWNER TO neondb_owner;

--
-- Name: application_profiles_id_seq; Type: SEQUENCE OWNED BY; Schema: admin_config; Owner: neondb_owner
--

ALTER SEQUENCE admin_config.application_profiles_id_seq OWNED BY admin_config.application_profiles.id;


--
-- Name: configuration_audits; Type: TABLE; Schema: admin_config; Owner: neondb_owner
--

CREATE TABLE admin_config.configuration_audits (
    id integer NOT NULL,
    profile_id integer,
    changed_by character varying(100) NOT NULL,
    change_type character varying(50) NOT NULL,
    field_name character varying(100),
    old_value character varying(200),
    new_value character varying(200),
    reason text,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE admin_config.configuration_audits OWNER TO neondb_owner;

--
-- Name: configuration_audits_id_seq; Type: SEQUENCE; Schema: admin_config; Owner: neondb_owner
--

CREATE SEQUENCE admin_config.configuration_audits_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE admin_config.configuration_audits_id_seq OWNER TO neondb_owner;

--
-- Name: configuration_audits_id_seq; Type: SEQUENCE OWNED BY; Schema: admin_config; Owner: neondb_owner
--

ALTER SEQUENCE admin_config.configuration_audits_id_seq OWNED BY admin_config.configuration_audits.id;


--
-- Name: engineering_constants; Type: TABLE; Schema: admin_config; Owner: neondb_owner
--

CREATE TABLE admin_config.engineering_constants (
    id integer NOT NULL,
    category character varying(50) NOT NULL,
    name character varying(100) NOT NULL,
    value character varying(200) NOT NULL,
    unit character varying(50),
    description text,
    formula text,
    is_locked boolean DEFAULT true NOT NULL
);


ALTER TABLE admin_config.engineering_constants OWNER TO neondb_owner;

--
-- Name: engineering_constants_id_seq; Type: SEQUENCE; Schema: admin_config; Owner: neondb_owner
--

CREATE SEQUENCE admin_config.engineering_constants_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE admin_config.engineering_constants_id_seq OWNER TO neondb_owner;

--
-- Name: engineering_constants_id_seq; Type: SEQUENCE OWNED BY; Schema: admin_config; Owner: neondb_owner
--

ALTER SEQUENCE admin_config.engineering_constants_id_seq OWNED BY admin_config.engineering_constants.id;


--
-- Name: data_corrections; Type: TABLE; Schema: brain_overlay; Owner: neondb_owner
--

CREATE TABLE brain_overlay.data_corrections (
    id integer NOT NULL,
    pump_code character varying(100) NOT NULL,
    pump_id integer,
    correction_type character varying(50) NOT NULL,
    field_path character varying(200) NOT NULL,
    table_name character varying(100),
    record_id integer,
    original_value text,
    corrected_value text NOT NULL,
    value_type character varying(20) DEFAULT 'numeric'::character varying,
    justification text NOT NULL,
    source character varying(100) NOT NULL,
    confidence_score numeric(3,2) DEFAULT 1.0,
    impact_assessment text,
    proposed_by character varying(100) NOT NULL,
    approved_by character varying(100),
    status character varying(20) DEFAULT 'pending'::character varying,
    effective_date timestamp without time zone,
    expiry_date timestamp without time zone,
    test_results jsonb,
    related_issue_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    activated_at timestamp without time zone,
    deactivated_at timestamp without time zone
);


ALTER TABLE brain_overlay.data_corrections OWNER TO neondb_owner;

--
-- Name: active_corrections; Type: VIEW; Schema: brain_overlay; Owner: neondb_owner
--

CREATE VIEW brain_overlay.active_corrections AS
 SELECT pump_code,
    correction_type,
    field_path,
    corrected_value,
    justification,
    confidence_score,
    activated_at
   FROM brain_overlay.data_corrections
  WHERE (((status)::text = 'active'::text) AND ((effective_date IS NULL) OR (effective_date <= CURRENT_TIMESTAMP)) AND ((expiry_date IS NULL) OR (expiry_date > CURRENT_TIMESTAMP)));


ALTER VIEW brain_overlay.active_corrections OWNER TO neondb_owner;

--
-- Name: brain_configurations; Type: TABLE; Schema: brain_overlay; Owner: neondb_owner
--

CREATE TABLE brain_overlay.brain_configurations (
    id integer NOT NULL,
    profile_name character varying(100) NOT NULL,
    display_name character varying(200),
    description text,
    category character varying(50) DEFAULT 'general'::character varying,
    scoring_config jsonb NOT NULL,
    logic_flags jsonb,
    correction_rules jsonb,
    validation_rules jsonb,
    use_case_description text,
    is_active boolean DEFAULT false,
    is_default boolean DEFAULT false,
    is_production boolean DEFAULT false,
    requires_approval boolean DEFAULT true,
    created_by character varying(100) NOT NULL,
    approved_by character varying(100),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    approved_at timestamp without time zone,
    last_used_at timestamp without time zone
);


ALTER TABLE brain_overlay.brain_configurations OWNER TO neondb_owner;

--
-- Name: brain_configurations_id_seq; Type: SEQUENCE; Schema: brain_overlay; Owner: neondb_owner
--

CREATE SEQUENCE brain_overlay.brain_configurations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE brain_overlay.brain_configurations_id_seq OWNER TO neondb_owner;

--
-- Name: brain_configurations_id_seq; Type: SEQUENCE OWNED BY; Schema: brain_overlay; Owner: neondb_owner
--

ALTER SEQUENCE brain_overlay.brain_configurations_id_seq OWNED BY brain_overlay.brain_configurations.id;


--
-- Name: configuration_history; Type: TABLE; Schema: brain_overlay; Owner: neondb_owner
--

CREATE TABLE brain_overlay.configuration_history (
    id integer NOT NULL,
    configuration_id integer,
    change_type character varying(50),
    field_changed character varying(100),
    old_value jsonb,
    new_value jsonb,
    reason text,
    changed_by character varying(100),
    changed_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE brain_overlay.configuration_history OWNER TO neondb_owner;

--
-- Name: configuration_history_id_seq; Type: SEQUENCE; Schema: brain_overlay; Owner: neondb_owner
--

CREATE SEQUENCE brain_overlay.configuration_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE brain_overlay.configuration_history_id_seq OWNER TO neondb_owner;

--
-- Name: configuration_history_id_seq; Type: SEQUENCE OWNED BY; Schema: brain_overlay; Owner: neondb_owner
--

ALTER SEQUENCE brain_overlay.configuration_history_id_seq OWNED BY brain_overlay.configuration_history.id;


--
-- Name: data_corrections_id_seq; Type: SEQUENCE; Schema: brain_overlay; Owner: neondb_owner
--

CREATE SEQUENCE brain_overlay.data_corrections_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE brain_overlay.data_corrections_id_seq OWNER TO neondb_owner;

--
-- Name: data_corrections_id_seq; Type: SEQUENCE OWNED BY; Schema: brain_overlay; Owner: neondb_owner
--

ALTER SEQUENCE brain_overlay.data_corrections_id_seq OWNED BY brain_overlay.data_corrections.id;


--
-- Name: data_quality_issues; Type: TABLE; Schema: brain_overlay; Owner: neondb_owner
--

CREATE TABLE brain_overlay.data_quality_issues (
    id integer NOT NULL,
    pump_code character varying(100) NOT NULL,
    pump_id integer,
    issue_type character varying(50) NOT NULL,
    field_name character varying(100),
    expected_value numeric(12,4),
    actual_value numeric(12,4),
    severity character varying(20) DEFAULT 'minor'::character varying NOT NULL,
    description text,
    source_reference text,
    detected_by character varying(100),
    detected_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    reviewed_by character varying(100),
    reviewed_at timestamp without time zone,
    status character varying(20) DEFAULT 'open'::character varying,
    resolution_notes text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE brain_overlay.data_quality_issues OWNER TO neondb_owner;

--
-- Name: data_quality_issues_id_seq; Type: SEQUENCE; Schema: brain_overlay; Owner: neondb_owner
--

CREATE SEQUENCE brain_overlay.data_quality_issues_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE brain_overlay.data_quality_issues_id_seq OWNER TO neondb_owner;

--
-- Name: data_quality_issues_id_seq; Type: SEQUENCE OWNED BY; Schema: brain_overlay; Owner: neondb_owner
--

ALTER SEQUENCE brain_overlay.data_quality_issues_id_seq OWNED BY brain_overlay.data_quality_issues.id;


--
-- Name: data_quality_summary; Type: VIEW; Schema: brain_overlay; Owner: neondb_owner
--

CREATE VIEW brain_overlay.data_quality_summary AS
 SELECT pump_code,
    count(*) AS total_issues,
    count(*) FILTER (WHERE ((severity)::text = 'critical'::text)) AS critical_issues,
    count(*) FILTER (WHERE ((severity)::text = 'major'::text)) AS major_issues,
    count(*) FILTER (WHERE ((severity)::text = 'minor'::text)) AS minor_issues,
    count(*) FILTER (WHERE ((status)::text = 'open'::text)) AS open_issues,
    max(detected_at) AS last_issue_detected
   FROM brain_overlay.data_quality_issues
  GROUP BY pump_code;


ALTER VIEW brain_overlay.data_quality_summary OWNER TO neondb_owner;

--
-- Name: decision_traces; Type: TABLE; Schema: brain_overlay; Owner: neondb_owner
--

CREATE TABLE brain_overlay.decision_traces (
    id integer NOT NULL,
    session_id character varying(100) NOT NULL,
    trace_type character varying(50) DEFAULT 'selection'::character varying,
    duty_flow_m3hr numeric(10,3) NOT NULL,
    duty_head_m numeric(10,3) NOT NULL,
    additional_parameters jsonb,
    brain_config_id integer,
    config_snapshot jsonb,
    corrections_applied jsonb,
    data_quality_flags jsonb,
    pump_rankings jsonb NOT NULL,
    selected_pump_code character varying(100),
    selection_reason text,
    decision_factors jsonb,
    processing_time_ms integer,
    warnings jsonb,
    user_context jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE brain_overlay.decision_traces OWNER TO neondb_owner;

--
-- Name: decision_traces_id_seq; Type: SEQUENCE; Schema: brain_overlay; Owner: neondb_owner
--

CREATE SEQUENCE brain_overlay.decision_traces_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE brain_overlay.decision_traces_id_seq OWNER TO neondb_owner;

--
-- Name: decision_traces_id_seq; Type: SEQUENCE OWNED BY; Schema: brain_overlay; Owner: neondb_owner
--

ALTER SEQUENCE brain_overlay.decision_traces_id_seq OWNED BY brain_overlay.decision_traces.id;


--
-- Name: manufacturer_selections; Type: TABLE; Schema: brain_overlay; Owner: neondb_owner
--

CREATE TABLE brain_overlay.manufacturer_selections (
    id integer NOT NULL,
    source_type character varying(20) NOT NULL,
    manufacturer_name character varying(100),
    document_reference character varying(255),
    duty_flow_m3hr numeric(10,3) NOT NULL,
    duty_head_m numeric(10,3) NOT NULL,
    fluid_properties jsonb,
    application_context text,
    selected_pump_model character varying(100) NOT NULL,
    claimed_efficiency numeric(5,2),
    claimed_power_kw numeric(10,3),
    claimed_npsh_m numeric(8,2),
    claimed_impeller_diameter_mm numeric(8,2),
    operating_speed_rpm integer,
    additional_specs jsonb,
    selection_rationale text,
    document_path character varying(500),
    extraction_confidence numeric(3,2),
    verification_status character varying(20) DEFAULT 'unverified'::character varying,
    verified_by character varying(100),
    verified_at timestamp without time zone,
    notes text,
    entered_by character varying(100) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE brain_overlay.manufacturer_selections OWNER TO neondb_owner;

--
-- Name: manufacturer_selections_id_seq; Type: SEQUENCE; Schema: brain_overlay; Owner: neondb_owner
--

CREATE SEQUENCE brain_overlay.manufacturer_selections_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE brain_overlay.manufacturer_selections_id_seq OWNER TO neondb_owner;

--
-- Name: manufacturer_selections_id_seq; Type: SEQUENCE OWNED BY; Schema: brain_overlay; Owner: neondb_owner
--

ALTER SEQUENCE brain_overlay.manufacturer_selections_id_seq OWNED BY brain_overlay.manufacturer_selections.id;


--
-- Name: performance_analyses; Type: TABLE; Schema: brain_overlay; Owner: neondb_owner
--

CREATE TABLE brain_overlay.performance_analyses (
    id integer NOT NULL,
    decision_trace_id integer,
    pump_code character varying(100) NOT NULL,
    analysis_type character varying(50),
    calculated_values jsonb,
    manufacturer_values jsonb,
    variance_analysis jsonb,
    confidence_metrics jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE brain_overlay.performance_analyses OWNER TO neondb_owner;

--
-- Name: performance_analyses_id_seq; Type: SEQUENCE; Schema: brain_overlay; Owner: neondb_owner
--

CREATE SEQUENCE brain_overlay.performance_analyses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE brain_overlay.performance_analyses_id_seq OWNER TO neondb_owner;

--
-- Name: performance_analyses_id_seq; Type: SEQUENCE OWNED BY; Schema: brain_overlay; Owner: neondb_owner
--

ALTER SEQUENCE brain_overlay.performance_analyses_id_seq OWNED BY brain_overlay.performance_analyses.id;


--
-- Name: production_config; Type: VIEW; Schema: brain_overlay; Owner: neondb_owner
--

CREATE VIEW brain_overlay.production_config AS
 SELECT id,
    profile_name,
    display_name,
    description,
    category,
    scoring_config,
    logic_flags,
    correction_rules,
    validation_rules,
    use_case_description,
    is_active,
    is_default,
    is_production,
    requires_approval,
    created_by,
    approved_by,
    created_at,
    approved_at,
    last_used_at
   FROM brain_overlay.brain_configurations
  WHERE ((is_production = true) AND (is_active = true))
 LIMIT 1;


ALTER VIEW brain_overlay.production_config OWNER TO neondb_owner;

--
-- Name: selection_comparisons; Type: TABLE; Schema: brain_overlay; Owner: neondb_owner
--

CREATE TABLE brain_overlay.selection_comparisons (
    id integer NOT NULL,
    manufacturer_selection_id integer,
    brain_decision_trace_id integer,
    comparison_type character varying(50) DEFAULT 'standard'::character varying,
    brain_selection jsonb NOT NULL,
    manufacturer_selection jsonb NOT NULL,
    delta_analysis jsonb NOT NULL,
    agreement_score numeric(5,2),
    key_differences jsonb,
    explanation text,
    learning_insights jsonb,
    follow_up_actions jsonb,
    analyst_notes text,
    analyzed_by character varying(100),
    analyzed_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE brain_overlay.selection_comparisons OWNER TO neondb_owner;

--
-- Name: selection_comparisons_id_seq; Type: SEQUENCE; Schema: brain_overlay; Owner: neondb_owner
--

CREATE SEQUENCE brain_overlay.selection_comparisons_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE brain_overlay.selection_comparisons_id_seq OWNER TO neondb_owner;

--
-- Name: selection_comparisons_id_seq; Type: SEQUENCE OWNED BY; Schema: brain_overlay; Owner: neondb_owner
--

ALTER SEQUENCE brain_overlay.selection_comparisons_id_seq OWNED BY brain_overlay.selection_comparisons.id;


--
-- Name: ai_prompts; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.ai_prompts (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    prompt_text text NOT NULL,
    last_updated timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    label character varying(255)
);


ALTER TABLE public.ai_prompts OWNER TO neondb_owner;

--
-- Name: ai_prompts_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.ai_prompts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ai_prompts_id_seq OWNER TO neondb_owner;

--
-- Name: ai_prompts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.ai_prompts_id_seq OWNED BY public.ai_prompts.id;


--
-- Name: engineering_constants; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.engineering_constants (
    id integer NOT NULL,
    category character varying(100) NOT NULL,
    name character varying(100) NOT NULL,
    value character varying(50) NOT NULL,
    unit character varying(50),
    description text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.engineering_constants OWNER TO neondb_owner;

--
-- Name: engineering_constants_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.engineering_constants_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.engineering_constants_id_seq OWNER TO neondb_owner;

--
-- Name: engineering_constants_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.engineering_constants_id_seq OWNED BY public.engineering_constants.id;


--
-- Name: extras; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.extras (
    id integer NOT NULL,
    pump_id integer NOT NULL,
    eff_curves_no integer,
    npshr_curves_no integer,
    imp_imperial boolean,
    motor_imperial boolean,
    unit_flow character varying(50),
    unit_head character varying(50),
    pump_imp_diam numeric,
    poly_order integer,
    tasgrx_flow_0 numeric,
    tasgrx_flow_1 numeric,
    tasgrx_flow_2 numeric,
    tasgrx_flow_3 numeric,
    tasgrx_head_0 numeric,
    tasgrx_head_1 numeric,
    tasgrx_head_2 numeric,
    tasgrx_head_3 numeric,
    tasgrx_eff_0 numeric,
    tasgrx_eff_1 numeric,
    tasgrx_eff_2 numeric,
    tasgrx_eff_3 numeric,
    tasgrx_power_0 numeric,
    tasgrx_power_1 numeric,
    tasgrx_power_2 numeric,
    tasgrx_power_3 numeric,
    tasgrx_npsh_0 numeric,
    tasgrx_npsh_1 numeric,
    tasgrx_npsh_2 numeric,
    tasgrx_npsh_3 numeric
);


ALTER TABLE public.extras OWNER TO neondb_owner;

--
-- Name: extras_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.extras_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.extras_id_seq OWNER TO neondb_owner;

--
-- Name: extras_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.extras_id_seq OWNED BY public.extras.id;


--
-- Name: processed_files; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.processed_files (
    id integer NOT NULL,
    filename character varying(255) NOT NULL,
    processed_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.processed_files OWNER TO neondb_owner;

--
-- Name: processed_files_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.processed_files_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.processed_files_id_seq OWNER TO neondb_owner;

--
-- Name: processed_files_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.processed_files_id_seq OWNED BY public.processed_files.id;


--
-- Name: pump_bep_markers; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.pump_bep_markers (
    id integer NOT NULL,
    pump_id integer,
    impeller_diameter numeric(10,2),
    bep_flow numeric(10,2),
    bep_head numeric(10,2),
    bep_efficiency numeric(5,2),
    marker_label character varying(50),
    coordinate_x numeric(10,2),
    coordinate_y numeric(10,2),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.pump_bep_markers OWNER TO neondb_owner;

--
-- Name: pump_bep_markers_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.pump_bep_markers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pump_bep_markers_id_seq OWNER TO neondb_owner;

--
-- Name: pump_bep_markers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.pump_bep_markers_id_seq OWNED BY public.pump_bep_markers.id;


--
-- Name: pump_curves; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.pump_curves (
    id integer NOT NULL,
    pump_id integer NOT NULL,
    impeller_diameter_mm numeric NOT NULL
);


ALTER TABLE public.pump_curves OWNER TO neondb_owner;

--
-- Name: pump_curves_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.pump_curves_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pump_curves_id_seq OWNER TO neondb_owner;

--
-- Name: pump_curves_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.pump_curves_id_seq OWNED BY public.pump_curves.id;


--
-- Name: pump_diameters; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.pump_diameters (
    id integer NOT NULL,
    pump_id integer NOT NULL,
    sequence_order integer NOT NULL,
    diameter_value numeric
);


ALTER TABLE public.pump_diameters OWNER TO neondb_owner;

--
-- Name: pump_diameters_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.pump_diameters_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pump_diameters_id_seq OWNER TO neondb_owner;

--
-- Name: pump_diameters_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.pump_diameters_id_seq OWNED BY public.pump_diameters.id;


--
-- Name: pump_eff_iso; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.pump_eff_iso (
    id integer NOT NULL,
    pump_id integer NOT NULL,
    sequence_order integer NOT NULL,
    eff_iso_value numeric
);


ALTER TABLE public.pump_eff_iso OWNER TO neondb_owner;

--
-- Name: pump_eff_iso_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.pump_eff_iso_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pump_eff_iso_id_seq OWNER TO neondb_owner;

--
-- Name: pump_eff_iso_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.pump_eff_iso_id_seq OWNED BY public.pump_eff_iso.id;


--
-- Name: pump_names; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.pump_names (
    id integer NOT NULL,
    pump_id integer NOT NULL,
    sequence_order integer NOT NULL,
    pump_name character varying(255)
);


ALTER TABLE public.pump_names OWNER TO neondb_owner;

--
-- Name: pump_names_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.pump_names_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pump_names_id_seq OWNER TO neondb_owner;

--
-- Name: pump_names_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.pump_names_id_seq OWNED BY public.pump_names.id;


--
-- Name: pump_performance_points; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.pump_performance_points (
    id integer NOT NULL,
    curve_id integer NOT NULL,
    operating_point integer NOT NULL,
    flow_rate numeric,
    head numeric,
    efficiency numeric,
    npshr numeric
);


ALTER TABLE public.pump_performance_points OWNER TO neondb_owner;

--
-- Name: pump_performance_points_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.pump_performance_points_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pump_performance_points_id_seq OWNER TO neondb_owner;

--
-- Name: pump_performance_points_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.pump_performance_points_id_seq OWNED BY public.pump_performance_points.id;


--
-- Name: pump_specifications; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.pump_specifications (
    id integer NOT NULL,
    pump_id integer NOT NULL,
    test_speed_rpm integer,
    max_flow_m3hr numeric,
    max_head_m numeric,
    max_power_kw numeric,
    bep_flow_m3hr numeric,
    bep_head_m numeric,
    npshr_at_bep numeric,
    min_impeller_diameter_mm numeric,
    max_impeller_diameter_mm numeric,
    min_speed_rpm integer,
    max_speed_rpm integer,
    variable_speed boolean,
    variable_diameter boolean
);


ALTER TABLE public.pump_specifications OWNER TO neondb_owner;

--
-- Name: pump_specifications_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.pump_specifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pump_specifications_id_seq OWNER TO neondb_owner;

--
-- Name: pump_specifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.pump_specifications_id_seq OWNED BY public.pump_specifications.id;


--
-- Name: pump_speeds; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.pump_speeds (
    id integer NOT NULL,
    pump_id integer NOT NULL,
    sequence_order integer NOT NULL,
    speed_value numeric
);


ALTER TABLE public.pump_speeds OWNER TO neondb_owner;

--
-- Name: pump_speeds_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.pump_speeds_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pump_speeds_id_seq OWNER TO neondb_owner;

--
-- Name: pump_speeds_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.pump_speeds_id_seq OWNED BY public.pump_speeds.id;


--
-- Name: pumps; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.pumps (
    id integer NOT NULL,
    pump_code character varying(255) NOT NULL,
    manufacturer character varying(255),
    pump_type character varying(255),
    series character varying(255),
    application_category character varying(255),
    construction_standard character varying(255),
    impeller_type character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.pumps OWNER TO neondb_owner;

--
-- Name: pumps_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.pumps_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pumps_id_seq OWNER TO neondb_owner;

--
-- Name: pumps_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.pumps_id_seq OWNED BY public.pumps.id;


--
-- Name: application_profiles id; Type: DEFAULT; Schema: admin_config; Owner: neondb_owner
--

ALTER TABLE ONLY admin_config.application_profiles ALTER COLUMN id SET DEFAULT nextval('admin_config.application_profiles_id_seq'::regclass);


--
-- Name: configuration_audits id; Type: DEFAULT; Schema: admin_config; Owner: neondb_owner
--

ALTER TABLE ONLY admin_config.configuration_audits ALTER COLUMN id SET DEFAULT nextval('admin_config.configuration_audits_id_seq'::regclass);


--
-- Name: engineering_constants id; Type: DEFAULT; Schema: admin_config; Owner: neondb_owner
--

ALTER TABLE ONLY admin_config.engineering_constants ALTER COLUMN id SET DEFAULT nextval('admin_config.engineering_constants_id_seq'::regclass);


--
-- Name: brain_configurations id; Type: DEFAULT; Schema: brain_overlay; Owner: neondb_owner
--

ALTER TABLE ONLY brain_overlay.brain_configurations ALTER COLUMN id SET DEFAULT nextval('brain_overlay.brain_configurations_id_seq'::regclass);


--
-- Name: configuration_history id; Type: DEFAULT; Schema: brain_overlay; Owner: neondb_owner
--

ALTER TABLE ONLY brain_overlay.configuration_history ALTER COLUMN id SET DEFAULT nextval('brain_overlay.configuration_history_id_seq'::regclass);


--
-- Name: data_corrections id; Type: DEFAULT; Schema: brain_overlay; Owner: neondb_owner
--

ALTER TABLE ONLY brain_overlay.data_corrections ALTER COLUMN id SET DEFAULT nextval('brain_overlay.data_corrections_id_seq'::regclass);


--
-- Name: data_quality_issues id; Type: DEFAULT; Schema: brain_overlay; Owner: neondb_owner
--

ALTER TABLE ONLY brain_overlay.data_quality_issues ALTER COLUMN id SET DEFAULT nextval('brain_overlay.data_quality_issues_id_seq'::regclass);


--
-- Name: decision_traces id; Type: DEFAULT; Schema: brain_overlay; Owner: neondb_owner
--

ALTER TABLE ONLY brain_overlay.decision_traces ALTER COLUMN id SET DEFAULT nextval('brain_overlay.decision_traces_id_seq'::regclass);


--
-- Name: manufacturer_selections id; Type: DEFAULT; Schema: brain_overlay; Owner: neondb_owner
--

ALTER TABLE ONLY brain_overlay.manufacturer_selections ALTER COLUMN id SET DEFAULT nextval('brain_overlay.manufacturer_selections_id_seq'::regclass);


--
-- Name: performance_analyses id; Type: DEFAULT; Schema: brain_overlay; Owner: neondb_owner
--

ALTER TABLE ONLY brain_overlay.performance_analyses ALTER COLUMN id SET DEFAULT nextval('brain_overlay.performance_analyses_id_seq'::regclass);


--
-- Name: selection_comparisons id; Type: DEFAULT; Schema: brain_overlay; Owner: neondb_owner
--

ALTER TABLE ONLY brain_overlay.selection_comparisons ALTER COLUMN id SET DEFAULT nextval('brain_overlay.selection_comparisons_id_seq'::regclass);


--
-- Name: ai_prompts id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.ai_prompts ALTER COLUMN id SET DEFAULT nextval('public.ai_prompts_id_seq'::regclass);


--
-- Name: engineering_constants id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.engineering_constants ALTER COLUMN id SET DEFAULT nextval('public.engineering_constants_id_seq'::regclass);


--
-- Name: extras id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.extras ALTER COLUMN id SET DEFAULT nextval('public.extras_id_seq'::regclass);


--
-- Name: processed_files id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.processed_files ALTER COLUMN id SET DEFAULT nextval('public.processed_files_id_seq'::regclass);


--
-- Name: pump_bep_markers id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pump_bep_markers ALTER COLUMN id SET DEFAULT nextval('public.pump_bep_markers_id_seq'::regclass);


--
-- Name: pump_curves id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pump_curves ALTER COLUMN id SET DEFAULT nextval('public.pump_curves_id_seq'::regclass);


--
-- Name: pump_diameters id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pump_diameters ALTER COLUMN id SET DEFAULT nextval('public.pump_diameters_id_seq'::regclass);


--
-- Name: pump_eff_iso id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pump_eff_iso ALTER COLUMN id SET DEFAULT nextval('public.pump_eff_iso_id_seq'::regclass);


--
-- Name: pump_names id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pump_names ALTER COLUMN id SET DEFAULT nextval('public.pump_names_id_seq'::regclass);


--
-- Name: pump_performance_points id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pump_performance_points ALTER COLUMN id SET DEFAULT nextval('public.pump_performance_points_id_seq'::regclass);


--
-- Name: pump_specifications id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pump_specifications ALTER COLUMN id SET DEFAULT nextval('public.pump_specifications_id_seq'::regclass);


--
-- Name: pump_speeds id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pump_speeds ALTER COLUMN id SET DEFAULT nextval('public.pump_speeds_id_seq'::regclass);


--
-- Name: pumps id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pumps ALTER COLUMN id SET DEFAULT nextval('public.pumps_id_seq'::regclass);


--
-- Data for Name: application_profiles; Type: TABLE DATA; Schema: admin_config; Owner: neondb_owner
--

COPY admin_config.application_profiles (id, name, description, bep_weight, efficiency_weight, head_margin_weight, npsh_weight, bep_optimal_min, bep_optimal_max, min_acceptable_efficiency, excellent_efficiency, good_efficiency, fair_efficiency, optimal_head_margin_max, acceptable_head_margin_max, npsh_excellent_margin, npsh_good_margin, npsh_minimum_margin, speed_variation_penalty_factor, trimming_penalty_factor, max_acceptable_trim_pct, top_recommendation_threshold, acceptable_option_threshold, near_miss_count, is_active, created_at, updated_at, created_by) FROM stdin;
1	General Purpose	Balanced configuration for general pump applications	40	30	15	15	0.95	1.05	40	85	75	65	5	10	3	1.5	0.5	15	10	75	70	50	5	t	2025-08-11 08:06:07.131634	2025-08-11 08:06:07.131634	\N
2	Municipal Water Supply	High reliability and efficiency for municipal water systems	35	35	15	15	0.95	1.05	40	85	75	65	5	10	3.5	2	0.5	15	10	75	70	50	5	t	2025-08-11 08:06:07.131634	2025-08-11 08:06:07.131634	\N
3	Industrial Process	Tight tolerances and high efficiency for industrial processes	30	40	20	10	0.95	1.05	40	85	75	65	3	7	3	1.5	0.5	15	10	75	70	50	5	t	2025-08-11 08:06:07.131634	2025-08-11 08:06:07.131634	\N
4	HVAC Systems	Energy optimization for HVAC and cooling applications	30	45	15	10	0.95	1.05	40	80	70	65	5	10	3	1.5	0.5	15	10	75	70	50	5	t	2025-08-11 08:06:07.131634	2025-08-11 08:06:07.131634	\N
5	Fire Protection	Maximum reliability with regulatory compliance	45	20	20	15	0.95	1.05	40	85	75	65	5	10	4	1.5	0.5	20	10	75	70	50	5	t	2025-08-11 08:06:07.131634	2025-08-11 08:06:07.131634	\N
6	Chemical Processing	High safety margins for chemical applications	35	25	20	20	0.95	1.05	40	85	75	65	5	10	4	2.5	1	15	10	75	70	50	5	t	2025-08-11 08:06:07.131634	2025-08-11 08:06:07.131634	\N
\.


--
-- Data for Name: configuration_audits; Type: TABLE DATA; Schema: admin_config; Owner: neondb_owner
--

COPY admin_config.configuration_audits (id, profile_id, changed_by, change_type, field_name, old_value, new_value, reason, "timestamp") FROM stdin;
\.


--
-- Data for Name: engineering_constants; Type: TABLE DATA; Schema: admin_config; Owner: neondb_owner
--

COPY admin_config.engineering_constants (id, category, name, value, unit, description, formula, is_locked) FROM stdin;
1	Affinity Laws	Flow vs Speed	Q2 = Q1 × (N2/N1)	\N	Flow rate varies directly with speed	Q2 = Q1 × (N2/N1)	t
2	Affinity Laws	Head vs Speed	H2 = H1 × (N2/N1)²	\N	Head varies with the square of speed	H2 = H1 × (N2/N1)²	t
3	Affinity Laws	Power vs Speed	P2 = P1 × (N2/N1)³	\N	Power varies with the cube of speed	P2 = P1 × (N2/N1)³	t
4	Impeller Trimming	Flow vs Diameter	Q2 = Q1 × (D2/D1)	\N	Flow rate varies directly with impeller diameter	Q2 = Q1 × (D2/D1)	t
5	Impeller Trimming	Head vs Diameter	H2 = H1 × (D2/D1)²	\N	Head varies with the square of impeller diameter	H2 = H1 × (D2/D1)²	t
6	Physical Limits	Minimum Trim Percentage	75	%	Minimum allowable impeller trim percentage to maintain hydraulic efficiency	\N	t
7	Physical Limits	Maximum Trim Percentage	100	%	Maximum impeller size (full diameter)	\N	t
8	Physical Limits	Minimum Speed	600	RPM	Minimum pump operating speed	\N	t
9	Physical Limits	Maximum Speed	3600	RPM	Maximum pump operating speed	\N	t
10	NPSH	Minimum Safety Margin	0.5	m	Absolute minimum NPSH margin to prevent cavitation	NPSHa - NPSHr ≥ 0.5m	t
11	Interpolation	Method	Quadratic/Cubic Spline	\N	Mathematical method for curve interpolation	\N	t
12	Interpolation	Maximum Extrapolation	15	%	Maximum allowable extrapolation beyond curve data points	\N	t
18	BEP Migration	bep_shift_flow_exponent	1.2	\N	Flow exponent for BEP migration calculations during impeller trimming	Q_shifted = Q_original × (D_trim/D_full)^exponent	t
19	BEP Migration	bep_shift_head_exponent	2.2	\N	Head exponent for BEP migration calculations during impeller trimming	H_shifted = H_original × (D_trim/D_full)^exponent	t
20	BEP Migration	efficiency_correction_exponent	0.1	\N	Efficiency correction factor for off-BEP operation penalties	η_penalty = (QBP - 110) × correction_exponent	t
21	BEP Migration	trim_dependent_small_exponent	2.9	\N	Enhanced affinity law exponent for small trims (<5%) - research-based	H2 = H1 × (D2/D1)^exponent for trims <5%	t
22	BEP Migration	trim_dependent_large_exponent	2.1	\N	Enhanced affinity law exponent for large trims (5-15%) - research-based	H2 = H1 × (D2/D1)^exponent for trims 5-15%	t
23	BEP Migration	efficiency_penalty_volute	0.20	\N	Efficiency penalty factor for volute pumps (research: 0.15-0.25)	Δη = factor × (1 - D_trim/D_full)	t
24	BEP Migration	efficiency_penalty_diffuser	0.45	\N	Efficiency penalty factor for diffuser pumps (research: 0.4-0.5)	Δη = factor × (1 - D_trim/D_full)	t
25	BEP Migration	npsh_degradation_threshold	10.0	%	Trim percentage above which NPSH degradation occurs (research: >10%)	NPSH penalty applies when trim > threshold	t
26	BEP Migration	npsh_degradation_factor	1.15	\N	NPSH multiplier for heavily trimmed impellers (research-based)	NPSH_required = NPSH_base × factor (for heavy trims)	t
34	Affinity Laws	flow_vs_diameter_exp	1.0	dimensionless	Q2/Q1 = (D2/D1)^n	\N	t
35	Affinity Laws	head_vs_diameter_exp	2.0	dimensionless	H2/H1 = (D2/D1)^n	\N	t
36	Affinity Laws	power_vs_diameter_exp	3.0	dimensionless	P2/P1 = (D2/D1)^n	\N	t
37	BEP Migration	bep_flow_exponent	1.2	dimensionless	Flow BEP migration exponent	\N	t
38	BEP Migration	bep_head_exponent	2.2	dimensionless	Head BEP migration exponent	\N	t
39	BEP Migration	bep_efficiency_exponent	0.1	dimensionless	Efficiency BEP migration exponent	\N	t
40	Trimming Research	small_trim_head_exp	2.8	dimensionless	Head exponent for <5% trim	\N	t
41	Trimming Research	large_trim_head_exp	2.0	dimensionless	Head exponent for >10% trim	\N	t
42	Efficiency Penalties	volute_efficiency_penalty	0.2	dimensionless	Volute pump efficiency penalty factor	\N	t
\.


--
-- Data for Name: brain_configurations; Type: TABLE DATA; Schema: brain_overlay; Owner: neondb_owner
--

COPY brain_overlay.brain_configurations (id, profile_name, display_name, description, category, scoring_config, logic_flags, correction_rules, validation_rules, use_case_description, is_active, is_default, is_production, requires_approval, created_by, approved_by, created_at, approved_at, last_used_at) FROM stdin;
1	production_default	Production Default Configuration	Default production configuration based on current Brain system settings	general	{"npsh_weight": 0, "bep_optimal_range": [0.95, 1.05], "efficiency_weight": 35, "head_margin_weight": 20, "efficiency_brackets": {"fair": 65.0, "good": 75.0, "minimum": 40.0, "excellent": 85.0}, "max_trim_percentage": 15.0, "trim_penalty_factor": 2.0, "bep_proximity_weight": 45}	{"strict_npsh_gates": true, "use_affinity_laws": true, "enforce_qbp_limits": true, "enable_speed_variation": false, "enable_impeller_trimming": true}	{"apply_all_active": true, "require_approval": true, "minimum_confidence": 0.8}	\N	\N	t	t	t	t	system	\N	2025-08-11 08:29:38.914002	\N	\N
\.


--
-- Data for Name: configuration_history; Type: TABLE DATA; Schema: brain_overlay; Owner: neondb_owner
--

COPY brain_overlay.configuration_history (id, configuration_id, change_type, field_changed, old_value, new_value, reason, changed_by, changed_at) FROM stdin;
\.


--
-- Data for Name: data_corrections; Type: TABLE DATA; Schema: brain_overlay; Owner: neondb_owner
--

COPY brain_overlay.data_corrections (id, pump_code, pump_id, correction_type, field_path, table_name, record_id, original_value, corrected_value, value_type, justification, source, confidence_score, impact_assessment, proposed_by, approved_by, status, effective_date, expiry_date, test_results, related_issue_id, created_at, activated_at, deactivated_at) FROM stdin;
\.


--
-- Data for Name: data_quality_issues; Type: TABLE DATA; Schema: brain_overlay; Owner: neondb_owner
--

COPY brain_overlay.data_quality_issues (id, pump_code, pump_id, issue_type, field_name, expected_value, actual_value, severity, description, source_reference, detected_by, detected_at, reviewed_by, reviewed_at, status, resolution_notes, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: decision_traces; Type: TABLE DATA; Schema: brain_overlay; Owner: neondb_owner
--

COPY brain_overlay.decision_traces (id, session_id, trace_type, duty_flow_m3hr, duty_head_m, additional_parameters, brain_config_id, config_snapshot, corrections_applied, data_quality_flags, pump_rankings, selected_pump_code, selection_reason, decision_factors, processing_time_ms, warnings, user_context, created_at) FROM stdin;
\.


--
-- Data for Name: manufacturer_selections; Type: TABLE DATA; Schema: brain_overlay; Owner: neondb_owner
--

COPY brain_overlay.manufacturer_selections (id, source_type, manufacturer_name, document_reference, duty_flow_m3hr, duty_head_m, fluid_properties, application_context, selected_pump_model, claimed_efficiency, claimed_power_kw, claimed_npsh_m, claimed_impeller_diameter_mm, operating_speed_rpm, additional_specs, selection_rationale, document_path, extraction_confidence, verification_status, verified_by, verified_at, notes, entered_by, created_at) FROM stdin;
\.


--
-- Data for Name: performance_analyses; Type: TABLE DATA; Schema: brain_overlay; Owner: neondb_owner
--

COPY brain_overlay.performance_analyses (id, decision_trace_id, pump_code, analysis_type, calculated_values, manufacturer_values, variance_analysis, confidence_metrics, created_at) FROM stdin;
\.


--
-- Data for Name: selection_comparisons; Type: TABLE DATA; Schema: brain_overlay; Owner: neondb_owner
--

COPY brain_overlay.selection_comparisons (id, manufacturer_selection_id, brain_decision_trace_id, comparison_type, brain_selection, manufacturer_selection, delta_analysis, agreement_score, key_differences, explanation, learning_insights, follow_up_actions, analyst_notes, analyzed_by, analyzed_at) FROM stdin;
\.


--
-- Data for Name: ai_prompts; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.ai_prompts (id, name, prompt_text, last_updated, label) FROM stdin;
\.


--
-- Data for Name: engineering_constants; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.engineering_constants (id, category, name, value, unit, description, created_at, updated_at) FROM stdin;
1	Affinity Laws	flow_vs_diameter_exp	1.0	dimensionless	Q2/Q1 = (D2/D1)^n	2025-08-12 13:19:23.631499	2025-08-12 13:19:23.631499
2	Affinity Laws	head_vs_diameter_exp	2.0	dimensionless	H2/H1 = (D2/D1)^n	2025-08-12 13:19:23.631499	2025-08-12 13:19:23.631499
3	Affinity Laws	power_vs_diameter_exp	3.0	dimensionless	P2/P1 = (D2/D1)^n	2025-08-12 13:19:23.631499	2025-08-12 13:19:23.631499
4	BEP Migration	bep_flow_exponent	1.2	dimensionless	Flow BEP migration exponent	2025-08-12 13:19:23.631499	2025-08-12 13:19:23.631499
5	BEP Migration	bep_head_exponent	2.2	dimensionless	Head BEP migration exponent	2025-08-12 13:19:23.631499	2025-08-12 13:19:23.631499
6	BEP Migration	bep_efficiency_exponent	0.1	dimensionless	Efficiency BEP migration exponent	2025-08-12 13:19:23.631499	2025-08-12 13:19:23.631499
7	Trimming Research	small_trim_head_exp	2.8	dimensionless	Head exponent for <5% trim	2025-08-12 13:19:23.631499	2025-08-12 13:19:23.631499
8	Trimming Research	large_trim_head_exp	2.0	dimensionless	Head exponent for >10% trim	2025-08-12 13:19:23.631499	2025-08-12 13:19:23.631499
9	Efficiency Penalties	volute_efficiency_penalty	0.2	dimensionless	Volute pump efficiency penalty factor	2025-08-12 13:19:23.631499	2025-08-12 13:19:23.631499
\.


--
-- Data for Name: extras; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.extras (id, pump_id, eff_curves_no, npshr_curves_no, imp_imperial, motor_imperial, unit_flow, unit_head, pump_imp_diam, poly_order, tasgrx_flow_0, tasgrx_flow_1, tasgrx_flow_2, tasgrx_flow_3, tasgrx_head_0, tasgrx_head_1, tasgrx_head_2, tasgrx_head_3, tasgrx_eff_0, tasgrx_eff_1, tasgrx_eff_2, tasgrx_eff_3, tasgrx_power_0, tasgrx_power_1, tasgrx_power_2, tasgrx_power_3, tasgrx_npsh_0, tasgrx_npsh_1, tasgrx_npsh_2, tasgrx_npsh_3) FROM stdin;
1	1	5	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
2	2	5	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
3	3	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
4	4	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
5	5	5	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
6	6	4	1	f	f	m^3/hr	m	336	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
7	7	4	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
8	8	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
9	9	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
10	10	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
11	11	2	1	f	f	m^3/hr	m	584	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
12	12	3	1	f	f	US gpm	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
13	13	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
14	14	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
15	15	1	1	f	f	US gpm	ft	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
16	16	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
17	17	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
18	18	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
19	19	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
20	20	1	1	f	f	m^3/hr	m	198	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
21	21	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
22	22	3	1	f	f	l/sec	ft	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
23	23	3	1	f	f	US gpm	ft	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
24	24	1	1	f	f	m^3/hr	m	1250	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
25	25	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
26	26	3	1	f	f	l/sec	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
27	27	6	1	f	f	m^3/hr	m	271	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
28	28	4	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
29	29	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
30	30	1	1	f	f	m^3/hr	m	813	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
31	31	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
32	32	1	1	f	f	l/sec	m	382	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
33	33	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
34	34	3	1	f	f	m^3/hr	m	0	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
35	35	3	1	f	f	m^3/hr	m	0	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
36	36	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
37	37	1	1	f	f	m^3/hr	m	229	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
38	38	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
39	39	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
40	40	1	1	f	f	US gpm	ft	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
41	41	1	1	f	f	l/sec	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
42	42	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
43	43	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
44	44	1	1	f	f	US gpm	ft	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
45	45	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
46	46	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
47	47	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
48	48	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
49	49	4	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
50	50	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
51	51	1	1	f	f	US gpm	ft	596.5	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
52	52	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
53	53	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
54	54	2	1	f	f	m^3/hr	m	546	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
55	55	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
56	56	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
57	57	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
58	58	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
59	59	1	1	f	f	m^3/hr	m	262	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
60	60	1	1	f	f	m^3/hr	m	262	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
61	61	1	1	f	f	m^3/hr	m	262	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
62	62	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
63	63	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
64	64	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
65	65	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
66	66	4	1	f	f	m^3/hr	m	239	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
67	67	3	2	f	f	m^3/hr	m	210	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
68	68	5	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
69	69	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
70	70	4	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
71	71	6	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
72	72	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
73	73	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
74	74	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
75	75	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
76	76	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
77	77	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
78	78	3	1	f	f	m^3/hr	m	910	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
79	79	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
80	80	3	1	f	f	m^3/hr	m	0	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
81	81	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
82	82	1	1	f	f	m^3/hr	m	343	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
83	83	1	1	f	f	m^3/hr	m	343	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
84	84	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
85	85	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
86	86	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
87	87	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
88	88	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
89	89	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
90	90	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
91	91	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
92	92	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
93	93	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
94	94	1	1	f	f	m^3/hr	m	308	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
95	95	2	1	f	f	m^3/hr	m	267	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
96	96	1	1	f	f	m^3/hr	m	215	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
97	97	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
98	98	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
99	99	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
100	100	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
101	101	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
102	102	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
103	103	4	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
104	104	4	1	f	f	m^3/hr	m	272	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
105	105	3	1	f	f	m^3/hr	m	245	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
106	106	3	1	f	f	m^3/hr	m	245	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
107	107	4	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
108	108	4	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
109	109	3	1	f	f	m^3/hr	m	275	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
110	110	3	3	f	f	m^3/hr	m	275	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
111	111	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
112	112	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
113	113	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
114	114	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
115	115	2	1	f	f	m^3/hr	m	540	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
116	116	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
117	117	1	1	f	f	m^3/hr	m	608	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
118	118	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
119	119	1	1	f	f	m^3/hr	m	698	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
120	120	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
121	121	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
122	122	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
123	123	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
124	124	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
125	125	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
126	126	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
127	127	3	1	f	f	m^3/hr	m	743	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
128	128	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
129	129	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
130	130	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
131	131	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
132	132	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
133	133	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
134	134	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
135	135	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
136	136	4	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
137	137	5	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
138	138	3	2	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
139	139	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
140	140	4	1	f	f	m^3/hr	m	398	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
141	141	5	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
142	142	3	1	f	f	m^3/hr	m	345	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
143	143	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
144	144	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
145	145	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
146	146	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
147	147	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
148	148	4	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
149	149	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
150	150	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
151	151	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
152	152	2	1	f	f	m^3/hr	ft	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
153	153	2	1	f	f	m^3/hr	ft	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
154	154	2	1	f	f	US gpm	ft	279	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
155	155	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
156	156	1	1	f	f	l/sec	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
157	157	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
158	158	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
159	159	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
160	160	5	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
161	161	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
162	162	2	1	f	f	m^3/hr	m	588	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
163	163	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
164	164	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
165	165	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
166	166	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
167	167	2	1	f	f	m^3/hr	m	660.4	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
168	168	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
169	169	4	1	f	f	US gpm	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
170	170	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
171	171	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
172	172	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
173	173	1	1	f	f	m^3/hr	m	261	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
174	174	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
175	175	1	1	f	f	m^3/hr	m	553	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
176	176	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
177	177	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
178	178	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
179	179	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
180	180	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
181	181	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
182	182	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
183	183	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
184	184	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
185	185	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
186	186	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
187	187	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
188	188	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
189	189	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
190	190	4	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
191	191	2	1	f	f	US gpm	ft	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
192	192	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
193	193	3	1	f	f	US gpm	ft	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
194	194	3	1	f	f	US gpm	ft	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
195	195	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
196	196	3	1	f	f	US gpm	ft	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
197	197	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
198	198	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
199	199	1	1	f	f	m^3/hr	m	337	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
200	200	2	1	f	f	US gpm	ft	336.5	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
201	201	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
202	202	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
203	203	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
204	204	5	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
205	205	4	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
206	206	4	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
207	207	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
208	208	2	1	f	f	m^3/hr	m	328	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
209	209	2	1	f	f	US gpm	ft	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
210	210	3	1	f	f	US gpm	ft	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
211	211	3	1	f	f	m^3/hr	m	0	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
212	212	3	1	f	f	US gpm	ft	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
213	213	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
214	214	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
215	215	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
216	216	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
217	217	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
218	218	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
219	219	2	1	f	f	m^3/hr	m	0	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
220	220	1	1	f	f	m^3/hr	m	381	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
221	221	4	1	f	f	m^3/hr	m	143	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
222	222	5	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
223	223	5	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
224	224	1	1	f	f	m^3/hr	m	218	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
225	225	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
226	226	5	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
227	227	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
228	228	5	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
229	229	4	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
230	230	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
231	231	2	1	f	f	m^3/hr	ft	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
232	232	2	1	f	f	m^3/hr	ft	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
233	233	4	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
234	234	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
235	235	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
236	236	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
237	237	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
238	238	2	1	f	f	m^3/hr	ft	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
239	239	2	1	f	f	US gpm	ft	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
240	240	1	1	f	f	m^3/hr	m	142	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
241	241	1	1	f	f	m^3/hr	m	119.9	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
242	242	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
243	243	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
244	244	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
245	245	1	1	f	f	m^3/hr	m	108.5	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
246	246	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
247	247	2	1	f	f	m^3/hr	m	342	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
248	248	3	1	f	f	l/sec	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
249	249	3	1	f	f	l/sec	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
250	250	2	1	f	f	US gpm	ft	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
251	251	1	1	f	f	m^3/hr	m	140.5	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
252	252	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
253	253	4	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
254	254	5	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
255	255	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
256	256	6	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
257	257	4	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
258	258	4	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
259	259	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
260	260	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
261	261	1	1	t	t	m^3/hr	m	0	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
262	262	1	1	f	f	m^3/hr	m	635	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
263	263	1	1	f	f	m^3/hr	m	350	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
264	264	1	1	f	f	m^3/hr	m	350	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
265	265	1	1	f	f	m^3/hr	m	350	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
266	266	1	1	f	f	m^3/hr	m	350	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
267	267	1	1	f	f	m^3/hr	m	350	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
268	268	1	1	f	f	m^3/hr	m	350	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
269	269	1	1	f	f	m^3/hr	m	350	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
270	270	1	1	f	f	m^3/hr	m	406	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
271	271	1	1	f	f	m^3/hr	m	400	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
272	272	1	1	f	f	m^3/hr	m	400	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
273	273	1	1	f	f	m^3/hr	m	400	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
274	274	1	1	f	f	m^3/hr	m	400	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
275	275	1	1	f	f	m^3/hr	m	500	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
276	276	1	1	f	f	m^3/hr	m	500	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
277	277	1	1	f	f	m^3/hr	m	508	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
278	278	1	1	f	f	m^3/hr	m	500	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
279	279	1	1	f	f	m^3/hr	m	600	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
280	280	1	1	f	f	m^3/hr	m	600	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
281	281	1	1	t	f	m^3/hr	m	600	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
282	282	1	1	t	f	m^3/hr	m	600	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
283	283	1	1	f	f	m^3/hr	m	750	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
284	284	1	1	f	f	m^3/hr	m	750	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
285	285	1	1	f	f	m^3/hr	m	750	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
286	286	1	1	f	f	m^3/hr	m	750	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
287	287	1	1	f	f	US gpm	ft	217	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
288	288	1	1	t	t	m^3/hr	m	217	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
289	289	1	1	f	f	m^3/hr	m	400	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
290	290	5	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
291	291	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
292	292	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
293	293	2	1	f	f	l/sec	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
294	294	2	1	f	f	m^3/hr	m	566	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
295	295	4	1	f	f	m^3/hr	ft	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
296	296	1	1	f	f	m^3/hr	m	444	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
297	297	1	1	f	f	m^3/hr	m	444	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
298	298	4	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
299	299	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
300	300	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
301	301	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
302	302	1	1	f	f	m^3/hr	m	192	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
303	303	2	1	f	f	US gpm	ft	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
304	304	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
305	305	1	1	f	f	m^3/hr	m	192	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
306	306	1	1	f	f	m^3/hr	m	192	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
307	307	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
308	308	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
309	309	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
310	310	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
311	311	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
312	312	1	1	f	f	US gpm	ft	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
313	313	1	1	f	f	US gpm	ft	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
314	314	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
315	315	1	1	f	f	US gpm	ft	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
316	316	1	1	f	f	US gpm	ft	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
317	317	1	1	f	f	US gpm	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
318	318	1	1	f	f	US gpm	ft	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
319	319	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
320	320	4	1	f	f	l/sec	m	440	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
321	321	4	1	f	f	m^3/hr	m	440	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
322	322	2	1	f	f	m^3/hr	m	419	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
323	323	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
324	324	1	1	f	f	m^3/hr	m	409	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
325	325	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
326	326	1	1	f	f	l/sec	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
327	327	1	1	f	f	m^3/hr	m	201	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
328	328	1	1	f	f	m^3/hr	m	304	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
329	329	1	1	f	f	l/sec	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
330	330	1	1	f	f	m^3/hr	m	331	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
331	331	1	1	f	f	m^3/hr	m	331	4	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
332	332	1	1	f	f	l/sec	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
333	333	2	1	f	f	m^3/hr	m	292	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
334	334	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
335	335	3	1	f	f	l/sec	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
336	336	1	1	f	f	lmp gpm	ft	435	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
337	337	1	1	f	f	lmp gpm	ft	435	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
338	338	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
339	339	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
340	340	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
341	341	3	1	f	f	l/sec	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
342	342	3	1	f	f	l/sec	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
343	343	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
344	344	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
345	345	1	1	f	f	l/sec	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
346	346	3	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
347	347	3	1	f	f	l/sec	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
348	348	3	1	f	f	l/sec	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
349	349	3	1	f	f	l/sec	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
350	350	4	1	f	f	m^3/hr	m	337	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
351	351	2	1	f	f	l/sec	m	360	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
352	352	3	1	f	f	l/sec	m	360	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
353	353	2	1	f	f	l/sec	m	240	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
354	354	3	1	f	f	l/sec	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
355	355	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
356	356	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
357	357	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
358	358	1	1	f	f	l/sec	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
359	359	1	1	f	f	l/sec	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
360	360	1	1	f	f	l/sec	m	369	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
361	361	1	1	f	f	l/sec	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
362	362	1	1	f	f	l/sec	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
363	363	1	1	f	f	l/sec	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
364	364	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
365	365	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
366	366	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
367	367	1	1	f	f	m^3/hr	m	300	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
368	368	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
369	369	2	1	f	f	m^3/hr	m	135	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
370	370	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
371	371	2	1	f	f	m^3/hr	m	135	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
372	372	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
373	373	2	1	f	f	m^3/hr	m	160	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
374	374	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
375	375	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
376	376	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
377	377	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
378	378	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
379	379	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
380	380	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
381	381	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
382	382	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
383	383	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
384	384	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
385	385	2	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
386	386	1	1	f	f	m^3/hr	m	0	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0
\.


--
-- Data for Name: processed_files; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.processed_files (id, filename, processed_at) FROM stdin;
1	100-200_2f.txt	2025-07-30 14:05:53.377836+00
2	100-200_2f_2p.txt	2025-07-30 14:05:53.825573+00
3	100-200_caision.txt	2025-07-30 14:05:54.121752+00
4	100-250_2f.txt	2025-07-30 14:05:54.296998+00
5	100-250_2f_2p.txt	2025-07-30 14:05:54.693601+00
6	100-315_2f.txt	2025-07-30 14:05:55.094733+00
7	100-400_2f.txt	2025-07-30 14:05:55.362698+00
8	100-50_multistage.txt	2025-07-30 14:05:55.72791+00
9	100-80-250_4p.txt	2025-07-30 14:05:55.845718+00
10	10_12_ble.txt	2025-07-30 14:05:56.006926+00
11	10_12_desc.txt	2025-07-30 14:05:56.130256+00
12	10_12_dme.txt	2025-07-30 14:05:56.31731+00
13	10_12_gme.txt	2025-07-30 14:05:56.459037+00
14	10_adm.txt	2025-07-30 14:05:56.698771+00
15	10_nhtb.txt	2025-07-30 14:05:56.834369+00
16	10_wln_18a.txt	2025-07-30 14:05:56.961828+00
17	10_wln_22a.txt	2025-07-30 14:05:57.188832+00
18	10_wln_26a.txt	2025-07-30 14:05:57.504698+00
19	10_wln_32a.txt	2025-07-30 14:05:58.113601+00
20	10_wo_2p.txt	2025-07-30 14:05:58.471836+00
21	10_wo_4p.txt	2025-07-30 14:05:58.808714+00
22	11_mq_h_1100vlt.txt	2025-07-30 14:05:59.142809+00
23	11_mq_h_1100vlt_2p.txt	2025-07-30 14:05:59.511236+00
24	1200mf.txt	2025-07-30 14:05:59.983102+00
25	125-100-250.txt	2025-07-30 14:06:00.084817+00
26	125-100-315_4p.txt	2025-07-30 14:06:00.225154+00
27	125-250_2f.txt	2025-07-30 14:06:00.640831+00
28	125-315_2f.txt	2025-07-30 14:06:01.144855+00
29	125-400_2f.txt	2025-07-30 14:06:01.598462+00
30	12_10_ah_warman_slurry.txt	2025-07-30 14:06:02.01732+00
31	12_14_bdy.txt	2025-07-30 14:06:02.114654+00
32	12_14_ble.txt	2025-07-30 14:06:02.248702+00
33	12_14_desc.txt	2025-07-30 14:06:02.373826+00
34	12_14_dm.txt	2025-07-30 14:06:02.573563+00
35	12_14_dme.txt	2025-07-30 14:06:02.762593+00
36	12_15_v_s_m_f_v.txt	2025-07-30 14:06:02.892916+00
37	12_hc_1133_4p.txt	2025-07-30 14:06:03.098202+00
38	12_hc_1134_4p.txt	2025-07-30 14:06:03.319414+00
39	12_hc_4p.txt	2025-07-30 14:06:03.533298+00
40	12_lc_4p.txt	2025-07-30 14:06:04.036071+00
41	12_lc_9stg__test_results.txt	2025-07-30 14:06:04.174+00
42	12_lnh_21a.txt	2025-07-30 14:06:04.28707+00
43	12_lnh_21b.txt	2025-07-30 14:06:04.584367+00
44	12_mc_4p.txt	2025-07-30 14:06:04.772554+00
45	12_wln_14a.txt	2025-07-30 14:06:04.871696+00
46	12_wln_14b.txt	2025-07-30 14:06:05.052331+00
47	12_wln_17a.txt	2025-07-30 14:06:05.249239+00
48	12_wln_17b.txt	2025-07-30 14:06:05.539701+00
49	12_wln_21a.txt	2025-07-30 14:06:05.750998+00
50	12_wln_21b.txt	2025-07-30 14:06:05.959993+00
51	12x16x23h_dsjh.txt	2025-07-30 14:06:06.182423+00
52	14_12bdy.txt	2025-07-30 14:06:06.287711+00
53	14_16_adm.txt	2025-07-30 14:06:06.495769+00
54	14_16_ble.txt	2025-07-30 14:06:06.754929+00
55	14_18_eme.txt	2025-07-30 14:06:06.9038+00
56	14_hc_1203_4p.txt	2025-07-30 14:06:07.011196+00
57	14_hc_1204_4p.txt	2025-07-30 14:06:07.244753+00
58	14_mc_6970_4p.txt	2025-07-30 14:06:07.483209+00
59	14_mc_755_4p.txt	2025-07-30 14:06:07.586961+00
60	14_mc_756_4p.txt	2025-07-30 14:06:07.726778+00
61	14_mc_757_4p.txt	2025-07-30 14:06:07.871167+00
62	14_wln_19a.txt	2025-07-30 14:06:08.208491+00
63	150-125-250_4p.txt	2025-07-30 14:06:08.63232+00
64	150-125-315.txt	2025-07-30 14:06:10.313029+00
65	150-125-400_4p.txt	2025-07-30 14:06:10.744992+00
66	150-150-200_4p.txt	2025-07-30 14:06:11.225776+00
67	150-150-200a_4p.txt	2025-07-30 14:06:11.591521+00
68	150-200_2f.txt	2025-07-30 14:06:12.791803+00
69	150-250_2f.txt	2025-07-30 14:06:14.65335+00
70	150-315_2f.txt	2025-07-30 14:06:15.252385+00
71	150-400_2f.txt	2025-07-30 14:06:15.700651+00
72	16_hc_1262_4p.txt	2025-07-30 14:06:16.299508+00
73	16_hc_1262_6p.txt	2025-07-30 14:06:16.393758+00
74	16_hc_1264_4p.txt	2025-07-30 14:06:16.495226+00
75	16_hc_1264_6p.txt	2025-07-30 14:06:16.901606+00
76	16_wln_23c.txt	2025-07-30 14:06:17.126488+00
77	16_wln_28c.txt	2025-07-30 14:06:17.44745+00
78	16_wln_35_c.txt	2025-07-30 14:06:17.770053+00
79	18_16_bdm.txt	2025-07-30 14:06:18.508026+00
80	18_20_dme.txt	2025-07-30 14:06:19.670838+00
81	18_22_medivane.txt	2025-07-30 14:06:19.985727+00
82	18_hc_1213_4p.txt	2025-07-30 14:06:20.271341+00
83	18_hc_1213_4p_sabs.txt	2025-07-30 14:06:20.535459+00
84	18_hc_1213_6p.txt	2025-07-30 14:06:20.710445+00
85	18_hc_1214_4p.txt	2025-07-30 14:06:20.843568+00
86	18_hc_1214_4p_6st_sabs.txt	2025-07-30 14:06:21.005338+00
87	18_hc_1214_4p_sabs.txt	2025-07-30 14:06:21.21524+00
88	18_hc_1214_6p.txt	2025-07-30 14:06:21.356562+00
89	18_hc___18_xhc_special.txt	2025-07-30 14:06:21.461771+00
90	18_xhc_2185_4p.txt	2025-07-30 14:06:21.566416+00
91	18_xhc_2185_6p.txt	2025-07-30 14:06:21.770198+00
92	18_xhc_2186_4p.txt	2025-07-30 14:06:21.929426+00
93	18_xhc_2186_6p.txt	2025-07-30 14:06:22.306023+00
94	18xhc_-_3_stage.txt	2025-07-30 14:06:22.761407+00
95	1_5x2x10_5_h.txt	2025-07-30 14:06:23.113681+00
96	1_5x2x8_5_h.txt	2025-07-30 14:06:23.248143+00
97	200-150-315_4p.txt	2025-07-30 14:06:23.379163+00
98	200-150-315_6p.txt	2025-07-30 14:06:23.677594+00
99	200-150-400_4p.txt	2025-07-30 14:06:23.93066+00
100	200-150-400_6p.txt	2025-07-30 14:06:24.123153+00
101	200-150-456_6p.txt	2025-07-30 14:06:24.340732+00
102	200-150-460_4p.txt	2025-07-30 14:06:24.456366+00
103	200-200-250_4p.txt	2025-07-30 14:06:24.660689+00
104	200-200-250_6p.txt	2025-07-30 14:06:25.140955+00
105	200-200-250a_4p.txt	2025-07-30 14:06:25.387182+00
106	200-200-250a_6p.txt	2025-07-30 14:06:25.70071+00
107	200-200-310_4p.txt	2025-07-30 14:06:25.949816+00
108	200-200-310_6p.txt	2025-07-30 14:06:26.217483+00
109	200-200-310a_4p.txt	2025-07-30 14:06:26.598201+00
110	200-200-310a_6p.txt	2025-07-30 14:06:26.756036+00
111	200-200-350_4p.txt	2025-07-30 14:06:27.228213+00
112	200-200-430_4p.txt	2025-07-30 14:06:27.391908+00
113	200-200-430_6p.txt	2025-07-30 14:06:27.885733+00
114	200-200-540_4p.txt	2025-07-30 14:06:28.026421+00
115	20_24_cme.txt	2025-07-30 14:06:28.225196+00
116	20_24_cme2.txt	2025-07-30 14:06:28.715213+00
117	20_24_dv_cme.txt	2025-07-30 14:06:29.131396+00
118	20_24_dv_medi.txt	2025-07-30 14:06:29.424226+00
119	20_d_s.txt	2025-07-30 14:06:29.554767+00
120	20_wln_22a.txt	2025-07-30 14:06:29.6806+00
121	20_wln_22a_6p.txt	2025-07-30 14:06:29.897316+00
122	20_wln_22b.txt	2025-07-30 14:06:30.202644+00
123	20_wln_26a.txt	2025-07-30 14:06:30.328293+00
124	20_wln_26b.txt	2025-07-30 14:06:30.558617+00
125	20_wln_28b_6p.txt	2025-07-30 14:06:30.810987+00
126	20_wln_28b_8p.txt	2025-07-30 14:06:30.97708+00
127	20_wln_28c.txt	2025-07-30 14:06:31.227119+00
128	24_wln_26a.txt	2025-07-30 14:06:31.639983+00
129	24_wln_34a.txt	2025-07-30 14:06:31.886133+00
130	24_wln_42a.txt	2025-07-30 14:06:32.09419+00
131	24_wln_46a.txt	2025-07-30 14:06:32.277481+00
132	250-200-480_4p.txt	2025-07-30 14:06:32.43197+00
133	250-200-480_6p.txt	2025-07-30 14:06:32.631001+00
134	250-200-610_4p.txt	2025-07-30 14:06:32.892549+00
135	250-200-610_6p.txt	2025-07-30 14:06:33.162133+00
136	250-250-360_4p.txt	2025-07-30 14:06:33.524218+00
137	250-250-360_6p.txt	2025-07-30 14:06:33.736318+00
138	250-250-360a_4p.txt	2025-07-30 14:06:33.93825+00
139	250-250-360a_6p.txt	2025-07-30 14:06:34.121445+00
140	250-250-400_4p.txt	2025-07-30 14:06:34.284406+00
141	250-250-400_6p.txt	2025-07-30 14:06:34.500451+00
142	250-250-400a_4p.txt	2025-07-30 14:06:34.689171+00
143	250-250-400a_6p.txt	2025-07-30 14:06:34.844913+00
144	250-250-450_4p.txt	2025-07-30 14:06:35.07737+00
145	250-250-450_6p.txt	2025-07-30 14:06:35.236679+00
146	250-250-540_4p.txt	2025-07-30 14:06:35.373536+00
147	250-250-540_6p.txt	2025-07-30 14:06:35.750939+00
148	250_300_bst.txt	2025-07-30 14:06:35.945883+00
149	250_450.txt	2025-07-30 14:06:36.05997+00
150	28_hc_6p.txt	2025-07-30 14:06:36.148773+00
151	28_hc_8p.txt	2025-07-30 14:06:36.260274+00
152	2_5_k.txt	2025-07-30 14:06:36.365855+00
153	2_5_kl.txt	2025-07-30 14:06:36.543573+00
154	2_k.txt	2025-07-30 14:06:36.688226+00
155	2_kl.txt	2025-07-30 14:06:36.776666+00
156	300-250-600.txt	2025-07-30 14:06:36.86046+00
157	30_hc_6p.txt	2025-07-30 14:06:36.958688+00
158	30_wln_30c.txt	2025-07-30 14:06:37.225115+00
159	30_wln_41c.txt	2025-07-30 14:06:37.36823+00
160	32-200_2f.txt	2025-07-30 14:06:37.473055+00
161	32-200_2f_2p.txt	2025-07-30 14:06:37.718922+00
162	32_hc_6p.txt	2025-07-30 14:06:37.903672+00
163	32_hc_8p.txt	2025-07-30 14:06:38.011302+00
164	32_xhc_6p.txt	2025-07-30 14:06:38.122142+00
165	32_xhc_8p.txt	2025-07-30 14:06:38.233372+00
166	350-300-429_desc.txt	2025-07-30 14:06:38.482124+00
167	36_hc_6p.txt	2025-07-30 14:06:38.920448+00
168	36_xhc_8p.txt	2025-07-30 14:06:39.293875+00
169	3_40i.txt	2025-07-30 14:06:39.405462+00
170	3_4_medi.txt	2025-07-30 14:06:39.589045+00
171	3_k.txt	2025-07-30 14:06:39.753914+00
172	3wln12k.txt	2025-07-30 14:06:39.965959+00
173	3x4x10_5_h_sja.txt	2025-07-30 14:06:40.113555+00
174	400-300-435.txt	2025-07-30 14:06:40.237383+00
175	400-600.txt	2025-07-30 14:06:40.349493+00
176	4503-42936.txt	2025-07-30 14:06:40.448789+00
177	4503-42937.txt	2025-07-30 14:06:40.693308+00
178	4503-44648.txt	2025-07-30 14:06:40.848325+00
179	4503-44649.txt	2025-07-30 14:06:40.978345+00
180	4503-44786.txt	2025-07-30 14:06:41.474064+00
181	4503-44787.txt	2025-07-30 14:06:41.713473+00
182	4504-42564.txt	2025-07-30 14:06:41.933213+00
183	4504-42565.txt	2025-07-30 14:06:42.097959+00
184	4505-48159.txt	2025-07-30 14:06:42.242494+00
185	4505-48190.txt	2025-07-30 14:06:42.395388+00
186	4506-48170.txt	2025-07-30 14:06:42.55026+00
187	4506-48171.txt	2025-07-30 14:06:42.700251+00
188	4625-38112.txt	2025-07-30 14:06:42.823098+00
189	48_48_lonovane.txt	2025-07-30 14:06:42.920158+00
190	4_40_gme.txt	2025-07-30 14:06:43.088252+00
191	4_5.txt	2025-07-30 14:06:43.271354+00
192	4_5_2_stage_medi.txt	2025-07-30 14:06:43.362138+00
193	4_5_ale.txt	2025-07-30 14:06:43.461087+00
194	4_5_ble.txt	2025-07-30 14:06:43.579777+00
195	4_5_cme.txt	2025-07-30 14:06:43.822559+00
196	4_5_dme.txt	2025-07-30 14:06:44.217325+00
197	4_5_medi.txt	2025-07-30 14:06:44.376097+00
198	4k.txt	2025-07-30 14:06:44.460069+00
199	4x6x13_25_h-sja.txt	2025-07-30 14:06:44.618216+00
200	4x6x13_25_l_gsjh.txt	2025-07-30 14:06:44.730302+00
201	4x6x8_5_l_sja.txt	2025-07-30 14:06:44.810169+00
202	50-160_2f.txt	2025-07-30 14:06:44.911607+00
203	50-160_2f_2p.txt	2025-07-30 14:06:45.105023+00
204	50-200_2f.txt	2025-07-30 14:06:45.266303+00
205	50-200_2f_2p.txt	2025-07-30 14:06:45.485184+00
206	50-250_2f.txt	2025-07-30 14:06:45.655236+00
207	50-250_2f_2p.txt	2025-07-30 14:06:45.897578+00
208	50-315_2f.txt	2025-07-30 14:06:46.118283+00
209	5_6.txt	2025-07-30 14:06:46.262906+00
210	5_6_ale.txt	2025-07-30 14:06:46.40121+00
211	5_6_ble.txt	2025-07-30 14:06:46.579868+00
212	5_6_cme.txt	2025-07-30 14:06:46.751549+00
213	5_6_dme.txt	2025-07-30 14:06:46.86796+00
214	5_6_medi.txt	2025-07-30 14:06:46.983893+00
215	5_6_medi_2p.txt	2025-07-30 14:06:47.132142+00
216	5_6_medivane.txt	2025-07-30 14:06:47.347105+00
217	5_6_medivane_2p.txt	2025-07-30 14:06:47.463253+00
218	5_k.txt	2025-07-30 14:06:47.58077+00
219	5_kl.txt	2025-07-30 14:06:47.690774+00
220	5x6_hsc.txt	2025-07-30 14:06:47.830151+00
221	65-125_2f.txt	2025-07-30 14:06:47.932392+00
222	65-160_2f.txt	2025-07-30 14:06:48.204071+00
223	65-160_2f_2p.txt	2025-07-30 14:06:48.68239+00
224	65-200_1f.txt	2025-07-30 14:06:49.174603+00
225	65-200_2f.txt	2025-07-30 14:06:49.298392+00
226	65-200_2f_2p.txt	2025-07-30 14:06:49.443777+00
227	65-250_2f.txt	2025-07-30 14:06:49.647616+00
228	65-250_2f_2p.txt	2025-07-30 14:06:49.857458+00
229	65-315_2f.txt	2025-07-30 14:06:50.107392+00
230	6_8_ale.txt	2025-07-30 14:06:50.280992+00
231	6_8_dme.txt	2025-07-30 14:06:50.579616+00
232	6_8_dmp.txt	2025-07-30 14:06:50.843166+00
233	6_8_eme.txt	2025-07-30 14:06:50.965926+00
234	6_8_gme.txt	2025-07-30 14:06:51.351519+00
235	6_b_b.txt	2025-07-30 14:06:51.586616+00
236	6_hc.txt	2025-07-30 14:06:51.722388+00
237	6_k_6_vane.txt	2025-07-30 14:06:51.821708+00
238	6_k_8_vane.txt	2025-07-30 14:06:51.958168+00
239	6_kl.txt	2025-07-30 14:06:52.088954+00
240	6_lc.txt	2025-07-30 14:06:52.233405+00
241	6_mc.txt	2025-07-30 14:06:52.325681+00
242	6_slm_2p.txt	2025-07-30 14:06:52.414839+00
243	6_wln_18a.txt	2025-07-30 14:06:52.50399+00
244	6_wln_21a.txt	2025-07-30 14:06:52.723797+00
245	6_xlc.txt	2025-07-30 14:06:52.93133+00
246	6x8x11l_dsja.txt	2025-07-30 14:06:53.046869+00
247	6x8x13h_sja.txt	2025-07-30 14:06:53.309493+00
248	700-600-710_6p.txt	2025-07-30 14:06:53.662004+00
249	700-600-710_8p.txt	2025-07-30 14:06:53.896264+00
250	7_kl.txt	2025-07-30 14:06:54.091035+00
251	7_mc.txt	2025-07-30 14:06:54.218521+00
252	80-160_2f.txt	2025-07-30 14:06:54.349263+00
253	80-160_2f_2p.txt	2025-07-30 14:06:54.516454+00
254	80-200_2f.txt	2025-07-30 14:06:54.811127+00
255	80-200_2f_2p.txt	2025-07-30 14:06:54.984789+00
256	80-250_2f.txt	2025-07-30 14:06:55.15902+00
257	80-250_2f_2p.txt	2025-07-30 14:06:55.717888+00
258	80-315_2f.txt	2025-07-30 14:06:55.878587+00
259	80-50-315_2p.txt	2025-07-30 14:06:56.059878+00
260	80-50-315_4p.txt	2025-07-30 14:06:56.220776+00
261	8211-16_970.txt	2025-07-30 14:06:56.436441+00
262	8211-30.txt	2025-07-30 14:06:56.535413+00
263	8312-14.txt	2025-07-30 14:06:56.6345+00
264	8312-14_310f.txt	2025-07-30 14:06:56.810712+00
265	8312-14_311f.txt	2025-07-30 14:06:56.926335+00
266	8312-14_311t.txt	2025-07-30 14:06:57.066093+00
267	8312-14_312t.txt	2025-07-30 14:06:57.148177+00
268	8312-14_313t.txt	2025-07-30 14:06:57.218717+00
269	8312-14_313t_4p.txt	2025-07-30 14:06:57.373091+00
270	8312-16_312t.txt	2025-07-30 14:06:57.597043+00
271	8312-16_370f.txt	2025-07-30 14:06:57.826841+00
272	8312-16_371t.txt	2025-07-30 14:06:57.998543+00
273	8312-16_372t.txt	2025-07-30 14:06:58.076839+00
274	8312-16_373t.txt	2025-07-30 14:06:58.243349+00
275	8312-20_340f.txt	2025-07-30 14:06:58.417368+00
276	8312-20_341t.txt	2025-07-30 14:06:58.718872+00
277	8312-20_342t.txt	2025-07-30 14:06:59.150244+00
278	8312-20_343t.txt	2025-07-30 14:06:59.403313+00
279	8312-24_360f.txt	2025-07-30 14:06:59.503904+00
280	8312-24_361t.txt	2025-07-30 14:06:59.609164+00
281	8312-24_362t.txt	2025-07-30 14:06:59.726447+00
282	8312-24_363t.txt	2025-07-30 14:06:59.820445+00
283	8312-30_a330f.txt	2025-07-30 14:06:59.926521+00
284	8312-30_a331t.txt	2025-07-30 14:07:00.046957+00
285	8312-30_a332t.txt	2025-07-30 14:07:00.154493+00
286	8312-30_a333t.txt	2025-07-30 14:07:00.30812+00
287	8312_-10_b1431t.txt	2025-07-30 14:07:00.467466+00
288	8312_-10_b1433t.txt	2025-07-30 14:07:00.5858+00
289	8314-5.txt	2025-07-30 14:07:00.756653+00
290	8_10_ble.txt	2025-07-30 14:07:00.877265+00
291	8_10_cme_-_ta.txt	2025-07-30 14:07:01.243655+00
292	8_10_cme_-_tb.txt	2025-07-30 14:07:01.502523+00
293	8_10_desc.txt	2025-07-30 14:07:01.720478+00
294	8_10_dme.txt	2025-07-30 14:07:01.849996+00
295	8_10_gme.txt	2025-07-30 14:07:01.967436+00
296	8_8_cme.txt	2025-07-30 14:07:02.25103+00
297	8_8_cme_1900rpm.txt	2025-07-30 14:07:02.358065+00
298	8_8_dme.txt	2025-07-30 14:07:02.442134+00
299	8_8_gme_4p.txt	2025-07-30 14:07:02.620409+00
300	8_b_b.txt	2025-07-30 14:07:02.763908+00
301	8_desc.txt	2025-07-30 14:07:02.901355+00
302	8_hc.txt	2025-07-30 14:07:03.018597+00
303	8_k.txt	2025-07-30 14:07:03.151313+00
304	8_kl.txt	2025-07-30 14:07:03.293391+00
305	8_lc.txt	2025-07-30 14:07:03.366031+00
306	8_mc.txt	2025-07-30 14:07:03.462591+00
307	8_slh_2p.txt	2025-07-30 14:07:03.577906+00
308	8_wln_18a.txt	2025-07-30 14:07:03.739444+00
309	8_wln_18c.txt	2025-07-30 14:07:03.865254+00
310	8_wln_21a.txt	2025-07-30 14:07:04.02114+00
311	8_wln_29b.txt	2025-07-30 14:07:04.164397+00
312	8x10x13_2s.txt	2025-07-30 14:07:04.342094+00
313	8x10x13_2s_new.txt	2025-07-30 14:07:04.414245+00
314	8x10x13_3s.txt	2025-07-30 14:07:04.512685+00
315	8x10x13_3s_new.txt	2025-07-30 14:07:04.594727+00
316	8x10x13_4s.txt	2025-07-30 14:07:04.712295+00
317	8x10x13_4s2p.txt	2025-07-30 14:07:04.794266+00
318	8x10x13_4s_new.txt	2025-07-30 14:07:04.974981+00
319	9-11_2_stage_medivane.txt	2025-07-30 14:07:05.073815+00
320	ape_dwu-150_bc.txt	2025-07-30 14:07:05.145873+00
321	ape_dwu_-_150.txt	2025-07-30 14:07:05.285864+00
322	bdm_16_14.txt	2025-07-30 14:07:05.641482+00
323	dvms_4000-125.txt	2025-07-30 14:07:05.756218+00
324	fd_300-250-400.txt	2025-07-30 14:07:05.818666+00
325	hms_50_4.txt	2025-07-30 14:07:05.902962+00
326	kl_150-100.txt	2025-07-30 14:07:06.001462+00
327	miso_100-200.txt	2025-07-30 14:07:06.171883+00
328	miso_65-315h.txt	2025-07-30 14:07:06.306809+00
329	morgenstond_1.txt	2025-07-30 14:07:06.536815+00
330	msd10x10x13_5_3_4.txt	2025-07-30 14:07:06.675366+00
331	msd_10x10x13_5_3_4.txt	2025-07-30 14:07:06.784482+00
332	msj.txt	2025-07-30 14:07:06.88388+00
333	nitz_100-80-250.txt	2025-07-30 14:07:07.034461+00
334	pj_100.txt	2025-07-30 14:07:07.252427+00
335	pj_100_as.txt	2025-07-30 14:07:07.35037+00
336	pj_150_an.txt	2025-07-30 14:07:07.464418+00
337	pj_150_as.txt	2025-07-30 14:07:07.582379+00
338	pj_200.txt	2025-07-30 14:07:07.741736+00
339	pj_200_as.txt	2025-07-30 14:07:07.847551+00
340	pj_250_an.txt	2025-07-30 14:07:07.935013+00
341	pj_250_as.txt	2025-07-30 14:07:08.046279+00
342	pj_250_bs.txt	2025-07-30 14:07:08.157828+00
343	pj_250_h.txt	2025-07-30 14:07:08.435798+00
344	pj_258_h.txt	2025-07-30 14:07:08.753966+00
345	pj_80.txt	2025-07-30 14:07:09.111964+00
346	pj_80_as.txt	2025-07-30 14:07:09.351993+00
347	pl_100_an.txt	2025-07-30 14:07:09.473713+00
348	pl_100_as.txt	2025-07-30 14:07:09.602131+00
349	pl_150_an.txt	2025-07-30 14:07:09.829454+00
350	pl_150_as.txt	2025-07-30 14:07:09.955322+00
351	pl_200_an.txt	2025-07-30 14:07:10.114366+00
352	pl_200_as.txt	2025-07-30 14:07:10.247288+00
353	pl_80_an.txt	2025-07-30 14:07:10.406753+00
354	pl_80_as.txt	2025-07-30 14:07:10.599839+00
355	qw400-26-45.txt	2025-07-30 14:07:10.776644+00
356	scp_150_580ha-132_4.txt	2025-07-30 14:07:10.879811+00
357	scp_250_450ha.txt	2025-07-30 14:07:10.955728+00
358	umgeni_verulam_july_2022.txt	2025-07-30 14:07:11.084653+00
359	vbk_35-22_3_stage.txt	2025-07-30 14:07:11.268122+00
360	vbk_35-22_5_3_stage.txt	2025-07-30 14:07:11.522778+00
361	vbk_420_018-4s.txt	2025-07-30 14:07:11.748663+00
362	vbk_620_022-4s.txt	2025-07-30 14:07:11.944124+00
363	vbk_620_022-4s__test_curve.txt	2025-07-30 14:07:12.052714+00
364	wi-1414.txt	2025-07-30 14:07:12.158343+00
365	wvp-130-30__p30.txt	2025-07-30 14:07:12.298515+00
366	wxh-100-240.txt	2025-07-30 14:07:12.386482+00
367	wxh-150-300.txt	2025-07-30 14:07:12.528329+00
368	wxh-32-132.txt	2025-07-30 14:07:12.676832+00
369	wxh-32-135.txt	2025-07-30 14:07:12.815636+00
370	wxh-34-35-100.txt	2025-07-30 14:07:12.93149+00
371	wxh-40-135.txt	2025-07-30 14:07:13.105277+00
372	wxh-40-135_2p.txt	2025-07-30 14:07:13.269693+00
373	wxh-50-160.txt	2025-07-30 14:07:13.389861+00
374	wxh-50-160_2p.txt	2025-07-30 14:07:13.507586+00
375	wxh-64-100-150.txt	2025-07-30 14:07:13.651004+00
376	wxh-64-100-150b.txt	2025-07-30 14:07:13.791377+00
377	wxh-64-125-150a.txt	2025-07-30 14:07:13.881799+00
378	wxh-64-32-50.txt	2025-07-30 14:07:14.032974+00
379	wxh-64-35-100.txt	2025-07-30 14:07:14.144335+00
380	wxh-64-40-65.txt	2025-07-30 14:07:14.260968+00
381	wxh-64-80-125.txt	2025-07-30 14:07:14.409163+00
382	wxh-65-185.txt	2025-07-30 14:07:14.568582+00
383	wxh-65-185_2p.txt	2025-07-30 14:07:14.712342+00
384	wxh-80-210.txt	2025-07-30 14:07:14.834547+00
385	wxh-80-210_2p.txt	2025-07-30 14:07:14.977358+00
386	xf18.txt	2025-07-30 14:07:15.168472+00
\.


--
-- Data for Name: pump_bep_markers; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.pump_bep_markers (id, pump_id, impeller_diameter, bep_flow, bep_head, bep_efficiency, marker_label, coordinate_x, coordinate_y, created_at) FROM stdin;
\.


--
-- Data for Name: pump_curves; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.pump_curves (id, pump_id, impeller_diameter_mm) FROM stdin;
1	1	184
2	1	192
3	1	200
4	1	208
5	1	217
6	2	184
7	2	192
8	2	200
9	2	208
10	2	217
11	3	260
12	4	226
13	4	246
14	4	266
15	5	226
16	5	236
17	5	246
18	5	256
19	5	266
20	6	276
21	6	306
22	6	321
23	6	336
24	7	336
25	7	375
26	7	393
27	7	412
28	8	173
29	9	210
30	9	250
31	9	293
32	10	390
33	11	531
34	11	584
35	12	454
36	12	500
37	12	546
38	13	510
39	13	573
40	13	605
41	14	330
42	14	406
43	15	470
44	16	365
45	16	454
46	17	442
47	17	590
48	18	530
49	18	614
50	18	670
51	19	685
52	19	720
53	19	755
54	20	198
55	21	197
56	22	203
57	22	406
58	22	457
59	23	161
60	23	182
61	23	202
62	24	600
63	25	226
64	25	251
65	25	276
66	26	268
67	26	300
68	26	343
69	27	221
70	27	231
71	27	241
72	27	251
73	27	261
74	27	271
75	28	276
76	28	306
77	28	321
78	28	336
79	29	338
80	29	378
81	29	418
82	30	600
83	31	419
84	31	483
85	32	382
86	33	501.6
87	33	590.5
88	34	470
89	34	530
90	34	555.5
91	35	470
92	35	530
93	35	555.5
94	36	474
95	37	229
96	38	229
97	39	215.7
98	39	226
99	39	228.6
100	40	225.25
101	41	225
102	42	489
103	42	502
104	42	540
105	43	464
106	43	502
107	43	540
108	44	227
109	45	310
110	45	340
111	45	385
112	46	334
113	46	374
114	46	390
115	47	340
116	47	415
117	47	460
118	48	340
119	48	403
120	48	445
121	49	483
122	49	502
123	49	521
124	49	552
125	50	464
126	50	502
127	50	540
128	51	596.9
129	52	419
130	52	483
131	53	482.6
132	53	533.4
133	54	464
134	54	546
135	55	603
136	55	683
137	55	720
138	56	260
139	57	266
140	58	354
141	59	262
142	60	262
143	61	262
144	62	400
145	62	475
146	63	240
147	63	260
148	63	272
149	64	323
150	65	315
151	65	360
152	65	406
153	66	210
154	66	220
155	66	230
156	66	239
157	67	190
158	67	200
159	67	210
160	68	212
161	68	214
162	68	215
163	68	216
164	68	217
165	69	216
166	69	236
167	69	266
168	70	261
169	70	291
170	70	321
171	70	336
172	71	350
173	71	365
174	71	380
175	71	395
176	71	406
177	71	418
178	72	307
179	73	307
180	74	307
181	75	307
182	76	490
183	76	562
184	76	610
185	77	610
186	77	675
187	77	745
188	78	730
189	78	838
190	78	910
191	79	368
192	79	425
193	80	635
194	80	675
195	80	750
196	81	545
197	81	575
198	81	625
199	82	343
200	83	343
201	84	343
202	85	343
203	86	343
204	87	343
205	88	343
206	89	362
207	90	362
208	91	362
209	92	362
210	93	362
211	94	0
212	95	203
213	95	267
214	96	215
215	97	280
216	97	292
217	97	309
218	98	281
219	98	293
220	98	309
221	99	315
222	99	338
223	99	371
224	100	317
225	100	340
226	100	371
227	101	370
228	101	420
229	101	459
230	102	370
231	102	420
232	102	459
233	103	245
234	103	255
235	103	265
236	103	272
237	104	245
238	104	255
239	104	265
240	104	272
241	105	220
242	105	230
243	105	245
244	106	220
245	106	230
246	106	245
247	107	275
248	107	290
249	107	300
250	107	309
251	108	275
252	108	285
253	108	295
254	108	309
255	109	250
256	109	265
257	109	275
258	110	250
259	110	265
260	110	275
261	111	318
262	111	332
263	111	352
264	112	358
265	112	384
266	112	431
267	113	360
268	113	400
269	113	431
270	114	420
271	114	480
272	114	542
273	115	540
274	115	740
275	116	540
276	116	740
277	117	608
278	118	780
279	119	698
280	120	500
281	120	520
282	120	545
283	121	475
284	121	525
285	121	545
286	122	455
287	122	472
288	122	490
289	123	520
290	123	556
291	123	580
292	124	540
293	124	595
294	124	650
295	125	592
296	125	675
297	125	724
298	126	660
299	126	686
300	126	724
301	127	635
302	127	672
303	127	743
304	128	680
305	129	675
306	129	720
307	129	770
308	130	940
309	130	1041
310	130	1102
311	131	860
312	131	962
313	131	1085
314	132	401
315	132	446
316	132	484
317	133	403
318	133	433
319	133	484
320	134	475
321	134	540
322	134	609
323	135	475
324	135	540
325	135	609
326	136	310
327	136	325
328	136	340
329	136	358
330	137	310
331	137	325
332	137	340
333	137	350
334	137	358
335	138	280
336	138	295
337	138	310
338	139	280
339	139	296
340	139	310
341	140	345
342	140	360
343	140	375
344	140	398
345	141	345
346	141	360
347	141	375
348	141	390
349	141	398
350	142	310
351	142	325
352	142	345
353	143	310
354	143	325
355	143	345
356	144	395
357	144	428
358	144	453
359	145	397
360	145	430
361	145	453
362	146	444
363	146	494
364	146	537
365	147	446
366	147	495
367	147	537
368	148	315
369	148	335
370	148	355
371	148	375
372	149	0
373	150	451
374	150	501
375	151	451
376	151	501
377	152	304
378	152	381
379	153	165
380	153	203
381	154	229
382	154	305
383	155	210
384	155	260
385	156	610
386	157	468
387	157	536
388	158	590
389	158	620
390	158	686
391	159	902
392	159	965
393	159	1067
394	160	180
395	160	189
396	160	197
397	160	205
398	160	212
399	161	180
400	161	197
401	161	212
402	162	527
403	162	588
404	163	527
405	163	588
406	164	590
407	164	640
408	165	590
409	165	640
410	166	364
411	166	403
412	166	428
413	167	600
414	167	660.4
415	168	664
416	168	720
417	169	242
418	169	254
419	169	267
420	169	277
421	170	360
422	171	238
423	171	318
424	172	229
425	172	267
426	172	305
427	173	261
428	174	446
429	175	553
430	176	108
431	176	122
432	176	135
433	177	108
434	177	122
435	177	135
436	178	108
437	178	122
438	178	135
439	179	108
440	179	122
441	179	135
442	180	108
443	180	122
444	180	135
445	181	108
446	181	122
447	181	135
448	182	130
449	182	142
450	182	155
451	183	130
452	183	142
453	183	155
454	184	154
455	184	166
456	184	180
457	185	154
458	185	166
459	185	180
460	186	170
461	186	186
462	186	205
463	187	170
464	187	186
465	187	205
466	188	376
467	189	967
468	189	1055
469	189	1125
470	190	242
471	190	254
472	190	267
473	190	277
474	191	288
475	191	360
476	192	370
477	193	134
478	193	148
479	193	157
480	194	162
481	194	178
482	194	188
483	195	187
484	195	209
485	195	220
486	196	227
487	196	260
488	196	275
489	197	370
490	198	248
491	198	330
492	198	343
493	199	337
494	200	254
495	200	336.5
496	201	216
497	202	137
498	202	157
499	202	177
500	203	137
501	203	157
502	203	177
503	204	178
504	204	188
505	204	198
506	204	208
507	204	218
508	205	178
509	205	188
510	205	198
511	205	218
512	206	207
513	206	217
514	206	227
515	206	247
516	207	207
517	207	227
518	207	247
519	208	280
520	208	328
521	209	288
522	209	360
523	210	255
524	210	285
525	210	300
526	211	303
527	211	335
528	211	351
529	212	193
530	212	210
531	212	220
532	213	230
533	213	247
534	213	274
535	214	220
536	214	305
537	214	360
538	215	220
539	215	305
540	215	360
541	216	220
542	216	305
543	216	360
544	217	220
545	217	305
546	217	360
547	218	268
548	218	356
549	219	184
550	219	229
551	220	381
552	221	113
553	221	123
554	221	133
555	221	143
556	222	140
557	222	150
558	222	160
559	222	170
560	222	177
561	223	140
562	223	150
563	223	160
564	223	170
565	223	177
566	224	218
567	225	178
568	225	202
569	225	218
570	226	178
571	226	186
572	226	202
573	226	210
574	226	218
575	227	226
576	227	246
577	227	266
578	228	226
579	228	236
580	228	245
581	228	256
582	228	266
583	229	281
584	229	306
585	229	318
586	229	328
587	230	259
588	230	295
589	230	312
590	231	232
591	231	273
592	232	232
593	232	273
594	233	285
595	233	300
596	233	318
597	233	335
598	234	472
599	235	330
600	235	387
601	236	2900
602	237	295
603	237	394
604	238	286
605	238	381
606	239	203
607	239	254
608	240	142
609	241	2250
610	242	147
611	243	370
612	243	422
613	243	450
614	244	461
615	244	505
616	244	560
617	245	108.45
618	246	279
619	247	254
620	247	342
621	248	600
622	248	675
623	248	715
624	249	600
625	249	675
626	249	715
627	250	248
628	250	292
629	251	2250
630	252	160
631	252	168
632	252	177
633	253	160
634	253	168
635	253	173
636	253	177
637	254	184
638	254	192
639	254	202
640	254	209
641	254	216
642	255	184
643	255	202
644	255	216
645	256	220
646	256	230
647	256	240
648	256	251
649	256	262
650	256	271
651	257	220
652	257	240
653	257	262
654	257	271
655	258	276
656	258	306
657	258	321
658	258	336
659	259	220
660	259	280
661	259	328
662	260	220
663	260	280
664	260	328
665	261	970
666	262	635
667	263	350
668	264	970
669	265	1470
670	266	970
671	267	970
672	268	970
673	269	1470
674	270	970
675	271	970
676	272	970
677	273	970
678	274	970
679	275	735
680	276	843
681	277	735
682	278	735
683	279	735
684	280	735
685	281	735
686	282	735
687	283	580
688	284	580
689	285	580
690	286	0
691	287	880
692	288	880
693	289	350
694	290	318
695	290	340
696	290	360
697	290	376
698	290	383
699	291	458
700	292	400
701	293	482.6
702	293	533.4
703	294	448
704	294	566
705	295	522
706	295	544
707	295	567
708	295	591
709	296	444
710	297	444
711	298	433
712	298	465
713	298	495
714	298	527
715	299	417
716	299	470
717	299	495
718	300	406
719	300	495
720	301	482.6
721	301	533.4
722	302	192
723	303	330.2
724	303	406.4
725	304	248
726	304	292
727	305	2250
728	306	2900
729	307	186
730	308	356
731	308	410
732	308	454
733	309	356
734	309	425
735	309	463
736	310	438
737	310	570
738	311	590
739	311	674
740	311	730
741	312	344
742	313	344
743	314	344
744	315	344
745	316	344
746	317	344
747	318	344
748	319	500
749	320	1000
750	320	1600
751	320	1800
752	320	2200
753	321	1600
754	321	1800
755	321	2000
756	321	2200
757	322	343
758	322	419
759	323	675
760	324	409
761	325	165
762	326	302
763	327	201
764	328	304
765	329	450
766	330	2860
767	331	2860
768	332	484
769	333	210
770	333	292
771	334	340
772	334	378
773	335	320
774	335	359
775	335	378
776	336	435
777	337	435
778	338	459
779	339	459
780	340	475
781	340	528
782	340	555
783	341	475
784	341	528
785	341	555
786	342	495
787	342	528
788	342	555
789	343	490
790	343	530
791	344	520
792	344	580
793	345	282
794	346	269
795	346	298
796	346	314
797	347	247
798	347	259
799	347	288
800	348	249
801	348	273
802	348	288
803	349	287
804	349	319
805	349	337
806	350	287
807	350	303
808	350	319
809	350	337
810	351	313
811	351	360
812	352	313
813	352	343
814	352	360
815	353	203
816	353	240
817	354	203
818	354	227
819	354	240
820	355	305
821	356	561
822	357	382
823	358	362
824	359	369
825	360	369
826	361	420.6
827	362	632.8
828	363	632.8
829	364	1499
830	365	730
831	366	220
832	366	240
833	367	300
834	368	122
835	368	135
836	369	122
837	369	135
838	370	190
839	370	210
840	371	122
841	371	135
842	372	122
843	372	135
844	373	144
845	373	160
846	374	160
847	375	242
848	375	275
849	376	242
850	376	275
851	377	280
852	377	318
853	378	146
854	378	160
855	379	190
856	379	210
857	380	160
858	380	175
859	381	210
860	381	240
861	382	169
862	382	185
863	383	169
864	383	185
865	384	189
866	384	210
867	385	189
868	385	210
869	386	311
\.


--
-- Data for Name: pump_diameters; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.pump_diameters (id, pump_id, sequence_order, diameter_value) FROM stdin;
1	1	1	184
2	1	2	192
3	1	3	200
4	1	4	208
5	1	5	217
6	1	6	0
7	1	7	0
8	1	8	0
9	2	1	184
10	2	2	192
11	2	3	200
12	2	4	208
13	2	5	217
14	2	6	0
15	2	7	0
16	2	8	0
17	3	1	200
18	3	2	230
19	3	3	260
20	3	4	0
21	3	5	0
22	3	6	0
23	3	7	0
24	3	8	0
25	4	1	226
26	4	2	236
27	4	3	246
28	4	4	256
29	4	5	266
30	4	6	0
31	4	7	0
32	4	8	0
33	5	1	226
34	5	2	236
35	5	3	246
36	5	4	256
37	5	5	266
38	5	6	0
39	5	7	0
40	5	8	0
41	6	1	276
42	6	2	291
43	6	3	306
44	6	4	321
45	6	5	336
46	6	6	0
47	6	7	0
48	6	8	0
49	7	1	336
50	7	2	355
51	7	3	374
52	7	4	393
53	7	5	412
54	7	6	0
55	7	7	0
56	7	8	0
57	8	1	0
58	8	2	0
59	8	3	0
60	8	4	0
61	8	5	0
62	8	6	0
63	8	7	0
64	8	8	0
65	9	1	210
66	9	2	230
67	9	3	250
68	9	4	270
69	9	5	293
70	9	6	0
71	9	7	0
72	9	8	0
73	10	1	390
74	10	2	375
75	10	3	345
76	10	4	325
77	10	5	0
78	10	6	0
79	10	7	0
80	10	8	0
81	11	1	0
82	11	2	0
83	11	3	0
84	11	4	0
85	11	5	0
86	11	6	0
87	11	7	0
88	11	8	0
89	12	1	454
90	12	2	480
91	12	3	500
92	12	4	520
93	12	5	546
94	12	6	0
95	12	7	0
96	12	8	0
97	13	1	510
98	13	2	520
99	13	3	530
100	13	4	540
101	13	5	550
102	13	6	573
103	13	7	605
104	13	8	0
105	14	1	0
106	14	2	0
107	14	3	0
108	14	4	0
109	14	5	0
110	14	6	0
111	14	7	0
112	14	8	0
113	15	1	400
114	15	2	435
115	15	3	470
116	15	4	0
117	15	5	0
118	15	6	0
119	15	7	0
120	15	8	0
121	16	1	365
122	16	2	420
123	16	3	454
124	16	4	0
125	16	5	0
126	16	6	0
127	16	7	0
128	16	8	0
129	17	1	442
130	17	2	535
131	17	3	590
132	17	4	0
133	17	5	0
134	17	6	0
135	17	7	0
136	17	8	0
137	18	1	530
138	18	2	614
139	18	3	670
140	18	4	0
141	18	5	0
142	18	6	0
143	18	7	0
144	18	8	0
145	19	1	0
146	19	2	0
147	19	3	0
148	19	4	0
149	19	5	0
150	19	6	0
151	19	7	0
152	19	8	0
153	20	1	0
154	20	2	0
155	20	3	0
156	20	4	0
157	20	5	0
158	20	6	0
159	20	7	0
160	20	8	0
161	21	1	0
162	21	2	0
163	21	3	0
164	21	4	0
165	21	5	0
166	21	6	0
167	21	7	0
168	21	8	0
169	22	1	0
170	22	2	0
171	22	3	0
172	22	4	0
173	22	5	0
174	22	6	0
175	22	7	0
176	22	8	0
177	23	1	0
178	23	2	0
179	23	3	0
180	23	4	0
181	23	5	0
182	23	6	0
183	23	7	0
184	23	8	0
185	24	1	0
186	24	2	0
187	24	3	0
188	24	4	0
189	24	5	0
190	24	6	0
191	24	7	0
192	24	8	0
193	25	1	226
194	25	2	251
195	25	3	276
196	25	4	0
197	25	5	0
198	25	6	0
199	25	7	0
200	25	8	0
201	26	1	265
202	26	2	275
203	26	3	290
204	26	4	300
205	26	5	315
206	26	6	325
207	26	7	343
208	26	8	0
209	27	1	221
210	27	2	231
211	27	3	241
212	27	4	251
213	27	5	261
214	27	6	271
215	27	7	0
216	27	8	0
217	28	1	276
218	28	2	291
219	28	3	306
220	28	4	321
221	28	5	336
222	28	6	0
223	28	7	0
224	28	8	0
225	29	1	338
226	29	2	358
227	29	3	378
228	29	4	398
229	29	5	418
230	29	6	0
231	29	7	0
232	29	8	0
233	30	1	813
234	30	2	813
235	30	3	813
236	30	4	813
237	30	5	813
238	30	6	813
239	30	7	813
240	30	8	0
241	31	1	0
242	31	2	0
243	31	3	0
244	31	4	0
245	31	5	0
246	31	6	0
247	31	7	0
248	31	8	0
249	32	1	0
250	32	2	0
251	32	3	0
252	32	4	0
253	32	5	0
254	32	6	0
255	32	7	0
256	32	8	0
257	33	1	0
258	33	2	0
259	33	3	0
260	33	4	0
261	33	5	0
262	33	6	0
263	33	7	0
264	33	8	0
265	34	1	470
266	34	2	500
267	34	3	530
268	34	4	555.5
269	34	5	0
270	34	6	0
271	34	7	0
272	34	8	0
273	35	1	470
274	35	2	500
275	35	3	530
276	35	4	555.5
277	35	5	0
278	35	6	0
279	35	7	0
280	35	8	0
281	36	1	0
282	36	2	0
283	36	3	0
284	36	4	0
285	36	5	0
286	36	6	0
287	36	7	0
288	36	8	0
289	37	1	184
290	37	2	206
291	37	3	229
292	37	4	0
293	37	5	0
294	37	6	0
295	37	7	0
296	37	8	0
297	38	1	185
298	38	2	207
299	38	3	229
300	38	4	0
301	38	5	0
302	38	6	0
303	38	7	0
304	38	8	0
305	39	1	216
306	39	2	226
307	39	3	229
308	39	4	0
309	39	5	0
310	39	6	0
311	39	7	0
312	39	8	0
313	40	1	225
314	40	2	0
315	40	3	0
316	40	4	0
317	40	5	0
318	40	6	0
319	40	7	0
320	40	8	0
321	41	1	0
322	41	2	0
323	41	3	0
324	41	4	0
325	41	5	0
326	41	6	0
327	41	7	0
328	41	8	0
329	42	1	483
330	42	2	502
331	42	3	521
332	42	4	552
333	42	5	0
334	42	6	0
335	42	7	0
336	42	8	0
337	43	1	464
338	43	2	483
339	43	3	502
340	43	4	521
341	43	5	540
342	43	6	0
343	43	7	0
344	43	8	0
345	44	1	180
346	44	2	210
347	44	3	227
348	44	4	0
349	44	5	0
350	44	6	0
351	44	7	0
352	44	8	0
353	45	1	310
354	45	2	350
355	45	3	385
356	45	4	0
357	45	5	0
358	45	6	0
359	45	7	0
360	45	8	0
361	46	1	334
362	46	2	353
363	46	3	375
364	46	4	390
365	46	5	0
366	46	6	0
367	46	7	0
368	46	8	0
369	47	1	340
370	47	2	415
371	47	3	460
372	47	4	0
373	47	5	0
374	47	6	0
375	47	7	0
376	47	8	0
377	48	1	340
378	48	2	403
379	48	3	445
380	48	4	0
381	48	5	0
382	48	6	0
383	48	7	0
384	48	8	0
385	49	1	483
386	49	2	502
387	49	3	521
388	49	4	552
389	49	5	0
390	49	6	0
391	49	7	0
392	49	8	0
393	50	1	0
394	50	2	0
395	50	3	0
396	50	4	0
397	50	5	0
398	50	6	0
399	50	7	0
400	50	8	0
401	51	1	444.5
402	51	2	520.7
403	51	3	596.9
404	51	4	0
405	51	5	0
406	51	6	0
407	51	7	0
408	51	8	0
409	52	1	419
410	52	2	457
411	52	3	483
412	52	4	0
413	52	5	0
414	52	6	0
415	52	7	0
416	52	8	0
417	53	1	482
418	53	2	533
419	53	3	0
420	53	4	0
421	53	5	0
422	53	6	0
423	53	7	0
424	53	8	0
425	54	1	0
426	54	2	0
427	54	3	0
428	54	4	0
429	54	5	0
430	54	6	0
431	54	7	0
432	54	8	0
433	55	1	603
434	55	2	643
435	55	3	683
436	55	4	710
437	55	5	720
438	55	6	0
439	55	7	0
440	55	8	0
441	56	1	0
442	56	2	0
443	56	3	0
444	56	4	0
445	56	5	0
446	56	6	0
447	56	7	0
448	56	8	0
449	57	1	0
450	57	2	0
451	57	3	0
452	57	4	0
453	57	5	0
454	57	6	0
455	57	7	0
456	57	8	0
457	58	1	0
458	58	2	0
459	58	3	0
460	58	4	0
461	58	5	0
462	58	6	0
463	58	7	0
464	58	8	0
465	59	1	0
466	59	2	0
467	59	3	0
468	59	4	0
469	59	5	0
470	59	6	0
471	59	7	0
472	59	8	0
473	60	1	0
474	60	2	0
475	60	3	0
476	60	4	0
477	60	5	0
478	60	6	0
479	60	7	0
480	60	8	0
481	61	1	0
482	61	2	0
483	61	3	0
484	61	4	0
485	61	5	0
486	61	6	0
487	61	7	0
488	61	8	0
489	62	1	400
490	62	2	445
491	62	3	475
492	62	4	0
493	62	5	0
494	62	6	0
495	62	7	0
496	62	8	0
497	63	1	240
498	63	2	250
499	63	3	260
500	63	4	272
501	63	5	0
502	63	6	0
503	63	7	0
504	63	8	0
505	64	1	0
506	64	2	0
507	64	3	0
508	64	4	0
509	64	5	0
510	64	6	0
511	64	7	0
512	64	8	0
513	65	1	315
514	65	2	330
515	65	3	345
516	65	4	360
517	65	5	375
518	65	6	390
519	65	7	406
520	65	8	0
521	66	1	0
522	66	2	0
523	66	3	0
524	66	4	0
525	66	5	0
526	66	6	0
527	66	7	0
528	66	8	0
529	67	1	0
530	67	2	0
531	67	3	0
532	67	4	0
533	67	5	0
534	67	6	0
535	67	7	0
536	67	8	0
537	68	1	212
538	68	2	214
539	68	3	215
540	68	4	216
541	68	5	217
542	68	6	0
543	68	7	0
544	68	8	0
545	69	1	216
546	69	2	226
547	69	3	236
548	69	4	246
549	69	5	256
550	69	6	266
551	69	7	0
552	69	8	0
553	70	1	261
554	70	2	276
555	70	3	291
556	70	4	306
557	70	5	321
558	70	6	336
559	70	7	0
560	70	8	0
561	71	1	350
562	71	2	365
563	71	3	380
564	71	4	395
565	71	5	406
566	71	6	418
567	71	7	0
568	71	8	0
569	72	1	250
570	72	2	307
571	72	3	0
572	72	4	0
573	72	5	0
574	72	6	0
575	72	7	0
576	72	8	0
577	73	1	252
578	73	2	280
579	73	3	307
580	73	4	0
581	73	5	0
582	73	6	0
583	73	7	0
584	73	8	0
585	74	1	250
586	74	2	280
587	74	3	307
588	74	4	0
589	74	5	0
590	74	6	0
591	74	7	0
592	74	8	0
593	75	1	0
594	75	2	0
595	75	3	0
596	75	4	0
597	75	5	0
598	75	6	0
599	75	7	0
600	75	8	0
601	76	1	490
602	76	2	562
603	76	3	610
604	76	4	0
605	76	5	0
606	76	6	0
607	76	7	0
608	76	8	0
609	77	1	610
610	77	2	640
611	77	3	675
612	77	4	715
613	77	5	745
614	77	6	0
615	77	7	0
616	77	8	0
617	78	1	0
618	78	2	0
619	78	3	0
620	78	4	0
621	78	5	0
622	78	6	0
623	78	7	0
624	78	8	0
625	79	1	368
626	79	2	395
627	79	3	425
628	79	4	0
629	79	5	0
630	79	6	0
631	79	7	0
632	79	8	0
633	80	1	635
634	80	2	675
635	80	3	715
636	80	4	750
637	80	5	0
638	80	6	0
639	80	7	0
640	80	8	0
641	81	1	0
642	81	2	0
643	81	3	0
644	81	4	0
645	81	5	0
646	81	6	0
647	81	7	0
648	81	8	0
649	82	1	274
650	82	2	308
651	82	3	343
652	82	4	0
653	82	5	0
654	82	6	0
655	82	7	0
656	82	8	0
657	83	1	274
658	83	2	308
659	83	3	343
660	83	4	0
661	83	5	0
662	83	6	0
663	83	7	0
664	83	8	0
665	84	1	256
666	84	2	300
667	84	3	343
668	84	4	0
669	84	5	0
670	84	6	0
671	84	7	0
672	84	8	0
673	85	1	272
674	85	2	306
675	85	3	343
676	85	4	0
677	85	5	0
678	85	6	0
679	85	7	0
680	85	8	0
681	86	1	343
682	86	2	0
683	86	3	0
684	86	4	0
685	86	5	0
686	86	6	0
687	86	7	0
688	86	8	0
689	87	1	272
690	87	2	306
691	87	3	343
692	87	4	0
693	87	5	0
694	87	6	0
695	87	7	0
696	87	8	0
697	88	1	258
698	88	2	300
699	88	3	343
700	88	4	0
701	88	5	0
702	88	6	0
703	88	7	0
704	88	8	0
705	89	1	0
706	89	2	0
707	89	3	0
708	89	4	0
709	89	5	0
710	89	6	0
711	89	7	0
712	89	8	0
713	90	1	274
714	90	2	318
715	90	3	362
716	90	4	0
717	90	5	0
718	90	6	0
719	90	7	0
720	90	8	0
721	91	1	292
722	91	2	327
723	91	3	362
724	91	4	0
725	91	5	0
726	91	6	0
727	91	7	0
728	91	8	0
729	92	1	291
730	92	2	362
731	92	3	0
732	92	4	0
733	92	5	0
734	92	6	0
735	92	7	0
736	92	8	0
737	93	1	281
738	93	2	362
739	93	3	0
740	93	4	0
741	93	5	0
742	93	6	0
743	93	7	0
744	93	8	0
745	94	1	0
746	94	2	0
747	94	3	0
748	94	4	0
749	94	5	0
750	94	6	0
751	94	7	0
752	94	8	0
753	95	1	203
754	95	2	230
755	95	3	267
756	95	4	0
757	95	5	0
758	95	6	0
759	95	7	0
760	95	8	0
761	96	1	152
762	96	2	190
763	96	3	215
764	96	4	0
765	96	5	0
766	96	6	0
767	96	7	0
768	96	8	0
769	97	1	280
770	97	2	292
771	97	3	309
772	97	4	0
773	97	5	0
774	97	6	0
775	97	7	0
776	97	8	0
777	98	1	0
778	98	2	0
779	98	3	0
780	98	4	0
781	98	5	0
782	98	6	0
783	98	7	0
784	98	8	0
785	99	1	315
786	99	2	327
787	99	3	338
788	99	4	350
789	99	5	362
790	99	6	371
791	99	7	0
792	99	8	0
793	100	1	0
794	100	2	0
795	100	3	0
796	100	4	0
797	100	5	0
798	100	6	0
799	100	7	0
800	100	8	0
801	101	1	0
802	101	2	0
803	101	3	0
804	101	4	0
805	101	5	0
806	101	6	0
807	101	7	0
808	101	8	0
809	102	1	370
810	102	2	385
811	102	3	405
812	102	4	420
813	102	5	440
814	102	6	459
815	102	7	0
816	102	8	0
817	103	1	0
818	103	2	0
819	103	3	0
820	103	4	0
821	103	5	0
822	103	6	0
823	103	7	0
824	103	8	0
825	104	1	0
826	104	2	0
827	104	3	0
828	104	4	0
829	104	5	0
830	104	6	0
831	104	7	0
832	104	8	0
833	105	1	0
834	105	2	0
835	105	3	0
836	105	4	0
837	105	5	0
838	105	6	0
839	105	7	0
840	105	8	0
841	106	1	0
842	106	2	0
843	106	3	0
844	106	4	0
845	106	5	0
846	106	6	0
847	106	7	0
848	106	8	0
849	107	1	0
850	107	2	0
851	107	3	0
852	107	4	0
853	107	5	0
854	107	6	0
855	107	7	0
856	107	8	0
857	108	1	0
858	108	2	0
859	108	3	0
860	108	4	0
861	108	5	0
862	108	6	0
863	108	7	0
864	108	8	0
865	109	1	0
866	109	2	0
867	109	3	0
868	109	4	0
869	109	5	0
870	109	6	0
871	109	7	0
872	109	8	0
873	110	1	0
874	110	2	0
875	110	3	0
876	110	4	0
877	110	5	0
878	110	6	0
879	110	7	0
880	110	8	0
881	111	1	0
882	111	2	0
883	111	3	0
884	111	4	0
885	111	5	0
886	111	6	0
887	111	7	0
888	111	8	0
889	112	1	358
890	112	2	371
891	112	3	384
892	112	4	398
893	112	5	411
894	112	6	431
895	112	7	0
896	112	8	0
897	113	1	0
898	113	2	0
899	113	3	0
900	113	4	0
901	113	5	0
902	113	6	0
903	113	7	0
904	113	8	0
905	114	1	420
906	114	2	440
907	114	3	460
908	114	4	480
909	114	5	500
910	114	6	520
911	114	7	542
912	114	8	0
913	115	1	540
914	115	2	600
915	115	3	670
916	115	4	740
917	115	5	0
918	115	6	0
919	115	7	0
920	115	8	0
921	116	1	540
922	116	2	600
923	116	3	670
924	116	4	740
925	116	5	0
926	116	6	0
927	116	7	0
928	116	8	0
929	117	1	544
930	117	2	608
931	117	3	0
932	117	4	0
933	117	5	0
934	117	6	0
935	117	7	0
936	117	8	0
937	118	1	641
938	118	2	691
939	118	3	735
940	118	4	810
941	118	5	870
942	118	6	0
943	118	7	0
944	118	8	0
945	119	1	630
946	119	2	698
947	119	3	0
948	119	4	0
949	119	5	0
950	119	6	0
951	119	7	0
952	119	8	0
953	120	1	500
954	120	2	520
955	120	3	545
956	120	4	0
957	120	5	0
958	120	6	0
959	120	7	0
960	120	8	0
961	121	1	475
962	121	2	500
963	121	3	525
964	121	4	545
965	121	5	0
966	121	6	0
967	121	7	0
968	121	8	0
969	122	1	455
970	122	2	472
971	122	3	490
972	122	4	0
973	122	5	0
974	122	6	0
975	122	7	0
976	122	8	0
977	123	1	520
978	123	2	556
979	123	3	580
980	123	4	0
981	123	5	0
982	123	6	0
983	123	7	0
984	123	8	0
985	124	1	540
986	124	2	595
987	124	3	650
988	124	4	0
989	124	5	0
990	124	6	0
991	124	7	0
992	124	8	0
993	125	1	592
994	125	2	675
995	125	3	724
996	125	4	0
997	125	5	0
998	125	6	0
999	125	7	0
1000	125	8	0
1001	126	1	0
1002	126	2	0
1003	126	3	0
1004	126	4	0
1005	126	5	0
1006	126	6	0
1007	126	7	0
1008	126	8	0
1009	127	1	635
1010	127	2	672
1011	127	3	711
1012	127	4	743
1013	127	5	0
1014	127	6	0
1015	127	7	0
1016	127	8	0
1017	128	1	576
1018	128	2	628
1019	128	3	680
1020	128	4	0
1021	128	5	0
1022	128	6	0
1023	128	7	0
1024	128	8	0
1025	129	1	675
1026	129	2	720
1027	129	3	750
1028	129	4	770
1029	129	5	0
1030	129	6	0
1031	129	7	0
1032	129	8	0
1033	130	1	940
1034	130	2	991
1035	130	3	1041
1036	130	4	1102
1037	130	5	0
1038	130	6	0
1039	130	7	0
1040	130	8	0
1041	131	1	860
1042	131	2	915
1043	131	3	962
1044	131	4	1020
1045	131	5	1085
1046	131	6	0
1047	131	7	0
1048	131	8	0
1049	132	1	401
1050	132	2	416
1051	132	3	431
1052	132	4	446
1053	132	5	461
1054	132	6	484
1055	132	7	0
1056	132	8	0
1057	133	1	0
1058	133	2	0
1059	133	3	0
1060	133	4	0
1061	133	5	0
1062	133	6	0
1063	133	7	0
1064	133	8	0
1065	134	1	475
1066	134	2	495
1067	134	3	520
1068	134	4	540
1069	134	5	564
1070	134	6	585
1071	134	7	609
1072	134	8	0
1073	135	1	475
1074	135	2	495
1075	135	3	520
1076	135	4	540
1077	135	5	565
1078	135	6	585
1079	135	7	609
1080	135	8	0
1081	136	1	0
1082	136	2	0
1083	136	3	0
1084	136	4	0
1085	136	5	0
1086	136	6	0
1087	136	7	0
1088	136	8	0
1089	137	1	0
1090	137	2	0
1091	137	3	0
1092	137	4	0
1093	137	5	0
1094	137	6	0
1095	137	7	0
1096	137	8	0
1097	138	1	0
1098	138	2	0
1099	138	3	0
1100	138	4	0
1101	138	5	0
1102	138	6	0
1103	138	7	0
1104	138	8	0
1105	139	1	0
1106	139	2	0
1107	139	3	0
1108	139	4	0
1109	139	5	0
1110	139	6	0
1111	139	7	0
1112	139	8	0
1113	140	1	0
1114	140	2	0
1115	140	3	0
1116	140	4	0
1117	140	5	0
1118	140	6	0
1119	140	7	0
1120	140	8	0
1121	141	1	0
1122	141	2	0
1123	141	3	0
1124	141	4	0
1125	141	5	0
1126	141	6	0
1127	141	7	0
1128	141	8	0
1129	142	1	0
1130	142	2	0
1131	142	3	0
1132	142	4	0
1133	142	5	0
1134	142	6	0
1135	142	7	0
1136	142	8	0
1137	143	1	0
1138	143	2	0
1139	143	3	0
1140	143	4	0
1141	143	5	0
1142	143	6	0
1143	143	7	0
1144	143	8	0
1145	144	1	395
1146	144	2	405
1147	144	3	428
1148	144	4	453
1149	144	5	0
1150	144	6	0
1151	144	7	0
1152	144	8	0
1153	145	1	397
1154	145	2	410
1155	145	3	430
1156	145	4	453
1157	145	5	0
1158	145	6	0
1159	145	7	0
1160	145	8	0
1161	146	1	444
1162	146	2	461
1163	146	3	477
1164	146	4	494
1165	146	5	510
1166	146	6	537
1167	146	7	0
1168	146	8	0
1169	147	1	446
1170	147	2	465
1171	147	3	479
1172	147	4	495
1173	147	5	512
1174	147	6	537
1175	147	7	0
1176	147	8	0
1177	148	1	315
1178	148	2	335
1179	148	3	355
1180	148	4	375
1181	148	5	0
1182	148	6	0
1183	148	7	0
1184	148	8	0
1185	149	1	382
1186	149	2	0
1187	149	3	0
1188	149	4	0
1189	149	5	0
1190	149	6	0
1191	149	7	0
1192	149	8	0
1193	150	1	0
1194	150	2	0
1195	150	3	0
1196	150	4	0
1197	150	5	0
1198	150	6	0
1199	150	7	0
1200	150	8	0
1201	151	1	451
1202	151	2	501
1203	151	3	0
1204	151	4	0
1205	151	5	0
1206	151	6	0
1207	151	7	0
1208	151	8	0
1209	152	1	0
1210	152	2	0
1211	152	3	0
1212	152	4	0
1213	152	5	0
1214	152	6	0
1215	152	7	0
1216	152	8	0
1217	153	1	0
1218	153	2	0
1219	153	3	0
1220	153	4	0
1221	153	5	0
1222	153	6	0
1223	153	7	0
1224	153	8	0
1225	154	1	0
1226	154	2	0
1227	154	3	0
1228	154	4	0
1229	154	5	0
1230	154	6	0
1231	154	7	0
1232	154	8	0
1233	155	1	0
1234	155	2	0
1235	155	3	0
1236	155	4	0
1237	155	5	0
1238	155	6	0
1239	155	7	0
1240	155	8	0
1241	156	1	474
1242	156	2	520
1243	156	3	568
1244	156	4	610
1245	156	5	0
1246	156	6	0
1247	156	7	0
1248	156	8	0
1249	157	1	468
1250	157	2	502
1251	157	3	536
1252	157	4	0
1253	157	5	0
1254	157	6	0
1255	157	7	0
1256	157	8	0
1257	158	1	0
1258	158	2	0
1259	158	3	0
1260	158	4	0
1261	158	5	0
1262	158	6	0
1263	158	7	0
1264	158	8	0
1265	159	1	902
1266	159	2	965
1267	159	3	1016
1268	159	4	1067
1269	159	5	0
1270	159	6	0
1271	159	7	0
1272	159	8	0
1273	160	1	180
1274	160	2	189
1275	160	3	197
1276	160	4	205
1277	160	5	212
1278	160	6	0
1279	160	7	0
1280	160	8	0
1281	161	1	180
1282	161	2	189
1283	161	3	197
1284	161	4	205
1285	161	5	212
1286	161	6	0
1287	161	7	0
1288	161	8	0
1289	162	1	0
1290	162	2	0
1291	162	3	0
1292	162	4	0
1293	162	5	0
1294	162	6	0
1295	162	7	0
1296	162	8	0
1297	163	1	0
1298	163	2	0
1299	163	3	0
1300	163	4	0
1301	163	5	0
1302	163	6	0
1303	163	7	0
1304	163	8	0
1305	164	1	590
1306	164	2	615
1307	164	3	640
1308	164	4	0
1309	164	5	0
1310	164	6	0
1311	164	7	0
1312	164	8	0
1313	165	1	0
1314	165	2	0
1315	165	3	0
1316	165	4	0
1317	165	5	0
1318	165	6	0
1319	165	7	0
1320	165	8	0
1321	166	1	0
1322	166	2	0
1323	166	3	0
1324	166	4	0
1325	166	5	0
1326	166	6	0
1327	166	7	0
1328	166	8	0
1329	167	1	600
1330	167	2	630
1331	167	3	660
1332	167	4	0
1333	167	5	0
1334	167	6	0
1335	167	7	0
1336	167	8	0
1337	168	1	664
1338	168	2	692
1339	168	3	720
1340	168	4	0
1341	168	5	0
1342	168	6	0
1343	168	7	0
1344	168	8	0
1345	169	1	0
1346	169	2	0
1347	169	3	0
1348	169	4	0
1349	169	5	0
1350	169	6	0
1351	169	7	0
1352	169	8	0
1353	170	1	360
1354	170	2	333
1355	170	3	306
1356	170	4	279
1357	170	5	252
1358	170	6	0
1359	170	7	0
1360	170	8	0
1361	171	1	0
1362	171	2	0
1363	171	3	0
1364	171	4	0
1365	171	5	0
1366	171	6	0
1367	171	7	0
1368	171	8	0
1369	172	1	229
1370	172	2	255
1371	172	3	280
1372	172	4	305
1373	172	5	0
1374	172	6	0
1375	172	7	0
1376	172	8	0
1377	173	1	130
1378	173	2	160
1379	173	3	190
1380	173	4	230
1381	173	5	261
1382	173	6	0
1383	173	7	0
1384	173	8	0
1385	174	1	449
1386	174	2	417
1387	174	3	386
1388	174	4	354
1389	174	5	0
1390	174	6	0
1391	174	7	0
1392	174	8	0
1393	175	1	0
1394	175	2	0
1395	175	3	0
1396	175	4	0
1397	175	5	0
1398	175	6	0
1399	175	7	0
1400	175	8	0
1401	176	1	108
1402	176	2	122
1403	176	3	135
1404	176	4	0
1405	176	5	0
1406	176	6	0
1407	176	7	0
1408	176	8	0
1409	177	1	0
1410	177	2	0
1411	177	3	0
1412	177	4	0
1413	177	5	0
1414	177	6	0
1415	177	7	0
1416	177	8	0
1417	178	1	108
1418	178	2	122
1419	178	3	135
1420	178	4	0
1421	178	5	0
1422	178	6	0
1423	178	7	0
1424	178	8	0
1425	179	1	108
1426	179	2	122
1427	179	3	135
1428	179	4	0
1429	179	5	0
1430	179	6	0
1431	179	7	0
1432	179	8	0
1433	180	1	108
1434	180	2	122
1435	180	3	135
1436	180	4	0
1437	180	5	0
1438	180	6	0
1439	180	7	0
1440	180	8	0
1441	181	1	108
1442	181	2	122
1443	181	3	135
1444	181	4	0
1445	181	5	0
1446	181	6	0
1447	181	7	0
1448	181	8	0
1449	182	1	130
1450	182	2	142
1451	182	3	155
1452	182	4	0
1453	182	5	0
1454	182	6	0
1455	182	7	0
1456	182	8	0
1457	183	1	130
1458	183	2	145
1459	183	3	155
1460	183	4	0
1461	183	5	0
1462	183	6	0
1463	183	7	0
1464	183	8	0
1465	184	1	154
1466	184	2	166
1467	184	3	180
1468	184	4	0
1469	184	5	0
1470	184	6	0
1471	184	7	0
1472	184	8	0
1473	185	1	154
1474	185	2	166
1475	185	3	180
1476	185	4	0
1477	185	5	0
1478	185	6	0
1479	185	7	0
1480	185	8	0
1481	186	1	170
1482	186	2	186
1483	186	3	205
1484	186	4	0
1485	186	5	0
1486	186	6	0
1487	186	7	0
1488	186	8	0
1489	187	1	170
1490	187	2	186
1491	187	3	205
1492	187	4	0
1493	187	5	0
1494	187	6	0
1495	187	7	0
1496	187	8	0
1497	188	1	0
1498	188	2	0
1499	188	3	0
1500	188	4	0
1501	188	5	0
1502	188	6	0
1503	188	7	0
1504	188	8	0
1505	189	1	0
1506	189	2	0
1507	189	3	0
1508	189	4	0
1509	189	5	0
1510	189	6	0
1511	189	7	0
1512	189	8	0
1513	190	1	0
1514	190	2	0
1515	190	3	0
1516	190	4	0
1517	190	5	0
1518	190	6	0
1519	190	7	0
1520	190	8	0
1521	191	1	0
1522	191	2	0
1523	191	3	0
1524	191	4	0
1525	191	5	0
1526	191	6	0
1527	191	7	0
1528	191	8	0
1529	192	1	370
1530	192	2	350
1531	192	3	325
1532	192	4	290
1533	192	5	253
1534	192	6	0
1535	192	7	0
1536	192	8	0
1537	193	1	0
1538	193	2	0
1539	193	3	0
1540	193	4	0
1541	193	5	0
1542	193	6	0
1543	193	7	0
1544	193	8	0
1545	194	1	0
1546	194	2	0
1547	194	3	0
1548	194	4	0
1549	194	5	0
1550	194	6	0
1551	194	7	0
1552	194	8	0
1553	195	1	187
1554	195	2	198
1555	195	3	209
1556	195	4	220
1557	195	5	0
1558	195	6	0
1559	195	7	0
1560	195	8	0
1561	196	1	227
1562	196	2	243
1563	196	3	260
1564	196	4	275
1565	196	5	0
1566	196	6	0
1567	196	7	0
1568	196	8	0
1569	197	1	370
1570	197	2	360
1571	197	3	340
1572	197	4	320
1573	197	5	300
1574	197	6	0
1575	197	7	0
1576	197	8	0
1577	198	1	0
1578	198	2	0
1579	198	3	0
1580	198	4	0
1581	198	5	0
1582	198	6	0
1583	198	7	0
1584	198	8	0
1585	199	1	337
1586	199	2	298
1587	199	3	254
1588	199	4	0
1589	199	5	0
1590	199	6	0
1591	199	7	0
1592	199	8	0
1593	200	1	254
1594	200	2	300
1595	200	3	336
1596	200	4	0
1597	200	5	0
1598	200	6	0
1599	200	7	0
1600	200	8	0
1601	201	1	216
1602	201	2	184
1603	201	3	152
1604	201	4	0
1605	201	5	0
1606	201	6	0
1607	201	7	0
1608	201	8	0
1609	202	1	137
1610	202	2	147
1611	202	3	157
1612	202	4	167
1613	202	5	177
1614	202	6	0
1615	202	7	0
1616	202	8	0
1617	203	1	137
1618	203	2	147
1619	203	3	157
1620	203	4	167
1621	203	5	177
1622	203	6	0
1623	203	7	0
1624	203	8	0
1625	204	1	178
1626	204	2	188
1627	204	3	198
1628	204	4	208
1629	204	5	218
1630	204	6	0
1631	204	7	0
1632	204	8	0
1633	205	1	178
1634	205	2	188
1635	205	3	198
1636	205	4	208
1637	205	5	218
1638	205	6	0
1639	205	7	0
1640	205	8	0
1641	206	1	207
1642	206	2	217
1643	206	3	227
1644	206	4	237
1645	206	5	247
1646	206	6	0
1647	206	7	0
1648	206	8	0
1649	207	1	207
1650	207	2	217
1651	207	3	227
1652	207	4	237
1653	207	5	247
1654	207	6	0
1655	207	7	0
1656	207	8	0
1657	208	1	280
1658	208	2	304
1659	208	3	328
1660	208	4	0
1661	208	5	0
1662	208	6	0
1663	208	7	0
1664	208	8	0
1665	209	1	288
1666	209	2	324
1667	209	3	360
1668	209	4	0
1669	209	5	0
1670	209	6	0
1671	209	7	0
1672	209	8	0
1673	210	1	255
1674	210	2	272
1675	210	3	285
1676	210	4	300
1677	210	5	0
1678	210	6	0
1679	210	7	0
1680	210	8	0
1681	211	1	303
1682	211	2	321
1683	211	3	335
1684	211	4	351
1685	211	5	0
1686	211	6	0
1687	211	7	0
1688	211	8	0
1689	212	1	0
1690	212	2	0
1691	212	3	0
1692	212	4	0
1693	212	5	0
1694	212	6	0
1695	212	7	0
1696	212	8	0
1697	213	1	230
1698	213	2	247
1699	213	3	260
1700	213	4	274
1701	213	5	0
1702	213	6	0
1703	213	7	0
1704	213	8	0
1705	214	1	220
1706	214	2	260
1707	214	3	305
1708	214	4	360
1709	214	5	0
1710	214	6	0
1711	214	7	0
1712	214	8	0
1713	215	1	220
1714	215	2	260
1715	215	3	305
1716	215	4	360
1717	215	5	0
1718	215	6	0
1719	215	7	0
1720	215	8	0
1721	216	1	220
1722	216	2	260
1723	216	3	305
1724	216	4	360
1725	216	5	0
1726	216	6	0
1727	216	7	0
1728	216	8	0
1729	217	1	220
1730	217	2	305
1731	217	3	360
1732	217	4	0
1733	217	5	0
1734	217	6	0
1735	217	7	0
1736	217	8	0
1737	218	1	0
1738	218	2	0
1739	218	3	0
1740	218	4	0
1741	218	5	0
1742	218	6	0
1743	218	7	0
1744	218	8	0
1745	219	1	0
1746	219	2	0
1747	219	3	0
1748	219	4	0
1749	219	5	0
1750	219	6	0
1751	219	7	0
1752	219	8	0
1753	220	1	350
1754	220	2	366
1755	220	3	381
1756	220	4	0
1757	220	5	0
1758	220	6	0
1759	220	7	0
1760	220	8	0
1761	221	1	113
1762	221	2	123
1763	221	3	133
1764	221	4	143
1765	221	5	0
1766	221	6	0
1767	221	7	0
1768	221	8	0
1769	222	1	140
1770	222	2	150
1771	222	3	160
1772	222	4	170
1773	222	5	177
1774	222	6	0
1775	222	7	0
1776	222	8	0
1777	223	1	140
1778	223	2	150
1779	223	3	160
1780	223	4	170
1781	223	5	177
1782	223	6	0
1783	223	7	0
1784	223	8	0
1785	224	1	178
1786	224	2	198
1787	224	3	218
1788	224	4	0
1789	224	5	0
1790	224	6	0
1791	224	7	0
1792	224	8	0
1793	225	1	178
1794	225	2	186
1795	225	3	194
1796	225	4	202
1797	225	5	210
1798	225	6	218
1799	225	7	0
1800	225	8	0
1801	226	1	178
1802	226	2	186
1803	226	3	194
1804	226	4	202
1805	226	5	210
1806	226	6	218
1807	226	7	0
1808	226	8	0
1809	227	1	226
1810	227	2	236
1811	227	3	246
1812	227	4	256
1813	227	5	266
1814	227	6	0
1815	227	7	0
1816	227	8	0
1817	228	1	226
1818	228	2	236
1819	228	3	246
1820	228	4	256
1821	228	5	266
1822	228	6	0
1823	228	7	0
1824	228	8	0
1825	229	1	281
1826	229	2	294
1827	229	3	306
1828	229	4	318
1829	229	5	328
1830	229	6	0
1831	229	7	0
1832	229	8	0
1833	230	1	0
1834	230	2	0
1835	230	3	0
1836	230	4	0
1837	230	5	0
1838	230	6	0
1839	230	7	0
1840	230	8	0
1841	231	1	0
1842	231	2	0
1843	231	3	0
1844	231	4	0
1845	231	5	0
1846	231	6	0
1847	231	7	0
1848	231	8	0
1849	232	1	0
1850	232	2	0
1851	232	3	0
1852	232	4	0
1853	232	5	0
1854	232	6	0
1855	232	7	0
1856	232	8	0
1857	233	1	0
1858	233	2	0
1859	233	3	0
1860	233	4	0
1861	233	5	0
1862	233	6	0
1863	233	7	0
1864	233	8	0
1865	234	1	0
1866	234	2	0
1867	234	3	0
1868	234	4	0
1869	234	5	0
1870	234	6	0
1871	234	7	0
1872	234	8	0
1873	235	1	0
1874	235	2	0
1875	235	3	0
1876	235	4	0
1877	235	5	0
1878	235	6	0
1879	235	7	0
1880	235	8	0
1881	236	1	0
1882	236	2	0
1883	236	3	0
1884	236	4	0
1885	236	5	0
1886	236	6	0
1887	236	7	0
1888	236	8	0
1889	237	1	295
1890	237	2	345
1891	237	3	394
1892	237	4	0
1893	237	5	0
1894	237	6	0
1895	237	7	0
1896	237	8	0
1897	238	1	286
1898	238	2	333
1899	238	3	381
1900	238	4	0
1901	238	5	0
1902	238	6	0
1903	238	7	0
1904	238	8	0
1905	240	1	0
1906	240	2	0
1907	240	3	0
1908	240	4	0
1909	240	5	0
1910	240	6	0
1911	240	7	0
1912	240	8	0
1913	241	1	0
1914	241	2	0
1915	241	3	0
1916	241	4	0
1917	241	5	0
1918	241	6	0
1919	241	7	0
1920	241	8	0
1921	242	1	122
1922	242	2	135
1923	242	3	147
1924	242	4	0
1925	242	5	0
1926	242	6	0
1927	242	7	0
1928	242	8	0
1929	243	1	370
1930	243	2	393
1931	243	3	422
1932	243	4	450
1933	243	5	0
1934	243	6	0
1935	243	7	0
1936	243	8	0
1937	244	1	0
1938	244	2	0
1939	244	3	0
1940	244	4	0
1941	244	5	0
1942	244	6	0
1943	244	7	0
1944	244	8	0
1945	245	1	0
1946	245	2	0
1947	245	3	0
1948	245	4	0
1949	245	5	0
1950	245	6	0
1951	245	7	0
1952	245	8	0
1953	246	1	279
1954	246	2	254
1955	246	3	222
1956	246	4	0
1957	246	5	0
1958	246	6	0
1959	246	7	0
1960	246	8	0
1961	247	1	254
1962	247	2	342
1963	247	3	0
1964	247	4	0
1965	247	5	0
1966	247	6	0
1967	247	7	0
1968	247	8	0
1969	248	1	600
1970	248	2	675
1971	248	3	715
1972	248	4	0
1973	248	5	0
1974	248	6	0
1975	248	7	0
1976	248	8	0
1977	249	1	600
1978	249	2	675
1979	249	3	715
1980	249	4	0
1981	249	5	0
1982	249	6	0
1983	249	7	0
1984	249	8	0
1985	250	1	248
1986	250	2	292
1987	250	3	0
1988	250	4	0
1989	250	5	0
1990	250	6	0
1991	250	7	0
1992	250	8	0
1993	251	1	0
1994	251	2	0
1995	251	3	0
1996	251	4	0
1997	251	5	0
1998	251	6	0
1999	251	7	0
2000	251	8	0
2001	252	1	160
2002	252	2	164
2003	252	3	168
2004	252	4	173
2005	252	5	177
2006	252	6	0
2007	252	7	0
2008	252	8	0
2009	253	1	160
2010	253	2	164
2011	253	3	168
2012	253	4	173
2013	253	5	177
2014	253	6	0
2015	253	7	0
2016	253	8	0
2017	254	1	184
2018	254	2	192
2019	254	3	202
2020	254	4	209
2021	254	5	216
2022	254	6	0
2023	254	7	0
2024	254	8	0
2025	255	1	184
2026	255	2	192
2027	255	3	202
2028	255	4	209
2029	255	5	216
2030	255	6	0
2031	255	7	0
2032	255	8	0
2033	256	1	220
2034	256	2	230
2035	256	3	240
2036	256	4	251
2037	256	5	262
2038	256	6	271
2039	256	7	0
2040	256	8	0
2041	257	1	220
2042	257	2	230
2043	257	3	240
2044	257	4	251
2045	257	5	262
2046	257	6	271
2047	257	7	0
2048	257	8	0
2049	258	1	276
2050	258	2	291
2051	258	3	306
2052	258	4	321
2053	258	5	336
2054	258	6	0
2055	258	7	0
2056	258	8	0
2057	259	1	220
2058	259	2	280
2059	259	3	328
2060	259	4	0
2061	259	5	0
2062	259	6	0
2063	259	7	0
2064	259	8	0
2065	260	1	220
2066	260	2	280
2067	260	3	328
2068	260	4	0
2069	260	5	0
2070	260	6	0
2071	260	7	0
2072	260	8	0
2073	261	1	0
2074	261	2	0
2075	261	3	0
2076	261	4	0
2077	261	5	0
2078	261	6	0
2079	261	7	0
2080	261	8	0
2081	262	1	0
2082	262	2	0
2083	262	3	0
2084	262	4	0
2085	262	5	0
2086	262	6	0
2087	262	7	0
2088	262	8	0
2089	263	1	0
2090	263	2	0
2091	263	3	0
2092	263	4	0
2093	263	5	0
2094	263	6	0
2095	263	7	0
2096	263	8	0
2097	264	1	0
2098	264	2	0
2099	264	3	0
2100	264	4	0
2101	264	5	0
2102	264	6	0
2103	264	7	0
2104	264	8	0
2105	265	1	0
2106	265	2	0
2107	265	3	0
2108	265	4	0
2109	265	5	0
2110	265	6	0
2111	265	7	0
2112	265	8	0
2113	266	1	0
2114	266	2	0
2115	266	3	0
2116	266	4	0
2117	266	5	0
2118	266	6	0
2119	266	7	0
2120	266	8	0
2121	267	1	0
2122	267	2	0
2123	267	3	0
2124	267	4	0
2125	267	5	0
2126	267	6	0
2127	267	7	0
2128	267	8	0
2129	268	1	0
2130	268	2	0
2131	268	3	0
2132	268	4	0
2133	268	5	0
2134	268	6	0
2135	268	7	0
2136	268	8	0
2137	269	1	0
2138	269	2	0
2139	269	3	0
2140	269	4	0
2141	269	5	0
2142	269	6	0
2143	269	7	0
2144	269	8	0
2145	270	1	0
2146	270	2	0
2147	270	3	0
2148	270	4	0
2149	270	5	0
2150	270	6	0
2151	270	7	0
2152	270	8	0
2153	271	1	0
2154	271	2	0
2155	271	3	0
2156	271	4	0
2157	271	5	0
2158	271	6	0
2159	271	7	0
2160	271	8	0
2161	272	1	0
2162	272	2	0
2163	272	3	0
2164	272	4	0
2165	272	5	0
2166	272	6	0
2167	272	7	0
2168	272	8	0
2169	273	1	0
2170	273	2	0
2171	273	3	0
2172	273	4	0
2173	273	5	0
2174	273	6	0
2175	273	7	0
2176	273	8	0
2177	274	1	0
2178	274	2	0
2179	274	3	0
2180	274	4	0
2181	274	5	0
2182	274	6	0
2183	274	7	0
2184	274	8	0
2185	275	1	0
2186	275	2	0
2187	275	3	0
2188	275	4	0
2189	275	5	0
2190	275	6	0
2191	275	7	0
2192	275	8	0
2193	276	1	0
2194	276	2	0
2195	276	3	0
2196	276	4	0
2197	276	5	0
2198	276	6	0
2199	276	7	0
2200	276	8	0
2201	277	1	0
2202	277	2	0
2203	277	3	0
2204	277	4	0
2205	277	5	0
2206	277	6	0
2207	277	7	0
2208	277	8	0
2209	278	1	0
2210	278	2	0
2211	278	3	0
2212	278	4	0
2213	278	5	0
2214	278	6	0
2215	278	7	0
2216	278	8	0
2217	279	1	0
2218	279	2	0
2219	279	3	0
2220	279	4	0
2221	279	5	0
2222	279	6	0
2223	279	7	0
2224	279	8	0
2225	280	1	0
2226	280	2	0
2227	280	3	0
2228	280	4	0
2229	280	5	0
2230	280	6	0
2231	280	7	0
2232	280	8	0
2233	281	1	0
2234	281	2	0
2235	281	3	0
2236	281	4	0
2237	281	5	0
2238	281	6	0
2239	281	7	0
2240	281	8	0
2241	282	1	0
2242	282	2	0
2243	282	3	0
2244	282	4	0
2245	282	5	0
2246	282	6	0
2247	282	7	0
2248	282	8	0
2249	283	1	0
2250	283	2	0
2251	283	3	0
2252	283	4	0
2253	283	5	0
2254	283	6	0
2255	283	7	0
2256	283	8	0
2257	284	1	0
2258	284	2	0
2259	284	3	0
2260	284	4	0
2261	284	5	0
2262	284	6	0
2263	284	7	0
2264	284	8	0
2265	285	1	0
2266	285	2	0
2267	285	3	0
2268	285	4	0
2269	285	5	0
2270	285	6	0
2271	285	7	0
2272	285	8	0
2273	286	1	0
2274	286	2	0
2275	286	3	0
2276	286	4	0
2277	286	5	0
2278	286	6	0
2279	286	7	0
2280	286	8	0
2281	287	1	0
2282	287	2	0
2283	287	3	0
2284	287	4	0
2285	287	5	0
2286	287	6	0
2287	287	7	0
2288	287	8	0
2289	288	1	0
2290	288	2	0
2291	288	3	0
2292	288	4	0
2293	288	5	0
2294	288	6	0
2295	288	7	0
2296	288	8	0
2297	289	1	0
2298	289	2	0
2299	289	3	0
2300	289	4	0
2301	289	5	0
2302	289	6	0
2303	289	7	0
2304	289	8	0
2305	290	1	318
2306	290	2	340
2307	290	3	360
2308	290	4	376
2309	290	5	383
2310	290	6	0
2311	290	7	0
2312	290	8	0
2313	291	1	458
2314	291	2	444
2315	291	3	430
2316	291	4	415
2317	291	5	401
2318	291	6	0
2319	291	7	0
2320	291	8	0
2321	292	1	400
2322	292	2	390
2323	292	3	377
2324	292	4	0
2325	292	5	0
2326	292	6	0
2327	292	7	0
2328	292	8	0
2329	293	1	0
2330	293	2	0
2331	293	3	0
2332	293	4	0
2333	293	5	0
2334	293	6	0
2335	293	7	0
2336	293	8	0
2337	294	1	448
2338	294	2	507
2339	294	3	566
2340	294	4	0
2341	294	5	0
2342	294	6	0
2343	294	7	0
2344	294	8	0
2345	295	1	522
2346	295	2	544
2347	295	3	567
2348	295	4	591
2349	295	5	0
2350	295	6	0
2351	295	7	0
2352	295	8	0
2353	296	1	377
2354	296	2	410
2355	296	3	444
2356	296	4	0
2357	296	5	0
2358	296	6	0
2359	296	7	0
2360	296	8	0
2361	297	1	377
2362	297	2	410
2363	297	3	444
2364	297	4	0
2365	297	5	0
2366	297	6	0
2367	297	7	0
2368	297	8	0
2369	298	1	433
2370	298	2	465
2371	298	3	495
2372	298	4	527
2373	298	5	0
2374	298	6	0
2375	298	7	0
2376	298	8	0
2377	299	1	417
2378	299	2	445
2379	299	3	470
2380	299	4	495
2381	299	5	0
2382	299	6	0
2383	299	7	0
2384	299	8	0
2385	300	1	406
2386	300	2	495
2387	300	3	0
2388	300	4	0
2389	300	5	0
2390	300	6	0
2391	300	7	0
2392	300	8	0
2393	301	1	0
2394	301	2	0
2395	301	3	0
2396	301	4	0
2397	301	5	0
2398	301	6	0
2399	301	7	0
2400	301	8	0
2401	302	1	0
2402	302	2	0
2403	302	3	0
2404	302	4	0
2405	302	5	0
2406	302	6	0
2407	302	7	0
2408	302	8	0
2409	303	1	0
2410	303	2	0
2411	303	3	0
2412	303	4	0
2413	303	5	0
2414	303	6	0
2415	303	7	0
2416	303	8	0
2417	305	1	0
2418	305	2	0
2419	305	3	0
2420	305	4	0
2421	305	5	0
2422	305	6	0
2423	305	7	0
2424	305	8	0
2425	306	1	0
2426	306	2	0
2427	306	3	0
2428	306	4	0
2429	306	5	0
2430	306	6	0
2431	306	7	0
2432	306	8	0
2433	307	1	130
2434	307	2	158
2435	307	3	186
2436	307	4	0
2437	307	5	0
2438	307	6	0
2439	307	7	0
2440	307	8	0
2441	308	1	356
2442	308	2	410
2443	308	3	454
2444	308	4	0
2445	308	5	0
2446	308	6	0
2447	308	7	0
2448	308	8	0
2449	309	1	356
2450	309	2	425
2451	309	3	463
2452	309	4	0
2453	309	5	0
2454	309	6	0
2455	309	7	0
2456	309	8	0
2457	310	1	438
2458	310	2	520
2459	310	3	570
2460	310	4	0
2461	310	5	0
2462	310	6	0
2463	310	7	0
2464	310	8	0
2465	311	1	590
2466	311	2	674
2467	311	3	730
2468	311	4	0
2469	311	5	0
2470	311	6	0
2471	311	7	0
2472	311	8	0
2473	312	1	150
2474	312	2	200
2475	312	3	250
2476	312	4	300
2477	312	5	344
2478	312	6	0
2479	312	7	0
2480	312	8	0
2481	313	1	0
2482	313	2	0
2483	313	3	0
2484	313	4	0
2485	313	5	0
2486	313	6	0
2487	313	7	0
2488	313	8	0
2489	314	1	150
2490	314	2	200
2491	314	3	250
2492	314	4	300
2493	314	5	344
2494	314	6	0
2495	314	7	0
2496	314	8	0
2497	315	1	0
2498	315	2	0
2499	315	3	0
2500	315	4	0
2501	315	5	0
2502	315	6	0
2503	315	7	0
2504	315	8	0
2505	316	1	150
2506	316	2	200
2507	316	3	250
2508	316	4	300
2509	316	5	344
2510	316	6	0
2511	316	7	0
2512	316	8	0
2513	317	1	150
2514	317	2	200
2515	317	3	250
2516	317	4	300
2517	317	5	344
2518	317	6	0
2519	317	7	0
2520	317	8	0
2521	318	1	0
2522	318	2	0
2523	318	3	0
2524	318	4	0
2525	318	5	0
2526	318	6	0
2527	318	7	0
2528	318	8	0
2529	319	1	0
2530	319	2	0
2531	319	3	0
2532	319	4	0
2533	319	5	0
2534	319	6	0
2535	319	7	0
2536	319	8	0
2537	320	1	0
2538	320	2	0
2539	320	3	0
2540	320	4	0
2541	320	5	0
2542	320	6	0
2543	320	7	0
2544	320	8	0
2545	321	1	0
2546	321	2	0
2547	321	3	0
2548	321	4	0
2549	321	5	0
2550	321	6	0
2551	321	7	0
2552	321	8	0
2553	322	1	0
2554	322	2	0
2555	322	3	0
2556	322	4	0
2557	322	5	0
2558	322	6	0
2559	322	7	0
2560	322	8	0
2561	323	1	620
2562	323	2	675
2563	323	3	725
2564	323	4	0
2565	323	5	0
2566	323	6	0
2567	323	7	0
2568	323	8	0
2569	324	1	155
2570	324	2	200
2571	324	3	255
2572	324	4	300
2573	324	5	355
2574	324	6	409
2575	324	7	0
2576	324	8	0
2577	325	1	165
2578	325	2	160
2579	325	3	155
2580	325	4	150
2581	325	5	145
2582	325	6	140
2583	325	7	0
2584	325	8	0
2585	326	1	0
2586	326	2	0
2587	326	3	0
2588	326	4	0
2589	326	5	0
2590	326	6	0
2591	326	7	0
2592	326	8	0
2593	327	1	110
2594	327	2	130
2595	327	3	150
2596	327	4	170
2597	327	5	190
2598	327	6	201
2599	327	7	0
2600	327	8	0
2601	328	1	184
2602	328	2	224
2603	328	3	264
2604	328	4	304
2605	328	5	0
2606	328	6	0
2607	328	7	0
2608	328	8	0
2609	329	1	0
2610	329	2	0
2611	329	3	0
2612	329	4	0
2613	329	5	0
2614	329	6	0
2615	329	7	0
2616	329	8	0
2617	330	1	0
2618	330	2	0
2619	330	3	0
2620	330	4	0
2621	330	5	0
2622	330	6	0
2623	330	7	0
2624	330	8	0
2625	331	1	0
2626	331	2	0
2627	331	3	0
2628	331	4	0
2629	331	5	0
2630	331	6	0
2631	331	7	0
2632	331	8	0
2633	332	1	450
2634	332	2	484
2635	332	3	0
2636	332	4	0
2637	332	5	0
2638	332	6	0
2639	332	7	0
2640	332	8	0
2641	333	1	210
2642	333	2	230
2643	333	3	260
2644	333	4	292
2645	333	5	0
2646	333	6	0
2647	333	7	0
2648	333	8	0
2649	334	1	0
2650	334	2	0
2651	334	3	0
2652	334	4	0
2653	334	5	0
2654	334	6	0
2655	334	7	0
2656	334	8	0
2657	335	1	320
2658	335	2	339
2659	335	3	359
2660	335	4	378
2661	335	5	0
2662	335	6	0
2663	335	7	0
2664	335	8	0
2665	336	1	348
2666	336	2	391
2667	336	3	435
2668	336	4	0
2669	336	5	0
2670	336	6	0
2671	336	7	0
2672	336	8	0
2673	337	1	348
2674	337	2	391
2675	337	3	435
2676	337	4	0
2677	337	5	0
2678	337	6	0
2679	337	7	0
2680	337	8	0
2681	338	1	459
2682	338	2	484
2683	338	3	510
2684	338	4	0
2685	338	5	0
2686	338	6	0
2687	338	7	0
2688	338	8	0
2689	339	1	459
2690	339	2	489
2691	339	3	510
2692	339	4	0
2693	339	5	0
2694	339	6	0
2695	339	7	0
2696	339	8	0
2697	340	1	475
2698	340	2	502
2699	340	3	528
2700	340	4	555
2701	340	5	0
2702	340	6	0
2703	340	7	0
2704	340	8	0
2705	341	1	475
2706	341	2	502
2707	341	3	528
2708	341	4	555
2709	341	5	0
2710	341	6	0
2711	341	7	0
2712	341	8	0
2713	342	1	0
2714	342	2	0
2715	342	3	0
2716	342	4	0
2717	342	5	0
2718	342	6	0
2719	342	7	0
2720	342	8	0
2721	343	1	490
2722	343	2	530
2723	343	3	0
2724	343	4	0
2725	343	5	0
2726	343	6	0
2727	343	7	0
2728	343	8	0
2729	344	1	520
2730	344	2	580
2731	344	3	0
2732	344	4	0
2733	344	5	0
2734	344	6	0
2735	344	7	0
2736	344	8	0
2737	345	1	282
2738	345	2	298
2739	345	3	314
2740	345	4	0
2741	345	5	0
2742	345	6	0
2743	345	7	0
2744	345	8	0
2745	346	1	269
2746	346	2	298
2747	346	3	314
2748	346	4	0
2749	346	5	0
2750	346	6	0
2751	346	7	0
2752	346	8	0
2753	347	1	247
2754	347	2	259
2755	347	3	273
2756	347	4	288
2757	347	5	0
2758	347	6	0
2759	347	7	0
2760	347	8	0
2761	348	1	249
2762	348	2	259
2763	348	3	273
2764	348	4	288
2765	348	5	0
2766	348	6	0
2767	348	7	0
2768	348	8	0
2769	349	1	287
2770	349	2	319
2771	349	3	337
2772	349	4	0
2773	349	5	0
2774	349	6	0
2775	349	7	0
2776	349	8	0
2777	350	1	287
2778	350	2	303
2779	350	3	319
2780	350	4	337
2781	350	5	0
2782	350	6	0
2783	350	7	0
2784	350	8	0
2785	351	1	313
2786	351	2	336
2787	351	3	360
2788	351	4	0
2789	351	5	0
2790	351	6	0
2791	351	7	0
2792	351	8	0
2793	352	1	313
2794	352	2	328
2795	352	3	343
2796	352	4	360
2797	352	5	0
2798	352	6	0
2799	352	7	0
2800	352	8	0
2801	353	1	0
2802	353	2	0
2803	353	3	0
2804	353	4	0
2805	353	5	0
2806	353	6	0
2807	353	7	0
2808	353	8	0
2809	354	1	203
2810	354	2	213
2811	354	3	227
2812	354	4	240
2813	354	5	0
2814	354	6	0
2815	354	7	0
2816	354	8	0
2817	355	1	0
2818	355	2	0
2819	355	3	0
2820	355	4	0
2821	355	5	0
2822	355	6	0
2823	355	7	0
2824	355	8	0
2825	356	1	470
2826	356	2	485
2827	356	3	500
2828	356	4	515
2829	356	5	530
2830	356	6	546
2831	356	7	561
2832	356	8	576
2833	357	1	382
2834	357	2	0
2835	357	3	0
2836	357	4	0
2837	357	5	0
2838	357	6	0
2839	357	7	0
2840	357	8	0
2841	358	1	0
2842	358	2	0
2843	358	3	0
2844	358	4	0
2845	358	5	0
2846	358	6	0
2847	358	7	0
2848	358	8	0
2849	359	1	0
2850	359	2	0
2851	359	3	0
2852	359	4	0
2853	359	5	0
2854	359	6	0
2855	359	7	0
2856	359	8	0
2857	360	1	0
2858	360	2	0
2859	360	3	0
2860	360	4	0
2861	360	5	0
2862	360	6	0
2863	360	7	0
2864	360	8	0
2865	361	1	420.1
2866	361	2	404.3
2867	361	3	0
2868	361	4	0
2869	361	5	0
2870	361	6	0
2871	361	7	0
2872	361	8	0
2873	362	1	0
2874	362	2	0
2875	362	3	0
2876	362	4	0
2877	362	5	0
2878	362	6	0
2879	362	7	0
2880	362	8	0
2881	363	1	656
2882	363	2	632.8
2883	363	3	590
2884	363	4	0
2885	363	5	0
2886	363	6	0
2887	363	7	0
2888	363	8	0
2889	364	1	1200
2890	364	2	1614
2891	364	3	0
2892	364	4	0
2893	364	5	0
2894	364	6	0
2895	364	7	0
2896	364	8	0
2897	365	1	0
2898	365	2	0
2899	365	3	0
2900	365	4	0
2901	365	5	0
2902	365	6	0
2903	365	7	0
2904	365	8	0
2905	366	1	0
2906	366	2	0
2907	366	3	0
2908	366	4	0
2909	366	5	0
2910	366	6	0
2911	366	7	0
2912	366	8	0
2913	367	1	0
2914	367	2	0
2915	367	3	0
2916	367	4	0
2917	367	5	0
2918	367	6	0
2919	367	7	0
2920	367	8	0
2921	368	1	0
2922	368	2	0
2923	368	3	0
2924	368	4	0
2925	368	5	0
2926	368	6	0
2927	368	7	0
2928	368	8	0
2929	369	1	0
2930	369	2	0
2931	369	3	0
2932	369	4	0
2933	369	5	0
2934	369	6	0
2935	369	7	0
2936	369	8	0
2937	370	1	0
2938	370	2	0
2939	370	3	0
2940	370	4	0
2941	370	5	0
2942	370	6	0
2943	370	7	0
2944	370	8	0
2945	371	1	0
2946	371	2	0
2947	371	3	0
2948	371	4	0
2949	371	5	0
2950	371	6	0
2951	371	7	0
2952	371	8	0
2953	372	1	0
2954	372	2	0
2955	372	3	0
2956	372	4	0
2957	372	5	0
2958	372	6	0
2959	372	7	0
2960	372	8	0
2961	373	1	0
2962	373	2	0
2963	373	3	0
2964	373	4	0
2965	373	5	0
2966	373	6	0
2967	373	7	0
2968	373	8	0
2969	374	1	0
2970	374	2	0
2971	374	3	0
2972	374	4	0
2973	374	5	0
2974	374	6	0
2975	374	7	0
2976	374	8	0
2977	375	1	0
2978	375	2	0
2979	375	3	0
2980	375	4	0
2981	375	5	0
2982	375	6	0
2983	375	7	0
2984	375	8	0
2985	376	1	0
2986	376	2	0
2987	376	3	0
2988	376	4	0
2989	376	5	0
2990	376	6	0
2991	376	7	0
2992	376	8	0
2993	377	1	0
2994	377	2	0
2995	377	3	0
2996	377	4	0
2997	377	5	0
2998	377	6	0
2999	377	7	0
3000	377	8	0
3001	378	1	0
3002	378	2	0
3003	378	3	0
3004	378	4	0
3005	378	5	0
3006	378	6	0
3007	378	7	0
3008	378	8	0
3009	379	1	0
3010	379	2	0
3011	379	3	0
3012	379	4	0
3013	379	5	0
3014	379	6	0
3015	379	7	0
3016	379	8	0
3017	380	1	0
3018	380	2	0
3019	380	3	0
3020	380	4	0
3021	380	5	0
3022	380	6	0
3023	380	7	0
3024	380	8	0
3025	381	1	0
3026	381	2	0
3027	381	3	0
3028	381	4	0
3029	381	5	0
3030	381	6	0
3031	381	7	0
3032	381	8	0
3033	382	1	0
3034	382	2	0
3035	382	3	0
3036	382	4	0
3037	382	5	0
3038	382	6	0
3039	382	7	0
3040	382	8	0
3041	383	1	0
3042	383	2	0
3043	383	3	0
3044	383	4	0
3045	383	5	0
3046	383	6	0
3047	383	7	0
3048	383	8	0
3049	384	1	0
3050	384	2	0
3051	384	3	0
3052	384	4	0
3053	384	5	0
3054	384	6	0
3055	384	7	0
3056	384	8	0
3057	385	1	0
3058	385	2	0
3059	385	3	0
3060	385	4	0
3061	385	5	0
3062	385	6	0
3063	385	7	0
3064	385	8	0
3065	386	1	280
3066	386	2	295
3067	386	3	311
3068	386	4	0
3069	386	5	0
3070	386	6	0
3071	386	7	0
3072	386	8	0
\.


--
-- Data for Name: pump_eff_iso; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.pump_eff_iso (id, pump_id, sequence_order, eff_iso_value) FROM stdin;
1	1	1	60
2	1	2	65
3	1	3	70
4	1	4	74
5	1	5	77
6	1	6	80
7	1	7	0
8	1	8	0
9	2	1	60
10	2	2	65
11	2	3	70
12	2	4	74
13	2	5	77
14	2	6	80
15	2	7	82
16	2	8	0
17	3	1	40
18	3	2	50
19	3	3	55
20	3	4	60
21	3	5	65
22	3	6	0
23	3	7	0
24	3	8	0
25	4	1	55
26	4	2	60
27	4	3	65
28	4	4	70
29	4	5	75
30	4	6	77
31	4	7	78
32	4	8	0
33	5	1	50
34	5	2	60
35	5	3	65
36	5	4	70
37	5	5	73
38	5	6	76
39	5	7	78
40	5	8	80
41	6	1	60
42	6	2	70
43	6	3	75
44	6	4	78
45	6	5	80
46	6	6	81
47	6	7	0
48	6	8	0
49	7	1	50
50	7	2	55
51	7	3	60
52	7	4	65
53	7	5	70
54	7	6	72
55	7	7	74
56	7	8	76
57	8	1	0
58	8	2	0
59	8	3	0
60	8	4	0
61	8	5	0
62	8	6	0
63	8	7	0
64	8	8	0
65	9	1	30
66	9	2	40
67	9	3	50
68	9	4	60
69	9	5	70
70	9	6	0
71	9	7	0
72	9	8	0
73	10	1	50
74	10	2	60
75	10	3	70
76	10	4	75
77	10	5	80
78	10	6	84
79	10	7	86
80	10	8	0
81	11	1	60
82	11	2	65
83	11	3	70
84	11	4	75
85	11	5	0
86	11	6	0
87	11	7	0
88	11	8	0
89	12	1	40
90	12	2	50
91	12	3	60
92	12	4	70
93	12	5	80
94	12	6	85
95	12	7	86
96	12	8	0
97	13	1	40
98	13	2	50
99	13	3	60
100	13	4	70
101	13	5	80
102	13	6	84
103	13	7	0
104	13	8	0
105	14	1	30
106	14	2	50
107	14	3	60
108	14	4	70
109	14	5	80
110	14	6	83
111	14	7	0
112	14	8	0
113	15	1	40
114	15	2	60
115	15	3	70
116	15	4	70
117	15	5	75
118	15	6	80
119	15	7	0
120	15	8	0
121	16	1	50
122	16	2	60
123	16	3	70
124	16	4	75
125	16	5	77
126	16	6	80
127	16	7	83
128	16	8	0
129	17	1	50
130	17	2	60
131	17	3	70
132	17	4	75
133	17	5	78
134	17	6	80
135	17	7	82
136	17	8	84
137	18	1	50
138	18	2	60
139	18	3	70
140	18	4	75
141	18	5	78
142	18	6	80
143	18	7	81
144	18	8	82
145	19	1	74
146	19	2	76
147	19	3	78
148	19	4	0
149	19	5	0
150	19	6	0
151	19	7	0
152	19	8	0
153	20	1	40
154	20	2	50
155	20	3	55
156	20	4	61
157	20	5	65
158	20	6	67
159	20	7	0
160	20	8	0
161	21	1	40
162	21	2	50
163	21	3	55
164	21	4	60
165	21	5	64
166	21	6	67
167	21	7	0
168	21	8	0
169	22	1	60
170	22	2	65
171	22	3	70
172	22	4	75
173	22	5	78
174	22	6	80
175	22	7	81
176	22	8	0
177	23	1	60
178	23	2	65
179	23	3	70
180	23	4	75
181	23	5	78
182	23	6	80
183	23	7	81
184	23	8	82
185	24	1	45
186	24	2	56
187	24	3	68
188	24	4	75
189	24	5	83
190	24	6	87
191	24	7	0
192	24	8	0
193	25	1	40
194	25	2	50
195	25	3	60
196	25	4	67
197	25	5	72
198	25	6	76
199	25	7	0
200	25	8	0
201	26	1	30
202	26	2	40
203	26	3	50
204	26	4	60
205	26	5	70
206	26	6	74
207	26	7	0
208	26	8	0
209	27	1	65
210	27	2	70
211	27	3	75
212	27	4	80
213	27	5	82.5
214	27	6	85
215	27	7	86
216	27	8	0
217	28	1	60
218	28	2	70
219	28	3	75
220	28	4	78
221	28	5	80
222	28	6	82
223	28	7	83
224	28	8	0
225	29	1	60
226	29	2	65
227	29	3	70
228	29	4	75
229	29	5	77
230	29	6	78
231	29	7	0
232	29	8	0
233	30	1	48
234	30	2	65
235	30	3	76
236	30	4	84
237	30	5	86
238	30	6	0
239	30	7	0
240	30	8	0
241	31	1	30
242	31	2	50
243	31	3	70
244	31	4	80
245	31	5	85
246	31	6	0
247	31	7	0
248	31	8	0
249	32	1	0
250	32	2	0
251	32	3	0
252	32	4	0
253	32	5	0
254	32	6	0
255	32	7	0
256	32	8	0
257	33	1	30
258	33	2	50
259	33	3	60
260	33	4	70
261	33	5	75
262	33	6	0
263	33	7	0
264	33	8	0
265	34	1	70
266	34	2	74
267	34	3	78
268	34	4	82
269	34	5	84
270	34	6	86
271	34	7	87
272	34	8	0
273	35	1	70
274	35	2	74
275	35	3	78
276	35	4	82
277	35	5	84
278	35	6	86
279	35	7	87
280	35	8	0
281	36	1	70
282	36	2	73
283	36	3	77
284	36	4	80
285	36	5	81
286	36	6	0
287	36	7	0
288	36	8	0
289	37	1	40
290	37	2	50
291	37	3	60
292	37	4	70
293	37	5	75
294	37	6	0
295	37	7	0
296	37	8	0
297	38	1	50
298	38	2	60
299	38	3	65
300	38	4	70
301	38	5	72
302	38	6	75
303	38	7	78
304	38	8	0
305	39	1	75
306	39	2	78
307	39	3	0
308	39	4	0
309	39	5	0
310	39	6	0
311	39	7	0
312	39	8	0
313	40	1	40
314	40	2	50
315	40	3	60
316	40	4	70
317	40	5	75
318	40	6	80
319	40	7	0
320	40	8	0
321	41	1	0
322	41	2	0
323	41	3	0
324	41	4	0
325	41	5	0
326	41	6	0
327	41	7	0
328	41	8	0
329	42	1	60
330	42	2	75
331	42	3	80
332	42	4	83
333	42	5	85
334	42	6	87
335	42	7	88
336	42	8	0
337	43	1	60
338	43	2	75
339	43	3	80
340	43	4	83
341	43	5	85
342	43	6	87
343	43	7	89
344	43	8	0
345	44	1	60
346	44	2	70
347	44	3	75
348	44	4	75
349	44	5	79
350	44	6	81
351	44	7	0
352	44	8	0
353	45	1	50
354	45	2	60
355	45	3	70
356	45	4	74
357	45	5	77
358	45	6	80
359	45	7	83
360	45	8	0
361	46	1	65
362	46	2	70
363	46	3	75
364	46	4	80
365	46	5	83
366	46	6	85
367	46	7	0
368	46	8	0
369	47	1	60
370	47	2	70
371	47	3	75
372	47	4	80
373	47	5	85
374	47	6	87
375	47	7	0
376	47	8	0
377	48	1	60
378	48	2	70
379	48	3	75
380	48	4	80
381	48	5	83
382	48	6	85
383	48	7	87
384	48	8	0
385	49	1	60
386	49	2	75
387	49	3	80
388	49	4	83
389	49	5	85
390	49	6	87
391	49	7	88
392	49	8	0
393	50	1	50
394	50	2	60
395	50	3	75
396	50	4	80
397	50	5	83
398	50	6	85
399	50	7	87
400	50	8	89
401	51	1	60
402	51	2	65
403	51	3	70
404	51	4	75
405	51	5	80
406	51	6	0
407	51	7	0
408	51	8	0
409	52	1	30
410	52	2	50
411	52	3	70
412	52	4	80
413	52	5	85
414	52	6	0
415	52	7	0
416	52	8	0
417	53	1	40
418	53	2	50
419	53	3	60
420	53	4	65
421	53	5	72
422	53	6	75
423	53	7	76
424	53	8	0
425	54	1	40
426	54	2	50
427	54	3	60
428	54	4	70
429	54	5	75
430	54	6	78
431	54	7	80
432	54	8	0
433	55	1	50
434	55	2	60
435	55	3	70
436	55	4	75
437	55	5	0
438	55	6	0
439	55	7	0
440	55	8	0
441	56	1	40
442	56	2	50
443	56	3	60
444	56	4	70
445	56	5	75
446	56	6	80
447	56	7	0
448	56	8	0
449	57	1	40
450	57	2	60
451	57	3	65
452	57	4	69
453	57	5	72
454	57	6	74
455	57	7	0
456	57	8	0
457	58	1	65
458	58	2	70
459	58	3	75
460	58	4	78
461	58	5	81
462	58	6	83
463	58	7	0
464	58	8	0
465	59	1	65
466	59	2	70
467	59	3	75
468	59	4	80
469	59	5	0
470	59	6	0
471	59	7	0
472	59	8	0
473	60	1	65
474	60	2	75
475	60	3	78
476	60	4	80
477	60	5	81
478	60	6	0
479	60	7	0
480	60	8	0
481	61	1	65
482	61	2	70
483	61	3	75
484	61	4	78
485	61	5	80
486	61	6	0
487	61	7	0
488	61	8	0
489	62	1	50
490	62	2	60
491	62	3	70
492	62	4	75
493	62	5	78
494	62	6	80
495	62	7	82
496	62	8	84
497	63	1	50
498	63	2	60
499	63	3	70
500	63	4	75
501	63	5	79
502	63	6	0
503	63	7	0
504	63	8	0
505	64	1	40
506	64	2	45
507	64	3	50
508	64	4	55
509	64	5	60
510	64	6	65
511	64	7	70
512	64	8	75
513	65	1	40
514	65	2	50
515	65	3	60
516	65	4	70
517	65	5	74.5
518	65	6	0
519	65	7	0
520	65	8	0
521	66	1	60
522	66	2	65
523	66	3	70
524	66	4	75
525	66	5	78
526	66	6	0
527	66	7	0
528	66	8	0
529	67	1	60
530	67	2	65
531	67	3	70
532	67	4	75
533	67	5	78
534	67	6	0
535	67	7	0
536	67	8	0
537	68	1	50
538	68	2	60
539	68	3	70
540	68	4	75
541	68	5	80
542	68	6	82
543	68	7	84
544	68	8	85
545	69	1	60
546	69	2	64
547	69	3	70
548	69	4	74
549	69	5	78
550	69	6	80
551	69	7	82
552	69	8	83
553	70	1	60
554	70	2	65
555	70	3	70
556	70	4	75
557	70	5	80
558	70	6	82.5
559	70	7	85
560	70	8	0
561	71	1	60
562	71	2	70
563	71	3	75
564	71	4	78
565	71	5	80
566	71	6	81
567	71	7	0
568	71	8	0
569	72	1	40
570	72	2	50
571	72	3	60
572	72	4	67
573	72	5	72
574	72	6	75
575	72	7	0
576	72	8	0
577	73	1	70
578	73	2	75
579	73	3	80
580	73	4	0
581	73	5	0
582	73	6	0
583	73	7	0
584	73	8	0
585	74	1	40
586	74	2	50
587	74	3	64
588	74	4	68
589	74	5	72
590	74	6	75
591	74	7	0
592	74	8	0
593	75	1	40
594	75	2	50
595	75	3	65
596	75	4	68
597	75	5	72
598	75	6	75
599	75	7	77
600	75	8	0
601	76	1	50
602	76	2	60
603	76	3	75
604	76	4	81
605	76	5	84
606	76	6	87
607	76	7	89
608	76	8	0
609	77	1	70
610	77	2	75
611	77	3	80
612	77	4	85
613	77	5	88
614	77	6	0
615	77	7	0
616	77	8	0
617	78	1	50
618	78	2	60
619	78	3	75
620	78	4	80
621	78	5	83
622	78	6	86
623	78	7	87
624	78	8	88
625	79	1	40
626	79	2	55
627	79	3	65
628	79	4	75
629	79	5	81
630	79	6	83
631	79	7	85
632	79	8	0
633	80	1	40
634	80	2	50
635	80	3	60
636	80	4	70
637	80	5	75
638	80	6	82
639	80	7	86
640	80	8	88
641	81	1	40
642	81	2	55
643	81	3	65
644	81	4	75
645	81	5	80
646	81	6	85
647	81	7	87
648	81	8	88
649	82	1	50
650	82	2	60
651	82	3	70
652	82	4	75
653	82	5	80
654	82	6	0
655	82	7	0
656	82	8	0
657	83	1	50
658	83	2	60
659	83	3	70
660	83	4	75
661	83	5	80
662	83	6	0
663	83	7	0
664	83	8	0
665	84	1	50
666	84	2	60
667	84	3	70
668	84	4	75
669	84	5	78
670	84	6	0
671	84	7	0
672	84	8	0
673	85	1	65
674	85	2	70
675	85	3	75
676	85	4	80
677	85	5	0
678	85	6	0
679	85	7	0
680	85	8	0
681	86	1	65
682	86	2	70
683	86	3	75
684	86	4	80
685	86	5	0
686	86	6	0
687	86	7	0
688	86	8	0
689	87	1	65
690	87	2	70
691	87	3	75
692	87	4	80
693	87	5	0
694	87	6	0
695	87	7	0
696	87	8	0
697	88	1	65
698	88	2	70
699	88	3	75
700	88	4	78
701	88	5	0
702	88	6	0
703	88	7	0
704	88	8	0
705	89	1	0
706	89	2	0
707	89	3	0
708	89	4	0
709	89	5	0
710	89	6	0
711	89	7	0
712	89	8	0
713	90	1	72
714	90	2	76
715	90	3	78
716	90	4	80
717	90	5	0
718	90	6	0
719	90	7	0
720	90	8	0
721	91	1	76
722	91	2	80
723	91	3	82
724	91	4	0
725	91	5	0
726	91	6	0
727	91	7	0
728	91	8	0
729	92	1	70
730	92	2	77
731	92	3	80
732	92	4	83
733	92	5	0
734	92	6	0
735	92	7	0
736	92	8	0
737	93	1	65
738	93	2	70
739	93	3	75
740	93	4	82
741	93	5	0
742	93	6	0
743	93	7	0
744	93	8	0
745	94	1	60
746	94	2	65
747	94	3	68
748	94	4	71
749	94	5	0
750	94	6	0
751	94	7	0
752	94	8	0
753	95	1	30
754	95	2	35
755	95	3	40
756	95	4	45
757	95	5	48
758	95	6	49
759	95	7	0
760	95	8	0
761	96	1	20
762	96	2	25
763	96	3	30
764	96	4	35
765	96	5	40
766	96	6	45
767	96	7	50
768	96	8	54
769	97	1	50
770	97	2	60
771	97	3	70
772	97	4	75
773	97	5	78
774	97	6	80
775	97	7	0
776	97	8	0
777	98	1	50
778	98	2	60
779	98	3	64
780	98	4	68
781	98	5	72
782	98	6	78
783	98	7	0
784	98	8	0
785	99	1	50
786	99	2	62
787	99	3	70
788	99	4	75
789	99	5	78
790	99	6	80
791	99	7	0
792	99	8	0
793	100	1	50
794	100	2	60
795	100	3	70
796	100	4	75
797	100	5	78
798	100	6	81
799	100	7	0
800	100	8	0
801	101	1	40
802	101	2	50
803	101	3	60
804	101	4	70
805	101	5	74
806	101	6	76
807	101	7	0
808	101	8	0
809	102	1	40
810	102	2	50
811	102	3	60
812	102	4	70
813	102	5	75
814	102	6	77
815	102	7	0
816	102	8	0
817	103	1	60
818	103	2	65
819	103	3	70
820	103	4	75
821	103	5	78
822	103	6	0
823	103	7	0
824	103	8	0
825	104	1	60
826	104	2	66
827	104	3	69
828	104	4	72
829	104	5	75
830	104	6	77
831	104	7	0
832	104	8	0
833	105	1	60
834	105	2	65
835	105	3	70
836	105	4	75
837	105	5	78
838	105	6	0
839	105	7	0
840	105	8	0
841	106	1	60
842	106	2	66
843	106	3	69
844	106	4	72
845	106	5	0
846	106	6	0
847	106	7	0
848	106	8	0
849	107	1	60
850	107	2	66
851	107	3	72
852	107	4	75
853	107	5	77
854	107	6	80
855	107	7	0
856	107	8	0
857	108	1	60
858	108	2	66
859	108	3	69
860	108	4	72
861	108	5	75
862	108	6	78
863	108	7	0
864	108	8	0
865	109	1	60
866	109	2	66
867	109	3	70
868	109	4	75
869	109	5	78
870	109	6	80
871	109	7	0
872	109	8	0
873	110	1	60
874	110	2	66
875	110	3	72
876	110	4	77
877	110	5	79
878	110	6	0
879	110	7	0
880	110	8	0
881	111	1	50
882	111	2	60
883	111	3	70
884	111	4	75
885	111	5	78
886	111	6	80
887	111	7	0
888	111	8	0
889	112	1	50
890	112	2	60
891	112	3	70
892	112	4	78
893	112	5	81.5
894	112	6	0
895	112	7	0
896	112	8	0
897	113	1	50
898	113	2	60
899	113	3	70
900	113	4	76
901	113	5	81
902	113	6	0
903	113	7	0
904	113	8	0
905	114	1	40
906	114	2	50
907	114	3	60
908	114	4	70
909	114	5	75
910	114	6	0
911	114	7	0
912	114	8	0
913	115	1	40
914	115	2	50
915	115	3	60
916	115	4	70
917	115	5	80
918	115	6	84
919	115	7	85.5
920	115	8	0
921	116	1	40
922	116	2	50
923	116	3	60
924	116	4	70
925	116	5	80
926	116	6	84
927	116	7	86
928	116	8	0
929	117	1	40
930	117	2	50
931	117	3	60
932	117	4	70
933	117	5	80
934	117	6	85
935	117	7	90
936	117	8	0
937	118	1	40
938	118	2	50
939	118	3	60
940	118	4	70
941	118	5	75
942	118	6	80
943	118	7	90
944	118	8	0
945	119	1	30
946	119	2	40
947	119	3	50
948	119	4	60
949	119	5	70
950	119	6	75
951	119	7	80
952	119	8	0
953	120	1	74
954	120	2	81
955	120	3	74
956	120	4	81
957	120	5	84
958	120	6	86
959	120	7	0
960	120	8	0
961	121	1	50
962	121	2	60
963	121	3	65
964	121	4	71
965	121	5	77
966	121	6	83
967	121	7	86
968	121	8	0
969	122	1	70
970	122	2	74
971	122	3	77
972	122	4	80
973	122	5	82
974	122	6	84
975	122	7	0
976	122	8	0
977	123	1	50
978	123	2	60
979	123	3	70
980	123	4	75
981	123	5	80
982	123	6	83
983	123	7	85
984	123	8	87
985	124	1	73
986	124	2	77
987	124	3	80
988	124	4	83
989	124	5	84
990	124	6	85
991	124	7	87
992	124	8	0
993	125	1	50
994	125	2	60
995	125	3	70
996	125	4	78
997	125	5	83
998	125	6	86
999	125	7	89
1000	125	8	90
1001	126	1	60
1002	126	2	70
1003	126	3	80
1004	126	4	83
1005	126	5	85
1006	126	6	86
1007	126	7	87
1008	126	8	0
1009	127	1	75
1010	127	2	80
1011	127	3	83
1012	127	4	85
1013	127	5	86
1014	127	6	87
1015	127	7	0
1016	127	8	0
1017	128	1	50
1018	128	2	60
1019	128	3	70
1020	128	4	77
1021	128	5	82
1022	128	6	87
1023	128	7	0
1024	128	8	0
1025	129	1	50
1026	129	2	60
1027	129	3	75
1028	129	4	78
1029	129	5	82
1030	129	6	84
1031	129	7	85
1032	129	8	88
1033	130	1	50
1034	130	2	60
1035	130	3	79
1036	130	4	82
1037	130	5	84
1038	130	6	86
1039	130	7	88
1040	130	8	0
1041	131	1	75
1042	131	2	80
1043	131	3	85
1044	131	4	87
1045	131	5	89
1046	131	6	0
1047	131	7	0
1048	131	8	0
1049	132	1	50
1050	132	2	60
1051	132	3	70
1052	132	4	80
1053	132	5	83
1054	132	6	0
1055	132	7	0
1056	132	8	0
1057	133	1	40
1058	133	2	50
1059	133	3	60
1060	133	4	70
1061	133	5	75
1062	133	6	78
1063	133	7	80
1064	133	8	81
1065	134	1	40
1066	134	2	50
1067	134	3	60
1068	134	4	70
1069	134	5	75
1070	134	6	77
1071	134	7	0
1072	134	8	0
1073	135	1	40
1074	135	2	50
1075	135	3	60
1076	135	4	70
1077	135	5	75
1078	135	6	77
1079	135	7	0
1080	135	8	0
1081	136	1	60
1082	136	2	66
1083	136	3	70
1084	136	4	75
1085	136	5	80
1086	136	6	0
1087	136	7	0
1088	136	8	0
1089	137	1	60
1090	137	2	66
1091	137	3	72
1092	137	4	75
1093	137	5	77
1094	137	6	80
1095	137	7	0
1096	137	8	0
1097	138	1	60
1098	138	2	66
1099	138	3	69
1100	138	4	72
1101	138	5	75
1102	138	6	77
1103	138	7	79
1104	138	8	0
1105	139	1	60
1106	139	2	66
1107	139	3	69
1108	139	4	72
1109	139	5	75
1110	139	6	77
1111	139	7	79
1112	139	8	80
1113	140	1	60
1114	140	2	65
1115	140	3	70
1116	140	4	70
1117	140	5	78
1118	140	6	81
1119	140	7	0
1120	140	8	0
1121	141	1	60
1122	141	2	69
1123	141	3	75
1124	141	4	80
1125	141	5	0
1126	141	6	0
1127	141	7	0
1128	141	8	0
1129	142	1	60
1130	142	2	65
1131	142	3	70
1132	142	4	75
1133	142	5	80
1134	142	6	0
1135	142	7	0
1136	142	8	0
1137	143	1	60
1138	143	2	69
1139	143	3	75
1140	143	4	80
1141	143	5	0
1142	143	6	0
1143	143	7	0
1144	143	8	0
1145	144	1	50
1146	144	2	60
1147	144	3	70
1148	144	4	75
1149	144	5	78
1150	144	6	80
1151	144	7	81
1152	144	8	0
1153	145	1	50
1154	145	2	60
1155	145	3	70
1156	145	4	75
1157	145	5	79
1158	145	6	81
1159	145	7	0
1160	145	8	0
1161	146	1	60
1162	146	2	70
1163	146	3	75
1164	146	4	78
1165	146	5	80
1166	146	6	0
1167	146	7	0
1168	146	8	0
1169	147	1	50
1170	147	2	60
1171	147	3	70
1172	147	4	75
1173	147	5	78
1174	147	6	80
1175	147	7	81
1176	147	8	0
1177	148	1	61.5
1178	148	2	72
1179	148	3	78
1180	148	4	82
1181	148	5	84
1182	148	6	86
1183	148	7	87
1184	148	8	88
1185	149	1	0
1186	149	2	0
1187	149	3	0
1188	149	4	0
1189	149	5	0
1190	149	6	0
1191	149	7	0
1192	149	8	0
1193	150	1	70
1194	150	2	75
1195	150	3	80
1196	150	4	82
1197	150	5	85
1198	150	6	0
1199	150	7	0
1200	150	8	0
1201	151	1	70
1202	151	2	75
1203	151	3	80
1204	151	4	82
1205	151	5	0
1206	151	6	0
1207	151	7	0
1208	151	8	0
1209	152	1	30
1210	152	2	40
1211	152	3	50
1212	152	4	55
1213	152	5	57
1214	152	6	0
1215	152	7	0
1216	152	8	0
1217	153	1	40
1218	153	2	48
1219	153	3	54
1220	153	4	60
1221	153	5	65
1222	153	6	67
1223	153	7	0
1224	153	8	0
1225	154	1	40
1226	154	2	45
1227	154	3	50
1228	154	4	55
1229	154	5	58
1230	154	6	60
1231	154	7	0
1232	154	8	0
1233	155	1	30
1234	155	2	40
1235	155	3	47
1236	155	4	50
1237	155	5	52
1238	155	6	0
1239	155	7	0
1240	155	8	0
1241	156	1	76
1242	156	2	80
1243	156	3	82
1244	156	4	83
1245	156	5	0
1246	156	6	0
1247	156	7	0
1248	156	8	0
1249	157	1	70
1250	157	2	75
1251	157	3	80
1252	157	4	83
1253	157	5	0
1254	157	6	0
1255	157	7	0
1256	157	8	0
1257	158	1	20
1258	158	2	40
1259	158	3	50
1260	158	4	60
1261	158	5	70
1262	158	6	75
1263	158	7	80
1264	158	8	85
1265	159	1	50
1266	159	2	60
1267	159	3	70
1268	159	4	80
1269	159	5	84
1270	159	6	87
1271	159	7	88
1272	159	8	89
1273	160	1	45
1274	160	2	50
1275	160	3	55
1276	160	4	57
1277	160	5	60
1278	160	6	62
1279	160	7	0
1280	160	8	0
1281	161	1	45
1282	161	2	50
1283	161	3	55
1284	161	4	57
1285	161	5	60
1286	161	6	63
1287	161	7	0
1288	161	8	0
1289	162	1	70
1290	162	2	75
1291	162	3	80
1292	162	4	82
1293	162	5	84
1294	162	6	0
1295	162	7	0
1296	162	8	0
1297	163	1	75
1298	163	2	80
1299	163	3	82
1300	163	4	0
1301	163	5	0
1302	163	6	0
1303	163	7	0
1304	163	8	0
1305	164	1	75
1306	164	2	77
1307	164	3	80
1308	164	4	83
1309	164	5	0
1310	164	6	0
1311	164	7	0
1312	164	8	0
1313	165	1	78
1314	165	2	81
1315	165	3	84
1316	165	4	0
1317	165	5	0
1318	165	6	0
1319	165	7	0
1320	165	8	0
1321	166	1	60
1322	166	2	65
1323	166	3	70
1324	166	4	75
1325	166	5	80
1326	166	6	82
1327	166	7	0
1328	166	8	0
1329	167	1	70
1330	167	2	75
1331	167	3	80
1332	167	4	82
1333	167	5	84
1334	167	6	85
1335	167	7	0
1336	167	8	0
1337	168	1	72
1338	168	2	75
1339	168	3	80
1340	168	4	82
1341	168	5	0
1342	168	6	0
1343	168	7	0
1344	168	8	0
1345	169	1	60
1346	169	2	63
1347	169	3	65
1348	169	4	67
1349	169	5	69
1350	169	6	0
1351	169	7	0
1352	169	8	0
1353	170	1	30
1354	170	2	40
1355	170	3	50
1356	170	4	60
1357	170	5	65
1358	170	6	67
1359	170	7	0
1360	170	8	0
1361	171	1	40
1362	171	2	50
1363	171	3	60
1364	171	4	65
1365	171	5	70
1366	171	6	0
1367	171	7	0
1368	171	8	0
1369	172	1	56
1370	172	2	64
1371	172	3	70
1372	172	4	73
1373	172	5	0
1374	172	6	0
1375	172	7	0
1376	172	8	0
1377	173	1	30
1378	173	2	40
1379	173	3	50
1380	173	4	60
1381	173	5	65
1382	173	6	69
1383	173	7	0
1384	173	8	0
1385	174	1	75
1386	174	2	80
1387	174	3	85
1388	174	4	0
1389	174	5	0
1390	174	6	0
1391	174	7	0
1392	174	8	0
1393	175	1	40
1394	175	2	50
1395	175	3	60
1396	175	4	70
1397	175	5	75
1398	175	6	0
1399	175	7	0
1400	175	8	0
1401	176	1	20
1402	176	2	30
1403	176	3	35
1404	176	4	40
1405	176	5	45
1406	176	6	47
1407	176	7	0
1408	176	8	0
1409	177	1	30
1410	177	2	40
1411	177	3	45
1412	177	4	50
1413	177	5	53
1414	177	6	0
1415	177	7	0
1416	177	8	0
1417	178	1	20
1418	178	2	25
1419	178	3	30
1420	178	4	35
1421	178	5	38
1422	178	6	0
1423	178	7	0
1424	178	8	0
1425	179	1	20
1426	179	2	26
1427	179	3	31
1428	179	4	35
1429	179	5	40
1430	179	6	0
1431	179	7	0
1432	179	8	0
1433	180	1	20
1434	180	2	30
1435	180	3	35
1436	180	4	41
1437	180	5	45
1438	180	6	0
1439	180	7	0
1440	180	8	0
1441	181	1	30
1442	181	2	40
1443	181	3	45
1444	181	4	50
1445	181	5	52
1446	181	6	55
1447	181	7	0
1448	181	8	0
1449	182	1	30
1450	182	2	40
1451	182	3	47
1452	182	4	54
1453	182	5	57
1454	182	6	0
1455	182	7	0
1456	182	8	0
1457	183	1	40
1458	183	2	50
1459	183	3	55
1460	183	4	60
1461	183	5	62
1462	183	6	0
1463	183	7	0
1464	183	8	0
1465	184	1	40
1466	184	2	50
1467	184	3	55
1468	184	4	60
1469	184	5	63
1470	184	6	65
1471	184	7	0
1472	184	8	0
1473	185	1	30
1474	185	2	40
1475	185	3	50
1476	185	4	57
1477	185	5	0
1478	185	6	0
1479	185	7	0
1480	185	8	0
1481	186	1	40
1482	186	2	50
1483	186	3	60
1484	186	4	66
1485	186	5	70
1486	186	6	0
1487	186	7	0
1488	186	8	0
1489	187	1	40
1490	187	2	50
1491	187	3	55
1492	187	4	60
1493	187	5	63
1494	187	6	0
1495	187	7	0
1496	187	8	0
1497	188	1	0
1498	188	2	0
1499	188	3	0
1500	188	4	0
1501	188	5	0
1502	188	6	0
1503	188	7	0
1504	188	8	0
1505	189	1	50
1506	189	2	60
1507	189	3	70
1508	189	4	75
1509	189	5	80
1510	189	6	85
1511	189	7	88
1512	189	8	0
1513	190	1	40
1514	190	2	50
1515	190	3	60
1516	190	4	65
1517	190	5	68
1518	190	6	69
1519	190	7	0
1520	190	8	0
1521	191	1	50
1522	191	2	55
1523	191	3	60
1524	191	4	65
1525	191	5	68
1526	191	6	70
1527	191	7	72
1528	191	8	0
1529	192	1	50
1530	192	2	60
1531	192	3	67
1532	192	4	70
1533	192	5	0
1534	192	6	0
1535	192	7	0
1536	192	8	0
1537	193	1	30
1538	193	2	45
1539	193	3	55
1540	193	4	65
1541	193	5	70
1542	193	6	75
1543	193	7	77
1544	193	8	0
1545	194	1	55
1546	194	2	65
1547	194	3	70
1548	194	4	75
1549	194	5	77
1550	194	6	78
1551	194	7	0
1552	194	8	0
1553	195	1	50
1554	195	2	60
1555	195	3	65
1556	195	4	70
1557	195	5	74
1558	195	6	76
1559	195	7	77
1560	195	8	0
1561	196	1	40
1562	196	2	50
1563	196	3	60
1564	196	4	66
1565	196	5	70
1566	196	6	72
1567	196	7	74
1568	196	8	75
1569	197	1	50
1570	197	2	60
1571	197	3	70
1572	197	4	80
1573	197	5	82
1574	197	6	0
1575	197	7	0
1576	197	8	0
1577	198	1	55
1578	198	2	60
1579	198	3	65
1580	198	4	70
1581	198	5	74
1582	198	6	0
1583	198	7	0
1584	198	8	0
1585	199	1	60
1586	199	2	65
1587	199	3	70
1588	199	4	75
1589	199	5	77
1590	199	6	78
1591	199	7	77
1592	199	8	75
1593	200	1	40
1594	200	2	50
1595	200	3	60
1596	200	4	65
1597	200	5	70
1598	200	6	0
1599	200	7	0
1600	200	8	0
1601	201	1	50
1602	201	2	60
1603	201	3	70
1604	201	4	75
1605	201	5	76
1606	201	6	0
1607	201	7	0
1608	201	8	0
1609	202	1	55
1610	202	2	60
1611	202	3	65
1612	202	4	70
1613	202	5	72
1614	202	6	74
1615	202	7	75.5
1616	202	8	0
1617	203	1	50
1618	203	2	55
1619	203	3	60
1620	203	4	65
1621	203	5	70
1622	203	6	73
1623	203	7	75
1624	203	8	77
1625	204	1	55
1626	204	2	60
1627	204	3	65
1628	204	4	70
1629	204	5	72
1630	204	6	73
1631	204	7	74
1632	204	8	0
1633	205	1	50
1634	205	2	60
1635	205	3	65
1636	205	4	68
1637	205	5	70
1638	205	6	72
1639	205	7	74
1640	205	8	75
1641	206	1	50
1642	206	2	55
1643	206	3	60
1644	206	4	65
1645	206	5	70
1646	206	6	72
1647	206	7	73
1648	206	8	0
1649	207	1	60
1650	207	2	55
1651	207	3	60
1652	207	4	65
1653	207	5	68
1654	207	6	70
1655	207	7	72
1656	207	8	0
1657	208	1	40
1658	208	2	50
1659	208	3	55
1660	208	4	59
1661	208	5	62
1662	208	6	64
1663	208	7	0
1664	208	8	0
1665	209	1	40
1666	209	2	50
1667	209	3	60
1668	209	4	65
1669	209	5	72
1670	209	6	74
1671	209	7	76
1672	209	8	0
1673	210	1	60
1674	210	2	65
1675	210	3	70
1676	210	4	75
1677	210	5	77
1678	210	6	78
1679	210	7	80
1680	210	8	0
1681	211	1	60
1682	211	2	65
1683	211	3	70
1684	211	4	75
1685	211	5	80
1686	211	6	0
1687	211	7	0
1688	211	8	0
1689	212	1	60
1690	212	2	65
1691	212	3	70
1692	212	4	74
1693	212	5	76
1694	212	6	78
1695	212	7	79
1696	212	8	80
1697	213	1	50
1698	213	2	55
1699	213	3	60
1700	213	4	65
1701	213	5	70
1702	213	6	75
1703	213	7	80
1704	213	8	0
1705	214	1	51.5
1706	214	2	62
1707	214	3	67
1708	214	4	70
1709	214	5	75
1710	214	6	78
1711	214	7	80
1712	214	8	0
1713	215	1	51.5
1714	215	2	62
1715	215	3	67
1716	215	4	70
1717	215	5	75
1718	215	6	78
1719	215	7	80
1720	215	8	0
1721	216	1	51.5
1722	216	2	62
1723	216	3	67
1724	216	4	70
1725	216	5	75
1726	216	6	78
1727	216	7	80
1728	216	8	0
1729	217	1	50
1730	217	2	60
1731	217	3	67
1732	217	4	72
1733	217	5	75
1734	217	6	78
1735	217	7	80
1736	217	8	0
1737	218	1	50
1738	218	2	60
1739	218	3	68
1740	218	4	72
1741	218	5	75
1742	218	6	0
1743	218	7	0
1744	218	8	0
1745	219	1	65
1746	219	2	70
1747	219	3	75
1748	219	4	78
1749	219	5	0
1750	219	6	0
1751	219	7	0
1752	219	8	0
1753	220	1	30
1754	220	2	35
1755	220	3	40
1756	220	4	45
1757	220	5	50
1758	220	6	60
1759	220	7	0
1760	220	8	0
1761	221	1	55
1762	221	2	60
1763	221	3	65
1764	221	4	70
1765	221	5	75
1766	221	6	80
1767	221	7	81
1768	221	8	0
1769	222	1	50
1770	222	2	55
1771	222	3	60
1772	222	4	65
1773	222	5	70
1774	222	6	73
1775	222	7	76
1776	222	8	78
1777	223	1	50
1778	223	2	55
1779	223	3	60
1780	223	4	65
1781	223	5	70
1782	223	6	75
1783	223	7	77
1784	223	8	78
1785	224	1	50
1786	224	2	60
1787	224	3	70
1788	224	4	75
1789	224	5	78
1790	224	6	0
1791	224	7	0
1792	224	8	0
1793	225	1	50
1794	225	2	55
1795	225	3	60
1796	225	4	65
1797	225	5	70
1798	225	6	73
1799	225	7	76
1800	225	8	78
1801	226	1	50
1802	226	2	55
1803	226	3	60
1804	226	4	65
1805	226	5	70
1806	226	6	73
1807	226	7	75
1808	226	8	77
1809	227	1	50
1810	227	2	60
1811	227	3	65
1812	227	4	70
1813	227	5	72
1814	227	6	74
1815	227	7	0
1816	227	8	0
1817	228	1	50
1818	228	2	55
1819	228	3	60
1820	228	4	65
1821	228	5	68
1822	228	6	70
1823	228	7	72
1824	228	8	0
1825	229	1	55
1826	229	2	60
1827	229	3	65
1828	229	4	67
1829	229	5	70
1830	229	6	71
1831	229	7	0
1832	229	8	0
1833	230	1	60
1834	230	2	65
1835	230	3	70
1836	230	4	75
1837	230	5	78
1838	230	6	81
1839	230	7	0
1840	230	8	0
1841	231	1	60
1842	231	2	70
1843	231	3	75
1844	231	4	79
1845	231	5	80
1846	231	6	81
1847	231	7	0
1848	231	8	0
1849	232	1	60
1850	232	2	70
1851	232	3	75
1852	232	4	78
1853	232	5	80
1854	232	6	0
1855	232	7	0
1856	232	8	0
1857	233	1	50
1858	233	2	60
1859	233	3	65
1860	233	4	70
1861	233	5	73
1862	233	6	75
1863	233	7	0
1864	233	8	0
1865	234	1	0
1866	234	2	0
1867	234	3	0
1868	234	4	0
1869	234	5	0
1870	234	6	0
1871	234	7	0
1872	234	8	0
1873	235	1	40
1874	235	2	50
1875	235	3	60
1876	235	4	70
1877	235	5	0
1878	235	6	0
1879	235	7	0
1880	235	8	0
1881	236	1	55
1882	236	2	60
1883	236	3	65
1884	236	4	70
1885	236	5	0
1886	236	6	0
1887	236	7	0
1888	236	8	0
1889	237	1	50
1890	237	2	60
1891	237	3	65
1892	237	4	72
1893	237	5	75
1894	237	6	0
1895	237	7	0
1896	237	8	0
1897	238	1	50
1898	238	2	60
1899	238	3	70
1900	238	4	75
1901	238	5	80
1902	238	6	82
1903	238	7	0
1904	238	8	0
1905	239	1	60
1906	239	2	65
1907	239	3	70
1908	239	4	75
1909	239	5	0
1910	239	6	0
1911	239	7	0
1912	239	8	0
1913	240	1	38
1914	240	2	49
1915	240	3	57
1916	240	4	63
1917	240	5	67
1918	240	6	70
1919	240	7	72
1920	240	8	0
1921	241	1	50
1922	241	2	55
1923	241	3	60
1924	241	4	65
1925	241	5	70
1926	241	6	75
1927	241	7	0
1928	241	8	0
1929	242	1	50
1930	242	2	58
1931	242	3	65
1932	242	4	70
1933	242	5	73
1934	242	6	0
1935	242	7	0
1936	242	8	0
1937	243	1	65
1938	243	2	74
1939	243	3	79
1940	243	4	82
1941	243	5	84
1942	243	6	0
1943	243	7	0
1944	243	8	0
1945	244	1	64
1946	244	2	69
1947	244	3	76
1948	244	4	80
1949	244	5	0
1950	244	6	0
1951	244	7	0
1952	244	8	0
1953	245	1	52
1954	245	2	58
1955	245	3	64
1956	245	4	68
1957	245	5	72
1958	245	6	0
1959	245	7	0
1960	245	8	0
1961	246	1	50
1962	246	2	60
1963	246	3	65
1964	246	4	70
1965	246	5	75
1966	246	6	83
1967	246	7	0
1968	246	8	0
1969	247	1	40
1970	247	2	50
1971	247	3	60
1972	247	4	65
1973	247	5	70
1974	247	6	75
1975	247	7	0
1976	247	8	0
1977	248	1	50
1978	248	2	60
1979	248	3	70.075
1980	248	4	80
1981	248	5	83
1982	248	6	86
1983	248	7	0
1984	249	1	50
1985	249	2	60
1986	249	3	70
1987	249	4	75
1988	249	5	82
1989	249	6	85
1990	249	7	0
1991	249	8	0
1992	250	1	65
1993	250	2	70
1994	250	3	74
1995	250	4	77
1996	250	5	80
1997	250	6	0
1998	250	7	0
1999	250	8	0
2000	251	1	59
2001	251	2	70
2002	251	3	75
2003	251	4	76
2004	251	5	0
2005	251	6	0
2006	251	7	0
2007	251	8	0
2008	252	1	50
2009	252	2	60
2010	252	3	65
2011	252	4	70
2012	252	5	75
2013	252	6	78
2014	252	7	80
2015	252	8	82
2016	253	1	50
2017	253	2	60
2018	253	3	65
2019	253	4	70
2020	253	5	75
2021	253	6	80
2022	253	7	0
2023	253	8	0
2024	254	1	50
2025	254	2	60
2026	254	3	65
2027	254	4	70
2028	254	5	72
2029	254	6	74
2030	254	7	75
2031	254	8	0
2032	255	1	60
2033	255	2	65
2034	255	3	70
2035	255	4	75
2036	255	5	78
2037	255	6	80
2038	255	7	0
2039	255	8	0
2040	256	1	60
2041	256	2	65
2042	256	3	70
2043	256	4	74
2044	256	5	78
2045	256	6	80
2046	256	7	81
2047	256	8	0
2048	257	1	60
2049	257	2	65
2050	257	3	70
2051	257	4	75
2052	257	5	78
2053	257	6	80
2054	257	7	0
2055	257	8	0
2056	258	1	60
2057	258	2	65
2058	258	3	70
2059	258	4	72
2060	258	5	73
2061	258	6	0
2062	258	7	0
2063	258	8	0
2064	259	1	30
2065	259	2	40
2066	259	3	45
2067	259	4	50
2068	259	5	54
2069	259	6	0
2070	259	7	0
2071	259	8	0
2072	260	1	30
2073	260	2	40
2074	260	3	45
2075	260	4	50
2076	260	5	53
2077	260	6	0
2078	260	7	0
2079	260	8	0
2080	261	1	28
2081	261	2	32
2082	261	3	37
2083	261	4	42
2084	261	5	0
2085	261	6	0
2086	261	7	0
2087	261	8	0
2088	262	1	0
2089	262	2	0
2090	262	3	0
2091	262	4	0
2092	262	5	0
2093	262	6	0
2094	262	7	0
2095	262	8	0
2096	263	1	50
2097	263	2	65
2098	263	3	75
2099	263	4	80
2100	263	5	0
2101	263	6	0
2102	263	7	0
2103	263	8	0
2104	264	1	50
2105	264	2	65
2106	264	3	75
2107	264	4	80
2108	264	5	82
2109	264	6	0
2110	264	7	0
2111	264	8	0
2112	265	1	58
2113	265	2	68
2114	265	3	78
2115	265	4	80.8
2116	265	5	0
2117	265	6	0
2118	265	7	0
2119	265	8	0
2120	266	1	50
2121	266	2	60
2122	266	3	70
2123	266	4	78
2124	266	5	80
2125	266	6	0
2126	266	7	0
2127	266	8	0
2128	267	1	50
2129	267	2	63
2130	267	3	76
2131	267	4	82
2132	267	5	0
2133	267	6	0
2134	267	7	0
2135	267	8	0
2136	268	1	65
2137	268	2	70
2138	268	3	75
2139	268	4	80
2140	268	5	84
2141	268	6	0
2142	268	7	0
2143	268	8	0
2144	269	1	55
2145	269	2	75
2146	269	3	80
2147	269	4	83
2148	269	5	0
2149	269	6	0
2150	269	7	0
2151	269	8	0
2152	270	1	40
2153	270	2	50
2154	270	3	60
2155	270	4	70
2156	270	5	75
2157	270	6	80
2158	270	7	0
2159	270	8	0
2160	271	1	50
2161	271	2	65
2162	271	3	75
2163	271	4	81
2164	271	5	0
2165	271	6	0
2166	271	7	0
2167	271	8	0
2168	272	1	60
2169	272	2	70
2170	272	3	80
2171	272	4	84
2172	272	5	0
2173	272	6	0
2174	272	7	0
2175	272	8	0
2176	273	1	45
2177	273	2	55
2178	273	3	70
2179	273	4	80
2180	273	5	0
2181	273	6	0
2182	273	7	0
2183	273	8	0
2184	274	1	45
2185	274	2	60
2186	274	3	73
2187	274	4	80
2188	274	5	0
2189	274	6	0
2190	274	7	0
2191	274	8	0
2192	275	1	71
2193	275	2	80
2194	275	3	84
2195	275	4	0
2196	275	5	0
2197	275	6	0
2198	275	7	0
2199	275	8	0
2200	276	1	60
2201	276	2	70
2202	276	3	78
2203	276	4	87
2204	276	5	0
2205	276	6	0
2206	276	7	0
2207	276	8	0
2208	277	1	50
2209	277	2	60
2210	277	3	70
2211	277	4	80
2212	277	5	85
2213	277	6	88
2214	277	7	0
2215	277	8	0
2216	278	1	50
2217	278	2	66
2218	278	3	80
2219	278	4	86
2220	278	5	0
2221	278	6	0
2222	278	7	0
2223	278	8	0
2224	279	1	51
2225	279	2	67
2226	279	3	80
2227	279	4	82.9
2228	279	5	0
2229	279	6	0
2230	279	7	0
2231	279	8	0
2232	280	1	50
2233	280	2	67
2234	280	3	77
2235	280	4	83
2236	280	5	0
2237	280	6	0
2238	280	7	0
2239	280	8	0
2240	281	1	50
2241	281	2	70
2242	281	3	81
2243	281	4	85.5
2244	281	5	0
2245	281	6	0
2246	281	7	0
2247	281	8	0
2248	282	1	66
2249	282	2	81
2250	282	3	86.5
2251	282	4	0
2252	282	5	0
2253	282	6	0
2254	282	7	0
2255	282	8	0
2256	283	1	56
2257	283	2	68
2258	283	3	77
2259	283	4	81
2260	283	5	83
2261	283	6	0
2262	283	7	0
2263	283	8	0
2264	284	1	61
2265	284	2	73
2266	284	3	82
2267	284	4	86
2268	284	5	0
2269	284	6	0
2270	284	7	0
2271	284	8	0
2272	285	1	56
2273	285	2	75
2274	285	3	85
2275	285	4	87.2
2276	285	5	0
2277	285	6	0
2278	285	7	0
2279	285	8	0
2280	286	1	60
2281	286	2	70
2282	286	3	80
2283	286	4	85
2284	286	5	87
2285	286	6	0
2286	286	7	0
2287	286	8	0
2288	287	1	40
2289	287	2	50
2290	287	3	60
2291	287	4	70
2292	287	5	77
2293	287	6	0
2294	287	7	0
2295	287	8	0
2296	288	1	45
2297	288	2	50
2298	288	3	55
2299	288	4	60
2300	288	5	65
2301	288	6	70
2302	288	7	75
2303	288	8	80
2304	289	1	65
2305	289	2	70
2306	289	3	80
2307	289	4	88
2308	289	5	0
2309	289	6	0
2310	289	7	0
2311	289	8	0
2312	290	1	50
2313	290	2	60
2314	290	3	70
2315	290	4	80
2316	290	5	85
2317	290	6	0
2318	290	7	0
2319	290	8	0
2320	291	1	78
2321	291	2	82
2322	291	3	86
2323	291	4	87
2324	291	5	88
2325	291	6	89
2326	291	7	0
2327	291	8	0
2328	292	1	76
2329	292	2	80
2330	292	3	82
2331	292	4	84
2332	292	5	85
2333	292	6	0
2334	292	7	0
2335	292	8	0
2336	293	1	40
2337	293	2	50
2338	293	3	60
2339	293	4	65
2340	293	5	70
2341	293	6	72
2342	293	7	0
2343	293	8	0
2344	294	1	60
2345	294	2	65
2346	294	3	70
2347	294	4	75
2348	294	5	80
2349	294	6	83
2350	294	7	85
2351	294	8	0
2352	295	1	30
2353	295	2	40
2354	295	3	50
2355	295	4	60
2356	295	5	70
2357	295	6	80
2358	295	7	0
2359	295	8	0
2360	296	1	50
2361	296	2	60
2362	296	3	70
2363	296	4	75
2364	296	5	80
2365	296	6	81
2366	296	7	82
2367	296	8	0
2368	297	1	40
2369	297	2	50
2370	297	3	60
2371	297	4	70
2372	297	5	80
2373	297	6	82
2374	297	7	83
2375	297	8	0
2376	298	1	50
2377	298	2	60
2378	298	3	67
2379	298	4	72
2380	298	5	77
2381	298	6	80
2382	298	7	0
2383	298	8	0
2384	299	1	40
2385	299	2	50
2386	299	3	60
2387	299	4	70
2388	299	5	74
2389	299	6	78
2390	299	7	80
2391	299	8	81
2392	300	1	60
2393	300	2	65
2394	300	3	70
2395	300	4	73
2396	300	5	75
2397	300	6	0
2398	300	7	0
2399	300	8	0
2400	301	1	30
2401	301	2	40
2402	301	3	50
2403	301	4	60
2404	301	5	70
2405	301	6	80
2406	301	7	70
2407	301	8	0
2408	302	1	50
2409	302	2	55
2410	302	3	60
2411	302	4	64
2412	302	5	66
2413	302	6	68
2414	302	7	70
2415	302	8	0
2416	303	1	60
2417	303	2	65
2418	303	3	70
2419	303	4	75
2420	303	5	0
2421	303	6	0
2422	303	7	0
2423	303	8	0
2424	304	1	65
2425	304	2	70
2426	304	3	75
2427	304	4	77
2428	304	5	0
2429	304	6	0
2430	304	7	0
2431	304	8	0
2432	305	1	50
2433	305	2	60
2434	305	3	65
2435	305	4	69
2436	305	5	72
2437	305	6	76
2438	305	7	78
2439	305	8	0
2440	306	1	50
2441	306	2	60
2442	306	3	65
2443	306	4	70
2444	306	5	74
2445	306	6	79
2446	306	7	0
2447	306	8	0
2448	307	1	50
2449	307	2	55
2450	307	3	60
2451	307	4	65
2452	307	5	70
2453	307	6	0
2454	307	7	0
2455	307	8	0
2456	308	1	50
2457	308	2	60
2458	308	3	70
2459	308	4	73
2460	308	5	75
2461	308	6	77
2462	308	7	79
2463	308	8	80
2464	309	1	50
2465	309	2	60
2466	309	3	75
2467	309	4	78
2468	309	5	81
2469	309	6	83
2470	309	7	0
2471	309	8	0
2472	310	1	70
2473	310	2	73
2474	310	3	75
2475	310	4	77
2476	310	5	78
2477	310	6	79
2478	310	7	0
2479	310	8	0
2480	311	1	50
2481	311	2	60
2482	311	3	65
2483	311	4	68
2484	311	5	70
2485	311	6	73
2486	311	7	0
2487	311	8	0
2488	312	1	40
2489	312	2	50
2490	312	3	60
2491	312	4	70
2492	312	5	80
2493	312	6	84
2494	312	7	86
2495	312	8	0
2496	313	1	50
2497	313	2	60
2498	313	3	70
2499	313	4	77
2500	313	5	80
2501	313	6	87
2502	313	7	0
2503	313	8	0
2504	314	1	40
2505	314	2	60
2506	314	3	70
2507	314	4	80
2508	314	5	85
2509	314	6	0
2510	314	7	0
2511	314	8	0
2512	315	1	50
2513	315	2	60
2514	315	3	70
2515	315	4	75
2516	315	5	80
2517	315	6	87
2518	315	7	0
2519	315	8	0
2520	316	1	40
2521	316	2	50
2522	316	3	60
2523	316	4	70
2524	316	5	80
2525	316	6	84
2526	316	7	86
2527	316	8	0
2528	317	1	40
2529	317	2	50
2530	317	3	60
2531	317	4	70
2532	317	5	80
2533	317	6	85
2534	317	7	90
2535	317	8	0
2536	318	1	50
2537	318	2	60
2538	318	3	70
2539	318	4	80
2540	318	5	83
2541	318	6	85
2542	318	7	87
2543	318	8	0
2544	319	1	10
2545	319	2	20
2546	319	3	30
2547	319	4	40
2548	319	5	50
2549	319	6	60
2550	319	7	0
2551	319	8	0
2552	320	1	50
2553	320	2	60
2554	320	3	68
2555	320	4	72
2556	320	5	74
2557	320	6	0
2558	320	7	0
2559	320	8	0
2560	321	1	50
2561	321	2	60
2562	321	3	65
2563	321	4	70
2564	321	5	72
2565	321	6	0
2566	321	7	0
2567	321	8	0
2568	322	1	40
2569	322	2	45
2570	322	3	50
2571	322	4	55
2572	322	5	60
2573	322	6	65
2574	322	7	70
2575	322	8	80
2576	323	1	40
2577	323	2	50
2578	323	3	60
2579	323	4	64
2580	323	5	75
2581	323	6	80
2582	323	7	82
2583	323	8	0
2584	324	1	50
2585	324	2	60
2586	324	3	70
2587	324	4	80
2588	324	5	90
2589	324	6	0
2590	324	7	0
2591	324	8	0
2592	325	1	30
2593	325	2	40
2594	325	3	51
2595	325	4	60
2596	325	5	65
2597	325	6	68
2598	325	7	0
2599	325	8	0
2600	326	1	0
2601	326	2	0
2602	326	3	0
2603	326	4	0
2604	326	5	0
2605	326	6	0
2606	326	7	0
2607	326	8	0
2608	327	1	30
2609	327	2	40
2610	327	3	50
2611	327	4	60
2612	327	5	70
2613	327	6	75
2614	327	7	80
2615	327	8	83
2616	328	1	40
2617	328	2	50
2618	328	3	60
2619	328	4	65
2620	328	5	69
2621	328	6	0
2622	328	7	0
2623	328	8	0
2624	329	1	50
2625	329	2	60
2626	329	3	70
2627	329	4	80
2628	329	5	90
2629	329	6	0
2630	329	7	0
2631	329	8	0
2632	330	1	67
2633	330	2	75
2634	330	3	81
2635	330	4	84
2636	330	5	86
2637	330	6	0
2638	330	7	0
2639	330	8	0
2640	331	1	67
2641	331	2	75
2642	331	3	81
2643	331	4	84
2644	331	5	86
2645	331	6	0
2646	331	7	0
2647	331	8	0
2648	332	1	60
2649	332	2	70
2650	332	3	80
2651	332	4	82
2652	332	5	0
2653	332	6	0
2654	332	7	0
2655	332	8	0
2656	333	1	40
2657	333	2	50
2658	333	3	60
2659	333	4	65
2660	333	5	70
2661	333	6	73
2662	333	7	0
2663	333	8	0
2664	334	1	20
2665	334	2	30
2666	334	3	40
2667	334	4	50
2668	334	5	60
2669	334	6	70
2670	334	7	0
2671	334	8	0
2672	335	1	30
2673	335	2	40
2674	335	3	50
2675	335	4	60
2676	335	5	70
2677	335	6	73
2678	335	7	75
2679	335	8	0
2680	336	1	40
2681	336	2	50
2682	336	3	60
2683	336	4	65
2684	336	5	70
2685	336	6	73
2686	336	7	75
2687	336	8	76
2688	337	1	55
2689	337	2	65
2690	337	3	70
2691	337	4	75
2692	337	5	77
2693	337	6	0
2694	337	7	0
2695	337	8	0
2696	338	1	50
2697	338	2	60
2698	338	3	65
2699	338	4	70
2700	338	5	72
2701	338	6	74
2702	338	7	0
2703	338	8	0
2704	339	1	20
2705	339	2	30
2706	339	3	40
2707	339	4	50
2708	339	5	60
2709	339	6	70
2710	339	7	75
2711	339	8	0
2712	340	1	30
2713	340	2	40
2714	340	3	50
2715	340	4	60
2716	340	5	70
2717	340	6	75
2718	340	7	78
2719	340	8	79
2720	341	1	30
2721	341	2	50
2722	341	3	60
2723	341	4	74
2724	341	5	77
2725	341	6	79
2726	341	7	80
2727	341	8	81
2728	342	1	30
2729	342	2	40
2730	342	3	50
2731	342	4	60
2732	342	5	70
2733	342	6	77
2734	342	7	80
2735	342	8	81
2736	343	1	50
2737	343	2	68
2738	343	3	73
2739	343	4	78
2740	343	5	80
2741	343	6	82
2742	343	7	83
2743	343	8	0
2744	344	1	50
2745	344	2	60
2746	344	3	65
2747	344	4	70
2748	344	5	75
2749	344	6	80
2750	344	7	0
2751	344	8	0
2752	345	1	40
2753	345	2	47
2754	345	3	54
2755	345	4	60
2756	345	5	65
2757	345	6	67
2758	345	7	0
2759	345	8	0
2760	346	1	30
2761	346	2	40
2762	346	3	50
2763	346	4	60
2764	346	5	65
2765	346	6	70
2766	346	7	72
2767	346	8	0
2768	347	1	30
2769	347	2	40
2770	347	3	50
2771	347	4	60
2772	347	5	65
2773	347	6	68
2774	347	7	70
2775	347	8	0
2776	348	1	30
2777	348	2	40
2778	348	3	50
2779	348	4	60
2780	348	5	65
2781	348	6	70
2782	348	7	72
2783	348	8	73
2784	349	1	30
2785	349	2	40
2786	349	3	50
2787	349	4	60
2788	349	5	70
2789	349	6	75
2790	349	7	0
2791	349	8	0
2792	350	1	40
2793	350	2	50
2794	350	3	55
2795	350	4	60
2796	350	5	65
2797	350	6	70
2798	350	7	72
2799	350	8	74
2800	351	1	40
2801	351	2	50
2802	351	3	60
2803	351	4	65
2804	351	5	70
2805	351	6	74
2806	351	7	76
2807	351	8	78
2808	352	1	30
2809	352	2	40
2810	352	3	50
2811	352	4	60
2812	352	5	70
2813	352	6	77
2814	352	7	79
2815	352	8	0
2816	353	1	40
2817	353	2	50
2818	353	3	60
2819	353	4	66
2820	353	5	68
2821	353	6	0
2822	353	7	0
2823	353	8	0
2824	354	1	30
2825	354	2	40
2826	354	3	50
2827	354	4	60
2828	354	5	67
2829	354	6	69
2830	354	7	0
2831	354	8	0
2832	355	1	0
2833	355	2	0
2834	355	3	0
2835	355	4	0
2836	355	5	0
2837	355	6	0
2838	355	7	0
2839	355	8	0
2840	356	1	50
2841	356	2	60
2842	356	3	65
2843	356	4	70
2844	356	5	75
2845	356	6	77
2846	356	7	0
2847	356	8	0
2848	357	1	0
2849	357	2	0
2850	357	3	0
2851	357	4	0
2852	357	5	0
2853	357	6	0
2854	357	7	0
2855	357	8	0
2856	358	1	60
2857	358	2	65
2858	358	3	70
2859	358	4	75
2860	358	5	78
2861	358	6	0
2862	358	7	0
2863	358	8	0
2864	359	1	50
2865	359	2	60
2866	359	3	65
2867	359	4	70
2868	359	5	75
2869	359	6	80
2870	359	7	0
2871	359	8	0
2872	360	1	42
2873	360	2	55
2874	360	3	66
2875	360	4	75
2876	360	5	80
2877	360	6	83
2878	360	7	0
2879	360	8	0
2880	361	1	0
2881	361	2	0
2882	361	3	0
2883	361	4	0
2884	361	5	0
2885	361	6	0
2886	361	7	0
2887	361	8	0
2888	362	1	28
2889	362	2	50
2890	362	3	64
2891	362	4	74
2892	362	5	80
2893	362	6	0
2894	362	7	0
2895	362	8	0
2896	363	1	28
2897	363	2	50
2898	363	3	64
2899	363	4	74
2900	363	5	80
2901	363	6	0
2902	363	7	0
2903	363	8	0
2904	364	1	50
2905	364	2	60
2906	364	3	70
2907	364	4	75
2908	364	5	80
2909	364	6	82
2910	364	7	0
2911	364	8	0
2912	365	1	60
2913	365	2	65
2914	365	3	70
2915	365	4	72
2916	365	5	75
2917	365	6	0
2918	365	7	0
2919	365	8	0
2920	366	1	0
2921	366	2	0
2922	366	3	0
2923	366	4	0
2924	366	5	0
2925	366	6	0
2926	366	7	0
2927	366	8	0
2928	367	1	0
2929	367	2	0
2930	367	3	0
2931	367	4	0
2932	367	5	0
2933	367	6	0
2934	367	7	0
2935	367	8	0
2936	368	1	0
2937	368	2	0
2938	368	3	0
2939	368	4	0
2940	368	5	0
2941	368	6	0
2942	368	7	0
2943	368	8	0
2944	369	1	0
2945	369	2	0
2946	369	3	0
2947	369	4	0
2948	369	5	0
2949	369	6	0
2950	369	7	0
2951	369	8	0
2952	370	1	0
2953	370	2	0
2954	370	3	0
2955	370	4	0
2956	370	5	0
2957	370	6	0
2958	370	7	0
2959	370	8	0
2960	371	1	0
2961	371	2	0
2962	371	3	0
2963	371	4	0
2964	371	5	0
2965	371	6	0
2966	371	7	0
2967	371	8	0
2968	372	1	0
2969	372	2	0
2970	372	3	0
2971	372	4	0
2972	372	5	0
2973	372	6	0
2974	372	7	0
2975	372	8	0
2976	373	1	0
2977	373	2	0
2978	373	3	0
2979	373	4	0
2980	373	5	0
2981	373	6	0
2982	373	7	0
2983	373	8	0
2984	374	1	0
2985	374	2	0
2986	374	3	0
2987	374	4	0
2988	374	5	0
2989	374	6	0
2990	374	7	0
2991	374	8	0
2992	375	1	0
2993	375	2	0
2994	375	3	0
2995	375	4	0
2996	375	5	0
2997	375	6	0
2998	375	7	0
2999	375	8	0
3000	376	1	0
3001	376	2	0
3002	376	3	0
3003	376	4	0
3004	376	5	0
3005	376	6	0
3006	376	7	0
3007	376	8	0
3008	377	1	0
3009	377	2	0
3010	377	3	0
3011	377	4	0
3012	377	5	0
3013	377	6	0
3014	377	7	0
3015	377	8	0
3016	378	1	0
3017	378	2	0
3018	378	3	0
3019	378	4	0
3020	378	5	0
3021	378	6	0
3022	378	7	0
3023	378	8	0
3024	379	1	0
3025	379	2	0
3026	379	3	0
3027	379	4	0
3028	379	5	0
3029	379	6	0
3030	379	7	0
3031	379	8	0
3032	380	1	0
3033	380	2	0
3034	380	3	0
3035	380	4	0
3036	380	5	0
3037	380	6	0
3038	380	7	0
3039	380	8	0
3040	381	1	0
3041	381	2	0
3042	381	3	0
3043	381	4	0
3044	381	5	0
3045	381	6	0
3046	381	7	0
3047	381	8	0
3048	382	1	0
3049	382	2	0
3050	382	3	0
3051	382	4	0
3052	382	5	0
3053	382	6	0
3054	382	7	0
3055	382	8	0
3056	383	1	0
3057	383	2	0
3058	383	3	0
3059	383	4	0
3060	383	5	0
3061	383	6	0
3062	383	7	0
3063	383	8	0
3064	384	1	0
3065	384	2	0
3066	384	3	0
3067	384	4	0
3068	384	5	0
3069	384	6	0
3070	384	7	0
3071	384	8	0
3072	385	1	0
3073	385	2	0
3074	385	3	0
3075	385	4	0
3076	385	5	0
3077	385	6	0
3078	385	7	0
3079	385	8	0
3080	386	1	40
3081	386	2	50
3082	386	3	60
3083	386	4	68
3084	386	5	75
3085	386	6	79
3086	386	7	82
3087	386	8	0
\.


--
-- Data for Name: pump_names; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.pump_names (id, pump_id, sequence_order, pump_name) FROM stdin;
1	1	1	100-200 2F;100-200 2F;100-200 2F;100-200 2F;100-200 2F
2	2	1	100-200 2F;100-200 2F;100-200 2F;100-200 2F;100-200 2F
3	3	1	100-200 CAISION
4	4	1	100-250 2F;100-250 2F;100-250 2F
5	5	1	100-250 2F;100-250 2F;100-250 2F;100-250 2F;100-250 2F
6	6	1	100-315 2F;100-315 2F;100-315 2F;100-315 2F
7	7	1	100-400;100-400;100-400;100-400
8	8	1	100-150 Multistage
9	9	1	100-80-250;100-80-250;100-80-250
10	10	1	10/12 BLE
11	11	1	10/12 DESC;10/12 DESC
12	12	1	10/12 DME;10/12 DME;10/12 DME
13	13	1	10/12 GME;10/12 GME;10/12 GME
14	14	1	10 ADM;10 ADM
15	15	1	10 NHTB
16	16	1	10 WLN 18A;10 WLN 18A
17	17	1	10 WLN 22A;10 WLN 22A
18	18	1	10 WLN 26A;10 WLN 26A;10 WLN 26A
19	19	1	10 WLN 32A;10 WLN 32A;10 WLN 32A
20	20	1	10 WO 2P
21	21	1	10 WO 4P
22	22	1	11 MQ H 1100VLT;11 MQ H 1100VLT;11 MQ H 1100VLT
23	23	1	11 MQ H 1100VLT;11 MQ H 1100VLT;11 MQ H 1100VLT
24	24	1	1200MF
25	25	1	125-100-250;125-100-250;125-100-250
26	26	1	125-100-315;125-100-315;125-100-315
27	27	1	125-250 2F;125-250 2F;125-250 2F;125-250 2F;125-250 2F;125-250 2F
28	28	1	125-315 2F;125-315 2F;125-315 2F;125-315 2F
29	29	1	125-400 2F;125-400 2F;125-400 2F
30	30	1	12/10 AH WARMAN SLURRY
31	31	1	14/12BDY;14/12BDY
32	32	1	12/14 BLE
33	33	1	12/14 DESC;12/14 DESC
34	34	1	12/14 DME;12/14 DME;12/14 DME
35	35	1	12/14 DME;12/14 DME;12/14 DME
36	36	1	12/15 V.S.M.F.V
37	37	1	12 HC 1133 4P
38	38	1	12 HC 1134 4P
39	39	1	12 HC;12 HC;12 HC
40	40	1	12 LC 4P
41	41	1	12 LC 9stg (Test Results)
42	42	1	12 LNH 21A;12 LNH 21A;12 LNH 21A
43	43	1	12 LNH 21B;12 LNH 21B;12 LNH 21B
44	44	1	12 MC 4P
45	45	1	12 WLN 14A;12 WLN 14A;12 WLN 14A
46	46	1	12 WLN 14B;12 WLN 14B;12 WLN 14B
47	47	1	12 WLN 17A;12 WLN 17A;12 WLN 17A
48	48	1	12 WLN 17B;12 WLN 17B;12 WLN 17B
49	49	1	12 WLN 21A;12 WLN 21A;12 WLN 21A;12 WLN 21A
50	50	1	12 WLN 21B;12 WLN 21B;12 WLN 21B
51	51	1	12X16X23H DSJH
52	52	1	14/12BDY;14/12BDY
53	53	1	14/16 ADM;14/16 ADM
54	54	1	14/16 BLE;14/16 BLE
55	55	1	14/18 EME;14/18 EME;14/18 EME
56	56	1	14 HC 1203 4P
57	57	1	14 HC 1204 4P
58	58	1	14 MC 6970
59	59	1	14 MC 755  4P
60	60	1	14 MC 756  4P
61	61	1	14 MC 757  4P
62	62	1	14 WLN 19A;14 WLN 19A
63	63	1	150-125-250;150-125-250;150-125-250
64	64	1	150-125-315
65	65	1	150-125-400;150-125-400;150-125-400
66	66	1	150-150-200;150-150-200;150-150-200;150-150-200
67	67	1	150-150-200 10Deg;150-150-200 10Deg;150-150-200 10Deg
68	68	1	150-200 2F;150-200 2F;150-200 2F;150-200 2F;150-200 2F
69	69	1	150-250 2F;150-250 2F;150-250 2F
70	70	1	150-315 2F;150-315 2F;150-315 2F;150-315 2F
71	71	1	150-400 2F;150-400 2F;150-400 2F;150-400 2F;150-400 2F;150-400 2F
72	72	1	16 HC 1262 4P
73	73	1	16 HC 1262 6P
74	74	1	16 HC 1264 4P
75	75	1	16 HC 1264 6P
76	76	1	16 WLN 23C;16 WLN 23C;16 WLN 23C
77	77	1	16 WLN 28C;16 WLN2 8C;16 WLN 28C
78	78	1	16 WLN 35 C;16 WLN 35 C;16 WLN 35 C
79	79	1	18/16 BDM;18/16 BDM
80	80	1	18/20 DME;18/20 DME;18/20 DME
81	81	1	18/22 MEDIVANE;18/22 MEDIVANE;18/22 MEDIVANE
82	82	1	18 HC 1213 4P
83	83	1	18 HC 1213 4P SABS
84	84	1	18 HC 1213 6P
85	85	1	18 HC 1214 4P
86	86	1	18 HC 1214 4P 6ST SABS
87	87	1	18 HC 1214 4P SABS
88	88	1	18 HC 1214 6P
89	89	1	18 HC + 18 XHC SPECIAL
90	90	1	18 XHC 2185 4P
91	91	1	18 XHC 2185 6P
92	92	1	18 XHC 2186 4P
93	93	1	18 XHC 2186 6P
94	95	1	1.5X2X10.5 H;1.5X2X10.5 H
95	96	1	1.5X2X8.5 H
96	97	1	200-150-315;200-150-315;200-150-315
97	98	1	200-150-315;200-150-315;200-150-315
98	99	1	200-150-400;200-150-400;200-150-400
99	100	1	200-150-400;200-150-400;200-150-400
100	101	1	200-150-450;200-150-450;200-150-450
101	102	1	200-150-460;200-150-460;200-150-460
102	103	1	200-200-250;200-200-250;200-200-250;200-200-250
103	104	1	200-200-250;200-200-250;200-200-250;200-200-250
104	105	1	200-200-250 10Deg;200-200-250 10Deg;200-200-250 10Deg
105	106	1	200-200-250 10deg;200-200-250 10deg;200-200-250 10deg
106	107	1	200-200-310;200-200-310;200-200-310;200-200-310 
107	108	1	200-200-310;200-200-310;200-200-310;200-200-310 
108	109	1	200-200-310 10deg;200-200-310 10deg;200-200-310 10deg
109	110	1	200-200-310 10deg;200-200-310 10deg;200-200-310 10deg
110	111	1	200-200-350;200-200-350;200-200-350
111	112	1	200-200-430;200-200-430;200-200-430
112	113	1	200-200-430;200-200-430;200-200-430
355	356	1	SCP 150/580HA-132/4
113	114	1	200-200-540;200-200-540;200-200-540
114	115	1	20-24 CME;20-24 CME
115	116	1	500/600 CME;500/600 CME
116	117	1	20/24 DV CME
117	118	1	20/24 DV MEDI
118	119	1	20 D.S
119	120	1	20 WLN 22A;20 WLN 22A;20 WLN 22A
120	121	1	20 WLN 22A;20 WLN 22A ;20 WLN 22A
121	122	1	20 WLN 22B;20 WLN 22B;20 WLN 22B
122	123	1	20 WLN 26A;20 WLN 26A;20 WLN 26A
123	124	1	20 WLN 26B;20 WLN 26B;20 WLN 26B
124	125	1	20 WLN 28B ;20 WLN 28B ;20 WLN 28B
125	126	1	20 WLN 28B;20 WLN 28B ;20 WLN 28B 
126	127	1	20 WLN 28C;20 WLN 28C;20 WLN 28C
127	128	1	24 WLN 26A
128	129	1	24 WLN 34A;24 WLN 34A;24 WLN 34A
129	130	1	24 WLN 42A;24 WLN 42A;24 WLN 42A
130	131	1	24 WLN 46A;24 WLN 46A;24 WLN 46A
131	132	1	250-200-480;250-200-480;250-200-480
132	133	1	250-200-480;250-200-480;250-200-480
133	134	1	250-200-610;250-200-610;250-200-610
134	135	1	250-200-610;250-200-610;250-200-610
135	136	1	250-250-360;250-250-360;250-250-360;250-250-360
136	137	1	250-250-360 6P-2;250-250-360 6P-2;250-250-360 6P-2;250-250-360 6P-2;250-250-360 6P-2
137	138	1	250-250-360 10Deg;250-250-360 10Deg;250-250-360 10Deg
138	139	1	250-250-360 10deg;250-250-360 10deg;250-250-360 10deg
139	140	1	250-250-400;250-250-400;250-250-400;250-250-400
140	141	1	250-250-400;250-250-400;250-250-400;250-250-400;250-250-400 
141	142	1	250-250-400 10Deg;250-250-400 10Deg;250-250-400 10Deg
142	143	1	250-250-400 10deg;250-250-400 10deg;250-250-400 10Deg
143	144	1	250-250-450;250-250-450;250-250-450
144	145	1	250-250-450;250-250-450;250-250-450
145	146	1	250-250-540;250-250-540;250-250-540
146	147	1	250-250-540;250-250-540;250-250-540
147	148	1	250/300 BST;250/300 BST;250/300 BST;250/300 BST
148	149	1	250/450
149	150	1	28 HC 6P;28 HC
150	151	1	28 HC 8P;28 HC
151	152	1	2.5 K;2.5 K
152	153	1	2.5 KL;2.5 KL
153	154	1	2 K;2 K
154	155	1	2 KL;2 KL
155	156	1	300-250-600
156	157	1	30 HC;30 HC
157	158	1	30 WLN 30C;30 WLN 30C;30 WLN 30C
158	159	1	30 WLN 41C;30 WLN 41C;30 WLN 41C
159	160	1	32-200 2F;32-200 2F;32-200 2F;32-200 2F;32-200 2F
160	161	1	32-300 2F;32-300 2F;32-300 2F
161	162	1	32 HC 6P;32 HC 6P
162	163	1	32 HC;32 HC
163	164	1	32 XHC 6P;32 XHC 6P
164	165	1	32 XHC;32 XHC
165	166	1	350-300-429 DESC;350-300-429 DESC;350-300-429 DESC
166	167	1	36 HC 6P;36 HC 6P
167	168	1	36 XHC;36 XHC
168	169	1	3/40I;3/40I;3/40I;3/40I
169	170	1	3/4 MEDI
170	171	1	3 K;3 K
171	172	1	3WLN12K;3WLN12K;3WLN12K
172	173	1	3X4X10.5 H SJA
173	174	1	400-300-435
174	175	1	400-600
175	176	1	4503-42936;4503-42936;4503-42936
176	177	1	4503-42937;4503-42937;4503-42937
177	178	1	4503_44648;4503_44648;4503_44648
178	179	1	4503_44649;4503_44649;4503_44649
179	180	1	4503-44786;4503-44786;4503-44786
180	181	1	4503-44787;4503-44787;4503-44787
181	182	1	4504-42564;4504-42564;4504-42564
182	183	1	4504-42565;4504-42565;4504-42565
183	184	1	4505-48159;4505-48159;4505-48159
184	185	1	4505-48190;4505-48190;4505-48190
185	186	1	4506-48170;4506-48170;4506-48170
186	187	1	4506-48171;4506-48171;4506-48171
187	188	1	4625-38112
188	189	1	48/48 LONOVANE;48/48 LONOVANE;48/48 LONOVANE
189	190	1	4/40 GME;4/40 GME;4/40 GME;4/40 GME
190	191	1	4/5;4/5
191	192	1	4/5 2 STAGE MEDI
192	193	1	4/5 ALE;4/5 ALE;4/5 ALE
193	194	1	4/5 BLE;4/5 BLE;4/5 BLE
194	195	1	4/5 CME;4/5 CME;4/5 CME
195	196	1	4/5 DME;4/5 DME;4/5 DME
196	197	1	4/5 MEDI
197	198	1	4K;4K;4K
198	199	1	4x6x13.25 H-SJA
199	200	1	4X6X13.25 L GSJH;4X6X13.25 L GSJH
200	201	1	4X6X8.5 L SJA
201	202	1	50-160 2F;50-160 2F;50-160 2F
202	203	1	50-160 2F;50-160 2F;50-160 2F
203	204	1	50-200 2F;50-200 2F;50-200 2F;50-200 2F;50-200 2F
204	205	1	50-200 2F;50-200 2F;50-200 2F;50-200 2F
205	206	1	50-250 2F;50-250 2F;50-250 2F;50-250 2F
206	207	1	50-250 2F;50-250 2F;50-250 2F
207	208	1	50-315 2F;50-315 2F
208	209	1	5/6;5/6
209	210	1	5/6 ALE;5/6 ALE;5/6 ALE
210	211	1	5/6 BLE;5/6 BLE;5/6 BLE
211	212	1	5/6 CME;5/6 CME;5/6 CME
212	213	1	5/6 DME;5/6 DME;5/6 DME
213	214	1	5/6 MEDI;5/6 MEDI;5/6 MEDI
214	215	1	5/6 MEDI;5/6 MEDI;5/6 MEDI
215	216	1	5/6 MEDIVANE;5/6 MEDIVANE;5/6 MEDIVANE
216	217	1	5/6 MEDIVANE;5/6 MEDIVANE;5/6 MEDIVANE
217	218	1	5 K;5 K
218	219	1	5 KL;5 KL
219	220	1	5X6 HSC
220	221	1	65-125 2F;65-125 2F;65-125 2F;65-125 2F
221	222	1	65-160 2F;65-160 2F;65-160 2F;65-160 2F;65-160 2F
222	223	1	65-160 2F;65-160 2F;65-160 2F;65-160 2F;65-160 2F
223	224	1	65-200 1F
224	225	1	65-200 2F;65-200 2F;65-200 2F
225	226	1	65-200 2F;65-200 2F;65-200 2F;65-200 2F;65-200 2F
226	227	1	65-250 2F;65-250 2F;65-250 2F
227	228	1	65-250 2F;65-250 2F;65-250 2F;65-250 2F;65-250 2F
228	229	1	65-315 2F;65-315 2F;65-315 2F;65-315 2F
229	230	1	6/8 ALE;6/8 ALE;6/8 ALE
230	231	1	6/8 DME;6/8 DME
231	232	1	6/8 DMP;6/8 DMP
232	233	1	6/8 EME;6/8 EME;6/8 EME;6/8 EME
233	234	1	6/8 GME
234	235	1	6 B/B;6 B/B
235	236	1	6 HC
236	237	1	6K 6 VANE;6K 6 VANE
237	238	1	6 K 8 VANE;6 K 8 VANE
238	239	1	6 KL;6 KL
239	240	1	6 LC
240	241	1	6 MC
241	242	1	6 SLM 2P
242	243	1	6 WLN 18A;6 WLN 18A;6 WLN 18A
243	244	1	6 WLN 21A;6 WLN 21A;6 WLN 21A
244	245	1	6 XLC
245	246	1	6X8X11L DSJA
246	247	1	6X8X13H SJA;6X8X13H SJA
247	248	1	700-600-710;700-600-710;700-600-710
248	249	1	700-600-710;700-600-710;700-600-710
249	250	1	7 KL;7 KL
250	251	1	7 MC
251	252	1	80-160 2F;80-160 2F;80-160 2F
252	253	1	80-160 2F;80-160 2F;80-160 2F;80-160 2F
253	254	1	80-200 2F;80-200 2F;80-200 2F;80-200 2F;80-200 2F
254	255	1	80-200 2F;80-200 2F;80-200 2F
255	256	1	80-250 2F;80-250 2F;80-250 2F;80-250 2F;80-250 2F;80-250 2F
256	257	1	80-250 2F;80-250 2F;80-250 2F;80-250 2F
257	258	1	80-315 2F;80-315 2F;80-315 2F;80-315 2F
258	259	1	80-50-315;80-50-315;80-50-315
259	260	1	80-50-315;80-50-315;80-50-315
260	261	1	8211-16 970
261	262	1	8211-30
262	263	1	8312-14
263	264	1	8312-14 310F
264	265	1	8312-14 311F
265	266	1	8312-14 311T
266	267	1	8312-14 312T
267	268	1	8312-14 313T
268	269	1	8312-14 313T
269	270	1	8312-16 312T
270	271	1	8312-16 370F
271	272	1	8312-16 371T
272	273	1	8312-16 372T
273	274	1	8312-16 373T
274	275	1	8312-20 340F
275	276	1	8312-20 341T
276	277	1	8312-20 342T
277	278	1	8312-20 343T
278	279	1	8312-24 360F
279	280	1	8312-24 361T
280	281	1	8312-24 362T
281	282	1	8312-24 363T
282	283	1	8312-30 A330F
283	284	1	8312-30 A331T
284	285	1	8312-30 A332T
285	286	1	8312-30 A333T
286	287	1	8312 -10 B1431T
287	288	1	8312 -10 B1433T
288	289	1	8314-5
289	290	1	8/10 BLE;8/10 BLE;8/10 BLE;8/10 BLE;8/10 BLE
290	291	1	8/10 CME - TA
291	292	1	8/10 CME - TB
292	293	1	8/10 DESC;8/10 DESC
293	294	1	8/10 DME;8/10 DME
294	295	1	8/10 GME;8/10 GME;8/10 GME;8/10 GME
295	296	1	8/8 CME
296	297	1	8/8 CME 1900rpm
297	298	1	8/8 DME;8/8 DME;8/8 DME;8/8 DME
298	299	1	8/8 GME 4P;8/8 GME 4P;8/8 GME
299	300	1	8 B/B;8 B/B
300	301	1	8 DESC;8 DESC
301	302	1	8 HC
302	303	1	8 K;8 K
303	304	1	8 KL;8 KL
304	305	1	8 LC
305	306	1	8 MC
306	307	1	8 SLH 2P
307	308	1	8 WLN 18A;8 WLN 18A;8 WLN 18A
308	309	1	8 WLN 18C;8 WLN 18C;8 WLN 18C
309	310	1	8 WLN 21A;8 WLN 21A
310	311	1	8 LN 29B;8 LN 29B;8 LN 29B
311	312	1	8X10X13 2S
312	313	1	8X10X13 2S NEW
313	314	1	8X10X13 3S
314	315	1	8X10X13 3S NEW
315	316	1	8X10X13 4S
316	317	1	8X10X13 4S2P
317	318	1	8X10X13 4S NEW
318	319	1	9-11 2 STAGE MEDIVANE
319	320	1	APE DWU-150 BC;APE DWU-150 BC;APE DWU-150 BC;APE DWU-150 BC
320	321	1	APE DWU - 150;APE DWU - 150;APE DWU - 150;APE DWU - 150
321	322	1	BDM 16/14;BDM 16/14
322	323	1	DVMS 4000-125
323	324	1	FD 300-250-400
324	325	1	HMS 50/4
325	326	1	KL 150-100
326	327	1	MISO 100-200
327	328	1	MISO 65-315H
328	329	1	Morgenstond 1
329	330	1	MSD 10x10x13.5 3
330	331	1	MSD 10x10x13.5 3
331	332	1	MSJ
332	333	1	Nitz 100-80-250;Nitz 100-80-250
333	334	1	PJ 100;PJ 100
334	335	1	PJ 100 AS;PJ 100 AS;PJ 100 AS
335	336	1	PJ 150 AN
336	337	1	PJ 150 AS
337	338	1	PJ 200
338	339	1	PJ 200 AS
339	340	1	PJ 250 AN;PJ 250 AN;PJ 250 AN
340	341	1	PJ 250 AS;PJ 250 AS;PJ 250 AS
341	342	1	PJ 250 BS;PJ 250 BS;PJ 250 BS
342	343	1	PJ 250 H;PJ 250 H
343	344	1	PJ 258 H;PJ 258 H
344	345	1	PJ 80
345	346	1	PJ 80 AS;PJ 80 AS;PJ 80 AS
346	347	1	PL 100 AN;PL 100 AN;PL 100 AN
347	348	1	PL 100 AS;PL 100 AS;PL 100 AS
348	349	1	PL 150 AN;PL 150 AN;PL 150 AN
349	350	1	PL 150 AS;PL 150 AS;PL 150 AS;PL 150 AS
350	351	1	PL 200 AN;PL 200 AN
351	352	1	PL 200 AS;PL 200 AS;PL 200 AS
352	353	1	PL 80 AN;PL 80 AN
353	354	1	PL 80 AS;PL 80 AS;PL 80 AS
354	355	1	QW400-26-45
356	357	1	SCP 250/450HA
357	358	1	Umgeni Verulam July 2022
358	359	1	VBK 35-22 3 Stage
359	360	1	VBK 35-22.5 3 STAGE
360	361	1	VBK 420/018-4S
361	362	1	VBK 620/022-4S
362	363	1	VBK 620/022-4S (Test Curve)
363	364	1	WI-1414
364	365	1	WVP-130-30 (P30)
365	366	1	WXH-100-240;WXH-100-240
366	367	1	WXH-150-300
367	368	1	WXH-32-132;WXH-32-132
368	369	1	WXH-32-135;WXH-32-135
369	370	1	WXH-34-35-100;WXH-34-35-100
370	371	1	WXH-40-135;WXH-40-135
371	372	1	WXH-40-135 2P;WXH-40-135 2P
372	373	1	WXH-50-160;WXH-50-160
373	374	1	WXH-50-160 2P
374	375	1	WXH-64-100-150;WXH-64-100-150
375	376	1	WXH-64-100-150B;WXH-64-100-150B
376	377	1	WXH-64-125-150A;WXH-64-125-150A
377	378	1	WXH-64-32-50;WXH-64-32-50
378	379	1	WXH-34-35-100;WXH-34-35-100
379	380	1	WXH-64-40-65;WXH-64-40-65
380	381	1	WXH-64-80-125;WXH-64-80-125
381	382	1	WXH-65-185;WXH-65-185
382	383	1	WXH-65-185 2P;WXH-65-185 2P
383	384	1	WXH-80-210;WXH-80-210
384	385	1	WXH-80-210 2P;WXH-80-210 2P
385	386	1	XF18
\.


--
-- Data for Name: pump_performance_points; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.pump_performance_points (id, curve_id, operating_point, flow_rate, head, efficiency, npshr) FROM stdin;
1	1	1	0	9.3	0	2.4
2	1	2	57.1	9.1	60	2.4
3	1	3	67.3	9	65	2.5
4	1	4	100.7	7.9	70	3.7
5	1	5	125.9	6.3	65	5.7
6	1	6	133.1	5.7	62	6.3
7	2	1	0	10.98	0	2.4
8	2	2	58.6	10.8	60	2.4
9	2	3	67.9	10.6	65	2.4
10	2	4	81.2	10.3	70	2.9
11	2	5	100.7	9.7	74	3.7
12	2	6	108.5	9.3	75	4
13	2	7	116.7	8.9	74	4.4
14	2	8	134.2	7.7	70	6.2
15	2	9	145.5	6.8	65	6.8
16	2	10	148	6.6	63	7.5
17	3	1	0	12.7	0	2.4
18	3	2	61.2	12.6	60	2.5
19	3	3	80.2	12.4	70	2.5
20	3	4	105.9	11.6	77	3.2
21	3	5	119.8	11	78.5	3.8
22	3	6	134.7	10.2	77	4.8
23	3	7	148.6	9.2	74	6
24	3	8	156.3	8.4	70	6.5
25	3	9	166.5	7.4	64.85	7.3
26	4	1	0	14	0	2.4
27	4	2	63.7	14	60	2.4
28	4	3	84.3	14	70	2.6
29	4	4	106.9	13.5	77	3
30	4	5	123.4	13	80	3.5
31	4	6	132.6	12.5	80.75	4
32	4	7	141.4	12.1	80	4.7
33	4	8	158.8	10.8	77	5.3
34	4	9	167.1	10	74	6
35	4	10	174.8	9.2	70	7
36	4	11	182	8.4	65	7.6
37	5	1	0	15	0	2.5
38	5	2	66.3	15	60	2.1
39	5	3	76.6	15	65	2.2
40	5	4	100.2	14.9	74	2.5
41	5	5	125.9	14.4	80	3.5
42	5	6	141.4	13.8	81	4
43	5	7	158.3	12.9	80	5
44	5	8	171.7	11.7	77	6.3
45	5	9	187.6	9.8	70	7.9
46	5	10	194.8	8.9	64	8
47	6	1	0	40.5	0	3
48	6	2	109.7	40.5	60	3
49	6	3	129.4	40	65	2.9
50	6	4	164.6	37.9	70	3
51	6	5	199.8	34.8	72.42	3.2
52	6	6	231.9	31.3	70	4.1
53	6	7	261.9	27.1	65	6
54	6	8	273.3	25.4	64	7.6
55	7	1	0	45.6	0	3
56	7	2	111.8	45.5	60	3
57	7	3	131.5	45.2	65	2.9
58	7	4	158.4	43.9	70	3
59	7	5	202.9	41.2	74	3
60	7	6	223.6	39.2	75.85	3.8
61	7	7	245.4	37	74	4.8
62	7	8	283.7	31.8	70	6.7
63	7	9	303.3	28.7	65	8.4
64	8	1	0	51.1	0	3
65	8	2	114.9	51	60	3
66	8	3	134.6	50.7	64	2.9
67	8	4	156.3	50	70	2.9
68	8	5	186.4	48.8	74	3.3
69	8	6	221.6	46.6	77	3.7
70	8	7	244.3	44.4	78.54	4.1
71	8	8	263	42.2	77	4.9
72	8	9	293	37.9	74	6.5
73	8	10	315.8	34	70	7.6
74	8	11	328.2	30.7	65	9.2
75	9	1	0	56.6	0	3
76	9	2	118	56.8	60	2.9
77	9	3	138.7	56.6	65	3.2
78	9	4	158.4	56.3	70	3.2
79	9	5	181.2	55.7	74	3
80	9	6	208.1	54.6	77	3.3
81	9	7	256.8	50.7	80.85	4.4
82	9	8	310.6	43.9	77	6.3
83	9	9	327.2	40.9	74	7.9
84	9	10	344.8	37.8	70	8.7
85	9	11	359.2	34.3	65	9.8
86	10	1	0	64.3	0	2.9
87	10	2	125.3	64.5	60	3
88	10	3	166.7	64.5	70	3
89	10	4	183.2	64.3	74	3.2
90	10	5	208.1	63.9	77	3.5
91	10	6	230.9	62.9	80	3.2
92	10	7	261.9	61	82	4
93	10	8	281.6	59.5	82.5	4.6
94	10	9	299.2	57.1	82	5.1
95	10	10	324	53.7	80	5.9
96	10	11	344.8	49.7	77	6.8
97	10	12	360.3	46.3	74	8.3
98	10	13	381	40.8	68	9.5
99	11	1	0	24.9	0	1.5
100	11	2	35	23.9	47	1.6
101	11	3	68	23.7	65	1.8
102	11	4	85	22	68	2.1
103	11	5	98	18.9	65	2.5
104	11	6	115	14.9	55	3.9
105	11	7	125	10.9	44	5.3
106	12	1	0	16	0	1.2
107	12	2	41.9	16	55	1.2
108	12	3	58.1	16	65	1.2
109	12	4	68.1	15.9	70	1.2
110	12	5	96.4	14.8	75.22	1.6
111	12	6	133	11.6	70	2.8
112	12	7	144	10.2	65	3.3
113	12	8	153	9	60	3.9
114	12	9	154.5	8.6	59	4.1
115	13	1	0	20.3	0	1.2
116	13	2	45.6	20.4	55	1.2
117	13	3	52.4	20.4	60	1.2
118	13	4	72.3	20.3	70	1.2
119	13	5	91.1	19.8	75	1.4
120	13	6	105.3	19.1	77	1.6
121	13	7	113.7	18.6	77.35	1.7
122	13	8	123.1	17.9	77	1.9
123	13	9	137.8	16.6	75	2.3
124	13	10	158.2	14.1	70	3
125	13	11	169.2	12.4	65	3.6
126	13	12	178.6	10.9	60	4.8
127	13	13	179.7	10.6	59	5.3
128	14	1	0	24.3	0	1.2
129	14	2	49.2	24.3	55	1.2
130	14	3	66.5	24.3	65	1.2
131	14	4	94.8	23.7	75	1.2
132	14	5	105.8	23.2	77	1.4
133	14	6	115.2	22.6	78	1.4
134	14	7	125.2	22	78.5	1.4
135	14	8	137.2	21.2	78	1.6
136	14	9	146.7	20.5	77	1.9
137	14	10	161.3	19.1	75	2.2
138	14	11	181.8	16.8	70	3.1
139	14	12	194.9	15	65	4.7
140	14	13	205.3	13.5	60	6.7
141	15	1	0	68.3	0	2.7
142	15	2	71.5	68.4	50	2.7
143	15	3	103.3	68.4	60	2.7
144	15	4	119.2	68.3	65	2.7
145	15	5	139.1	67.7	70	2.7
146	15	6	159.9	66.4	73	2.9
147	15	7	183.7	64.2	76	2.9
148	15	8	214.5	60.3	77.85	3
149	15	9	242.3	55.6	76	3.7
150	15	10	262.2	51.2	73	4.4
151	15	11	267.2	50	72.58	4.8
152	16	1	0	75.3	0	2.9
153	16	2	75.5	75.5	50	2.7
154	16	3	107.3	75.5	60	2.7
155	16	4	125.1	75.5	65	2.7
156	16	5	145	75.2	70	2.7
157	16	6	162.9	74.4	73	2.9
158	16	7	186.7	72.8	76	2.9
159	16	8	232.4	67.3	78.75	3.5
160	16	9	271.2	60	76	4.4
161	16	10	288	56.4	73	5.2
162	16	11	308.9	50.8	70	6.7
163	17	1	0	83.9	0	2.7
164	17	2	81.4	83.9	50	2.7
165	17	3	112.2	84.1	60	2.7
166	17	4	153	83.9	70	2.7
167	17	5	169.8	83.3	73	2.9
168	17	6	192.7	81.7	76	3
169	17	7	219.5	79.2	78	3.3
170	17	8	245.3	75.8	80.75	3.7
171	17	9	273.1	71.1	78	4.6
172	17	10	298	65.8	76	5.4
173	17	11	310.9	62.3	73	5.9
174	17	12	332.7	55.8	69.98	7
175	18	1	0	91.4	0	2.9
176	18	2	87.4	91.6	50	2.7
177	18	3	118.2	91.7	60	2.7
178	18	4	139.1	91.7	65	2.7
179	18	5	177.8	90.9	73	2.9
180	18	6	199.6	89.5	76	3
181	18	7	221.5	87.8	78	3.3
182	18	8	256.3	83.4	80.75	3.8
183	18	9	297	76.2	78	5.1
184	18	10	317.8	71.6	76	5.7
185	18	11	329.8	68.3	73	6
186	18	12	351.6	61.7	69.86	7
187	19	1	0	99.7	0	2.9
188	19	2	93.4	99.8	50	2.9
189	19	3	124.2	100	60	2.7
190	19	4	169.8	99.8	70	2.9
191	19	5	208.6	97.8	76	3.2
192	19	6	226.5	96.4	78	3.2
193	19	7	245.3	94.5	80	3.5
194	19	8	282.1	89.2	81.5	4.1
195	19	9	303.9	85.3	80	4.9
196	19	10	318.8	82.3	78	5.1
197	19	11	336.7	78.4	76	5.9
198	19	12	367.5	69.8	70	7.3
199	20	1	0	26.1	0	2.5
200	20	2	70.2	26	60	2.5
201	20	3	109.4	25.9	70	2.5
202	20	4	130.6	25.4	75	2.5
203	20	5	168.3	23.8	78.1	2.5
204	20	6	200.8	21.1	75	3
205	20	7	241.5	16.2	71	7
206	21	1	0	33.1	0	1.5
207	21	2	74.7	33.1	60	1.5
208	21	3	110.9	33	70	1.6
209	21	4	132.8	33	75	2
210	21	5	173.6	31.9	80	2.5
211	21	6	191.7	30.9	80.85	3
212	21	7	206	29.7	80	2.7
213	21	8	228.7	27.7	78	3.9
214	21	9	251.3	25.3	75	6.2
215	21	10	261.6	24	73	7.4
216	22	1	0	36.9	0	1.5
217	22	2	78.2	36.9	60	1.5
218	22	3	114	36.8	70	1.6
219	22	4	135.9	36.7	75	1.7
220	22	5	155.6	36.5	78	1.7
221	22	6	170.2	36.1	80	1.8
222	22	7	192.9	35	81.25	2.3
223	22	8	226.5	32.4	80	3.5
224	22	9	241.8	30.9	78	4.1
225	22	10	266.7	28.2	75	6.1
226	22	11	272.5	27.2	74	7.1
227	23	1	0	41.2	0	1.5
228	23	2	84.7	41.1	60	1.5
229	23	3	121.3	41	70	1.8
230	23	4	143.2	41	75	1.8
231	23	5	160.7	40.8	78	1.9
232	23	6	173.9	40.4	80	1.9
233	23	7	192.9	39.5	81	2
234	23	8	204.6	38.6	81.5	2.1
235	23	9	215.5	37.7	81	2.3
236	23	10	238.2	35.7	80	3.2
237	23	11	252.1	34.2	78	4.1
238	23	12	276.2	31.5	75	6.1
239	23	13	283.5	30.9	74	6.8
240	24	1	0	39.4	0	1.5
241	24	2	54.8	39.7	50	1.5
242	24	3	77.4	39.5	60	1.5
243	24	4	91.6	39.1	65	1.5
244	24	5	114.9	38.5	70	1.7
245	24	6	165.3	35.4	74.35	2.5
246	24	7	200.6	31.9	72	3.8
247	24	8	217.8	29.3	70	4.8
248	25	1	0	48.7	0	1.4
249	25	2	60.1	48.8	50	1.5
250	25	3	71.4	48.8	55	1.5
251	25	4	99.2	48.5	65	1.5
252	25	5	151.7	47	74	2.3
253	25	6	184	45	75.55	2.9
254	25	7	213.3	42.4	74	3.8
255	25	8	230.6	40.4	72	4.6
256	25	9	248.6	37.7	70	5.4
257	25	10	253.1	36.9	69	6.3
258	26	1	0	54.2	0	1.5
259	26	2	63.8	54.3	50	1.5
260	26	3	90.1	54.3	60	1.5
261	26	4	129.2	53.5	70	1.7
262	26	5	156.2	52.6	74	2.2
263	26	6	199.1	49.9	77.45	2.8
264	26	7	229.9	46.8	74	4.3
265	26	8	244.9	45	72	5.1
266	26	9	264.4	42.1	70	6.2
267	26	10	270.4	40.6	68	7.2
268	27	1	0	60.2	0	1.5
269	27	2	69.9	60.4	50	1.5
270	27	3	83.4	60.4	55	1.5
271	27	4	117.2	59.9	65	1.7
272	27	5	163	58.4	74	2.3
273	27	6	193.8	56.7	76	2.6
274	27	7	206.6	55.8	76.45	3.1
275	27	8	220.8	54.5	76	3.5
276	27	9	246.4	51.6	74	4.6
277	27	10	258.4	49.9	72	5.1
278	27	11	279.4	46.7	70	6
279	27	12	287.7	44.9	67	6.6
280	28	1	0	480	0	1.65
281	28	2	10	471	38	1.65
282	28	3	20	462	60	1.7
283	28	4	30	440	70	1.8
284	28	5	40	404	73.8	2.1
285	28	6	50	350	73.8	2.5
286	28	7	52	340	73	2.6
287	29	1	0	14	0	1
288	29	2	17.4	14.6	45	1
289	29	3	25.1	14.5	60	1
290	29	4	36.4	14.1	75	1
291	29	5	45.6	13.3	78.4	1.35
292	29	6	55.1	12.1	75	2.3
293	29	7	63.4	11.1	70	3.3
294	30	1	0	21	0	1
295	30	2	9.3	21.3	30	1
296	30	3	19.1	21.4	50	1
297	30	4	38.1	21.1	70	1
298	30	5	58.5	19.1	78.2	1.25
299	30	6	71.4	17.4	75	2.1
300	30	7	81.1	15.9	70	3.3
301	31	1	0	29.5	0	1
302	31	2	10.8	29.9	30	1
303	31	3	21.5	30	50	1
304	31	4	32.6	29.9	60	1
305	31	5	56.5	28.6	74	1.1
306	31	6	73.7	26.3	72	2
307	31	7	86.9	24.1	68	3.3
308	32	1	0	53.64	0	0
309	32	2	250	51.82	40.08	0
310	32	3	500	49.38	66.28	4.88
311	32	4	750	45.72	82.36	5.49
312	32	5	1000	40.23	88.48	6.4
313	32	6	1250	32.92	82.55	7.92
314	33	1	0	103.1	0	0
315	33	2	247.1	100.2	46	0
316	33	3	473.8	94.2	70	0
317	33	4	584.1	89.6	75	0
318	33	5	706.7	82	76	0
319	33	6	795.6	75.1	75	0
320	33	7	899.7	64.9	70	0
321	33	8	961	58.5	65	0
322	34	1	0	126.3	0	0
323	34	2	228.7	123.1	46	0
324	34	3	437.1	117.9	70	0
325	34	4	565.8	112.3	75	0
326	34	5	768	101.6	79	0
327	34	6	942.6	86.6	75	0
328	34	7	1038	74.5	70	0
329	34	8	1096	66.1	65	0
330	35	1	0	72.4	0	4.6
331	35	2	113.56	68.4	70	4.7
332	35	3	154.17	66.7	78	5.4
333	35	4	192.87	64.9	82	5.9
334	35	5	254.15	59.9	87.5	7.1
335	35	6	289.13	55	84	7.9
336	35	7	310.03	51.5	83	8.4
337	36	1	0	90	0	4.6
338	36	2	121.58	85	70	4.8
339	36	3	161.46	83.7	78	5.1
340	36	4	198.96	82.4	82	5.6
341	36	5	284.13	75.6	88	6.7
342	36	6	315.48	70.4	86	7.3
343	36	7	354.31	61.4	83	8.5
344	37	1	0	109	0	4.6
345	37	2	134.84	102.7	70	4.8
346	37	3	176.5	101.6	78	5
347	37	4	217.59	99.9	82	5.3
348	37	5	310.93	91.1	88	6.5
349	37	6	355	83.2	86	7.5
350	37	7	387.7	76	83	8.5
351	38	1	0	167.6	0	0
352	38	2	482.6	153.9	70	0
353	38	3	613.2	149.4	78	0
354	38	4	709.7	144.8	82	0
355	38	5	840.3	137.2	86	0
356	38	6	1022	121.9	82	0
357	38	7	1136	106.7	79	0
358	39	1	0	219.5	0	0
359	39	2	511	202.7	70	0
360	39	3	613.2	196.6	78	0
361	39	4	749.4	192	82	0
362	39	5	965.2	178.3	86	0
363	39	6	1136	157	82	0
364	39	7	1249	143.3	79	0
365	40	1	0	246.9	0	1.83
366	40	2	545	225.6	70	1.83
367	40	3	681.3	221	78	1.83
368	40	4	772.1	216.4	82	1.98
369	40	5	959.5	198.1	86	2.44
370	40	6	1192	179.8	82	3.5
371	40	7	1340	155.5	79	4.57
372	41	1	0	33.8	0	3.9
373	41	2	120.2	33.2	33.5	3.9
374	41	3	272.7	31.7	60.7	3.9
375	41	4	408.5	29.6	75.6	5
376	41	5	558.2	26.1	81.6	7.1
377	41	6	665.2	22.9	80.6	8
378	41	7	788.4	17.5	76.7	11.3
379	42	1	0	57.4	0	3.9
380	42	2	357.2	53.5	61.8	3.9
381	42	3	608.4	47.8	81.1	4.1
382	42	4	793.4	41.6	84.8	4.4
383	42	5	976.6	34.1	78.9	6.1
384	42	6	1134	24	63.3	9.3
385	42	7	1217	17.3	50.8	11.3
386	43	1	0	77.72	0	2.44
387	43	2	590.52	65.53	60	2.44
388	43	3	1044.77	56.39	80	4.27
389	43	4	1453.6	46.48	84	7.01
390	43	5	1635.3	39.62	82	8.53
391	43	6	1873.78	32	74	10.06
392	43	7	2044.12	28.96	70	10.67
393	44	1	0	44.7	0	3
394	44	2	322.7	41.7	49	3.1
395	44	3	550.5	39.2	69.5	3.1
396	44	4	713.2	37.2	77	3.5
397	44	5	968.1	31.7	81	4.7
398	44	6	1112	27.6	79.7	5.9
399	44	7	1199	25.1	78	6.8
400	45	1	0	72.4	0	2.9
401	45	2	320	70.4	46	3.2
402	45	3	588.5	68.3	69.6	3.2
403	45	4	824.4	65.3	80	4
404	45	5	1204	55.8	86	6.8
405	45	6	1397	46.5	83.5	10.7
406	45	7	1524	37.7	79.5	14
407	46	1	0	68.5	0	2.5
408	46	2	282.4	66	40	2.5
409	46	3	637.4	62	70	2.8
410	46	4	774.3	59.5	75	3.2
411	46	5	1100	52.5	80	4.4
412	46	6	1288	46	78	4.9
413	46	7	1480	38.5	71.85	6
414	47	1	0	124.5	0	0
415	47	2	359.8	123	40	0
416	47	3	635.7	120.7	60	0
417	47	4	793.4	119	70	0
418	47	5	1000	116.7	78	0
419	47	6	1203	112.7	82	0
420	47	7	1345	109.4	84	0
421	47	8	1582	100.8	84	0
422	47	9	1720	93.6	82	0
423	47	10	1799	89.3	80	0
424	47	11	1912	80	74.8	0
425	48	1	0	88.8	0	0.9
426	48	2	401.6	84.7	45	1.4
427	48	3	821.3	77.6	70	2.3
428	48	4	1002	72.4	75	2.7
429	48	5	1300	60.2	78.5	3.6
430	48	6	1431	55.1	78	4.1
431	48	7	1652	42.9	74.85	5.5
432	49	1	0	135.9	0	0
433	49	2	405.7	132.7	40	0
434	49	3	816.4	127.1	70	0
435	49	4	973.6	123.5	75	0
436	49	5	1242	114	82	0
437	49	6	1562	98.8	81	0
438	49	7	1750	89.2	78	0
439	49	8	1881	82.5	74	0
440	50	1	0	170.4	0	0.9
441	50	2	401.6	168.4	40	1.3
442	50	3	893.5	160.2	70	2.5
443	50	4	1273	151	80	3.6
444	50	5	1552	139.8	82.5	4.9
445	50	6	1922	120.4	78	8.4
446	50	7	2049	114.3	74.85	10.3
447	51	1	0	76.7	0	0
448	51	2	410.4	75.3	55	0
449	51	3	800	71.2	74	0
450	51	4	929.9	68.5	76	0
451	51	5	1195	62.3	78.2	0
452	51	6	1392	56.2	76	0
453	51	7	1444	53.4	74	0
454	51	8	1507	50.7	72	0
455	52	1	0	85.6	0	0
456	52	2	426	84.2	55	0
457	52	3	836.4	79.5	74	0
458	52	4	950.6	77.4	76	0
459	52	5	1086	74	78	0
460	52	6	1226	70.5	78.55	0
461	52	7	1366	66.4	78	0
462	52	8	1486	61.6	76	0
463	52	9	1538	58.9	74	0
464	52	10	1590	56.2	72	0
465	53	1	0	95.2	0	3
466	53	2	451.9	93.2	55	3
467	53	3	888.3	87.7	74	3.2
468	53	4	971.4	85.6	76	3.3
469	53	5	1091	83.6	78	3.5
470	53	6	1294	78.1	79	4.2
471	53	7	1460	72.6	78	5.1
472	53	8	1564	67.8	76	6
473	53	9	1631	64.4	74	6.8
474	53	10	1678	61.6	72	7.8
475	54	1	50.4	43	23.6	0
476	54	2	75	41	35	0
477	54	3	125	38.1	51	0
478	54	4	200	32.7	65	0
479	54	5	270.6	26.6	69	0
480	54	6	338.3	20.2	65	0
481	54	7	400	12.6	52	0
482	55	1	25	10.75	27	0
483	55	2	32	10.5	30	0
484	55	3	63.3	9.5	52	0
485	55	4	101.1	8.1	65	0
486	55	5	132.4	6.6	69	0
487	55	6	175.6	4.5	63	0
488	55	7	200.3	3	52	0
489	56	1	0	17.28	0	0
490	56	2	651.24	16.52	40	0
491	56	3	1203.48	14.75	60	0
492	56	4	1387.44	14.33	65	0
493	56	5	1627.92	13.81	70	0
494	56	6	1939.68	13.26	75	0
495	56	7	2477.52	12.04	80	0
496	56	8	2788.92	11.13	80.65	0
497	56	9	3057.84	10	80	0
498	56	10	3412.08	8.44	75	0
499	56	11	3610.8	7.1	69.87	0
500	57	1	0	22.04	0	0
501	57	2	637.2	21.28	40	0
502	57	3	1330.92	18.93	60	0
503	57	4	1528.92	18.35	65	0
504	57	5	1783.8	17.59	70	0
505	57	6	2109.6	16.95	75	0
506	57	7	2619	15.82	80	0
507	57	8	2803.32	15.39	81	0
508	57	9	3128.76	14.11	81.95	0
509	57	10	3482.64	12.77	81	0
510	57	11	3610.8	12.19	80	0
511	57	12	3880.8	10.49	75	0
512	57	13	4093.2	8.99	69.95	0
513	58	1	0	26.85	0	1.52
514	58	2	722.16	26	40	1.22
515	58	3	1429.92	23.32	60	1.52
516	58	4	1656.36	22.46	65	1.52
517	58	5	1897.2	21.76	70	1.52
518	58	6	2236.68	20.91	75	1.83
519	58	7	2760.84	19.63	80	2.74
520	58	8	2902.32	19.29	81	2.9
521	58	9	3057.84	18.78	82	3.05
522	58	10	3468.6	17.28	83	3.35
523	58	11	3837.6	15.45	82	5.49
524	58	12	3963.6	14.87	81	6.1
525	58	13	4316.4	12.47	75	8.23
526	58	14	4503.6	10.97	70	11.28
527	59	1	0	48.34	0	0
528	59	2	68.71	46.21	40	0
529	59	3	126.99	41.27	60	0
530	59	4	146.38	40.05	65	0
531	59	5	171.75	38.62	70	0
532	59	6	204.64	37.09	75	0
533	59	7	261.42	33.68	80	0
534	59	8	294.35	31.12	80.65	0
535	59	9	322.52	27.96	80	0
536	59	10	359.99	23.61	75	0
537	59	11	380.89	19.86	69.87	0
538	60	1	0	61.63	0	0
539	60	2	67.23	59.5	40	0
540	60	3	140.43	52.94	60	0
541	60	4	161.3	51.33	65	0
542	60	5	188.2	49.19	70	0
543	60	6	222.58	47.4	75	0
544	60	7	276.41	44.23	80	0
545	60	8	295.72	43.04	81	0
546	60	9	330.01	39.47	81.95	0
547	60	10	367.49	35.72	81	0
548	60	11	380.89	34.11	80	0
549	60	12	409.51	29.32	75	0
550	60	13	431.76	25.15	69.95	0
551	61	1	0	75.1	0	4.26
552	61	2	76.2	72.73	40	3.41
553	61	3	150.86	65.2	60	4.26
554	61	4	174.75	62.82	65	4.26
555	61	5	200.17	60.87	70	4.26
556	61	6	235.98	58.49	75	5.11
557	61	7	291.17	54.89	80	7.67
558	61	8	306.16	53.95	81	8.1
559	61	9	322.52	52.52	82	8.53
560	61	10	365.9	48.34	83	9.38
561	61	11	404.96	43.22	82	15.34
562	61	12	418.14	41.61	81	17.05
563	61	13	455.39	34.87	75	23.02
564	61	14	475.14	30.69	70	31.55
565	62	1	0	37	0	5.75
566	62	2	2000	35.6	17.5	5.75
567	62	3	5500	31.25	44.5	5.75
568	62	4	10000	29.63	72	5.75
569	62	5	13000	27	83	6.5
570	62	6	16000	23.75	88	7.5
571	62	7	28500	17	82	12
572	63	1	0	65.7	0	0
573	63	2	40.4	67.8	40	0
574	63	3	71.5	68.7	55	0
575	63	4	102.6	68.2	65	0
576	63	5	132.6	67.1	72	0
577	63	6	177.2	61.7	76	0
578	63	7	213.5	55.4	77	0
579	64	1	0	84.1	0	0
580	64	2	56	85.2	40	0
581	64	3	72.5	85	50	0
582	64	4	102.6	84.8	60	0
583	64	5	142	82.9	70	0
584	64	6	171	80.3	75	0
585	64	7	188.6	78	77	0
586	64	8	216.6	73.1	78.75	0
587	64	9	234.2	68.7	78	0
588	65	1	0	101.8	0	3.3
589	65	2	68.4	103	40	3.3
590	65	3	99.5	102.7	50	3.4
591	65	4	126.4	101.8	60	3.5
592	65	5	169.9	98.5	70	4.1
593	65	6	202.1	94.3	75	4.8
594	65	7	223.8	91.1	76	5.9
595	65	8	245.6	86.9	76.9	7
596	66	1	0	22.4	0	2.5
597	66	2	88.2	23.2	35	2.5
598	66	3	174.24	23.2	60	2.5
599	66	4	240.48	22.7	73	2.5
600	66	5	323.64	21.18	75.5	2.6
601	66	6	419.76	18.8	73	3.1
602	66	7	461.88	17.3	70	5.1
603	67	1	0	30.1	0	2.6
604	67	2	66.6	30.7	30	2.6
605	67	3	173.52	30.9	60	2.6
606	67	4	243	30.5	70	2.5
607	67	5	378	27.9	75.5	2.5
608	67	6	510.12	24.1	73	3.8
609	67	7	552.6	22.2	70	5.1
610	68	1	0	40.4	0	2.6
611	68	2	64.08	41.2	30	2.6
612	68	3	191.88	41.5	60	2.6
613	68	4	307.08	40.7	70	2.6
614	68	5	451.08	37.3	75.5	2.5
615	68	6	563.4	33.1	73	3.7
616	68	7	624.24	30.6	70	5.1
617	69	1	0	14.1	0	1.1
618	69	2	92.3	14	65	1.1
619	69	3	129.2	13.4	75	1.1
620	69	4	153.8	12.7	80	1.4
621	69	5	170.3	12.2	82.5	1.4
622	69	6	190.8	11.2	83	1.4
623	69	7	205.1	10.5	82.5	1.7
624	69	8	220.5	9.6	80	2
625	69	9	236.9	8.6	75	2.3
626	69	10	258.5	7	71	3.4
627	70	1	0	16.2	0	1.1
628	70	2	93.3	16.1	65	1.1
629	70	3	109.7	15.9	70	1.1
630	70	4	128.2	15.5	75	1.1
631	70	5	153.8	15	80	1.2
632	70	6	170.3	14.4	82.5	1.2
633	70	7	210.3	12.8	85.35	1.7
634	70	8	243.1	11	82.5	2.3
635	70	9	255.4	10	80	2.8
636	70	10	271.8	8.9	75	3.2
637	70	11	281	8.2	72	5.6
638	71	1	0	18.1	0	1.1
639	71	2	97.4	18	65	1.1
640	71	3	113.8	17.8	70	1.1
641	71	4	156.9	17	80	1.4
642	71	5	205.1	15.3	85	1.7
643	71	6	223.6	14.5	85.45	1.7
644	71	7	242.1	13.5	85	2.2
645	71	8	268.7	11.9	82.5	2.7
646	71	9	282.1	11	80	4.2
647	71	10	300.5	9.6	77	5.8
648	72	1	0	20.2	0	1.1
649	72	2	100.5	20.2	65	1.1
650	72	3	137.4	19.8	75	1.2
651	72	4	178.5	18.9	82.5	1.4
652	72	5	210.3	17.7	85	1.7
653	72	6	236.9	16.6	86	2
654	72	7	264.6	15	85	2.5
655	72	8	306.7	12.2	80	4.8
656	72	9	326.2	10.8	75	7.2
657	73	1	0	22	0	1.1
658	73	2	104.6	22	65	1.1
659	73	3	144.6	21.6	75	1.2
660	73	4	185.6	20.6	82.5	1.6
661	73	5	217.4	19.5	85	1.7
662	73	6	237.9	18.9	86	2
663	73	7	252.3	18.2	86.44	2.3
664	73	8	262.6	17.7	86	2.5
665	73	9	285.1	16.5	85	3.6
666	73	10	326.2	13.8	80	5.9
667	73	11	348.7	11.9	74	7.8
668	74	1	0	24	0	1.1
669	74	2	109.7	24	65	1.1
670	74	3	128.2	23.7	70	1.1
671	74	4	178.5	23	80	1.2
672	74	5	226.7	21.6	85	1.7
673	74	6	249.2	20.8	86	2
674	74	7	263.6	20.2	86.55	1.9
675	74	8	303.6	18	85	3.4
676	74	9	328.2	16.6	82.5	4.7
677	74	10	364.1	14	75	7.3
678	74	11	375.4	13.1	73	8.6
679	75	1	0	24.8	0	2.3
680	75	2	92	24.8	60	2.3
681	75	3	127	24.8	70	2.3
682	75	4	159.1	24.5	75	2.4
683	75	5	208.6	22.9	77.97	2.9
684	75	6	253.1	20.1	75	3.8
685	75	7	299.5	15.7	71	5.9
686	76	1	0	32.1	0	2.3
687	76	2	91.9	32.1	60	2.3
688	76	3	129.1	32.2	70	2.3
689	76	4	159.1	31.9	75	2.3
690	76	5	179.7	31.6	78	2.3
691	76	6	221	30.3	80	2.9
692	76	7	245.8	29.3	80.45	3.3
693	76	8	269.6	28.2	80	3.9
694	76	9	302.6	26	78	5
695	76	10	332.6	23.7	74.85	6.8
696	77	1	0	36.8	0	2.3
697	77	2	94	36.8	60	2.3
698	77	3	131.2	36.8	70	2.1
699	77	4	159.1	36.5	75	2
700	77	5	177.7	36.2	78	2.1
701	77	6	202.4	35.6	80	2.4
702	77	7	250	33.7	82.45	3.5
703	77	8	311.9	30.1	80	5.5
704	77	9	332.6	28.7	78	6.5
705	77	10	345	27.6	76.55	7.3
706	78	1	0	41.8	0	2.1
707	78	2	101	41.8	60	2.4
708	78	3	134.3	41.8	70	2
709	78	4	161.1	41.7	75	2.1
710	78	5	181.8	41.4	78	1.8
711	78	6	200	41	80	2.1
712	78	7	246.9	39.5	83	2.9
713	78	8	270.6	38.4	83.5	3.8
714	78	9	303.7	36.6	83	4.4
715	78	10	321.2	35.4	82	4.8
716	78	11	347	33.4	80	6.2
717	78	12	361.5	32.3	78	7.4
718	79	1	0	39.3	0	1.5
719	79	2	92.8	39.1	60	1.5
720	79	3	111	38.8	65	1.5
721	79	4	134.2	38.4	70	1.5
722	79	5	170.6	37	75	1.5
723	79	6	209.9	34.9	77	1.6
724	79	7	222	34.2	77.25	1.8
725	79	8	231.1	33.5	77	1.6
726	79	9	265.4	30.6	75	2
727	79	10	310.8	26.2	70	2.6
728	79	11	350.2	21.7	65	3.4
729	80	1	0	50	0	1.3
730	80	2	97.9	50.2	60	1.3
731	80	3	141.3	49.4	70	1.3
732	80	4	201.8	47.1	77	1.1
733	80	5	226.1	45.7	78	1.3
734	80	6	245.2	44.4	78.45	1.5
735	80	7	266.4	43	78	1.8
736	80	8	297.7	40.7	77	2.1
737	80	9	325	38.5	75	2.6
738	80	10	368.3	34.2	70	3.4
739	80	11	384.5	32.3	68	4.6
740	81	1	0	62.2	0	1.1
741	81	2	110	61.9	60	1.5
742	81	3	130.2	61.6	65	1.1
743	81	4	191.7	59.5	75	0.8
744	81	5	242.2	56.9	78	1.1
745	81	6	275.5	54.9	78.5	1.5
746	81	7	309.8	52.4	78	2
747	81	8	340.1	49.9	77	2.5
748	81	9	368.3	47.4	75	3.1
749	81	10	420.8	42.4	68.75	4.8
750	82	1	0	39.1	0	1.71
751	82	2	277.2	39.9	48.4	1.71
752	82	3	522.4	39.5	64.9	2.55
753	82	4	776.9	38.7	75.7	3.26
754	82	5	1092	37	83.8	4.1
755	82	6	1299	35.4	86.3	4.6
756	82	7	1471	33.8	86.1	5.27
757	82	8	1656	32	85.17	6
758	83	1	0	61.5	0	4.9
759	83	2	250	61.1	42	4.9
760	83	3	500	60.5	67	4.9
761	83	4	800	51.5	81.5	4.9
762	83	5	1050	53	87	5.9
763	83	6	1300	43.5	81.5	8.2
764	83	7	1470	30	65	10.2
765	84	1	0	82.28	0	4.9
766	84	2	250	82	42	4.9
767	84	3	500	82	67	4.9
768	84	4	850	78	81.5	4.9
769	84	5	1150	74	87	6.8
770	84	6	1350	67.5	81.5	9
771	84	7	1500	55	65	10.2
772	85	1	0	55	0	0
773	85	2	360	52	37.9	0
774	85	3	720	48	64.46	0
775	85	4	1080	42	79.19	0
776	85	5	1368	37	87.8	0
777	85	6	1440	35	87.98	0
778	85	7	1800	24	77.4	0
779	85	8	1900.8	19	66.01	0
780	86	1	0	83.1	0	3
781	86	2	357.3	80.6	50	3
782	86	3	471.8	80.2	60	3
783	86	4	650.4	76.3	70	3.5
784	86	5	790.1	73.4	75	3.9
785	86	6	920	69	76.5	4.8
786	86	7	1008	64.2	76	8.6
787	87	1	0	120.8	0	3
788	87	2	208.4	119.4	30	3
789	87	3	538.2	114.5	60	3
790	87	4	716.8	110.6	70	3.5
791	87	5	861.1	107.3	75	4
792	87	6	1127	97.1	80	7
793	87	7	1234	98.2	77	8.6
794	88	1	0	77.9	0	4.6
795	88	2	500	77	58	4.7
796	88	3	824	73.6	75	4.7
797	88	4	1054	70	82	5
798	88	5	1331	62.1	85	5.9
799	88	6	1447	57.9	84	6
800	88	7	1546	54.3	81.86	6.4
801	89	1	0	101.8	0	4.6
802	89	2	721.9	98.9	70	4.9
803	89	3	1035	95	80	5
804	89	4	1320	89.3	86	5.9
805	89	5	1539	82.9	87.5	6.4
806	89	6	1684	77.1	86	6.9
807	89	7	1848	69.3	81.85	7.4
808	90	1	0	112.9	0	4.7
809	90	2	769.3	109.6	70	4.7
810	90	3	1076	105.7	80	5.1
811	90	4	1364	100	86	5.7
812	90	5	1626	91.8	88	6.7
813	90	6	1787	85	86	7.1
814	90	7	1965	76.1	81.85	7.9
815	91	1	0	77.9	0	4.6
816	91	2	500	77	58	4.7
817	91	3	824	73.6	75	4.7
818	91	4	1054	70	82	5
819	91	5	1331	62.1	85	5.9
820	91	6	1447	57.9	84	6
821	91	7	1546	54.3	81.86	6.4
822	92	1	0	101.8	0	4.6
823	92	2	721.9	98.9	70	4.9
824	92	3	1035	95	80	5
825	92	4	1320	89.3	86	5.9
826	92	5	1539	82.9	87.5	6.4
827	92	6	1684	77.1	86	6.9
828	92	7	1848	69.3	81.85	7.4
829	93	1	0	112.9	0	4.7
830	93	2	769.3	109.6	70	4.7
831	93	3	1076	105.7	80	5.1
832	93	4	1364	100	86	5.7
833	93	5	1626	91.8	88	6.7
834	93	6	1787	85	86	7.1
835	93	7	1965	76.1	81.85	7.9
836	94	1	617.4	30.1	68.77	0
837	94	2	766	28.24	74.15	0
838	94	3	875.3	26.69	77.14	4
839	94	4	976.5	25.41	80.13	4.2
840	94	5	1080	23.38	81.8	5
841	94	6	1255	18.54	83.66	6.5
842	94	7	1474	11.6	82.15	9.8
843	95	1	0	14.9	0	0
844	95	2	161	13.7	76	0
845	95	3	183.4	12.9	78	0
846	95	4	224.7	11.2	80.2	0
847	95	5	258	9.4	78	0
848	95	6	276.6	8.4	76	0
849	95	7	296.2	7	70	0
850	96	1	0	15.4	0	0
851	96	2	169	14.9	70	0
852	96	3	199.4	14.1	76	0
853	96	4	260.1	12.1	78	0
854	96	5	280.6	11.4	77.5	0
855	96	6	321.1	9.6	76	0
856	96	7	355.3	7.9	70	0
857	97	1	185	10.8	71	0
858	97	2	220.5	10.1	72	0
859	97	3	233	9.6	77	0
860	97	4	306	8	78.2	0
861	97	5	346.6	6.6	77	0
862	97	6	363.4	5.8	70	0
863	97	7	383.4	4.5	65	0
864	98	1	188	11.2	71	0
865	98	2	223.9	10.5	72	0
866	98	3	237	10.1	77	0
867	98	4	311.2	8.6	78.2	0
868	98	5	366.3	7.1	77	0
869	98	6	396.6	5.9	70	0
870	98	7	415.4	4.6	65	0
871	99	1	195	11.5	71	0
872	99	2	220	11	72	0
873	99	3	242	10.6	77	0
874	99	4	317.6	9.1	78.2	0
875	99	5	378.4	7.4	77	0
876	99	6	419.7	6	70	0
877	99	7	446.9	4.8	65	0
878	100	1	30.53	12.74	38	0
879	100	2	46.11	12.34	55	0
880	100	3	60.67	11.86	70	0
881	100	4	83.72	10.97	81.5	0
882	100	5	106.7	9.6	84	0
883	100	6	132.62	7.53	80	0
884	100	7	154.01	5.49	70	0
885	101	1	58.43	114.1	60.17	0
886	101	2	73.01	109.3	65.97	0
887	101	3	88.96	97.47	67.5	0
888	101	4	108.94	86.34	69.55	0
889	101	5	127.33	73.15	67.02	0
890	101	6	142.42	54.54	55.93	0
891	102	1	0	80.6	0	1.7
892	102	2	546.4	79.7	47	2.2
893	102	3	1142	76.2	75	3.4
894	102	4	1503	72.7	82	4.4
895	102	5	2049	64.7	87	6.3
896	102	6	2421	55.8	85	8.5
897	102	7	2650	49.8	82	10.2
898	103	1	0	88.6	0	1.5
899	103	2	551.9	88.1	45	2.2
900	103	3	1098	84.1	73	3.4
901	103	4	1585	79.7	84.8	4.4
902	103	5	2109	71.2	88.3	6.6
903	103	6	2607	59.8	85	10.2
904	103	7	2858	52.3	82	12.7
905	104	1	0	104	0	1.2
906	104	2	546.4	103	45	2.2
907	104	3	1142	99.6	74.5	3.4
908	104	4	1634	95.1	85.5	4.9
909	104	5	2279	84.1	89	7.6
910	104	6	2727	73.2	86	11.2
911	104	7	3137	60.7	82	16.3
912	105	1	0	74.2	0	1.2
913	105	2	508.8	72.2	49	2.1
914	105	3	982.3	67.7	75	3.3
915	105	4	1201	65.7	80.7	3.6
916	105	5	1647	56.3	86	5.3
917	105	6	1838	52.3	83.5	6.8
918	105	7	2007	48.8	80	8.9
919	106	1	0	89.6	0	0.9
920	106	2	508.8	88.6	53	2.1
921	106	3	869.3	85.1	75	3
922	106	4	1343	79.7	87	3.9
923	106	5	1724	73.2	88.95	6.2
924	106	6	2113	64.7	85	10.1
925	106	7	2368	57.3	80	13.6
926	107	1	0	106.5	0	1.2
927	107	2	501.8	104.5	50	2.1
928	107	3	932.9	102	75	3.3
929	107	4	1576	95.6	89.2	5
930	107	5	1922	88.1	90	7.7
931	107	6	2318	78.2	86.8	13
932	107	7	2657	67.2	80	19
933	108	1	0	12.5	0	0
934	108	2	127.87	11.98	74.5	0
935	108	3	158.67	11.06	80	0
936	108	4	178.38	10.18	82	0
937	108	5	203.98	8.66	79.8	0
938	108	6	226.74	7.01	74	0
939	108	7	249.61	4.85	60	0
940	109	1	0	29.4	0	2.6
941	109	2	277.6	27.9	40	2.2
942	109	3	633.3	24.6	70	2.6
943	109	4	773.7	23.3	76	2.9
944	109	5	1039	19.3	81	3.9
945	109	6	1173	16.2	79.8	4.8
946	109	7	1232	14.3	78	5.1
947	110	1	0	38	0	2.8
948	110	2	277.6	36.3	40	2.4
949	110	3	648.9	32.8	70	2.6
950	110	4	857.9	30.2	78	3.2
951	110	5	1157	25.3	83.1	4.6
952	110	6	1298	21.3	81.4	5.7
953	110	7	1410	17.5	78	7.3
954	111	1	0	48.5	0	2.6
955	111	2	271.4	46.6	32	2.3
956	111	3	705	42.5	67.5	2.6
957	111	4	914	39.5	78	3.4
958	111	5	1363	31.1	86	6.6
959	111	6	1547	25.7	82	10.6
960	111	7	1647	21.2	77	13.5
961	112	1	0	39	0	0
962	112	2	400	36	40	0
963	112	3	822.9	33.1	65	0
964	112	4	1047	30.5	75	0
965	112	5	1188	28.7	80	0
966	112	6	1307	27.1	83	0
967	112	7	1385	25.5	83.55	0
968	112	8	1443	24.2	83	0
969	112	9	1495	22.3	80	0
970	112	10	1547	20	75	0
971	112	11	1594	17.8	70	0
972	112	12	1662	15	63	0
973	113	1	0	48.8	0	0
974	113	2	453.1	45.2	40	0
975	113	3	869.8	42	65	0
976	113	4	1010	40.4	70	0
977	113	5	1260	36.7	80	0
978	113	6	1380	34.9	83	0
979	113	7	1526	32.1	85.3	0
980	113	8	1635	29.4	83	0
981	113	9	1719	25.3	75	0
982	113	10	1771	22.6	70	0
983	113	11	1859	18.4	66	0
984	114	1	0	54.1	0	3.7
985	114	2	531.2	49.5	45	3.7
986	114	3	916.7	46.3	65	4.2
987	114	4	1198	42.6	75	5
988	114	5	1448	38.8	83	5.7
989	114	6	1557	36.9	83	6.4
990	114	7	1620	35.8	86	6.8
991	114	8	1766	30.5	80	8.8
992	114	9	1880	25.3	70	11.2
993	114	10	1984	20.7	65	13.8
994	115	1	0	39.7	0	4
995	115	2	497.3	38.2	40	4
996	115	3	1004	34.7	70	4.2
997	115	4	1201	32.7	75	4.6
998	115	5	1644	25.1	82	6
999	115	6	1868	20.6	80	6.8
1000	115	7	2043	16.1	77	8.2
1001	116	1	0	62.2	0	0
1002	116	2	485.7	58.9	40	0
1003	116	3	1007	55.4	70	0
1004	116	4	1191	53.8	75.8	0
1005	116	5	1437	51	82	0
1006	116	6	1570	48.9	84	0
1007	116	7	1815	44.1	85	0
1008	116	8	2030	39.2	84	0
1009	116	9	2224	34.1	82	0
1010	116	10	2388	29.5	79.5	0
1011	117	1	0	77.4	0	3.8
1012	117	2	497.3	73.9	40	3.8
1013	117	3	1057	69.3	70	4.4
1014	117	4	1600	63.3	85	5.8
1015	117	5	1985	56.3	88.5	7.4
1016	117	6	2285	49.7	86	11
1017	117	7	2491	42.7	82	15.8
1018	118	1	0	43.4	0	4.3
1019	118	2	496.3	38.9	45	4.4
1020	118	3	891.5	34.7	70	5.1
1021	118	4	1121	31.9	75	5.6
1022	118	5	1498	25.7	80.5	7.3
1023	118	6	1645	23	80	8.2
1024	118	7	1733	20.5	78	8.9
1025	119	1	0	58.5	0	0
1026	119	2	487.4	53.9	44	0
1027	119	3	885.7	49.9	70	0
1028	119	4	1143	46.7	80	0
1029	119	5	1357	43.3	85.4	0
1030	119	6	1525	39.6	87.6	0
1031	119	7	1829	32.8	85	0
1032	119	8	1950	29.9	82.6	0
1033	119	9	2039	27.6	79.5	0
1034	120	1	0	69	0	4.2
1035	120	2	500.9	65	43	4.4
1036	120	3	942.1	59.8	70	5.1
1037	120	4	1232	55.3	80	6.1
1038	120	5	1765	45.4	87.5	9.3
1039	120	6	1985	39.9	87	12.8
1040	120	7	2247	32.2	80	17.9
1041	121	1	0	20.2	0	0.5
1042	121	2	277.4	20	45	0.6
1043	121	3	581.3	19.5	75	0.9
1044	121	4	799.3	18.4	83	1.1
1045	121	5	1021	16.4	87	1.5
1046	121	6	1153	15	88	1.9
1047	121	7	1275	13	84	2.4
1048	122	1	0	22	0	0.5
1049	122	2	274.1	22.1	45	0.6
1050	122	3	564.8	21.5	75	0.8
1051	122	4	769.5	20.5	83	1.1
1052	122	5	1050	18	88	1.6
1053	122	6	1262	15.4	86	2.4
1054	122	7	1371	13.8	84	2.8
1055	123	1	0	24.2	0	0
1056	123	2	270.6	23.9	45	0
1057	123	3	561.7	23.4	75	0
1058	123	4	729.8	22.6	83	0
1059	123	5	975.9	20.8	88	0
1060	123	6	1214	18.1	88	0
1061	123	7	1345	16.4	86	0
1062	123	8	1464	14.8	83.5	0
1063	124	1	0	26.1	0	0.4
1064	124	2	274.1	26	45	0.6
1065	124	3	578	25.1	75	0.8
1066	124	4	762.9	24.4	83	1.1
1067	124	5	1143	20.9	89	1.9
1068	124	6	1357	18.1	87	2.8
1069	124	7	1506	16.1	84	3.7
1070	125	1	0	34	0	0.8
1071	125	2	353.3	32.7	50	0.9
1072	125	3	672.2	30.5	75	1.2
1073	125	4	805.7	29.5	80	1.5
1074	125	5	1077	26	85.5	2
1075	125	6	1211	24.3	84	2.5
1076	125	7	1344	22.1	80	3.2
1077	126	1	0	40.9	0	0.8
1078	126	2	357.6	39.9	53	1
1079	126	3	586	38.9	73.3	1.2
1080	126	4	861.8	36.9	85	1.6
1081	126	5	1159	34	89	2.2
1082	126	6	1379	30.2	87	3.5
1083	126	7	1590	26.3	80	5.2
1084	127	1	0	48.6	0	0.6
1085	127	2	357.6	47.8	53	0.9
1086	127	3	616.2	47.1	75	1.4
1087	127	4	887.6	45.6	85.5	1.6
1088	127	5	1297	40.6	90	3.2
1089	127	6	1564	35.4	86.6	4.9
1090	127	7	1793	30.5	80	8.2
1091	128	1	0	138.38	0	3.66
1092	128	2	567.81	132.89	60	3.66
1093	128	3	817.65	129.54	65	3.66
1094	128	4	1090.2	125.58	75	3.66
1095	128	5	1181.05	121.92	80	3.84
1096	128	6	1430.89	115.82	83	4.36
1097	128	7	1567.16	112.78	84.5	5.18
1098	128	8	1703.44	107.59	85	6.1
1099	128	9	1839.71	101.5	84.5	6.86
1100	128	10	1930.56	98.15	83	7.92
1101	128	11	2089.55	91.44	80	9.14
1102	128	12	2271.25	83.52	70	10.67
1103	129	1	0	61.5	0	4.9
1104	129	2	250	61.1	42	4.9
1105	129	3	500	60.5	67	4.9
1106	129	4	800	51.5	81.5	4.9
1107	129	5	1050	53	87	5.9
1108	129	6	1300	43.5	81.5	8.2
1109	129	7	1470	30	65	10.2
1110	130	1	0	82.28	0	4.9
1111	130	2	250	82	42	4.9
1112	130	3	500	82	67	4.9
1113	130	4	850	78	81.5	4.9
1114	130	5	1150	74	87	6.8
1115	130	6	1350	67.5	81.5	9
1116	130	7	1500	55	65	10.2
1117	131	1	0	39.9	0	0
1118	131	2	343.3	35	28.6	0
1119	131	3	602.3	32.8	45.7	0
1120	131	4	1002	29.8	70.1	0
1121	131	5	1480	24.1	73.1	0
1122	131	6	1722	19.1	70.9	0
1123	131	7	2004	9.9	63.2	0
1124	132	1	0	60	0	0
1125	132	2	596.6	52	45.3	0
1126	132	3	1002	49.4	65.9	0
1127	132	4	1396	45.6	72	0
1128	132	5	1902	36.9	75.4	0
1129	132	6	2128	30	72	0
1130	132	7	2364	17.7	64	0
1131	133	1	0	32.46	0	2
1132	133	2	545.5	30.9	47	2.3
1133	133	3	818.3	30.17	62	3.32
1134	133	4	1037	29.26	70	3.65
1135	133	5	1364	27.4	79	3.68
1136	133	6	1773	24.6	81	4.45
1137	133	7	2209	21	75	5.65
1138	134	1	0	45.72	0	2
1139	134	2	545.3	42.97	47	2.3
1140	134	3	872.9	41.9	63	3.32
1141	134	4	1132	40.8	72	3.65
1142	134	5	1555	39	80	3.68
1143	134	6	1855	35.8	80	4.45
1144	134	7	2182	33.2	80	5.65
1145	135	1	0	132.8	0	4.4
1146	135	2	604.2	132.9	51	4.4
1147	135	3	794.7	132.1	61.5	4.4
1148	135	4	1089	129	70	4.4
1149	135	5	1452	121.1	73	5.8
1150	135	6	1781	111.7	70	7.6
1151	135	7	1919	107.2	67	9.1
1152	136	1	0	168.8	0	4.4
1153	136	2	561.4	170.3	51	4.4
1154	136	3	940.6	169.8	70	4.4
1155	136	4	1168	167.8	76	5.7
1156	136	5	1782	151.3	80.1	7.8
1157	136	6	2123	137.1	78	8.4
1158	136	7	2439	121	69	9.3
1159	137	1	0	189.4	0	4.4
1160	137	2	615	190.5	51	4.4
1161	137	3	969.7	188.6	65.5	4.7
1162	137	4	1300	184.7	74	5
1163	137	5	1880	170.2	80.5	7
1164	137	6	2275	153.1	78	8.2
1165	137	7	2617	135.5	68	9.4
1166	138	1	165	20.7	60	2.75
1167	138	2	202	19.7	70	2.92
1168	138	3	294.6	16.4	80	3.63
1169	138	4	330.3	14.8	80.5	4.17
1170	138	5	403	11.4	77	5.2
1171	138	6	454.5	8.8	70	6.69
1172	138	7	502.2	5.9	59.9	8.3
1173	139	1	227.5	20.4	65	2.86
1174	139	2	316.7	19.2	75	3.72
1175	139	3	362	18.3	77	3.95
1176	139	4	419.3	16.5	78	4.66
1177	139	5	497.7	13.8	75	5.34
1178	139	6	552.1	11.6	70	6.35
1179	139	7	611	9	60	7.64
1180	140	1	200	24.4	66.43	0
1181	140	2	260.5	24.1	75.5	0
1182	140	3	330.2	23.3	82	0
1183	140	4	389.4	22.1	84	0
1184	140	5	439.7	20.4	82.5	0
1185	140	6	489.7	18.1	77.7	0
1186	140	7	534.2	14.7	69	0
1187	141	1	136.4	17.6	65	2.4
1188	141	2	149.6	17.2	70	2.4
1189	141	3	172.7	16.5	75	2.2
1190	141	4	200.8	15.6	78	2.5
1191	141	5	222.3	14.8	80	2.8
1192	141	6	245.5	13.7	81	3.2
1193	141	7	267.8	12.5	80	3.7
1194	141	8	314	9.5	75	5.5
1195	141	9	328.9	8.3	70	6.2
1196	141	10	343	7	65	7
1197	142	1	142.9	18.6	65	2.7
1198	142	2	164.3	18.2	70	2.7
1199	142	3	194	17.6	75	2.7
1200	142	4	233.6	16.4	78	3.2
1201	142	5	251.8	15.8	80	3.5
1202	142	6	274	14.8	81	4
1203	142	7	296.3	13.8	80	4.7
1204	142	8	336.7	11.6	75	5.7
1205	142	9	363.1	10	70	7
1206	142	10	381.2	8.8	65	7.9
1207	143	1	180.7	18.9	65	2.9
1208	143	2	205	18.6	70	3
1209	143	3	237	18.1	75	3.3
1210	143	4	283.2	17.1	78	3.8
1211	143	5	312.6	16.3	80	4.3
1212	143	6	342	15.1	82	4.6
1213	143	7	370.6	13.9	80	5.1
1214	143	8	415.7	11.5	75	6.4
1215	143	9	440.5	10.2	70	7.1
1216	143	10	462.8	8.9	65	7.8
1217	144	1	0	25	0	2.7
1218	144	2	548.4	23	40	2.6
1219	144	3	1124	19.8	70	3
1220	144	4	1430	17.6	78	3.3
1221	144	5	1860	12.6	83	4
1222	144	6	2048	9.9	81	4.7
1223	144	7	2145	8.4	79.85	5.2
1224	145	1	0	39.9	0	2.7
1225	145	2	543	37.9	40	2.6
1226	145	3	1161	34.2	70	3.2
1227	145	4	1602	31.2	80	3.6
1228	145	5	2097	24.8	85	5.1
1229	145	6	2344	20.5	83	6.4
1230	145	7	2484	17.8	80	7.8
1231	146	1	0	17.5	0	2.15
1232	146	2	57.4	17.4	50	2.15
1233	146	3	126.6	16.1	72	2.2
1234	146	4	161.2	14.7	78	2.3
1235	146	5	185.3	13.4	78.5	2.45
1236	146	6	246	9.2	72	4.15
1237	146	7	273	7	63	5.15
1238	147	1	0	21.1	0	2.15
1239	147	2	63	21	50	2.15
1240	147	3	111.9	20.4	68	2.15
1241	147	4	164.9	18.7	78	2.25
1242	147	5	207.2	16.4	79.2	3
1243	147	6	261.2	12.5	76	3.45
1244	147	7	307	8.1	63	5.15
1245	148	1	0	23.2	0	2.15
1246	148	2	66.7	23	50	2.15
1247	148	3	116.7	22.4	68	2.15
1248	148	4	169.7	20.9	78	2.2
1249	148	5	226.3	18.2	79.5	2.4
1250	148	6	281.7	14	76	3.35
1251	148	7	323.7	9.2	63	5.15
1252	149	1	0	140	0	4
1253	149	2	106	142	40	4
1254	149	3	170	142	55	4
1255	149	4	230	140	65	4.75
1256	149	5	280	136	72	5.8
1257	149	6	330	131	75	7
1258	149	7	395	121.5	78	9
1259	149	8	450	110	77	12
1260	150	1	0	31.5	0	2.2
1261	150	2	60.3	32.5	50	2.2
1262	150	3	100.5	32.2	70	2.2
1263	150	4	121.1	31.5	75	2.2
1264	150	5	154.4	30	76.5	2.5
1265	150	6	187.4	27.6	75	3.6
1266	150	7	207.4	25.7	73	6.9
1267	151	1	0	43	0	2.2
1268	151	2	32.7	43.8	30	2.2
1269	151	3	82.5	44.2	60	2.2
1270	151	4	129.3	43.2	75	2.3
1271	151	5	186.6	40.2	76.5	3.4
1272	151	6	231	35.9	75	5.3
1273	151	7	255.3	33.3	73	6.9
1274	152	1	0	56.2	0	2.2
1275	152	2	31	57	30	2.2
1276	152	3	64.1	57.4	50	2.2
1277	152	4	157.5	55.9	75	2.5
1278	152	5	223	51	76.5	3.6
1279	152	6	258	47.1	75	4.8
1280	152	7	284.6	44.3	73	6.9
1281	153	1	0	10.8	0	0
1282	153	2	50.5	10.9	39.44	0
1283	153	3	86.6	10.8	60	0
1284	153	4	101	10.6	65	0
1285	153	5	119.1	10.4	70	0
1286	153	6	145.2	9.8	75	0
1287	153	7	176.8	8.8	77.8	0
1288	153	8	209.3	7	75	0
1289	153	9	228.2	5.7	70	0
1290	153	10	240.9	4.8	65	0
1291	153	11	251.7	3.9	60	0
1292	154	1	0	12.2	0	0
1293	154	2	49.9	12.3	40	0
1294	154	3	88.3	12.2	60	0
1295	154	4	114.2	12	69	0
1296	154	5	137.1	11.5	75	0
1297	154	6	151.6	11.2	77	0
1298	154	7	168.2	10.7	79	0
1299	154	8	184.9	10	79.2	0
1300	154	9	197.3	9.5	79	0
1301	154	10	216	8.4	77	0
1302	154	11	245.1	6.6	72	0
1303	154	12	262.8	5.1	66	0
1304	154	13	270	4.3	60	0
1305	155	1	0	14.1	0	0
1306	155	2	50.9	14.1	40	0
1307	155	3	91.4	13.9	60	0
1308	155	4	108	13.8	66	0
1309	155	5	130.9	13.5	72	0
1310	155	6	145.4	13.2	75	0
1311	155	7	176.6	12.4	79	0
1312	155	8	199.4	11.4	79.3	0
1313	155	9	220.2	10.3	79	0
1314	155	10	238.9	9.2	77	0
1315	155	11	251.3	8.4	75	0
1316	155	12	276.3	6.5	69	0
1317	155	13	292.9	5.1	60	0
1318	156	1	0	16	0	2.1
1319	156	2	50.5	15.8	38	2
1320	156	3	97.4	15.7	60	1.9
1321	156	4	112.8	15.6	65	2.1
1322	156	5	132.6	15.4	70	2.1
1323	156	6	159.7	14.9	75	2.3
1324	156	7	184.9	14.1	78	2.7
1325	156	8	220.1	12.6	78.5	3.3
1326	156	9	249	10.9	78	4
1327	156	10	269.7	9.5	75	4.6
1328	156	11	289.6	8	70	5.3
1329	156	12	304	6.9	65	5.8
1330	156	13	313.9	6.1	60	6.3
1331	157	1	0	6.9	0	0
1332	157	2	50.1	6.7	40	0
1333	157	3	100.2	6.3	60	0
1334	157	4	115.5	6.1	66	0
1335	157	5	150.2	5.3	67.5	0
1336	157	6	172.2	4.3	66	0
1337	157	7	185.2	3.3	60	0
1338	158	1	0	8.4	0	0
1339	158	2	50.9	8.3	41.52	0
1340	158	3	90.4	8.1	60	0
1341	158	4	117.4	7.8	69	0
1342	158	5	152.7	6.8	71.89	0
1343	158	6	191.1	5.1	69	0
1344	158	7	202.5	4.3	66	0
1345	158	8	210.8	3.4	60	0
1346	159	1	0	10.1	0	2
1347	159	2	85.2	9.9	60	2
1348	159	3	110.1	9.7	69	2.5
1349	159	4	139.2	9	75	2.7
1350	159	5	162	8.2	76	3
1351	159	6	182.8	7.4	75	3.5
1352	159	7	207.7	6	72	4.2
1353	159	8	220.2	5.1	69	4.8
1354	159	9	227.4	4.5	66	5
1355	159	10	237.8	3.6	60	6
1356	160	1	0	6.6	0	4.8
1357	160	2	150.7	7.7	50	4.9
1358	160	3	182.2	7.7	60	5.1
1359	160	4	215.8	7.6	70	5.5
1360	160	5	238.2	7.3	75	5.8
1361	160	6	313.6	6.2	79.65	7.7
1362	160	7	350.2	5.4	78	8.9
1363	160	8	370.6	4.9	75	10.2
1364	160	9	386.9	4.4	73	11.1
1365	161	1	0	7.8	0	4.2
1366	161	2	149.7	8.7	50	4.3
1367	161	3	181.2	8.6	60	4.3
1368	161	4	214.8	8.5	70	4.8
1369	161	5	238.2	8.3	75	4.9
1370	161	6	287.1	7.6	80	5.8
1371	161	7	323.8	6.9	82	6.9
1372	161	8	364.5	5.9	80	8.6
1373	161	9	382.8	5.5	78	9.2
1374	161	10	399.1	5	75	10.3
1375	161	11	408.3	4.7	74	11.1
1376	162	1	0	8.7	0	3.7
1377	162	2	149.7	9.8	50	4.2
1378	162	3	180.2	9.8	60	3.7
1379	162	4	213.8	9.7	70	4.3
1380	162	5	240.3	9.5	75	4.3
1381	162	6	275.9	9.1	80	4.9
1382	162	7	295.2	8.8	82	5.5
1383	162	8	342.1	7.9	84.15	6.6
1384	162	9	386.9	6.7	82	8
1385	162	10	399.1	6.3	80	8.6
1386	162	11	417.4	5.8	78	9.2
1387	162	12	435.7	5.2	74.75	10.9
1388	163	1	0	10.3	0	3.1
1389	163	2	151.7	11	50	3.7
1390	163	3	183.3	10.95	60	3.5
1391	163	4	216.9	10.7	70	3.7
1392	163	5	270.8	10.2	80	4
1393	163	6	291.2	9.9	82	4.3
1394	163	7	316.6	9.5	84	4.8
1395	163	8	352.3	8.8	84.45	5.5
1396	163	9	396	7.7	84	7.1
1397	163	10	419.5	7.1	82	8.2
1398	163	11	429.6	6.8	80	8.5
1399	163	12	464.3	5.7	75	10.5
1400	164	1	0	11.2	0	2.5
1401	164	2	154.8	11.8	50	2.6
1402	164	3	186.3	11.8	60	2.8
1403	164	4	218.9	11.8	70	2.9
1404	164	5	246.4	11.6	75	3.1
1405	164	6	289.1	11.1	82	3.5
1406	164	7	324.8	10.5	85	4
1407	164	8	368.6	9.5	86	4.6
1408	164	9	406.2	8.5	85	5.5
1409	164	10	420.5	8.1	84	6.2
1410	164	11	449	7.1	80	7.1
1411	164	12	468.3	6.5	78	7.5
1412	164	13	485.6	5.9	74.97	10.3
1413	165	1	0	15.2	0	2
1414	165	2	189.6	15	70	2
1415	165	3	217	14.7	74	2
1416	165	4	241.3	14.3	76	2.3
1417	165	5	263.6	13.6	77	3
1418	165	6	287.9	12.6	76	3.8
1419	165	7	318.3	10.6	70	5.5
1420	165	8	338.6	9.1	64	6.7
1421	165	9	349.8	7.9	57	7.5
1422	165	10	358.9	7	55	8.3
1423	166	1	0	19	0	2
1424	166	2	186.5	18.5	70	2
1425	166	3	209.9	18.5	74	2
1426	166	4	241.3	18.2	78	2
1427	166	5	257.5	17.9	80	2
1428	166	6	282.9	17.1	82.9	2.3
1429	166	7	312.3	15.9	80	3
1430	166	8	335.6	14.6	76	4.1
1431	166	9	347.7	13.7	74	4.5
1432	166	10	369	11.9	67	5.2
1433	166	11	386.3	10.3	60	6.4
1434	166	12	400.5	9	55	8
1435	167	1	0	24.2	0	2
1436	167	2	185.5	24	70	2
1437	167	3	217	23.9	76	2
1438	167	4	246.4	23.8	80	2
1439	167	5	274.7	23.4	83	2
1440	167	6	290	23.1	84	2
1441	167	7	317.3	22.3	85	2
1442	167	8	339.6	21.2	84	2
1443	167	9	359.9	20.3	82	2.3
1444	167	10	379.2	19	78	3
1445	167	11	414.7	16.1	70	4.7
1446	167	12	458.2	11.2	55	8.1
1447	168	1	0	21.6	0	1.7
1448	168	2	143.2	21.7	60	1.9
1449	168	3	166.1	21.8	65	1.9
1450	168	4	187.6	21.7	70	1.9
1451	168	5	226.3	21.2	75	2.7
1452	168	6	295	19.2	79.85	3.9
1453	168	7	353.7	16.5	75	6.7
1454	168	8	382.3	14.4	70	8.3
1455	168	9	388.1	13.7	69.97	9.1
1456	169	1	0	27.4	0	1.7
1457	169	2	141.8	27.5	60	2
1458	169	3	186.2	27.5	70	1.9
1459	169	4	220.5	27.3	75	2
1460	169	5	266.3	26.6	80	2.7
1461	169	6	332.2	24.4	82.5	4.5
1462	169	7	393.8	21.1	80	7
1463	169	8	426.7	18.9	75	9.1
1464	169	9	448.2	17.1	70	10.2
1465	169	10	458.2	16.3	69	10.8
1466	170	1	0	34	0	1.9
1467	170	2	141.8	34.1	60	2
1468	170	3	164.7	34.1	64	2
1469	170	4	216.2	34.1	75	2
1470	170	5	283.5	33.2	82.5	3.1
1471	170	6	342.2	31.4	85.35	3.9
1472	170	7	422.4	27.2	82.5	5.5
1473	170	8	451.1	25.2	80	6.9
1474	170	9	479.7	22.8	75	8.3
1475	170	10	504.1	20.6	70	9.5
1476	170	11	519.8	19.3	69	10.2
1477	171	1	0	38	0	1.7
1478	171	2	141.8	38.1	60	1.9
1479	171	3	189	38.2	70	2
1480	171	4	254.9	37.7	80	2.2
1481	171	5	280.7	37.2	82.5	2.7
1482	171	6	330.8	35.8	85	2.8
1483	171	7	359.4	34.7	85.55	3.3
1484	171	8	385.2	33.4	85	3.6
1485	171	9	441.1	29.9	82.5	4.7
1486	171	10	469.7	27.9	80	5.6
1487	171	11	502.6	25.1	75	6.4
1488	171	12	531.3	22.5	70	7.2
1489	171	13	548.4	20.9	68	8.4
1490	172	1	0	39.1	0	1.4
1491	172	2	123.2	39.2	60	1.2
1492	172	3	172.5	39.2	70	1.4
1493	172	4	207.2	39.1	75	1.5
1494	172	5	237.7	38.6	78	2
1495	172	6	268.1	37.9	80	1.8
1496	172	7	311.6	35.8	81.45	2.2
1497	172	8	369.6	32.4	80	2.8
1498	172	9	404.3	29.9	78	3.4
1499	172	10	439.1	27	75	3.8
1500	172	11	479.7	23.3	70	4.9
1501	172	12	514.5	19.3	63	6
1502	173	1	0	43.7	0	1.4
1503	173	2	129	43.8	60	1.4
1504	173	3	178.3	44	70	1.5
1505	173	4	243.5	43.5	78	1.5
1506	173	5	276.8	42.8	80	1.8
1507	173	6	298.6	42	81	1.8
1508	173	7	340.6	40.3	81.25	2
1509	173	8	385.5	37.9	81	2.6
1510	173	9	411.6	36	80	3.2
1511	173	10	478.3	30.9	75	4
1512	173	11	520.3	27	70	4.6
1513	173	12	533.3	25.6	68	5.1
1514	174	1	0	48.8	0	1.4
1515	174	2	134.8	49.1	60	1.4
1516	174	3	185.5	48.9	70	1.7
1517	174	4	250.7	48.6	78	1.5
1518	174	5	305.8	47.2	81	2
1519	174	6	369.6	44.5	81.35	2.6
1520	174	7	421.7	41.6	81	3.4
1521	174	8	444.9	39.9	80	3.8
1522	174	9	511.6	35	75	5.1
1523	174	10	558	30.6	69	6.9
1524	175	1	0	54.2	0	1.4
1525	175	2	142	54.4	60	1.4
1526	175	3	194.2	54.5	70	1.5
1527	175	4	230.4	54	75	1.5
1528	175	5	294.2	53	80	1.8
1529	175	6	318.8	52.5	81	2.2
1530	175	7	397.1	49.1	82.46	2.8
1531	175	8	453.6	45.5	81	3.5
1532	175	9	478.3	43.8	80	3.7
1533	175	10	505.8	41.8	78	4.3
1534	175	11	540.6	39.2	75	4.6
1535	175	12	578.3	35.7	70	6
1536	176	1	0	58.1	0	1.6
1537	176	2	148.5	58.3	60	1.1
1538	176	3	201	58.3	70	1.4
1539	176	4	304.4	56.9	80	1.7
1540	176	5	329.1	56.2	81	1.7
1541	176	6	369.9	55	82	2
1542	176	7	410.7	52.8	82.35	2.7
1543	176	8	451.5	50.6	82	3.1
1544	176	9	477.7	48.9	81	3.4
1545	176	10	531.6	45.4	78	4.4
1546	176	11	562.1	42.8	75	5.2
1547	176	12	594.2	39.7	71	6.4
1548	177	1	0	62.9	0	1.5
1549	177	2	156.5	63.2	60	1.5
1550	177	3	208.7	63	70	1.7
1551	177	4	250.7	62.7	75	1.5
1552	177	5	276.8	62.4	78	1.5
1553	177	6	315.9	61.3	80	1.8
1554	177	7	342	60.5	81	1.8
1555	177	8	376.8	59.3	82	2.2
1556	177	9	430.4	56.4	82.5	2.8
1557	177	10	479.7	53.5	82	3.4
1558	177	11	495.7	52.3	81	3.5
1559	177	12	520.3	50.5	80	3.8
1560	177	13	608.7	43	73	5.8
1561	178	1	226.5	27.3	60	0
1562	178	2	280	26.3	70	0
1563	178	3	342.5	24.8	75	0
1564	178	4	434.3	22.2	78	0
1565	178	5	508.4	18.9	76	0
1566	178	6	550.2	16.4	70	0
1567	178	7	572.6	14.7	65	0
1568	179	1	175.6	11.7	69.92	0
1569	179	2	224	11	75	0
1570	179	3	253	10.4	77	0
1571	179	4	272.3	9.9	78	0
1572	179	5	287.4	9.4	78.3	0
1573	179	6	310.1	8.5	77	0
1574	179	7	333.5	7	70	0
1575	180	1	340	26.8	65	0
1576	180	2	390	25.9	70	0
1577	180	3	454.5	24.6	75	0
1578	180	4	594.3	21.4	79	0
1579	180	5	660	19.7	78	0
1580	180	6	709.6	17.9	75	0
1581	180	7	813.2	13.3	65	0
1582	181	1	213.8	11.8	64.98	0
1583	181	2	253	11.6	70	0
1584	181	3	300.5	11	75	0
1585	181	4	348.5	10.3	78	0
1586	181	5	391.4	9.4	79	0
1587	181	6	447.7	8	77	0
1588	181	7	509.6	6.1	65	0
1589	182	1	0	42.1	0	4.6
1590	182	2	766.3	38.6	45	4.5
1591	182	3	1598	34.7	75	4.6
1592	182	4	1981	31.2	82	4.7
1593	182	5	2380	28.2	84	5.2
1594	182	6	2690	25.7	85	5.8
1595	182	7	3130	19.8	83.5	7.2
1596	183	1	0	54.3	0	0
1597	183	2	753.1	50.8	40	0
1598	183	3	1600	46.8	74.5	0
1599	183	4	2052	43.7	84	0
1600	183	5	2410	40.6	88.5	0
1601	183	6	2787	36.8	90	0
1602	183	7	3088	33.2	88	0
1603	183	8	3314	30.4	86	0
1604	183	9	3606	26.8	83.8	0
1605	184	1	0	62.9	0	4.5
1606	184	2	758.2	60.4	40	4.6
1607	184	3	1663	55.9	75	4.6
1608	184	4	2226	51.5	85	4.9
1609	184	5	2976	45	90	6.6
1610	184	6	3457	40.1	88	8.4
1611	184	7	3905	33.7	83.5	11.1
1612	185	1	0	59.4	0	0
1613	185	2	1012	55.3	70	0
1614	185	3	1194	54.3	75	0
1615	185	4	1367	53	80	0
1616	185	5	1668	50.2	85	0
1617	185	6	2106	45.2	86.5	0
1618	185	7	2488	40.2	85	0
1619	185	8	2643	37	81	0
1620	185	9	2707	35.6	80.75	0
1621	186	1	0	75.3	0	0
1622	186	2	1048	70.3	70	0
1623	186	3	1240	68.9	75	0
1624	186	4	1413	67.6	80	0
1625	186	5	1695	65.3	85	0
1626	186	6	2361	56.2	88	0
1627	186	7	2807	48.9	85	0
1628	186	8	2953	45.7	81	0
1629	186	9	3008	44.3	80.75	0
1630	187	1	0	93.2	0	4
1631	187	2	1158	86.8	70	4
1632	187	3	1367	85.4	75	4.2
1633	187	4	1568	83.6	80	4.3
1634	187	5	1832	80.8	85	4.6
1635	187	6	2206	76.3	88	5
1636	187	7	2598	70.3	89	6.3
1637	187	8	2917	64.8	88	8.1
1638	187	9	3154	58.9	85	9.8
1639	187	10	3263	56.2	81	10.6
1640	187	11	3300	55.3	80.95	11.4
1641	188	1	0	84	0	4.2
1642	188	2	500	83	30	4.2
1643	188	3	1400	80	61	4.2
1644	188	4	2000	77	75	4.5
1645	188	5	2700	71	82	5.8
1646	188	6	3300	62	84.8	8
1647	188	7	4100	51	80.5	10.5
1648	189	1	0	115.2	0	0
1649	189	2	1032	111.9	41	0
1650	189	3	2023	106.7	71.6	0
1651	189	4	2579	102.4	82	0
1652	189	5	3081	97.6	87.5	0
1653	189	6	3652	91.9	88.5	0
1654	189	7	4249	83.8	86	0
1655	189	8	4629	77.1	83	0
1656	189	9	4887	72.6	80	0
1657	190	1	0	140	0	4.2
1658	190	2	1000	138.5	40	4.2
1659	190	3	2000	132.5	69	4.2
1660	190	4	3000	126	84	4.5
1661	190	5	4000	115	88.5	5.8
1662	190	6	4800	105	85.5	8
1663	190	7	5500	94	80	10.5
1664	191	1	0	44	0	3
1665	191	2	412.2	38.8	25.6	3
1666	191	3	727	35.4	43.3	3
1667	191	4	1030	32.9	59	4
1668	191	5	1425	29	75.7	5
1669	191	6	1832	24.3	82.6	10
1670	191	7	2181	18.4	79.7	15
1671	192	1	0	60.5	0	3
1672	192	2	423.6	54.2	25.6	3
1673	192	3	1036	48.5	56.1	3
1674	192	4	1632	43.7	77.7	4
1675	192	5	2227	37.2	86.1	5
1676	192	6	2530	31.7	84.6	10
1677	192	7	2868	22.9	75.2	15
1678	193	1	0	65.5	0	3.6
1679	193	2	825.3	63.1	45	3.9
1680	193	3	1584	59.9	70	3.9
1681	193	4	2045	57.1	80	4.3
1682	193	5	2818	49.8	86.55	5.1
1683	193	6	3056	46.3	86	5.3
1684	193	7	3309	41.7	84	5.8
1685	194	1	0	73.9	0	3.6
1686	194	2	817.8	72.2	44	3.9
1687	194	3	1621	69	70	3.9
1688	194	4	2175	67.3	82	4
1689	194	5	2550	62.4	86	4.9
1690	194	6	2989	56.8	87.5	5.3
1691	194	7	3569	46.6	85	6.4
1692	195	1	0	91.7	0	3.8
1693	195	2	810.4	89.7	42	4
1694	195	3	1777	85.8	70	3.9
1695	195	4	2379	82.7	82	4.6
1696	195	5	3376	70.4	89	5.8
1697	195	6	3814	62.4	88	6.9
1698	195	7	4022	57.1	86	8.3
1699	196	1	0	155	0	0
1700	196	2	681.3	151	55	0
1701	196	3	1136	140	75	0
1702	196	4	1454	129	85	0
1703	196	5	1703	116	87	0
1704	196	6	1931	110	88	0
1705	196	7	2203	90	86	0
1706	197	1	0	174	0	0
1707	197	2	681.3	169	55	0
1708	197	3	1136	159	75	0
1709	197	4	1454	147	85	0
1710	197	5	1703	135	87	0
1711	197	6	1931	124	88	0
1712	197	7	2339	104	86	0
1713	198	1	0	205	0	0
1714	198	2	681.3	200	55	0
1715	198	3	1136	190	75	0
1716	198	4	1454	180	85	0
1717	198	5	1703	167	87	0
1718	198	6	1931	154	88	0
1719	198	7	2603	118	86	0
1720	199	1	365	33.6	63	4.39
1721	199	2	486.8	31.5	75	4.52
1722	199	3	647.3	27.8	81	5
1723	199	4	748.7	24.8	82	5.75
1724	199	5	855.6	21	81	6.75
1725	199	6	916.6	18.7	78	7.5
1726	199	7	992.9	15.8	70	8.75
1727	200	1	68.13	35.7	22.5	4.51
1728	200	2	162.3	35.5	37	4.64
1729	200	3	495.2	31.5	75.5	5.14
1730	200	4	559.6	29.5	79.2	5.91
1731	200	5	661	25.5	82	6.94
1732	200	6	760	21.8	82.5	7.71
1733	200	7	788.5	20.5	82	8.99
1734	201	1	0	15.8	0	0
1735	201	2	330.2	14.3	75	0
1736	201	3	388.1	13.5	80	0
1737	201	4	476.8	11.8	82	0
1738	201	5	547.6	9.4	80	0
1739	201	6	634.7	7.6	75	0
1740	201	7	695	5.7	65	0
1741	202	1	454.6	36.8	63.26	4.39
1742	202	2	636.9	34.7	75	4.65
1743	202	3	828.6	31.1	80	6.29
1744	202	4	898.1	29.5	80.6	7.17
1745	202	5	1045	25.3	78	9.52
1746	202	6	1236	19	70	14.5
1747	202	7	1390	13.3	60	19.8
1748	203	1	105.4	220.9	23.1	4.39
1749	203	2	220.3	217.5	40.98	4.65
1750	203	3	443.2	212.7	65.19	6.29
1751	203	4	810	164.3	80.46	7.17
1752	203	5	902.2	148.4	79.87	9.52
1753	203	6	936.6	138.5	77.7	14.5
1754	203	7	1076	110.6	72.27	19.8
1755	204	1	105.4	36.82	21.54	4.3
1756	204	2	220.3	36.25	39.72	4.35
1757	204	3	443.2	35.45	64.2	4.4
1758	204	4	673.4	31	76.44	4.9
1759	204	5	810.3	27.38	79.49	6.3
1760	204	6	849.9	26.31	80.1	6.7
1761	204	7	902.2	24.73	80.6	7.1
1762	204	8	936.6	23.08	80.6	7.6
1763	204	9	1029	19.86	79	9.4
1764	204	10	1076	18.44	77.3	9.7
1765	205	1	298.8	16.6	64.99	0
1766	205	2	412.1	15.6	75	0
1767	205	3	512.1	14.4	80	0
1768	205	4	599.4	13.3	81.5	0
1769	205	5	672.7	12.1	80	0
1770	205	6	748.9	10.7	75	0
1771	205	7	854.9	8.3	65	0
1772	206	1	0	193	0	0
1773	206	2	490	157	0	0
1774	206	3	656	143	0	0
1775	206	4	745	130	0	0
1776	206	5	782	125	0	0
1777	206	6	797	122	0	0
1778	206	7	803	121	0	0
1779	206	8	809	120	0	0
1780	206	9	824	120	0	0
1781	206	10	827	120	0	0
1782	207	1	868.6	30.5	74	5.26
1783	207	2	955.2	29.9	78	5.42
1784	207	3	1079	28.6	82	5.88
1785	207	4	1236	26.1	83.6	6.82
1786	207	5	1315	24.2	83	7.42
1787	207	6	1399	21.5	80	8.6
1788	207	7	1430	19.8	78	8.91
1789	208	1	577.9	13.4	74.76	2.44
1790	208	2	676.3	12.9	80	2.52
1791	208	3	769.1	12.1	83	2.71
1792	208	4	819.9	11.5	83.5	2.9
1793	208	5	865.1	10.7	83	3.17
1794	208	6	926.1	9.5	80	3.68
1795	208	7	953.5	8.7	78	3.95
1796	209	1	928.2	23	76	5.41
1797	209	2	1033	22.5	80	5.62
1798	209	3	1125	21.6	82	5.85
1799	209	4	1221	20.2	83	6.24
1800	209	5	1345	17.5	80	6.82
1801	209	6	1445	15.1	76	7.31
1802	209	7	1587	11	65	8.23
1803	210	1	614.6	10	70.01	2.45
1804	210	2	692.5	9.8	80	2.55
1805	210	3	793.6	9.1	80.6	2.68
1806	210	4	908	7.5	80	3
1807	210	5	967.3	6.5	76	3.34
1808	210	6	1018	5.6	70	3.55
1809	210	7	1061	4.8	65	3.73
1810	211	1	110	77	62.5	0
1811	211	2	132	72	69.3	0
1812	211	3	181	52.3	72.2	0
1813	211	4	219	37.5	65.1	0
1814	211	5	246	24	51.3	0
1815	212	1	0	56.1	0	0
1816	212	2	8	54.7	30	2
1817	212	3	10.7	54	35	2
1818	212	4	15.5	51	44	2.2
1819	212	5	22	46	46	2.7
1820	212	6	27.5	38.5	44	3.3
1821	212	7	32	31	41	4.6
1822	213	1	0	101	0	0
1823	213	2	9.5	99.5	30	2
1824	213	3	14.7	97.5	40	2
1825	213	4	19	95	46	2.2
1826	213	5	24	91.5	49	2.7
1827	213	6	29.5	84.5	50	3.3
1828	213	7	37.5	70.5	48	4.6
1829	214	1	0	65	0	2
1830	214	2	6	65	26.54	2
1831	214	3	12	63.1	42.95	2
1832	214	4	19	60	51.73	2.3
1833	214	5	25	54.8	54.85	2.8
1834	214	6	31	47.5	55.68	3.8
1835	214	7	34	42.9	50.91	5
1836	215	1	0	23.6	0	3.2
1837	215	2	88.1	23.4	50	3.2
1838	215	3	194.2	22	72	3.2
1839	215	4	294.4	18.27	79.2	4
1840	215	5	336.9	15.7	78	4.5
1841	215	6	387.7	12.4	72	6
1842	215	7	426.6	9	63	6.95
1843	216	1	0	25.5	0	3.2
1844	216	2	89.4	25.8	50	3.2
1845	216	3	197.1	24.2	72	3.2
1846	216	4	308.6	20.2	79.2	3.7
1847	216	5	365.8	17	78	4.5
1848	216	6	415.1	13.6	72	5.6
1849	216	7	457.8	10.7	63	6.95
1850	217	1	0	30	0	3.2
1851	217	2	95.7	29.6	50	3.2
1852	217	3	202.7	28.2	72	3.2
1853	217	4	331.9	23.6	79.2	4
1854	217	5	407	19	78	5
1855	217	6	450.7	15.7	72	5.8
1856	217	7	495.6	12.3	63	6.95
1857	218	1	0	10	0	0
1858	218	2	86	10.2	60	0
1859	218	3	135	9.6	72	0
1860	218	4	160	9	76	0
1861	218	5	190	7.9	78.4	0
1862	218	6	235	6.4	76	0
1863	218	7	275	4.5	64	0
1864	219	1	0	11	0	0
1865	219	2	83	11.1	60	0
1866	219	3	133	10.5	72	0
1867	219	4	175	9.8	78	0
1868	219	5	220	8.8	79	0
1869	219	6	275	6	72	0
1870	219	7	295	5	64	0
1871	220	1	0	13	0	2.8
1872	220	2	95	12.95	60	2.8
1873	220	3	140	12.4	72	2.8
1874	220	4	175	11.7	78	2.9
1875	220	5	225	10.2	79.5	3
1876	220	6	280	8.2	76	3.5
1877	220	7	325	6	64	4
1878	221	1	0	32.1	0	2.4
1879	221	2	96.2	32.7	50	2.4
1880	221	3	175.9	31.9	75	2.6
1881	221	4	274.1	28.1	81.5	3.4
1882	221	5	312.7	25.4	80	4.6
1883	221	6	384.5	19.8	70	6.4
1884	221	7	446.3	13.4	60	10
1885	222	1	0	38.6	0	2.4
1886	222	2	82.9	39.2	50	2.4
1887	222	3	181	38.1	75	2.6
1888	222	4	296.9	33.3	81.5	3.8
1889	222	5	341.6	30	80	4.6
1890	222	6	414.4	23.5	70	6.6
1891	222	7	472.5	17.5	60	10
1892	223	1	0	48	0	2.4
1893	223	2	83.9	48.3	50	2.4
1894	223	3	205.6	46.5	75	2.8
1895	223	4	329.2	40.1	81.5	4.4
1896	223	5	375	36.3	80	5
1897	223	6	446.7	28.8	70	6.6
1898	223	7	517.9	20.4	59	10
1899	224	1	0	14	0	2.3
1900	224	2	65	14.3	50	2.3
1901	224	3	140	13.9	78	2.3
1902	224	4	180	12.5	80.5	2.5
1903	224	5	220	10.1	78	3
1904	224	6	255	8	73	3.7
1905	224	7	300	5.4	60	5.2
1906	225	1	0	16.2	0	0
1907	225	2	60	16.6	50	0
1908	225	3	150	16	78	0
1909	225	4	195	14.9	80.5	0
1910	225	5	240	12.5	78	0
1911	225	6	275	10	70	0
1912	225	7	315	7.5	60	0
1913	226	1	0	20	0	2.3
1914	226	2	60	20.3	50	2.3
1915	226	3	170	19	78	2.3
1916	226	4	224	17.5	80.5	2.5
1917	226	5	265	15	78	3.1
1918	226	6	285	12.5	70	4
1919	226	7	330	9.9	60	5
1920	227	1	0	18	0	0
1921	227	2	60	19	45	0
1922	227	3	110	18.6	70	0
1923	227	4	135	18.2	75	0
1924	227	5	150	17.8	76	0
1925	227	6	170	17.4	76.5	0
1926	227	7	220	15.9	72.5	0
1927	228	1	0	25.3	0	0
1928	228	2	55	25.7	40	0
1929	228	3	85	26	60	0
1930	228	4	135	25.5	73	0
1931	228	5	200	23.7	76.5	0
1932	228	6	240	21.5	75	0
1933	228	7	265	20	73	0
1934	229	1	0	30.5	0	2.4
1935	229	2	50	31.4	40	2.4
1936	229	3	90	31.5	60	2.4
1937	229	4	155	30.5	73	2.4
1938	229	5	230	27.5	76.5	2.8
1939	229	6	265	25	75	3.5
1940	229	7	295	24	73	4.5
1941	230	1	0	44	0	2
1942	230	2	68.2	45	30	2
1943	230	3	135.2	44.9	60	2.1
1944	230	4	194.2	43.5	75	2.3
1945	230	5	248.2	41.2	77.5	3.1
1946	230	6	299.3	38.25	76	4.9
1947	230	7	343.6	35.2	73	7.9
1948	231	1	0	58.3	0	2
1949	231	2	55.5	59.5	30	2
1950	231	3	131.8	59.9	60	2.1
1951	231	4	223.4	58.1	75	2.4
1952	231	5	303.6	53.7	77.5	3.9
1953	231	6	364.6	49	76	5.1
1954	231	7	418	44.8	73	7.9
1955	232	1	0	71	0	2
1956	232	2	49.8	72.3	30	2
1957	232	3	136.7	72.9	60	2.1
1958	232	4	258.8	69.8	75	3.1
1959	232	5	349.3	64.3	77.5	4.4
1960	232	6	403.4	59.6	76	5.9
1961	232	7	459.8	54.8	73	7.9
1962	233	1	0	14.1	0	2.6
1963	233	2	134.2	14	60	2.8
1964	233	3	211.1	13.1	75	3.4
1965	233	4	269.6	11.6	77.2	4.4
1966	233	5	328.8	9	75	5.8
1967	233	6	352.6	7.5	72	6.4
1968	233	7	381.1	5.8	66	8.2
1969	234	1	0	15.9	0	0
1970	234	2	83.1	16	40	0
1971	234	3	139.6	15.8	60	0
1972	234	4	177.8	15.5	69	0
1973	234	5	216.1	14.9	75	0
1974	234	6	275.9	13.6	79	0
1975	234	7	300.8	12.8	79.3	0
1976	234	8	320.8	12.1	79	0
1977	234	9	347.4	10.7	77	0
1978	234	10	392.2	8.2	72	0
1979	234	11	403.9	7.4	69	0
1980	234	12	417.2	6.5	66	0
1981	235	1	0	17.8	0	0
1982	235	2	144.6	17.6	60	0
1983	235	3	169.5	17.5	66	0
1984	235	4	206.1	17.1	72	0
1985	235	5	242.7	16.5	77	0
1986	235	6	269.3	15.9	79	0
1987	235	7	310.8	14.3	79.3	0
1988	235	8	354	12.5	79	0
1989	235	9	380.6	11.2	77	0
1990	235	10	395.6	10.3	75	0
1991	235	11	418.8	8.9	72	0
1992	235	12	430.5	8	69	0
1993	235	13	442.1	7.2	66	0
1994	236	1	0	19	0	2.6
1995	236	2	146	18.9	60	2.6
1996	236	3	227.8	17.9	75	2.8
1997	236	4	329.1	14.9	79.5	4
1998	236	5	410	10.7	75	5.6
1999	236	6	430	9.3	72	6.6
2000	236	7	455.8	7.5	66	8.2
2001	237	1	0	6.2	0	0
2002	237	2	90	6.2	60	0
2003	237	3	150	5.6	75	0
2004	237	4	180	5	77	0
2005	237	5	210	4.2	75	0
2006	237	6	235	3.1	69	0
2007	237	7	260	2.1	60	0
2008	238	1	0	6.8	0	0
2009	238	2	87.2	6.8	60	0
2010	238	3	112.2	6.7	69	0
2011	238	4	140.2	6.4	75	0
2012	238	5	155.8	6.1	77	0
2013	238	6	185.9	5.6	77.2	0
2014	238	7	216	4.7	77	0
2015	238	8	229.5	4.3	75	0
2016	238	9	247.2	3.6	72	0
2017	238	10	263.8	2.9	66	0
2018	238	11	275.2	2.3	60	0
2019	239	1	0	7.6	0	0
2020	239	2	90.4	7.6	60	0
2021	239	3	117.4	7.5	69	0
2022	239	4	142.3	7.2	75	0
2023	239	5	157.9	7	77	0
2024	239	6	199.4	6.1	77.2	0
2025	239	7	234.7	5	77	0
2026	239	8	263.8	3.9	72	0
2027	239	9	280.4	3.1	66	0
2028	239	10	290.8	2.6	60	0
2029	240	1	0	8.2	0	1.5
2030	240	2	91.4	8.2	60	1.5
2031	240	3	109.1	8.1	66	1.5
2032	240	4	132.9	8	72	1.5
2033	240	5	162	7.5	77	1.7
2034	240	6	208.8	6.4	77.5	1.9
2035	240	7	246.1	5.4	77	2.3
2036	240	8	261.7	4.8	75	3.2
2037	240	9	283.5	3.8	69	3.8
2038	240	10	301.2	2.8	60	5
2039	241	1	0	9	0	2.6
2040	241	2	98.8	8.7	40	2.6
2041	241	3	162.6	8.1	60	3.2
2042	241	4	212.5	7.2	66	4.2
2043	241	5	236.2	6.6	66.1	4.6
2044	241	6	259.7	6	66	5.2
2045	241	7	302.6	4.1	62	8.2
2046	242	1	0	10.5	0	0
2047	242	2	91.4	10.4	40	0
2048	242	3	149.6	9.9	60	0
2049	242	4	174.5	9.7	66	0
2050	242	5	196.1	9.4	69	0
2051	242	6	249.3	8.4	71	0
2052	242	7	299.2	6.5	69	0
2053	242	8	315.8	5.7	66	0
2054	242	9	330.7	4.8	64	0
2055	243	1	0	13.3	0	2.6
2056	243	2	79.8	13.3	40	2.6
2057	243	3	138	13	60	3
2058	243	4	176.2	12.7	69	3.5
2059	243	5	227.7	11.7	75	4
2060	243	6	275.9	10.3	76	4.6
2061	243	7	309.1	9.1	75	5
2062	243	8	340.7	7.5	72	6
2063	243	9	355.7	6.6	69	7
2064	243	10	367.3	5.8	66	8
2065	244	1	0	3.9	0	2
2066	244	2	50	3.9	40	2
2067	244	3	105.9	3.5	60	2
2068	244	4	148.5	3	64	2
2069	244	5	179.7	2.1	60	2.4
2070	244	6	184.9	1.9	59	5
2071	245	1	0	4.3	0	0
2072	245	2	93.5	4.2	60	0
2073	245	3	118.4	4	66	0
2074	245	4	138.1	3.8	69	0
2075	245	5	158.9	3.6	70	0
2076	245	6	180.7	3	69	0
2077	245	7	198.4	2.5	66	0
2078	245	8	209.8	2	65.85	0
2079	246	1	0	5.7	0	1.2
2080	246	2	86.2	5.5	60	1.2
2081	246	3	115.3	5.3	69	1.3
2082	246	4	134	5.1	72	1.6
2083	246	5	168.2	4.5	74.94	2
2084	246	6	207.7	3.4	72	2.7
2085	246	7	231.6	2.6	66	3.4
2086	246	8	245.1	2	60	5
2087	247	1	0	17.7	0	3.5
2088	247	2	183.9	17.5	60	3.5
2089	247	3	259.7	16.8	72	4
2090	247	4	382.4	14.4	77.3	7
2091	247	5	466.7	11.1	75	8.5
2092	247	6	502.3	9.5	72	10
2093	247	7	540.9	7.1	65.89	12.5
2094	248	1	0	20.2	0	0
2095	248	2	99.1	20.5	40	0
2096	248	3	191.8	20.3	60	0
2097	248	4	225.3	20.2	66	0
2098	248	5	268.5	20	72	0
2099	248	6	329.2	19	77	0
2100	248	7	372.4	18	79	0
2101	248	8	405.9	17.1	80	0
2102	248	9	421.9	16.6	80.2	0
2103	248	10	442.7	16	80	0
2104	248	11	505	13.5	77	0
2105	248	12	565.8	10.5	72	0
2106	248	13	600	8.3	66	0
2107	249	1	0	22.6	0	0
2108	249	2	105.5	22.6	40	0
2109	249	3	199.8	22.5	60	0
2110	249	4	255.7	22.2	69	0
2111	249	5	311.6	21.5	75	0
2112	249	6	375.6	20.1	79	0
2113	249	7	436.3	18.6	80.3	0
2114	249	8	489	16.7	80	0
2115	249	9	509.8	15.8	79	0
2116	249	10	568.9	13	75	0
2117	249	11	600.9	11.3	72	0
2118	249	12	639.3	9.3	65.89	0
2119	250	1	0	24.4	0	3.5
2120	250	2	111.1	24.6	40	3.4
2121	250	3	211.1	24.4	60	3.4
2122	250	4	246	24.2	66	3.5
2123	250	5	296.8	23.7	72	3.7
2124	250	6	352.4	23	77	4
2125	250	7	404.8	21.8	80	4.5
2126	250	8	461.9	20.1	80.5	5.1
2127	250	9	542.9	17.1	79	6.7
2128	250	10	603.2	14.1	75	8.7
2129	250	11	649.2	11	69	10.9
2130	250	12	663.5	10.1	66	12.6
2131	251	1	0	7.7	0	0
2132	251	2	125	7.6	60	0
2133	251	3	163.5	7.4	69	0
2134	251	4	208.2	7	76	0
2135	251	5	256.2	6.2	77	0
2136	251	6	297.7	5.1	76	0
2137	251	7	324.1	4.3	72	0
2138	251	8	354.5	3.3	66	0
2139	252	1	0	8.4	0	0
2140	252	2	77.2	8.4	39.23	0
2141	252	3	126.7	8.4	60	0
2142	252	4	145.1	8.3	66	0
2143	252	5	181.1	8.1	72	0
2144	252	6	226.6	7.6	77	0
2145	252	7	272.9	6.8	78	0
2146	252	8	310.5	5.9	77	0
2147	252	9	329.7	5.3	75	0
2148	252	10	371.2	4	69	0
2149	252	11	385.6	3.5	66	0
2150	253	1	0	9.4	0	0
2151	253	2	85.2	9.4	45	0
2152	253	3	130.7	9.3	60	0
2153	253	4	169.1	9.2	69	0
2154	253	5	205.8	8.9	76	0
2155	253	6	254.6	8.2	78	0
2156	253	7	284.9	7.6	78.2	0
2157	253	8	318.5	6.8	78	0
2158	253	9	338.5	6.2	77	0
2159	253	10	382.4	4.8	72	0
2160	253	11	411.2	3.9	66	0
2161	254	1	0	10.5	0	1.8
2162	254	2	135	10.4	60	1.8
2163	254	3	179.5	10.2	69	1.8
2164	254	4	220.2	9.9	75	1.8
2165	254	5	262.6	9.3	78	2
2166	254	6	304.9	8.5	78.5	25
2167	254	7	344.9	7.5	78	3
2168	254	8	368.8	6.7	77	34
2169	254	9	410.4	5.4	72	5
2170	254	10	436	4.3	66	55
2171	255	1	0	11.4	0	3.5
2172	255	2	94	11.3	30	4
2173	255	3	228.5	10.4	60	5
2174	255	4	283.5	9.5	66	5.5
2175	255	5	330.5	8.4	66.5	6.5
2176	255	6	366.7	7.3	66	8.5
2177	255	7	415.9	5.3	62	12.5
2178	256	1	0	13.9	0	0
2179	256	2	95.9	13.9	40	0
2180	256	3	203	13.5	60	0
2181	256	4	238.1	13.3	66	0
2182	256	5	266.9	12.9	69	0
2183	256	6	313.2	12.2	72	0
2184	256	7	351.6	11.3	72.5	0
2185	256	8	399.5	9.9	72	0
2186	256	9	452.3	7.9	69	0
2187	256	10	465.1	7.1	65.89	0
2188	257	1	0	16	0	3.5
2189	257	2	191.8	15.6	60	3.5
2190	257	3	247.7	14.9	69	4
2191	257	4	278.1	14.5	72	4.5
2192	257	5	338.8	13.3	75	5
2193	257	6	366	12.9	75.5	6
2194	257	7	394.7	11.8	75	6.5
2195	257	8	463.5	9.5	72	7
2196	257	9	495.4	8.1	69	10
2197	257	10	516.2	7.1	65.89	12.5
2198	258	1	0	5	0	1.8
2199	258	2	100	4.8	46	1.9
2200	258	3	158.7	4.5	60	2.2
2201	258	4	219.4	3.8	66.3	2.5
2202	258	5	288.1	2.4	65	5.5
2203	259	1	0	6	0	0
2204	259	2	65.2	6	35	0
2205	259	3	134.7	5.8	60	0
2206	259	4	160.3	5.7	66	0
2207	259	5	181.8	5.5	69	0
2208	259	6	233	4.9	72	0
2209	259	7	287.3	3.7	69	0
2210	259	8	312.9	2.9	65.87	0
2211	260	1	0	6.9	0	1.8
2212	260	2	81.2	6.8	45	1.8
2213	260	3	125.1	6.7	60	1.8
2214	260	4	149.9	6.6	66	1.8
2215	260	5	192.2	6.3	72	2
2216	260	6	245	5.6	76	2.3
2217	260	7	296.1	4.4	72	3
2218	260	8	320.1	3.7	69	4
2219	260	9	336.9	3.1	66	5
2220	261	1	0	30.8	0	4.4
2221	261	2	139	30.9	50	4.4
2222	261	3	252.2	29.6	68	4.4
2223	261	4	339	27.4	76	4.6
2224	261	5	446.1	23.7	80	5.6
2225	261	6	545.9	18.2	76	6.8
2226	261	7	628.5	13.3	64	8.8
2227	262	1	0	33.6	0	4.4
2228	262	2	141.3	33.4	50	4.4
2229	262	3	191.4	33	60	4.4
2230	262	4	340.5	30.3	76	4.6
2231	262	5	461.4	26.3	80.5	5.4
2232	262	6	584.7	20	76	7
2233	262	7	674.1	14.1	64	8.8
2234	263	1	0	39.1	0	4.4
2235	263	2	152.8	38.8	50	4.4
2236	263	3	264.5	37.8	68	4.4
2237	263	4	351.9	36.33	76	4.8
2238	263	5	507.4	30.5	81.5	5.6
2239	263	6	639.3	22.9	76	6.8
2240	263	7	748.3	14.8	63	8.8
2241	264	1	0	42.1	0	5
2242	264	2	140.7	43.3	50.26	5
2243	264	3	293.6	41	78	5
2244	264	4	400.3	36.8	81.5	5
2245	264	5	473.9	32.5	80	5.5
2246	264	6	578.2	24.9	70	7.5
2247	264	7	688.5	15.9	59.5	13
2248	265	1	0	50.3	0	5
2249	265	2	120.6	51.1	50	5
2250	265	3	309.2	48.5	78	5
2251	265	4	442.2	42.8	81.5	5
2252	265	5	518.6	38.1	80	6
2253	265	6	616.6	29	70	8
2254	265	7	711.2	19.8	59.5	13
2255	266	1	0	63.8	0	5
2256	266	2	130	64.6	50	5
2257	266	3	362.1	61.6	78	5
2258	266	4	503.1	54.1	81.5	5.5
2259	266	5	579.4	47.9	80	6.5
2260	266	6	678.9	38	70	9
2261	266	7	761.1	28.7	59.5	13
2262	267	1	0	17.5	0	3.2
2263	267	2	120	17.8	60	3.2
2264	267	3	200	17.6	78	3.2
2265	267	4	270	15.4	81.2	3.2
2266	267	5	300	14.6	80	3.5
2267	267	6	350	12.4	75	4.4
2268	267	7	370	10.4	70	5.6
2269	268	1	0	23	0	0
2270	268	2	120	23.5	60	0
2271	268	3	220	22.2	78	0
2272	268	4	300	20	81.1	0
2273	268	5	340	17.6	80	0
2274	268	6	390	15.3	75	0
2275	268	7	420	13.2	70	0
2276	269	1	0	27.4	0	3.2
2277	269	2	120	27.6	60	3.2
2278	269	3	250	26	78	3.2
2279	269	4	330	23.2	81.1	3.9
2280	269	5	370	21.8	80	4.4
2281	269	6	420	17.8	75	5.1
2282	269	7	440	17	70	5.6
2283	270	1	0	56.1	0	2
2284	270	2	101.2	57.8	35	2
2285	270	3	194.8	58	60	2.8
2286	270	4	277.5	56.4	75	4
2287	270	5	370.2	53.1	77.5	6.2
2288	270	6	452.9	48.6	76	9
2289	270	7	511.9	44.1	73	12
2290	271	1	0	76.1	0	2
2291	271	2	78.5	77.7	30	2
2292	271	3	192.3	78.2	60	2
2293	271	4	316.1	76.6	75	2.9
2294	271	5	454.3	70.6	78	5.6
2295	271	6	560	63.5	76	9
2296	271	7	615.9	58	73	12
2297	272	1	0	100	0	2
2298	272	2	73.4	101.4	30	2
2299	272	3	207.8	102.2	60	2
2300	272	4	398.6	98.9	75	3.6
2301	272	5	526	91.8	77.5	6.8
2302	272	6	618	84	76	9
2303	272	7	697.3	76.6	73	12
2304	273	1	0	48	0	4.4
2305	273	2	960	42	46.71	4.4
2306	273	3	1440	41	61.82	4.8
2307	273	4	1920	39	72.81	5
2308	273	5	2400	37	77.99	5.6
2309	273	6	2880	35	80.72	6.4
2310	273	7	3360	31	79.88	10.2
2311	274	1	0	89	0	4.4
2312	274	2	1600	77	57.83	4.8
2313	274	3	2400	73	73.95	5.5
2314	274	4	3200	69.5	83.52	6.4
2315	274	5	4000	64	86.05	7.8
2316	274	6	4800	55	84.06	10.2
2317	274	7	5400	45	73.51	14
2318	275	1	0	48	0	4.4
2319	275	2	960	42	46.71	4.4
2320	275	3	1440	41	61.82	4.8
2321	275	4	1920	39	72.81	5
2322	275	5	2400	37	77.99	5.6
2323	275	6	2880	35	80.72	6.4
2324	275	7	3360	31	79.88	10.2
2325	276	1	0	89	0	4.4
2326	276	2	1600	77	57.83	4.8
2327	276	3	2400	73	73.95	5.5
2328	276	4	3200	69.5	83.52	6.4
2329	276	5	4000	64	86.05	7.8
2330	276	6	4800	55	84.06	10.2
2331	276	7	5400	45	73.51	14
2332	277	1	0	58.5	0	3.75
2333	277	2	1000	56	38	3.75
2334	277	3	2000	53.5	68.75	3.75
2335	277	4	2875	50	87	3.9
2336	277	5	3750	44	90.5	5.5
2337	277	6	4980	31.5	81	9.9
2338	278	1	0	102	0	1
2339	278	2	1000	96	40.21	2.5
2340	278	3	2000	90	70.01	4
2341	278	4	3000	84	88.53	5
2342	278	5	4000	76	100.3	6.1
2343	278	6	5000	66	92.15	7.5
2344	278	7	6000	50	79.68	9
2345	278	8	6250	44	73.04	9.2
2346	279	1	0	80	0	0
2347	279	2	3539	70.2	80.4	0
2348	279	3	3759	68.4	82.2	0
2349	279	4	3945	67.2	82	0
2350	279	5	4195	64.5	81.63	0
2351	279	6	4510	58.8	77.66	0
2352	280	1	0	16.4	0	0
2353	280	2	898.2	15	40	0
2354	280	3	2099	12.2	74	0
2355	280	4	2548	10.9	81	0
2356	280	5	3175	8.4	84	0
2357	280	6	3530	6.2	81	0
2358	280	7	3666	5.3	74	0
2359	280	8	3770	4.6	71	0
2360	281	1	0	19.5	0	0
2361	281	2	1044	17.7	45	0
2362	281	3	2026	15.4	74	0
2363	281	4	2433	14.2	81	0
2364	281	5	2820	12.8	84	0
2365	281	6	3290	10.7	88	0
2366	281	7	3603	8.8	84	0
2367	281	8	3697	8.1	81	0
2368	281	9	3843	7	74	0
2369	281	10	3906	6.2	72	0
2370	282	1	0	21	0	3.6
2371	282	2	1232	18.8	50	3.7
2372	282	3	2005	16.8	74	3.8
2373	282	4	2381	15.7	81	4
2374	282	5	2705	14.6	84	4.3
2375	282	6	3154	12.8	86	5
2376	282	7	3332	11.9	86.55	5.3
2377	282	8	3530	10.9	86	5.6
2378	282	9	3655	10.2	84	5.8
2379	282	10	3760	9.5	81	5.9
2380	282	11	3927	8.3	74	6.2
2381	282	12	4073	6.6	70	6.3
2382	283	1	0	26.6	0	0
2383	283	2	1473	23.6	55	0
2384	283	3	1833	22.7	65	0
2385	283	4	2240	21.5	77	0
2386	283	5	2679	20.1	83	0
2387	283	6	3525	16.4	86	0
2388	283	7	4089	12.6	83	0
2389	283	8	4355	10.5	77	0
2390	283	9	4590	8.6	71	0
2391	283	10	4872	6.5	60	0
2392	283	11	5060	5.1	56	0
2393	284	1	0	32.9	0	0
2394	284	2	1661	29	55	0
2395	284	3	1833	28.5	60	0
2396	284	4	2225	27.1	71	0
2397	284	5	2836	25.2	83	0
2398	284	6	3306	23.4	86	0
2399	284	7	3823	20.8	86.55	0
2400	284	8	4324	17.3	86	0
2401	284	9	4762	13.6	77	0
2402	284	10	5154	10.3	65	0
2403	284	11	5342	8.6	60	0
2404	284	12	5546	7	54	0
2405	285	1	0	36.2	0	4.3
2406	285	2	1849	31.5	55	4.3
2407	285	3	2178	30.4	65	4.3
2408	285	4	2569	29.2	77	4.5
2409	285	5	2961	27.8	83	5.1
2410	285	6	3462	25.9	86	6.2
2411	285	7	3870	23.8	87	7.2
2412	285	8	4512	18.9	86	9.2
2413	285	9	4731	17.3	83	10.2
2414	285	10	5170	13.6	71	11.7
2415	285	11	5561	10	60	12.8
2416	285	12	5828	7.7	52	14.1
2417	286	1	0	25	0	0
2418	286	2	812.5	23.3	50	0
2419	286	3	1813	20	70	0
2420	286	4	2063	18.9	74	0
2421	286	5	2344	17.5	77	0
2422	286	6	2646	15.5	78.55	0
2423	286	7	2979	12	74	0
2424	286	8	3052	10.7	70	0
2425	286	9	3156	8.4	68	0
2426	287	1	0	27.1	0	0
2427	287	2	958.3	24.9	55	0
2428	287	3	1760	22.2	70	0
2429	287	4	2115	20.7	77	0
2430	287	5	2427	19.1	80	0
2431	287	6	2792	16.5	82.5	0
2432	287	7	3063	14.2	80	0
2433	287	8	3200	12	74	0
2434	287	9	3313	9.3	68	0
2435	288	1	0	30.2	0	6.5
2436	288	2	927.1	28	55	6.5
2437	288	3	1708	25.5	70	6.5
2438	288	4	2021	24	77	6.5
2439	288	5	2333	22.5	82	6.5
2440	288	6	2885	19.1	86	7.2
2441	288	7	3229	15.6	84	7.8
2442	288	8	3323	14.2	82	8
2443	288	9	3427	12.4	74	8.2
2444	288	10	3479	11	70	8.5
2445	289	1	0	47.8	0	3.1
2446	289	2	1047	43.3	40	3.2
2447	289	3	2215	35.3	70	3.4
2448	289	4	2804	30.8	78	3.7
2449	289	5	3229	25.9	80	3.9
2450	289	6	3927	17.9	75	4.9
2451	289	7	4462	9.5	65	6.2
2452	290	1	0	63.5	0	0
2453	290	2	1058	58.3	40	0
2454	290	3	2154	52.2	70.5	0
2455	290	4	2589	49.8	78.5	0
2456	290	5	3237	44.8	85.3	0
2457	290	6	3809	38.3	86	0
2458	290	7	4170	32.9	82.8	0
2459	290	8	4382	30	80	0
2460	290	9	4656	25.2	75	0
2461	290	10	5104	18.1	64.5	0
2462	291	1	0	75.6	0	3.1
2463	291	2	1058	70.1	40	3.3
2464	291	3	2204	64.7	70	3.4
2465	291	4	3196	57.7	85	3.9
2466	291	5	3895	51.2	88.5	4.9
2467	291	6	4647	42.3	83	6.8
2468	291	7	5564	24.9	63	14.9
2469	292	1	0	39.5	0	0
2470	292	2	1320	36	55	0
2471	292	3	2322	31.5	73	0
2472	292	4	2723	29	80	0
2473	292	5	3258	25	84	0
2474	292	6	3826	20	87	0
2475	292	7	4210	16.5	85	0
2476	292	8	4578	12	83	0
2477	292	9	4795	9	77	0
2478	293	1	0	57.5	0	0
2479	293	2	1420	53.5	55	0
2480	293	3	2422	48.5	73	0
2481	293	4	2573	47.5	77	0
2482	293	5	2991	44.5	83	0
2483	293	6	3525	40	85	0
2484	293	7	3742	37.5	87	0
2485	293	8	4127	33.5	87.55	0
2486	293	9	4544	28	87	0
2487	293	10	4912	22.5	84	0
2488	293	11	5212	18	80	0
2489	293	12	5413	14.5	76	0
2490	294	1	0	70	0	3.4
2491	294	2	1621	65.5	55	3.6
2492	294	3	2723	61	73	4.6
2493	294	4	3107	58.5	80	5
2494	294	5	3542	55.5	84	5.6
2495	294	6	3993	51.5	87	6.4
2496	294	7	4444	46.5	88	7.8
2497	294	8	4895	40.5	87	9.4
2498	294	9	5129	37	85	10.6
2499	294	10	5446	32	83	13
2500	294	11	5714	27.5	77	15.4
2501	294	12	6131	20.5	71	20.6
2502	295	1	0	51.5	0	4.4
2503	295	2	1506	48.5	50	5.3
2504	295	3	2629	45	75	6.5
2505	295	4	3360	42	83.5	7.6
2506	295	5	4091	37.5	86.8	8.9
2507	295	6	4713	33.5	85	10
2508	295	7	5204	29	81	11.5
2509	296	1	0	69.3	0	0
2510	296	2	1488	65.9	50	0
2511	296	3	2690	62.7	75	0
2512	296	4	3322	60.1	83	0
2513	296	5	3781	57.1	87	0
2514	296	6	4227	54	89.2	0
2515	296	7	4736	49.9	90	0
2516	296	8	5132	46.5	87.9	0
2517	296	9	5579	42.6	84.5	0
2518	297	1	0	80.5	0	4.5
2519	297	2	1506	77.5	50	5.4
2520	297	3	2826	73.5	75	6.7
2521	297	4	3611	69.5	85	8
2522	297	5	4691	62.5	90.5	10.1
2523	297	6	5236	58.5	89	11.6
2524	297	7	5760	52	84	13.6
2525	298	1	0	39.3	0	4.1
2526	298	2	1516	37.3	55	4.1
2527	298	3	2869	32.8	80	4.4
2528	298	4	3273	30.6	84	4.7
2529	298	5	3600	28.1	85	5.1
2530	298	6	3938	25.6	84	5.5
2531	298	7	4211	23.1	82	6
2532	299	1	0	43.5	0	4.1
2533	299	2	1506	40.3	55	4
2534	299	3	2815	37.3	80	4.5
2535	299	4	3207	35.8	84	4.7
2536	299	5	3840	31.6	87	5.3
2537	299	6	4309	27.4	85	6.2
2538	299	7	4636	23.4	82	6.9
2539	300	1	0	47	0	4.1
2540	300	2	1516	45	52	4.2
2541	300	3	2913	42.8	80	4.5
2542	300	4	3731	39.3	87	5.2
2543	300	5	4189	36.3	88	6.1
2544	300	6	4800	30.6	85	7.2
2545	300	7	5095	27.1	82	8
2546	301	1	0	66.8	0	0
2547	301	2	1456	63.4	55	0
2548	301	3	2808	58.9	79.3	0
2549	301	4	3439	55.9	84	0
2550	301	5	4637	48.5	86.5	0
2551	301	6	5384	43.1	84.1	0
2552	301	7	5976	37.6	82	0
2553	302	1	0	75.7	0	0
2554	302	2	1456	71.8	55	0
2555	302	3	2859	66.3	79.3	0
2556	302	4	3439	63.4	84	0
2557	302	5	4198	58.4	86	0
2558	302	6	4746	55.9	87.5	0
2559	302	7	5456	49.5	86	0
2560	302	8	6064	44.1	84	0
2561	302	9	6287	40.6	81	0
2562	303	1	0	89.1	0	7.4
2563	303	2	1623	86.6	55	7.2
2564	303	3	3103	82.2	81	7.4
2565	303	4	3570	80.7	84	7.4
2566	303	5	4117	77.7	86	8.1
2567	303	6	4462	75.2	87	8.4
2568	303	7	5111	70.8	88	9.6
2569	303	8	5719	64.9	87	11.1
2570	303	9	6328	57.4	85	13.6
2571	303	10	6855	52.5	82	16.5
2572	304	1	0	37	0	2.75
2573	304	2	1000	35.6	33	2.75
2574	304	3	2000	33.5	60	2.75
2575	304	4	3600	28	84	3
2576	304	5	4700	23.8	88.5	4.5
2577	304	6	5700	18	84	7.4
2578	304	7	6600	12	68	10.8
2579	305	1	0	38.8	0	3.2
2580	305	2	1923	35	50	3.2
2581	305	3	3315	32	74.5	3.8
2582	305	4	4127	29.5	81.8	4.2
2583	305	5	5155	25	84	4.9
2584	305	6	5884	20.8	81.5	6.2
2585	305	7	6232	17.5	79.5	7.2
2586	306	1	0	48	0	3.3
2587	306	2	1890	44	50	3.2
2588	306	3	3348	40.2	73	3.8
2589	306	4	4392	37	82.6	4.3
2590	306	5	5884	30.2	87	6
2591	306	6	6580	25	83.8	8.2
2592	306	7	6978	20.8	79.5	10.2
2593	307	1	0	55.2	0	3.3
2594	307	2	1906	50.2	50	3.2
2595	307	3	3448	46.5	71	3.8
2596	307	4	4691	42	84	4.5
2597	307	5	6298	34.2	89	7.3
2598	307	6	7094	28	84.5	11.2
2599	307	7	7343	24.8	80	13.1
2600	308	1	0	73.2	0	3.4
2601	308	2	3432	69.8	65	3.6
2602	308	3	5268	66.8	78.5	4
2603	308	4	6383	63.3	82.5	4.4
2604	308	5	7628	57.8	84.2	5.2
2605	308	6	8459	52.8	83.3	6.4
2606	308	7	9574	44.9	80	7.6
2607	309	1	0	96.1	0	3.4
2608	309	2	3432	91.1	63	3.6
2609	309	3	5312	86.7	79	4
2610	309	4	6798	82.2	85.5	4.6
2611	309	5	8634	73.7	88	6.4
2612	309	6	9945	65.8	86	8.4
2613	309	7	11366	55.3	80	11.6
2614	310	1	0	110	0	3.4
2615	310	2	3454	105.1	60	3.6
2616	310	3	5508	100.6	77.8	3.8
2617	310	4	6951	95.1	84.5	4.6
2618	310	5	9465	83.2	89	7.4
2619	310	6	10907	73.2	86	10.4
2620	310	7	12284	61.3	80	14.6
2621	311	1	0	118.7	0	0
2622	311	2	2946	112.3	75	0
2623	311	3	4068	105	86	0
2624	311	4	4979	94.1	87.55	0
2625	311	5	5634	83.1	87	0
2626	311	6	6125	74.9	80	0
2627	311	7	6475	67.6	75	0
2628	312	1	0	150.7	0	0
2629	312	2	3203	141.6	75	0
2630	312	3	3577	138.8	80	0
2631	312	4	4465	130.6	87	0
2632	312	5	5003	124.2	88	0
2633	312	6	5681	114.2	89.23	0
2634	312	7	6242	105	88	0
2635	312	8	6546	100.5	86	0
2636	312	9	7247	85.8	74.85	0
2637	313	1	0	187.2	0	6.2
2638	313	2	3623	179	75	7.1
2639	313	3	4418	172.6	86	7.8
2640	313	4	5330	160.7	88	8.7
2641	313	5	6288	146.1	90	11
2642	313	6	6896	134.2	89	13.3
2643	313	7	7294	125.1	87	15.6
2644	313	8	7621	117.8	80	17.9
2645	313	9	8088	106.8	74	21.1
2646	314	1	0	52.4	0	5.5
2647	314	2	198.1	53.9	50	5.5
2648	314	3	370.1	52.6	75	5.5
2649	314	4	572.8	47	83	5.5
2650	314	5	689	41.1	80	7
2651	314	6	821.9	31.9	70	9.5
2652	314	7	997.7	19.2	55	17
2653	315	1	0	68.7	0	5.5
2654	315	2	173.4	70	50	5.5
2655	315	3	385.2	68.8	75	5.5
2656	315	4	649	59.4	83	6
2657	315	5	769.6	51.1	80	7
2658	315	6	905.1	40.6	70	10
2659	315	7	1040	28	55	17
2660	316	1	0	79.9	0	5.5
2661	316	2	176	81.5	50	5.5
2662	316	3	423.4	80	75	5.5
2663	316	4	717.3	69.2	83	5.5
2664	316	5	824.3	61.1	80	7
2665	316	6	966.2	48.7	70	10
2666	316	7	1094	35.7	55	17
2667	317	1	0	22.5	0	4
2668	317	2	130	23.5	50	4
2669	317	3	210	22.9	70	4
2670	317	4	280	22.4	78	4
2671	317	5	370	20.1	81.5	4.2
2672	317	6	470	17	78	5
2673	317	7	540	14	70	7
2674	318	1	0	29.8	0	0
2675	318	2	120	30.2	50	0
2676	318	3	220	30	70	0
2677	318	4	310	28	78	0
2678	318	5	420	26	81.5	0
2679	318	6	520	21.5	78	0
2680	318	7	590	17.5	70	0
2681	319	1	0	34	0	4
2682	319	2	130	34.8	50	4
2683	319	3	240	34	70	4
2684	319	4	340	33.3	78	4
2685	319	5	460	29.9	81.5	4.5
2686	319	6	570	25	78	6
2687	319	7	630	22	70	7
2688	320	1	0	71.6	0	5
2689	320	2	198.3	73.5	47	5
2690	320	3	280.9	73.5	60	5
2691	320	4	426.1	70.7	77	5.5
2692	320	5	534.6	66.7	78.5	9
2693	320	6	645	60.8	76	13
2694	320	7	730	54.9	73	17
2695	321	1	0	96.1	0	5
2696	321	2	158.4	98.3	40	5
2697	321	3	271.4	98.9	60	5
2698	321	4	494.7	95	77	6
2699	321	5	639	88.8	78.5	8
2700	321	6	796.7	78	76	12.5
2701	321	7	876.2	72	73	17
2702	322	1	0	126	0	5
2703	322	2	157.2	128.1	40	5
2704	322	3	284.7	128.9	60	5
2705	322	4	618.6	121	77	6
2706	322	5	754.2	113	78.7	8
2707	322	6	888.9	103	76	12
2708	322	7	991.2	94	73	17
2709	323	1	0	30	0	0
2710	323	2	100	31	40	0
2711	323	3	190	31	60	0
2712	323	4	260	30	75	0
2713	323	5	350	29	77.5	0
2714	323	6	410	27	76	0
2715	323	7	480	25	73	0
2716	324	1	0	41	0	0
2717	324	2	180	43	60	0
2718	324	3	240	42	70	0
2719	324	4	300	41	75	0
2720	324	5	420	38	77.5	0
2721	324	6	510	35	76	0
2722	324	7	570	32	73	0
2723	325	1	0	54	0	3.9
2724	325	2	190	56	60	3.9
2725	325	3	290	55	70	3.9
2726	325	4	370	53	75	3.9
2727	325	5	500	49	77.5	4.5
2728	325	6	570	46	76	5.2
2729	325	7	650	42	73	7.1
2730	326	1	0	24.1	0	0
2731	326	2	287.3	24.1	60	0
2732	326	3	358.3	23.6	69	0
2733	326	4	392.1	23.2	72	0
2734	326	5	483.4	21.8	77	0
2735	326	6	581.4	19.7	79.78	0
2736	326	7	652.4	17.4	77	0
2737	326	8	709.9	15	75	0
2738	326	9	760.6	12.8	72	0
2739	326	10	791	11.3	69	0
2740	326	11	807.9	10.1	66	0
2741	327	1	0	27	0	5
2742	327	2	287.9	27.1	60	5
2743	327	3	468.1	25.9	77	6
2744	327	4	622.6	22.4	80.2	8.5
2745	327	5	758.5	17.6	77	10.5
2746	327	6	839.7	13.8	72	12.5
2747	327	7	887.8	11.1	66	14
2748	328	1	0	31.2	0	0
2749	328	2	304.2	30.9	60	0
2750	328	3	388.7	30.3	69	0
2751	328	4	459.7	29.7	75	0
2752	328	5	493.5	29.2	77	0
2753	328	6	574.6	27.6	80	0
2754	328	7	676.1	25.1	80.3	0
2755	328	8	757.2	22.2	80	0
2756	328	9	834.9	18.9	77	0
2757	328	10	905.9	15.4	72	0
2758	328	11	953.2	12.6	66	0
2759	329	1	0	36.9	0	5
2760	329	2	326.7	36.4	60	5
2761	329	3	551.1	34.3	77	5.5
2762	329	4	766.3	29.2	80.5	7.5
2763	329	5	935	21.7	77	10
2764	329	6	1003	17.8	72	11.5
2765	329	7	1065	15	66	14
2766	330	1	0	10.4	0	0
2767	330	2	96.3	10.4	45	0
2768	330	3	184.6	10.3	60	0
2769	330	4	236	10.1	69	0
2770	330	5	290.6	9.7	75	0
2771	330	6	342	9	77	0
2772	330	7	370.9	8.5	77.4	0
2773	330	8	401.4	7.8	77	0
2774	330	9	483.3	5.7	72	0
2775	330	10	521.8	4.4	66	0
2776	331	1	0	11.7	0	2
2777	331	2	187.8	11.6	60	2
2778	331	3	326.9	10.7	77	2.5
2779	331	4	401.8	9.6	79.7	3
2780	331	5	481.2	7.8	77	5
2781	331	6	540	6.1	72	6.5
2782	331	7	577.8	4.8	66	7.5
2783	332	1	0	13.5	0	0
2784	332	2	93.1	13.6	40	0
2785	332	3	191.1	13.4	60	0
2786	332	4	226.4	13.3	66	0
2787	332	5	274.5	13	72	0
2788	332	6	329.1	12.6	77	0
2789	332	7	396.6	11.4	80	0
2790	332	8	433.5	10.7	80.3	0
2791	332	9	492.9	9.4	79	0
2792	332	10	553.9	7.7	75	0
2793	332	11	602.1	6	69	0
2794	332	12	618.1	5.4	66	0
2795	333	1	0	14.7	0	0
2796	333	2	97.9	14.7	40	0
2797	333	3	199.1	14.5	60	0
2798	333	4	264.9	14.3	68	0
2799	333	5	319.5	13.9	75	0
2800	333	6	369.3	13.2	79	0
2801	333	7	399.8	12.8	80	0
2802	333	8	449.5	11.8	80.3	0
2803	333	9	505.7	10.6	80	0
2804	333	10	560.3	9	77	0
2805	333	11	619.7	7.3	72	0
2806	333	12	658.3	6	66	0
2807	334	1	0	16	0	2
2808	334	2	216.9	15.7	60	2
2809	334	3	363.9	14.7	77	2.5
2810	334	4	489.2	12.6	80.5	3.5
2811	334	5	598.9	9.6	77	5
2812	334	6	654.5	7.9	72	6
2813	334	7	694.2	6.6	66	7.5
2814	335	1	0	15.3	0	5
2815	335	2	131.4	15	38.33	6
2816	335	3	255.2	14.5	50	7.5
2817	335	4	337.9	13.8	60	8.5
2818	335	5	426.9	12.8	66	10.5
2819	335	6	488.9	11.6	68.5	11.5
2820	335	7	580	9.7	66	14
2821	336	1	0	18	0	0
2822	336	2	163.8	18	45	0
2823	336	3	305.5	17.4	60	0
2824	336	4	400	16.6	69	0
2825	336	5	485	15.4	72	0
2826	336	6	535.4	14.3	73	0
2827	336	7	585.8	13	72	0
2828	336	8	655.1	10.6	69	0
2829	336	9	680.3	9.6	66	0
2830	337	1	0	22	0	0
2831	337	2	160.6	21.9	45	5
2832	337	3	289.8	21.4	60	5
2833	337	4	327.6	21.1	66	5
2834	337	5	409.4	20.4	72	6
2835	337	6	469.3	19.7	75	7
2836	337	7	570.1	17.4	76	8
2837	337	8	636.2	15.1	75	10.5
2838	337	9	715	12.4	72	13
2839	337	10	755.9	10.8	69	14
2840	337	11	771.7	9.7	66	15
2841	338	1	0	6.6	0	2
2842	338	2	97.4	6.4	42.43	2
2843	338	3	229.9	5.8	60	3
2844	338	4	293.8	5.3	66	3.5
2845	338	5	324.2	4.9	66.1	4
2846	338	6	352.7	4.5	66	4.5
2847	338	7	416.1	3.2	62	7.5
2848	339	1	0	7.7	0	0
2849	339	2	94.7	7.6	39.19	0
2850	339	3	197.5	7.4	60	0
2851	339	4	239.2	7.2	66	0
2852	339	5	268.1	7	69	0
2853	339	6	335.6	6.2	71	0
2854	339	7	415.8	4.6	69	0
2855	339	8	439.9	4	65.76	0
2856	340	1	0	9.5	0	1.9
2857	340	2	97.9	9.4	41.76	2
2858	340	3	184.6	9.1	60	2.5
2859	340	4	215.1	9	66	2.5
2860	340	5	268.1	8.6	72	2.9
2861	340	6	314.7	8.2	75	3.2
2862	340	7	356.4	7.5	75.33	4.2
2863	340	8	388.5	6.9	75	4.8
2864	340	9	444.7	5.5	72	6.2
2865	340	10	476.8	4.8	69	7.2
2866	340	11	491.3	4.3	65.97	8.2
2867	341	1	0	28.4	0	0
2868	341	2	378	28.2	60	0
2869	341	3	432	28	66	0
2870	341	4	515.1	27.3	72	0
2871	341	5	635.6	25.8	77	0
2872	341	6	760.2	23.2	79.85	0
2873	341	7	897.3	19	77	0
2874	341	8	951.3	17.1	75	0
2875	341	9	1014	14.7	72	0
2876	341	10	1080	11.4	66	0
2877	342	1	0	31	0	5.1
2878	342	2	366.6	30.9	60	5.1
2879	342	3	602.9	29.5	77	5.1
2880	342	4	809.9	25.4	80.7	5.2
2881	342	5	940.8	21.9	79	5.35
2882	342	6	1098	15.8	72	9
2883	342	7	1164	12.3	66	10.15
2884	343	1	0	35.3	0	0
2885	343	2	398.8	35.1	60	0
2886	343	3	494.4	34.4	69	0
2887	343	4	602.4	33.2	75	0
2888	343	5	697.9	31.8	79	0
2889	343	6	793.5	30.1	81	0
2890	343	7	876.6	28.4	81.5	0
2891	343	8	951.3	26.3	81	0
2892	343	9	992.9	25.1	80	0
2893	343	10	1093	21.3	77	0
2894	343	11	1184	17.3	73	0
2895	343	12	1242	13.7	66	0
2896	344	1	0	42.8	0	5.1
2897	344	2	417.4	42.2	60	5.1
2898	344	3	720	39.8	77	5.2
2899	344	4	974.2	34.6	81.5	5.3
2900	344	5	1154	27.8	79	6
2901	344	6	1301	21.2	73	8
2902	344	7	1379	18.2	66	10.15
2903	345	1	0	12.3	0	0
2904	345	2	250.5	12.1	60	0
2905	345	3	312.4	11.8	69	0
2906	345	4	384.5	11.4	75	0
2907	345	5	442.3	10.7	77	0
2908	345	6	500	10	78.6	0
2909	345	7	557.7	8.9	77	0
2910	345	8	607.2	7.8	75	0
2911	345	9	654.6	6.6	72	0
2912	345	10	683.5	5.8	69	0
2913	345	11	702.1	5.2	66	0
2914	346	1	0	13.5	0	2.5
2915	346	2	251.8	13.4	60	2.5
2916	346	3	381.8	12.8	75	3.5
2917	346	4	541	11	80.15	4
2918	346	5	645.9	8.9	77	5
2919	346	6	722.9	6.9	72	6.5
2920	346	7	768.8	5.4	66	7.5
2921	347	1	0	15.3	0	0
2922	347	2	149.5	15.3	40	0
2923	347	3	262.9	15.2	60	0
2924	347	4	333	14.9	69	0
2925	347	5	401	14.6	75	0
2926	347	6	469.1	13.8	79	0
2927	347	7	500	13.4	80	0
2928	347	8	566	12.4	80.3	0
2929	347	9	634	11	80	0
2930	347	10	662.9	10.6	79	0
2931	347	11	702.1	9.5	77	0
2932	347	12	735.1	8.8	75	0
2933	347	13	815.5	6.2	66	0
2934	348	1	0	17.3	0	0
2935	348	2	163.9	17.3	42	0
2936	348	3	277.3	17	60	0
2937	348	4	322.7	16.9	66	0
2938	348	5	388.7	16.4	72	0
2939	348	6	458.8	15.8	77	0
2940	348	7	520.6	15	80	0
2941	348	8	601	13.7	80.4	0
2942	348	9	710.3	11.4	79	0
2943	348	10	782.5	9.6	75	0
2944	348	11	848.5	7.8	69	0
2945	348	12	873.2	7.1	66	0
2946	349	1	0	18.5	0	2.5
2947	349	2	284	18.3	60	2.5
2948	349	3	456.5	17.3	75	2.5
2949	349	4	640.6	14.7	80.55	3.5
2950	349	5	794.4	11.5	77	5.5
2951	349	6	867.6	9.5	72	7
2952	349	7	924.7	8	66	7.5
2953	350	1	0	17	0	0
2954	350	2	266.6	16.8	45.16	0
2955	350	3	462.1	15.3	60	0
2956	350	4	549.6	14.6	66	0
2957	350	5	641.8	13.1	67.5	0
2958	350	6	710.3	11.6	66	0
2959	350	7	784.7	8.8	63	0
2960	351	1	0	20.2	0	0
2961	351	2	411.3	20.1	60	0
2962	351	3	527.6	19.2	69	0
2963	351	4	610.7	18	72	0
2964	351	5	710.4	16.6	73.5	0
2965	351	6	785.2	14.5	72	0
2966	351	7	855.8	11.8	69	0
2967	351	8	880.7	10.4	66	0
2968	352	1	0	26.3	0	5.1
2969	352	2	378	25.4	60	5.1
2970	352	3	477.7	24.9	69	5.1
2971	352	4	598.2	23.2	75	5.1
2972	352	5	735.3	20.9	76.98	5.2
2973	352	6	872.4	17.1	75	6.5
2974	352	7	959.6	14.2	72	8.5
2975	352	8	1010	12.3	69	10
2976	352	9	1039	11.4	66	10.5
2977	353	1	0	7.5	0	3
2978	353	2	201.9	7.2	45	3
2979	353	3	313.2	6.7	60	3.5
2980	353	4	387.7	6.19	66	4
2981	353	5	432.8	5.7	67	4.5
2982	353	6	464.3	5.2	66	5
2983	353	7	513.6	4.3	62	7
2984	354	1	0	8.9	0	0
2985	354	2	168	8.9	40	0
2986	354	3	271.1	8.6	60	0
2987	354	4	324.7	8.3	66	0
2988	354	5	361.9	8.1	69	0
2989	354	6	448.5	7.2	71	0
2990	354	7	545.4	5.5	69	0
2991	354	8	578.4	4.8	66	0
2992	355	1	0	11.2	0	3
2993	355	2	252.6	10.9	60	3
2994	355	3	287.6	10.8	66	3.5
2995	355	4	359.8	10.3	72	4
2996	355	5	415.5	9.7	75	4.5
2997	355	6	483.5	8.9	76.55	4.4
2998	355	7	543.3	7.9	75	4.4
2999	355	8	611.3	6.5	72	5
3000	355	9	644.3	5.6	69	5.5
3001	355	10	664.9	5	66	7
3002	356	1	0	44.2	0	0
3003	356	2	262.1	44.1	50	0
3004	356	3	476.8	41.8	68	0
3005	356	4	625.6	38.5	76	0
3006	356	5	839.6	30.9	80.5	0
3007	356	6	1058	20.5	76	0
3008	356	7	1226	11.5	63	0
3009	357	1	0	56.5	0	0
3010	357	2	279.9	56.1	50	0
3011	357	3	484.8	54.4	68	0
3012	357	4	635.7	51.7	76	0
3013	357	5	929.9	41.6	81.5	0
3014	357	6	1218	27.3	76	0
3015	357	7	1392	15.6	63	0
3016	358	1	0	63.2	0	7
3017	358	2	308.4	62.6	50	7
3018	358	3	514.2	60.9	68	7
3019	358	4	669.3	58.4	76	7.5
3020	358	5	986.7	48.4	82	8.5
3021	358	6	1306	32	76	12.5
3022	358	7	1478	19.5	63	16.5
3023	359	1	0	20.3	0	3.1
3024	359	2	170.4	20.4	50	3.1
3025	359	3	312.4	19.8	68	3.5
3026	359	4	485.3	17	79	4.4
3027	359	5	557.2	15.3	79.5	5.1
3028	359	6	658	12.9	78	6.3
3029	359	7	778	9.7	60	8.7
3030	360	1	0	25.1	0	3.1
3031	360	2	184	25	50	3.1
3032	360	3	323.1	24.4	68	3.4
3033	360	4	492.4	22.3	79	4.3
3034	360	5	611.3	19.7	81	5.5
3035	360	6	764.1	15.5	78	7.3
3036	360	7	876.4	11.6	60	8.7
3037	361	1	0	28	0	3.1
3038	361	2	200.2	27.8	50	3.1
3039	361	3	345.4	27	68	3.3
3040	361	4	515.5	25.4	79	4
3041	361	5	662.3	22.6	81.5	5.3
3042	361	6	838	17.7	78	7.3
3043	361	7	949	13.5	60	8.7
3044	362	1	0	65.8	0	8
3045	362	2	272.4	68.6	50	8
3046	362	3	497.1	66.2	75	8
3047	362	4	784.3	57.8	82.5	8.5
3048	362	5	932.5	50.1	80	9
3049	362	6	1042	43.9	75	12
3050	362	7	1348	24.6	61	25
3051	363	1	0	86.7	0	8
3052	363	2	239.3	88.3	50	8
3053	363	3	524.3	86.5	75	8
3054	363	4	890.3	73.2	82.5	8.5
3055	363	5	1060	64.1	80	9
3056	363	6	1162	56.7	75	12
3057	363	7	1433	34.1	61	25
3058	364	1	0	100.3	0	8
3059	364	2	247.1	102.2	50	8
3060	364	3	575.9	100.5	75	8
3061	364	4	961.5	86.3	82.5	8
3062	364	5	1138	75.7	80	9
3063	364	6	1236	67.6	75	11
3064	364	7	1498	44.6	61	25
3065	365	1	0	27.9	0	4.2
3066	365	2	140.3	29	40	4.2
3067	365	3	308.2	28.7	70	4.2
3068	365	4	436.1	26.8	80	4.4
3069	365	5	536.2	24.2	82.1	4.8
3070	365	6	664.2	20.3	78	6.7
3071	365	7	755.2	17	72	10.2
3072	366	1	0	36.9	0	4.2
3073	366	2	126	37.2	40	4.2
3074	366	3	314.3	36.9	70	4.2
3075	366	4	483.2	34.7	80	4.7
3076	366	5	613.1	31	82.1	5.3
3077	366	6	740.5	25.5	78	7.46
3078	366	7	816.9	21.4	72	10.25
3079	367	1	0	43.3	0	4.2
3080	367	2	143.5	44	40	4.2
3081	367	3	337.4	43.8	70	4.2
3082	367	4	553.6	40.5	80	4.8
3083	367	5	674.9	36.8	82.1	5.8
3084	367	6	798.9	30.9	78	7.98
3085	367	7	883.7	26.1	72	10.25
3086	368	1	0	36.5	0	0
3087	368	2	250	35	36.09	0
3088	368	3	500	33	65.1	0
3089	368	4	750	29.5	79.26	0
3090	368	5	1000	24.5	85.52	0
3091	368	6	1250	16	71.65	0
3092	368	7	1300	14	65.67	0
3093	369	1	0	42.1	0	0
3094	369	2	250	41	38.76	0
3095	369	3	500	38.5	67.19	0
3096	369	4	750	35	81.21	0
3097	369	5	1000	30.5	85.61	0
3098	369	6	1250	23	78.27	0
3099	369	7	1350	18.5	70.1	0
3100	370	1	0	46.8	0	0
3101	370	2	250	45.5	37.77	0
3102	370	3	500	43.5	69.67	0
3103	370	4	750	40	82.5	0
3104	370	5	1000	35	87.42	0
3105	370	6	1250	28	82.15	0
3106	370	7	1400	21.5	71.88	0
3107	371	1	0	52.1	0	2.6
3108	371	2	250	51	34.03	3
3109	371	3	500	49	61.76	3.4
3110	371	4	750	46	80.28	3.8
3111	371	5	1000	42	87.96	4.6
3112	371	6	1250	34	85.08	6.4
3113	371	7	1450	25	71.52	9.4
3114	372	1	0	52	0	5
3115	372	2	250	51	32.5	5
3116	372	3	500	50.5	57.5	5
3117	372	4	750	49	75	5.5
3118	372	5	1000	45	82.5	6.5
3119	372	6	1250	38	82.5	9
3120	372	7	1438	30	77.5	9.5
3121	373	1	763.5	22.8	70.74	5.91
3122	373	2	911.7	21.5	75	5.92
3123	373	3	1117	19.6	80	5.93
3124	373	4	1390	16.5	81.9	6.2
3125	373	5	1588	13.8	80	6.7
3126	373	6	1741	11.2	75	7.38
3127	373	7	1884	8.6	70	8.5
3128	374	1	802.9	32.4	69.44	5.97
3129	374	2	1233	29	80	6
3130	374	3	1444	26.8	84	6.34
3131	374	4	1648	24.2	85	6.91
3132	374	5	1781	22.1	84	7.71
3133	374	6	2009	18.2	80	9.75
3134	374	7	2257	13.3	70	14.75
3135	375	1	573.8	12.4	71.75	3.32
3136	375	2	695.2	11.6	76	3.34
3137	375	3	841.6	10.6	80	3.37
3138	375	4	1047	8.7	83	3.43
3139	375	5	1201	7.2	80	3.79
3140	375	6	1309	5.9	75	4.34
3141	375	7	1420	4.5	67	5.15
3142	376	1	616.7	17.5	68.33	3.38
3143	376	2	779.6	16.6	76	3.38
3144	376	3	1001	15	82	3.4
3145	376	4	1224	13	85	3.93
3146	376	5	1443	10.6	82	5.34
3147	376	6	1616	8.3	75	7.26
3148	376	7	1737	6.6	69	9.52
3149	377	1	0	30.24	0	0
3150	377	2	13.9	30.42	25	0
3151	377	3	27.7	30.02	42	0
3152	377	4	44.1	27.89	52	0
3153	377	5	51	26.37	53.5	0
3154	377	6	58.4	24.29	52	0
3155	377	7	67.7	20.24	44	0
3156	378	1	0	49.53	0	0
3157	378	2	27.6	49.41	42	0
3158	378	3	41.6	48.31	52	0
3159	378	4	48.4	47.34	55	0
3160	378	5	64.4	43.16	57	0
3161	378	6	77.9	38.1	55	0
3162	378	7	88.3	29.29	49	0
3163	379	1	0	7.62	0	0
3164	379	2	13.6	7.47	37	0
3165	379	3	26.1	6.64	52	0
3166	379	4	31.7	6.13	54	0
3167	379	5	34.3	5.79	55	0
3168	379	6	41.1	4.88	53	0
3169	379	7	49.5	3.41	46	0
3170	380	1	0	13.01	0	0
3171	380	2	13.5	12.98	41	0
3172	380	3	22.7	12.56	55	0
3173	380	4	35.7	11.31	65	0
3174	380	5	47.2	9.54	67	0
3175	380	6	54.6	7.92	65	0
3176	380	7	62.7	6	58	0
3177	381	1	0	15.76	0	1.68
3178	381	2	11.56	15.76	31	10.42
3179	381	3	17.94	15.48	42	13.66
3180	381	4	23.89	14.97	50	15.85
3181	381	5	33.23	13.47	54	16.98
3182	381	6	41.61	11.55	50	15.73
3183	381	7	45.92	10.42	45	14.26
3184	382	1	0	30.51	0	1.68
3185	382	2	11.49	30.48	31	10.85
3186	382	3	23.96	29.9	52	16.03
3187	382	4	35.5	28.35	59	18.44
3188	382	5	45.61	25.85	60	18.96
3189	382	6	55.96	22.86	58	17.92
3190	382	7	64.37	19.81	50	16.46
3191	383	1	0	10.5	0	0
3192	383	2	7	10.9	24	0
3193	383	3	13.8	10.3	39	0
3194	383	4	20	8.9	45	0
3195	383	5	25.1	7.2	46	0
3196	383	6	29.6	5.4	45	0
3197	383	7	38	1.6	38	0
3198	384	1	0	22.8	0	0
3199	384	2	9.2	23.8	30	0
3200	384	3	18	22.8	45	0
3201	384	4	25.1	20.6	50	0
3202	384	5	33	17.2	52	0
3203	384	6	39.7	13.7	50	0
3204	384	7	46.8	9.3	42	0
3205	385	1	0	138	0	2.7
3206	385	2	716.4	135	76	2.7
3207	385	3	846	130	80	2.7
3208	385	4	928.8	127.5	82	2.7
3209	385	5	1008	125	83	2.9
3210	385	6	1159.2	117	84	3.5
3211	385	7	1440	107	83	5.5
3212	385	8	1530	103	82	6.7
3213	385	9	1627.2	97	80	8
3214	385	10	1756.8	92	76	11
3215	386	1	902.6	29.8	67.81	0
3216	386	2	1143	28.4	73.5	0
3217	386	3	1459	25.7	77.5	0
3218	386	4	1858	21.1	80	0
3219	386	5	2180	16.7	79	0
3220	386	6	2441	12.7	74	0
3221	386	7	2631	9.4	68	0
3222	387	1	1044	38.6	68.57	6.66
3223	387	2	1346	37.2	75	6.78
3224	387	3	1855	33	84	7.7
3225	387	4	2151	29.6	85.5	9.22
3226	387	5	2451	25.9	84	11.56
3227	387	6	2701	22.2	80	14.54
3228	387	7	3073	16	69	22.32
3229	388	1	0	18.1	0	1.5
3230	388	2	1833	15.7	45	3
3231	388	3	3186	13.1	70	3.8
3232	388	4	4407	10.6	83.6	5
3233	388	5	5804	7.3	87	6
3234	388	6	6786	4.8	85	7.5
3235	388	7	7396	3	83	8
3236	389	1	0	19.1	0	1.5
3237	389	2	1833	16.7	45	2.8
3238	389	3	3207	14.3	70	3.8
3239	389	4	4429	11.6	84.7	4.8
3240	389	5	5804	8.2	90	6.2
3241	389	6	6807	5.7	87.8	7.8
3242	389	7	7789	2.4	79	8.8
3243	390	1	0	21.1	0	1.5
3244	390	2	1789	18.6	45	2.8
3245	390	3	3207	16.1	70	3.8
3246	390	4	4407	13.4	84.3	5
3247	390	5	5826	9.9	90	5.8
3248	390	6	6807	7.3	87.8	7.5
3249	390	7	7964	3.7	76	9
3250	391	1	0	50	0	4.9
3251	391	2	3006	45.5	55	5
3252	391	3	5765	39.5	80	5
3253	391	4	6393	38.5	82	5.2
3254	391	5	7760	35	84	5.6
3255	391	6	9098	30	81.8	6.2
3256	391	7	9590	28	80	6.7
3257	392	1	0	57	0	4.9
3258	392	2	2978	53	55	4.9
3259	392	3	5492	48.5	80	5.2
3260	392	4	7131	45.5	86.5	5.3
3261	392	5	8497	41	87	6.1
3262	392	6	10055	35.5	84	7.3
3263	392	7	10929	31.5	80.04	8.1
3264	393	1	0	70	0	4.7
3265	393	2	2978	67.5	55	5
3266	393	3	5765	62.5	80	5
3267	393	4	7760	58	88	5.5
3268	393	5	9317	53.5	90	6.4
3269	393	6	11066	46	87	8.4
3270	393	7	12459	38.5	80	10.5
3271	394	1	0	10.5	0	2.1
3272	394	2	5.1	10.5	45	1.6
3273	394	3	7	10.4	55	1.7
3274	394	4	8.8	10.1	60	2.2
3275	394	5	9.8	9.9	62	2.7
3276	394	6	12.7	9.2	63.55	5.2
3277	394	7	13.7	8.8	63	6.2
3278	394	8	15.4	7.8	60	9.2
3279	394	9	16.1	7.3	57	10.8
3280	395	1	0	11.9	0	1.1
3281	395	2	5.1	11.7	45	1.1
3282	395	3	7.4	11.6	55	1.1
3283	395	4	9.4	11.3	60	1.6
3284	395	5	12.2	10.5	63	2.2
3285	395	6	13.3	10.2	63.5	3.3
3286	395	7	15.4	9.2	62	6.2
3287	395	8	16.9	8	57	10.8
3288	396	1	0	13	0	1.1
3289	396	2	5.3	12.9	45	1.2
3290	396	3	6.6	12.8	50	1.3
3291	396	4	8.8	12.6	57	1.3
3292	396	5	11.4	12.1	62	1.3
3293	396	6	13	11.6	63	1.9
3294	396	7	13.9	11.3	63.6	2.4
3295	396	8	16	10.4	62	3.2
3296	396	9	16.9	9.8	60	9
3297	396	10	17.8	9.1	57	10
3298	396	11	18	8.8	56	10.8
3299	397	1	0	14.4	0	1.1
3300	397	2	5.7	14.1	45	1.1
3301	397	3	7	14	50	1.1
3302	397	4	9.5	13.6	57	1.3
3303	397	5	10.8	13.3	60	1.1
3304	397	6	14.4	12.3	63.25	2.2
3305	397	7	16.3	11.5	62	4.1
3306	397	8	18.4	10.1	57	7
3307	397	9	18.8	9.7	56	10.8
3308	398	1	0	15.5	0	0.8
3309	398	2	6.1	15.1	45	0.8
3310	398	3	9.1	14.7	55	1.1
3311	398	4	11.6	14.2	60	1
3312	398	5	13.3	13.8	62	1.1
3313	398	6	14.9	13.2	62.55	1.7
3314	398	7	16.3	12.6	62	3
3315	398	8	17.3	12.1	60	4.4
3316	398	9	18.8	11.1	57	6.2
3317	398	10	19.5	10.5	55	10.8
3318	399	1	0	45.4	0	2
3319	399	2	9	45.6	45	1.7
3320	399	3	13.3	45.3	55	1.9
3321	399	4	16.6	44.5	60	2
3322	399	5	19	43.6	63	1.9
3323	399	6	21.6	42.2	64	2.3
3324	399	7	24	40.5	64.55	2.7
3325	399	8	26.6	38	64	3.1
3326	399	9	30	33.4	60	4.4
3327	399	10	31.6	30.4	55	6.6
3328	400	1	0	55.4	0	1.7
3329	400	2	9.8	55.7	45	1.7
3330	400	3	12.3	55.6	50	1.6
3331	400	4	16.3	55.1	57	1.9
3332	400	5	21.4	53.3	62	1.7
3333	400	6	26.5	50.2	64	2.3
3334	400	7	30.3	46.3	63	3.6
3335	400	8	34.4	40	57	4.8
3336	400	9	35.3	37.9	55	6.1
3337	401	1	0	64.3	0	0.8
3338	401	2	11.5	64.6	45	0.5
3339	401	3	16.9	63.5	55	1.2
3340	401	4	21.6	62.3	60	0.6
3341	401	5	25.7	60	63	0.9
3342	401	6	28.7	58	63.57	1.7
3343	401	7	31.1	55.7	63	2
3344	401	8	34.9	51.4	60	3.4
3345	401	9	36.9	48	57	4.5
3346	401	10	38.5	44.8	54	5.5
3347	402	1	1261	33.9	75.09	0
3348	402	2	1694	30.7	80	0
3349	402	3	2055	27.3	83	0
3350	402	4	2283	24.9	83.5	0
3351	402	5	2624	20.7	82	0
3352	402	6	2869	17.2	80	0
3353	402	7	3158	12.5	77	0
3354	403	1	1528	43	70.99	7.26
3355	403	2	1991	39.7	83	7.94
3356	403	3	2301	37.1	85	8.3
3357	403	4	2537	34.8	85.6	8.74
3358	403	5	3105	27.7	82	10.3
3359	403	6	3315	24.3	80	11.23
3360	403	7	3624	18.5	78	13.24
3361	404	1	934.3	18.5	69.2	0
3362	404	2	1246	17	80	0
3363	404	3	1535	15.1	83	0
3364	404	4	1705	13.9	83.5	0
3365	404	5	1929	11.9	82	0
3366	404	6	2121	9.8	80	0
3367	404	7	2369	6.5	70	0
3368	405	1	1144	23.2	68.82	4.36
3369	405	2	1485	21.6	80	4.53
3370	405	3	1758	20	85	4.79
3371	405	4	1926	18.8	85.5	5
3372	405	5	2192	16.4	84	5.52
3373	405	6	2478	13.3	80	6.37
3374	405	7	2713	10	70	7.48
3375	406	1	3413	36.4	80.53	0
3376	406	2	3886	34.1	82	0
3377	406	3	4073	33	83	0
3378	406	4	4585	29.4	80	0
3379	406	5	4918	26.6	78	0
3380	406	6	5331	21.8	74	0
3381	406	7	5455	19.9	72	0
3382	407	1	3738	45.8	77.68	10.76
3383	407	2	4183	43.7	84	10.8
3384	407	3	4470	42.1	85	11
3385	407	4	5103	37.6	82	12.33
3386	407	5	5579	32.9	78	14.44
3387	407	6	5808	29.6	76	16
3388	407	7	6048	25.4	72	18
3389	408	1	2443	20.4	75.8	0
3390	408	2	2848	19.2	82	0
3391	408	3	3039	18.4	83	0
3392	408	4	3450	16	80	0
3393	408	5	3664	14.5	78	0
3394	408	6	3846	13.1	76	0
3395	408	7	4083	11	72	0
3396	409	1	2797	25.3	78	5.87
3397	409	2	3117	24.4	84	6.03
3398	409	3	3320	23.6	85.2	3.2
3399	409	4	3794	20.9	82	3.9
3400	409	5	4019	19.4	80	7.57
3401	409	6	4315	16.8	76	9.12
3402	409	7	4477	15.3	72	10.11
3403	410	1	0	42.5	0	0
3404	410	2	300.2	36.7	50	0
3405	410	3	591.8	32.8	70	0
3406	410	4	764.9	30.2	85	0
3407	410	5	946.8	26.1	87	0
3408	410	6	1071	21.7	86	0
3409	410	7	1163	17.4	82	0
3410	411	1	0	51.9	0	0
3411	411	2	297.3	44.9	50	0
3412	411	3	603.3	39.6	70	0
3413	411	4	825.6	35.7	83	0
3414	411	5	1025	30.4	88	0
3415	411	6	1143	25.8	85	0
3416	411	7	1290	19.1	79	0
3417	412	1	0	60.6	0	0
3418	412	2	297.3	51.9	50	0
3419	412	3	609.1	47.1	70	0
3420	412	4	903.5	42.5	80	0
3421	412	5	1114	35.7	87	0
3422	412	6	1267	30.7	83	0
3423	412	7	1368	26.1	71	0
3424	413	1	71	31.6	70	0
3425	413	2	485.8	30	75	0
3426	413	3	1047	27.4	80	0
3427	413	4	2340	19.5	82	0
3428	413	5	3304	11.2	80	0
3429	413	6	3719	6.7	77	0
3430	413	7	4012	3.5	74	0
3431	414	1	302.8	57.4	70	6.8
3432	414	2	803	55.5	75	6.5
3433	414	3	1377	52.7	80	6.5
3434	414	4	1718	50.7	82	6.8
3435	414	5	1974	48.8	84	7.2
3436	414	6	2389	46.3	85	7.2
3437	414	7	2987	42.1	86	7.9
3438	414	8	3658	36.4	85	10.6
3439	414	9	4000	33.2	84	12.7
3440	414	10	4366	30	82	16.4
3441	414	11	4561	28.1	80	18.8
3442	414	12	4878	24.3	76.86	23.6
3443	415	1	3624	24.6	78.04	0
3444	415	2	4069	23.3	82	0
3445	415	3	4379	22	83	0
3446	415	4	4858	19.7	80	0
3447	415	5	5174	17.8	78	0
3448	415	6	5570	14.9	74	0
3449	415	7	5771	13.1	72	0
3450	416	1	4021	30.4	77.76	5.94
3451	416	2	4460	29.2	84	6.13
3452	416	3	4764	28.1	85	6.42
3453	416	4	5115	26.4	84	6.96
3454	416	5	5712	22.9	80	8.72
3455	416	6	6209	19.2	75	10.7
3456	416	7	6443	17.2	72	12.1
3457	417	1	0	500	0	0
3458	417	2	22.71	499	40	0
3459	417	3	41.06	482.6	60	0
3460	417	4	50.67	469.2	64	0
3461	417	5	59.55	451.4	67	0
3462	417	6	67.68	433.6	66	0
3463	417	7	76.56	406.8	68	0
3464	417	8	91.01	354.5	65	0
3465	418	1	0	573	0	0
3466	418	2	22.71	560	40	0
3467	418	3	42.54	540.5	60	0
3468	418	4	60.3	511.6	67	0
3469	418	5	71.02	487	68	0
3470	418	6	80.27	463.6	69.3	0
3471	418	7	91.01	428	68.5	0
3472	418	8	97.28	399	66	0
3473	419	1	0	650	0	0
3474	419	2	22.71	623	40	0
3475	419	3	44.74	611	60	0
3476	419	4	62.46	575	67	0
3477	419	5	85.17	523	69.5	0
3478	419	6	95.85	488	69	0
3479	419	7	107.2	430	66	0
3480	420	1	0	700	0	6
3481	420	2	22.71	685	40	6
3482	420	3	45.42	662	60	6.1
3483	420	4	68.14	615	68	7.5
3484	420	5	90.85	560	70	9
3485	420	6	99.48	525	69	10
3486	420	7	110.84	462	66	12.5
3487	421	1	0	44	0	0
3488	421	2	20	43.5	33.84	0
3489	421	3	40	42.5	48.72	3.5
3490	421	4	60	40.5	57.53	3.5
3491	421	5	80	38	66.21	4
3492	421	6	100	35	68.06	5.5
3493	421	7	120	31	67.52	8
3494	422	1	0	17.3	0	0
3495	422	2	20.7	17.5	31	0
3496	422	3	35.9	17.5	58	0
3497	422	4	53.4	17	60	0
3498	422	5	69	15.8	63	0
3499	422	6	83	13.8	60	0
3500	422	7	99.8	9.8	57	0
3501	423	1	0	33.4	0	0
3502	423	2	22.3	33.9	31	0
3503	423	3	39.9	33.5	55	0
3504	423	4	54.7	33.3	60	0
3505	423	5	67.5	32.9	65	0
3506	423	6	87.6	30.9	70	0
3507	423	7	95	30.2	75	0
3508	423	8	102.4	29	70	0
3509	423	9	121.1	24.5	65	0
3510	423	10	130.3	21.8	60	0
3511	423	11	145.2	10.8	25	0
3512	424	1	0	20	0	0
3513	424	2	19.3	20	35	0
3514	424	3	37	19.8	56	0
3515	424	4	46.2	19.4	64	0
3516	424	5	55.7	18.9	70	0
3517	424	6	74.7	17	72.9	0
3518	424	7	93	14.6	70	0
3519	424	8	100.1	13.1	64	0
3520	424	9	108.3	11	56	0
3521	425	1	0	26.4	0	0
3522	425	2	19.7	26.5	35	0
3523	425	3	33.3	26.5	56	0
3524	425	4	43.1	26.2	64	0
3525	425	5	53.6	25.8	70	0
3526	425	6	65.2	25	73	0
3527	425	7	72.3	24.7	74	0
3528	425	8	83.8	23.4	76	0
3529	425	9	100.8	21.3	74	0
3530	425	10	105.9	20.4	73	0
3531	425	11	112.3	19.1	70	0
3532	425	12	121.2	16.8	64	0
3533	425	13	130.7	13.8	56	0
3534	426	1	0	34	0	2.7
3535	426	2	20	34.2	35	2.8
3536	426	3	39.4	34	56	2.8
3537	426	4	53.3	33.6	64	2.8
3538	426	5	64.8	33.1	70	2.8
3539	426	6	77	32.1	73	3
3540	426	7	93.3	31.2	74	3.4
3541	426	8	113	28.4	73	4.2
3542	426	9	124.9	25.6	70	5.2
3543	426	10	134.7	22.6	64	6.1
3544	426	11	144.6	18.5	56	7.3
3545	426	12	149.3	17	55	7.8
3546	427	1	0	98.42	0	1.9
3547	427	2	19.55	97.47	34.7	1.9
3548	427	3	34.21	95.56	50.14	1.9
3549	427	4	58.65	90.78	63.33	2
3550	427	5	78.2	86	70.02	2.5
3551	427	6	92.87	80.27	70.08	3.2
3552	427	7	117.3	66.89	67.26	4.8
3553	428	1	0	70	0	0
3554	428	2	360	68.75	32.87	0
3555	428	3	720	66.25	57.71	0
3556	428	4	1080	63.75	74.98	3.13
3557	428	5	1440	58.75	92.8	3.13
3558	428	6	1800	50	81.68	3.5
3559	428	7	2160	41.25	79.54	4.25
3560	428	8	2340	36.25	72.17	5
3561	429	1	0	221	0	4
3562	429	2	200	221	19	4
3563	429	3	500	219	45	3.9
3564	429	4	800	213	62	3.8
3565	429	5	1100	200	73	3.9
3566	429	6	1400	179.5	79	4.1
3567	429	7	1600	160	80	4.2
3568	429	8	1750	143	79	4.4
3569	430	1	0	3.7	0	3
3570	430	2	1.5	3.8	20	3.3
3571	430	3	2.7	3.8	31.2	3.3
3572	430	4	4.1	3.6	39.6	3.3
3573	430	5	5.6	3.1	43.5	3.4
3574	430	6	7.1	2.6	41.9	3.8
3575	430	7	8.6	1.9	34.2	5
3576	430	8	10.1	1.2	21.5	6.7
3577	431	1	0	5.1	0	3
3578	431	2	1.5	5.2	21.2	3
3579	431	3	2.8	5.2	33.1	3
3580	431	4	4.2	5	41.2	3
3581	431	5	5.5	4.6	45	3
3582	431	6	7.1	4	44.6	3.1
3583	431	7	8.7	3.3	41.2	4.1
3584	431	8	10	2.6	34.6	5
3585	431	9	11.1	2	29.2	6.2
3586	432	1	0	6.5	0	3
3587	432	2	1.5	6.5	20.8	3
3588	432	3	2.8	6.5	33.1	3
3589	432	4	4.3	6.4	41.9	3
3590	432	5	5.6	6.1	47.3	3
3591	432	6	7.2	5.5	48.1	3.1
3592	432	7	8.8	4.7	45	3.7
3593	432	8	10	4.1	40.4	4.4
3594	432	9	11.1	3.5	35.4	5.3
3595	433	1	0	14.7	0	2.2
3596	433	2	3.7	15.4	30.7	2.2
3597	433	3	6.6	14.9	45.9	2.2
3598	433	4	10	13.6	54.1	2.3
3599	433	5	13.4	11.3	53	2.7
3600	433	6	16.9	8.2	44.1	3.6
3601	433	7	19.9	5	28.9	5
3602	434	1	0	21	0	2.2
3603	434	2	4.1	21.2	30.7	2.2
3604	434	3	7.1	20.5	45.9	2.2
3605	434	4	10.2	19.3	54.1	2.3
3606	434	5	13.8	16.8	53	2.7
3607	434	6	17.2	13.8	44.1	3.4
3608	434	7	21	9.7	28.9	5
3609	435	1	0	25.9	0	1.9
3610	435	2	4.3	25.9	30.7	1.9
3611	435	3	7.2	25.6	45.9	1.9
3612	435	4	10.5	24.6	54.1	2
3613	435	5	14	22.3	53	2.4
3614	435	6	17.9	18.7	44.1	3.2
3615	435	7	21.2	14.8	28.9	4.6
3616	436	1	0	3.9	0	6.1
3617	436	2	1.2	3.7	20.5	6.1
3618	436	3	2.3	3.2	29.2	6.1
3619	436	4	3.3	2.5	27.7	6.1
3620	436	5	4.1	1.6	20.5	6.9
3621	436	6	4.8	0.6	10.2	8.2
3622	437	1	0	5.6	0	5.3
3623	437	2	1.2	5.4	20.8	5.3
3624	437	3	2.4	4.8	32.6	5.3
3625	437	4	3.4	3.9	34.8	5.5
3626	437	5	4.3	3	29.9	6.3
3627	437	6	4.9	2.1	22.7	7.1
3628	437	7	5.4	1.3	16.7	7.8
3629	438	1	0	6.9	0	4.7
3630	438	2	1.2	6.8	20.5	4.7
3631	438	3	2.4	6.2	34.5	4.7
3632	438	4	3.5	5.3	39.4	4.7
3633	438	5	4.4	4.2	37.5	5.1
3634	438	6	5.1	3.3	32.6	6.1
3635	438	7	6	1.9	20.1	8
3636	439	1	0	15.4	0	4.5
3637	439	2	1.7	15.1	18.8	4.5
3638	439	3	3.1	14.1	29.3	4.5
3639	439	4	4.4	12.5	33.5	4.5
3640	439	5	5.6	10.6	33.1	4.7
3641	439	6	6.7	8.4	28.9	5.1
3642	439	7	7.9	5.8	21.8	5.9
3643	439	8	8.9	3.4	13.5	7.1
3644	440	1	0	21.7	0	3.7
3645	440	2	1.7	21.4	18.8	3.7
3646	440	3	3.1	20.5	29.3	3.7
3647	440	4	4.5	19	36.5	4.1
3648	440	5	5.7	17	38.3	3.9
3649	440	6	6.8	14.7	36.5	4.1
3650	440	7	7.9	11.8	32.7	4.9
3651	440	8	9	8.4	24.1	5.5
3652	440	9	10	5.5	15	6.3
3653	441	1	0	26.7	0	2.9
3654	441	2	1.7	26.4	18.8	2.9
3655	441	3	3.1	25.7	29.7	2.9
3656	441	4	4.5	24.3	37.6	2.7
3657	441	5	5.7	22.8	40.6	2.9
3658	441	6	6.8	20.8	41	3.1
3659	441	7	8.1	17.8	38.3	3.5
3660	441	8	9.1	15	34.6	3.9
3661	441	9	10.1	12.2	30.1	4.3
3662	441	10	11	9.6	23.3	5.1
3663	441	11	11.7	7.2	17.3	5.1
3664	442	1	0	3.5	0	3.9
3665	442	2	1.4	3.7	17.2	3.9
3666	442	3	2.7	3.7	30.5	3.9
3667	442	4	4.1	3.5	38.2	3.9
3668	442	5	5.2	3.1	40.1	4.3
3669	442	6	6.4	2.7	38.2	5
3670	442	7	7.6	2	30.5	6.1
3671	442	8	8.5	1.3	21.4	7
3672	443	1	0	4.8	0	3.6
3673	443	2	1.4	5.1	17.2	3.6
3674	443	3	2.7	5.1	30.2	3.6
3675	443	4	4.1	4.8	40.1	3.6
3676	443	5	5.3	4.4	43.9	3.9
3677	443	6	6.5	3.9	43.5	4.4
3678	443	7	7.7	3.3	38.5	5.4
3679	443	8	8.8	2.6	31.3	6.6
3680	443	9	9.6	2	23.7	7.4
3681	444	1	0	6.3	0	3.2
3682	444	2	1.5	6.4	18.7	3.2
3683	444	3	2.8	6.3	31.3	3.2
3684	444	4	4.1	6.1	41.6	3.4
3685	444	5	5.4	5.7	46.2	3.5
3686	444	6	6.7	5.2	47.3	4.1
3687	444	7	7.8	4.6	44.3	4.9
3688	444	8	8.8	4	39.7	6
3689	444	9	9.8	3.3	33.6	6.9
3690	445	1	0	12.8	0	3
3691	445	2	4.5	13.6	25.1	3
3692	445	3	6.9	13.4	40.3	3
3693	445	4	10	11.8	50.1	3.1
3694	445	5	12.6	9.4	49.4	3.8
3695	445	6	15.1	6.2	42.5	4.6
3696	445	7	17.5	2.6	25.4	6.1
3697	446	1	0	19.6	0	2.7
3698	446	2	4.5	20.4	25.1	2.7
3699	446	3	7	20	40.3	2.7
3700	446	4	10.3	18.2	51.6	2.8
3701	446	5	12.7	15.9	53.2	3.3
3702	446	6	15.2	12.6	49.4	4
3703	446	7	17.4	8.9	39.5	4.8
3704	446	8	19.5	5.2	27.3	6.1
3705	447	1	0	25.3	0	2.4
3706	447	2	4.6	25.5	25.4	2.4
3707	447	3	7.1	25.3	41	2.4
3708	447	4	10.3	24	53.2	2.5
3709	447	5	12.8	21.7	55.8	2.8
3710	447	6	15.3	18.3	53.5	3.6
3711	447	7	17.5	14.7	47.5	4.5
3712	447	8	19.4	11.3	39.1	5.7
3713	448	1	0	4.8	0	3.1
3714	448	2	4.9	4.8	29.8	3.1
3715	448	3	9	4.5	43.7	3.2
3716	448	4	13.1	4	49.1	3.6
3717	448	5	17.4	3.2	46.4	5
3718	448	6	21.8	2.2	35.2	6.8
3719	449	1	0	6.3	0	2.4
3720	449	2	5	6.3	30.2	2.4
3721	449	3	9	6.1	47.2	2.6
3722	449	4	13.2	5.5	54.5	2.8
3723	449	5	17.6	4.5	52.6	3.9
3724	449	6	20.9	3.6	45.6	5.5
3725	450	1	0	8.1	0	1.5
3726	450	2	4.9	8.1	30.6	1.5
3727	450	3	9	7.7	49.9	1.6
3728	450	4	13.1	7.1	58	1.8
3729	450	5	17.5	6	58	2.7
3730	450	6	21	4.9	50.7	4.1
3731	451	1	0	19.5	0	2.3
3732	451	2	15.8	19.4	37.76	2.3
3733	451	3	20.4	19.1	48.2	2.4
3734	451	4	24.8	18.5	57.2	2.6
3735	451	5	29.6	16.9	59.1	3.3
3736	451	6	34.8	14.3	55.3	4.3
3737	451	7	39.1	11.3	47	5.4
3738	451	8	42.7	8.4	36.5	6.2
3739	452	1	0	25.8	0	2
3740	452	2	15.8	25.7	36.85	2
3741	452	3	20.6	25.5	48.9	2
3742	452	4	25.2	24.6	57.6	2.2
3743	452	5	29.7	23	60.6	2.7
3744	452	6	34.9	20.2	59.1	3.6
3745	452	7	39.4	17.1	51.9	4.7
3746	452	8	42.9	14.4	44.8	5.4
3747	453	1	0	33.3	0	1.5
3748	453	2	15.8	33.3	38.71	1.5
3749	453	3	21	32.7	49.7	1.5
3750	453	4	25.2	31.7	58.3	1.7
3751	453	5	29.7	30	62.5	2.1
3752	453	6	35.5	26.5	61.3	3.1
3753	453	7	39.8	23.1	57.2	3.9
3754	453	8	42.7	20.4	52.3	4.6
3755	454	1	0	8.5	0	2.3
3756	454	2	7.5	8.7	36.1	2.3
3757	454	3	12.2	8.4	52.8	2.3
3758	454	4	16.9	7.9	62.1	2.3
3759	454	5	20.9	7	64.5	2.5
3760	454	6	25	6	61.4	3.5
3761	454	7	28.7	4.9	55.5	4.4
3762	454	8	32.4	3.6	45.4	5.6
3763	454	9	34.7	2.7	37.7	7.1
3764	455	1	0	10.4	0	2.3
3765	455	2	7.5	10.6	36.1	2.3
3766	455	3	12.2	10.3	52.8	2.3
3767	455	4	17	9.7	62.1	2.3
3768	455	5	20.9	8.8	66	2.5
3769	455	6	25	7.8	65.2	2.9
3770	455	7	28.7	6.7	60.2	3.8
3771	455	8	32.4	5.4	52	4.8
3772	455	9	34.7	4.5	46.2	5.8
3773	456	1	0	12.6	0	1.5
3774	456	2	7.9	12.6	37.3	1.5
3775	456	3	12.2	12.4	52.8	1.5
3776	456	4	17	11.8	62.1	1.5
3777	456	5	20.9	11	67.6	1.7
3778	456	6	25.1	9.9	68	2.3
3779	456	7	28.8	8.7	64.1	3.1
3780	456	8	32.4	7.5	57.5	4
3781	456	9	34.6	6.6	51.7	4.8
3782	457	1	0	32.8	0	3
3783	457	2	20.2	33.5	35.1	3
3784	457	3	29.3	32.6	54.2	3
3785	457	4	39.9	28.8	62	3
3786	457	5	49.8	22.6	57.8	3.8
3787	457	6	59.2	15.9	45.7	5.4
3788	457	7	66.6	10	32.4	7.2
3789	458	1	0	41	0	2.2
3790	458	2	20.2	41	35.1	2.2
3791	458	3	29.6	39.9	54.2	2.2
3792	458	4	39.9	36	62	2.2
3793	458	5	50	29.9	57.8	3.2
3794	458	6	59.3	23.6	45.7	4.8
3795	458	7	69.9	15.6	32.4	7.4
3796	459	1	0	49.2	0	1.6
3797	459	2	20.1	49.4	35.1	1.6
3798	459	3	29.6	48.3	54.2	1.6
3799	459	4	40.1	44.8	62	1.8
3800	459	5	50	39.5	57.8	2.6
3801	459	6	59.3	33.2	45.7	4
3802	459	7	69.9	24.9	33.85	6.2
3803	460	1	0	9.7	0	2.5
3804	460	2	14	9.6	34.6	2.5
3805	460	3	26.3	9	57.3	2.5
3806	460	4	36.5	8	65	2.7
3807	460	5	48.6	5.9	61.9	3.8
3808	460	6	59.8	3.2	46.5	6.7
3809	461	1	0	12.6	0	1.7
3810	461	2	14.2	12.4	34.6	1.7
3811	461	3	26.3	11.9	57.3	1.7
3812	461	4	36.5	11	66.9	1.7
3813	461	5	49.3	8.8	66.2	3.1
3814	461	6	60	6.4	53.8	5.4
3815	462	1	0	15.9	0	0.6
3816	462	2	14.2	15.9	34.6	0.6
3817	462	3	26.5	15.3	57.7	0.6
3818	462	4	36.5	14.2	70	1
3819	462	5	49.3	12.2	71.5	1.9
3820	462	6	60.1	9.7	62.3	4.7
3821	463	1	15	38.2	0	2
3822	463	2	32.5	38.2	29.2	2
3823	463	3	47.8	37.3	47.7	2
3824	463	4	62.7	34.5	60.4	2
3825	463	5	80.2	29	63.8	2.8
3826	463	6	92.2	23.9	60.4	3.8
3827	463	7	102.3	19.1	53.8	4.4
3828	464	1	15	48.8	0	1
3829	464	2	32.7	48.6	29.2	1
3830	464	3	48	47.6	47.7	1
3831	464	4	62.9	45.1	60.4	1.2
3832	464	5	80.4	39.9	63.8	1.8
3833	464	6	92	35.3	60.4	2.6
3834	464	7	101.9	30.9	53.8	3.2
3835	465	1	15	59.4	0	1
3836	465	2	32.7	59.6	29.2	1
3837	465	3	47.6	59.3	47.7	1
3838	465	4	62.9	57.6	60.4	1.2
3839	465	5	80.4	53.4	63.8	1.8
3840	465	6	92.2	48.8	60.4	2.6
3841	465	7	101.7	44.1	53.8	3.2
3842	466	1	0	57.8	0	0
3843	466	2	100	54	22	0
3844	466	3	200	50.8	42	0
3845	466	4	300	48	58	6
3846	466	5	400	45.8	70	4.6
3847	466	6	500	43.6	78	4.6
3848	466	7	600	40.6	80	7.2
3849	466	8	700	36	74	11.8
3850	467	1	0	35.2	0	5.1
3851	467	2	3132	31.5	30	5.1
3852	467	3	6125	28.9	53	5.1
3853	467	4	10279	24.8	72	8.3
3854	467	5	11011	23.9	77	8.8
3855	467	6	12733	21.5	82	12.2
3856	467	7	14149	18.1	80	12
3857	468	1	0	43.6	0	5.1
3858	468	2	6147	36.3	53	5.1
3859	468	3	8970	34.4	72	6.5
3860	468	4	11062	32.4	82	7.1
3861	468	5	12921	30.2	88	7.9
3862	468	6	13911	28.8	90.5	8.3
3863	468	7	17256	19.8	80	11.9
3864	469	1	0	51.7	0	5.1
3865	469	2	6168	44.9	53	5.1
3866	469	3	9779	42.1	72	5.1
3867	469	4	11932	39.9	82	5.4
3868	469	5	13686	37.6	88	6
3869	469	6	15067	35.3	91.5	7.9
3870	469	7	19021	24.9	80	11.8
3871	470	1	0	152.4	0	21.8
3872	470	2	27.9	150.7	40	21.8
3873	470	3	50.4	145.4	60	21.8
3874	470	4	62	141.4	64	22
3875	470	5	82	131	68	26
3876	470	6	92.9	123.3	68.5	30
3877	470	7	110	107.7	65	45
3878	471	1	0	172.6	0	21.8
3879	471	2	27.9	168.8	40	21.8
3880	471	3	51.9	163.1	60	21.8
3881	471	4	63.1	158.9	64	22
3882	471	5	80.6	150.6	68	24
3883	471	6	97.5	139.5	69.1	28
3884	471	7	118.8	119.9	65.5	45
3885	472	1	0	195.3	0	21.8
3886	472	2	27.8	190.5	40	21.8
3887	472	3	53.8	182.8	60	21.8
3888	472	4	75.6	174.1	67	23
3889	472	5	93.4	164.5	69	27
3890	472	6	104.4	156.9	69.5	31
3891	472	7	129.2	132.3	65.6	45
3892	473	1	0	211.9	0	21.8
3893	473	2	27.7	206.6	40	21.8
3894	473	3	55.4	197.8	60	21.8
3895	473	4	77.1	188.7	67	23
3896	473	5	95.7	177.8	69	26
3897	473	6	109.3	167.8	70	31
3898	473	7	135	140.6	65.7	45
3899	474	1	0	32.49	0	0
3900	474	2	6.27	33.71	14	0
3901	474	3	21.76	34.66	43	0
3902	474	4	55.08	32.8	66	0
3903	474	5	81.79	28.19	71	0
3904	474	6	94.96	24.81	69	0
3905	474	7	101.89	22.04	65	0
3906	475	1	0	78.33	0	0
3907	475	2	12.86	79.55	14	0
3908	475	3	51.44	78.33	52	0
3909	475	4	87.06	72.18	69	0
3910	475	5	123.01	61.11	73.2	0
3911	475	6	142.45	53.4	71	0
3912	475	7	162.58	43.56	65	0
3913	476	1	0	83	0	0
3914	476	2	40	82	44.65	2
3915	476	3	80	79	63.73	2.2
3916	476	4	120	70	71.47	2.5
3917	476	5	160	58	72.19	3.1
3918	476	6	200	42	63.53	4
3919	476	7	240	25	46.67	5.5
3920	477	1	0	23.47	0	2.44
3921	477	2	43.15	23.16	62	2.44
3922	477	3	64.96	22.56	72	2.44
3923	477	4	78.36	20.73	76	2.44
3924	477	5	88.58	19.81	77	3.05
3925	477	6	101.3	18.29	76	2.74
3926	477	7	111.29	16.15	72	3.96
3927	478	1	0	29.26	0	2.44
3928	478	2	44.97	29.26	62	2.44
3929	478	3	67	28.96	72	2.44
3930	478	4	79.04	27.43	76	2.44
3931	478	5	99.93	25.6	77	2.74
3932	478	6	113.56	22.56	76	3.35
3933	478	7	122.65	19.81	72	3.96
3934	479	1	0	32.92	0	2.44
3935	479	2	45.42	32.31	62	2.44
3936	479	3	67.68	31.7	72	2.44
3937	479	4	79.49	30.48	76	2.44
3938	479	5	102.21	28.04	77	2.44
3939	479	6	122.65	25.6	76	3.66
3940	479	7	134.68	22.25	72	3.96
3941	480	1	0	36	0	0
3942	480	2	41	35.17	60	0
3943	480	3	59.1	33.99	70	0
3944	480	4	72.02	32.83	75	0
3945	480	5	83.83	30.85	77	0
3946	480	6	96.39	28.71	77.5	0
3947	480	7	104.89	26.97	77	0
3948	480	8	114.49	24.75	75	0
3949	481	1	0	44.5	0	1.83
3950	481	2	44.97	43.89	60	1.83
3951	481	3	65.87	42.98	70	2.13
3952	481	4	89.94	40.23	77	2.44
3953	481	5	112.43	36.27	79	3.05
3954	481	6	122.65	33.53	78	3.35
3955	481	7	124.46	31.7	77	3.96
3956	482	1	0	49.07	0	1.83
3957	482	2	45.42	48.77	60	1.83
3958	482	3	63.53	47.24	70	2.04
3959	482	4	77.56	45.96	75	2.16
3960	482	5	88.62	44.44	77	2.29
3961	482	6	98.59	42.79	78	2.38
3962	482	7	114.11	39.62	79	2.74
3963	482	8	127.42	36.21	78	2.99
3964	482	9	134.8	34.35	77	3.35
3965	482	10	137.02	33.77	76	3.35
3966	483	1	0	49.1	0	2
3967	483	2	54.3	48.1	60	2
3968	483	3	83.1	46.5	72	2.2
3969	483	4	107	44.1	76	2.5
3970	483	5	125	41.6	78	3.3
3971	483	6	136	39.8	76	4.2
3972	483	7	147	37.7	74	5
3973	484	1	0	62.5	0	2
3974	484	2	59.5	61.6	60	2
3975	484	3	90.1	59.7	72	2.2
3976	484	4	110	57.5	76	2.5
3977	484	5	142	52.5	78	3.2
3978	484	6	154	50.1	77	3.5
3979	484	7	170	46.9	74	5
3980	485	1	0	68.8	0	2
3981	485	2	62.4	67.8	60	2
3982	485	3	93.6	65.4	72	2.2
3983	485	4	114	63	76	2.5
3984	485	5	149	57.6	78	3.3
3985	485	6	168	54	76	4.2
3986	485	7	179	51.7	74	5
3987	486	1	0	72.85	0	0.84
3988	486	2	34.07	71.63	50	0.84
3989	486	3	55.65	70.1	60	0.91
3990	486	4	79.27	68.28	70	1.1
3991	486	5	113.11	62.18	76	1.21
3992	486	6	128.33	56.69	72	1.49
3993	486	7	141.95	50.6	69	2.23
3994	487	1	0	97.54	0	0.84
3995	487	2	34.07	96.93	50	0.84
3996	487	3	59.05	97.23	60	0.84
3997	487	4	88.58	91.44	70	1.02
3998	487	5	135.14	82.3	76	1.39
3999	487	6	147.4	76.2	74	1.58
4000	487	7	158.99	70.1	70	2.23
4001	488	1	0	108.51	0	0.84
4002	488	2	34.07	107.29	50	0.84
4003	488	3	67.91	105.16	60	0.84
4004	488	4	90.85	102.11	70	0.91
4005	488	5	136.27	91.44	76	1.49
4006	488	6	151.49	84.73	74	1.58
4007	488	7	170.34	77.72	69	2.23
4008	489	1	0	46	0	0
4009	489	2	40	46	31.31	0
4010	489	3	80	45.5	52.16	3
4011	489	4	120	44.5	67.62	2.5
4012	489	5	160	43	78.05	3
4013	489	6	200	40	82.19	3.5
4014	489	7	240	36	84.01	5
4015	489	8	280	30	77.52	7
4016	490	1	0	18	0	1.3
4017	490	2	30	19	35	1.3
4018	490	3	70	18	60	1.3
4019	490	4	108	16	68	1.8
4020	490	5	125	14	65	3
4021	490	6	145	11	60	5
4022	490	7	158	9	56	6.1
4023	491	1	0	35	0	1.3
4024	491	2	30	36	35	1.3
4025	491	3	78	35	65	1.3
4026	491	4	143	32	76	3
4027	491	5	183	24	70	5
4028	491	6	196	22	65	5.5
4029	491	7	214	16	58	6.1
4030	492	1	0	39	0	1.3
4031	492	2	30	39	35	1.3
4032	492	3	81	38	65	1.3
4033	492	4	147	35	76	3
4034	492	5	191	28	70	4.8
4035	492	6	209	24	65	5.8
4036	492	7	220	22	60	6.1
4037	493	1	0	164	0	2.2
4038	493	2	40	163	26.9	2.2
4039	493	3	80	160	44.68	2.2
4040	493	4	120	156	57.92	2.2
4041	493	5	160	151	67.12	2.6
4042	493	6	200	144	72.6	3.6
4043	493	7	240	136	75.31	5.2
4044	493	8	280	124	75.02	8
4045	493	9	320	112	73.92	10.4
4046	494	1	0	176.78	0	1.83
4047	494	2	59.05	170.69	50	2.13
4048	494	3	74.95	167.64	55	2.44
4049	494	4	104.48	158.5	62	3.05
4050	494	5	136.27	146.3	64	3.96
4051	494	6	168.07	121.92	62	5.79
4052	494	7	181.7	109.73	58	7.01
4053	495	1	0	316.99	0	1.83
4054	495	2	65.87	310.9	50	2.13
4055	495	3	95.39	304.8	60	2.74
4056	495	4	136.27	286.51	68	3.96
4057	495	5	174.89	262.13	71	6.4
4058	495	6	206.68	231.65	68	10.36
4059	495	7	240.75	195.07	58	15.24
4060	496	1	0	69	0	4
4061	496	2	20	67.5	21.62	3.4
4062	496	3	40	65.5	39.63	2.8
4063	496	4	60	62.5	53.73	2.4
4064	496	5	80	59.5	61.71	2
4065	496	6	100	56	70.91	2
4066	496	7	120	51.5	76.48	2.4
4067	496	8	140	46	77.93	3.2
4068	496	9	160	40	75.76	4.6
4069	497	1	0	5.4	0	0.2
4070	497	2	12.4	5.3	55	0.2
4071	497	3	17.9	5.2	65	0.2
4072	497	4	24.4	4.9	72	0.3
4073	497	5	30.2	4.6	73	0.6
4074	497	6	34.8	4.1	72	1.1
4075	497	7	40.6	3.4	65	2.1
4076	497	8	43	3	60	2.2
4077	497	9	45.8	2.4	58	2.7
4078	498	1	0	7.4	0	0.2
4079	498	2	14.1	7.4	55	0.2
4080	498	3	16.7	7.3	60	0.2
4081	498	4	24.2	7.1	70	0.5
4082	498	5	31.4	6.8	74	0.8
4083	498	6	35.8	6.4	74.5	0.9
4084	498	7	41.2	5.9	74	1.6
4085	498	8	46.2	5.3	65	2.5
4086	498	9	50.2	4.6	65	2.11
4087	498	10	52.9	4.1	60	3
4088	498	11	53.6	3.8	59.85	3.5
4089	499	1	0	9.8	0	0.2
4090	499	2	16.5	9.8	55	0.2
4091	499	3	22.6	9.6	65	0.3
4092	499	4	27.6	9.4	70	0.5
4093	499	5	33.2	9.1	74	1
4094	499	6	37.3	8.9	75.5	1.3
4095	499	7	40.2	8.6	75.6	1.6
4096	499	8	43.2	8.4	75.5	1.7
4097	499	9	47.3	8	74	2.2
4098	499	10	50.6	7.6	72	2.5
4099	499	11	58	6.4	65	3.3
4100	499	12	61.4	5.7	60	3.7
4101	499	13	63	5.3	58.5	4.1
4102	500	1	0	22.7	0	0.9
4103	500	2	24.6	22.4	50	0.9
4104	500	3	28.8	22.4	55	0.9
4105	500	4	34.4	22.1	60	0.9
4106	500	5	40.3	21.5	65	0.9
4107	500	6	49.3	20.7	70	1.4
4108	500	7	66.6	17.8	73.35	2.9
4109	500	8	78.4	15.4	71	4.2
4110	501	1	0	31.3	0	0.9
4111	501	2	26.6	31.1	50	0.9
4112	501	3	36.4	31.1	60	0.9
4113	501	4	41.4	30.9	65	0.9
4114	501	5	50.7	30.3	70	1.4
4115	501	6	60.2	29.4	73	1.7
4116	501	7	74.2	27.1	75.36	2.9
4117	501	8	90.4	23.2	73	3.6
4118	501	9	93.2	22.4	72	4.4
4119	502	1	0	42.2	0	0.9
4120	502	2	29.4	42.2	50	0.9
4121	502	3	33.6	42.1	55	0.9
4122	502	4	44.8	41.9	65	0.9
4123	502	5	53.7	41.4	70	1.1
4124	502	6	61.3	40.7	73	1.4
4125	502	7	69.1	39.9	75	1.7
4126	502	8	83.4	37.4	77	2.4
4127	502	9	87	36.7	77.21	2.6
4128	502	10	89.8	36.1	77	2.7
4129	502	11	101	33.2	75	3.2
4130	502	12	107.2	31.5	73	3.8
4131	502	13	112	30.1	72	4.1
4132	503	1	0	10.8	0	4.2
4133	503	2	19.1	10.6	55	4.2
4134	503	3	23	10.4	60	4.5
4135	503	4	29	9.9	65	5.3
4136	503	5	35.5	9.1	67.5	6.4
4137	503	6	41.8	8.1	65	8
4138	503	7	47.5	7	60	9.8
4139	503	8	50.6	6.4	55	11.7
4140	503	9	51.9	6	54	13.1
4141	504	1	0	12.1	0	2.8
4142	504	2	18.2	12.1	55	2.8
4143	504	3	21.7	11.9	60	3.1
4144	504	4	26.4	11.6	65	3.4
4145	504	5	37	10.4	70	5.3
4146	504	6	46.7	8.7	65	8.1
4147	504	7	51.1	7.6	60	9.5
4148	504	8	54	6.9	55	11.9
4149	504	9	56.2	6.3	54	13.4
4150	505	1	0	13.1	0	1.9
4151	505	2	17.3	13.2	55	2.2
4152	505	3	20.8	13.2	60	2.2
4153	505	4	24.9	13.1	65	2.5
4154	505	5	31.5	12.6	70	3.6
4155	505	6	38.1	11.8	72	4.7
4156	505	7	45.5	10.6	70	6.6
4157	505	8	50.8	9.4	65	8.4
4158	505	9	54.6	8.4	60	9.4
4159	505	10	57.5	7.6	55	10.8
4160	505	11	59.4	7	53	13
4161	506	1	0	14.7	0	1.6
4162	506	2	16.6	14.8	55	1.7
4163	506	3	19.8	14.8	60	1.7
4164	506	4	23.6	14.6	65	1.9
4165	506	5	29.5	14.3	70	2.3
4166	506	6	33.6	13.9	72	3
4167	506	7	39.5	13.1	72.7	3.9
4168	506	8	46.4	12	72	5.6
4169	506	9	49.4	11.4	70	6.7
4170	506	10	54.6	10.2	65	7.8
4171	506	11	58.2	9.4	60	9.8
4172	506	12	61.5	8.5	55	11.6
4173	506	13	63.1	8	54	13.1
4174	507	1	0	17	0	0.8
4175	507	2	15.8	17	55	1.1
4176	507	3	22.7	16.9	65	1.2
4177	507	4	28.5	16.6	70	1.4
4178	507	5	35.5	15.9	73	2.2
4179	507	6	40.6	15.1	74	2.5
4180	507	7	44.4	14.5	73	3.4
4181	507	8	49.9	13.4	72	5
4182	507	9	58.5	11.3	65	8.6
4183	507	10	61.9	10.3	60	9.7
4184	507	11	65	9.4	55	11.7
4185	507	12	66.5	9	54	13.4
4186	508	1	0	44.3	0	2.7
4187	508	2	27.4	45.4	50	2.7
4188	508	3	38.2	45	60	2.5
4189	508	4	47.2	44	65	2.7
4190	508	5	52.8	43.2	68	3
4191	508	6	60.3	41.8	70	3.3
4192	508	7	67.4	40.1	71	3.9
4193	508	8	74.6	38	70	5.3
4194	508	9	81.8	35.7	69	8.8
4195	509	1	0	50	0	2.3
4196	509	2	26.2	51.4	50	2.3
4197	509	3	36.9	50.9	60	2.2
4198	509	4	45.1	50.1	65	2
4199	509	5	57.4	48.3	70	2.7
4200	509	6	69.5	45.3	72.85	3
4201	509	7	84.1	41.2	70	6.4
4202	509	8	89	39.3	68	8.9
4203	510	1	0	56.7	0	2
4204	510	2	25.4	58.2	50	1.9
4205	510	3	35.9	57.7	60	1.9
4206	510	4	44.1	56.9	65	2
4207	510	5	55.4	55	70	2.3
4208	510	6	62.6	53.6	72	2.3
4209	510	7	74.4	50.6	74.85	2.5
4210	510	8	86.4	46.8	72	4.8
4211	510	9	92.1	44.8	70	7.5
4212	510	10	95.4	43.5	69	9.4
4213	511	1	0	70.4	0	1.7
4214	511	2	25.6	71.7	50	1.6
4215	511	3	35.9	71.5	60	1.6
4216	511	4	43.8	71.2	65	1.6
4217	511	5	53.6	69.9	70	1.7
4218	511	6	60.8	68.8	72	1.7
4219	511	7	68.2	67.6	74	2.2
4220	511	8	78.2	65.7	75	2.5
4221	511	9	84.6	64.3	75.5	2.8
4222	511	10	89.5	63.2	75	3.3
4223	511	11	96.9	61.3	74	3.9
4224	511	12	103.6	59.1	72	5.2
4225	511	13	109.7	55.6	69	8.9
4226	512	1	0	14.9	0	1.2
4227	512	2	11.4	14.8	50	0.9
4228	512	3	16.4	14.8	60	0.8
4229	512	4	25.3	14.2	70	0.8
4230	512	5	32.5	13.4	72.55	1.7
4231	512	6	40.1	11.9	70	3
4232	512	7	45.5	10.5	65	4.4
4233	512	8	48.6	9.3	60	5.5
4234	512	9	50.9	8.4	55	6.2
4235	512	10	53.3	7.2	49	7.7
4236	513	1	0	16.9	0	1.2
4237	513	2	11.9	16.9	50	0.9
4238	513	3	17.1	16.9	60	0.6
4239	513	4	25.9	16.3	70	0.9
4240	513	5	30	15.8	72	1.2
4241	513	6	34	15.4	73.4	1.2
4242	513	7	38.8	14.5	72	1.8
4243	513	8	48.7	12	65	4.1
4244	513	9	54.4	9.7	55	7.1
4245	513	10	55.5	9.1	54	7.9
4246	514	1	0	18.6	0	1.1
4247	514	2	12.4	18.6	50	0.9
4248	514	3	15.1	18.6	55	0.9
4249	514	4	20.9	18.4	65	0.8
4250	514	5	30.3	17.7	72	1.2
4251	514	6	35	17.2	73.55	1.7
4252	514	7	37.6	16.7	73	2
4253	514	8	41.3	16.1	72	2.6
4254	514	9	45.5	15.1	70	3.5
4255	514	10	51.2	13.4	65	5.3
4256	514	11	54.7	12	60	6.1
4257	514	12	57.7	10.6	54.89	7.3
4258	515	1	0	21.8	0	1.1
4259	515	2	13.8	21.9	50	0.9
4260	515	3	19.9	21.6	60	0.9
4261	515	4	28.5	21.2	70	0.8
4262	515	5	35.3	20.5	73	1.1
4263	515	6	38	20.1	73.55	1.4
4264	515	7	44.8	19.1	72	2.1
4265	515	8	55.6	16.2	65	4.7
4266	515	9	60.1	14.7	60	5.9
4267	515	10	62.3	13.8	55.45	7.1
4268	516	1	0	64.9	0	2.2
4269	516	2	24.9	65.1	50	2.2
4270	516	3	34.5	64.6	60	2.1
4271	516	4	46.6	63.5	68	2.2
4272	516	5	56.5	61.9	72	2.7
4273	516	6	68	59.1	73.5	3.4
4274	516	7	79.8	55	72	4.9
4275	516	8	84.6	52.6	70	5.8
4276	516	9	91.3	47.9	65	7
4277	516	10	97.7	41.5	61	8.8
4278	517	1	0	78	0	2.4
4279	517	2	27	78.1	50	2.2
4280	517	3	32.1	78.1	55	2.1
4281	517	4	45	77.5	65	2.2
4282	517	5	55.1	76.6	70	2.5
4283	517	6	71.2	74	73.5	3.7
4284	517	7	77.6	72.5	73.55	4.3
4285	517	8	83.5	70.5	73.5	4.8
4286	517	9	89.4	68.4	72	5.8
4287	517	10	95.3	65.4	70	6.7
4288	517	11	98.5	63.4	68	7.9
4289	517	12	101.2	61.6	65	8.7
4290	517	13	103.8	58.7	63	9.4
4291	518	1	0	93	0	2.2
4292	518	2	30.2	92.6	50	2.2
4293	518	3	43.1	91.5	60	2.2
4294	518	4	57.8	89.8	68	2.5
4295	518	5	69.6	88	72	3
4296	518	6	80.3	85.4	72.55	4
4297	518	7	88.3	83	72	5.2
4298	518	8	96.9	79.7	70	6.4
4299	518	9	103.6	76.5	68	7.3
4300	518	10	108.9	73.3	64	8.5
4301	519	1	0	26	0	2.5
4302	519	2	13.2	25.8	40	2.5
4303	519	3	27	25	62	3
4304	519	4	32	24.2	64	3.75
4305	519	5	39	22.5	64	5
4306	519	6	43	21	62	6.75
4307	519	7	46	19.8	58	7.5
4308	520	1	0	38.5	0	2.5
4309	520	2	14	38.5	40	2.5
4310	520	3	30	37.5	62	3
4311	520	4	38.5	35.5	64	3.75
4312	520	5	42	34.5	64	5
4313	520	6	48	31	62	6.75
4314	520	7	50	28.5	58	7.5
4315	521	1	0	33.74	0	0
4316	521	2	19.6	35.27	26	0
4317	521	3	49.67	35.84	56	0
4318	521	4	105.23	31.3	73	0
4319	521	5	134.64	25.85	74	0
4320	521	6	154.24	21.31	72	0
4321	521	7	162.73	18.26	70	0
4322	522	1	0	75.01	0	0
4323	522	2	32.68	78.03	27	0
4324	522	3	81.04	77.72	56	0
4325	522	4	133.98	70.74	71	0
4326	522	5	200.66	55.87	76.5	0
4327	522	6	229.4	44.35	74	0
4328	522	7	261.65	35.36	68	0
4329	523	1	0	22.77	0	1.1
4330	523	2	61.96	22.71	60	1.1
4331	523	3	85.76	22.25	70	1.19
4332	523	4	113.24	21.18	76	1.32
4333	523	5	145.86	19.14	79	1.64
4334	523	6	168.12	17.56	74	2
4335	523	7	179.02	16.46	70	2.23
4336	524	1	0	29.5	0	1.1
4337	524	2	66.46	29.14	60	1.1
4338	524	3	91.6	28.41	70	1.15
4339	524	4	119.08	27.28	76	1.28
4340	524	5	161.53	24.63	79	1.56
4341	524	6	193.19	22.4	76	1.95
4342	524	7	207.14	21.12	70	2.23
4343	525	1	0	32.31	0	1.1
4344	525	2	70.36	32	60	1.1
4345	525	3	99.09	31.39	70	1.12
4346	525	4	124.9	30.48	76	1.25
4347	525	5	174.02	27.61	79	1.58
4348	525	6	204	24.78	76	1.9
4349	525	7	216.5	23.38	70	2.23
4350	526	1	0	33.2	0	1.12
4351	526	2	79	32.6	60	1.12
4352	526	3	116	31.8	70	1.18
4353	526	4	158	30.1	76	1.35
4354	526	5	187	28.4	78	1.5
4355	526	6	224	25.6	74	1.9
4356	526	7	247	23.3	70	2.4
4357	527	1	0	41.6	0	1.12
4358	527	2	83.3	41	60	1.12
4359	527	3	120	40.2	70	1.21
4360	527	4	161	38.7	76	1.38
4361	527	5	196	36.2	78	1.58
4362	527	6	229	32.8	76	1.86
4363	527	7	264	28.6	70	2.4
4364	528	1	0	45.4	0	1.12
4365	528	2	91	44.9	60	1.12
4366	528	3	131	44	70	1.21
4367	528	4	173	42.3	76	1.38
4368	528	5	216	39.5	78	1.58
4369	528	6	256	35.8	76	1.86
4370	528	7	292	31.4	70	2.4
4371	529	1	0	48.77	0	0.98
4372	529	2	85.4	48.77	60	0.98
4373	529	3	124.01	47.24	74	1.07
4374	529	4	169.44	42.06	78.5	1.22
4375	529	5	199.42	34.14	74	1.77
4376	529	6	215.77	30.48	70	1.83
4377	529	7	225.99	25.91	66	2.26
4378	530	1	0	60.35	0	0.98
4379	530	2	79.49	60.35	60	0.98
4380	530	3	124.92	57.91	74	0.98
4381	530	4	181.7	51.21	79.5	1.22
4382	530	5	223.72	42.06	74	1.77
4383	530	6	236.21	38.1	70	1.83
4384	530	7	241.89	33.53	66	2.26
4385	531	1	0	67.06	0	0.98
4386	531	2	87.67	66.75	60	0.98
4387	531	3	135.59	64.01	74	1.07
4388	531	4	193.06	57.3	80	1.22
4389	531	5	236.89	47.55	74	1.77
4390	531	6	249.61	43.28	70	1.83
4391	531	7	260.97	39.32	66	2.26
4392	532	1	0	73.2	0	0
4393	532	2	89.3	71.8	60	0
4394	532	3	130.3	69.3	70	0
4395	532	4	155.9	67.4	74	0
4396	532	5	185.9	64.4	76	0
4397	532	6	200.5	61.9	76.5	0
4398	532	7	238.8	55.1	74	0
4399	532	8	260.7	49.9	70	0
4400	533	1	0	86	0	0
4401	533	2	94.8	84.7	60	0
4402	533	3	113	83.6	65	0
4403	533	4	145.8	81.4	72	0
4404	533	5	182.3	78.1	76	0
4405	533	6	206.9	75.3	77	0
4406	533	7	216	74.2	77.2	0
4407	533	8	235.2	71.2	77	0
4408	533	9	247.9	69	76	0
4409	533	10	265.2	64.9	74	0
4410	533	11	288	58.4	70	0
4411	534	1	0	109.3	0	3.6
4412	534	2	110.3	106.6	60	3.5
4413	534	3	153.1	103.6	70	3.7
4414	534	4	182.3	101.6	74	4
4415	534	5	209.6	98.4	77	4.2
4416	534	6	245.2	92.3	78	4.7
4417	534	7	280.7	85.5	76	5.4
4418	534	8	315.4	77.3	72	6.3
4419	534	9	328.1	73.2	70	6.8
4420	535	1	0	12	0	0
4421	535	2	88.23	11.68	51.5	0
4422	535	3	110.9	11.36	55.5	0
4423	535	4	178	8.63	61.5	0
4424	535	5	213.8	5.12	60	0
4425	536	1	0	29.01	0	0
4426	536	2	59.2	28.48	51.5	0
4427	536	3	95.27	27.58	61.5	0
4428	536	4	157.4	24.01	70	0
4429	536	5	196.1	20.49	73	0
4430	536	6	257.5	13.28	67	0
4431	536	7	277.8	9.24	61	0
4432	537	1	0	42.29	0	2.3
4433	537	2	66.33	41.51	51.5	2.3
4434	537	3	114.2	40.12	67	3
4435	537	4	167.5	37.63	75	4
4436	537	5	229.7	31.09	81	5
4437	537	6	284.9	23.28	74	8
4438	537	7	319.9	16.3	60	10
4439	538	1	0	47.02	0	0
4440	538	2	174.7	45.77	51.5	0
4441	538	3	219.5	44.51	55.5	0
4442	538	4	352.4	33.82	61.5	0
4443	538	5	423.1	20.06	60	0
4444	539	1	0	113.7	0	0
4445	539	2	117.2	111.6	51.5	0
4446	539	3	188.6	108.1	61.5	0
4447	539	4	311.6	94.08	70	0
4448	539	5	388.2	80.29	73	0
4449	539	6	509.8	52.04	67	0
4450	539	7	549.9	36.21	61	0
4451	540	1	0	165.7	0	9.01
4452	540	2	131.3	162.7	51.5	9.01
4453	540	3	226	157.2	67	11.76
4454	540	4	331.5	147.5	75	15.67
4455	540	5	454.7	121.8	81	19.59
4456	540	6	563.9	91.22	74	31.35
4457	540	7	633.2	63.87	60	39.18
4458	541	1	0	12	0	0
4459	541	2	88.23	11.68	51.5	0
4460	541	3	110.9	11.36	55.5	0
4461	541	4	178	8.63	61.5	0
4462	541	5	213.8	5.12	60	0
4463	542	1	0	29.01	0	0
4464	542	2	59.2	28.48	51.5	0
4465	542	3	95.27	27.58	61.5	0
4466	542	4	157.4	24.01	70	0
4467	542	5	196.1	20.49	73	0
4468	542	6	257.5	13.28	67	0
4469	542	7	277.8	9.24	61	0
4470	543	1	0	42.29	0	2.3
4471	543	2	66.33	41.51	51.5	2.3
4472	543	3	114.2	40.12	67	3
4473	543	4	167.5	37.63	75	4
4474	543	5	229.7	31.09	81	5
4475	543	6	284.9	23.28	74	8
4476	543	7	319.9	16.3	60	10
4477	544	1	0	47.02	0	0
4478	544	2	174.7	45.77	51.5	0
4479	544	3	219.5	44.51	55.5	0
4480	544	4	352.4	33.82	61.5	0
4481	544	5	423.1	20.06	60	0
4482	545	1	0	113.7	0	0
4483	545	2	117.2	111.6	51.5	0
4484	545	3	188.6	108.1	61.5	0
4485	545	4	311.6	94.08	70	0
4486	545	5	388.2	80.29	73	0
4487	545	6	509.8	52.04	67	0
4488	545	7	549.9	36.21	61	0
4489	546	1	0	165.7	0	9.01
4490	546	2	131.3	162.7	51.5	9.01
4491	546	3	226	157.2	67	11.76
4492	546	4	331.5	147.5	75	15.67
4493	546	5	454.7	121.8	81	19.59
4494	546	6	563.9	91.22	74	31.35
4495	546	7	633.2	63.87	60	39.18
4496	547	1	0	21.3	0	0
4497	547	2	51.3	21.8	47	0
4498	547	3	82.1	21.4	60	0
4499	547	4	105.4	20.7	65	0
4500	547	5	146.9	18.5	68	0
4501	547	6	183	15.7	65	0
4502	547	7	191.7	15	63	0
4503	548	1	0	41.1	0	0
4504	548	2	111.5	42	68	0
4505	548	3	196.7	36.8	76	0
4506	548	4	240.8	32.7	75	0
4507	548	5	267	29.25	70	0
4508	548	6	284.7	26.2	65	0
4509	548	7	300	22.9	59	0
4510	549	1	0	8.8	0	0
4511	549	2	54.6	8.96	46	0
4512	549	3	82	8.8	56	0
4513	549	4	111.7	8.4	65	0
4514	549	5	140.9	7.6	70	0
4515	549	6	176.1	6.18	65	0
4516	549	7	204.7	4.29	54	0
4517	550	1	0	15.8	0	0
4518	550	2	54.7	16	46	0
4519	550	3	108.1	15.9	65	0
4520	550	4	147.9	15.3	75	0
4521	550	5	198.8	13.6	79	0
4522	550	6	240.6	11	75	0
4523	550	7	278.1	7.5	59	0
4524	551	1	0	95.76	0	0
4525	551	2	117	92.28	54	0
4526	551	3	150	87.51	58.4	0
4527	551	4	180	82.82	61.2	0
4528	551	5	234	70.22	61.4	0
4529	551	6	258	61.72	57.4	0
4530	551	7	328	34.08	38.3	0
4531	552	1	0	13.9	0	2.6
4532	552	2	35.1	13.7	55	2.3
4533	552	3	41.5	13.4	60	2.3
4534	552	4	50.8	12.7	65	2.3
4535	552	5	75.5	10.3	70.6	3.5
4536	552	6	106.2	5.6	61	9.1
4537	553	1	0	17.6	0	2.6
4538	553	2	34.8	17.6	55	2
4539	553	3	41.1	17.4	60	1.8
4540	553	4	49.3	17	65	1.8
4541	553	5	58.7	16.4	70	2
4542	553	6	76.3	15	75	2.9
4543	553	7	86.4	13.8	76.75	4.1
4544	553	8	95	12.5	75	5.3
4545	553	9	108	10.3	70	6.7
4546	553	10	115.9	8.8	62	9.1
4547	554	1	0	21.3	0	2.3
4548	554	2	35.1	21.3	55	1.7
4549	554	3	48.6	21.2	65	1.7
4550	554	4	55.3	20.9	70	1.7
4551	554	5	68	20.1	75	1.7
4552	554	6	82.2	19.1	80	2.7
4553	554	7	95	17.6	80.67	4.1
4554	554	8	108.8	15.6	80	4.8
4555	554	9	116.6	14.3	75	6.7
4556	554	10	127.1	12.4	69.85	8.9
4557	555	1	0	26.6	0	1.7
4558	555	2	35.9	26.5	55	1.1
4559	555	3	41.5	26.5	60	1.2
4560	555	4	55.7	26.4	70	1.1
4561	555	5	66.9	26	75	1.2
4562	555	6	77.4	25.3	80	1.7
4563	555	7	92	24	81	2.4
4564	555	8	103.9	22.7	81.5	3.5
4565	555	9	112.1	21.6	81	4.2
4566	555	10	125.6	19.5	80	5.9
4567	555	11	132.7	18	75	6.8
4568	555	12	138.7	16.9	71	8.6
4569	556	1	0	5.7	0	5.9
4570	556	2	18.8	5.6	50	5.9
4571	556	3	22.1	5.6	55	5.9
4572	556	4	25.4	5.5	60	5.9
4573	556	5	30.3	5.3	65	5.9
4574	556	6	43.4	4.6	70.1	7
4575	556	7	55	3.7	66	9.2
4576	557	1	0	6.6	0	5
4577	557	2	18	6.6	50	5
4578	557	3	23.7	6.6	60	5
4579	557	4	28.4	6.5	65	5
4580	557	5	36.2	6.2	70	5.2
4581	557	6	45	5.8	73	6.2
4582	557	7	48.9	5.5	73.05	6.7
4583	557	8	52.4	5.3	73	7.4
4584	557	9	58.3	4.7	70	8.2
4585	557	10	60.8	4.5	68.65	9.4
4586	558	1	0	7.9	0	3.8
4587	558	2	17.2	7.9	50	3.9
4588	558	3	19.8	7.9	55	3.8
4589	558	4	27.6	7.8	65	3.8
4590	558	5	34.4	7.6	70	3.8
4591	558	6	38.9	7.5	73	4.1
4592	558	7	48.3	6.9	76	4.7
4593	558	8	51.5	6.7	76.05	5.8
4594	558	9	55	6.4	79	6.2
4595	558	10	63	5.7	73	8
4596	558	11	66.5	5.3	70	8.9
4597	559	1	0	9.4	0	2.6
4598	559	2	17.4	9.3	50	2.4
4599	559	3	23.7	9.3	60	2.3
4600	559	4	34.4	9.2	70	2.7
4601	559	5	38.5	9	73	2.9
4602	559	6	44.8	8.7	76	3.5
4603	559	7	54.8	8.1	78	5
4604	559	8	66.5	7.1	76	7
4605	559	9	72	6.5	73	8.2
4606	559	10	73.4	6.3	72.65	9.4
4607	560	1	0	10.8	0	1.4
4608	560	2	18.4	10.9	50	1.5
4609	560	3	22.3	10.9	55	1.5
4610	560	4	30.5	10.8	65	1.2
4611	560	5	40.5	10.5	73	1.7
4612	560	6	49.7	10	78	2.4
4613	560	7	58.3	9.3	79	4.1
4614	560	8	66.3	8.6	78	5.5
4615	560	9	71.8	8	76	6.8
4616	560	10	78.5	7.2	72.95	9.1
4617	561	1	0	24.6	0	1.2
4618	561	2	32.2	24.4	50	1.2
4619	561	3	40.6	24.2	55	1.4
4620	561	4	47.5	23.8	60	1.4
4621	561	5	57.8	23.2	65	1.4
4622	561	6	86.9	19.8	70.58	2.6
4623	561	7	110.6	15.5	64	5.8
4624	562	1	0	29.3	0	1.2
4625	562	2	32.5	29.3	50	1.2
4626	562	3	47.8	28.8	60	1.2
4627	562	4	58.2	28.3	65	1.4
4628	562	5	72	27.2	70	1.5
4629	562	6	95.3	24.2	75.84	3.15
4630	562	7	120.2	19.9	70	6.9
4631	562	8	122.5	19.2	69	8.9
4632	563	1	0	34.2	0	1.2
4633	563	2	33.7	34.3	50	1.2
4634	563	3	41.3	34.1	55	1.2
4635	563	4	58.9	33.6	65	1.4
4636	563	5	69.3	33	70	1.4
4637	563	6	81.1	32.1	75	1.7
4638	563	7	96.1	30.2	77	2.6
4639	563	8	102.2	29.3	77.64	3.2
4640	563	9	108.7	28.3	77	4.2
4641	563	10	122.9	25.5	75	6.2
4642	563	11	136.3	22.6	69.97	9.4
4643	564	1	0	38.7	0	1.2
4644	564	2	36	38.7	50	1.4
4645	564	3	50.5	38.7	60	1.4
4646	564	4	69.3	38.1	70	1.4
4647	564	5	81.1	37.5	75	1.7
4648	564	6	93.8	36.3	77	2.5
4649	564	7	107.2	34.6	78.65	3.7
4650	564	8	123.3	32	77	5.4
4651	564	9	134	30	75	7.4
4652	564	10	146.2	27.2	70	10
4653	564	11	148.5	26.8	69.95	10.5
4654	565	1	0	43.7	0	1.2
4655	565	2	39.4	43.8	50	1.7
4656	565	3	45.9	43.7	55	1.5
4657	565	4	63.2	43.3	65	1.4
4658	565	5	84.6	42	75	1.5
4659	565	6	96.5	40.8	77	2.3
4660	565	7	106.4	39.5	78	2.8
4661	565	8	113.3	38.4	79	3.4
4662	565	9	120.6	37.1	78	4
4663	565	10	125.2	36.2	77	4.9
4664	565	11	135.1	34.2	75	5.8
4665	565	12	150.4	30.7	70	8.2
4666	565	13	156.2	29.3	68	9.5
4667	566	1	0	54.33	0	1
4668	566	2	32	53.83	63.98	1
4669	566	3	44	52.33	72.98	2
4670	566	4	56	50	76.92	2.5
4671	566	5	64	47.67	78.96	3.5
4672	566	6	72	44.33	76.97	5.5
4673	566	7	84	37.33	68.96	8.5
4674	567	1	0	10.2	0	2.5
4675	567	2	18.6	10.1	50	2.5
4676	567	3	23.6	10.1	60	2.6
4677	567	4	28.4	10	65	2.8
4678	567	5	33.1	9.9	70	2.9
4679	567	6	39.8	9.6	73	3.7
4680	567	7	51.4	8.7	74.55	5.4
4681	567	8	61.3	7.5	73	7.4
4682	567	9	65.2	6.9	70	9.1
4683	568	1	0	13.9	0	2
4684	568	2	20.1	13.9	50	2
4685	568	3	23.2	13.8	55	2
4686	568	4	31.7	13.7	65	2.3
4687	568	5	42	13.3	73	2.6
4688	568	6	50.7	12.8	76	3.4
4689	568	7	59.8	12	78	4.8
4690	568	8	62.5	11.8	78.05	5.4
4691	568	9	64.8	11.5	78	5.8
4692	568	10	70.4	10.6	76	7.2
4693	568	11	74.3	9.8	73	8
4694	568	12	76.8	9.3	70	9.1
4695	568	13	77.6	9.1	69.85	9.2
4696	569	1	0	16.6	0	1.2
4697	569	2	21.5	16.6	50	0.8
4698	569	3	29.4	16.5	60	0.9
4699	569	4	40	16.2	70	1.4
4700	569	5	50.9	15.7	76	2.2
4701	569	6	59.2	15.1	78	3.2
4702	569	7	65.4	14.5	79	3.7
4703	569	8	71	13.8	78	5.4
4704	569	9	76.2	13	76	5.7
4705	569	10	80.8	12.1	73	6.9
4706	569	11	83.4	11.5	70	7.7
4707	569	12	85.7	11	66	8.3
4708	570	1	0	42	0	1.4
4709	570	2	37.2	42.3	50	1.4
4710	570	3	43.2	42.3	55	1.6
4711	570	4	52.2	42.1	60	1.9
4712	570	5	62.3	41.5	65	2.2
4713	570	6	77.4	40.2	70	3.1
4714	570	7	90.1	38.3	73	3.8
4715	570	8	104	35.6	74.55	4.7
4716	570	9	115.7	33.1	73	5.9
4717	570	10	130	28.7	71	7.2
4718	571	1	0	45.8	0	1.4
4719	571	2	37.2	46.1	50	1.1
4720	571	3	52.2	46.1	60	1.6
4721	571	4	77.7	44.8	70	2.8
4722	571	5	90.1	43.2	73	3.8
4723	571	6	108.9	40.1	75.85	4.7
4724	571	7	127.3	35.6	73	6.6
4725	571	8	134.5	33.8	72	7.8
4726	572	1	0	56.4	0	1.4
4727	572	2	38.7	56.7	50	1.6
4728	572	3	54.1	56.7	60	1.6
4729	572	4	78.5	55.2	70	2.3
4730	572	5	90.9	54	73	2.8
4731	572	6	99.5	52.7	75	3.4
4732	572	7	120.6	48.9	77.35	4.8
4733	572	8	137.1	45	75	6.2
4734	572	9	144.6	42.9	73	7.3
4735	573	1	0	62.2	0	1.6
4736	573	2	40.9	62.7	50	1.4
4737	573	3	47.3	62.5	55	1.6
4738	573	4	66.5	62.4	65	1.7
4739	573	5	92.4	60	73	2.8
4740	573	6	100.7	58.9	75	3.4
4741	573	7	114.9	56.5	77	4.4
4742	573	8	126.2	54.3	77.76	5
4743	573	9	137.1	51.8	77	5.9
4744	573	10	146.5	49.4	75	7
4745	573	11	149.5	48.4	74	7.5
4746	574	1	0	69.2	0	1.4
4747	574	2	43.6	69.5	50	0.9
4748	574	3	50.7	69.5	55	0.9
4749	574	4	69.1	69	65	1.6
4750	574	5	82.3	68	70	2.2
4751	574	6	94.3	66.8	73	2.8
4752	574	7	102.9	65.7	75	3.3
4753	574	8	116.8	63.6	77	4.1
4754	574	9	130.7	60.9	78	5.2
4755	574	10	146.1	57.6	77	6.4
4756	574	11	156.6	54.9	75	7.7
4757	575	1	0	16.1	0	1.4
4758	575	2	18.7	16.3	50	1.4
4759	575	3	23.1	16.3	55	1.4
4760	575	4	27.9	16.2	60	1.4
4761	575	5	34	16	65	1.8
4762	575	6	42.4	15.5	70	1.8
4763	575	7	48.7	14.9	72	2
4764	575	8	53.8	14.2	73	2.1
4765	575	9	59.4	13.5	72	2.7
4766	575	10	64.1	12.7	70	3.3
4767	575	11	72.7	11.1	66	5.3
4768	576	1	0	19.6	0	1.5
4769	576	2	18.7	19.7	50	1.5
4770	576	3	22.3	19.7	55	1.4
4771	576	4	26.5	19.7	60	1.4
4772	576	5	31.5	19.7	65	1.7
4773	576	6	38.9	19.5	70	2
4774	576	7	42	19.3	72	2
4775	576	8	47.9	18.9	74	2.1
4776	576	9	58.8	17.7	75	2.4
4777	576	10	69.1	16.3	74	3.6
4778	576	11	75.4	15.1	72	4.8
4779	576	12	79.2	14.4	70	5.9
4780	576	13	80.9	14	69	6.7
4781	577	1	0	24.5	0	1.4
4782	577	2	19.5	24.7	50	1.4
4783	577	3	27.3	24.6	60	1.4
4784	577	4	39.5	24.3	70	2
4785	577	5	47.9	23.7	74	2.1
4786	577	6	52.1	23.3	75	2.3
4787	577	7	60.5	22.3	76	2.6
4788	577	8	64.9	21.7	76.55	2.7
4789	577	9	68.5	21.2	76	3
4790	577	10	79.2	19.3	74	4.5
4791	577	11	84.2	18.3	72	4.8
4792	577	12	87.8	17.6	70	6.1
4793	577	13	89.5	17.2	69	6.8
4794	578	1	0	67.7	0	1.5
4795	578	2	42.5	67.5	50	1.7
4796	578	3	50.7	67.3	55	1.5
4797	578	4	61.9	66.7	60	1.5
4798	578	5	77.2	65.3	65	1.7
4799	578	6	87.3	63.8	68	1.8
4800	578	7	98.8	61.6	70	2.2
4801	578	8	105.5	60	70.1	2.5
4802	578	9	112.3	58.5	70	2.6
4803	578	10	124.2	55	68	3.5
4804	578	11	139.1	50.1	62	4.8
4805	579	1	0	73.5	0	1.5
4806	579	2	43.3	73.4	50	1.7
4807	579	3	63.8	72.8	60	1.5
4808	579	4	79.1	71.4	65	1.5
4809	579	5	89.5	70.1	68	1.6
4810	579	6	99.6	68.2	70	1.6
4811	579	7	113.8	65.2	71.65	2
4812	579	8	129.8	60.7	70	2.2
4813	579	9	140.2	57.4	68	3.5
4814	579	10	148.1	54.6	63	4.6
4815	580	1	0	80.2	0	0
4816	580	2	44.8	80.1	50	1.7
4817	580	3	65.6	79.7	60	1.5
4818	580	4	80.9	78.4	65	1.7
4819	580	5	92.1	77	68	1.8
4820	580	6	101.1	75.5	70	2.3
4821	580	7	120.5	71.4	72.4	2.9
4822	580	8	146.6	64.1	70	4.9
4823	580	9	157.4	60.3	67.97	6
4824	581	1	0	87.5	0	1.5
4825	581	2	46.6	87.2	50	1.7
4826	581	3	55.2	87.3	55	1.5
4827	581	4	67.9	86.9	60	1.5
4828	581	5	95.5	84.4	68	2
4829	581	6	103.3	83.1	70	2.2
4830	581	7	116.4	80.8	72	2.9
4831	581	8	130.9	77.4	73	3.7
4832	581	9	146.6	72.7	72	4.8
4833	581	10	160.7	67.8	70	6
4834	581	11	166.3	65.7	68.32	6.9
4835	582	1	0	96.7	0	1.7
4836	582	2	49.6	96.7	50	1.7
4837	582	3	58.6	96.5	55	1.7
4838	582	4	88	95.3	65	1.8
4839	582	5	107.4	92.9	70	2.5
4840	582	6	118.6	91.1	72	2.8
4841	582	7	136.9	86.5	74	4
4842	582	8	142.1	85	74.25	4.2
4843	582	9	147.3	83.6	74	4.5
4844	582	10	164.8	77.3	72	6
4845	582	11	175.7	73	70	6.9
4846	582	12	177.9	72	69	7.7
4847	583	1	0	26.5	0	2.1
4848	583	2	32.7	26.5	55	2.1
4849	583	3	40.6	26.4	60	2.1
4850	583	4	48.5	26.2	65	2.1
4851	583	5	52.6	26	67	2.1
4852	583	6	61.2	25.5	70	2.4
4853	583	7	73.2	24.3	70.25	2.5
4854	583	8	87.5	22.4	70	3.4
4855	583	9	96.9	20.8	67	4
4856	583	10	101	20	65	4.5
4857	584	1	0	31.3	0	1.8
4858	584	2	35.3	31.3	55	1.8
4859	584	3	42.8	31.3	60	1.8
4860	584	4	58.6	30.9	67	1.6
4861	584	5	67.6	30.4	70	1.8
4862	584	6	76.2	29.7	71	2.2
4863	584	7	85.3	28.7	71.9	2.7
4864	584	8	94.3	27.5	71	3.3
4865	584	9	101.8	26.3	70	3.9
4866	584	10	110.4	24.6	67	4
4867	584	11	114.2	23.5	65	4.3
4868	585	1	0	34	0	1.5
4869	585	2	37.9	34.1	55	1.5
4870	585	3	56.3	33.7	65	1.6
4871	585	4	72.1	32.9	70	1.9
4872	585	5	86	31.7	72	2.4
4873	585	6	89	31.3	72.95	2.5
4874	585	7	93.1	30.9	72	2.7
4875	585	8	100.7	29.8	71	3.1
4876	585	9	116.4	26.9	67	4
4877	585	10	121.3	25.9	65	4.8
4878	586	1	0	36.5	0	1.5
4879	586	2	41.3	36.5	55	1.5
4880	586	3	60.8	36.4	65	1.5
4881	586	4	77	35.5	70	1.6
4882	586	5	85.3	34.8	71	1.8
4883	586	6	90.9	34.3	72	1.8
4884	586	7	95.8	33.7	73	2.2
4885	586	8	100.3	33	72	2.4
4886	586	9	105.9	32.2	71	2.5
4887	586	10	113.1	30.9	70	3
4888	586	11	121.7	29.1	67	3.1
4889	586	12	127.7	27.9	65	4
4890	587	1	0	24.1	0	1.83
4891	587	2	112	23.5	60	1.83
4892	587	3	153	22.6	70	1.98
4893	587	4	199	21.1	76	2.35
4894	587	5	247	19.5	79	2.5
4895	587	6	282	18.1	82	3.02
4896	587	7	343	15.5	77	3.66
4897	588	1	0	32.4	0	1.83
4898	588	2	118	31.2	60	1.83
4899	588	3	188	29.5	74	2
4900	588	4	230	28.1	78	2.29
4901	588	5	288	26	81	2.8
4902	588	6	324	24.4	82	3.17
4903	588	7	390	20.8	78.9	3.66
4904	589	1	0	36.6	0	1.83
4905	589	2	128	34.9	60	1.83
4906	589	3	198	32.9	74	2.1
4907	589	4	237	31.6	78	2.38
4908	589	5	342	27.4	82	2.78
4909	589	6	374	25.7	81	3.2
4910	589	7	408	23.7	79	3.66
4911	590	1	0	72.54	0	1.37
4912	590	2	140	70.71	60	1.37
4913	590	3	215	67.67	75	1.4
4914	590	4	310	61.57	79.9	1.83
4915	590	5	360	56.69	78	2.16
4916	590	6	440	46.02	70	3.05
4917	591	1	0	106.68	0	1.37
4918	591	2	150	104.85	60	1.37
4919	591	3	255	100.74	75	1.46
4920	591	4	305	97.54	80	1.58
4921	591	5	380	91.44	82	1.86
4922	591	6	460	81.69	79	2.35
4923	591	7	530	67.06	70	3.05
4924	592	1	0	72.54	0	1.37
4925	592	2	140	70.71	60	1.37
4926	592	3	215	67.67	75	1.4
4927	592	4	310	61.57	79.9	1.83
4928	592	5	360	56.69	78	2.16
4929	592	6	440	46.02	70	3.05
4930	593	1	0	106.68	0	1.37
4931	593	2	150	104.85	60	1.37
4932	593	3	255	100.74	75	1.46
4933	593	4	305	97.54	80	1.58
4934	593	5	380	91.44	82	1.86
4935	593	6	460	81.69	79	2.35
4936	593	7	530	67.06	70	3.05
4937	594	1	0	117	0	5.2
4938	594	2	82	115.8	44.5	5.2
4939	594	3	164	110.9	69.25	5.2
4940	594	4	218	104.8	75.85	5.3
4941	594	5	300	96.3	78.65	6.4
4942	594	6	355	87.7	76.85	7.3
4943	594	7	382	82.9	74.13	8.2
4944	595	1	0	134.1	0	5.2
4945	595	2	82	131.6	43.78	5.2
4946	595	3	164	126.7	68.99	5.2
4947	595	4	218	121.9	75.84	5.3
4948	595	5	300	110.9	79.46	6.4
4949	595	6	355	100.5	76.66	7.3
4950	595	7	382	96.3	75.47	8.2
4951	596	1	0	150	0	5.2
4952	596	2	109	147	51.81	5.2
4953	596	3	191	141.4	71.46	5.3
4954	596	4	273	131	77.77	6
4955	596	5	341	124.3	79.59	7.3
4956	596	6	382	115.8	78.41	8.2
4957	596	7	409	109.7	75.87	9.1
4958	597	1	0	167	0	5.2
4959	597	2	109	163.3	49.96	5.2
4960	597	3	191	157.2	68.52	5.3
4961	597	4	273	147.5	75.76	6
4962	597	5	341	137.1	77.61	7.3
4963	597	6	382	131	78.75	8.2
4964	597	7	436	120.7	76.58	10.3
4965	598	1	0	162.4	0	0
4966	598	2	172.7	162.4	54.91	0
4967	598	3	274.3	158.9	69.18	0
4968	598	4	365.1	152.8	76.09	0
4969	598	5	440.6	146.9	78.47	0
4970	598	6	501.3	138	82.54	0
4971	598	7	554.3	131.8	79.22	0
4972	598	8	600.4	121.1	76.51	0
4973	599	1	0	68.3	0	0
4974	599	2	51.1	67.8	35	0
4975	599	3	102.1	67	47	0
4976	599	4	152.6	65.9	58	0
4977	599	5	252	61.1	68	0
4978	599	6	276.6	58.3	67.5	0
4979	599	7	301.8	54.2	67	0
4980	600	1	0	94.3	0	0
4981	600	2	51.3	93.4	35	0
4982	600	3	102.7	92.2	44	0
4983	600	4	152.8	91.1	60	0
4984	600	5	297.8	83.9	74.5	0
4985	600	6	351.1	76.4	73	0
4986	600	7	407.9	58.9	64	0
4987	601	1	0	13.6	0	0
4988	601	2	20	13.6	40	0
4989	601	3	40	13.2	65	0
4990	601	4	62	12.7	75	0
4991	601	5	75	10.6	66	0
4992	601	6	86	8	58	0
4993	601	7	95	5.6	50	0
4994	602	1	10	26	8.33	0
4995	602	2	72	25	40	0
4996	602	3	109	24	55	0
4997	602	4	159	23	64	0
4998	602	5	220	20	68	0
4999	602	6	267	16	75	0
5000	602	7	309	11	60	0
5001	603	1	10	51	6.94	0
5002	603	2	73	49	40	0
5003	603	3	191	46	67	0
5004	603	4	243	43	75	0
5005	603	5	300	38	80	0
5006	603	6	380	29	70	0
5007	603	7	414	22	64	0
5008	604	1	0	22.68	0	0
5009	604	2	109.9	24.48	52	0
5010	604	3	204.8	23.56	70	0
5011	604	4	241.3	22.37	71	0
5012	604	5	270.8	20.97	70	0
5013	604	6	318.9	16.7	60	0
5014	604	7	325.9	15.82	58	0
5015	605	1	0	46.42	0	0
5016	605	2	186.9	48.31	52	0
5017	605	3	223.9	48.1	70.5	0
5018	605	4	329.5	45.81	75	0
5019	605	5	419.9	38.98	82	0
5020	605	6	442.6	36.12	76	0
5021	605	7	488.9	27.52	58	0
5022	606	1	0	8.14	0	0
5023	606	2	58.17	8.17	44	0
5024	606	3	145.47	7.62	65	0
5025	606	4	177.54	6.89	67	0
5026	606	5	218.49	5.36	65	0
5027	606	6	239.16	4.02	60	0
5028	606	7	270.73	1.04	48	0
5029	607	1	0	19.11	0	0
5030	607	2	58.05	19.14	44	0
5031	607	3	138.41	18.9	68	0
5032	607	4	205.23	17.98	75	0
5033	607	5	258.92	16.25	77	0
5034	607	6	335.69	10.97	70	0
5035	607	7	369.99	6.22	57	0
5036	608	1	7	17.5	41.69	0
5037	608	2	10.1	17.4	49	0
5038	608	3	20.6	16.5	69	0
5039	608	4	27.3	15.2	76	0
5040	608	5	34	13.2	72	0
5041	608	6	40.7	9.9	62	0
5042	608	7	43.9	7.6	61	0
5043	609	1	26.7	15.1	68.6	0
5044	609	2	34	14.6	74	0
5045	609	3	41.3	13.7	77	0
5046	609	4	44.9	13	77.8	0
5047	609	5	54.6	10.6	73	0
5048	609	6	61.5	8.4	65	0
5049	609	7	69.1	5.4	50.8	0
5050	610	1	25.1	15.39	64.13	0
5051	610	2	33.7	14.6	71	0
5052	610	3	41.3	13.3	74	0
5053	610	4	45	12.5	73	0
5054	610	5	51.4	10.8	69	0
5055	610	6	57.5	8.5	61.7	0
5056	610	7	64.1	5.95	48	0
5057	611	1	0	50.3	0	0
5058	611	2	100	49.1	27	0
5059	611	3	238.3	45.7	65	0
5060	611	4	284.3	42.8	74	0
5061	611	5	330.3	40.5	79	0
5062	611	6	381.2	37	81.45	0
5063	611	7	451.9	32.4	78.97	0
5064	612	1	0	67.6	0	0
5065	612	2	124.9	66.5	33	0
5066	612	3	256.3	64.2	65	0
5067	612	4	297.4	63	74	0
5068	612	5	335.2	61.3	79	0
5069	612	6	373	60.1	82	0
5070	612	7	415.7	57.8	84	0
5071	612	8	443.7	56.1	84.5	0
5072	612	9	478.2	53.2	84	0
5073	612	10	516	50.3	82	0
5074	612	11	542.3	48	79	0
5075	612	12	558.7	46.8	78	0
5076	613	1	0	76.9	0	2.6
5077	613	2	144.6	75.7	35	2.6
5078	613	3	274.4	73.4	65	2.8
5079	613	4	313.8	72.3	74	3.2
5080	613	5	351.6	71.7	79	3.5
5081	613	6	391.1	69.4	82	4.1
5082	613	7	422.3	67.6	84	4.4
5083	613	8	458.5	65.9	84.5	5.3
5084	613	9	507.7	62.4	84	6.2
5085	613	10	552.1	59	82	7.2
5086	613	11	578.4	57.2	79	7.8
5087	613	12	608	54.3	73	8.5
5088	614	1	0	80.4	0	0
5089	614	2	323.1	73.8	76	0
5090	614	3	383	70.2	79	0
5091	614	4	500.2	63.6	80	0
5092	614	5	601.9	54	79	0
5093	614	6	646.2	49.2	76	0
5094	614	7	687.8	43.2	69	0
5095	614	8	719.1	38.4	64	0
5096	614	9	734.7	34.8	64	0
5097	615	1	0	95	0	0
5098	615	2	336.1	88.2	76	0
5099	615	3	411.7	85.8	79	0
5100	615	4	456	83.4	80	0
5101	615	5	526.3	79.2	80.5	0
5102	615	6	630.5	70.8	80	0
5103	615	7	669.6	66.6	79	0
5104	615	8	713.9	60.6	76	0
5105	615	9	766	51.6	69	0
5106	615	10	794.7	45.6	64	0
5107	615	11	820.7	40.8	62	0
5108	616	1	0	108.6	0	2.1
5109	616	2	406.5	103.2	76	2.4
5110	616	3	482	100.8	79	2.7
5111	616	4	528.9	98.4	80	3.3
5112	616	5	591.4	94.2	80.5	4.2
5113	616	6	654	88.8	80	5.1
5114	616	7	690.4	85.2	79	6
5115	616	8	758.2	76.2	76	8.1
5116	616	9	820.7	65.4	69	11
5117	616	10	862.4	58.2	64	13.7
5118	616	11	891.1	53.4	62	16.1
5119	617	1	6.6	12.5	52.23	0
5120	617	2	8.7	12.2	58	0
5121	617	3	10.8	11.7	64	0
5122	617	4	17.8	9.6	72.8	0
5123	617	5	21.8	7.9	70	0
5124	617	6	24.5	6.3	64	0
5125	617	7	27.6	4.2	49.6	0
5126	618	1	0	115.8	0	0
5127	618	2	80	114.3	32	2.4
5128	618	3	160	111.3	60	2.4
5129	618	4	240	105.2	76	2.7
5130	618	5	320	97.5	82.2	3.4
5131	618	6	400	86.9	82.75	4.9
5132	618	7	480	74.7	79	7.9
5133	619	1	0	20	0	0
5134	619	2	90	21	50	0
5135	619	3	149	21	65	0
5136	619	4	213	20.7	75	0
5137	619	5	281	19.5	78	0
5138	619	6	354	16.7	75	0
5139	619	7	377	15.2	70	0
5140	620	1	0	41.4	0	1.8
5141	620	2	202	42	50	2.2
5142	620	3	281	41	65	2.7
5143	620	4	381	39	75	3
5144	620	5	445	36.5	78	3.6
5145	620	6	481	34.7	75	5.4
5146	620	7	358	30	70	9.4
5147	621	1	0	51.7	0	0
5148	621	2	1479.6	48.6	60	0
5149	621	3	2940.48	42.3	81	0
5150	621	4	3464.64	38.3	83	0
5151	621	5	3726	35.8	83.5	0
5152	621	6	4064.4	32.9	83	0
5153	621	7	4532.4	28	81	0
5154	621	8	4888.8	24.5	80	0
5155	622	1	0	67.6	0	0
5156	622	2	1479.6	64.8	60	0
5157	622	3	2884.32	58.9	81	0
5158	622	4	3371.04	56.8	85	0
5159	622	5	3970.8	53.1	87	0
5160	622	6	4327.2	50.3	87.55	0
5161	622	7	4719.6	46.8	87	0
5162	622	8	5299.2	40	83	0
5163	622	9	5673.6	35.3	80.6	0
5164	623	1	0	75.8	0	4
5165	623	2	1440	73.7	60	4
5166	623	3	2977.92	68.8	81	4
5167	623	4	3352.32	67.1	85	4.3
5168	623	5	3801.6	64.5	87	5
5169	623	6	4683.6	58.2	89	7
5170	623	7	5414.4	51.7	87	10
5171	623	8	5713.2	48.2	85	13
5172	623	9	6105.6	43.5	81	14
5173	623	10	6292.8	40.4	80	15
5174	624	1	0	29.48	0	0
5175	624	2	1117.44	27.71	60	0
5176	624	3	2220.48	24.12	81	0
5177	624	4	2616.12	21.84	83	0
5178	624	5	2813.4	20.41	83.5	0
5179	624	6	3069	18.76	83	0
5180	624	7	3422.52	15.96	81	0
5181	624	8	3690	13.97	80	0
5182	625	1	0	38.54	0	0
5183	625	2	1117.44	36.95	60	0
5184	625	3	2178	33.58	81	0
5185	625	4	2545.56	32.39	85	0
5186	625	5	2998.44	30.28	87	0
5187	625	6	3267.36	28.68	87.55	0
5188	625	7	3563.64	26.68	87	0
5189	625	8	4003.2	22.81	83	0
5190	625	9	4284	20.13	80.6	0
5191	626	1	0	43.22	0	2.28
5192	626	2	1087.2	42.02	60	2.28
5193	626	3	2248.56	39.23	81	2.28
5194	626	4	2531.52	38.26	85	2.45
5195	626	5	2870.64	36.78	87	2.85
5196	626	6	3536.64	33.18	89	3.99
5197	626	7	4089.6	29.48	87	5.7
5198	626	8	4312.8	27.48	85	7.41
5199	626	9	4611.6	24.8	81	7.98
5200	626	10	4752	23.04	80	8.55
5201	627	1	112.43	15.85	48.57	0
5202	627	2	185.79	15.58	65	0
5203	627	3	226.19	15.33	70	0
5204	627	4	286.18	14.23	74.1	0
5205	627	5	338.42	12.95	73.5	0
5206	627	6	360.9	11.09	70	0
5207	627	7	389.06	8.53	62	0
5208	628	1	115.83	24.84	52.28	0
5209	628	2	184.7	24.99	65	0
5210	628	3	218.04	24.69	72	0
5211	628	4	277.55	24.54	78	0
5212	628	5	378.16	22.31	81	0
5213	628	6	457.88	17.47	74	0
5214	628	7	500.13	11.67	64	0
5215	629	1	50	17.8	56.35	0
5216	629	2	68	17.4	70	0
5217	629	3	82.6	16.5	75	0
5218	629	4	95.6	15.1	76	0
5219	629	5	110	12.9	73	0
5220	629	6	117.3	11	69	0
5221	629	7	132.7	5.8	46.6	0
5222	630	1	0	6.45	0	1.4
5223	630	2	41.7	6.3	57.22	1.3
5224	630	3	49.7	6.1	60	1.3
5225	630	4	59.1	5.9	65	1.3
5226	630	5	80.5	5.1	70	1.5
5227	630	6	106.3	3.7	61	1.9
5228	631	1	0	7.9	0	1.2
5229	631	2	35.6	7.9	50	1.2
5230	631	3	42.1	7.9	60	1.2
5231	631	4	58.8	7.7	70	1.2
5232	631	5	69.7	7.4	75	1.2
5233	631	6	84.9	6.9	78	1.3
5234	631	7	93.2	6.5	79.55	1.3
5235	631	8	100.9	6.1	78	1.4
5236	631	9	108.5	5.6	75	1.6
5237	631	10	119.4	4.9	70	1.7
5238	631	11	121.9	4.7	67	1.9
5239	632	1	0	9.2	0	1
5240	632	2	35.2	9.2	50	0.8
5241	632	3	49	9.2	65	1
5242	632	4	57	9.2	70	0.9
5243	632	5	70.4	9	75	0.8
5244	632	6	77.6	8.8	78	0.9
5245	632	7	84.9	8.6	80	1
5246	632	8	96.1	8.2	82	1
5247	632	9	101.2	8	83	1.1
5248	632	10	105.9	7.7	82	1.1
5249	632	11	116.1	7.1	80	1.2
5250	632	12	121.5	6.7	78	1.4
5251	632	13	137.1	5.5	70	1.8
5252	633	1	0	27.6	0	3.3
5253	633	2	65.8	27.2	50	3.3
5254	633	3	94.2	26.2	60	3.3
5255	633	4	112.5	25.3	65	3.3
5256	633	5	138.8	23.7	70	3.4
5257	633	6	168.8	21.2	73	4.1
5258	633	7	195.1	18.4	70	4.8
5259	633	8	211.1	16.5	63	5.6
5260	634	1	0	33.1	0	2.8
5261	634	2	62.1	33	50	2.8
5262	634	3	85.5	32.7	60	2.8
5263	634	4	101.6	32.2	65	3.1
5264	634	5	120.5	31.4	70	3
5265	634	6	149.8	29.7	75	3.3
5266	634	7	182.6	26.9	78.95	4.1
5267	634	8	212.6	23.8	75	4.7
5268	634	9	236.7	20.5	70	5.9
5269	634	10	239.6	20.1	69.85	6.1
5270	635	1	0	35.9	0	2.9
5271	635	2	62.1	35.9	50	2.9
5272	635	3	82.6	35.8	60	2.9
5273	635	4	97.2	35.5	65	3.1
5274	635	5	115.4	35	70	3.3
5275	635	6	136.6	34.2	75	3.6
5276	635	7	183.4	31.2	80.95	4.4
5277	635	8	234.5	25.4	75	4.9
5278	635	9	256.4	22.2	69.89	6.4
5279	636	1	0	39.5	0	2.5
5280	636	2	62.1	39.5	50	2.3
5281	636	3	81.8	39.3	60	2.5
5282	636	4	94.2	39.2	65	2.5
5283	636	5	110.3	39	70	2.7
5284	636	6	130.8	38.6	75	2.8
5285	636	7	159.3	37.5	80	3.1
5286	636	8	200.9	34.9	82	4.2
5287	636	9	228.7	32	80	4.7
5288	636	10	255	28.4	75	5.6
5289	636	11	271.1	25.5	70	6.2
5290	636	12	274.7	24.7	69.85	6.7
5291	637	1	0	11	0	2.6
5292	637	2	26.6	11	50	2.8
5293	637	3	42.3	11	60	2.8
5294	637	4	54	10.8	65	3.1
5295	637	5	68.2	10.5	70	4.2
5296	637	6	83.2	9.7	71	5.5
5297	637	7	97	8.9	70	7.4
5298	637	8	110.9	7.8	65	10.3
5299	638	1	0	12.6	0	2.2
5300	638	2	27.4	12.7	50	2.2
5301	638	3	42	12.7	60	2.2
5302	638	4	52.5	12.6	65	2.6
5303	638	5	64.1	12.3	70	3.2
5304	638	6	80.9	11.6	72	4.8
5305	638	7	89.9	11.1	72.85	5.7
5306	638	8	95.9	10.8	72	6.5
5307	638	9	107.5	9.8	70	7.4
5308	638	10	118.8	8.9	65	10.5
5309	639	1	0	13.7	0	2
5310	639	2	28.1	13.8	50	2
5311	639	3	42	13.8	60	2.2
5312	639	4	51.7	13.7	65	2.6
5313	639	5	62.2	13.6	70	2.8
5314	639	6	72.3	13.3	72	3.2
5315	639	7	89.6	12.5	74.95	5.1
5316	639	8	109	11.2	72	7.4
5317	639	9	115.8	10.6	70	8.6
5318	639	10	125.5	9.9	65	10.2
5319	640	1	0	15	0	1.8
5320	640	2	28.9	15	50	1.7
5321	640	3	42.3	15	60	1.7
5322	640	4	51.7	15	65	1.8
5323	640	5	60.7	14.9	70	2.2
5324	640	6	67.8	14.7	72	2.3
5325	640	7	76.4	14.4	74	3.1
5326	640	8	90.7	13.8	74.98	4.5
5327	640	9	108.3	12.6	74	6.8
5328	640	10	116.9	11.9	72	7.5
5329	640	11	122.5	11.5	70	8.3
5330	640	12	131.9	10.4	64.98	10.3
5331	641	1	0	16.2	0	1.2
5332	641	2	30	16.3	50	1.2
5333	641	3	43.1	16.2	60	1.4
5334	641	4	60.3	16.2	70	1.8
5335	641	5	65.9	16.1	72	1.8
5336	641	6	73.1	15.8	74	2.3
5337	641	7	77.6	15.7	75	3.1
5338	641	8	95.9	14.7	76	4.3
5339	641	9	111.3	13.6	75	5.7
5340	641	10	121.8	12.7	72	6.6
5341	641	11	127.4	12.2	70	7.7
5342	641	12	135.6	11.4	65	10.3
5343	642	1	0	46.8	0	0.8
5344	642	2	78	47.1	60	1
5345	642	3	93.4	46.8	65	1.3
5346	642	4	120.6	45.7	70	2.2
5347	642	5	160.4	42.6	74.46	4.6
5348	642	6	194.9	38.6	70	8.4
5349	642	7	206	36.9	69	9.7
5350	643	1	0	58.6	0	0.6
5351	643	2	72.1	59	60	1
5352	643	3	88.3	58.6	65	1.3
5353	643	4	110.3	58.1	70	1.9
5354	643	5	133.1	56.9	75	2.9
5355	643	6	185.4	52.7	78.57	5.6
5356	643	7	229.5	46.5	75	11.1
5357	643	8	245	42.6	70	13.3
5358	644	1	0	68.3	0	2.8
5359	644	2	72.1	68.3	60	0.8
5360	644	3	88.3	68.2	65	1.3
5361	644	4	107.4	67.6	70	1.6
5362	644	5	135.4	66.2	75	1.7
5363	644	6	154.5	64.8	78	2.1
5364	644	7	172.1	62.8	80	3
5365	644	8	199.4	60	81	4
5366	644	9	226.6	56.1	80	5.6
5367	644	10	239.1	53.8	78	6.3
5368	644	11	256.7	50.4	75	7.5
5369	644	12	273.7	45.9	70	10.6
5370	645	1	0	16.5	0	2.8
5371	645	2	34.9	16.6	60	2.8
5372	645	3	47.7	16.5	70	3
5373	645	4	68.4	15.7	78	3
5374	645	5	84.1	14.6	80	3.5
5375	645	6	101.4	12.8	78	4.3
5376	645	7	112.7	11.4	74	5.5
5377	645	8	119.4	10.3	70	6.7
5378	645	9	130.3	8.4	66	8.8
5379	646	1	0	18.3	0	2.6
5380	646	2	35.3	18.4	60	2.9
5381	646	3	49.6	18.4	70	3
5382	646	4	57.1	18.2	74	3
5383	646	5	81.9	16.9	80	3.3
5384	646	6	90.1	16.2	80.65	3.5
5385	646	7	100.3	15.2	80	3.9
5386	646	8	109.3	14.1	78	4.5
5387	646	9	120.2	12.6	74	5.7
5388	646	10	128.5	11.4	70	7
5389	646	11	136.7	10	67	8.7
5390	647	1	0	20.1	0	2.7
5391	647	2	36.4	20.3	60	3
5392	647	3	43.2	20.3	65	3
5393	647	4	51.5	20.2	70	3
5394	647	5	59.3	20	74	3.2
5395	647	6	83.4	18.8	80	3.3
5396	647	7	94.6	18.1	81.85	3.8
5397	647	8	108.9	16.6	80	4.1
5398	647	9	118.3	15.5	78	5.4
5399	647	10	129.6	14.2	74	6.4
5400	647	11	137.8	12.9	70	7.7
5401	647	12	144.2	11.9	66	8.8
5402	648	1	0	22.6	0	2.8
5403	648	2	39.1	22.6	60	3
5404	648	3	54.1	22.6	70	3
5405	648	4	75.9	21.9	78	3
5406	648	5	93.9	20.8	81	3.5
5407	648	6	100.7	20.3	81.35	3.3
5408	648	7	107.8	19.8	81	3.2
5409	648	8	117.9	18.7	80	3.8
5410	648	9	127.7	17.7	78	4.2
5411	648	10	139.3	16.2	74	6.7
5412	648	11	149.1	15	70	8
5413	648	12	152.9	14.4	68	8.6
5414	649	1	0	25.2	0	2.8
5415	649	2	42.1	25.3	60	3
5416	649	3	48.8	25.3	65	3
5417	649	4	67.2	25	74	3
5418	649	5	80	24.5	78	3.2
5419	649	6	98.4	23.4	81	3.3
5420	649	7	106.3	22.9	81.5	3.3
5421	649	8	114.9	22.2	81	3.5
5422	649	9	126.2	21.1	80	4.2
5423	649	10	149.5	18.5	74	6.7
5424	649	11	162.3	16.7	67	8.4
5425	650	1	0	27.3	0	2.6
5426	650	2	44.3	27.4	60	2.6
5427	650	3	61.6	27.3	70	3
5428	650	4	83.4	26.7	78	3
5429	650	5	95.4	26.1	80	3
5430	650	6	103.3	25.6	81	3
5431	650	7	112.7	25	81.95	3
5432	650	8	120.6	24.3	81	3.6
5433	650	9	143.5	22.2	78	4.9
5434	650	10	157.7	20.6	74	6.4
5435	650	11	169	19	70	8.7
5436	651	1	0	68.1	0	3.8
5437	651	2	80.6	68.7	60	3.8
5438	651	3	94.3	68.4	65	3.7
5439	651	4	112.5	67.5	70	3.8
5440	651	5	136.1	65.6	75	4
5441	651	6	178.6	60.1	79.95	4.5
5442	651	7	210.5	53.3	75	5.7
5443	651	8	233.3	46.9	70	7.1
5444	651	9	254.6	38	66	9.4
5445	652	1	0	82.8	0	3.5
5446	652	2	85.9	83.4	60	3.5
5447	652	3	100.3	83.4	65	3.5
5448	652	4	120.9	82.5	70	3.5
5449	652	5	142.9	81.3	75	3.8
5450	652	6	167.2	79.4	78	4
5451	652	7	197.6	75.1	80.85	4.8
5452	652	8	233.3	68.4	78	6.5
5453	652	9	249.3	63.8	75	7.5
5454	652	10	272.9	55.8	69	9.7
5455	653	1	0	100.6	0	3.4
5456	653	2	94.3	101.6	60	3.4
5457	653	3	111.7	101.3	65	3.4
5458	653	4	132.3	100.6	70	3.5
5459	653	5	155.1	99.4	75	3.7
5460	653	6	178.6	97.9	78	4.2
5461	653	7	200.7	95.7	80	4.6
5462	653	8	224.2	93.3	80.85	5.7
5463	653	9	250.1	89	80	7.2
5464	653	10	269.8	85	78	8.6
5465	653	11	288.8	79.7	75	9.7
5466	653	12	294.2	78.2	74	10.3
5467	654	1	0	111.1	0	3.1
5468	654	2	100.3	110.8	60	3.1
5469	654	3	118.6	110.2	65	3.2
5470	654	4	139.1	109.6	70	3.4
5471	654	5	162.7	108.3	75	3.5
5472	654	6	186.2	106.8	78	4
5473	654	7	209	104.6	80	4.6
5474	654	8	230.3	101.9	81	5.5
5475	654	9	264.5	97	80	7.5
5476	654	10	285	93.3	78	8.6
5477	654	11	306.3	88	75	10.2
5478	655	1	0	25.1	0	1.7
5479	655	2	54.4	25.1	60	2
5480	655	3	68.6	24.8	65	1.9
5481	655	4	104.8	22.5	70	2.6
5482	655	5	126.2	20.2	68	3.1
5483	655	6	137.2	18.7	65	3.5
5484	655	7	145.6	17.4	62	3.8
5485	656	1	0	31.8	0	1.7
5486	656	2	56.9	31.9	60	2.1
5487	656	3	71.2	31.7	65	1.9
5488	656	4	87.4	31.1	70	2.2
5489	656	5	119.7	28.9	72	2.8
5490	656	6	151.4	25.6	70	3.7
5491	656	7	159.2	24.6	68	4.1
5492	656	8	166.9	23.4	64.85	4.4
5493	657	1	0	35.5	0	1.7
5494	657	2	59.2	35.5	60	1.9
5495	657	3	73.5	35.5	65	1.8
5496	657	4	87.3	34.9	70	2.1
5497	657	5	104.2	34	72	2.6
5498	657	6	125.3	32.4	73	2.9
5499	657	7	148.1	30.2	72	3.6
5500	657	8	162.9	28.2	70	4.2
5501	657	9	170.3	27.3	68	4.3
5502	657	10	175	26.5	66	4.4
5503	658	1	0	40	0	1.7
5504	658	2	62.1	39.9	60	1.9
5505	658	3	87.4	39.2	70	2.2
5506	658	4	102.2	38.6	72	2.3
5507	658	5	111.9	38	73	2.5
5508	658	6	133.3	36.2	74.5	2.9
5509	658	7	153.4	33.8	73	3.5
5510	658	8	172.1	31.4	70	4.1
5511	658	9	185.1	29.3	66	4.5
5512	659	1	0	70.5	0	0
5513	659	2	15	67.6	40	0
5514	659	3	23.4	65.2	50	0
5515	659	4	32.2	62.4	57	0
5516	659	5	48.1	54.8	60.5	0
5517	659	6	64.1	46.1	57	0
5518	659	7	72	39.9	50	0
5519	660	1	0	117.3	0	0
5520	660	2	22.1	112.3	40	0
5521	660	3	34.7	108.2	50	0
5522	660	4	44.2	103.7	54	0
5523	660	5	62	93.9	56	0
5524	660	6	82.7	79.2	54	0
5525	660	7	92.4	70.4	50	0
5526	661	1	0	165.7	0	2.6
5527	661	2	31.6	155.3	40	2.6
5528	661	3	49.1	148.1	50	2.6
5529	661	4	65	139.1	54	2.9
5530	661	5	77.7	130.4	54.4	3.7
5531	661	6	86.6	122.2	54	4.3
5532	661	7	109.9	100.9	50	6.9
5533	662	1	0	17.4	0	0.6
5534	662	2	8.4	16.7	40	0.6
5535	662	3	12.6	16	50	0.6
5536	662	4	23.8	13.1	58.5	0.7
5537	662	5	33.3	10.8	55	0.8
5538	662	6	37.9	8.9	50	0.95
5539	662	7	40.6	7.6	45	1.2
5540	663	1	0	29.3	0	0.6
5541	663	2	11.5	27.9	40	0.6
5542	663	3	17.8	26.7	50	0.6
5543	663	4	27	24.3	55	0.6
5544	663	5	31.1	23.1	55.5	0.65
5545	663	6	40.7	19.2	53	0.85
5546	663	7	50.8	14.5	45	1.2
5547	664	1	0	41.4	0	0.6
5548	664	2	15.7	39.1	40	0.6
5549	664	3	25.8	36.9	50	0.6
5550	664	4	37.3	32.7	53.5	0.75
5551	664	5	43.7	30.7	53	0.9
5552	664	6	52.9	26.1	50	1
5553	664	7	60.3	21.9	45	1.2
5554	665	1	1250	4	35	0
5555	665	2	1579	3.5	42.5	0
5556	665	3	1983	2.4	40	0
5557	665	4	2219	1.5	32	0
5558	665	5	2368	0.8	27	0
5559	666	1	3750	4.6	39.14	0
5560	666	2	4620	4	41.93	0
5561	666	3	5000	3.7	42.33	0
5562	666	4	5500	3.3	41.88	0
5563	666	5	7500	3	52.36	0
5564	666	6	6000	2.7	38.35	0
5565	666	7	6600	2	32.17	0
5566	666	8	6800	1.75	29.45	0
5567	667	1	865.1	7.2	89	0
5568	667	2	1057	6.5	83	0
5569	667	3	1240	5.5	78	0
5570	667	4	1340	4.7	75	0
5571	667	5	1470	3.4	65	0
5572	667	6	1562	2	45	0
5573	668	1	872	7.5	80	0
5574	668	2	1067	6.6	83	0
5575	668	3	1242	5.6	80	0
5576	668	4	1339	4.8	75	0
5577	668	5	1472	3.5	65	0
5578	668	6	1573	2	45	0
5579	669	1	652	17.2	77	0
5580	669	2	970.6	15.5	80	0
5581	669	3	1249	13.7	81	0
5582	669	4	1493	12.2	80	0
5583	669	5	1598	11.3	78	0
5584	669	6	1772	9.8	72	0
5585	669	7	1916	8.3	65	0
5586	669	8	2001	7.2	57	0
5587	670	1	638.4	6.4	75.01	0
5588	670	2	829.2	5.5	80	0
5589	670	3	965.5	4.7	79	0
5590	670	4	1055	4.1	75	0
5591	670	5	1141	3.5	70	0
5592	670	6	1234	2.7	60	0
5593	670	7	1331	1.7	45	0
5594	671	1	581.1	6.1	74.99	0
5595	671	2	635.4	5.8	80	0
5596	671	3	743.8	5.1	83	0
5597	671	4	887.2	4.2	80	0
5598	671	5	964.6	3.6	75	0
5599	671	6	1077	2.6	63	0
5600	671	7	1162	1.7	45	0
5601	672	1	412.7	5.6	70	0
5602	672	2	506.1	5.2	80	0
5603	672	3	630.7	4.5	85	0
5604	672	4	763	3.6	80	0
5605	672	5	844.8	3	74.9	0
5606	672	6	907.1	2.3	66.8	0
5607	672	7	942.1	1.6	60	0
5608	673	1	242.2	13.3	75.02	0
5609	673	2	430.1	12.3	83.8	0
5610	673	3	672.4	10.8	83	0
5611	673	4	924.5	8.6	80	0
5612	673	5	1068	7.1	75	0
5613	673	6	1167	5.7	67	0
5614	673	7	1266	3.9	50	0
5615	674	1	1050	7	69.99	0
5616	674	2	1200	6.5	80.9	0
5617	674	3	1250	6	82	0
5618	674	4	1425	5	80	0
5619	674	5	1650	3.5	65	0
5620	674	6	1700	3	63.1	0
5621	674	7	1800	1.75	45	0
5622	675	1	1021	10.4	75	0
5623	675	2	1183	9.9	80	0
5624	675	3	1593	8.2	83	0
5625	675	4	2003	5.7	80	0
5626	675	5	2289	3.5	70	0
5627	675	6	2544	1.5	50	0
5628	676	1	992.9	8.3	79.8	0
5629	676	2	1399	7.1	85	0
5630	676	3	1829	4.9	80	0
5631	676	4	2063	3.4	70	0
5632	676	5	2266	2	54	0
5633	677	1	831	7.1	79.7	0
5634	677	2	1058	6.2	82	0
5635	677	3	1230	5.2	80	0
5636	677	4	1434	3.6	65	0
5637	677	5	1614	1.9	44.8	0
5638	678	1	527	6.9	73	0
5639	678	2	715.4	5.7	80	0
5640	678	3	935.2	4.1	73	0
5641	678	4	1045	3.1	60	0
5642	678	5	1155	1.9	43	0
5643	679	1	1776	10	72.8	0
5644	679	2	2561	8.7	85	0
5645	679	3	2855	8	85	0
5646	679	4	3468	6.1	80	0
5647	679	5	3828	4.4	70	0
5648	680	1	1159	8.4	75	0
5649	680	2	1799	7.4	85	0
5650	680	3	2251	6.4	87.8	0
5651	680	4	2875	4.8	80	0
5652	680	5	3212	3.7	70	0
5653	680	6	3491	2.5	60	0
5654	681	1	1500	7.6	77.59	0
5655	681	2	1700	7.25	80	0
5656	681	3	2000	6.5	88.5	0
5657	681	4	2200	5.8	89	0
5658	681	5	2500	4.8	86	0
5659	681	6	2650	4.2	80	0
5660	681	7	2800	3.1	70	0
5661	682	1	450.8	7.7	75	0
5662	682	2	843.3	6.8	85	0
5663	682	3	1236	5.7	87	0
5664	682	4	1637	4.1	80	0
5665	682	5	1817	3.2	70	0
5666	682	6	2021	2	50	0
5667	683	1	3409	11.5	76.5	0
5668	683	2	3693	10.8	80	0
5669	683	3	4311	9.2	83	0
5670	683	4	4795	7.6	79	0
5671	683	5	5163	6.2	70	0
5672	683	6	5580	3.7	50	0
5673	684	1	2714	10.3	76.8	0
5674	684	2	2949	10	80	0
5675	684	3	3685	8.3	85	0
5676	684	4	4288	6.2	80	0
5677	684	5	4656	4.8	70	0
5678	684	6	5125	3	50	0
5679	685	1	1970	10.6	70	0
5680	685	2	2475	9.6	80	0
5681	685	3	3013	8.2	85.5	0
5682	685	4	3636	5.8	80	0
5683	685	5	4174	2.6	49.8	0
5684	686	1	1526	9.9	71	0
5685	686	2	1927	9	80	0
5686	686	3	2630	6.9	87	0
5687	686	4	3099	4.7	80	0
5688	686	5	3317	3.5	65	0
5689	687	1	4686	9.6	83.5	0
5690	687	2	5346	8.6	83.9	0
5691	687	3	6296	7	80	0
5692	687	4	6729	6	75	0
5693	687	5	7390	3.6	55	0
5694	688	1	3062	9.7	80.02	0
5695	688	2	3832	9	85	0
5696	688	3	4359	8.1	86.5	0
5697	688	4	4865	7.1	85	0
5698	688	5	5372	6	80	0
5699	688	6	5940	4.7	70	0
5700	688	7	6325	3.8	60	0
5701	689	1	2251	9.6	80.1	0
5702	689	2	2697	8.9	85	0
5703	689	3	3467	7.6	87.5	0
5704	689	4	3994	6.4	85	0
5705	689	5	4399	5.5	80	0
5706	689	6	4825	4.3	70	0
5707	689	7	5169	3.2	55	0
5708	690	1	1635	8.4	80	0
5709	690	2	2099	7.8	85	0
5710	690	3	2624	6.9	87	0
5711	690	4	3088	6	85	0
5712	690	5	3451	5	80	0
5713	690	6	3936	3.2	60	0
5714	691	1	227.12	2.13	73.38	0
5715	691	2	272.55	1.83	79.91	0
5716	691	3	295.26	1.62	79.27	0
5717	691	4	317.97	1.37	74.29	0
5718	691	5	340.69	1.13	69.81	0
5719	691	6	363.4	0.85	56.35	0
5720	691	7	386.11	0.58	46.88	0
5721	692	1	500	6.8	60	0
5722	692	2	600	6.4	70	0
5723	692	3	700	5.8	79.02	0
5724	692	4	800	5	84.34	0
5725	692	5	900	4.4	83.5	0
5726	692	6	1000	3.4	78.21	0
5727	692	7	1200	1	43.38	0
5728	693	1	865.1	7.2	60	0
5729	693	2	1057	6.5	82	0
5730	693	3	1240	5.5	90	0
5731	693	4	1340	4.7	83.5	0
5732	693	5	1470	3.4	65	0
5733	693	6	1562	2	45	0
5734	694	1	0	35	0	0
5735	694	2	100	34	30	0
5736	694	3	200	33.2	53.17	0
5737	694	4	300	32.9	67.18	0
5738	694	5	400	32.1	75.99	0
5739	694	6	500	31.1	84.67	0
5740	694	7	600	29.5	89.24	0
5741	694	8	700	26.8	88.06	0
5742	694	9	800	23.5	83.91	0
5743	695	1	0	41	0	0
5744	695	2	100	40	33	0
5745	695	3	200	39.4	53.63	0
5746	695	4	300	38.6	67.08	0
5747	695	5	400	38	79.58	0
5748	695	6	500	37	86.84	0
5749	695	7	600	35	89.33	0
5750	695	8	700	32	89.68	0
5751	695	9	800	28	84.7	0
5752	695	10	850	26	82.42	0
5753	696	1	0	46.5	0	0
5754	696	2	100	45	32.24	0
5755	696	3	200	44	52.08	0
5756	696	4	300	43.5	65.79	0
5757	696	5	400	42.5	74.65	0
5758	696	6	500	41.5	83.08	0
5759	696	7	600	40	88.3	0
5760	696	8	700	37.5	89.33	0
5761	696	9	800	34	88.16	0
5762	696	10	900	29	81.68	0
5763	697	1	0	51	0	0
5764	697	2	100	49.5	30.63	0
5765	697	3	200	48.6	49.01	0
5766	697	4	300	47.6	62.71	0
5767	697	5	400	47	75.27	0
5768	697	6	500	46	82.39	0
5769	697	7	600	44	86.6	0
5770	697	8	700	42	90.96	0
5771	697	9	800	38	89	0
5772	697	10	900	33.5	83.76	0
5773	697	11	940	31	79.34	0
5774	698	1	0	55	0	2
5775	698	2	100	53.5	28.01	2.1
5776	698	3	200	52.1	48.91	2.2
5777	698	4	300	51.1	63.24	2.3
5778	698	5	400	50.1	73.73	2.4
5779	698	6	500	49.1	81.51	2.5
5780	698	7	600	47.5	87.18	2.8
5781	698	8	700	45	90.27	3.2
5782	698	9	800	41	89.3	3.6
5783	698	10	900	37	87.17	4
5784	698	11	970	33	82.22	4.6
5785	699	1	0	78.5	0	0
5786	699	2	200	77.5	47.95	2
5787	699	3	400	76.5	74.38	3
5788	699	4	600	73.5	85.76	3.5
5789	699	5	800	68.8	89.73	4.1
5790	699	6	1000	59	84.54	6
5791	700	1	0	58	0	0
5792	700	2	100	56.5	23.67	0
5793	700	3	200	55.5	41.68	3.3
5794	700	4	300	55	56.15	3.3
5795	700	5	400	55	67.3	3.5
5796	700	6	500	54.5	80.2	3.6
5797	700	7	600	53	82.45	3.8
5798	700	8	700	51	86.4	4.2
5799	700	9	800	48	87.12	4.6
5800	700	10	900	44.5	85.52	5.4
5801	700	11	1000	40	80.67	6.8
5802	701	1	0	76	0	0
5803	701	2	540	78	41	0
5804	701	3	990	78	60	0
5805	701	4	1350	75	68	0
5806	701	5	1674	68	71	0
5807	701	6	1980	56	68	0
5808	701	7	2160	45	63	0
5809	702	1	0	93	0	0
5810	702	2	540	95	41	0
5811	702	3	1080	95	62.5	0
5812	702	4	1530	93	71	0
5813	702	5	1926	86	73	0
5814	702	6	2250	75	70	0
5815	702	7	2520	60	60	0
5816	703	1	0	75	0	3
5817	703	2	440	72	72	3
5818	703	3	480	71	74	3
5819	703	4	520	70	77	3
5820	703	5	570	69	80	3.5
5821	703	6	660	66	82	4
5822	703	7	760	62	82	4.5
5823	704	1	0	120	0	3
5824	704	2	420	114	72	3
5825	704	3	500	112	77	3
5826	704	4	620	108	82	3.5
5827	704	5	800	102	87	5
5828	704	6	950	94	87	6.5
5829	704	7	1080	87	82	8.5
5830	705	1	0	183.7	0	0
5831	705	2	205.2	183.25	51.21	0
5832	705	3	389.6	177.3	71.63	0
5833	705	4	565.6	166.18	80.83	0
5834	705	5	709.3	151.73	83.82	0
5835	705	6	814.4	138.47	83.09	0
5836	705	7	940.4	117.53	77.24	0
5837	706	1	0	204.22	0	0
5838	706	2	206.6	203.09	48.87	0
5839	706	3	401.8	196.2	71.47	0
5840	706	4	601.3	182.09	81.93	0
5841	706	5	748.2	166.06	84.88	0
5842	706	6	882	146.76	82.95	0
5843	706	7	1005	123.78	76.74	0
5844	707	1	0	222.87	0	0
5845	707	2	222.4	222.02	47.85	0
5846	707	3	418.1	215.55	70.46	0
5847	707	4	621.1	200.65	81.21	0
5848	707	5	780.9	181.87	84.25	0
5849	707	6	947	157.19	82.35	0
5850	707	7	1094	129.97	75.11	0
5851	708	1	0	241.89	0	3.84
5852	708	2	247.9	241.01	49.22	3.84
5853	708	3	444.6	234.15	70.86	3.84
5854	708	4	649.2	217.63	81.11	4.02
5855	708	5	811.6	198.06	84.56	5.21
5856	708	6	991.6	169.47	82.16	6.49
5857	708	7	1152	138.93	75.22	8.9
5858	709	1	0	73.5	0	2.6
5859	709	2	90	72.5	30	2.6
5860	709	3	185	72	50	2.6
5861	709	4	310	70.5	70	2.6
5862	709	5	470	65.5	80	3
5863	709	6	600	60.5	83	3.8
5864	709	7	710	52	81	4.6
5865	710	1	0	121.1	0	4.28
5866	710	2	115.5	119.5	30	4.28
5867	710	3	237.5	118.7	50	4.28
5868	710	4	398	116.2	70	4.28
5869	710	5	603.3	107.9	80	4.94
5870	710	6	770.2	99.7	83	6.26
5871	710	7	911.4	85.69	81	7.58
5872	711	1	0	68.1	0	0
5873	711	2	161.2	67.6	50	0
5874	711	3	333.1	66.5	75	0
5875	711	4	393.3	65.1	78	0
5876	711	5	414.8	64.6	79	0
5877	711	6	455.6	63	80	0
5878	711	7	509.3	60.3	80.5	0
5879	711	8	548	57.8	80	0
5880	711	9	591	55.1	78	0
5881	711	10	640.4	51.4	74	0
5882	712	1	0	78.6	0	0
5883	712	2	163.3	78.1	50	0
5884	712	3	348.1	77	75	0
5885	712	4	399.7	75.9	78	0
5886	712	5	457.7	74.1	80	0
5887	712	6	492.1	72.7	81	0
5888	712	7	550.1	69.5	81.5	0
5889	712	8	588.8	67	81	0
5890	712	9	631.8	63.8	79	0
5891	712	10	683.4	59.2	75	0
5892	713	1	0	89.2	0	0
5893	713	2	163.3	88.9	50	0
5894	713	3	367.5	87.8	75	0
5895	713	4	438.4	85.9	79	0
5896	713	5	472.8	84.9	80	0
5897	713	6	505	83.5	81	0
5898	713	7	588.8	79.2	81.8	0
5899	713	8	636.1	75.9	81	0
5900	713	9	681.2	72.4	79	0
5901	713	10	743.6	66.8	74	0
5902	714	1	0	101.1	0	2.2
5903	714	2	163.3	101.1	50	2.3
5904	714	3	391.1	99.5	75	3.4
5905	714	4	449.1	98.4	76	3.8
5906	714	5	498.6	96.5	80	4.1
5907	714	6	533	94.9	81	4.5
5908	714	7	625.4	89.7	82	5.3
5909	714	8	681.2	85.7	81	5.9
5910	714	9	724.2	81.9	79	6.3
5911	714	10	743.6	80	76	6.6
5912	714	11	795.1	74.9	74	7
5913	715	1	0	122.3	0	3
5914	715	2	323.6	113.4	70	5.5
5915	715	3	384.7	109.6	76	6.2
5916	715	4	444.2	104	79	7.1
5917	715	5	505.8	97.1	80	8.8
5918	715	6	574.1	85.5	79	10.3
5919	715	7	622	75.7	76	12.2
5920	716	1	0	157.1	0	3
5921	716	2	355.8	146.7	70	4.7
5922	716	3	446.1	140.2	78	5.8
5923	716	4	524.7	132	81	7.1
5924	716	5	583.9	123.9	81.5	8.1
5925	716	6	670	108.2	80	9.7
5926	716	7	723.3	96.4	75	12.2
5927	717	1	0	174	0	3
5928	717	2	372.9	164	70	4
5929	717	3	464	156.8	78	5
5930	717	4	548.1	147.2	81	6.5
5931	717	5	618.5	136.8	82	7.8
5932	717	6	712.5	119.5	80	10
5933	717	7	802.8	100.1	75	12.1
5934	718	1	100	107.4	29.24	3.9
5935	718	2	202.5	107.1	47.5	3.9
5936	718	3	306.2	106.3	61.5	3.9
5937	718	4	405.7	104.5	70	4.1
5938	718	5	528.9	98.2	73.5	6.3
5939	718	6	602.6	90	72	8
5940	718	7	678.1	75.8	67.5	10.5
5941	719	1	100	159.6	28.97	3.9
5942	719	2	203.3	159.2	47.5	3.9
5943	719	3	307.1	158.5	61.5	3.9
5944	719	4	405.9	157.2	70	4.1
5945	719	5	628.3	147.2	78	6.5
5946	719	6	703.2	139.1	77.5	7.8
5947	719	7	828	112.6	73	11
5948	720	1	0	76	0	0
5949	720	2	100	78	30	0
5950	720	3	300	77	65	0
5951	720	4	400	74	70	0
5952	720	5	450	69	76	0
5953	720	6	500	64	73	0
5954	720	7	600	45	65	0
5955	721	1	0	94	0	0
5956	721	2	100	95	30	0
5957	721	3	200	95	53	0
5958	721	4	400	93	70	0
5959	721	5	550	85	74	0
5960	721	6	650	73	68	0
5961	721	7	720	59	60	0
5962	722	1	110	21.9	54.66	0
5963	722	2	136	22.2	64	0
5964	722	3	150.9	21.8	67	0
5965	722	4	164	21.2	69	0
5966	722	5	191.3	19.4	72	0
5967	722	6	208.1	16.6	68	0
5968	722	7	215.1	14.6	67	0
5969	723	1	0	29.26	0	0
5970	723	2	156.22	29.26	54.1	0
5971	723	3	244.84	29.26	68.6	0
5972	723	4	305.48	26.97	71.6	0
5973	723	5	353.86	24.41	69	0
5974	723	6	394.06	20.54	62.1	0
5975	723	7	419.27	15.82	50.7	0
5976	724	1	0	53.34	0	0
5977	724	2	140.09	53.34	51.4	0
5978	724	3	293.22	51.63	73.5	0
5979	724	4	409.28	47.03	78.1	0
5980	724	5	482.87	41.03	73.1	0
5981	724	6	515.12	37	68.2	0
5982	724	7	561.45	27.4	54.1	0
5983	725	1	0	14.6	0	0
5984	725	2	156.4	14.6	31	0
5985	725	3	430.3	14.4	65	0
5986	725	4	558.7	13.6	72	0
5987	725	5	666.3	11.9	70	0
5988	725	6	723.4	10.3	65	0
5989	725	7	752.8	8.9	61	0
5990	726	1	0	24.9	0	0
5991	726	2	156.6	25	31	0
5992	726	3	445	24.7	67	0
5993	726	4	631.9	23.7	77	0
5994	726	5	757.9	22.3	79	0
5995	726	6	850	19.3	77	0
5996	726	7	991.9	12.9	65	0
5997	727	1	50	33.4	58.29	0
5998	727	2	69	32.9	71	0
5999	727	3	82.8	32.3	76	0
6000	727	4	95.6	31.4	78	0
6001	727	5	109.9	29.9	77	0
6002	727	6	123	27.9	72	0
6003	727	7	125.9	27.3	70.5	0
6004	728	1	56	25.4	45	0
6005	728	2	95.7	22	71	0
6006	728	3	113	20.6	75	0
6007	728	4	127.3	19	77	0
6008	728	5	162	13.9	76	0
6009	728	6	173	11	64	0
6010	728	7	179.5	8.9	63	0
6011	729	1	75	25.5	46.99	0
6012	729	2	83.5	24	50	0
6013	729	3	111.7	21	60	0
6014	729	4	129.8	20	65	0
6015	729	5	150	20	68	0
6016	729	6	179.5	18.8	70.5	0
6017	729	7	214.1	14.6	65.8	0
6018	730	1	0	42.5	0	2.6
6019	730	2	182	40	40	2.5
6020	730	3	461.4	35	70	2.6
6021	730	4	531.2	31.5	73	2.8
6022	730	5	621.3	27	74.5	3.2
6023	730	6	685.7	23	73.8	3.5
6024	730	7	707.7	21.5	73	3.6
6025	731	1	0	58.8	0	0
6026	731	2	219.1	55.4	43	0
6027	731	3	450.3	51.7	70	0
6028	731	4	527.4	49.7	74.5	0
6029	731	5	624.7	45.2	77.9	0
6030	731	6	728.2	38.6	78.5	0
6031	731	7	780.9	34.1	76.8	0
6032	731	8	860	27.9	73.5	0
6033	732	1	0	73	0	2.7
6034	732	2	246.3	70	44	2.5
6035	732	3	465.1	66	69.3	2.6
6036	732	4	604.8	62	77.65	3.2
6037	732	5	733.5	55	80.65	3.8
6038	732	6	876.8	45	76.7	5
6039	732	7	939.3	37	72.5	6.3
6040	733	1	0	45.3	0	2.5
6041	733	2	182	44.3	45	2.5
6042	733	3	409.9	39.8	74.8	2.7
6043	733	4	518.4	35.8	79.5	3.1
6044	733	5	575.4	32.8	79.5	3.4
6045	733	6	687.5	27.9	77	4
6046	733	7	792.3	20.4	70	5.1
6047	734	1	0	66.4	0	0
6048	734	2	216.8	63.6	47	0
6049	734	3	397.9	60.7	72.5	0
6050	734	4	477.9	58.7	78.5	0
6051	734	5	576.8	55.6	82.8	0
6052	734	6	688.4	50.3	82.5	0
6053	734	7	762.1	45.7	80	0
6054	734	8	821.1	41.3	76.8	0
6055	734	9	924.2	33.3	69.5	0
6056	735	1	0	78.6	0	2.5
6057	735	2	222.4	75.6	50	2.6
6058	735	3	417.3	72.6	74.6	2.8
6059	735	4	507.4	71.1	80.3	3.2
6060	735	5	694.9	65.7	85	4.1
6061	735	6	832.7	58.7	81	5.9
6062	735	7	977.9	48.3	70	9.4
6063	736	1	0	68.8	0	3.2
6064	736	2	250.5	62.8	46	3.2
6065	736	3	480.2	57.4	70	3.1
6066	736	4	608.9	52.9	75	3.3
6067	736	5	723.8	47.9	76.5	3.8
6068	736	6	873.2	40	72	4.5
6069	736	7	942.1	34.5	67	5
6070	737	1	0	120.5	0	3.2
6071	737	2	252.8	115.1	46	3.1
6072	737	3	480.2	110.1	70	3
6073	737	4	703.1	103.6	75	3.7
6074	737	5	864	97.2	76.5	4.5
6075	737	6	1041	87.7	72	6.1
6076	737	7	1163	76.8	67	8
6077	738	1	0	110.7	0	3.2
6078	738	2	362.9	106.6	50	3.1
6079	738	3	562.9	101.5	65	3.2
6080	738	4	642.9	99.5	68	3.2
6081	738	5	834.3	91.4	71	3.7
6082	738	6	934.3	84.3	70	4.1
6083	738	7	1040	76.1	66	4.8
6084	739	1	0	152.7	0	0
6085	739	2	355.9	149.2	48	0
6086	739	3	551.5	146.2	64.8	0
6087	739	4	673.3	143.1	70	0
6088	739	5	836.9	135.7	74	0
6089	739	6	952.3	127.8	73.8	0
6090	739	7	1055	119.5	72	0
6091	739	8	1158	111.2	69.3	0
6092	739	9	1254	102.4	65.5	0
6093	740	1	0	191.9	0	3.2
6094	740	2	360	190.9	47	3.1
6095	740	3	602.9	186.8	65	3.1
6096	740	4	757.1	181.7	71	3.4
6097	740	5	991.4	169.5	74.5	4.4
6098	740	6	1166	155.3	73	6.2
6099	740	7	1391	134	64	10.8
6100	741	1	0	313.03	0	0
6101	741	2	139.32	306.02	44	0
6102	741	3	273.46	302.82	69.8	0
6103	741	4	404.74	295.53	81.2	0
6104	741	5	510.35	277.98	84.7	0
6105	741	6	639.36	256.67	86.8	0
6106	741	7	851.49	197.48	78.4	0
6107	742	1	0	315.77	0	0
6108	742	2	184.52	305.41	56	0
6109	742	3	362.95	303.98	79.5	0
6110	742	4	537.83	278.65	86.3	0
6111	742	5	678.88	248.84	86.8	0
6112	742	6	769.5	227.99	84.8	0
6113	742	7	904.86	186.26	73.6	0
6114	743	1	0	1540	0	0
6115	743	2	613.4	1505	44	0
6116	743	3	1204	1490	69.8	0
6117	743	4	1782	1454	81.2	0
6118	743	5	2247	1368	84.7	0
6119	743	6	2815	1263	86.8	0
6120	743	7	3749	971.9	78.4	0
6121	744	1	0	470.92	0	0
6122	744	2	226.22	460.55	64.3	0
6123	744	3	360.45	439.52	79.6	0
6124	744	4	499.67	421.84	85.7	0
6125	744	5	658.21	385.88	87.4	0
6126	744	6	775.4	344.12	84.5	0
6127	744	7	897.6	287.61	75.4	0
6128	745	1	0	191.41	0	0
6129	745	2	139.32	189.59	44	0
6130	745	3	273.46	187.76	69.8	0
6131	745	4	404.74	181.36	81.2	0
6132	745	5	510.35	174.65	84.7	0
6133	745	6	639.36	158.19	86.8	0
6134	745	7	851.49	118.87	78.4	0
6135	746	1	0	1257	0	0
6136	746	2	139.32	1244	44	0
6137	746	3	273.46	1232	69.8	0
6138	746	4	404.74	1190	81.2	0
6139	746	5	510.35	1147	84.7	0
6140	746	6	639.36	1037	86.8	0
6141	746	7	851.49	780	78.4	0
6142	747	1	1.2	631.85	0	0
6143	747	2	268.46	616.92	70.7	0
6144	747	3	426.99	590.09	83.5	0
6145	747	4	558.95	551.38	87.4	0
6146	747	5	678.65	505.97	87.4	0
6147	747	6	812.88	445.62	82.5	0
6148	747	7	903.73	405.38	75.4	0
6149	748	1	0	112.7	0	0
6150	748	2	102.3	113.8	30	0
6151	748	3	204.6	114.4	47	0
6152	748	4	306.9	113.6	56	0
6153	748	5	401	111.3	58	0
6154	748	6	443.2	109.7	58	0
6155	748	7	511.4	106.4	57	0
6156	749	1	0	29.4	0	3
6157	749	2	96.12	30.7	50	3
6158	749	3	131.04	30.7	60	3
6159	749	4	173.52	30	68	3
6160	749	5	240.84	28.4	74	3.2
6161	749	6	274.32	26.9	74.3	3.6
6162	749	7	367.2	21.2	69	4.4
6163	750	1	0	75.3	0	3
6164	750	2	150.12	78.3	50	3.3
6165	750	3	268.56	77.8	68	4.3
6166	750	4	359.28	74.8	74	5.2
6167	750	5	434.16	70.1	75.1	6.2
6168	750	6	505.8	64.3	74	7
6169	750	7	601.2	54	69	8.2
6170	751	1	0	94.5	0	3
6171	751	2	167.76	99.6	50	3.7
6172	751	3	300.96	98.8	68	4.9
6173	751	4	399.6	94.7	74	6.1
6174	751	5	490.32	88.8	75.3	7.3
6175	751	6	574.2	80.9	74	8.2
6176	751	7	668.16	69.6	69	9.5
6177	752	1	0	140.5	0	3
6178	752	2	205.92	148.5	50	4.7
6179	752	3	366.12	147.2	68	6.5
6180	752	4	483.48	142.1	74	7.8
6181	752	5	594.36	133.1	75.7	9.3
6182	752	6	709.56	120.3	74	10.7
6183	752	7	817.2	103.9	69	13
6184	753	1	0	74	0	0
6185	753	2	108	78	44	2.8
6186	753	3	216	78	62	3.8
6187	753	4	324	76	72.4	4.8
6188	753	5	396	72.5	75.1	5.8
6189	753	6	468	67.5	75	6.4
6190	753	7	576	57.5	70	7.8
6191	754	1	0	92.5	0	0
6192	754	2	108	98	42	3.2
6193	754	3	216	100	59	4.2
6194	754	4	324	97.5	70	5.25
6195	754	5	432	93	75	6.5
6196	754	6	540	85	75	7.75
6197	754	7	648	72.5	70	9.2
6198	755	1	0	115	0	0
6199	755	2	126	122	40	3.75
6200	755	3	252	123	60	4.8
6201	755	4	378	120	71	6.3
6202	755	5	504	113	75.3	7.7
6203	755	6	630	102	74.3	9.2
6204	755	7	756	85	67	11
6205	756	1	0	140	0	3
6206	756	2	144	147	40	4
6207	756	3	288	149	61	5.5
6208	756	4	432	145	72	7
6209	756	5	576	135	75.4	9
6210	756	6	648	119	71	11
6211	756	7	792	108	69	13
6212	757	1	0	39.7	0	3.2
6213	757	2	394.3	34.2	34.2	3.2
6214	757	3	803.7	31.1	61.5	3.2
6215	757	4	1408	25.1	81.2	5
6216	757	5	1500	24	80	8
6217	757	6	1650	19	87	9
6218	757	7	2000	10	60	17
6219	758	1	0	60	0	3.2
6220	758	2	394.3	53.9	28.2	3.2
6221	758	3	803.7	50.3	53	3.2
6222	758	4	1398	45.6	78.6	5
6223	758	5	1812	38.7	85.5	10
6224	758	6	2371	17.3	60.7	14.5
6225	758	7	2450	18	50	17
6226	759	1	0	290	0	0
6227	759	2	750	287.5	38.75	6.25
6228	759	3	1500	280	63.75	6.25
6229	759	4	2250	270	75	7.5
6230	759	5	3000	260	81.25	8.75
6231	759	6	3750	245	83.13	9.25
6232	759	7	4500	225	80	15
6233	760	1	0	26.1	0	1.4
6234	760	2	150	25.7	55.98	1.4
6235	760	3	300	25	75.91	1.4
6236	760	4	400	23.8	81.25	1.4
6237	760	5	500	22.5	84.49	1.4
6238	760	6	600	21	83.16	1.6
6239	760	7	750	17.7	77.06	2.2
6240	761	1	0	158	0	0
6241	761	2	8	157	29.73	0
6242	761	3	16	153	51.27	2
6243	761	4	24	148	64.47	2.6
6244	761	5	32	137	68.2	3.2
6245	761	6	40	122	68.13	4.1
6246	761	7	48	106	64.43	5.5
6247	762	1	0	31.68	0	0
6248	762	2	53.64	32.07	42.78	0
6249	762	3	107.71	30.76	68.15	0
6250	762	4	143.64	28.66	77.05	0
6251	762	5	159.84	27.49	78.99	0
6252	763	1	0	54	0	4.5
6253	763	2	50	53.5	33.1	4.5
6254	763	3	100	52	56.63	4.5
6255	763	4	150	49	72.77	4.8
6256	763	5	200	45	81.68	5.5
6257	763	6	250	40	85.08	6.6
6258	763	7	318.8	30	77.71	8.4
6259	764	1	0	132.5	0	4.5
6260	764	2	37.5	136.3	41.4	4.5
6261	764	3	75	132.5	61.21	4.5
6262	764	4	120	120	69.14	5
6263	764	5	150	107.5	69.14	6.5
6264	764	6	175	93.5	64.38	7.3
6265	764	7	200	77.5	58.61	8
6266	765	1	0	156	0	0
6267	765	2	720	151	40	0
6268	765	3	1440	145	64	0
6269	765	4	2160	138	76	0
6270	765	5	2592	130	80	0
6271	765	6	2988	121	80.5	0
6272	765	7	3420	111	80	0
6273	765	8	3600	105	79	0
6274	766	1	0	464.7	0	0
6275	766	2	341.1	456.6	67	0
6276	766	3	512.8	440.5	81	0
6277	766	4	727.4	408.3	86	0
6278	766	5	882.5	358	84	0
6279	766	6	1040	295.7	78.4	0
6280	767	1	0	464.7	0	0
6281	767	2	341.1	456.6	67	0
6282	767	3	512.8	440.5	81	0
6283	767	4	727.4	408.3	86	0
6284	767	5	882.5	358	84	0
6285	767	6	1040	295.7	78.4	0
6286	768	1	180	97	52	0
6287	768	2	223.2	96	62	0
6288	768	3	316.8	96.9	73	0
6289	768	4	468	91.7	82	0
6290	768	5	583.2	85.7	78	0
6291	769	1	0	56	0	0.3
6292	769	2	50	57.5	50	1.6
6293	769	3	67.5	56	73	2
6294	769	4	82.5	54	76	2.6
6295	769	5	102.5	51	76	3.6
6296	769	6	122.5	46	73	4.8
6297	769	7	132.5	43	70	5.4
6298	770	1	0	118	0	0.3
6299	770	2	32.5	120	40	1.6
6300	770	3	60	120	50	2
6301	770	4	97.5	118	70	2.6
6302	770	5	125	112	73	3.6
6303	770	6	162.5	100	73	4.8
6304	770	7	187.5	90	70	5.4
6305	771	1	0	185.1	0	9.7
6306	771	2	147.5	185.1	50	16.1
6307	771	3	236.2	181.7	62	18.52
6308	771	4	296.2	177.9	68	23.9
6309	771	5	371.2	169.9	71	26.4
6310	771	6	442.5	160.6	72.5	29.4
6311	771	7	541.2	141.7	72	31.6
6312	772	1	0	185.1	0	12.3
6313	772	2	146.2	184.6	44	21.3
6314	772	3	337.5	180	66	28.1
6315	772	4	461.2	171.6	73	33.3
6316	772	5	568.8	160.6	77	36.7
6317	772	6	651.2	149.7	77	38.4
6318	772	7	715	138.7	75	40.1
6319	773	1	0	41.7	0	5.9
6320	773	2	23.76	41.7	30	5.7
6321	773	3	47.16	41.7	50	5.7
6322	773	4	99	40.5	70	5.7
6323	773	5	149.4	36.8	75	6.4
6324	773	6	178.56	33.5	73	7.6
6325	773	7	194.4	31.4	68	8.1
6326	774	1	0	52.4	0	5.9
6327	774	2	25.92	52.6	30	5.9
6328	774	3	51.84	52.4	50	5.7
6329	774	4	122.04	50.1	73	5.9
6330	774	5	162.72	46.4	75.5	7.1
6331	774	6	184.32	44	75	7.9
6332	774	7	218.16	39.2	68	10
6333	775	1	0	58.4	0	6
6334	775	2	28.08	58.2	30	5.7
6335	775	3	54.36	57.7	50	5.7
6336	775	4	126	55.5	73	5.9
6337	775	5	169.92	51.6	76	7.2
6338	775	6	195.84	48.5	75	8.6
6339	775	7	229.68	43.2	69	11.2
6340	776	1	0	77.42	0	0
6341	776	2	54.55	77.42	46	0
6342	776	3	109.11	74.68	66	0
6343	776	4	136.38	73.15	74	0
6344	776	5	163.66	70.1	76	0
6345	776	6	190.94	64.01	77	0
6346	776	7	220.67	59.44	75	0
6347	777	1	0	77.42	0	0
6348	777	2	54.55	77.42	40	0
6349	777	3	163.66	73.91	72	0
6350	777	4	218.21	69.8	77	0
6351	777	5	245.49	66.45	79	0
6352	777	6	272.77	62.48	78	0
6353	777	7	300.04	54.86	76	0
6354	778	1	0	357.6	0	3.9
6355	778	2	321.3	358.8	49	5.1
6356	778	3	798.2	350.7	64	7
6357	778	4	1059	340.1	70	8
6358	778	5	1451	313.3	79	9.3
6359	778	6	1667	294.1	75	9.8
6360	778	7	1873	269.8	72	10.3
6361	779	1	0	108.8	0	0
6362	779	2	54.55	109.1	30	0
6363	779	3	109.1	108.5	50	0
6364	779	4	163.7	106.7	64	0
6365	779	5	218.2	103.6	71	0
6366	779	6	327.3	91.74	77	0
6367	779	7	381.9	82.3	76	0
6368	780	1	0	83.7	0	8.4
6369	780	2	27.2	85.6	30	8
6370	780	3	50.5	85.9	50	8
6371	780	4	113.7	80	75	7.8
6372	780	5	155.8	71.1	78.5	8.2
6373	780	6	175.5	65.9	78	8.4
6374	780	7	208.5	55.9	74	10.5
6375	781	1	0	106.3	0	8.2
6376	781	2	29	107.8	30	8.2
6377	781	3	75.9	107.8	60	8.2
6378	781	4	125.1	101.9	75	7.8
6379	781	5	175.5	89.6	79.5	8.8
6380	781	6	211.1	78.9	78	10.7
6381	781	7	245.8	67.4	74	13.5
6382	782	1	0	117.8	0	8.4
6383	782	2	30.7	120.7	30	8.2
6384	782	3	59.2	121.1	50	8
6385	782	4	131.2	114.1	75	7.8
6386	782	5	187.4	99.6	80	8.9
6387	782	6	226.9	86.7	78	11.7
6388	782	7	259.4	75.2	74	15.7
6389	783	1	0	71	0	4
6390	783	2	100.8	72	30	4
6391	783	3	298.8	73	60	4
6392	783	4	540	71	77	5
6393	783	5	727.2	62	80.5	7
6394	783	6	831.6	55	79	10
6395	783	7	921.6	51	75.4	13.5
6396	784	1	0	104	0	3
6397	784	2	115.2	107	30	3
6398	784	3	331.2	108	60	3
6399	784	4	583.2	101	77	4
6400	784	5	817.2	89	81.5	8
6401	784	6	961.2	81	79	12
6402	784	7	1054.8	75	75.4	17.4
6403	785	1	0	116	0	2
6404	785	2	118.8	118	30	2
6405	785	3	349.2	120	60	2
6406	785	4	608.4	113	77	3
6407	785	5	860.4	100	82	8
6408	785	6	1029.6	88	79	14
6409	785	7	1116	82	75.4	21
6410	786	1	0	84.5	0	9.5
6411	786	2	200.52	82.7	30	9.5
6412	786	3	388.8	79	50	9.1
6413	786	4	645.48	76.1	70	8.9
6414	786	5	994.32	72	80.5	9.8
6415	786	6	1179	64.7	77	11.8
6416	786	7	1315.08	57.7	68	13.8
6417	787	1	0	108.3	0	9.5
6418	787	2	220.68	105.4	30	9.5
6419	787	3	433.08	100.3	50	9.1
6420	787	4	974.52	94.8	80	9.8
6421	787	5	1138.68	90.4	81.5	11.4
6422	787	6	1355.4	80.8	77	14.5
6423	787	7	1487.52	73.5	68	16.8
6424	788	1	0	120.8	0	9.5
6425	788	2	240.48	117.2	30	9.5
6426	788	3	453.24	111.7	50	9.3
6427	788	4	894.24	107.6	77	9.1
6428	788	5	1203.12	100.3	82	12.5
6429	788	6	1359.36	94	80	14.3
6430	788	7	1571.76	81.6	68	18.2
6431	789	1	0	92	0	0
6432	789	2	165	96.5	50	5.5
6433	789	3	360	94	73	5.5
6434	789	4	450	90	74	5.5
6435	789	5	578	83	80	6
6436	789	6	705	73.5	78	14.5
6437	789	7	845	60	68	20
6438	790	1	0	107.5	0	0
6439	790	2	180	112	50	5.5
6440	790	3	365	111	73	5.5
6441	790	4	460	108	80	5.5
6442	790	5	625	101	83	6
6443	790	6	880	79	78	14.5
6444	790	7	1000	66.5	68	20
6445	791	1	0	102.5	0	0
6446	791	2	160	106	40	5
6447	791	3	325	103.5	63	5
6448	791	4	400	102	70	5
6449	791	5	495	99	77	5
6450	791	6	700	89	80	6.3
6451	791	7	860	76	77	9.5
6452	792	1	0	128	0	5
6453	792	2	185	132.5	40	5
6454	792	3	365	131	63	5
6455	792	4	565	126	77	5
6456	792	5	650	122.5	80	5
6457	792	6	820	115	83	6.3
6458	792	7	1095	91.5	77	9.5
6459	793	1	0	129.7	0	0
6460	793	2	221.4	130.3	38.5	0
6461	793	3	425.16	127.9	55	0
6462	793	4	578.52	125.3	62	0
6463	793	5	782.28	118	68	0
6464	793	6	924.84	110.7	69	0
6465	793	7	1096.56	97.5	67	0
6466	794	1	0	27.4	0	2.5
6467	794	2	4.2	27.4	30	2.6
6468	794	3	8.8	27.2	50	2.7
6469	794	4	14.3	26.7	65	2.7
6470	794	5	21.7	23.8	71	3.2
6471	794	6	26.1	21.7	70	4.1
6472	794	7	31.1	17.9	64	6.2
6473	795	1	0	34.1	0	2.4
6474	795	2	4.7	34.2	30	2.5
6475	795	3	9	34.2	50	2.6
6476	795	4	15.4	33.3	65	2.5
6477	795	5	24.3	30.1	72.5	3.9
6478	795	6	30.4	25.8	70	5.8
6479	795	7	35.2	22	64	8.3
6480	796	1	0	38	0	2.4
6481	796	2	5.1	38	30	2.7
6482	796	3	13.5	37.5	60	2.6
6483	796	4	21.8	35.3	72	3.3
6484	796	5	25.9	33.2	73	4.3
6485	796	6	32.8	28.3	70	7
6486	796	7	37.5	24.4	64	9.3
6487	797	1	0	91.8	0	4
6488	797	2	24.84	92.3	30	3.8
6489	797	3	51.84	90.2	50	3.8
6490	797	4	73.08	87.7	60	4
6491	797	5	106.56	79.1	68	4.5
6492	797	6	125.28	70.5	70	4.9
6493	797	7	147.96	57.4	67	5.5
6494	798	1	0	102.1	0	4
6495	798	2	27	102.1	30	4
6496	798	3	54	100.9	50	3.8
6497	798	4	93.96	93.9	65	4.2
6498	798	5	123.84	83.2	70	4.9
6499	798	6	135.36	77.5	71	5.1
6500	798	7	158.4	63.9	67	5.8
6501	799	1	0	127.1	0	4
6502	799	2	30.24	127.5	30	3.9
6503	799	3	84.24	121.8	60	4
6504	799	4	115.56	113.2	68	4.6
6505	799	5	147.24	98.4	71.5	5.5
6506	799	6	165.6	87.3	70	6
6507	799	7	178.92	77.1	67	6.6
6508	800	1	0	90.1	0	4.2
6509	800	2	22.68	90.1	30	4.1
6510	800	3	75.6	89	60	4.5
6511	800	4	109.08	86	70	5.5
6512	800	5	144.72	77	73.5	6.9
6513	800	6	162	70.1	73	7.7
6514	800	7	180	61	68	8.7
6515	801	1	0	114.9	0	4.2
6516	801	2	27	115.7	30	4.2
6517	801	3	54	114.9	50	4.3
6518	801	4	115.2	108.2	70	5.9
6519	801	5	159.84	97.7	75	7.7
6520	801	6	184.68	86.4	73	9
6521	801	7	200.52	77.2	68	9.8
6522	802	1	0	128.3	0	4.2
6523	802	2	29.88	127.9	30	4.1
6524	802	3	81.72	126.2	60	4.8
6525	802	4	131.04	117.8	72	6.3
6526	802	5	169.92	107.8	75.5	8.1
6527	802	6	191.16	99	74	9.5
6528	802	7	213.48	85.6	68	10.5
6529	803	1	0	123.7	0	4.5
6530	803	2	41.76	127.3	30	4.5
6531	803	3	59.04	128.2	40	5.1
6532	803	4	99	128.2	60	5.8
6533	803	5	172.8	110.3	73	7.2
6534	803	6	223.2	90.5	70	9
6535	803	7	245.52	78.8	64	10.1
6536	804	1	0	157.8	0	4.7
6537	804	2	45.72	161.4	30	5.1
6538	804	3	109.8	160.5	60	5.6
6539	804	4	178.56	146.2	75	7.6
6540	804	5	199.8	139	75.5	7.9
6541	804	6	253.44	112.9	70	10.4
6542	804	7	277.56	98.6	64	11.5
6543	805	1	0	175.8	0	4.7
6544	805	2	46.44	180.3	30	4.7
6545	805	3	89.28	181.2	50	5.8
6546	805	4	181.44	165.9	75	7.8
6547	805	5	210.6	156	76	8.5
6548	805	6	269.64	125.5	70	11
6549	805	7	293.04	110.3	64	12.2
6550	806	1	0	126	0	5.2
6551	806	2	72	124	50.64	5.2
6552	806	3	108	122	61.85	5.2
6553	806	4	144	118	68.03	6.2
6554	806	5	180	110	72.85	7.2
6555	806	6	216	102	72.27	8.8
6556	806	7	252	86	67.05	10.2
6557	807	1	0	144	0	5.2
6558	807	2	54	140	40.36	5.2
6559	807	3	108	138	60.56	5.2
6560	807	4	162	132	70.14	6.8
6561	807	5	216	120	73.51	8.8
6562	807	6	270	97	68.56	11
6563	807	7	288	86	66.11	12
6564	808	1	0	160	0	5.2
6565	808	2	54	158	40.05	5.2
6566	808	3	108	155	58.43	5.2
6567	808	4	162	150	69.64	6.8
6568	808	5	216	136	74.75	8.8
6569	808	6	270	120	71.14	11
6570	808	7	288	105	68.04	12
6571	809	1	0	178	0	5.2
6572	809	2	72	176	46.62	5.2
6573	809	3	144	170	66.65	6
6574	809	4	216	156	74.58	8.8
6575	809	5	252	146	74.75	10
6576	809	6	288	130	72.81	12
6577	809	7	306	118	68.27	13
6578	810	1	0	143	0	7
6579	810	2	90	143	40	7
6580	810	3	144	140	60	7
6581	810	4	219.6	132	70	7.5
6582	810	5	280.8	129	77	8.5
6583	810	6	324	119	79	9.5
6584	810	7	414	102	72	13.5
6585	811	1	0	194	0	7
6586	811	2	64.8	192	30	7
6587	811	3	172.8	189.5	60	7
6588	811	4	234	180	70	7.5
6589	811	5	324	170	77	8.5
6590	811	6	414	152	80	10
6591	811	7	504	130	72	13.5
6592	812	1	0	144.7	0	10.4
6593	812	2	77.04	145.5	30	10.4
6594	812	3	146.52	144.3	50	10.2
6595	812	4	263.52	139.3	70	10.9
6596	812	5	330.48	132.4	77	11.5
6597	812	6	404.64	120.5	78	13.3
6598	812	7	482.4	104.5	75	15.4
6599	813	1	0	175.8	0	10.4
6600	813	2	87.12	176.2	30	10.4
6601	813	3	160.2	175.4	50	10.4
6602	813	4	284.76	169.3	70	11.1
6603	813	5	410.04	154.9	80	13.3
6604	813	6	450.36	147.1	80.5	14.3
6605	813	7	538.2	126.6	75	17.8
6606	814	1	0	194.3	0	10.4
6607	814	2	93.24	194.3	30	10.2
6608	814	3	218.88	192.6	60	10.4
6609	814	4	299.16	188.5	70	11.3
6610	814	5	425.52	172.1	80	13.5
6611	814	6	474.12	162.7	81	15.4
6612	814	7	570.24	139.3	75	19.3
6613	815	1	0	59	0	5
6614	815	2	23.4	58	40	5
6615	815	3	41.4	55	60	5
6616	815	4	59.4	51	68	5.1
6617	815	5	73.8	46	70	5.5
6618	815	6	91.8	37	66	6.5
6619	815	7	106.2	28	57	7
6620	816	1	0	85	0	5
6621	816	2	25.2	84	40	5
6622	816	3	48.6	80	60	5
6623	816	4	77.4	73.5	70	5.1
6624	816	5	86.4	67	71	5.5
6625	816	6	108	55	67	6.5
6626	816	7	127.8	40.5	58	7
6627	817	1	0	58.9	0	4.4
6628	817	2	16.92	58.9	30	4.5
6629	817	3	35.28	56.8	50	4.5
6630	817	4	47.52	54.7	60	4.6
6631	817	5	86.76	44	68	5.5
6632	817	6	104.76	38.1	67	6.6
6633	817	7	122.4	30.9	63	7.8
6634	818	1	0	75.5	0	4.4
6635	818	2	20.52	75.5	30	4.5
6636	818	3	40.68	73.8	50	4.5
6637	818	4	54.72	70.9	60	4.7
6638	818	5	98.28	57.7	70	6.1
6639	818	6	120.24	47.9	67	7.6
6640	818	7	136.44	40.2	63	9
6641	819	1	0	84	0	4.4
6642	819	2	22.32	84.9	30	4.6
6643	819	3	43.92	82.3	50	4.7
6644	819	4	75.96	75.1	67	5.1
6645	819	5	105.84	64.5	70.5	6.7
6646	819	6	129.6	53	67	8.4
6647	819	7	144	45.7	63	9.5
6648	820	1	0	34	0	0
6649	820	2	150	30.5	35	0
6650	820	3	300	27.5	59	0
6651	820	4	450	24.5	72.5	0
6652	820	5	600	21.25	74	0
6653	820	6	750	16.25	67.5	0
6654	820	7	900	10.5	52.5	0
6655	821	1	0	125	0	0
6656	821	2	160	125	60.5	1.3
6657	821	3	200	125	68.06	1.4
6658	821	4	240	122	72.47	1.8
6659	821	5	280	120	76.23	2.4
6660	821	6	320	116	77.74	3.2
6661	821	7	360	112	78.41	4
6662	821	8	400	108	78.41	5
6663	821	9	440	98	73.37	5.8
6664	822	1	0	52	0	5
6665	822	2	250	51	32.5	5
6666	822	3	500	50.5	57.5	5
6667	822	4	750	49	75	5.5
6668	822	5	1000	45	82.5	6.5
6669	822	6	1250	38	82.5	9
6670	822	7	1438	30	77.5	9.5
6671	823	1	561.96	153.8	56	5.41
6672	823	2	861.84	139.4	72	5.62
6673	823	3	1035	132.5	81	5.85
6674	823	4	1220.04	119.3	81	6.24
6675	823	5	1350	108	81	6.82
6676	823	6	1450.08	85.7	75	7.31
6677	823	7	1548	64	65	8.8
6678	824	1	0	119.5	0	2
6679	824	2	187.2	115	50.5	2.2
6680	824	3	252	108	59	2.2
6681	824	4	284.4	105.5	63.5	2.2
6682	824	5	360	99.5	72.5	2.9
6683	824	6	432	95	79	3.7
6684	824	7	504	89.5	81.5	4.9
6685	824	8	576	80	80.5	6.4
6686	824	9	612	72.5	76	7.5
6687	825	1	144	120	42.78	1
6688	825	2	216	111.5	55.12	1.5
6689	825	3	288	105.5	66.2	2.2
6690	825	4	360	100	74.27	2.8
6691	825	5	432	95	80.99	3.7
6692	825	6	482.4	91.5	83.48	4.3
6693	825	7	540	85	83.33	5.6
6694	825	8	612	72.5	80.02	7.5
6695	826	1	0	237.5	0	0
6696	826	2	270	214	46.28	0
6697	826	3	531	195	70.15	0
6698	826	4	666	187.5	78.18	0
6699	826	5	756	173	79.15	0
6700	826	6	835.2	165	82.48	0
6701	826	7	900	155	83.49	0
6702	826	8	975.6	142	82.92	0
6703	827	1	0	290	0	0
6704	827	2	356.4	265	28	0
6705	827	3	720	242	50	0
6706	827	4	1080	220	64	0
6707	827	5	1440	205	74	0
6708	827	6	1800	195	80	0
6709	827	7	2196	183	82.7	0
6710	827	8	2520	160	81	0
6711	827	9	2808	135	76	0
6712	828	1	0	290	0	0
6713	828	2	356.4	265	28	0
6714	828	3	720	242	50	0
6715	828	4	1080	220	64	0
6716	828	5	1440	205	74	0
6717	828	6	1800	195	80	0
6718	828	7	2196	183	82.7	0
6719	828	8	2520	160	81	0
6720	828	9	2808	135	76	0
6721	829	1	0	26.5	0	0
6722	829	2	10000	22.5	30	0
6723	829	3	17500	19.7	70	9.8
6724	829	4	25000	17.5	78	9.8
6725	829	5	26500	17	80	9.8
6726	829	6	30000	14.8	82	9.9
6727	829	7	35500	8.5	74	10
6728	830	1	4200	10.5	64.9	0
6729	830	2	5050	9	68.74	0
6730	830	3	5340	8	67.62	6.5
6731	830	4	5630	7.5	70.96	6.9
6732	830	5	6120	6.5	75.7	7.16
6733	830	6	6460	5.5	77.39	7.5
6734	830	7	7020	3.5	70.41	8.2
6735	830	8	7300	2.8	74.2	8.5
6736	830	9	7600	2.6	86.08	9
6737	831	1	0	16.2	0	0
6738	831	2	20	15.8	33.09	0
6739	831	3	40	15	57.32	3
6740	831	4	60	14.2	74.83	3.75
6741	831	5	80	10	68.06	4.4
6742	831	6	100	6	48.04	4.9
6743	831	7	111	3.8	31.9	5.25
6744	832	1	0	19.8	0	0
6745	832	2	20	19	32.33	0
6746	832	3	40	18.4	55.66	3.75
6747	832	4	60	16.9	70.79	4.5
6748	832	5	80	13.8	75.14	5.25
6749	832	6	100	9.5	60.15	6
6750	832	7	120	5	36.71	6.7
6751	832	8	122	4.5	33.22	6.75
6752	833	1	0	33	0	0
6753	833	2	20	33	50	0
6754	833	3	40	32.5	58.99	0
6755	833	4	60	32	67.02	0
6756	833	5	80	31.5	81.68	3.4
6757	833	6	100	30.5	75.49	3.6
6758	833	7	120	29.5	81.68	4
6759	833	8	140	27.5	84.53	4.3
6760	833	9	160	25.5	79.34	4.7
6761	833	10	180	22.5	73.51	5.2
6762	833	11	189	21	68.39	5.5
6763	834	1	0	19	0	0
6764	834	2	2	17.8	13.85	0
6765	834	3	4	16.5	24.96	0
6766	834	4	6	15.4	32.67	0.5
6767	834	5	8	13.8	37.57	2.5
6768	834	6	10	11.2	33.88	4.3
6769	834	7	12	8	26.14	5.8
6770	834	8	14	3	9.69	6.4
6771	834	9	14.3	2.5	8.25	6.5
6772	835	1	0	23.5	0	0
6773	835	2	2	22.5	13.17	0
6774	835	3	4	21	23.34	0
6775	835	4	6	20	32.67	0
6776	835	5	8	18.6	36.83	1.7
6777	835	6	10	16	38.21	3.4
6778	835	7	12	12.3	33.49	4.8
6779	835	8	14	8.2	22.32	5.8
6780	835	9	16	3	8.02	6.5
6781	836	1	0	4.75	0	0
6782	836	2	1	4.4	12.4	0
6783	836	3	2	4.2	25	0
6784	836	4	3	3.8	34	0.2
6785	836	5	4	3.4	38	0.95
6786	836	6	5	3	35	1.55
6787	836	7	6	1.75	27	2
6788	836	8	7	0.75	11	2.15
6789	836	9	7.2	0.6	9	2.2
6790	837	1	0	5.8	0	0
6791	837	2	1	5.6	13.26	0
6792	837	3	2	5.4	24.92	0
6793	837	4	3	5	34.03	0
6794	837	5	4	4.55	39.64	0.6
6795	837	6	5	3.75	39.27	1.2
6796	837	7	6	2.95	34.42	1.7
6797	837	8	7	2	22.42	2.05
6798	837	9	8	0.75	8.17	2.3
6799	838	1	0	56	0	0
6800	838	2	20	54	42.01	3
6801	838	3	40	52	56.63	3.6
6802	838	4	60	48	60.31	4.2
6803	838	5	80	40	58.08	6
6804	838	6	95	31	50.11	8.4
6805	839	1	0	68	0	0
6806	839	2	20	66	39.93	3
6807	839	3	40	64	53.61	3.6
6808	839	4	60	59.5	60.75	4
6809	839	5	80	52	62.92	5.6
6810	839	6	100	39.5	55.15	8
6811	839	7	116	19	30.26	11
6812	840	1	0	6	0	0
6813	840	2	1	5.75	17	0
6814	840	3	2	5.5	32	0
6815	840	4	3	5.25	40	1.4
6816	840	5	4	5	45	1.4
6817	840	6	5	4.5	43.5	1.5
6818	840	7	6	3.8	39	1.65
6819	840	8	7	2.4	29	2.1
6820	840	9	7.5	1.5	22.5	2.45
6821	841	1	0	6.6	0	0
6822	841	2	1	6.5	13	0
6823	841	3	2	6.3	26	0
6824	841	4	3	6.1	36	1.4
6825	841	5	4	5.9	42	1.4
6826	841	6	5	5.6	45	1.4
6827	841	7	6	5.25	45	1.5
6828	841	8	7	4.7	42	1.6
6829	841	9	8	3.9	35	1.7
6830	841	10	9	2	25	2.2
6831	841	11	9.45	1	18	2.4
6832	842	1	0	21	0	0
6833	842	2	2	20.5	11.16	0
6834	842	3	4	20	21.78	0
6835	842	4	6	19	31.04	4
6836	842	5	8	18.5	40.29	4
6837	842	6	10	17	46.28	4.1
6838	842	7	12	15.3	45.44	4.4
6839	842	8	14	13	41.29	4.71
6840	842	9	16	7	24.01	6.2
6841	842	10	16.8	4	14.07	7
6842	843	1	0	27	0	0
6843	843	2	2	26	11.33	0
6844	843	3	4	25	20.94	0
6845	843	4	6	24.5	29.65	4
6846	843	5	8	23.5	36.56	4
6847	843	6	10	22.6	42.43	4
6848	843	7	12	21	45.74	4.25
6849	843	8	14	19	42.6	4.5
6850	843	9	16	16.2	38.15	4.9
6851	843	10	18	9.5	20.24	6.2
6852	843	11	19	5	9.95	6.9
6853	844	1	0	6.1	0	0
6854	844	2	5	6	40.84	2.5
6855	844	3	10	5.2	48.82	2.75
6856	844	4	15	2.5	25.52	3.25
6857	844	5	17	0.6	5.79	3.5
6858	845	1	0	7.8	0	2
6859	845	2	5	7.7	37.44	2.25
6860	845	3	10	7	56.05	2.6
6861	845	4	15	4.8	44.55	3
6862	845	5	19.2	0.6	5.81	3.5
6863	846	1	0	31	0	0
6864	846	2	5	30.5	0	0
6865	846	3	10	30	40.84	2
6866	846	4	15	29	49.35	2.25
6867	846	5	20	27	56.55	2.5
6868	846	6	25	23	52.18	2.7
6869	846	7	30	18	43.89	2.95
6870	846	8	35	10	22.69	3.25
6871	846	9	38.5	3	6.42	3.5
6872	847	1	0	94	0	0
6873	847	2	50	92	48.17	3.6
6874	847	3	100	86	61.62	4
6875	847	4	150	78	67.77	5.2
6876	847	5	200	59	59.49	8.4
6877	848	1	0	120	0	0
6878	848	2	50	118	43.41	3.6
6879	848	3	100	112	60.99	3.8
6880	848	4	150	102	69.42	4.2
6881	848	5	200	84	66.29	6.5
6882	848	6	250	63	57.17	12
6883	848	7	256	60	54.31	12.4
6884	849	1	0	94	0	0
6885	849	2	50	92	56.93	3.4
6886	849	3	100	89	67.31	4.1
6887	849	4	150	82	71.25	4.8
6888	849	5	200	72	70.01	6.4
6889	850	1	0	120	0	0
6890	850	2	50	119	50.62	3.4
6891	850	3	100	116	75.19	3.4
6892	850	4	150	110	72.45	3.8
6893	850	5	200	98	77.34	4.6
6894	850	6	250	84	75.23	7
6895	851	1	0	120	0	0
6896	851	2	50	120	40.84	0
6897	851	3	100	118	54.45	8.8
6898	851	4	150	116	64.02	8.8
6899	851	5	200	110	66.55	9.2
6900	851	6	250	100	63.02	10.2
6901	851	7	280	90	57.17	10.8
6902	852	1	0	156	0	0
6903	852	2	50	155	32.46	0
6904	852	3	100	154	52.41	8.8
6905	852	4	150	149	64.05	8.8
6906	852	5	200	144	73.97	9
6907	852	6	250	136	71.21	9.6
6908	852	7	300	116	63.16	10.4
6909	852	8	350	95	54.86	11.6
6910	852	9	362	90	52.18	12
6911	853	1	0	32.5	0	0
6912	853	2	5	32.5	29.49	0
6913	853	3	10	32	45.85	1.5
6914	853	4	15	30	52.13	1.2
6915	853	5	20	25	52.36	1.5
6916	853	6	25	22	50.76	3.2
6917	853	7	30	17	43.39	6
6918	854	1	0	40	0	0
6919	854	2	5	39	26.54	0
6920	854	3	10	38.5	43.67	1.2
6921	854	4	15	36	53.46	0.8
6922	854	5	20	33	56.15	0.9
6923	854	6	25	28.5	53.88	2.1
6924	854	7	30	23.5	47.98	4
6925	854	8	33	20	40.84	5
6926	855	1	0	56	0	0
6927	855	2	20	54	42.01	3
6928	855	3	40	52	56.63	3.6
6929	855	4	60	48	60.31	4.2
6930	855	5	80	40	58.08	6
6931	855	6	95	31	50.11	8.4
6932	856	1	0	68	0	0
6933	856	2	20	66	39.93	3
6934	856	3	40	64	53.61	3.6
6935	856	4	60	59.5	60.75	4
6936	856	5	80	52	62.92	5.6
6937	856	6	100	39.5	55.15	8
6938	856	7	116	19	30.26	11
6939	857	1	0	37	0	0
6940	857	2	5	36.8	20.04	0
6941	857	3	10	36.2	33.98	2.5
6942	857	4	15	36	45.94	2.55
6943	857	5	20	35	54.45	2.61
6944	857	6	25	33.5	60.8	2.9
6945	857	7	30	30.5	62.28	3.35
6946	857	8	35	27	59.83	3.8
6947	857	9	37	26	59.52	4
6948	858	1	0	45	0	0
6949	858	2	5	44.7	20.28	0
6950	858	3	10	44.2	35.39	2.5
6951	858	4	15	44	47.29	2.5
6952	858	5	20	43	55.09	2.5
6953	858	6	25	41.5	59.47	2.6
6954	858	7	30	39	60.67	2.9
6955	858	8	35	35.5	59.35	3.2
6956	858	9	40	31.5	57.17	3.6
6957	858	10	45	27	50.89	4
6958	859	1	0	70	0	0
6959	859	2	20	69	37.57	3
6960	859	3	40	68	49.37	3.5
6961	859	4	60	66	56.74	4
6962	859	5	80	62	64.3	4.8
6963	859	6	100	56	60.99	6
6964	859	7	120	51	57.46	7
6965	859	8	130	48	56.63	7.5
6966	860	1	0	91	0	0
6967	860	2	20	90	37.7	3
6968	860	3	40	89	51.01	3.3
6969	860	4	60	87	56.85	3.7
6970	860	5	80	83	64.56	4.2
6971	860	6	100	71	60.41	5
6972	860	7	120	70	65.34	6
6973	860	8	140	62	60.59	7.3
6974	860	9	158	54	52.79	8.5
6975	861	1	0	9.8	0	0
6976	861	2	10	9.2	41.75	1.8
6977	861	3	20	7.9	57.36	1.9
6978	861	4	30	6.1	62.28	2.2
6979	861	5	40	3.4	37.03	2.55
6980	861	6	46	1	10.02	2.7
6981	862	1	0	12	0	0
6982	862	2	10	11.5	39.14	1.8
6983	862	3	20	10	57.32	1.85
6984	862	4	30	8.2	66.97	2.1
6985	862	5	40	5.6	55.44	2.45
6986	862	6	50	1.4	14.66	2.7
6987	863	1	0	40	0	0
6988	863	2	20	37.5	40.84	5
6989	863	3	40	32	63.36	6.7
6990	863	4	60	24	56.01	6.8
6991	863	5	80	13	33.31	7.5
6992	863	6	90	4	10.32	8
6993	864	1	0	48	0	0
6994	864	2	20	46.2	41.93	5
6995	864	3	40	41	63.79	5.5
6996	864	4	60	32	61.5	6
6997	864	5	80	23	47.71	7
6998	864	6	100	5	10.47	8
6999	865	1	0	12	0	0
7000	865	2	10	11.2	25.41	0
7001	865	3	20	10.8	43.56	3
7002	865	4	30	10	58.34	3
7003	865	5	40	9.2	63.41	3.25
7004	865	6	50	8	68.06	3.6
7005	865	7	60	6.5	60.67	4.1
7006	865	8	70	5	52.94	4.6
7007	865	9	80	3.6	40.21	5
7008	866	1	0	15	0	0
7009	866	2	10	14.4	23.34	0
7010	866	3	20	13.8	41.75	3
7011	866	4	30	13	53.63	3
7012	866	5	40	12	62.23	3.1
7013	866	6	50	11	68.06	3.45
7014	866	7	60	9.5	65.2	3.75
7015	866	8	70	7.8	59.46	4.2
7016	866	9	80	6	48.76	4.6
7017	866	10	90	4.5	39.38	5
7018	867	1	0	48	0	0
7019	867	2	20	45	30.63	0
7020	867	3	40	43	46.83	3
7021	867	4	60	40	56.82	3
7022	867	5	80	36	61.26	3.4
7023	867	6	100	32	64.53	3.8
7024	867	7	120	26	60.67	4.2
7025	867	8	140	20	51.51	4.5
7026	867	9	160	14	39.35	5
7027	868	1	0	60	0	0
7028	868	2	20	58	28.71	0
7029	868	3	40	55	46.07	3
7030	868	4	60	52	54.8	3
7031	868	5	80	48	61.5	3.3
7032	868	6	100	44	64.75	3.5
7033	868	7	120	38	65.34	4
7034	868	8	140	31	59.08	4.2
7035	868	9	160	24	49.78	4.5
7036	868	10	180	18	40.1	5
7037	869	1	0	32	0	2
7038	869	2	75	31	40	2.1
7039	869	3	112.5	29.8	70	2.3
7040	869	4	250	27.8	78	2.6
7041	869	5	325	25	81	3.2
7042	869	6	388	20.8	78	4.2
7043	869	7	450	15.7	68	5.5
\.


--
-- Data for Name: pump_specifications; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.pump_specifications (id, pump_id, test_speed_rpm, max_flow_m3hr, max_head_m, max_power_kw, bep_flow_m3hr, bep_head_m, npshr_at_bep, min_impeller_diameter_mm, max_impeller_diameter_mm, min_speed_rpm, max_speed_rpm, variable_speed, variable_diameter) FROM stdin;
1	1	1450	194.8	15	0	137.22	14.03	8	184	217	700	2100	t	t
2	2	2960	381	64.3	0	271.04	60.32	9.5	184	217	2100	3450	t	t
3	3	1470	9.64	24.9	0	80.07	22.36	0	200	260	0	0	t	t
4	4	1450	205.3	24.3	0	123.44	22.17	6.7	226	266	700	2100	t	t
5	5	2970	367.5	99.7	0	265.19	91.97	7.3	226	266	2100	3450	t	t
6	6	1470	282	41.2	0	200.73	38.82	6.8	276	336	700	2100	t	t
7	7	1470	287.7	60.2	0	196.51	56.55	6.6	336	412	700	2100	t	t
8	8	2984	60	500	0	43.08	390.35	0	173	173	2984	2984	f	f
9	9	1460	86.9	29.5	0	47.82	13.05	3.3	210	293	1150	1800	t	t
10	10	1480	1500	60	0	998.19	40.35	0	325	390	700	2010	f	t
11	11	1480	1200	140	0	717.53	105.05	0	531	584	750	1480	t	t
12	12	1480	387.69	109	0	286.97	94.12	8.5	454	546	1150	1800	t	t
13	13	1480	1600.79	300.43	0	996.69	198.15	4.57	510	605	900	1800	t	t
14	14	1460	1216.9	57.4	0	759.14	43.34	11.3	330	406	1150	1800	t	t
15	15	1485	2044.12	77.72	0	1352.7	48.1	0	400	470	0	0	f	t
16	16	1480	1524.1	72.4	0	1132.88	58.22	14	365	454	1450	1480	f	t
17	17	1480	1908	125.5	0	1413.19	107.12	0	442	590	1450	1480	f	t
18	18	1480	2048.7	170.4	0	1521.24	141.05	10.3	530	670	1450	1480	f	t
19	19	985	1678	95.2	0	1187.8	81.17	7.8	685	755	750	785	f	t
20	20	2900	400	43	0	263.37	27.44	0	160	198	1460	2900	t	t
21	21	1450	4.28	11	0	133.4	6.62	0	160	197	900	1460	t	t
22	22	1770	4503.6	26.85	0	3191.51	18.19	11.28	8	18	1450	1770	f	t
23	23	2960	475.16	75.1	0	336.71	50.88	31.55	162	202	1450	2960	f	t
24	24	600	20000	37	0	20379.18	21.49	0	0	0	250	600	t	f
25	25	2920	245.6	101.8	0	234.2	68.84	7	226	276	0	0	f	t
26	26	1460	624.24	40.4	0	340.85	20.88	5.1	268	343	1150	1800	t	t
27	27	1460	374.4	24	0	247.06	20.85	8.6	221	271	700	2100	t	t
28	28	1470	361.5	41.8	0	255.72	39.14	7.4	276	336	700	2100	t	t
29	29	1470	384.5	50	0	255.9	56.09	4.8	338	418	700	2100	t	t
30	30	600	2880	170	0	1656	32	0	813	813	600	1200	t	f
31	31	1470	1500	83	0	1000.26	77.61	10.2	419	483	900	2900	t	t
32	32	1480	1980	60	0	1369.84	36.68	0	305.6	382	750	1800	t	t
33	33	1460	1200	130	0	1112.78	99.72	8.6	501.6	590.5	1450	1460	t	t
34	34	1480	1965.1	112.9	0	1605.91	92.49	7.9	470	555.5	1450	1480	t	t
35	35	1480	1965.1	112.9	0	1605.91	92.49	7.9	470	555.5	1450	1480	t	t
36	36	980	1474	30.1	0	1290.83	17.77	0	460	520	700	1480	t	t
37	37	1460	296.2	14.9	0	217.5	11.53	0	184	229	900	1800	t	t
38	38	1460	355.3	15.4	0	257.85	12.24	0	185	229	900	1800	t	t
39	39	1460	446.9	11.5	0	317.82	9.07	0	215	228	900	1800	t	t
40	40	1460	154.01	12.74	0	105.08	9.69	0	180	225	900	1460	t	t
41	41	1460	162	120	0	105.7	89.12	0	180	225	1460	1460	f	t
42	42	1480	3136.6	104	0	2138.34	86.93	16.3	489	540	1450	1480	f	t
43	43	1480	2657.2	106.5	0	1749.83	91.95	19	464	540	1450	1480	f	t
44	44	1460	249.66	12.5	0	178.11	10.19	0	180	227	900	1460	t	t
45	45	1480	1647.1	48.5	0	1275.22	33.14	13.5	310	385	1450	1480	f	t
46	46	1480	1968.8	54.1	0	1479.82	38.47	13.8	334	390	985	1480	f	t
47	47	1480	2491	77.4	0	1959.44	57.02	15.8	340	460	1450	1480	f	t
48	48	1480	2247.2	69	0	1737.72	45.85	17.9	340	445	1450	1480	f	t
49	49	735	1506.1	26.1	0	1085.42	21.53	3.7	483	552	500	735	f	t
50	50	985	1792.5	48.6	0	1168.64	42.36	8.2	464	540	985	1450	f	t
51	51	1480	2725.5	146.3	0	1564.1	111.96	0	444.5	596.5	500	1800	t	t
52	52	1470	1500	83	0	1000.26	77.61	10.2	419	483	900	2900	t	t
53	53	1490	2364	60	0	1674.29	42.18	0	482.6	533.4	0	0	f	t
54	54	980	2182	45.72	0	1883.44	36.09	5.65	464	546	700	1450	t	t
55	55	1490	2616.8	189.4	0	1781.28	173.04	9.4	603	720	1150	1500	t	t
56	56	1460	502.2	20.7	0	325.7	15.07	0	217	266	900	1460	t	t
57	57	1460	611	20.4	0	412.91	16.77	0	215	266	900	2200	t	t
58	58	1460	534.2	24.4	0	390.26	22.13	0	354	354	900	1460	t	f
59	59	1460	343	17.6	0	245.5	13.71	0	236	262	900	1460	t	t
60	60	1460	382.4	18.5	0	270.96	14.96	0	236	262	900	1460	t	t
61	61	1460	464.7	18.9	0	334.3	15.4	0	236	262	900	1460	t	t
62	62	985	2483.9	39.9	0	2027.47	25.82	7.8	400	475	985	1450	f	t
63	63	1460	323.7	23.2	0	202.78	19.56	5.15	240	272	1150	1800	t	t
64	64	2920	500	145	0	420.25	116.53	0	270	323	600	2920	t	t
65	65	1460	284.6	56.2	0	187.01	53.91	6.9	315	406	1150	1800	t	t
66	66	1460	313.9	16	0	217.32	12.71	6.3	210	239	1150	1800	t	t
67	67	1460	237.8	10.1	0	168.28	8.03	6	190	210	1150	1800	t	t
68	68	1450	386.9	6.6	0	371.36	9.48	10.3	212	217	700	2100	t	t
69	69	1470	458.2	24.2	0	306.69	22.61	8.1	216	266	700	2100	t	t
70	70	1470	548.4	38	0	349.12	34.99	8.4	261	336	700	2100	t	t
71	71	1480	608.7	62.9	0	389.63	58.51	5.8	350	418	700	2100	t	t
72	72	1460	572.6	27.3	0	424.76	22.54	0	250	307	900	1460	t	t
73	73	960	333.5	11.7	0	278.53	9.73	0	252	307	700	960	t	t
74	74	1460	813.2	26.8	0	586.19	21.71	0	250	307	900	1460	t	t
75	75	960	509.6	11.8	0	387.94	9.48	0	255	307	700	960	t	t
76	76	985	3904.9	62.9	0	2987.07	44.96	11.1	490	610	0	0	f	t
77	77	985	3299.5	93.2	0	2401.84	73.62	11.4	610	745	650	985	f	t
78	78	985	5500	140	0	4015.67	115.03	10.5	730	910	750	1450	t	t
79	79	1460	2800	60.5	0	2237.06	36.93	15	368	450	960	1480	t	t
80	80	980	4022.3	91.7	0	3430.46	69.74	8.3	635	750	980	1450	f	t
81	81	1000	2500	205	0	2044.29	149.83	0	545	625	700	1300	t	t
82	82	1460	1000	40	0	732.87	25.22	0	274	343	900	1600	t	t
83	83	1480	800	36	0	709.43	23.97	0	274	343	1200	1750	t	t
84	84	960	695	15.4	0	475.75	11.54	0	256	343	700	960	t	t
85	85	1460	1389.5	36.8	0	878.37	29.91	0	272	343	750	2000	t	t
86	86	1482	1389.5	220	0	804.12	165.48	0	272	343	1200	1580	t	t
87	87	1480	1070	37.82	0	879.26	25.31	0	272	343	750	1700	t	t
88	88	960	854.9	16.6	0	586.81	13.46	0	258	343	700	960	t	t
89	89	1450	2000	193	0	0	0	0	0	362	1000	1800	f	t
90	90	1460	1434.7	31	0	1217.45	26.56	0	274	362	900	1800	t	t
91	91	970	953.5	13.4	0	813.77	11.56	0	292	362	700	970	t	t
92	92	1460	1600	41.5	0	1197.69	20.53	0	291	362	900	1800	t	t
93	93	970	1061	10	0	808.01	8.89	0	281	362	700	980	t	t
94	94	1460	1600	77	0	167.37	57.88	0	970	1750	970	1750	t	f
95	95	2950	37.5	105	0	29.09	85.24	4.6	190	267	1800	3500	t	t
96	96	2950	34	65	0	25.4	54.4	0	152	215	0	0	t	t
97	97	1460	495.6	30	0	303.79	24.74	6.95	280	309	1150	1800	t	t
98	98	960	325	13	0	210.48	10.72	4	225	309	700	1150	t	t
99	99	1460	600	100	0	283.89	42.83	10	315	371	1150	2300	t	t
100	100	960	330	20	0	190.4	18.43	5	254	371	700	1150	t	t
101	101	960	295	30.5	0	199.6	28.71	4.5	296	459	700	1150	t	t
102	102	1460	459.8	71	0	302.98	67.27	7.9	370	459	1150	1800	t	t
103	103	1460	455.8	19	0	311.1	15.59	8.2	245	272	1150	1800	t	t
104	104	960	301.2	8.2	0	196.68	6.83	5	245	272	700	1150	t	t
105	105	1460	367.3	13.3	0	265.11	10.72	8	220	245	1150	1800	t	t
106	106	960	245.1	5.7	0	165.33	4.55	5	220	245	700	1150	t	t
107	107	1460	661.7	24.4	0	448.04	20.65	12.6	275	309	1150	1800	t	t
108	108	960	435	10.5	0	293.35	8.72	55	275	309	700	1150	t	t
109	109	1460	516.2	16	0	366.36	12.7	12.5	250	275	1150	1800	t	t
110	110	960	336.9	6.9	0	239.19	5.68	5	250	275	700	1150	t	t
111	111	1460	748.3	39.1	0	467.96	32.24	8.8	318	352	1150	1800	t	t
112	112	1460	761.1	63.8	0	433.3	58.05	13	358	431	1150	1800	t	t
113	113	960	440	27.5	0	287.76	24.96	5.6	288	431	700	1150	t	t
114	114	1460	697.3	102.2	0	427.5	72.23	12	420	542	1150	1800	t	t
115	115	980	5400	89	0	3894.54	64.81	14	540	740	650	1250	t	t
116	116	980	5400	89	0	3894.54	64.81	14	540	740	0	0	t	t
117	117	980	4980	58.5	0	3809.73	43.72	0	544	608	600	980	t	t
118	118	980	8000	130	0	4214.52	74.47	0	641	780	600	1000	t	t
119	119	985	4000	80	0	3934.62	67.3	0	698	630	700	1000	f	t
120	120	735	4073	21	0	3061.31	13.26	6.3	500	545	650	735	f	t
121	121	985	5828	36.2	0	3917	23.05	14.1	475	545	750	985	f	t
122	122	985	3479	30.2	0	2619.1	20.94	8.5	455	490	735	985	f	t
123	123	985	5563.6	75.6	0	3809.42	52.38	14.9	520	580	985	1450	f	t
124	124	985	6131	70	0	4339.79	47.51	20.6	540	650	758	985	f	t
125	125	985	5760	80.5	0	4645.47	63.03	13.6	592	724	985	1450	f	t
126	126	735	5094.5	47	0	4094.76	36.99	8	660	724	735	1450	f	t
127	127	985	6865	89.6	0	4823.8	72.71	16.5	635	743	985	1450	f	t
128	128	740	6600	37	0	4576	24.13	0	576	680	0	0	f	t
129	129	735	7342.5	55.2	0	5821.48	36.92	13.1	675	770	735	1450	f	t
130	130	735	12284.2	110	0	8861.18	86.58	14.6	940	1102	0	0	t	t
131	131	995	7500	200	0	5921.52	152.01	21.1	860	1085	750	995	f	t
132	132	1460	1094.2	79.9	0	614.72	73.8	17	401	484	1150	1800	t	t
133	133	960	630	34.5	0	412.26	31.34	7	322	484	700	1150	t	t
134	134	1460	991.2	126	0	642.66	119.52	17	475	609	1150	1800	t	t
135	135	960	650	54	0	393.55	38.84	7.1	380	609	700	1150	t	t
136	136	1460	1065	36.9	0	716.79	30.42	14	310	358	1150	1800	t	t
137	137	960	694.2	16	0	469.31	12.93	7.5	310	358	700	1150	t	t
138	138	1460	771.7	22	0	539.52	18.08	15	280	310	1150	1800	t	t
139	139	960	491.3	9.5	0	346.05	7.66	8.2	280	310	700	1150	t	t
140	140	1460	1379	42.8	0	929.43	35.37	10.15	345	398	1150	1800	t	t
141	141	960	924.7	18.5	0	621.52	15.03	7.5	345	398	700	1150	t	t
142	142	1460	1039	26.3	0	736.66	20.72	10.5	310	345	1150	1800	t	t
143	143	960	924.7	18.5	0	478.23	8.97	7	310	345	700	1150	t	t
144	144	1460	1477.9	63.2	0	936.16	50.53	16.5	395	453	1150	1800	t	t
145	145	960	949	28	0	610.85	23.7	8.7	397	453	700	1150	t	t
146	146	1460	1498.3	100.3	0	842.18	91.78	25	444	537	1150	1800	t	t
147	147	960	883.7	43.3	0	592.62	39.45	10.25	446	537	700	1150	t	t
148	148	1480	1500	55	0	1051.01	40.38	9.4	315	375	1480	2000	t	t
149	149	1488	1500	60	0	1126.94	42	0	382	382	1488	1488	f	t
150	150	980	2256.6	32.4	0	1644.72	24.16	14.75	451	501	700	1150	t	t
151	151	735	1736.6	17.5	0	1212.65	13.11	9.52	451	501	500	735	t	t
152	152	1450	88.3	49.53	0	61.31	44.65	0	305	381	900	1800	t	t
153	153	1450	62.7	13.01	0	42.01	10.4	0	165	203	900	1800	t	t
154	154	1450	63.75	30.51	0	42.12	26.83	16.46	229	305	900	1450	t	t
155	155	1450	46.8	25	0	30.2	18.56	0	210	260	0	0	f	t
156	156	1450	1756.8	138	0	1177.74	117.68	0	475	610	500	1450	t	t
157	157	980	3073	38.6	0	2182.05	29.35	22.32	468	536	700	1100	t	t
158	158	590	7963.6	21.1	0	5853.39	9.87	9	590	686	0	0	f	t
159	159	590	12459	70	0	8848.78	54.82	10.5	902	1067	590	1450	f	t
160	160	1400	19.5	15.5	0	14.05	13.54	10.8	180	212	700	2100	t	t
161	161	2900	38.5	64.3	0	27.1	59.27	5.5	180	212	2100	3450	t	t
162	162	980	3624	44	0	2435.99	35.83	13.24	512	588	600	1100	t	t
163	163	735	2713	23.2	0	1979.63	18.35	7.48	512	588	500	800	t	t
164	164	990	6048	47.5	0	4548.03	41.66	18	590	640	700	990	t	t
165	165	740	4477	25.3	0	3387.75	23.27	10.11	575	640	500	900	t	t
166	166	1460	1400	70	0	998.2	31.11	0	364	428	0	0	f	t
167	167	990	4800	59	0	3039.68	41.59	23.6	600	660.4	750	1200	t	t
168	168	735	6443	30.4	0	4840.26	27.74	12.1	664	720	500	900	t	t
169	169	2930	110.84	700	0	80.28	590.95	12.5	248	277	1450	2930	t	t
170	170	1465	140	45	0	120	31.04	0	252	360	1465	3000	f	t
171	171	1450	144.3	33.5	0	89.71	31.42	0	238	318	900	1450	t	t
172	172	1450	149.3	34	0	79.97	24.04	7.8	229	305	0	1450	f	t
173	173	2950	117.3	98.42	0	86.51	82.75	0	182	261	1450	2950	t	t
174	174	1450	2700	100	0	1658.15	53.9	0	354	449	1450	1450	f	t
175	175	1480	1800	225	0	1576.79	162.77	0	442	553	900	1480	t	t
176	176	1450	11.1	6.5	0	6.77	5.65	5.3	108	135	0	0	t	t
177	177	2900	21.2	25.9	0	12.33	23.45	4.6	108	135	0	0	f	t
178	178	1450	6	6.9	0	3.68	5.08	8	108	135	0	0	f	t
179	179	2900	11.7	26.7	0	6.51	21.19	5.1	108	135	0	0	f	t
180	180	1450	9.8	6.3	0	6.41	5.31	6.9	108	135	0	0	f	t
181	181	2900	19.4	25.3	0	13.54	20.77	5.7	108	135	1200	2900	t	t
182	182	1450	21	8.1	0	15.32	6.58	4.1	130	155	0	0	f	t
183	183	2900	42.7	33.3	0	33	28.2	4.6	130	155	0	0	f	t
184	184	1450	34.6	12.6	0	23.44	10.37	4.8	154	160	0	0	f	t
185	185	2900	69.9	49.2	0	44.26	42.63	6.2	154	180	0	0	f	t
186	186	1450	60.1	15.9	0	45.47	12.89	4.7	170	205	0	0	f	t
187	187	2900	101.7	59.4	0	78.38	54.03	3.2	170	205	0	0	f	t
188	188	1470	700	350	0	574.53	41.25	0	376	376	1470	1470	f	t
189	189	490	19021	51.7	0	15289.07	34.8	11.8	967	1125	250	750	t	t
190	190	2930	135	211.9	0	96.7	177.13	45	242	277	2250	2930	t	t
191	191	1465	162.58	78.33	0	118	63	0	288	360	0	0	f	t
192	192	1465	250	90	0	131	66.91	0	253	370	1465	2650	f	t
193	193	2930	134.68	32.92	0	94.92	29.23	3.96	134	157	1450	2930	t	t
194	194	2930	136.27	49.07	0	105.65	41.4	3.35	162	183	1430	2930	t	t
195	195	2930	179	68.8	0	136.04	59.82	5	187	220	1450	2930	t	t
196	196	2930	170.34	108.51	0	117.74	96.36	2.23	227	275	1450	2930	t	t
197	197	1465	300	50	0	218.07	38.39	0	300	370	1465	3000	f	t
198	198	1460	220	39	0	136.45	35.55	6.1	248	343	1150	1460	t	t
199	199	2950	360	180	0	264.42	129.07	0	254	337	2950	2950	f	t
200	200	2970	240.75	316.99	0	160.61	271.67	15.24	254	336.5	2550	3000	t	t
201	201	2950	180	80	0	142.22	45.48	0	152	216	2950	2950	f	t
202	202	1410	63	9.8	0	38.77	8.79	4.1	137	177	700	2100	t	t
203	203	2920	112	42.2	0	81.75	37.77	4.1	137	177	2100	3450	t	t
204	204	1420	66.5	17	0	38.07	15.48	13.4	178	218	700	2100	t	t
205	205	2920	109.7	70.4	0	75.42	66.5	8.9	178	218	2100	3450	t	t
206	206	1430	62.3	21.8	0	37.06	20.3	7.1	207	247	700	2100	t	t
207	207	2950	108.9	93	0	71.22	74.32	8.5	207	247	2100	3450	t	t
208	208	1450	50	38.5	0	37.95	35.87	7.5	280	328	700	2100	t	t
209	209	1465	261.65	75.01	0	184.8	59.19	0	288	360	0	0	f	t
210	210	1460	216.5	32.31	0	154.94	28.94	2.23	255	300	1450	1460	t	t
211	211	1490	292	45.4	0	217.84	39.36	2.4	303	351	1450	1490	t	t
212	212	2930	260.97	67.06	0	182	59.13	2.26	193	220	1450	2930	t	t
213	213	2930	275.9	349	0	233.15	94.66	6.8	193	220	1450	2930	t	t
214	214	1465	319.88	42.29	0	200.51	34.54	10	220	360	1000	3000	t	t
215	215	2900	633.2	165.71	0	396.88	135.34	39.18	220	360	1000	3000	t	t
216	216	1465	319.88	42.29	0	200.51	34.54	10	220	360	1000	3000	t	t
217	217	2900	633.2	165.71	0	396.88	135.34	39.18	220	360	1000	3000	t	t
218	218	1450	313.4	41.1	0	187.98	38	0	268	356	900	1450	t	t
219	219	1450	278.1	15.8	0	202.51	13.41	0	184	229	900	1800	t	t
220	220	1480	328	95.76	0	196.96	79.15	0	350	381	500	2900	t	t
221	221	2900	138.7	26.6	0	95.66	23.7	8.6	113	143	2100	3450	t	t
222	222	1420	78.5	10.8	0	56.18	9.52	9.1	140	177	700	2100	t	t
223	223	2920	156.2	43.7	0	108.76	39.07	9.5	140	177	2100	3450	t	t
224	224	1480	84	54.33	0	60.08	48.91	0	178	218	700	2100	t	t
225	225	1440	85.7	16.6	0	60.34	15.02	8.3	178	218	700	2100	t	t
226	226	2950	156.6	69.2	0	128.56	61.52	7.7	178	218	2100	3450	t	t
227	227	1440	89.5	24.5	0	58.12	22.61	6.8	226	266	700	2100	t	t
228	228	2960	177.9	96.7	0	134.85	87.21	7.7	226	266	2100	3450	t	t
229	229	1450	127.7	36.5	0	90.81	34.25	4	281	328	700	2100	t	t
230	230	1480	408	36.6	0	314.25	28.6	3.66	259	312	1450	1800	t	t
231	231	2930	530	106.68	0	354.47	94.11	3.05	232	273	600	3200	t	t
232	232	2930	530	106.68	0	354.47	94.11	3.05	232	273	600	3200	t	t
233	233	2930	436	167	0	310.37	127.51	10.3	285	335	0	3000	f	t
234	234	1450	600	200	0	472.35	142.6	0	414	472	0	2900	t	t
235	235	1470	407.9	94.3	0	282.98	86.17	0	330	387	900	1800	t	t
236	236	2900	95	13.6	0	59.51	12.62	0	0	0	2250	2900	t	f
237	237	1460	414	51	0	285.43	39.86	0	295	394	1460	2900	t	t
238	238	1450	488.9	46.42	0	360.98	44.38	0	286	381	1150	1800	t	t
239	239	1450	369.99	19.11	0	218.69	17.83	0	203	254	900	1800	t	t
240	240	2900	43.9	17.5	0	27.57	15.16	0	142	0	2250	2900	t	f
241	241	2900	80	15.1	0	43.96	13.19	0	0	0	2250	2900	t	f
242	242	2900	64.1	15.39	0	41.62	13.26	0	122	147	2250	3500	t	t
243	243	1450	608	76.9	0	472.12	65.01	8.5	370	450	950	1450	f	t
244	244	1460	891.1	108.6	0	521.03	80.2	16.1	461	560	760	1460	f	t
245	245	2900	26	12.5	0	18.2	9.48	0	108.4	108.4	2250	2900	t	f
246	246	2970	560	120	0	370.66	91.1	0	222	279	2970	2970	f	t
247	247	1480	358	41.4	0	264.57	19.88	9.4	254	342	900	1480	t	t
248	248	980	6292.8	75.8	0	4170.46	62.25	15	572	715	300	980	t	t
249	249	740	4751.68	43.22	0	3149.06	35.5	8.55	600	715	500	980	t	t
250	250	1450	500.11	24.84	0	352.41	23.5	0	248	292	900	1450	t	t
251	251	2900	150	18	0	94.24	15.41	0	0	0	2250	2900	t	f
252	252	1420	137.1	9.2	0	97.03	8.15	1.8	160	177	700	2100	t	t
253	253	2940	274.7	39.5	0	185.32	36.09	6.7	160	177	2100	3450	t	t
254	254	1450	135.6	16.2	0	88.24	15.16	10.3	184	216	700	2100	t	t
255	255	2950	273.7	68.3	0	179.4	62.46	10.6	184	216	2100	3450	t	t
256	256	1450	169	27.3	0	106.51	25.41	8.7	220	271	700	2100	t	t
257	257	2970	306.3	111.1	0	229.21	102.26	10.2	220	271	2100	3450	t	t
258	258	1450	185.1	40	0	124.49	36.96	4.5	276	336	700	2100	t	t
259	259	2920	109.9	165.7	0	43.93	57.22	6.9	220	328	1800	3500	t	t
260	260	1460	60.3	41.4	0	23	13.65	1.2	220	328	1150	1800	t	t
261	261	970	2368	4	0	1725.33	3.16	0	0	0	400	970	t	f
262	262	625	6800	4.6	0	4502.81	4.33	0	508	635	200	625	t	t
263	263	970	1562	7.2	0	871.79	7.18	0	0	0	400	1250	t	f
264	264	970	2500	7.5	0	1122.57	6.31	0	0	0	400	1250	t	f
265	265	1470	2001	17.2	0	1258.05	13.7	0	0	0	400	1500	t	f
266	266	970	2000	6.4	0	855.28	5.35	0	400	1260	400	1250	t	f
267	267	970	1162	6.1	0	744.16	5.12	0	0	0	400	1420	t	f
268	268	970	942.1	5.6	0	632.39	4.45	0	0	0	400	1500	t	f
269	269	1470	1400	13.3	0	478.75	12.04	0	0	0	400	1500	t	f
270	270	970	2000	8	0	1333.44	5.65	0	405	406	900	1100	t	f
271	271	970	2544	10.4	0	1572.8	8.31	0	0	0	400	1090	t	f
272	272	970	2500	8.3	0	1429.12	6.97	0	0	0	400	1078	t	f
273	273	970	1614	7.1	0	1106.57	5.95	0	0	0	400	1208	t	f
274	274	970	1155	6.9	0	766.36	5.36	0	0	0	400	1205	t	f
275	275	735	3828	10	0	2704.69	8.37	0	0	0	400	855	t	f
276	276	735	3491	8.4	0	2223.59	6.46	0	0	0	400	843	t	f
277	277	735	3200	8	0	2248.02	5.77	0	507	509	620	850	t	f
278	278	735	2021	7.7	0	1177.18	5.89	0	0	0	400	990	t	f
279	279	735	5580	11.5	0	4253.26	9.32	0	0	0	400	760	t	f
280	280	735	5125	10.3	0	3679.55	8.31	0	0	0	400	750	t	f
281	281	735	4174	10.6	0	3150.78	7.76	0	0	0	400	880	t	f
282	282	735	3317	9.9	0	2712.03	6.56	0	0	0	400	880	t	f
283	283	580	7507	10	0	5036.05	9.08	0	0	0	400	633	t	f
284	284	580	6324.6	9.7	0	4369.85	8.09	0	0	0	400	625	t	f
285	285	580	5169	9.6	0	3358.03	7.77	0	0	0	400	700	t	f
286	286	580	5000	8.4	0	2660.72	6.85	0	0	0	430	733	t	f
287	287	880	386.11	2.13	0	274.65	1.81	0	217	217	300	1450	t	f
288	288	880	1200	6.8	0	854.13	4.71	0	8.25	8.75	400	880	t	f
289	289	950	1562	7.2	0	1212.48	5.65	0	0	0	400	1250	t	f
290	290	1480	1000	60	0	721.9	44.19	4.6	318	383	1480	2200	t	t
291	291	1480	1200	80	0	744.96	70.35	0	401	458	1480	1480	f	t
292	292	1480	1100	60	0	768.81	49.34	0	377	400	1480	1480	f	t
293	293	1490	2520	93	0	1749.78	89.88	0	480	533	0	0	f	t
294	294	1480	1080	120	0	814.49	100.89	8.5	448	566	1000	3000	t	t
295	295	1480	940.4	241.89	0	796.92	200.07	8.9	480	591	1150	1800	t	t
296	296	1480	800	250	0	587.7	60.69	0	377	444	750	2950	t	t
297	297	1900	911.43	121.12	0	754.48	99.97	0	377	444	750	2200	t	t
298	298	1480	795.1	101.1	0	550.03	94.16	7	433	527	980	1800	t	t
299	299	1480	802.8	174	0	611.66	137.86	12.1	417	495	1150	2100	t	t
300	300	1490	828	159.6	0	630.07	147.34	11	406	495	900	1800	t	t
301	301	1490	700	100	0	475.81	90.43	0	482.6	533.4	1490	1800	t	t
302	302	2900	215.1	22.6	0	184.16	20.09	0	0	0	2250	2900	t	f
303	303	1450	561.36	53.34	0	366.64	50.01	0	330.2	406.4	1460	1800	t	t
304	304	1450	991.9	24.9	0	713.34	22.78	0	248	292	900	1800	t	t
305	305	2900	140	33.5	0	97.72	31.23	0	0	0	2250	2900	t	f
306	306	2900	179.5	250	0	133.97	18.47	0	0	192	1450	2900	t	f
307	307	2900	214.1	25.5	0	176.11	19.04	0	130	186	2250	2900	t	t
308	308	1480	939.3	73	0	727.27	55.72	6.3	356	454	1450	1480	f	t
309	309	1480	977.9	78.6	0	662.42	66.75	9.4	356	463	1450	1480	f	t
310	310	1480	1162.7	120.5	0	762.28	101.8	8	438	570	1450	1480	f	t
311	311	1480	1391.4	191.9	0	975.26	170.14	10.8	590	730	1450	1480	f	t
312	312	2960	851.38	312.94	0	554.38	273.12	0	150	344	2450	2960	t	t
313	313	2960	904.86	315.89	0	558.86	274.64	0	300	344	0	0	f	t
314	314	2960	3748.5	1540.05	0	2440.87	1343.99	0	150	344	2450	2960	t	t
315	315	2960	897.62	470.89	0	558.19	410.16	0	300	344	0	0	f	t
316	316	2960	851.38	191.41	0	554.38	169.4	0	300	344	2450	2960	t	t
317	317	2960	851.38	1257	0	554.38	1111.48	0	344	650	2400	2960	t	t
318	318	2960	903.66	631.82	0	561.5	549.17	0	300	344	0	0	f	t
319	319	1475	511.4	112.7	0	412.93	110.92	0	500	500	700	2950	t	t
320	320	2200	817.2	140.5	0	568.73	135.61	13	0	0	1000	2200	t	f
321	321	2200	792	140	0	499.32	113.49	13	0	0	1000	2200	t	f
322	322	1460	2450	60	0	1703.92	40.59	17	343	419	800	2900	t	t
323	323	1480	5000	400	0	3437.41	251.11	0	620	725	1480	1480	t	t
324	324	985	750	26.1	0	454.52	23.21	0	155	409	750	1450	t	t
325	325	2900	52	160	0	35.46	131.25	0	140	165	2900	2900	f	t
326	326	1490	216	50	0	159.84	27.47	0	300	320	0	1900	t	t
327	327	2950	320	54	0	243.87	40.53	0	110	201	2500	3000	t	t
328	328	2977	200	136.25	0	122.76	119.19	0	184	304	2500	3000	t	t
329	329	480	3592.8	156	0	3000.28	121.56	0	400	450	480	1450	t	t
330	330	2860	1040	464.7	0	725.44	406.01	0	0	0	2200	3800	t	f
331	331	2860	1040	464.7	0	725.44	406.01	0	0	0	2200	3800	t	f
332	332	1490	576	97	0	472.79	91.74	0	420	484	1490	1490	f	t
333	333	2920	190	122	0	102.14	50.83	5.4	210	292	1450	3000	t	t
334	334	1485	715	185.1	0	715	138.74	40.1	340	378	1450	1485	t	t
335	335	1480	229.68	58.4	0	154.04	53.23	11.2	320	378	1450	1480	f	t
336	336	1485	218.21	77.42	0	184.55	66.2	0	348	435	960	2900	t	t
337	337	1485	300.04	77.42	0	239.65	67.21	0	348	435	960	2900	t	t
338	338	1485	1872.5	357.6	0	1249.57	328.85	0	459	510	1450	1490	t	t
339	339	1485	381.87	108.81	0	339.5	89.82	0	459	510	1450	1485	f	t
340	340	1480	259.4	117.8	0	179.07	102.18	15.7	475	555	1450	1480	t	t
341	341	1480	1116	116	0	796.1	103.85	21	475	555	0	1940	f	t
342	342	1480	1571.76	120.8	0	1148.72	101.84	18.2	495	555	1450	1480	t	t
343	343	1490	1000	115	0	600.63	101.82	20	490	530	1150	1800	f	t
344	344	1490	1095	128	0	788.89	115.86	9.5	520	580	1150	1800	f	t
345	345	1485	1096.56	129.7	0	901.87	111.82	0	282	314	1450	1490	f	t
346	346	1480	37.5	38	0	25.29	33.52	9.3	269	314	1450	1480	t	t
347	347	2960	178.92	127.1	0	143.14	100.81	6.6	247	288	1450	2960	f	t
348	348	2960	213.48	128.3	0	157.25	111.85	10.5	249	288	1450	2960	f	t
349	349	2960	293.04	175.8	0	210.89	155.69	12.2	287	337	700	2960	f	t
350	350	2960	320	170	0	220.72	155.61	13	287	337	1450	2950	t	t
351	351	2960	504	194	0	367.92	161.62	13.5	290	360	1450	3600	t	t
352	352	2960	720	194.3	0	453.92	167.21	19.3	313	360	1450	2960	f	t
353	353	2960	144	90	0	82.91	69.49	7	203	240	0	0	f	t
354	354	2960	144	84	0	102.06	65.83	9.5	203	240	750	2960	t	t
355	355	1470	900	34	0	564.52	21.92	0	305	305	1470	1470	f	f
356	356	1480	480	140	0	338.89	114.72	0	470	576	1480	1480	f	t
357	357	1488	1500	60	0	1126.94	42	0	382	382	1488	1488	f	t
358	358	1460	1548	153.8	0	1204.38	122.24	0	362	362	1400	1800	t	t
359	359	1450	612	120	0	510.44	86.85	0	307	369	900	1450	t	t
360	360	1450	612	120	0	518.94	87.23	0	295.2	369	900	1800	t	t
361	361	1490	975.6	237.5	0	975.6	141.74	0	404.3	420.6	1491	1491	f	t
362	362	993	2736	290	0	2140.06	181.17	0	600	632.2	800	980	t	t
363	363	993	2736	290	0	2140.06	181.17	0	590	656	800	980	t	t
364	364	330	40000	27	0	28797.06	15.34	0	1200	1614	300	400	t	t
365	365	730	7600	10.5	0	7600	2.36	0	0	0	400	1450	t	f
366	366	1450	140	250	0	74.06	14.67	6.75	220	240	980	1450	t	t
367	367	1450	189	33	0	105.75	30.27	0	270	300	980	1450	t	t
368	368	2900	16	250	0	9.26	16.81	6.5	122	135	1800	2900	t	t
369	369	1450	8	105	0	4.57	4.12	2.3	122	135	980	1450	t	t
370	370	2900	120	630	0	66.78	58.28	11	210	190	1800	2900	t	t
371	371	1450	10	126	0	5.55	5.57	2.4	122	135	980	1450	t	t
372	372	2900	19	240	0	11.07	16.56	6.9	122	135	1800	2900	t	t
373	373	1450	24.44	105	0	10.86	6.82	3.5	144	160	980	1450	t	t
374	374	2900	40	350	0	0	0	0	144	160	1800	2900	t	t
375	375	2900	260	600	0	152.95	100.29	12.4	242	275	1450	2900	t	t
376	376	2900	250	600	0	142.53	110.52	7	242	275	1450	2900	t	t
377	377	2900	365	720	0	217.98	140.85	12	280	318	1450	2900	t	t
378	378	2900	33	2400	0	20.14	32.75	5	280	315	1800	2900	t	t
379	379	2900	120	630	0	66.78	58.28	11	210	190	1800	2900	t	t
380	380	2900	45	700	0	30.37	30.56	4	160	175	1800	2900	t	t
381	381	2900	160	600	0	87.66	78.92	8.5	210	240	1450	2900	t	t
382	382	1450	60	140	0	28.86	8.53	2.7	169	185	980	1450	t	t
383	383	2900	100	250	0	50.98	37.17	8	169	185	1800	2900	t	t
384	384	1450	100	1760	0	52.45	10.48	5	189	210	980	1450	t	t
385	385	2900	180	280	0	99.91	43.19	5	189	210	1800	2900	t	t
386	386	1480	500	32	0	256.3	27.51	0	280	311	735	1760	t	t
\.


--
-- Data for Name: pump_speeds; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.pump_speeds (id, pump_id, sequence_order, speed_value) FROM stdin;
1	1	1	700
2	1	2	900
3	1	3	1200
4	1	4	1450
5	1	5	1750
6	1	6	2100
7	1	7	0
8	1	8	0
9	2	1	2100
10	2	2	2300
11	2	3	2600
12	2	4	2900
13	2	5	3200
14	2	6	3450
15	2	7	0
16	2	8	0
17	3	1	0
18	3	2	0
19	3	3	0
20	3	4	0
21	3	5	0
22	3	6	0
23	3	7	0
24	3	8	0
25	4	1	700
26	4	2	900
27	4	3	1200
28	4	4	1450
29	4	5	1750
30	4	6	2100
31	4	7	0
32	4	8	0
33	5	1	2100
34	5	2	2300
35	5	3	2600
36	5	4	2900
37	5	5	3200
38	5	6	3450
39	5	7	0
40	5	8	0
41	6	1	700
42	6	2	900
43	6	3	1200
44	6	4	1450
45	6	5	1750
46	6	6	2100
47	6	7	0
48	6	8	0
49	7	1	700
50	7	2	900
51	7	3	1200
52	7	4	1450
53	7	5	1750
54	7	6	2100
55	7	7	0
56	7	8	0
57	8	1	0
58	8	2	0
59	8	3	0
60	8	4	0
61	8	5	0
62	8	6	0
63	8	7	0
64	8	8	0
65	9	1	1150
66	9	2	1250
67	9	3	1350
68	9	4	1450
69	9	5	1550
70	9	6	1650
71	9	7	1750
72	9	8	1800
73	10	1	1480
74	10	2	1480
75	10	3	1480
76	10	4	1480
77	10	5	0
78	10	6	0
79	10	7	0
80	10	8	0
81	11	1	0
82	11	2	0
83	11	3	0
84	11	4	0
85	11	5	0
86	11	6	0
87	11	7	0
88	11	8	0
89	12	1	0
90	12	2	0
91	12	3	0
92	12	4	0
93	12	5	0
94	12	6	0
95	12	7	0
96	12	8	0
97	13	1	0
98	13	2	0
99	13	3	0
100	13	4	0
101	13	5	0
102	13	6	0
103	13	7	0
104	13	8	0
105	14	1	0
106	14	2	0
107	14	3	0
108	14	4	0
109	14	5	0
110	14	6	0
111	14	7	0
112	14	8	0
113	15	1	0
114	15	2	0
115	15	3	0
116	15	4	0
117	15	5	0
118	15	6	0
119	15	7	0
120	15	8	0
121	16	1	0
122	16	2	0
123	16	3	0
124	16	4	0
125	16	5	0
126	16	6	0
127	16	7	0
128	16	8	0
129	17	1	0
130	17	2	0
131	17	3	0
132	17	4	0
133	17	5	0
134	17	6	0
135	17	7	0
136	17	8	0
137	18	1	0
138	18	2	0
139	18	3	0
140	18	4	0
141	18	5	0
142	18	6	0
143	18	7	0
144	18	8	0
145	19	1	0
146	19	2	0
147	19	3	0
148	19	4	0
149	19	5	0
150	19	6	0
151	19	7	0
152	19	8	0
153	20	1	2250
154	20	2	2650
155	20	3	3000
156	20	4	3300
157	20	5	3500
158	20	6	0
159	20	7	0
160	20	8	0
161	21	1	900
162	21	2	1100
163	21	3	1300
164	21	4	1500
165	21	5	1700
166	21	6	1900
167	21	7	0
168	21	8	0
169	22	1	0
170	22	2	0
171	22	3	0
172	22	4	0
173	22	5	0
174	22	6	0
175	22	7	0
176	22	8	0
177	23	1	0
178	23	2	0
179	23	3	0
180	23	4	0
181	23	5	0
182	23	6	0
183	23	7	0
184	23	8	0
185	24	1	450
186	24	2	500
187	24	3	550
188	24	4	600
189	24	5	0
190	24	6	0
191	24	7	0
192	24	8	0
193	25	1	0
194	25	2	0
195	25	3	0
196	25	4	0
197	25	5	0
198	25	6	0
199	25	7	0
200	25	8	0
201	26	1	1150
202	26	2	1200
203	26	3	1300
204	26	4	1400
205	26	5	1500
206	26	6	1600
207	26	7	1700
208	26	8	1800
209	27	1	700
210	27	2	900
211	27	3	1200
212	27	4	1450
213	27	5	1750
214	27	6	2100
215	27	7	0
216	27	8	0
217	28	1	700
218	28	2	900
219	28	3	1200
220	28	4	1450
221	28	5	1750
222	28	6	2100
223	28	7	0
224	28	8	0
225	29	1	700
226	29	2	900
227	29	3	1200
228	29	4	1450
229	29	5	1750
230	29	6	2100
231	29	7	0
232	29	8	0
233	30	1	600
234	30	2	700
235	30	3	800
236	30	4	900
237	30	5	1000
238	30	6	1100
239	30	7	1200
240	30	8	0
241	31	1	0
242	31	2	0
243	31	3	0
244	31	4	0
245	31	5	0
246	31	6	0
247	31	7	0
248	31	8	0
249	32	1	0
250	32	2	0
251	32	3	0
252	32	4	0
253	32	5	0
254	32	6	0
255	32	7	0
256	32	8	0
257	33	1	0
258	33	2	0
259	33	3	0
260	33	4	0
261	33	5	0
262	33	6	0
263	33	7	0
264	33	8	0
265	34	1	0
266	34	2	0
267	34	3	0
268	34	4	0
269	34	5	0
270	34	6	0
271	34	7	0
272	34	8	0
273	35	1	0
274	35	2	0
275	35	3	0
276	35	4	0
277	35	5	0
278	35	6	0
279	35	7	0
280	35	8	0
281	36	1	0
282	36	2	0
283	36	3	0
284	36	4	0
285	36	5	0
286	36	6	0
287	36	7	0
288	36	8	0
289	37	1	900
290	37	2	1012
291	37	3	1124
292	37	4	1236
293	37	5	1348
294	37	6	1460
295	37	7	0
296	37	8	0
297	38	1	900
298	38	2	1016
299	38	3	1132
300	38	4	1248
301	38	5	1364
302	38	6	1480
303	38	7	0
304	38	8	0
305	39	1	900
306	39	2	1012
307	39	3	1124
308	39	4	1236
309	39	5	1348
310	39	6	1460
311	39	7	0
312	39	8	0
313	40	1	1340
314	40	2	1660
315	40	3	1980
316	40	4	2300
317	40	5	0
318	40	6	0
319	40	7	0
320	40	8	0
321	41	1	0
322	41	2	0
323	41	3	0
324	41	4	0
325	41	5	0
326	41	6	0
327	41	7	0
328	41	8	0
329	42	1	0
330	42	2	0
331	42	3	0
332	42	4	0
333	42	5	0
334	42	6	0
335	42	7	0
336	42	8	0
337	43	1	0
338	43	2	0
339	43	3	0
340	43	4	0
341	43	5	0
342	43	6	0
343	43	7	0
344	43	8	0
345	44	1	0
346	44	2	0
347	44	3	0
348	44	4	0
349	44	5	0
350	44	6	0
351	44	7	0
352	44	8	0
353	45	1	0
354	45	2	0
355	45	3	0
356	45	4	0
357	45	5	0
358	45	6	0
359	45	7	0
360	45	8	0
361	46	1	0
362	46	2	0
363	46	3	0
364	46	4	0
365	46	5	0
366	46	6	0
367	46	7	0
368	46	8	0
369	47	1	0
370	47	2	0
371	47	3	0
372	47	4	0
373	47	5	0
374	47	6	0
375	47	7	0
376	47	8	0
377	48	1	0
378	48	2	0
379	48	3	0
380	48	4	0
381	48	5	0
382	48	6	0
383	48	7	0
384	48	8	0
385	49	1	0
386	49	2	0
387	49	3	0
388	49	4	0
389	49	5	0
390	49	6	0
391	49	7	0
392	49	8	0
393	50	1	0
394	50	2	0
395	50	3	0
396	50	4	0
397	50	5	0
398	50	6	0
399	50	7	0
400	50	8	0
401	51	1	0
402	51	2	0
403	51	3	0
404	51	4	0
405	51	5	0
406	51	6	0
407	51	7	0
408	51	8	0
409	52	1	0
410	52	2	0
411	52	3	0
412	52	4	0
413	52	5	0
414	52	6	0
415	52	7	0
416	52	8	0
417	53	1	0
418	53	2	0
419	53	3	0
420	53	4	0
421	53	5	0
422	53	6	0
423	53	7	0
424	53	8	0
425	54	1	0
426	54	2	0
427	54	3	0
428	54	4	0
429	54	5	0
430	54	6	0
431	54	7	0
432	54	8	0
433	55	1	0
434	55	2	0
435	55	3	0
436	55	4	0
437	55	5	0
438	55	6	0
439	55	7	0
440	55	8	0
441	56	1	900
442	56	2	1000
443	56	3	1100
444	56	4	1200
445	56	5	1325
446	56	6	1460
447	56	7	0
448	56	8	0
449	57	1	900
450	57	2	1000
451	57	3	1100
452	57	4	1200
453	57	5	1325
454	57	6	1460
455	57	7	0
456	57	8	0
457	58	1	900
458	58	2	1000
459	58	3	1100
460	58	4	1200
461	58	5	1325
462	58	6	1450
463	58	7	0
464	58	8	0
465	59	1	900
466	59	2	1000
467	59	3	1100
468	59	4	1200
469	59	5	1350
470	59	6	1460
471	59	7	0
472	59	8	0
473	60	1	900
474	60	2	1012
475	60	3	1124
476	60	4	1236
477	60	5	1348
478	60	6	1460
479	60	7	0
480	60	8	0
481	61	1	900
482	61	2	1012
483	61	3	1124
484	61	4	1236
485	61	5	1348
486	61	6	1460
487	61	7	0
488	61	8	0
489	62	1	0
490	62	2	0
491	62	3	0
492	62	4	0
493	62	5	0
494	62	6	0
495	62	7	0
496	62	8	0
497	63	1	1150
498	63	2	1200
499	63	3	1300
500	63	4	1400
501	63	5	1500
502	63	6	1600
503	63	7	1700
504	63	8	1800
505	64	1	0
506	64	2	0
507	64	3	0
508	64	4	0
509	64	5	0
510	64	6	0
511	64	7	0
512	64	8	0
513	65	1	1150
514	65	2	1300
515	65	3	1400
516	65	4	1500
517	65	5	1600
518	65	6	1700
519	65	7	1800
520	65	8	0
521	66	1	0
522	66	2	0
523	66	3	0
524	66	4	0
525	66	5	0
526	66	6	0
527	66	7	0
528	66	8	0
529	67	1	0
530	67	2	0
531	67	3	0
532	67	4	0
533	67	5	0
534	67	6	0
535	67	7	0
536	67	8	0
537	68	1	700
538	68	2	900
539	68	3	1200
540	68	4	1450
541	68	5	1750
542	68	6	2100
543	68	7	0
544	68	8	0
545	69	1	700
546	69	2	900
547	69	3	1200
548	69	4	1450
549	69	5	1750
550	69	6	2100
551	69	7	0
552	69	8	0
553	70	1	700
554	70	2	900
555	70	3	1200
556	70	4	1450
557	70	5	1750
558	70	6	2100
559	70	7	0
560	70	8	0
561	71	1	700
562	71	2	900
563	71	3	1200
564	71	4	1450
565	71	5	1750
566	71	6	2100
567	71	7	0
568	71	8	0
569	72	1	900
570	72	2	1050
571	72	3	1200
572	72	4	1350
573	72	5	1460
574	72	6	0
575	72	7	0
576	72	8	0
577	73	1	700
578	73	2	752
579	73	3	804
580	73	4	856
581	73	5	908
582	73	6	960
583	73	7	0
584	73	8	0
585	74	1	900
586	74	2	1050
587	74	3	1200
588	74	4	1350
589	74	5	1460
590	74	6	0
591	74	7	0
592	74	8	0
593	75	1	700
594	75	2	780
595	75	3	860
596	75	4	960
597	75	5	0
598	75	6	0
599	75	7	0
600	75	8	0
601	76	1	0
602	76	2	0
603	76	3	0
604	76	4	0
605	76	5	0
606	76	6	0
607	76	7	0
608	76	8	0
609	77	1	0
610	77	2	0
611	77	3	0
612	77	4	0
613	77	5	0
614	77	6	0
615	77	7	0
616	77	8	0
617	78	1	750
618	78	2	900
619	78	3	1100
620	78	4	1300
621	78	5	1450
622	78	6	0
623	78	7	0
624	78	8	0
625	79	1	0
626	79	2	0
627	79	3	0
628	79	4	0
629	79	5	0
630	79	6	0
631	79	7	0
632	79	8	0
633	80	1	0
634	80	2	0
635	80	3	0
636	80	4	0
637	80	5	0
638	80	6	0
639	80	7	0
640	80	8	0
641	81	1	0
642	81	2	0
643	81	3	0
644	81	4	0
645	81	5	0
646	81	6	0
647	81	7	0
648	81	8	0
649	82	1	1200
650	82	2	1300
651	82	3	1400
652	82	4	1500
653	82	5	1600
654	82	6	0
655	82	7	0
656	82	8	0
657	83	1	1200
658	83	2	1300
659	83	3	1400
660	83	4	1500
661	83	5	1600
662	83	6	1700
663	83	7	0
664	83	8	0
665	84	1	700
666	84	2	752
667	84	3	804
668	84	4	856
669	84	5	908
670	84	6	960
671	84	7	0
672	84	8	0
673	85	1	750
674	85	2	940
675	85	3	1130
676	85	4	1320
677	85	5	1510
678	85	6	1700
679	85	7	0
680	85	8	0
681	86	1	1200
682	86	2	1300
683	86	3	1400
684	86	4	1500
685	86	5	15800
686	86	6	0
687	86	7	0
688	86	8	0
689	87	1	750
690	87	2	1000
691	87	3	1250
692	87	4	1480
693	87	5	0
694	87	6	0
695	87	7	0
696	87	8	0
697	88	1	700
698	88	2	752
699	88	3	804
700	88	4	856
701	88	5	908
702	88	6	960
703	88	7	0
704	88	8	0
705	89	1	0
706	89	2	0
707	89	3	0
708	89	4	0
709	89	5	0
710	89	6	0
711	89	7	0
712	89	8	0
713	90	1	900
714	90	2	1080
715	90	3	1260
716	90	4	1440
717	90	5	1620
718	90	6	1800
719	90	7	0
720	90	8	0
721	91	1	700
722	91	2	754
723	91	3	808
724	91	4	862
725	91	5	916
726	91	6	970
727	91	7	0
728	91	8	0
729	92	1	900
730	92	2	1100
731	92	3	1300
732	92	4	1500
733	92	5	1800
734	92	6	0
735	92	7	0
736	92	8	0
737	93	1	700
738	93	2	750
739	93	3	800
740	93	4	850
741	93	5	900
742	93	6	980
743	93	7	0
744	93	8	0
745	94	1	970
746	94	2	1160
747	94	3	1450
748	94	4	1750
749	94	5	0
750	94	6	0
751	94	7	0
752	94	8	0
753	95	1	2000
754	95	2	2360
755	95	3	2650
756	95	4	2950
757	95	5	0
758	95	6	0
759	95	7	0
760	95	8	0
761	96	1	295
762	96	2	295
763	96	3	295
764	96	4	0
765	96	5	0
766	96	6	0
767	96	7	0
768	96	8	0
769	97	1	1150
770	97	2	1300
771	97	3	1400
772	97	4	1500
773	97	5	1600
774	97	6	1700
775	97	7	1800
776	97	8	0
777	98	1	700
778	98	2	800
779	98	3	900
780	98	4	1000
781	98	5	1150
782	98	6	0
783	98	7	0
784	98	8	0
785	99	1	1150
786	99	2	1300
787	99	3	1400
788	99	4	1500
789	99	5	1600
790	99	6	1700
791	99	7	1800
792	99	8	0
793	100	1	700
794	100	2	800
795	100	3	900
796	100	4	1000
797	100	5	1150
798	100	6	0
799	100	7	0
800	100	8	0
801	101	1	700
802	101	2	800
803	101	3	900
804	101	4	1000
805	101	5	1100
806	101	6	1150
807	101	7	0
808	101	8	0
809	102	1	1150
810	102	2	1300
811	102	3	1400
812	102	4	1500
813	102	5	1600
814	102	6	1700
815	102	7	1800
816	102	8	0
817	103	1	1150
818	103	2	1300
819	103	3	1400
820	103	4	1500
821	103	5	1600
822	103	6	1700
823	103	7	1800
824	103	8	0
825	104	1	700
826	104	2	800
827	104	3	900
828	104	4	1000
829	104	5	1100
830	104	6	1150
831	104	7	0
832	104	8	0
833	105	1	1150
834	105	2	1300
835	105	3	1400
836	105	4	1500
837	105	5	1600
838	105	6	1700
839	105	7	1800
840	105	8	0
841	106	1	700
842	106	2	800
843	106	3	900
844	106	4	1000
845	106	5	1100
846	106	6	1150
847	106	7	0
848	106	8	0
849	107	1	1150
850	107	2	1300
851	107	3	1400
852	107	4	1500
853	107	5	1600
854	107	6	1700
855	107	7	1800
856	107	8	0
857	108	1	700
858	108	2	800
859	108	3	900
860	108	4	1000
861	108	5	1100
862	108	6	1150
863	108	7	0
864	108	8	0
865	109	1	1150
866	109	2	1300
867	109	3	1400
868	109	4	1500
869	109	5	1600
870	109	6	1700
871	109	7	1800
872	109	8	0
873	110	1	700
874	110	2	800
875	110	3	900
876	110	4	1000
877	110	5	1100
878	110	6	1150
879	110	7	0
880	110	8	0
881	111	1	1150
882	111	2	1300
883	111	3	1400
884	111	4	1500
885	111	5	1600
886	111	6	1700
887	111	7	1800
888	111	8	0
889	112	1	1150
890	112	2	1300
891	112	3	1400
892	112	4	1500
893	112	5	1600
894	112	6	1700
895	112	7	1800
896	112	8	0
897	113	1	700
898	113	2	800
899	113	3	900
900	113	4	1000
901	113	5	1100
902	113	6	1150
903	113	7	0
904	113	8	0
905	114	1	1150
906	114	2	1300
907	114	3	1400
908	114	4	1500
909	114	5	1600
910	114	6	1700
911	114	7	1800
912	114	8	0
913	115	1	0
914	115	2	0
915	115	3	0
916	115	4	0
917	115	5	0
918	115	6	0
919	115	7	0
920	115	8	0
921	116	1	700
922	116	2	800
923	116	3	900
924	116	4	980
925	116	5	0
926	116	6	0
927	116	7	0
928	116	8	0
929	117	1	600
930	117	2	700
931	117	3	800
932	117	4	900
933	117	5	980
934	117	6	0
935	117	7	0
936	117	8	0
937	118	1	980
938	118	2	980
939	118	3	980
940	118	4	980
941	118	5	0
942	118	6	0
943	118	7	0
944	118	8	0
945	119	1	700
946	119	2	800
947	119	3	900
948	119	4	1000
949	119	5	0
950	119	6	0
951	119	7	0
952	119	8	0
953	120	1	0
954	120	2	0
955	120	3	0
956	120	4	0
957	120	5	0
958	120	6	0
959	120	7	0
960	120	8	0
961	121	1	0
962	121	2	0
963	121	3	0
964	121	4	0
965	121	5	0
966	121	6	0
967	121	7	0
968	121	8	0
969	122	1	0
970	122	2	0
971	122	3	0
972	122	4	0
973	122	5	0
974	122	6	0
975	122	7	0
976	122	8	0
977	123	1	0
978	123	2	0
979	123	3	0
980	123	4	0
981	123	5	0
982	123	6	0
983	123	7	0
984	123	8	0
985	124	1	0
986	124	2	0
987	124	3	0
988	124	4	0
989	124	5	0
990	124	6	0
991	124	7	0
992	124	8	0
993	125	1	0
994	125	2	0
995	125	3	0
996	125	4	0
997	125	5	0
998	125	6	0
999	125	7	0
1000	125	8	0
1001	126	1	0
1002	126	2	0
1003	126	3	0
1004	126	4	0
1005	126	5	0
1006	126	6	0
1007	126	7	0
1008	126	8	0
1009	127	1	0
1010	127	2	0
1011	127	3	0
1012	127	4	0
1013	127	5	0
1014	127	6	0
1015	127	7	0
1016	127	8	0
1017	128	1	0
1018	128	2	0
1019	128	3	0
1020	128	4	0
1021	128	5	0
1022	128	6	0
1023	128	7	0
1024	128	8	0
1025	129	1	0
1026	129	2	0
1027	129	3	0
1028	129	4	0
1029	129	5	0
1030	129	6	0
1031	129	7	0
1032	129	8	0
1033	130	1	0
1034	130	2	0
1035	130	3	0
1036	130	4	0
1037	130	5	0
1038	130	6	0
1039	130	7	0
1040	130	8	0
1041	131	1	0
1042	131	2	0
1043	131	3	0
1044	131	4	0
1045	131	5	0
1046	131	6	0
1047	131	7	0
1048	131	8	0
1049	132	1	1150
1050	132	2	1300
1051	132	3	1400
1052	132	4	1500
1053	132	5	1600
1054	132	6	1700
1055	132	7	1800
1056	132	8	0
1057	133	1	700
1058	133	2	800
1059	133	3	900
1060	133	4	1000
1061	133	5	1100
1062	133	6	1150
1063	133	7	0
1064	133	8	0
1065	134	1	1150
1066	134	2	1300
1067	134	3	1400
1068	134	4	1500
1069	134	5	1600
1070	134	6	1700
1071	134	7	1800
1072	134	8	0
1073	135	1	700
1074	135	2	800
1075	135	3	900
1076	135	4	1000
1077	135	5	1100
1078	135	6	1150
1079	135	7	0
1080	135	8	0
1081	136	1	1150
1082	136	2	1300
1083	136	3	1400
1084	136	4	1500
1085	136	5	1600
1086	136	6	1700
1087	136	7	1800
1088	136	8	0
1089	137	1	700
1090	137	2	800
1091	137	3	900
1092	137	4	1000
1093	137	5	1100
1094	137	6	1150
1095	137	7	0
1096	137	8	0
1097	138	1	1150
1098	138	2	1300
1099	138	3	1400
1100	138	4	1500
1101	138	5	1600
1102	138	6	1700
1103	138	7	1800
1104	138	8	0
1105	139	1	700
1106	139	2	800
1107	139	3	900
1108	139	4	1000
1109	139	5	1100
1110	139	6	1150
1111	139	7	0
1112	139	8	0
1113	140	1	1150
1114	140	2	1300
1115	140	3	1400
1116	140	4	1500
1117	140	5	1600
1118	140	6	1700
1119	140	7	1800
1120	140	8	0
1121	141	1	700
1122	141	2	800
1123	141	3	900
1124	141	4	1000
1125	141	5	1100
1126	141	6	1150
1127	141	7	0
1128	141	8	0
1129	142	1	1150
1130	142	2	1300
1131	142	3	1400
1132	142	4	1500
1133	142	5	1600
1134	142	6	1700
1135	142	7	1800
1136	142	8	0
1137	143	1	700
1138	143	2	800
1139	143	3	900
1140	143	4	1000
1141	143	5	1100
1142	143	6	1150
1143	143	7	0
1144	143	8	0
1145	144	1	1150
1146	144	2	1300
1147	144	3	1400
1148	144	4	1500
1149	144	5	1600
1150	144	6	1700
1151	144	7	1800
1152	144	8	0
1153	145	1	0
1154	145	2	0
1155	145	3	0
1156	145	4	0
1157	145	5	0
1158	145	6	0
1159	145	7	0
1160	145	8	0
1161	146	1	1150
1162	146	2	1300
1163	146	3	1400
1164	146	4	1500
1165	146	5	1600
1166	146	6	1700
1167	146	7	1800
1168	146	8	0
1169	147	1	700
1170	147	2	800
1171	147	3	900
1172	147	4	1000
1173	147	5	1150
1174	147	6	0
1175	147	7	0
1176	147	8	0
1177	148	1	1480
1178	148	2	1480
1179	148	3	1480
1180	148	4	1480
1181	148	5	0
1182	148	6	0
1183	148	7	0
1184	148	8	0
1185	149	1	1488
1186	149	2	0
1187	149	3	0
1188	149	4	0
1189	149	5	0
1190	149	6	0
1191	149	7	0
1192	149	8	0
1193	150	1	0
1194	150	2	0
1195	150	3	0
1196	150	4	0
1197	150	5	0
1198	150	6	0
1199	150	7	0
1200	150	8	0
1201	151	1	500
1202	151	2	547
1203	151	3	594
1204	151	4	641
1205	151	5	688
1206	151	6	735
1207	151	7	0
1208	151	8	0
1209	152	1	0
1210	152	2	0
1211	152	3	0
1212	152	4	0
1213	152	5	0
1214	152	6	0
1215	152	7	0
1216	152	8	0
1217	153	1	0
1218	153	2	0
1219	153	3	0
1220	153	4	0
1221	153	5	0
1222	153	6	0
1223	153	7	0
1224	153	8	0
1225	154	1	0
1226	154	2	0
1227	154	3	0
1228	154	4	0
1229	154	5	0
1230	154	6	0
1231	154	7	0
1232	154	8	0
1233	155	1	0
1234	155	2	0
1235	155	3	0
1236	155	4	0
1237	155	5	0
1238	155	6	0
1239	155	7	0
1240	155	8	0
1241	156	1	0
1242	156	2	0
1243	156	3	0
1244	156	4	0
1245	156	5	0
1246	156	6	0
1247	156	7	0
1248	156	8	0
1249	157	1	700
1250	157	2	790
1251	157	3	880
1252	157	4	970
1253	157	5	1060
1254	157	6	1100
1255	157	7	0
1256	157	8	0
1257	158	1	0
1258	158	2	0
1259	158	3	0
1260	158	4	0
1261	158	5	0
1262	158	6	0
1263	158	7	0
1264	158	8	0
1265	159	1	0
1266	159	2	0
1267	159	3	0
1268	159	4	0
1269	159	5	0
1270	159	6	0
1271	159	7	0
1272	159	8	0
1273	160	1	700
1274	160	2	900
1275	160	3	1200
1276	160	4	1450
1277	160	5	1750
1278	160	6	2100
1279	160	7	0
1280	160	8	0
1281	161	1	2100
1282	161	2	2300
1283	161	3	2600
1284	161	4	2900
1285	161	5	3200
1286	161	6	3450
1287	161	7	0
1288	161	8	0
1289	162	1	700
1290	162	2	790
1291	162	3	880
1292	162	4	970
1293	162	5	1060
1294	162	6	1150
1295	162	7	0
1296	162	8	0
1297	163	1	500
1298	163	2	550
1299	163	3	650
1300	163	4	725
1301	163	5	800
1302	163	6	0
1303	163	7	0
1304	163	8	0
1305	164	1	700
1306	164	2	745
1307	164	3	808
1308	164	4	862
1309	164	5	916
1310	164	6	990
1311	164	7	0
1312	164	8	0
1313	165	1	500
1314	165	2	590
1315	165	3	640
1316	165	4	725
1317	165	5	825
1318	165	6	900
1319	165	7	0
1320	165	8	0
1321	166	1	0
1322	166	2	0
1323	166	3	0
1324	166	4	0
1325	166	5	0
1326	166	6	0
1327	166	7	0
1328	166	8	0
1329	167	1	750
1330	167	2	840
1331	167	3	930
1332	167	4	1020
1333	167	5	1110
1334	167	6	1200
1335	167	7	0
1336	167	8	0
1337	168	1	500
1338	168	2	600
1339	168	3	700
1340	168	4	800
1341	168	5	900
1342	168	6	0
1343	168	7	0
1344	168	8	0
1345	169	1	0
1346	169	2	0
1347	169	3	0
1348	169	4	0
1349	169	5	0
1350	169	6	0
1351	169	7	0
1352	169	8	0
1353	170	1	1465
1354	170	2	1465
1355	170	3	1465
1356	170	4	1465
1357	170	5	1465
1358	170	6	0
1359	170	7	0
1360	170	8	0
1361	171	1	0
1362	171	2	0
1363	171	3	0
1364	171	4	0
1365	171	5	0
1366	171	6	0
1367	171	7	0
1368	171	8	0
1369	172	1	0
1370	172	2	0
1371	172	3	0
1372	172	4	0
1373	172	5	0
1374	172	6	0
1375	172	7	0
1376	172	8	0
1377	173	1	1450
1378	173	2	1750
1379	173	3	2050
1380	173	4	2350
1381	173	5	2650
1382	173	6	2950
1383	173	7	0
1384	173	8	0
1385	174	1	1450
1386	174	2	1450
1387	174	3	1450
1388	174	4	1450
1389	174	5	0
1390	174	6	0
1391	174	7	0
1392	174	8	0
1393	175	1	0
1394	175	2	0
1395	175	3	0
1396	175	4	0
1397	175	5	0
1398	175	6	0
1399	175	7	0
1400	175	8	0
1401	176	1	0
1402	176	2	0
1403	176	3	0
1404	176	4	0
1405	176	5	0
1406	176	6	0
1407	176	7	0
1408	176	8	0
1409	177	1	0
1410	177	2	0
1411	177	3	0
1412	177	4	0
1413	177	5	0
1414	177	6	0
1415	177	7	0
1416	177	8	0
1417	178	1	0
1418	178	2	0
1419	178	3	0
1420	178	4	0
1421	178	5	0
1422	178	6	0
1423	178	7	0
1424	178	8	0
1425	179	1	0
1426	179	2	0
1427	179	3	0
1428	179	4	0
1429	179	5	0
1430	179	6	0
1431	179	7	0
1432	179	8	0
1433	180	1	0
1434	180	2	0
1435	180	3	0
1436	180	4	0
1437	180	5	0
1438	180	6	0
1439	180	7	0
1440	180	8	0
1441	181	1	0
1442	181	2	0
1443	181	3	0
1444	181	4	0
1445	181	5	0
1446	181	6	0
1447	181	7	0
1448	181	8	0
1449	182	1	0
1450	182	2	0
1451	182	3	0
1452	182	4	0
1453	182	5	0
1454	182	6	0
1455	182	7	0
1456	182	8	0
1457	183	1	0
1458	183	2	0
1459	183	3	0
1460	183	4	0
1461	183	5	0
1462	183	6	0
1463	183	7	0
1464	183	8	0
1465	184	1	0
1466	184	2	0
1467	184	3	0
1468	184	4	0
1469	184	5	0
1470	184	6	0
1471	184	7	0
1472	184	8	0
1473	185	1	0
1474	185	2	0
1475	185	3	0
1476	185	4	0
1477	185	5	0
1478	185	6	0
1479	185	7	0
1480	185	8	0
1481	186	1	0
1482	186	2	0
1483	186	3	0
1484	186	4	0
1485	186	5	0
1486	186	6	0
1487	186	7	0
1488	186	8	0
1489	187	1	0
1490	187	2	0
1491	187	3	0
1492	187	4	0
1493	187	5	0
1494	187	6	0
1495	187	7	0
1496	187	8	0
1497	188	1	0
1498	188	2	0
1499	188	3	0
1500	188	4	0
1501	188	5	0
1502	188	6	0
1503	188	7	0
1504	188	8	0
1505	189	1	0
1506	189	2	0
1507	189	3	0
1508	189	4	0
1509	189	5	0
1510	189	6	0
1511	189	7	0
1512	189	8	0
1513	190	1	0
1514	190	2	0
1515	190	3	0
1516	190	4	0
1517	190	5	0
1518	190	6	0
1519	190	7	0
1520	190	8	0
1521	191	1	0
1522	191	2	0
1523	191	3	0
1524	191	4	0
1525	191	5	0
1526	191	6	0
1527	191	7	0
1528	191	8	0
1529	192	1	1465
1530	192	2	1465
1531	192	3	1465
1532	192	4	1465
1533	192	5	1465
1534	192	6	0
1535	192	7	0
1536	192	8	0
1537	193	1	0
1538	193	2	0
1539	193	3	0
1540	193	4	0
1541	193	5	0
1542	193	6	0
1543	193	7	0
1544	193	8	0
1545	194	1	1430
1546	194	2	1730
1547	194	3	2030
1548	194	4	2330
1549	194	5	2630
1550	194	6	2930
1551	194	7	0
1552	194	8	0
1553	195	1	1450
1554	195	2	1746
1555	195	3	2042
1556	195	4	2338
1557	195	5	2634
1558	195	6	2930
1559	195	7	0
1560	195	8	0
1561	196	1	1450
1562	196	2	1746
1563	196	3	2042
1564	196	4	2338
1565	196	5	2634
1566	196	6	2930
1567	196	7	0
1568	196	8	0
1569	197	1	1465
1570	197	2	1465
1571	197	3	1465
1572	197	4	1465
1573	197	5	1465
1574	197	6	0
1575	197	7	0
1576	197	8	0
1577	198	1	0
1578	198	2	0
1579	198	3	0
1580	198	4	0
1581	198	5	0
1582	198	6	0
1583	198	7	0
1584	198	8	0
1585	199	1	2950
1586	199	2	2950
1587	199	3	2950
1588	199	4	0
1589	199	5	0
1590	199	6	0
1591	199	7	0
1592	199	8	0
1593	200	1	2350
1594	200	2	2450
1595	200	3	2550
1596	200	4	2650
1597	200	5	2750
1598	200	6	2850
1599	200	7	2950
1600	200	8	0
1601	201	1	2950
1602	201	2	2950
1603	201	3	2950
1604	201	4	0
1605	201	5	0
1606	201	6	0
1607	201	7	0
1608	201	8	0
1609	202	1	700
1610	202	2	900
1611	202	3	1200
1612	202	4	1450
1613	202	5	1750
1614	202	6	2100
1615	202	7	0
1616	202	8	0
1617	203	1	2100
1618	203	2	2300
1619	203	3	2600
1620	203	4	2900
1621	203	5	3200
1622	203	6	3450
1623	203	7	0
1624	203	8	0
1625	204	1	700
1626	204	2	900
1627	204	3	1200
1628	204	4	1450
1629	204	5	1750
1630	204	6	2100
1631	204	7	0
1632	204	8	0
1633	205	1	2100
1634	205	2	2300
1635	205	3	2600
1636	205	4	2900
1637	205	5	3200
1638	205	6	3450
1639	205	7	0
1640	205	8	0
1641	206	1	700
1642	206	2	900
1643	206	3	1200
1644	206	4	1450
1645	206	5	1750
1646	206	6	2100
1647	206	7	0
1648	206	8	0
1649	207	1	2100
1650	207	2	2300
1651	207	3	2600
1652	207	4	2900
1653	207	5	3200
1654	207	6	3450
1655	207	7	0
1656	207	8	0
1657	208	1	700
1658	208	2	900
1659	208	3	1200
1660	208	4	1450
1661	208	5	1750
1662	208	6	2100
1663	208	7	0
1664	208	8	0
1665	209	1	0
1666	209	2	0
1667	209	3	0
1668	209	4	0
1669	209	5	0
1670	209	6	0
1671	209	7	0
1672	209	8	0
1673	210	1	0
1674	210	2	0
1675	210	3	0
1676	210	4	0
1677	210	5	0
1678	210	6	0
1679	210	7	0
1680	210	8	0
1681	211	1	0
1682	211	2	0
1683	211	3	0
1684	211	4	0
1685	211	5	0
1686	211	6	0
1687	211	7	0
1688	211	8	0
1689	212	1	0
1690	212	2	0
1691	212	3	0
1692	212	4	0
1693	212	5	0
1694	212	6	0
1695	212	7	0
1696	212	8	0
1697	213	1	0
1698	213	2	0
1699	213	3	0
1700	213	4	0
1701	213	5	0
1702	213	6	0
1703	213	7	0
1704	213	8	0
1705	214	1	0
1706	214	2	0
1707	214	3	0
1708	214	4	0
1709	214	5	0
1710	214	6	0
1711	214	7	0
1712	214	8	0
1713	215	1	0
1714	215	2	0
1715	215	3	0
1716	215	4	0
1717	215	5	0
1718	215	6	0
1719	215	7	0
1720	215	8	0
1721	216	1	0
1722	216	2	0
1723	216	3	0
1724	216	4	0
1725	216	5	0
1726	216	6	0
1727	216	7	0
1728	216	8	0
1729	217	1	1000
1730	217	2	1500
1731	217	3	2000
1732	217	4	2500
1733	217	5	3000
1734	217	6	0
1735	217	7	0
1736	217	8	0
1737	218	1	0
1738	218	2	0
1739	218	3	0
1740	218	4	0
1741	218	5	0
1742	218	6	0
1743	218	7	0
1744	218	8	0
1745	219	1	0
1746	219	2	0
1747	219	3	0
1748	219	4	0
1749	219	5	0
1750	219	6	0
1751	219	7	0
1752	219	8	0
1753	220	1	500
1754	220	2	980
1755	220	3	1460
1756	220	4	1940
1757	220	5	2420
1758	220	6	2900
1759	220	7	0
1760	220	8	0
1761	221	1	2100
1762	221	2	2300
1763	221	3	2600
1764	221	4	2900
1765	221	5	3200
1766	221	6	3450
1767	221	7	0
1768	221	8	0
1769	222	1	700
1770	222	2	900
1771	222	3	1200
1772	222	4	1450
1773	222	5	1750
1774	222	6	2100
1775	222	7	0
1776	222	8	0
1777	223	1	2100
1778	223	2	2300
1779	223	3	2600
1780	223	4	2900
1781	223	5	3200
1782	223	6	3450
1783	223	7	0
1784	223	8	0
1785	224	1	700
1786	224	2	900
1787	224	3	1200
1788	224	4	1450
1789	224	5	1750
1790	224	6	2100
1791	224	7	0
1792	224	8	0
1793	225	1	700
1794	225	2	900
1795	225	3	1200
1796	225	4	1450
1797	225	5	1750
1798	225	6	2100
1799	225	7	0
1800	225	8	0
1801	226	1	2100
1802	226	2	2300
1803	226	3	2600
1804	226	4	2900
1805	226	5	3200
1806	226	6	3450
1807	226	7	0
1808	226	8	0
1809	227	1	700
1810	227	2	900
1811	227	3	1200
1812	227	4	1450
1813	227	5	1750
1814	227	6	2100
1815	227	7	0
1816	227	8	0
1817	228	1	2100
1818	228	2	2300
1819	228	3	2600
1820	228	4	2900
1821	228	5	3200
1822	228	6	3450
1823	228	7	0
1824	228	8	0
1825	229	1	700
1826	229	2	900
1827	229	3	1200
1828	229	4	1450
1829	229	5	1750
1830	229	6	2100
1831	229	7	0
1832	229	8	0
1833	230	1	1450
1834	230	2	1535
1835	230	3	1620
1836	230	4	1705
1837	230	5	1800
1838	230	6	0
1839	230	7	0
1840	230	8	0
1841	231	1	0
1842	231	2	0
1843	231	3	0
1844	231	4	0
1845	231	5	0
1846	231	6	0
1847	231	7	0
1848	231	8	0
1849	232	1	0
1850	232	2	0
1851	232	3	0
1852	232	4	0
1853	232	5	0
1854	232	6	0
1855	232	7	0
1856	232	8	0
1857	233	1	0
1858	233	2	0
1859	233	3	0
1860	233	4	0
1861	233	5	0
1862	233	6	0
1863	233	7	0
1864	233	8	0
1865	234	1	0
1866	234	2	0
1867	234	3	0
1868	234	4	0
1869	234	5	0
1870	234	6	0
1871	234	7	0
1872	234	8	0
1873	235	1	0
1874	235	2	0
1875	235	3	0
1876	235	4	0
1877	235	5	0
1878	235	6	0
1879	235	7	0
1880	235	8	0
1881	236	1	2250
1882	236	2	2500
1883	236	3	2750
1884	236	4	2900
1885	236	5	0
1886	236	6	0
1887	236	7	0
1888	236	8	0
1889	237	1	1460
1890	237	2	1776
1891	237	3	2092
1892	237	4	2408
1893	237	5	2724
1894	237	6	2900
1895	237	7	0
1896	237	8	0
1897	238	1	1150
1898	238	2	1280
1899	238	3	1410
1900	238	4	1540
1901	238	5	1670
1902	238	6	1800
1903	238	7	0
1904	238	8	0
1905	240	1	2250
1906	240	2	2500
1907	240	3	2750
1908	240	4	2900
1909	240	5	0
1910	240	6	0
1911	240	7	0
1912	240	8	0
1913	241	1	2250
1914	241	2	2500
1915	241	3	2750
1916	241	4	2900
1917	241	5	0
1918	241	6	0
1919	241	7	0
1920	241	8	0
1921	242	1	2250
1922	242	2	2500
1923	242	3	2750
1924	242	4	3000
1925	242	5	3250
1926	242	6	3500
1927	242	7	0
1928	242	8	0
1929	243	1	0
1930	243	2	0
1931	243	3	0
1932	243	4	0
1933	243	5	0
1934	243	6	0
1935	243	7	0
1936	243	8	0
1937	244	1	0
1938	244	2	0
1939	244	3	0
1940	244	4	0
1941	244	5	0
1942	244	6	0
1943	244	7	0
1944	244	8	0
1945	245	1	2250
1946	245	2	2500
1947	245	3	2750
1948	245	4	2900
1949	245	5	0
1950	245	6	0
1951	245	7	0
1952	245	8	0
1953	246	1	2970
1954	246	2	2970
1955	246	3	2970
1956	246	4	0
1957	246	5	0
1958	246	6	0
1959	246	7	0
1960	246	8	0
1961	247	1	900
1962	247	2	1000
1963	247	3	1150
1964	247	4	1250
1965	247	5	1350
1966	247	6	1480
1967	247	7	0
1968	247	8	0
1969	248	1	750
1970	248	2	800
1971	248	3	850
1972	248	4	900
1973	248	5	950
1974	248	6	1000
1975	248	7	0
1976	248	8	0
1977	249	1	500
1978	249	2	650
1979	249	3	750
1980	249	4	850
1981	249	5	980
1982	249	6	0
1983	249	7	0
1984	249	8	0
1985	250	1	900
1986	250	2	1010
1987	250	3	1120
1988	250	4	1230
1989	250	5	1340
1990	250	6	1450
1991	250	7	0
1992	250	8	0
1993	251	1	2250
1994	251	2	2500
1995	251	3	2750
1996	251	4	2900
1997	251	5	0
1998	251	6	0
1999	251	7	0
2000	251	8	0
2001	252	1	700
2002	252	2	900
2003	252	3	1200
2004	252	4	1450
2005	252	5	1750
2006	252	6	2100
2007	252	7	0
2008	252	8	0
2009	253	1	2100
2010	253	2	2300
2011	253	3	2600
2012	253	4	2900
2013	253	5	3200
2014	253	6	3450
2015	253	7	0
2016	253	8	0
2017	254	1	700
2018	254	2	900
2019	254	3	1200
2020	254	4	1450
2021	254	5	1750
2022	254	6	2100
2023	254	7	0
2024	254	8	0
2025	255	1	2100
2026	255	2	2300
2027	255	3	2600
2028	255	4	2900
2029	255	5	3200
2030	255	6	3450
2031	255	7	0
2032	255	8	0
2033	256	1	700
2034	256	2	900
2035	256	3	1200
2036	256	4	1450
2037	256	5	1750
2038	256	6	2100
2039	256	7	0
2040	256	8	0
2041	257	1	2100
2042	257	2	2300
2043	257	3	2600
2044	257	4	2900
2045	257	5	3200
2046	257	6	3450
2047	257	7	0
2048	257	8	0
2049	258	1	700
2050	258	2	900
2051	258	3	1200
2052	258	4	1450
2053	258	5	1750
2054	258	6	2100
2055	258	7	0
2056	258	8	0
2057	259	1	1800
2058	259	2	2140
2059	259	3	2480
2060	259	4	2820
2061	259	5	3160
2062	259	6	3500
2063	259	7	0
2064	259	8	0
2065	260	1	1150
2066	260	2	1280
2067	260	3	1410
2068	260	4	1540
2069	260	5	1670
2070	260	6	1800
2071	260	7	0
2072	260	8	0
2073	261	1	400
2074	261	2	600
2075	261	3	800
2076	261	4	970
2077	261	5	0
2078	261	6	0
2079	261	7	0
2080	261	8	0
2081	262	1	0
2082	262	2	0
2083	262	3	0
2084	262	4	0
2085	262	5	0
2086	262	6	0
2087	262	7	0
2088	262	8	0
2089	263	1	400
2090	263	2	600
2091	263	3	800
2092	263	4	970
2093	263	5	1100
2094	263	6	1250
2095	263	7	0
2096	263	8	0
2097	264	1	400
2098	264	2	600
2099	264	3	800
2100	264	4	970
2101	264	5	1100
2102	264	6	1250
2103	264	7	0
2104	264	8	0
2105	265	1	400
2106	265	2	700
2107	265	3	970
2108	265	4	1250
2109	265	5	1500
2110	265	6	0
2111	265	7	0
2112	265	8	0
2113	266	1	400
2114	266	2	600
2115	266	3	800
2116	266	4	970
2117	266	5	1100
2118	266	6	1260
2119	266	7	0
2120	266	8	0
2121	267	1	400
2122	267	2	700
2123	267	3	970
2124	267	4	1200
2125	267	5	1420
2126	267	6	0
2127	267	7	0
2128	267	8	0
2129	268	1	400
2130	268	2	700
2131	268	3	970
2132	268	4	1250
2133	268	5	1500
2134	268	6	0
2135	268	7	0
2136	268	8	0
2137	269	1	400
2138	269	2	700
2139	269	3	970
2140	269	4	1250
2141	269	5	1500
2142	269	6	0
2143	269	7	0
2144	269	8	0
2145	270	1	900
2146	270	2	940
2147	270	3	980
2148	270	4	1020
2149	270	5	1060
2150	270	6	1100
2151	270	7	0
2152	270	8	0
2153	271	1	400
2154	271	2	600
2155	271	3	800
2156	271	4	950
2157	271	5	1090
2158	271	6	0
2159	271	7	0
2160	271	8	0
2161	272	1	400
2162	272	2	550
2163	272	3	750
2164	272	4	900
2165	272	5	1078
2166	272	6	0
2167	272	7	0
2168	272	8	0
2169	273	1	400
2170	273	2	600
2171	273	3	800
2172	273	4	980
2173	273	5	1208
2174	273	6	0
2175	273	7	0
2176	273	8	0
2177	274	1	400
2178	274	2	600
2179	274	3	800
2180	274	4	970
2181	274	5	1100
2182	274	6	1205
2183	274	7	0
2184	274	8	0
2185	275	1	400
2186	275	2	500
2187	275	3	625
2188	275	4	750
2189	275	5	855
2190	275	6	0
2191	275	7	0
2192	275	8	0
2193	276	1	400
2194	276	2	500
2195	276	3	625
2196	276	4	730
2197	276	5	843
2198	276	6	0
2199	276	7	0
2200	276	8	0
2201	277	1	620
2202	277	2	677
2203	277	3	734
2204	277	4	791
2205	277	5	850
2206	277	6	0
2207	277	7	0
2208	277	8	0
2209	278	1	400
2210	278	2	500
2211	278	3	625
2212	278	4	750
2213	278	5	855
2214	278	6	990
2215	278	7	0
2216	278	8	0
2217	279	1	400
2218	279	2	525
2219	279	3	650
2220	279	4	760
2221	279	5	0
2222	279	6	0
2223	279	7	0
2224	279	8	0
2225	280	1	450
2226	280	2	550
2227	280	3	650
2228	280	4	750
2229	280	5	0
2230	280	6	0
2231	280	7	0
2232	280	8	0
2233	281	1	450
2234	281	2	550
2235	281	3	650
2236	281	4	750
2237	281	5	880
2238	281	6	0
2239	281	7	0
2240	281	8	0
2241	282	1	450
2242	282	2	550
2243	282	3	650
2244	282	4	750
2245	282	5	880
2246	282	6	0
2247	282	7	0
2248	282	8	0
2249	283	1	400
2250	283	2	525
2251	283	3	600
2252	283	4	633
2253	283	5	0
2254	283	6	0
2255	283	7	0
2256	283	8	0
2257	284	1	400
2258	284	2	480
2259	284	3	560
2260	284	4	625
2261	284	5	0
2262	284	6	0
2263	284	7	0
2264	284	8	0
2265	285	1	400
2266	285	2	500
2267	285	3	600
2268	285	4	700
2269	285	5	0
2270	285	6	0
2271	285	7	0
2272	285	8	0
2273	286	1	430
2274	286	2	530
2275	286	3	630
2276	286	4	733
2277	286	5	0
2278	286	6	0
2279	286	7	0
2280	286	8	0
2281	287	1	400
2282	287	2	700
2283	287	3	900
2284	287	4	1100
2285	287	5	1300
2286	287	6	1450
2287	287	7	0
2288	287	8	0
2289	288	1	400
2290	288	2	500
2291	288	3	650
2292	288	4	765
2293	288	5	880
2294	288	6	0
2295	288	7	0
2296	288	8	0
2297	289	1	400
2298	289	2	600
2299	289	3	800
2300	289	4	970
2301	289	5	1100
2302	289	6	1250
2303	289	7	0
2304	289	8	0
2305	290	1	1480
2306	290	2	1480
2307	290	3	1480
2308	290	4	1480
2309	290	5	1480
2310	290	6	0
2311	290	7	0
2312	290	8	0
2313	291	1	1480
2314	291	2	1480
2315	291	3	1480
2316	291	4	1480
2317	291	5	1480
2318	291	6	0
2319	291	7	0
2320	291	8	0
2321	292	1	1480
2322	292	2	1480
2323	292	3	1480
2324	292	4	0
2325	292	5	0
2326	292	6	0
2327	292	7	0
2328	292	8	0
2329	293	1	0
2330	293	2	0
2331	293	3	0
2332	293	4	0
2333	293	5	0
2334	293	6	0
2335	293	7	0
2336	293	8	0
2337	294	1	1000
2338	294	2	1400
2339	294	3	1800
2340	294	4	2200
2341	294	5	2600
2342	294	6	3000
2343	294	7	0
2344	294	8	0
2345	295	1	1150
2346	295	2	1280
2347	295	3	1410
2348	295	4	1540
2349	295	5	1670
2350	295	6	1800
2351	295	7	0
2352	295	8	0
2353	296	1	750
2354	296	2	1040
2355	296	3	1330
2356	296	4	1620
2357	296	5	1800
2358	296	6	2000
2359	296	7	0
2360	296	8	0
2361	297	1	750
2362	297	2	1040
2363	297	3	1330
2364	297	4	1620
2365	297	5	1910
2366	297	6	2200
2367	297	7	0
2368	297	8	0
2369	298	1	1150
2370	298	2	1280
2371	298	3	1410
2372	298	4	1540
2373	298	5	1670
2374	298	6	1800
2375	298	7	0
2376	298	8	0
2377	299	1	1150
2378	299	2	1340
2379	299	3	1530
2380	299	4	1720
2381	299	5	1910
2382	299	6	2100
2383	299	7	0
2384	299	8	0
2385	300	1	0
2386	300	2	0
2387	300	3	0
2388	300	4	0
2389	300	5	0
2390	300	6	0
2391	300	7	0
2392	300	8	0
2393	301	1	0
2394	301	2	0
2395	301	3	0
2396	301	4	0
2397	301	5	0
2398	301	6	0
2399	301	7	0
2400	301	8	0
2401	302	1	2250
2402	302	2	2380
2403	302	3	2510
2404	302	4	2640
2405	302	5	2770
2406	302	6	2900
2407	302	7	0
2408	302	8	0
2409	303	1	0
2410	303	2	0
2411	303	3	0
2412	303	4	0
2413	303	5	0
2414	303	6	0
2415	303	7	0
2416	303	8	0
2417	305	1	2250
2418	305	2	2380
2419	305	3	2510
2420	305	4	2640
2421	305	5	2770
2422	305	6	2900
2423	305	7	0
2424	305	8	0
2425	306	1	2250
2426	306	2	2380
2427	306	3	2510
2428	306	4	2640
2429	306	5	2770
2430	306	6	2900
2431	306	7	0
2432	306	8	0
2433	307	1	2250
2434	307	2	2380
2435	307	3	2510
2436	307	4	2640
2437	307	5	2770
2438	307	6	2900
2439	307	7	0
2440	307	8	0
2441	308	1	0
2442	308	2	0
2443	308	3	0
2444	308	4	0
2445	308	5	0
2446	308	6	0
2447	308	7	0
2448	308	8	0
2449	309	1	0
2450	309	2	0
2451	309	3	0
2452	309	4	0
2453	309	5	0
2454	309	6	0
2455	309	7	0
2456	309	8	0
2457	310	1	0
2458	310	2	0
2459	310	3	0
2460	310	4	0
2461	310	5	0
2462	310	6	0
2463	310	7	0
2464	310	8	0
2465	311	1	0
2466	311	2	0
2467	311	3	0
2468	311	4	0
2469	311	5	0
2470	311	6	0
2471	311	7	0
2472	311	8	0
2473	312	1	2450
2474	312	2	2550
2475	312	3	2650
2476	312	4	2750
2477	312	5	2850
2478	312	6	2960
2479	312	7	0
2480	312	8	0
2481	313	1	0
2482	313	2	0
2483	313	3	0
2484	313	4	0
2485	313	5	0
2486	313	6	0
2487	313	7	0
2488	313	8	0
2489	314	1	2450
2490	314	2	2550
2491	314	3	2650
2492	314	4	2750
2493	314	5	2850
2494	314	6	2960
2495	314	7	0
2496	314	8	0
2497	315	1	0
2498	315	2	0
2499	315	3	0
2500	315	4	0
2501	315	5	0
2502	315	6	0
2503	315	7	0
2504	315	8	0
2505	316	1	2450
2506	316	2	2550
2507	316	3	2650
2508	316	4	2750
2509	316	5	2850
2510	316	6	2950
2511	316	7	0
2512	316	8	0
2513	317	1	2450
2514	317	2	2550
2515	317	3	2650
2516	317	4	2750
2517	317	5	2850
2518	317	6	2960
2519	317	7	0
2520	317	8	0
2521	318	1	0
2522	318	2	0
2523	318	3	0
2524	318	4	0
2525	318	5	0
2526	318	6	0
2527	318	7	0
2528	318	8	0
2529	319	1	0
2530	319	2	0
2531	319	3	0
2532	319	4	0
2533	319	5	0
2534	319	6	0
2535	319	7	0
2536	319	8	0
2537	320	1	1000
2538	320	2	1200
2539	320	3	1400
2540	320	4	1600
2541	320	5	1800
2542	320	6	2000
2543	320	7	2200
2544	320	8	0
2545	321	1	1000
2546	321	2	1240
2547	321	3	1480
2548	321	4	1720
2549	321	5	1960
2550	321	6	2200
2551	321	7	0
2552	322	1	0
2553	322	2	0
2554	322	3	0
2555	322	4	0
2556	322	5	0
2557	322	6	0
2558	322	7	0
2559	322	8	0
2560	323	1	0
2561	323	2	0
2562	323	3	0
2563	323	4	0
2564	323	5	0
2565	323	6	0
2566	323	7	0
2567	323	8	0
2568	324	1	750
2569	324	2	850
2570	324	3	950
2571	324	4	1050
2572	324	5	0
2573	324	6	0
2574	324	7	0
2575	324	8	0
2576	325	1	2900
2577	325	2	2900
2578	325	3	2900
2579	325	4	2900
2580	325	5	2900
2581	325	6	2900
2582	325	7	0
2583	325	8	0
2584	326	1	0
2585	326	2	0
2586	326	3	0
2587	326	4	0
2588	326	5	0
2589	326	6	0
2590	326	7	0
2591	326	8	0
2592	327	1	2500
2593	327	2	2600
2594	327	3	2700
2595	327	4	2800
2596	327	5	2900
2597	327	6	3000
2598	327	7	0
2599	327	8	0
2600	328	1	2500
2601	328	2	2600
2602	328	3	2700
2603	328	4	2800
2604	328	5	2900
2605	328	6	3000
2606	328	7	0
2607	328	8	0
2608	329	1	0
2609	329	2	0
2610	329	3	0
2611	329	4	0
2612	329	5	0
2613	329	6	0
2614	329	7	0
2615	329	8	0
2616	330	1	2200
2617	330	2	2520
2618	330	3	2840
2619	330	4	3160
2620	330	5	3480
2621	330	6	3800
2622	330	7	0
2623	330	8	0
2624	331	1	2200
2625	331	2	2520
2626	331	3	2840
2627	331	4	3160
2628	331	5	3480
2629	331	6	3800
2630	331	7	0
2631	331	8	0
2632	332	1	1490
2633	332	2	1490
2634	332	3	0
2635	332	4	0
2636	332	5	0
2637	332	6	0
2638	332	7	0
2639	332	8	0
2640	333	1	1450
2641	333	2	1850
2642	333	3	2250
2643	333	4	2650
2644	333	5	3050
2645	333	6	0
2646	333	7	0
2647	333	8	0
2648	334	1	0
2649	334	2	0
2650	334	3	0
2651	334	4	0
2652	334	5	0
2653	334	6	0
2654	334	7	0
2655	334	8	0
2656	335	1	0
2657	335	2	0
2658	335	3	0
2659	335	4	0
2660	335	5	0
2661	335	6	0
2662	335	7	0
2663	335	8	0
2664	336	1	960
2665	336	2	1348
2666	336	3	1736
2667	336	4	2124
2668	336	5	2512
2669	336	6	2900
2670	336	7	0
2671	336	8	0
2672	337	1	690
2673	337	2	1348
2674	337	3	1736
2675	337	4	2124
2676	337	5	2512
2677	337	6	2900
2678	337	7	0
2679	337	8	0
2680	338	1	1450
2681	338	2	1460
2682	338	3	1470
2683	338	4	1480
2684	338	5	1490
2685	338	6	0
2686	338	7	0
2687	338	8	0
2688	339	1	0
2689	339	2	0
2690	339	3	0
2691	339	4	0
2692	339	5	0
2693	339	6	0
2694	339	7	0
2695	339	8	0
2696	340	1	0
2697	340	2	0
2698	340	3	0
2699	340	4	0
2700	340	5	0
2701	340	6	0
2702	340	7	0
2703	340	8	0
2704	341	1	0
2705	341	2	0
2706	341	3	0
2707	341	4	0
2708	341	5	0
2709	341	6	0
2710	341	7	0
2711	341	8	0
2712	342	1	0
2713	342	2	0
2714	342	3	0
2715	342	4	0
2716	342	5	0
2717	342	6	0
2718	342	7	0
2719	342	8	0
2720	343	1	0
2721	343	2	0
2722	343	3	0
2723	343	4	0
2724	343	5	0
2725	343	6	0
2726	343	7	0
2727	343	8	0
2728	344	1	0
2729	344	2	0
2730	344	3	0
2731	344	4	0
2732	344	5	0
2733	344	6	0
2734	344	7	0
2735	344	8	0
2736	345	1	0
2737	345	2	0
2738	345	3	0
2739	345	4	0
2740	345	5	0
2741	345	6	0
2742	345	7	0
2743	345	8	0
2744	346	1	1450
2745	346	2	1460
2746	346	3	1470
2747	346	4	1480
2748	346	5	0
2749	346	6	0
2750	346	7	0
2751	346	8	0
2752	347	1	0
2753	347	2	0
2754	347	3	0
2755	347	4	0
2756	347	5	0
2757	347	6	0
2758	347	7	0
2759	347	8	0
2760	348	1	0
2761	348	2	0
2762	348	3	0
2763	348	4	0
2764	348	5	0
2765	348	6	0
2766	348	7	0
2767	348	8	0
2768	349	1	0
2769	349	2	0
2770	349	3	0
2771	349	4	0
2772	349	5	0
2773	349	6	0
2774	349	7	0
2775	349	8	0
2776	350	1	1450
2777	350	2	1750
2778	350	3	2050
2779	350	4	2350
2780	350	5	2650
2781	350	6	2950
2782	350	7	0
2783	350	8	0
2784	351	1	0
2785	351	2	0
2786	351	3	0
2787	351	4	0
2788	351	5	0
2789	351	6	0
2790	351	7	0
2791	351	8	0
2792	352	1	0
2793	352	2	0
2794	352	3	0
2795	352	4	0
2796	352	5	0
2797	352	6	0
2798	352	7	0
2799	352	8	0
2800	353	1	0
2801	353	2	0
2802	353	3	0
2803	353	4	0
2804	353	5	0
2805	353	6	0
2806	353	7	0
2807	353	8	0
2808	354	1	0
2809	354	2	0
2810	354	3	0
2811	354	4	0
2812	354	5	0
2813	354	6	0
2814	354	7	0
2815	354	8	0
2816	355	1	0
2817	355	2	0
2818	355	3	0
2819	355	4	0
2820	355	5	0
2821	355	6	0
2822	355	7	0
2823	355	8	0
2824	356	1	1480
2825	356	2	1480
2826	356	3	1480
2827	356	4	1480
2828	356	5	1480
2829	356	6	1480
2830	356	7	1480
2831	356	8	14
2832	357	1	1488
2833	357	2	0
2834	357	3	0
2835	357	4	0
2836	357	5	0
2837	357	6	0
2838	357	7	0
2839	357	8	0
2840	358	1	0
2841	358	2	0
2842	358	3	0
2843	358	4	0
2844	358	5	0
2845	358	6	0
2846	358	7	0
2847	358	8	0
2848	359	1	900
2849	359	2	1050
2850	359	3	1250
2851	359	4	1450
2852	359	5	0
2853	359	6	0
2854	359	7	0
2855	359	8	0
2856	360	1	900
2857	360	2	1000
2858	360	3	1150
2859	360	4	1450
2860	360	5	1800
2861	360	6	0
2862	360	7	0
2863	360	8	0
2864	361	1	1491
2865	361	2	1491
2866	361	3	0
2867	361	4	0
2868	361	5	0
2869	361	6	0
2870	361	7	0
2871	361	8	0
2872	362	1	0
2873	362	2	0
2874	362	3	0
2875	362	4	0
2876	362	5	0
2877	362	6	0
2878	362	7	0
2879	362	8	0
2880	363	1	993
2881	363	2	993
2882	363	3	993
2883	363	4	0
2884	363	5	0
2885	363	6	0
2886	363	7	0
2887	363	8	0
2888	364	1	300
2889	364	2	330
2890	364	3	360
2891	364	4	400
2892	364	5	0
2893	364	6	0
2894	364	7	0
2895	364	8	0
2896	365	1	850
2897	365	2	1100
2898	365	3	1250
2899	365	4	1450
2900	365	5	0
2901	365	6	0
2902	365	7	0
2903	365	8	0
2904	366	1	0
2905	366	2	0
2906	366	3	0
2907	366	4	0
2908	366	5	0
2909	366	6	0
2910	366	7	0
2911	366	8	0
2912	367	1	0
2913	367	2	0
2914	367	3	0
2915	367	4	0
2916	367	5	0
2917	367	6	0
2918	367	7	0
2919	367	8	0
2920	368	1	0
2921	368	2	0
2922	368	3	0
2923	368	4	0
2924	368	5	0
2925	368	6	0
2926	368	7	0
2927	368	8	0
2928	369	1	0
2929	369	2	0
2930	369	3	0
2931	369	4	0
2932	369	5	0
2933	369	6	0
2934	369	7	0
2935	369	8	0
2936	370	1	0
2937	370	2	0
2938	370	3	0
2939	370	4	0
2940	370	5	0
2941	370	6	0
2942	370	7	0
2943	370	8	0
2944	371	1	0
2945	371	2	0
2946	371	3	0
2947	371	4	0
2948	371	5	0
2949	371	6	0
2950	371	7	0
2951	371	8	0
2952	372	1	0
2953	372	2	0
2954	372	3	0
2955	372	4	0
2956	372	5	0
2957	372	6	0
2958	372	7	0
2959	372	8	0
2960	373	1	0
2961	373	2	0
2962	373	3	0
2963	373	4	0
2964	373	5	0
2965	373	6	0
2966	373	7	0
2967	373	8	0
2968	374	1	0
2969	374	2	0
2970	374	3	0
2971	374	4	0
2972	374	5	0
2973	374	6	0
2974	374	7	0
2975	374	8	0
2976	375	1	0
2977	375	2	0
2978	375	3	0
2979	375	4	0
2980	375	5	0
2981	375	6	0
2982	375	7	0
2983	375	8	0
2984	376	1	0
2985	376	2	0
2986	376	3	0
2987	376	4	0
2988	376	5	0
2989	376	6	0
2990	376	7	0
2991	376	8	0
2992	377	1	0
2993	377	2	0
2994	377	3	0
2995	377	4	0
2996	377	5	0
2997	377	6	0
2998	377	7	0
2999	377	8	0
3000	378	1	0
3001	378	2	0
3002	378	3	0
3003	378	4	0
3004	378	5	0
3005	378	6	0
3006	378	7	0
3007	378	8	0
3008	379	1	0
3009	379	2	0
3010	379	3	0
3011	379	4	0
3012	379	5	0
3013	379	6	0
3014	379	7	0
3015	379	8	0
3016	380	1	0
3017	380	2	0
3018	380	3	0
3019	380	4	0
3020	380	5	0
3021	380	6	0
3022	380	7	0
3023	380	8	0
3024	381	1	0
3025	381	2	0
3026	381	3	0
3027	381	4	0
3028	381	5	0
3029	381	6	0
3030	381	7	0
3031	381	8	0
3032	382	1	0
3033	382	2	0
3034	382	3	0
3035	382	4	0
3036	382	5	0
3037	382	6	0
3038	382	7	0
3039	382	8	0
3040	383	1	0
3041	383	2	0
3042	383	3	0
3043	383	4	0
3044	383	5	0
3045	383	6	0
3046	383	7	0
3047	383	8	0
3048	384	1	0
3049	384	2	0
3050	384	3	0
3051	384	4	0
3052	384	5	0
3053	384	6	0
3054	384	7	0
3055	384	8	0
3056	385	1	0
3057	385	2	0
3058	385	3	0
3059	385	4	0
3060	385	5	0
3061	385	6	0
3062	385	7	0
3063	385	8	0
3064	386	1	735
3065	386	2	940
3066	386	3	1145
3067	386	4	1350
3068	386	5	1555
3069	386	6	1760
3070	386	7	0
3071	386	8	0
\.


--
-- Data for Name: pumps; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.pumps (id, pump_code, manufacturer, pump_type, series, application_category, construction_standard, impeller_type, created_at) FROM stdin;
1	100-200 2F	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:05:53.377836+00
2	100-200 2F 2P 	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:05:53.825573+00
3	100-200 CAISION	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	RADIAL	2025-07-30 14:05:54.121752+00
4	100-250 2F	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:05:54.296998+00
5	100-250 2F 2P	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:05:54.693601+00
6	100-315 2F	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:05:55.094733+00
7	100-400 2F	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:05:55.362698+00
8	100-50 Multistage	APE PUMPS	MULTI-STAGE	MATHER AND PLATT	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:05:55.72791+00
9	100-80-250 4P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:05:55.845718+00
10	10/12 BLE	APE PUMPS	HSC	MATHER AND PLATT	WATER SUPPLY	BS	CLOSED DOUBLE SUCTION	2025-07-30 14:05:56.006926+00
11	10/12 DESC	APE PUMPS	HSC	DESC	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:05:56.130256+00
12	10/12 DME	APE PUMPS	HSC	DME	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:05:56.31731+00
13	10/12 GME	APE PUMPS	HSC	GME	WATER SUPPLY	BS	CLOSED	2025-07-30 14:05:56.459037+00
14	10 ADM	APE PUMPS	HSC	ADM	WATER SUPPLY	BS	CLOSED	2025-07-30 14:05:56.698771+00
15	10 NHTB	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:05:56.834369+00
16	10 WLN 18A	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:05:56.961828+00
17	10 WLN 22A	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:05:57.188832+00
18	10 WLN 26A	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:05:57.504698+00
19	10 WLN 32A	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:05:58.113601+00
20	10 WO 2P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	OPEN	2025-07-30 14:05:58.471836+00
21	10 WO 4P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	OPEN	2025-07-30 14:05:58.808714+00
22	11 MQ H 1100VLT	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:05:59.142809+00
23	11 MQ H 1100VLT 2P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:05:59.511236+00
24	1200MF	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	OPEN	2025-07-30 14:05:59.983102+00
25	125-100-250	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:00.084817+00
26	125-100-315 4P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:00.225154+00
27	125-250 2F	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:00.640831+00
28	125-315 2F	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:01.144855+00
29	125-400 2F	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:01.598462+00
30	12/10 AH WARMAN SLURRY	APE PUMPS	END SUCTION	APE	WATER SUPPLY	-	CLOSED	2025-07-30 14:06:02.01732+00
31	12/14 BDY	APE PUMPS	HSC	BDY	WATER SUPPLY	BS	CLOSED DOUBLE SUCTION	2025-07-30 14:06:02.114654+00
32	12/14 BLE	APE PUMPS	HSC	BLE	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:02.248702+00
33	12/14 DESC	APE PUMPS	HSC	DESC	WATER SUPPLY	BS	 DOUBLE SUCTION	2025-07-30 14:06:02.373826+00
34	12/14 DM	APE PUMPS	HSC	DME	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:02.573563+00
35	12/14 DME	APE PUMPS	HSC	DME	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:02.762593+00
36	12/15 V.S.M.F.V	APE PUMPS	END SUCTION	APE	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:02.892916+00
37	12 HC 1133 4P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:06:03.098202+00
38	12 HC 1134 4P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:06:03.319414+00
39	12 HC 4P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:06:03.533298+00
40	12 LC 4P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	OPEN	2025-07-30 14:06:04.036071+00
41	12 LC 9stg (Test Results)	APE PUMPS	VERTICAL TURBINE	SITE TEST	WATER SUPPLY	BS	OPEN	2025-07-30 14:06:04.174+00
42	12 LNH 21A	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:04.28707+00
43	12 LNH 21B	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:04.584367+00
44	12 MC 4P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	OPEN	2025-07-30 14:06:04.772554+00
45	12 WLN 14A	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:04.871696+00
46	12 WLN 14B	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:05.052331+00
47	12 WLN 17A	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:05.249239+00
48	12 WLN 17B	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:05.539701+00
49	12 WLN 21A	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:05.750998+00
50	12 WLN 21B	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:05.959993+00
51	12X16X23H DSJH	APE PUMPS	END SUCTION	BJ	PETROCHEM	API	CLOSED 	2025-07-30 14:06:06.182423+00
52	14/12BDY	APE PUMPS	HSC	BDY	WATER SUPPLY	BS	CLOSED DOUBLE SUCTION	2025-07-30 14:06:06.287711+00
53	14/16 ADM	APE PUMPS	HSC	ADM	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:06.495769+00
54	14/16 BLE	APE PUMPS	HSC	BLE	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:06.754929+00
55	14/18 EME	APE PUMPS	HSC	EME	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:06.9038+00
56	14 HC 1203 4P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:06:07.011196+00
57	14 HC 1204 4P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:06:07.244753+00
58	14 MC 6970 4P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	OPEN	2025-07-30 14:06:07.483209+00
59	14 MC 755  4P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:07.586961+00
60	14 MC 756  4P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:07.726778+00
61	14 MC 757  4P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:07.871167+00
62	14 WLN 19A	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:08.208491+00
63	150-125-250 4P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:08.63232+00
64	150-125-315	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:10.313029+00
65	150-125-400 4P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:10.744992+00
66	150-150-200 4P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:11.225776+00
67	150-150-200A 4P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:11.591521+00
68	150-200 2F	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:12.791803+00
69	150-250 2F	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:14.65335+00
70	150-315 2F	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:15.252385+00
71	150-400 2F	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:15.700651+00
72	16 HC 1262 4P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:06:16.299508+00
73	16 HC 1262 6P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:06:16.393758+00
74	16 HC 1264 4P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:06:16.495226+00
75	16 HC 1264 6P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:06:16.901606+00
76	16 WLN 23C	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:17.126488+00
77	16 WLN 28C	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:17.44745+00
78	16 WLN 35 C	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:17.770053+00
79	18/16 BDM	APE PUMPS	HSC	BDM	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:18.508026+00
80	18/20 DME	APE PUMPS	HSC	DME	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:19.670838+00
81	18/22 MEDIVANE	APE PUMPS	HSC	MEDIVANE	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:19.985727+00
82	18 HC 1213 4P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:06:20.271341+00
83	18 HC 1213 4P SABS	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:06:20.535459+00
84	18 HC 1213 6P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:06:20.710445+00
85	18 HC 1214 4P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:06:20.843568+00
86	18 HC 1214 4P 6ST SABS	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:06:21.005338+00
87	18 HC 1214 4P SABS	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:06:21.21524+00
88	18 HC 1214 6P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:06:21.356562+00
89	18 HC + 18 XHC SPECIAL	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:21.461771+00
90	18 XHC 2185 4P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:06:21.566416+00
91	18 XHC 2185 6P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:06:21.770198+00
92	18 XHC 2186 4P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:06:21.929426+00
93	18 XHC 2186 6P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:06:22.306023+00
94	18XHC - 3 Stage	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:22.761407+00
95	1.5X2X10.5 H	APE PUMPS	END SUCTION	BJ	PETROCHEM	API	CLOSED 	2025-07-30 14:06:23.113681+00
96	1.5X2X8.5 H	APE PUMPS	END SUCTION	BJ	PETROCHEM	API	CLOSED 	2025-07-30 14:06:23.248143+00
97	200-150-315 4P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:23.379163+00
98	200-150-315 6P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:23.677594+00
99	200-150-400 4P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:23.93066+00
100	200-150-400 6P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:24.123153+00
101	200-150-456 6P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:24.340732+00
102	200-150-460 4P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:24.456366+00
103	200-200-250 4P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:24.660689+00
104	200-200-250 6P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:25.140955+00
105	200-200-250A 4P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:25.387182+00
106	200-200-250A 6P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:25.70071+00
107	200-200-310 4P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:25.949816+00
108	200-200-310 6P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:26.217483+00
109	200-200-310A 4P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:26.598201+00
110	200-200-310A 6P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:26.756036+00
111	200-200-350 4P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:27.228213+00
112	200-200-430 4P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:27.391908+00
113	200-200-430 6P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:27.885733+00
114	200-200-540 4P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:28.026421+00
115	20/24 CME	APE PUMPS	HSC	CME	WATER SUPPLY	BS	CLOSED DOUBLE SUCTION	2025-07-30 14:06:28.225196+00
116	20/24 CME2	APE PUMPS	HSC	CME	WATER SUPPLY	BS	CLOSED DOUBLE SUCTION	2025-07-30 14:06:28.715213+00
117	20/24 DV CME	APE PUMPS	HSC	CME	WATER SUPPLY	BS	CLOSED DOUBLE SUCTION	2025-07-30 14:06:29.131396+00
118	20/24 DV MEDI	APE PUMPS	HSC	MATHER AND PLATT	WATER SUPPLY	BS	 DOUBLE SUCTION	2025-07-30 14:06:29.424226+00
119	20 D.S	APE PUMPS	HSC	APE	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:29.554767+00
120	20 WLN 22A	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:29.6806+00
121	20 WLN 22A 6P	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:29.897316+00
122	20 WLN 22B	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:30.202644+00
123	20 WLN 26A	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:30.328293+00
124	20 WLN 26B	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:30.558617+00
125	20 WLN 28B 6P	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:30.810987+00
126	20 WLN 28B 8P	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:30.97708+00
127	20 WLN 28C	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:31.227119+00
128	24 WLN 26A	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:31.639983+00
129	24 WLN 34A	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:31.886133+00
130	24 WLN 42A	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:32.09419+00
131	24 WLN 46A	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:32.277481+00
132	250-200-480 4P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:32.43197+00
133	250-200-480 6P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:32.631001+00
134	250-200-610 4P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:32.892549+00
135	250-200-610 6P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:33.162133+00
136	250-250-360 4P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:33.524218+00
137	250-250-360 6P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:33.736318+00
138	250-250-360A 4P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:33.93825+00
139	250-250-360A 6P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:34.121445+00
140	250-250-400 4P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:34.284406+00
141	250-250-400 6P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:34.500451+00
142	250-250-400A 4P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:34.689171+00
143	250-250-400A 6P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:34.844913+00
144	250-250-450 4P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:35.07737+00
145	250-250-450 6P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:35.236679+00
146	250-250-540 4P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:35.373536+00
147	250-250-540 6P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:35.750939+00
148	250/300 BST	APE PUMPS	HSC	APE	WATER SUPPLY	BS	CLOSED DOUBLE SUCTION	2025-07-30 14:06:35.945883+00
149	250/450	APE PUMPS	HSC	MATHER AND PLATT	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:36.05997+00
150	28 HC 6P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:06:36.148773+00
151	28 HC 8P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:06:36.260274+00
152	2.5 K	APE PUMPS	HSC	K	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:36.365855+00
153	2.5 KL	APE PUMPS	HSC	KL	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:36.543573+00
154	2 K	APE PUMPS	HSC	K	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:36.688226+00
155	2 KL	APE PUMPS	HSC	KL	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:36.776666+00
156	300-250-600	APE PUMPS	HSC	APE	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:36.86046+00
157	30 HC 6P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:06:36.958688+00
158	30 WLN 30C	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:37.225115+00
159	30 WLN 41C	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:37.36823+00
160	32-200 2F	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:37.473055+00
161	32-200 2F 2P	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:37.718922+00
162	32 HC 6P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:06:37.903672+00
163	32 HC 8P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:06:38.011302+00
164	32 XHC 6P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:06:38.122142+00
165	32 XHC 8P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:06:38.233372+00
166	350-300-429 DESC	APE PUMPS	HSC	DESC	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:38.482124+00
167	36 HC 6P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:06:38.920448+00
168	36 XHC 8P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:06:39.293875+00
169	3/40I	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:39.405462+00
170	3/4 MEDI	APE PUMPS	HSC	MATHER AND PLATT	WATER SUPPLY	BS	 DOUBLE SUCTION	2025-07-30 14:06:39.589045+00
171	3 K	APE PUMPS	HSC	K	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:39.753914+00
172	3WLN12K	APE PUMPS	HSC	LR	WATER SUPPLY	-	OPEN	2025-07-30 14:06:39.965959+00
173	3X4X10.5 H SJA	APE PUMPS	END SUCTION	BJ	PETROCHEM	API	CLOSED 	2025-07-30 14:06:40.113555+00
174	400-300-435	APE PUMPS	HSC	APE	WATER SUPPLY	BS	CLOSED DOUBLE SUCTION	2025-07-30 14:06:40.237383+00
175	400-600	APE PUMPS	VERTICAL TURBINE	CAISSON	WATER SUPPLY	BS	DOUBLE IMPELLER	2025-07-30 14:06:40.349493+00
176	4503-42936	APE PUMPS	MULTI-STAGE	APE	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:40.448789+00
177	4503-42937	APE PUMPS	MULTI-STAGE	APE	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:40.693308+00
178	4503-44648	APE PUMPS	MULTI-STAGE	APE	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:40.848325+00
179	4503-44649	APE PUMPS	MULTI-STAGE	APE	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:40.978345+00
180	4503-44786	APE PUMPS	MULTI-STAGE	APE	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:41.474064+00
181	4503-44787	APE PUMPS	MULTI-STAGE	APE	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:41.713473+00
182	4504-42564	APE PUMPS	MULTI-STAGE	APE	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:41.933213+00
183	4504-42565	APE PUMPS	MULTI-STAGE	APE	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:42.097959+00
184	4505-48159	APE PUMPS	MULTI-STAGE	APE	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:42.242494+00
185	4505-48190	APE PUMPS	MULTI-STAGE	APE	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:42.395388+00
186	4506-48170	APE PUMPS	MULTI-STAGE	APE	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:42.55026+00
187	4506-48171	APE PUMPS	MULTI-STAGE	APE	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:42.700251+00
188	4625-38112	APE PUMPS	MULTI-STAGE	RITZ	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:42.823098+00
189	48/48 LONOVANE	APE PUMPS	HSC	APE	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:42.920158+00
190	4/40 GME	APE PUMPS	HSC	GME	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:43.088252+00
191	4/5	APE PUMPS	MULTI-STAGE	APE	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:43.271354+00
192	4/5 2 STAGE MEDI	APE PUMPS	HSC	MATHER AND PLATT	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:43.362138+00
193	4/5 ALE	APE PUMPS	HSC	ALE	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:43.461087+00
194	4/5 BLE	APE PUMPS	HSC	BLE	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:43.579777+00
195	4/5 CME	APE PUMPS	HSC	CME	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:43.822559+00
196	4/5 DME	APE PUMPS	HSC	DME	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:44.217325+00
197	4/5 MEDI	APE PUMPS	HSC	MATHER AND PLATT	WATER SUPPLY	BS	 DOUBLE SUCTION	2025-07-30 14:06:44.376097+00
198	4K	APE PUMPS	HSC	K	WATER SUPPLY	BS	CLOSED DOUBLE SUCTION	2025-07-30 14:06:44.460069+00
199	4x6x13.25 H-SJA	APE PUMPS	END SUCTION	BJ	WATER SUPPLY	API	RADIAL	2025-07-30 14:06:44.618216+00
200	4X6X13.25 L GSJH	APE PUMPS	END SUCTION	BJ	PETROCHEM	API	CLOSED 	2025-07-30 14:06:44.730302+00
201	4X6X8.5 L SJA	APE PUMPS	END SUCTION	BJ	PETROCHEM	API	RADIAL	2025-07-30 14:06:44.810169+00
202	50-160 2F	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:44.911607+00
203	50-160 2F 2P	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:45.105023+00
204	50-200 2F	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:45.266303+00
205	50-200 2F 2P 	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:45.485184+00
206	50-250 2F	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:45.655236+00
207	50-250 2F 2P	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:45.897578+00
208	50-315 2F	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:46.118283+00
209	5/6	APE PUMPS	MULTI-STAGE	WPIL	WATER SUPPLY	BS	OPEN	2025-07-30 14:06:46.262906+00
210	5/6 ALE	APE PUMPS	HSC	ALE	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:46.40121+00
211	5/6 BLE	APE PUMPS	HSC	BLE	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:46.579868+00
212	5/6 CME 	APE PUMPS	HSC	CME	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:46.751549+00
213	5/6 DME	APE PUMPS	HSC	DME	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:46.86796+00
214	5/6 MEDI	APE PUMPS	HSC	MEDIVANE	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:46.983893+00
215	5/6 MEDI 2P	APE PUMPS	HSC	MEDIVANE	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:47.132142+00
216	5/6 MEDIVANE	APE PUMPS	HSC	MEDIVANE	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:47.347105+00
217	5/6 MEDIVANE 2P	APE PUMPS	HSC	MEDIVANE	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:47.463253+00
218	5 K	APE PUMPS	HSC	K	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:47.58077+00
219	5 KL	APE PUMPS	HSC	KL	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:47.690774+00
220	5X6 HSC	APE PUMPS	HSC	APE	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:47.830151+00
221	65-125 2F	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:47.932392+00
222	65-160 2F	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:48.204071+00
223	65-160 2F 2P	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:48.68239+00
224	65-200 1F	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:49.174603+00
225	65-200 2F	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:49.298392+00
226	65-200 2F 2P	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:49.443777+00
227	65-250 2F	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:49.647616+00
228	65-250 2F 2P	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:49.857458+00
229	65-315 2F	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:50.107392+00
230	6/8 ALE	APE PUMPS	HSC	ALE	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:50.280992+00
231	6/8 DME	APE PUMPS	HSC	DME	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:50.579616+00
232	6/8 DMP	APE PUMPS	HSC	DMP	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:50.843166+00
233	6/8 EME	APE PUMPS	HSC	EME	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:50.965926+00
234	6/8 GME	APE PUMPS	HSC	GME	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:51.351519+00
235	6 B/B	APE PUMPS	HSC	APE	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:51.586616+00
236	6 HC	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	OPEN	2025-07-30 14:06:51.722388+00
237	6 K 6 VANE	APE PUMPS	HSC	K	WATER SUPPLY	BS	CLOSED DOUBLE SUCTION	2025-07-30 14:06:51.821708+00
238	6 K 8 VANE	APE PUMPS	HSC	K	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:51.958168+00
239	6 KL	APE PUMPS	HSC	KL	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:52.088954+00
240	6 LC	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	OPEN	2025-07-30 14:06:52.233405+00
241	6 MC	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	OPEN	2025-07-30 14:06:52.325681+00
242	6 SLM 2P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:52.414839+00
243	6 WLN 18A	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:52.50399+00
244	6 WLN 21A	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:52.723797+00
245	6 XLC	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:06:52.93133+00
246	6X8X11L DSJA	APE PUMPS	END SUCTION	BJ	WATER SUPPLY	API	 DOUBLE SUCTION	2025-07-30 14:06:53.046869+00
247	6X8X13H SJA	APE PUMPS	END SUCTION	BJ	PETROCHEM	API	CLOSED 	2025-07-30 14:06:53.309493+00
248	700-600-710 6P	APE PUMPS	HSC	DESC	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:53.662004+00
249	700-600-710 8P	APE PUMPS	HSC	DESC	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:53.896264+00
250	7 KL	APE PUMPS	HSC	KL	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:06:54.091035+00
251	7 MC	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	OPEN	2025-07-30 14:06:54.218521+00
252	80-160 2F	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:54.349263+00
253	80-160 2F 2P	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:54.516454+00
254	80-200 2F	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:54.811127+00
255	80-200 2F 2P	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:54.984789+00
256	80-250 2F	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:55.15902+00
257	80-250 2F 2P	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:55.717888+00
258	80-315 2F	APE PUMPS	END SUCTION	2F	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:06:55.878587+00
259	80-50-315 2P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:56.059878+00
260	80-50-315 4P	APE PUMPS	END SUCTION	NIMBUS	WATER SUPPLY	BS	CLOSED	2025-07-30 14:06:56.220776+00
261	8211-16 970	APE PUMPS	AXIAL FLOW	PROPELLOR	RAW WATER	BS	OPEN	2025-07-30 14:06:56.436441+00
262	8211-30	APE PUMPS	AXIAL FLOW	PROPELLOR	RAW WATER	BS	OPEN	2025-07-30 14:06:56.535413+00
263	8312-14	APE PUMPS	AXIAL FLOW	PROPELLOR	RAW WATER	BS	OPEN	2025-07-30 14:06:56.6345+00
264	8312-14 310F	APE PUMPS	AXIAL FLOW	PROPELLOR	RAW WATER	BS	OPEN	2025-07-30 14:06:56.810712+00
265	8312-14 311F	APE PUMPS	AXIAL FLOW	PROPELLOR	RAW WATER	BS	OPEN	2025-07-30 14:06:56.926335+00
266	8312-14 311T	APE PUMPS	AXIAL FLOW	PROPELLOR	RAW WATER	BS	OPEN	2025-07-30 14:06:57.066093+00
267	8312-14 312T	APE PUMPS	AXIAL FLOW	PROPELLOR	RAW WATER	BS	OPEN	2025-07-30 14:06:57.148177+00
268	8312-14 313T	APE PUMPS	AXIAL FLOW	PROPELLOR	RAW WATER	BS	OPEN	2025-07-30 14:06:57.218717+00
269	8312-14 313T 4P	APE PUMPS	AXIAL FLOW	PROPELLOR	RAW WATER	BS	OPEN	2025-07-30 14:06:57.373091+00
270	8312-16 312T	APE PUMPS	AXIAL FLOW	PROPELLOR	RAW WATER	BS	OPEN	2025-07-30 14:06:57.597043+00
271	8312-16 370F	APE PUMPS	AXIAL FLOW	PROPELLOR	RAW WATER	BS	OPEN	2025-07-30 14:06:57.826841+00
272	8312-16 371T	APE PUMPS	AXIAL FLOW	PROPELLOR	RAW WATER	BS	OPEN	2025-07-30 14:06:57.998543+00
273	8312-16 372T	APE PUMPS	AXIAL FLOW	PROPELLOR	RAW WATER	BS	OPEN	2025-07-30 14:06:58.076839+00
274	8312-16 373T	APE PUMPS	AXIAL FLOW	PROPELLOR	RAW WATER	BS	OPEN	2025-07-30 14:06:58.243349+00
275	8312-20 340F	APE PUMPS	AXIAL FLOW	PROPELLOR	RAW WATER	BS	OPEN	2025-07-30 14:06:58.417368+00
276	8312-20 341T	APE PUMPS	AXIAL FLOW	PROPELLOR	RAW WATER	BS	OPEN	2025-07-30 14:06:58.718872+00
277	8312-20 342T	APE PUMPS	AXIAL FLOW	PROPELLOR	RAW WATER	BS	OPEN	2025-07-30 14:06:59.150244+00
278	8312-20 343T	APE PUMPS	AXIAL FLOW	PROPELLOR	RAW WATER	BS	OPEN	2025-07-30 14:06:59.403313+00
279	8312-24 360F	APE PUMPS	AXIAL FLOW	PROPELLOR	RAW WATER	BS	OPEN	2025-07-30 14:06:59.503904+00
280	8312-24 361T	APE PUMPS	AXIAL FLOW	PROPELLOR	RAW WATER	BS	OPEN	2025-07-30 14:06:59.609164+00
281	8312-24 362T	APE PUMPS	AXIAL FLOW	PROPELLOR	RAW WATER	BS	OPEN	2025-07-30 14:06:59.726447+00
282	8312-24 363T	APE PUMPS	AXIAL FLOW	PROPELLOR	RAW WATER	BS	OPEN	2025-07-30 14:06:59.820445+00
283	8312-30 A330F	APE PUMPS	AXIAL FLOW	PROPELLOR	RAW WATER	BS	OPEN	2025-07-30 14:06:59.926521+00
284	8312-30 A331T	APE PUMPS	AXIAL FLOW	PROPELLOR	RAW WATER	BS	OPEN	2025-07-30 14:07:00.046957+00
285	8312-30 A332T	APE PUMPS	AXIAL FLOW	PROPELLOR	RAW WATER	BS	OPEN	2025-07-30 14:07:00.154493+00
286	8312-30 A333T	APE PUMPS	AXIAL FLOW	PROPELLOR	RAW WATER	BS	OPEN	2025-07-30 14:07:00.30812+00
287	8312 -10 B1431T	APE PUMPS	AXIAL FLOW	PROPELLOR	RAW WATER	BS	OPEN	2025-07-30 14:07:00.467466+00
288	8312 -10 B1433T	APE PUMPS	AXIAL FLOW	PROPELLOR	RAW WATER	BS	OPEN	2025-07-30 14:07:00.5858+00
289	8314-5	APE PUMPS	AXIAL FLOW	PROPELLOR	RAW WATER	BS	OPEN	2025-07-30 14:07:00.756653+00
290	8/10 BLE	APE PUMPS	HSC	BLE	WATER SUPPLY	BS	CLOSED DOUBLE SUCTION	2025-07-30 14:07:00.877265+00
291	8/10 CME - TA	APE PUMPS	HSC	MATHER AND PLATT	WATER SUPPLY	BS	DOUBLE IMPELLER	2025-07-30 14:07:01.243655+00
292	8/10 CME - TB	APE PUMPS	HSC	MATHER AND PLATT	WATER SUPPLY	BS	DOUBLE IMPELLER	2025-07-30 14:07:01.502523+00
293	8/10 DESC	APE PUMPS	HSC	DESC	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:07:01.720478+00
294	8/10 DME	APE PUMPS	HSC	DME	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:07:01.849996+00
295	8/10 GME	APE PUMPS	HSC	GME	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:07:01.967436+00
296	8/8 CME	APE PUMPS	HSC	CME	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:07:02.25103+00
297	8/8 CME 1900rpm	APE PUMPS	HSC	CME	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:07:02.358065+00
298	8/8 DME	APE PUMPS	HSC	DME	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:07:02.442134+00
299	8/8 GME 4P	APE PUMPS	HSC	GME	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:07:02.620409+00
300	8 B/B	APE PUMPS	HSC	APE	WATER SUPPLY	BS	DOUBLE IMPELLER	2025-07-30 14:07:02.763908+00
301	8 DESC	APE PUMPS	HSC	DESC	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:07:02.901355+00
302	8 HC	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	OPEN	2025-07-30 14:07:03.018597+00
303	8 K	APE PUMPS	HSC	K	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:07:03.151313+00
304	8 KL	APE PUMPS	HSC	KL	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:07:03.293391+00
305	8 LC	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	OPEN	2025-07-30 14:07:03.366031+00
306	8 MC	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	OPEN	2025-07-30 14:07:03.462591+00
307	8 SLH 2P	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	OPEN	2025-07-30 14:07:03.577906+00
308	8 WLN 18A	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:07:03.739444+00
309	8 WLN 18C	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:07:03.865254+00
310	8 WLN 21A	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:07:04.02114+00
311	8 WLN 29B	APE PUMPS	HSC	LN	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:07:04.164397+00
312	8X10X13 2S	APE PUMPS	MULTI-STAGE	BJ	PETROCHEM	API	CLOSED	2025-07-30 14:07:04.342094+00
313	8X10X13 2S NEW	APE PUMPS	MULTI-STAGE	BJ	PETROCHEM	API	CLOSED	2025-07-30 14:07:04.414245+00
314	8X10X13 3S	APE PUMPS	MULTI-STAGE	BJ	PETROCHEM	API	CLOSED	2025-07-30 14:07:04.512685+00
315	8X10X13 3S NEW	APE PUMPS	MULTI-STAGE	BJ	PETROCHEM	API	CLOSED	2025-07-30 14:07:04.594727+00
316	8X10X13 4S	APE PUMPS	MULTI-STAGE	BJ	PETROCHEM	API	CLOSED	2025-07-30 14:07:04.712295+00
317	8X10X13 4S2P	APE PUMPS	MULTI-STAGE	BJ	PETROCHEM	API	CLOSED	2025-07-30 14:07:04.794266+00
318	8X10X13 4S NEW	APE PUMPS	MULTI-STAGE	BJ	PETROCHEM	API	CLOSED	2025-07-30 14:07:04.974981+00
319	9-11 2 STAGE MEDIVANE	APE PUMPS	HSC	MEDIVANE	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:07:05.073815+00
320	APE DWU-150 BC	APE PUMPS	HSC	APE	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:07:05.145873+00
321	APE DWU - 150	APE PUMPS	HSC	APE	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:07:05.285864+00
322	BDM 16/14	APE PUMPS	HSC	BDM	WATER SUPPLY	BS	CLOSED 	2025-07-30 14:07:05.641482+00
323	DVMS 4000-125	APE PUMPS	HSC	APE	WATER SUPPLY	BS	CLOSED DOUBLE SUCTION	2025-07-30 14:07:05.756218+00
324	FD 300-250-400	APE PUMPS	END SUCTION	FD	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:05.818666+00
325	HMS 50/4	APE PUMPS	MULTI-STAGE	MATHER AND PLATT	WATER SUPPLY	BS	RADIAL	2025-07-30 14:07:05.902962+00
326	KL 150-100	APE PUMPS	END SUCTION	MATHER AND PLATT	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:06.001462+00
327	MISO 100-200	APE PUMPS	END SUCTION	MISO	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:06.171883+00
328	MISO 65-315H	APE PUMPS	END SUCTION	MISO	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:06.306809+00
329	Morgenstond 1	APE PUMPS	HSC	SITE TEST	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:06.536815+00
330	MSD10x10x13.5 3 4	APE PUMPS	HSC	MSD	WATER SUPPLY	BS	OPEN	2025-07-30 14:07:06.675366+00
331	MSD 10x10x13.5 3(4)	APE PUMPS	HSC	MSD	WATER SUPPLY	BS	OPEN	2025-07-30 14:07:06.784482+00
332	MSJ	APE PUMPS	MULTI-STAGE	MSJ	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:06.88388+00
333	Nitz 100-80-250	APE PUMPS	END SUCTION	NITZ	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:07.034461+00
334	PJ 100	APE PUMPS	MULTI-STAGE	PJ	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:07.252427+00
335	PJ 100 AS	APE PUMPS	MULTI-STAGE	PJ	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:07.35037+00
336	PJ 150 AN	APE PUMPS	MULTI-STAGE	PJ	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:07.464418+00
337	PJ 150 AS	APE PUMPS	MULTI-STAGE	PJ	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:07.582379+00
338	PJ 200	APE PUMPS	MULTI-STAGE	PJ	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:07.741736+00
339	PJ 200 AS	APE PUMPS	MULTI-STAGE	PJ	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:07.847551+00
340	PJ 250 AN	APE PUMPS	MULTI-STAGE	PJ	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:07.935013+00
341	PJ 250 AS	APE PUMPS	MULTI-STAGE	PJ	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:08.046279+00
342	PJ 250 BS	APE PUMPS	MULTI-STAGE	PJ	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:08.157828+00
343	PJ 250 H	APE PUMPS	MULTI-STAGE	PJ	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:08.435798+00
344	PJ 258 H	APE PUMPS	MULTI-STAGE	PJ	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:08.753966+00
345	PJ 80 	APE PUMPS	MULTI-STAGE	PJ	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:09.111964+00
346	PJ 80 AS	APE PUMPS	MULTI-STAGE	PJ	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:09.351993+00
347	PL 100 AN	APE PUMPS	MULTI-STAGE	PL	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:09.473713+00
348	PL 100 AS	APE PUMPS	MULTI-STAGE	PL	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:09.602131+00
349	PL 150 AN	APE PUMPS	MULTI-STAGE	PL	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:09.829454+00
350	PL 150 AS	APE PUMPS	MULTI-STAGE	PL	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:09.955322+00
351	PL 200 AN	APE PUMPS	MULTI-STAGE	PL	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:10.114366+00
352	PL 200 AS	APE PUMPS	MULTI-STAGE	PL	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:10.247288+00
353	PL 80 AN	APE PUMPS	MULTI-STAGE	PL	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:10.406753+00
354	PL 80 AS	APE PUMPS	MULTI-STAGE	PL	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:10.599839+00
355	QW400-26-45	APE PUMPS	HSC	APE	WATER SUPPLY	BS	CLOSED DOUBLE SUCTION	2025-07-30 14:07:10.776644+00
356	SCP 150/580HA-132/4	APE PUMPS	HSC	APE	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:10.879811+00
357	SCP 250/450HA	APE PUMPS	HSC	APE	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:10.955728+00
358	Umgeni Verulam July 2022	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:11.084653+00
359	VBK 35-22 3 Stage	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:11.268122+00
360	VBK 35-22.5 3 STAGE	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	FRANCIS VANE	2025-07-30 14:07:11.522778+00
361	VBK 420/018-4S	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	MIXED	2025-07-30 14:07:11.748663+00
362	VBK 620/022-4S	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:11.944124+00
363	VBK 620/022-4S (Test Curve)	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:12.052714+00
364	WI-1414	APE PUMPS	VERTICAL TURBINE	VTP	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:12.158343+00
365	WVP-130-30 (P30)	APE PUMPS	AXIAL FLOW	PROPELLOR	RAW WATER	BS	OPEN	2025-07-30 14:07:12.298515+00
366	WXH-100-240	APE PUMPS	MULTI-STAGE	WXH Series	WATER SUPPLY	BS	RADIAL	2025-07-30 14:07:12.386482+00
367	WXH-150-300	APE PUMPS	MULTI-STAGE	WXH Series	WATER SUPPLY	BS	RADIAL	2025-07-30 14:07:12.528329+00
368	WXH-32-132	APE PUMPS	MULTI-STAGE	WXH Series	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:07:12.676832+00
369	WXH-32-135	APE PUMPS	MULTI-STAGE	WXH Series	WATER SUPPLY	BS	RADIAL	2025-07-30 14:07:12.815636+00
370	WXH-34-35-100 	APE PUMPS	MULTI-STAGE	WXH Series	WATER SUPPLY	BS	RADIAL	2025-07-30 14:07:12.93149+00
371	WXH-40-135	APE PUMPS	MULTI-STAGE	WXH Series	WATER SUPPLY	BS	RADIAL	2025-07-30 14:07:13.105277+00
372	WXH-40-135 2P	APE PUMPS	MULTI-STAGE	WXH Series	WATER SUPPLY	BS	RADIAL	2025-07-30 14:07:13.269693+00
373	WXH-50-160	APE PUMPS	MULTI-STAGE	WXH Series	WATER SUPPLY	BS	RADIAL	2025-07-30 14:07:13.389861+00
374	WXH-50-160 2P	APE PUMPS	MULTI-STAGE	WXH Series	WATER SUPPLY	BS	RADIAL	2025-07-30 14:07:13.507586+00
375	WXH-64-100-150	APE PUMPS	MULTI-STAGE	WXH Series	WATER SUPPLY	BS	RADIAL	2025-07-30 14:07:13.651004+00
376	WXH-64-100-150B	APE PUMPS	MULTI-STAGE	WXH Series	WATER SUPPLY	BS	RADIAL	2025-07-30 14:07:13.791377+00
377	WXH-64-125-150A	APE PUMPS	MULTI-STAGE	WXH Series	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:07:13.881799+00
378	WXH-64-32-50	APE PUMPS	MULTI-STAGE	WXH Series	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:07:14.032974+00
379	WXH-64-35-100 	APE PUMPS	MULTI-STAGE	WXH Series	WATER SUPPLY	BS	RADIAL	2025-07-30 14:07:14.144335+00
380	WXH-64-40-65	APE PUMPS	MULTI-STAGE	WXH Series	WATER SUPPLY	BS	RADIAL	2025-07-30 14:07:14.260968+00
381	WXH-64-80-125 	APE PUMPS	MULTI-STAGE	WXH Series	WATER SUPPLY	BS	RADIAL 	2025-07-30 14:07:14.409163+00
382	WXH-65-185	APE PUMPS	MULTI-STAGE	WXH Series	WATER SUPPLY	BS	RADIAL	2025-07-30 14:07:14.568582+00
383	WXH-65-185 2P	APE PUMPS	MULTI-STAGE	WXH Series	WATER SUPPLY	BS	RADIAL	2025-07-30 14:07:14.712342+00
384	WXH-80-210	APE PUMPS	MULTI-STAGE	WXH Series	WATER SUPPLY	BS	RADIAL	2025-07-30 14:07:14.834547+00
385	WXH-80-210 2P	APE PUMPS	MULTI-STAGE	WXH Series	WATER SUPPLY	BS	RADIAL	2025-07-30 14:07:14.977358+00
386	XF18	APE PUMPS	VERTICAL TURBINE	XF	WATER SUPPLY	BS	CLOSED	2025-07-30 14:07:15.168472+00
\.


--
-- Name: application_profiles_id_seq; Type: SEQUENCE SET; Schema: admin_config; Owner: neondb_owner
--

SELECT pg_catalog.setval('admin_config.application_profiles_id_seq', 12, true);


--
-- Name: configuration_audits_id_seq; Type: SEQUENCE SET; Schema: admin_config; Owner: neondb_owner
--

SELECT pg_catalog.setval('admin_config.configuration_audits_id_seq', 1, false);


--
-- Name: engineering_constants_id_seq; Type: SEQUENCE SET; Schema: admin_config; Owner: neondb_owner
--

SELECT pg_catalog.setval('admin_config.engineering_constants_id_seq', 42, true);


--
-- Name: brain_configurations_id_seq; Type: SEQUENCE SET; Schema: brain_overlay; Owner: neondb_owner
--

SELECT pg_catalog.setval('brain_overlay.brain_configurations_id_seq', 2, true);


--
-- Name: configuration_history_id_seq; Type: SEQUENCE SET; Schema: brain_overlay; Owner: neondb_owner
--

SELECT pg_catalog.setval('brain_overlay.configuration_history_id_seq', 1, false);


--
-- Name: data_corrections_id_seq; Type: SEQUENCE SET; Schema: brain_overlay; Owner: neondb_owner
--

SELECT pg_catalog.setval('brain_overlay.data_corrections_id_seq', 1, false);


--
-- Name: data_quality_issues_id_seq; Type: SEQUENCE SET; Schema: brain_overlay; Owner: neondb_owner
--

SELECT pg_catalog.setval('brain_overlay.data_quality_issues_id_seq', 1, false);


--
-- Name: decision_traces_id_seq; Type: SEQUENCE SET; Schema: brain_overlay; Owner: neondb_owner
--

SELECT pg_catalog.setval('brain_overlay.decision_traces_id_seq', 1, false);


--
-- Name: manufacturer_selections_id_seq; Type: SEQUENCE SET; Schema: brain_overlay; Owner: neondb_owner
--

SELECT pg_catalog.setval('brain_overlay.manufacturer_selections_id_seq', 1, false);


--
-- Name: performance_analyses_id_seq; Type: SEQUENCE SET; Schema: brain_overlay; Owner: neondb_owner
--

SELECT pg_catalog.setval('brain_overlay.performance_analyses_id_seq', 1, false);


--
-- Name: selection_comparisons_id_seq; Type: SEQUENCE SET; Schema: brain_overlay; Owner: neondb_owner
--

SELECT pg_catalog.setval('brain_overlay.selection_comparisons_id_seq', 1, false);


--
-- Name: ai_prompts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.ai_prompts_id_seq', 1, false);


--
-- Name: engineering_constants_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.engineering_constants_id_seq', 9, true);


--
-- Name: extras_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.extras_id_seq', 386, true);


--
-- Name: processed_files_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.processed_files_id_seq', 386, true);


--
-- Name: pump_bep_markers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.pump_bep_markers_id_seq', 1, false);


--
-- Name: pump_curves_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.pump_curves_id_seq', 869, true);


--
-- Name: pump_diameters_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.pump_diameters_id_seq', 3072, true);


--
-- Name: pump_eff_iso_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.pump_eff_iso_id_seq', 3087, true);


--
-- Name: pump_names_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.pump_names_id_seq', 385, true);


--
-- Name: pump_performance_points_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.pump_performance_points_id_seq', 7043, true);


--
-- Name: pump_specifications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.pump_specifications_id_seq', 386, true);


--
-- Name: pump_speeds_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.pump_speeds_id_seq', 3071, true);


--
-- Name: pumps_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.pumps_id_seq', 386, true);


--
-- Name: application_profiles application_profiles_name_key; Type: CONSTRAINT; Schema: admin_config; Owner: neondb_owner
--

ALTER TABLE ONLY admin_config.application_profiles
    ADD CONSTRAINT application_profiles_name_key UNIQUE (name);


--
-- Name: application_profiles application_profiles_pkey; Type: CONSTRAINT; Schema: admin_config; Owner: neondb_owner
--

ALTER TABLE ONLY admin_config.application_profiles
    ADD CONSTRAINT application_profiles_pkey PRIMARY KEY (id);


--
-- Name: configuration_audits configuration_audits_pkey; Type: CONSTRAINT; Schema: admin_config; Owner: neondb_owner
--

ALTER TABLE ONLY admin_config.configuration_audits
    ADD CONSTRAINT configuration_audits_pkey PRIMARY KEY (id);


--
-- Name: engineering_constants engineering_constants_category_name_key; Type: CONSTRAINT; Schema: admin_config; Owner: neondb_owner
--

ALTER TABLE ONLY admin_config.engineering_constants
    ADD CONSTRAINT engineering_constants_category_name_key UNIQUE (category, name);


--
-- Name: engineering_constants engineering_constants_pkey; Type: CONSTRAINT; Schema: admin_config; Owner: neondb_owner
--

ALTER TABLE ONLY admin_config.engineering_constants
    ADD CONSTRAINT engineering_constants_pkey PRIMARY KEY (id);


--
-- Name: brain_configurations brain_configurations_pkey; Type: CONSTRAINT; Schema: brain_overlay; Owner: neondb_owner
--

ALTER TABLE ONLY brain_overlay.brain_configurations
    ADD CONSTRAINT brain_configurations_pkey PRIMARY KEY (id);


--
-- Name: brain_configurations brain_configurations_profile_name_key; Type: CONSTRAINT; Schema: brain_overlay; Owner: neondb_owner
--

ALTER TABLE ONLY brain_overlay.brain_configurations
    ADD CONSTRAINT brain_configurations_profile_name_key UNIQUE (profile_name);


--
-- Name: configuration_history configuration_history_pkey; Type: CONSTRAINT; Schema: brain_overlay; Owner: neondb_owner
--

ALTER TABLE ONLY brain_overlay.configuration_history
    ADD CONSTRAINT configuration_history_pkey PRIMARY KEY (id);


--
-- Name: data_corrections data_corrections_pkey; Type: CONSTRAINT; Schema: brain_overlay; Owner: neondb_owner
--

ALTER TABLE ONLY brain_overlay.data_corrections
    ADD CONSTRAINT data_corrections_pkey PRIMARY KEY (id);


--
-- Name: data_quality_issues data_quality_issues_pkey; Type: CONSTRAINT; Schema: brain_overlay; Owner: neondb_owner
--

ALTER TABLE ONLY brain_overlay.data_quality_issues
    ADD CONSTRAINT data_quality_issues_pkey PRIMARY KEY (id);


--
-- Name: decision_traces decision_traces_pkey; Type: CONSTRAINT; Schema: brain_overlay; Owner: neondb_owner
--

ALTER TABLE ONLY brain_overlay.decision_traces
    ADD CONSTRAINT decision_traces_pkey PRIMARY KEY (id);


--
-- Name: manufacturer_selections manufacturer_selections_pkey; Type: CONSTRAINT; Schema: brain_overlay; Owner: neondb_owner
--

ALTER TABLE ONLY brain_overlay.manufacturer_selections
    ADD CONSTRAINT manufacturer_selections_pkey PRIMARY KEY (id);


--
-- Name: performance_analyses performance_analyses_pkey; Type: CONSTRAINT; Schema: brain_overlay; Owner: neondb_owner
--

ALTER TABLE ONLY brain_overlay.performance_analyses
    ADD CONSTRAINT performance_analyses_pkey PRIMARY KEY (id);


--
-- Name: selection_comparisons selection_comparisons_pkey; Type: CONSTRAINT; Schema: brain_overlay; Owner: neondb_owner
--

ALTER TABLE ONLY brain_overlay.selection_comparisons
    ADD CONSTRAINT selection_comparisons_pkey PRIMARY KEY (id);


--
-- Name: ai_prompts ai_prompts_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.ai_prompts
    ADD CONSTRAINT ai_prompts_pkey PRIMARY KEY (id);


--
-- Name: engineering_constants engineering_constants_name_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.engineering_constants
    ADD CONSTRAINT engineering_constants_name_key UNIQUE (name);


--
-- Name: engineering_constants engineering_constants_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.engineering_constants
    ADD CONSTRAINT engineering_constants_pkey PRIMARY KEY (id);


--
-- Name: extras extras_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.extras
    ADD CONSTRAINT extras_pkey PRIMARY KEY (id);


--
-- Name: extras extras_pump_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.extras
    ADD CONSTRAINT extras_pump_id_key UNIQUE (pump_id);


--
-- Name: processed_files processed_files_filename_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.processed_files
    ADD CONSTRAINT processed_files_filename_key UNIQUE (filename);


--
-- Name: processed_files processed_files_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.processed_files
    ADD CONSTRAINT processed_files_pkey PRIMARY KEY (id);


--
-- Name: pump_bep_markers pump_bep_markers_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pump_bep_markers
    ADD CONSTRAINT pump_bep_markers_pkey PRIMARY KEY (id);


--
-- Name: pump_curves pump_curves_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pump_curves
    ADD CONSTRAINT pump_curves_pkey PRIMARY KEY (id);


--
-- Name: pump_curves pump_curves_pump_id_impeller_diameter_mm_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pump_curves
    ADD CONSTRAINT pump_curves_pump_id_impeller_diameter_mm_key UNIQUE (pump_id, impeller_diameter_mm);


--
-- Name: pump_diameters pump_diameters_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pump_diameters
    ADD CONSTRAINT pump_diameters_pkey PRIMARY KEY (id);


--
-- Name: pump_diameters pump_diameters_pump_id_sequence_order_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pump_diameters
    ADD CONSTRAINT pump_diameters_pump_id_sequence_order_key UNIQUE (pump_id, sequence_order);


--
-- Name: pump_eff_iso pump_eff_iso_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pump_eff_iso
    ADD CONSTRAINT pump_eff_iso_pkey PRIMARY KEY (id);


--
-- Name: pump_eff_iso pump_eff_iso_pump_id_sequence_order_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pump_eff_iso
    ADD CONSTRAINT pump_eff_iso_pump_id_sequence_order_key UNIQUE (pump_id, sequence_order);


--
-- Name: pump_names pump_names_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pump_names
    ADD CONSTRAINT pump_names_pkey PRIMARY KEY (id);


--
-- Name: pump_names pump_names_pump_id_sequence_order_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pump_names
    ADD CONSTRAINT pump_names_pump_id_sequence_order_key UNIQUE (pump_id, sequence_order);


--
-- Name: pump_performance_points pump_performance_points_curve_id_operating_point_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pump_performance_points
    ADD CONSTRAINT pump_performance_points_curve_id_operating_point_key UNIQUE (curve_id, operating_point);


--
-- Name: pump_performance_points pump_performance_points_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pump_performance_points
    ADD CONSTRAINT pump_performance_points_pkey PRIMARY KEY (id);


--
-- Name: pump_specifications pump_specifications_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pump_specifications
    ADD CONSTRAINT pump_specifications_pkey PRIMARY KEY (id);


--
-- Name: pump_specifications pump_specifications_pump_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pump_specifications
    ADD CONSTRAINT pump_specifications_pump_id_key UNIQUE (pump_id);


--
-- Name: pump_speeds pump_speeds_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pump_speeds
    ADD CONSTRAINT pump_speeds_pkey PRIMARY KEY (id);


--
-- Name: pump_speeds pump_speeds_pump_id_sequence_order_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pump_speeds
    ADD CONSTRAINT pump_speeds_pump_id_sequence_order_key UNIQUE (pump_id, sequence_order);


--
-- Name: pumps pumps_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pumps
    ADD CONSTRAINT pumps_pkey PRIMARY KEY (id);


--
-- Name: pumps pumps_pump_code_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pumps
    ADD CONSTRAINT pumps_pump_code_key UNIQUE (pump_code);


--
-- Name: idx_brain_config_active; Type: INDEX; Schema: brain_overlay; Owner: neondb_owner
--

CREATE INDEX idx_brain_config_active ON brain_overlay.brain_configurations USING btree (is_active);


--
-- Name: idx_brain_config_production; Type: INDEX; Schema: brain_overlay; Owner: neondb_owner
--

CREATE INDEX idx_brain_config_production ON brain_overlay.brain_configurations USING btree (is_production);


--
-- Name: idx_corrections_pump_code; Type: INDEX; Schema: brain_overlay; Owner: neondb_owner
--

CREATE INDEX idx_corrections_pump_code ON brain_overlay.data_corrections USING btree (pump_code);


--
-- Name: idx_corrections_status; Type: INDEX; Schema: brain_overlay; Owner: neondb_owner
--

CREATE INDEX idx_corrections_status ON brain_overlay.data_corrections USING btree (status);


--
-- Name: idx_corrections_type; Type: INDEX; Schema: brain_overlay; Owner: neondb_owner
--

CREATE INDEX idx_corrections_type ON brain_overlay.data_corrections USING btree (correction_type);


--
-- Name: idx_data_quality_pump_code; Type: INDEX; Schema: brain_overlay; Owner: neondb_owner
--

CREATE INDEX idx_data_quality_pump_code ON brain_overlay.data_quality_issues USING btree (pump_code);


--
-- Name: idx_data_quality_severity; Type: INDEX; Schema: brain_overlay; Owner: neondb_owner
--

CREATE INDEX idx_data_quality_severity ON brain_overlay.data_quality_issues USING btree (severity);


--
-- Name: idx_data_quality_status; Type: INDEX; Schema: brain_overlay; Owner: neondb_owner
--

CREATE INDEX idx_data_quality_status ON brain_overlay.data_quality_issues USING btree (status);


--
-- Name: idx_decision_traces_created; Type: INDEX; Schema: brain_overlay; Owner: neondb_owner
--

CREATE INDEX idx_decision_traces_created ON brain_overlay.decision_traces USING btree (created_at);


--
-- Name: idx_decision_traces_duty; Type: INDEX; Schema: brain_overlay; Owner: neondb_owner
--

CREATE INDEX idx_decision_traces_duty ON brain_overlay.decision_traces USING btree (duty_flow_m3hr, duty_head_m);


--
-- Name: idx_decision_traces_pump; Type: INDEX; Schema: brain_overlay; Owner: neondb_owner
--

CREATE INDEX idx_decision_traces_pump ON brain_overlay.decision_traces USING btree (selected_pump_code);


--
-- Name: idx_decision_traces_session; Type: INDEX; Schema: brain_overlay; Owner: neondb_owner
--

CREATE INDEX idx_decision_traces_session ON brain_overlay.decision_traces USING btree (session_id);


--
-- Name: idx_manufacturer_selections_duty; Type: INDEX; Schema: brain_overlay; Owner: neondb_owner
--

CREATE INDEX idx_manufacturer_selections_duty ON brain_overlay.manufacturer_selections USING btree (duty_flow_m3hr, duty_head_m);


--
-- Name: idx_manufacturer_selections_manufacturer; Type: INDEX; Schema: brain_overlay; Owner: neondb_owner
--

CREATE INDEX idx_manufacturer_selections_manufacturer ON brain_overlay.manufacturer_selections USING btree (manufacturer_name);


--
-- Name: idx_selection_comparisons_agreement; Type: INDEX; Schema: brain_overlay; Owner: neondb_owner
--

CREATE INDEX idx_selection_comparisons_agreement ON brain_overlay.selection_comparisons USING btree (agreement_score);


--
-- Name: idx_pump_curves_pump_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_pump_curves_pump_id ON public.pump_curves USING btree (pump_id);


--
-- Name: idx_pump_performance_points_curve_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_pump_performance_points_curve_id ON public.pump_performance_points USING btree (curve_id);


--
-- Name: idx_pump_specifications_pump_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_pump_specifications_pump_id ON public.pump_specifications USING btree (pump_id);


--
-- Name: idx_pumps_pump_code; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_pumps_pump_code ON public.pumps USING btree (pump_code);


--
-- Name: application_profiles update_application_profiles_updated_at; Type: TRIGGER; Schema: admin_config; Owner: neondb_owner
--

CREATE TRIGGER update_application_profiles_updated_at BEFORE UPDATE ON admin_config.application_profiles FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: configuration_audits configuration_audits_profile_id_fkey; Type: FK CONSTRAINT; Schema: admin_config; Owner: neondb_owner
--

ALTER TABLE ONLY admin_config.configuration_audits
    ADD CONSTRAINT configuration_audits_profile_id_fkey FOREIGN KEY (profile_id) REFERENCES admin_config.application_profiles(id);


--
-- Name: configuration_history configuration_history_configuration_id_fkey; Type: FK CONSTRAINT; Schema: brain_overlay; Owner: neondb_owner
--

ALTER TABLE ONLY brain_overlay.configuration_history
    ADD CONSTRAINT configuration_history_configuration_id_fkey FOREIGN KEY (configuration_id) REFERENCES brain_overlay.brain_configurations(id);


--
-- Name: data_corrections data_corrections_pump_id_fkey; Type: FK CONSTRAINT; Schema: brain_overlay; Owner: neondb_owner
--

ALTER TABLE ONLY brain_overlay.data_corrections
    ADD CONSTRAINT data_corrections_pump_id_fkey FOREIGN KEY (pump_id) REFERENCES public.pumps(id);


--
-- Name: data_corrections data_corrections_related_issue_id_fkey; Type: FK CONSTRAINT; Schema: brain_overlay; Owner: neondb_owner
--

ALTER TABLE ONLY brain_overlay.data_corrections
    ADD CONSTRAINT data_corrections_related_issue_id_fkey FOREIGN KEY (related_issue_id) REFERENCES brain_overlay.data_quality_issues(id);


--
-- Name: data_quality_issues data_quality_issues_pump_id_fkey; Type: FK CONSTRAINT; Schema: brain_overlay; Owner: neondb_owner
--

ALTER TABLE ONLY brain_overlay.data_quality_issues
    ADD CONSTRAINT data_quality_issues_pump_id_fkey FOREIGN KEY (pump_id) REFERENCES public.pumps(id);


--
-- Name: decision_traces decision_traces_brain_config_id_fkey; Type: FK CONSTRAINT; Schema: brain_overlay; Owner: neondb_owner
--

ALTER TABLE ONLY brain_overlay.decision_traces
    ADD CONSTRAINT decision_traces_brain_config_id_fkey FOREIGN KEY (brain_config_id) REFERENCES brain_overlay.brain_configurations(id);


--
-- Name: performance_analyses performance_analyses_decision_trace_id_fkey; Type: FK CONSTRAINT; Schema: brain_overlay; Owner: neondb_owner
--

ALTER TABLE ONLY brain_overlay.performance_analyses
    ADD CONSTRAINT performance_analyses_decision_trace_id_fkey FOREIGN KEY (decision_trace_id) REFERENCES brain_overlay.decision_traces(id);


--
-- Name: selection_comparisons selection_comparisons_brain_decision_trace_id_fkey; Type: FK CONSTRAINT; Schema: brain_overlay; Owner: neondb_owner
--

ALTER TABLE ONLY brain_overlay.selection_comparisons
    ADD CONSTRAINT selection_comparisons_brain_decision_trace_id_fkey FOREIGN KEY (brain_decision_trace_id) REFERENCES brain_overlay.decision_traces(id);


--
-- Name: selection_comparisons selection_comparisons_manufacturer_selection_id_fkey; Type: FK CONSTRAINT; Schema: brain_overlay; Owner: neondb_owner
--

ALTER TABLE ONLY brain_overlay.selection_comparisons
    ADD CONSTRAINT selection_comparisons_manufacturer_selection_id_fkey FOREIGN KEY (manufacturer_selection_id) REFERENCES brain_overlay.manufacturer_selections(id);


--
-- Name: extras extras_pump_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.extras
    ADD CONSTRAINT extras_pump_id_fkey FOREIGN KEY (pump_id) REFERENCES public.pumps(id) ON DELETE CASCADE;


--
-- Name: pump_bep_markers pump_bep_markers_pump_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pump_bep_markers
    ADD CONSTRAINT pump_bep_markers_pump_id_fkey FOREIGN KEY (pump_id) REFERENCES public.pumps(id) ON DELETE CASCADE;


--
-- Name: pump_curves pump_curves_pump_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pump_curves
    ADD CONSTRAINT pump_curves_pump_id_fkey FOREIGN KEY (pump_id) REFERENCES public.pumps(id) ON DELETE CASCADE;


--
-- Name: pump_diameters pump_diameters_pump_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pump_diameters
    ADD CONSTRAINT pump_diameters_pump_id_fkey FOREIGN KEY (pump_id) REFERENCES public.pumps(id) ON DELETE CASCADE;


--
-- Name: pump_eff_iso pump_eff_iso_pump_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pump_eff_iso
    ADD CONSTRAINT pump_eff_iso_pump_id_fkey FOREIGN KEY (pump_id) REFERENCES public.pumps(id) ON DELETE CASCADE;


--
-- Name: pump_names pump_names_pump_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pump_names
    ADD CONSTRAINT pump_names_pump_id_fkey FOREIGN KEY (pump_id) REFERENCES public.pumps(id) ON DELETE CASCADE;


--
-- Name: pump_performance_points pump_performance_points_curve_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pump_performance_points
    ADD CONSTRAINT pump_performance_points_curve_id_fkey FOREIGN KEY (curve_id) REFERENCES public.pump_curves(id) ON DELETE CASCADE;


--
-- Name: pump_specifications pump_specifications_pump_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pump_specifications
    ADD CONSTRAINT pump_specifications_pump_id_fkey FOREIGN KEY (pump_id) REFERENCES public.pumps(id) ON DELETE CASCADE;


--
-- Name: pump_speeds pump_speeds_pump_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.pump_speeds
    ADD CONSTRAINT pump_speeds_pump_id_fkey FOREIGN KEY (pump_id) REFERENCES public.pumps(id) ON DELETE CASCADE;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: public; Owner: cloud_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE cloud_admin IN SCHEMA public GRANT ALL ON SEQUENCES TO neon_superuser WITH GRANT OPTION;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: cloud_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE cloud_admin IN SCHEMA public GRANT ALL ON TABLES TO neon_superuser WITH GRANT OPTION;


--
-- PostgreSQL database dump complete
--

