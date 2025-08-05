"""
Reports Routes
Routes for pump reports and PDF generation
"""
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, make_response, Response
from ..session_manager import safe_flash, safe_session_get, safe_session_set, safe_session_pop, safe_session_clear, get_form_data, store_form_data
from ..data_models import SiteRequirements
from ..pump_repository import load_all_pump_data
from ..utils import validate_site_requirements
from .. import app

logger = logging.getLogger(__name__)

# Create blueprint
reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/pump_report', methods=['POST'])
def pump_report_post():
    """Handle POST requests for pump reports."""
    try:
        pump_code = request.form.get('pump_code')
        if not pump_code:
            safe_flash('Pump code is required.', 'error')
            return redirect(url_for('main_flow.index'))

        return redirect(url_for('reports.pump_report', pump_code=pump_code))

    except Exception as e:
        logger.error(f"Error in pump_report_post: {str(e)}")
        safe_flash('An error occurred processing your request.', 'error')
        return redirect(url_for('main_flow.index'))

@reports_bp.route('/pump_report/<path:pump_code>')
def pump_report(pump_code):
    """Display comprehensive pump selection report (modern UI)."""
    try:
        from urllib.parse import unquote
        pump_code = unquote(pump_code)

        # Get stored results from session with validation
        pump_selections = session.get('pump_selections', [])
        site_requirements_data = session.get('site_requirements', {})
        exclusion_data = session.get('exclusion_data', None)

        # Validate session data integrity
        if pump_selections and not isinstance(pump_selections, list):
            logger.warning("Invalid pump_selections data in session, resetting")
            pump_selections = []
        if site_requirements_data and not isinstance(site_requirements_data, dict):
            logger.warning("Invalid site_requirements data in session, resetting")
            site_requirements_data = {}

        # If no session data, regenerate from URL parameters using catalog engine
        if not pump_selections:
            flow = request.args.get('flow', type=float)
            head = request.args.get('head', type=float)
            if not flow or not head:
                safe_flash('Flow and head parameters are required for pump analysis.', 'error')
                return redirect(url_for('main_flow.index'))
            from ..catalog_engine import get_catalog_engine
            catalog_engine = get_catalog_engine()
            try:
                site_requirements_data = {
                    'flow_m3hr': flow,
                    'head_m': head,
                    'pump_type': request.args.get('pump_type', 'General'),
                    'customer_name': request.args.get('customer', ''),
                    'project_name': request.args.get('project', ''),
                }
                
                # Generate exclusion data when regenerating from URL parameters
                if not exclusion_data:
                    pump_type = request.args.get('pump_type', 'General')
                    selection_data = catalog_engine.select_pumps(
                        flow_m3hr=flow, 
                        head_m=head, 
                        max_results=10, 
                        pump_type=pump_type, 
                        return_exclusions=True
                    )
                    
                    if isinstance(selection_data, dict):
                        exclusion_data = {
                            'excluded_pumps': selection_data.get('excluded_pumps', []),
                            'exclusion_summary': selection_data.get('exclusion_summary', {}),
                            'total_evaluated': selection_data.get('total_evaluated', 0),
                            'feasible_count': selection_data.get('feasible_count', 0),
                            'excluded_count': selection_data.get('excluded_count', 0)
                        }
                        # Use the selection results for pump_selections if not already set
                        if 'suitable_pumps' in selection_data:
                            pump_selections = selection_data['suitable_pumps']
                
                target_pump = catalog_engine.get_pump_by_code(pump_code)
                if target_pump and not pump_selections:
                    performance = target_pump.get_performance_at_duty(flow, head)
                    if performance:
                        # Calculate proper suitability score to match catalog engine scoring
                        efficiency_pct = performance.get('efficiency_pct', 0)
                        efficiency_score = min(efficiency_pct, 80)  # Max 80 points for efficiency
                        bep_score = 15  # Default BEP proximity score
                        head_margin_bonus = 20 if performance.get('head_m', 0) >= head else 0
                        raw_suitability_score = efficiency_score + bep_score + head_margin_bonus
                        # Normalize to 0-100% scale (115 is the maximum possible score)
                        suitability_score = min(100.0, (raw_suitability_score / 115.0) * 100.0)

                        pump_selections = [{
                            'pump_code': pump_code,
                            'overall_score': suitability_score,
                            'efficiency_at_duty': efficiency_pct,
                            'operating_point': performance,
                            'suitable': efficiency_pct > 40,
                            'manufacturer': target_pump.manufacturer,
                            'pump_type': target_pump.pump_type,
                            'test_speed_rpm': performance.get('test_speed_rpm', 1480),
                            'stages': '1'
                        }]
                    else:
                        pump_selections = []
                else:
                    pump_selections = []
            except Exception as e:
                logger.warning(f"Catalog pump evaluation failed: {e}")
                pump_selections = []

        # Find the selected pump in results
        selected_pump = None
        for selection in pump_selections:
            if selection.get('pump_code') == pump_code:
                selected_pump = selection
                # Ensure scoring_details is available if not already present
                if 'scoring_details' not in selected_pump and selected_pump.get('operating_point'):
                    # Generate scoring details for display
                    performance = selected_pump['operating_point']
                    efficiency = selected_pump.get('efficiency_at_duty', 0)
                    selected_pump['scoring_details'] = {
                        'qbp_proximity': {
                            'score': selected_pump.get('bep_score', 0),
                            'description': 'Best Efficiency Point proximity',
                            'formula': '40 × max(0, 1 - ((flow_ratio - 1) / 0.5)²)'
                        },
                        'efficiency': {
                            'score': selected_pump.get('efficiency_score', 0),
                            'description': f"Efficiency at duty point: {efficiency:.1f}%",
                            'formula': '(efficiency/100)² × 30'
                        },
                        'head_margin': {
                            'score': selected_pump.get('margin_score', 0),
                            'description': f"Head margin: {selected_pump.get('head_margin_pct', 0):.1f}%",
                            'formula': 'Graduated scoring based on margin percentage'
                        },
                        'npsh': {
                            'score': selected_pump.get('npsh_score', 0),
                            'description': f"NPSHr: {performance.get('npshr_m', 'N/A'):.1f}m" if performance.get('npshr_m') else "No NPSH data",
                            'formula': '15 × max(0, (8 - NPSHr) / 6)' if performance.get('npshr_m') else 'N/A'
                        },
                        'speed_penalty': {
                            'score': 0,
                            'description': "No speed variation",
                            'formula': '1.5 × speed_change_% (max -15)'
                        },
                        'trim_penalty': {
                            'score': 0,
                            'description': "No trimming",
                            'formula': '0.5 × trim_%'
                        }
                    }
                break

        # If pump not found in session data, force regenerate with specific pump
        if not selected_pump:
            flow = request.args.get('flow', 1600.0, type=float)
            head = request.args.get('head', 10.3, type=float)
            pump_type = request.args.get('pump_type', 'AXIAL_FLOW')
            from ..catalog_engine import get_catalog_engine
            catalog_engine = get_catalog_engine()
            target_pump = catalog_engine.get_pump_by_code(pump_code)
            if target_pump:
                performance = target_pump.get_performance_at_duty(flow, head)
                if performance:
                    # Calculate proper suitability score to match catalog engine scoring
                    efficiency_pct = performance.get('efficiency_pct', 0)
                    efficiency_score = min(efficiency_pct, 80)  # Max 80 points for efficiency
                    bep_score = 15  # Default BEP proximity score
                    head_margin_bonus = 20 if performance.get('head_m', 0) >= head else 0
                    raw_suitability_score = efficiency_score + bep_score + head_margin_bonus
                    # Normalize to 0-100% scale (115 is the maximum possible score)
                    suitability_score = min(100.0, (raw_suitability_score / 115.0) * 100.0)

                    selected_pump = {
                        'pump_code': pump_code,
                        'overall_score': suitability_score,
                        'efficiency_at_duty': efficiency_pct,
                        'operating_point': performance,
                        'suitable': efficiency_pct > 40,
                        'manufacturer': target_pump.manufacturer,
                        'pump_type': target_pump.pump_type,
                        'test_speed_rpm': performance.get('test_speed_rpm', 1480),
                        'stages': '1'
                    }
                    site_requirements_data = {
                        'flow_m3hr': flow,
                        'head_m': head,
                        'pump_type': pump_type
                    }
                    pump_selections = [selected_pump]

        # Check if this is a direct search to determine validation behavior
        direct_search = request.args.get('direct_search', 'false').lower() == 'true'
        
        # CRITICAL FIX: Direct search should NEVER redirect away - always show analysis
        if not selected_pump:
            if direct_search:
                # For direct searches, try to force analysis even if pump not initially found
                flow = request.args.get('flow', 200.0, type=float)
                head = request.args.get('head', 10.0, type=float)
                pump_type = request.args.get('pump_type', 'GENERAL')
                
                # Force refresh catalog engine to ensure data sync
                from ..catalog_engine import get_catalog_engine
                catalog_engine = get_catalog_engine()
                catalog_engine.load_catalog()  # Force reload to sync with database
                
                # Try again with refreshed catalog
                target_pump = catalog_engine.get_pump_by_code(pump_code)
                if target_pump:
                    logger.info(f"Direct search: Found pump {pump_code} after catalog refresh")
                    # Force performance calculation at any operating point
                    performance = target_pump.get_performance_at_duty(flow, head)
                    if not performance:
                        # If no performance at exact duty, find ANY performance point to analyze
                        performance = target_pump.get_any_performance_point(flow, head)
                    
                    if performance:
                        # Calculate suitability score even for poor performance
                        efficiency_pct = performance.get('efficiency_pct', 0)
                        efficiency_score = min(efficiency_pct, 80)
                        bep_score = 15  # Default BEP proximity score
                        head_margin_bonus = 20 if performance.get('head_m', 0) >= head else 0
                        raw_suitability_score = efficiency_score + bep_score + head_margin_bonus
                        suitability_score = min(100.0, (raw_suitability_score / 115.0) * 100.0)

                        selected_pump = {
                            'pump_code': pump_code,
                            'overall_score': suitability_score,
                            'efficiency_at_duty': efficiency_pct,
                            'operating_point': performance,
                            'suitable': efficiency_pct > 20,  # Lower threshold for direct search
                            'manufacturer': target_pump.manufacturer,
                            'pump_type': target_pump.pump_type,
                            'test_speed_rpm': performance.get('test_speed_rpm', 1480),
                            'stages': '1',
                            'forced_analysis': True,  # Flag to indicate this is forced analysis
                            'warnings': []  # Initialize warnings list
                        }
                        
                        # Add warnings for off-BEP operation
                        bep_point = target_pump.get_bep_point()
                        if bep_point:
                            bep_flow = bep_point['flow_m3hr']
                            bep_head = bep_point['head_m']
                            flow_deviation = abs((flow - bep_flow) / bep_flow * 100) if bep_flow > 0 else 0
                            head_deviation = abs((head - bep_head) / bep_head * 100) if bep_head > 0 else 0
                            
                            if flow_deviation > 15:
                                selected_pump['warnings'].append(f"Operating flow ({flow:.1f} m³/h) deviates {flow_deviation:.1f}% from BEP flow ({bep_flow:.1f} m³/h)")
                            if head_deviation > 15:
                                selected_pump['warnings'].append(f"Operating head ({head:.1f} m) deviates {head_deviation:.1f}% from BEP head ({bep_head:.1f} m)")
                            if efficiency_pct < 60:
                                selected_pump['warnings'].append(f"Low efficiency ({efficiency_pct:.1f}%) at specified operating point")
                        
                        site_requirements_data = {
                            'flow_m3hr': flow,
                            'head_m': head,
                            'pump_type': pump_type,
                            'direct_search': True
                        }
                        pump_selections = [selected_pump]
                        safe_flash(f'Direct search analysis for pump "{pump_code}" - Review warnings below', 'warning')
                    else:
                        # Create minimal analysis even if no performance calculation possible
                        selected_pump = {
                            'pump_code': pump_code,
                            'overall_score': 0,
                            'efficiency_at_duty': 0,
                            'operating_point': {'flow_m3hr': flow, 'head_m': 0, 'efficiency_pct': 0, 'power_kw': 0},
                            'suitable': False,
                            'manufacturer': target_pump.manufacturer,
                            'pump_type': target_pump.pump_type,
                            'test_speed_rpm': 1480,
                            'stages': '1',
                            'forced_analysis': True,
                            'warnings': ['Unable to calculate performance at specified operating point', 'Pump may not be suitable for this application']
                        }
                        site_requirements_data = {
                            'flow_m3hr': flow,
                            'head_m': head,
                            'pump_type': pump_type,
                            'direct_search': True
                        }
                        pump_selections = [selected_pump]
                        safe_flash(f'Pump "{pump_code}" found but performance cannot be calculated at {flow} m³/h, {head} m head', 'error')
                else:
                    # Pump truly not found - create error analysis
                    selected_pump = {
                        'pump_code': pump_code,
                        'overall_score': 0,
                        'efficiency_at_duty': 0,
                        'operating_point': {'flow_m3hr': flow, 'head_m': 0, 'efficiency_pct': 0, 'power_kw': 0},
                        'suitable': False,
                        'manufacturer': 'Unknown',
                        'pump_type': 'Unknown',
                        'test_speed_rpm': 0,
                        'stages': '1',
                        'forced_analysis': True,
                        'warnings': [f'Pump model "{pump_code}" not found in database', 'Please verify the pump model name and try again']
                    }
                    site_requirements_data = {
                        'flow_m3hr': flow,
                        'head_m': head,
                        'pump_type': pump_type,
                        'direct_search': True
                    }
                    pump_selections = [selected_pump]
                    safe_flash(f'Pump "{pump_code}" not found in database. Showing error analysis.', 'error')
            else:
                # For algorithm selections, this shouldn't happen, so redirect
                safe_flash('Selected pump not found or cannot meet requirements. Please start a new selection.', 'warning')
                return redirect(url_for('main_flow.index'))

        logger.info(f"Displaying report for pump: {pump_code}")

        # Get complete pump data with curves for data table
        from ..catalog_engine import get_catalog_engine
        catalog_engine = get_catalog_engine()
        catalog_pump = catalog_engine.get_pump_by_code(pump_code)
        if catalog_pump:
            selected_pump['curves'] = catalog_pump.curves
            selected_pump['pump_type'] = catalog_pump.pump_type
            selected_pump['manufacturer'] = catalog_pump.manufacturer

        # Generate alternative pumps using catalog engine
        alternatives = []
        try:
            flow = site_requirements_data.get('flow_m3hr', 0)
            head = site_requirements_data.get('head_m', 0)
            pump_type = site_requirements_data.get('pump_type', 'General')
            direct_search = request.args.get('direct_search', 'false').lower() == 'true'

            if flow and head:
                from ..catalog_engine import get_catalog_engine
                catalog_engine = get_catalog_engine()

                # Handle direct pump search with enhanced validation
                if direct_search:
                    # Phase 1: Find and validate the directly selected pump
                    target_pump = None
                    search_code = pump_code.lower().strip()

                    # Enhanced search logic with better matching for pump codes like "28 HC 6P"
                    best_match = None
                    best_match_score = 0
                    
                    for pump in catalog_engine.pumps:
                        pump_code_lower = pump.pump_code.lower().strip()
                        
                        # Try exact match first (highest priority)
                        if pump_code_lower == search_code:
                            target_pump = pump
                            logger.info(f"Direct search: Found exact match '{pump.pump_code}' for search '{pump_code}'")
                            break
                        
                        # Calculate similarity score for fuzzy matching
                        match_score = 0
                        
                        # Method 1: Direct substring matching
                        if search_code in pump_code_lower:
                            match_score += 80
                        elif pump_code_lower in search_code:
                            match_score += 70
                        
                        # Method 2: Normalized matching (remove spaces, hyphens, slashes, underscores)
                        normalized_search = search_code.replace('/', '').replace('-', '').replace(' ', '').replace('_', '').replace('.', '')
                        normalized_pump = pump_code_lower.replace('/', '').replace('-', '').replace(' ', '').replace('_', '').replace('.', '')
                        
                        if normalized_search == normalized_pump:
                            match_score += 100  # Perfect normalized match
                        elif normalized_search in normalized_pump:
                            match_score += 90   # Partial normalized match
                        elif normalized_pump in normalized_search:
                            match_score += 85   # Reverse partial match
                        
                        # Method 3: Word-by-word matching with fuzzy tolerance
                        search_words = [w for w in search_code.split() if len(w) > 0]
                        pump_words = [w for w in pump_code_lower.split() if len(w) > 0]
                        
                        word_matches = 0
                        for search_word in search_words:
                            for pump_word in pump_words:
                                # Exact word match
                                if search_word == pump_word:
                                    word_matches += 2
                                # Partial word match
                                elif search_word in pump_word or pump_word in search_word:
                                    word_matches += 1
                                # Handle common variations (e.g., "6P" vs "6")
                                elif len(search_word) > 1 and len(pump_word) > 1:
                                    if search_word[:-1] == pump_word or pump_word[:-1] == search_word:
                                        word_matches += 1
                        
                        if word_matches > 0:
                            match_score += word_matches * 15
                        
                        # Method 4: Handle common pump code patterns (e.g., "28 HC 6P" should match "28HC6P")
                        # Create compact versions for pattern matching
                        compact_search = ''.join(search_code.split())
                        compact_pump = ''.join(pump_code_lower.split())
                        
                        if compact_search == compact_pump:
                            match_score += 95
                        elif compact_search in compact_pump or compact_pump in compact_search:
                            match_score += 75
                        
                        # Method 5: Character-level similarity for very close matches
                        if len(search_code) > 2 and len(pump_code_lower) > 2:
                            common_chars = sum(1 for char in search_code if char in pump_code_lower)
                            char_similarity = (common_chars / max(len(search_code), len(pump_code_lower))) * 100
                            if char_similarity > 70:
                                match_score += int(char_similarity * 0.3)
                        
                        # Bonus for starts-with matching
                        if pump_code_lower.startswith(search_code[:3]) or search_code.startswith(pump_code_lower[:3]):
                            match_score += 10
                        
                        # Update best match if this is better (lowered threshold to 40)
                        if match_score > best_match_score and match_score >= 40:
                            best_match = pump
                            best_match_score = match_score
                    
                    # Use best match if no exact match found
                    if not target_pump and best_match:
                        target_pump = best_match
                        logger.info(f"Direct search: Found fuzzy match '{best_match.pump_code}' (score: {best_match_score}) for search '{pump_code}'")

                    if not target_pump:
                        # Enhanced debugging - show pumps that start with similar patterns
                        search_prefix = pump_code.split()[0] if ' ' in pump_code else pump_code[:3]
                        similar_pumps = [p.pump_code for p in catalog_engine.pumps if p.pump_code.lower().startswith(search_prefix.lower())][:10]
                        
                        # Additional debugging - look for pumps containing key parts
                        search_parts = [part.lower() for part in pump_code.split() if len(part) > 0]
                        partial_matches = []
                        for pump in catalog_engine.pumps[:50]:  # Check first 50 pumps
                            pump_code_lower = pump.pump_code.lower()
                            if any(part in pump_code_lower for part in search_parts):
                                partial_matches.append(pump.pump_code)
                        
                        # Look for pumps with similar patterns
                        pattern_matches = []
                        normalized_search = pump_code.replace(' ', '').replace('-', '').lower()
                        for pump in catalog_engine.pumps[:100]:  # Check first 100 pumps
                            normalized_pump = pump.pump_code.replace(' ', '').replace('-', '').lower()
                            if normalized_search in normalized_pump or normalized_pump in normalized_search:
                                pattern_matches.append(pump.pump_code)
                        
                        logger.error(f"Direct search failed for pump code: '{pump_code}'")
                        logger.error(f"Search parts: {search_parts}")
                        logger.error(f"Pumps starting with '{search_prefix}': {similar_pumps}")
                        logger.error(f"Partial matches (contains search parts): {partial_matches[:10]}")
                        logger.error(f"Pattern matches (normalized): {pattern_matches[:10]}")
                        logger.error(f"Total pumps in catalog: {len(catalog_engine.pumps)}")
                        logger.error(f"Sample pump codes: {[p.pump_code for p in catalog_engine.pumps[:20]]}")
                        
                        # Show the best scoring pump even if it didn't meet threshold
                        if best_match:
                            logger.error(f"Best match found: '{best_match.pump_code}' (score: {best_match_score}, threshold: 40)")
                        
                        safe_flash(f'Pump "{pump_code}" not found in database. Please check the model name and try again.', 'error')
                        return redirect(url_for('main_flow.index'))

                    # Phase 2: Run algorithm comparison in background for validation
                    logger.info(f"Direct search: Running background optimization for comparison")
                    optimal_selections = catalog_engine.select_pumps(
                        flow_m3hr=flow,
                        head_m=head,
                        max_results=5,
                        pump_type=pump_type
                    )

                    # Calculate performance for the direct search pump with FORCED ANALYSIS
                    try:
                        # Try normal performance calculation first
                        performance_result = target_pump.get_performance_at_duty(flow, head)

                        if not performance_result or performance_result.get('error'):
                            # FORCE ANALYSIS: Try forced performance calculation for ANY operating point
                            logger.info(f"Normal performance calculation failed for {pump_code}, forcing analysis at ANY operating point")
                            performance_result = target_pump.get_any_performance_point(flow, head)

                        if performance_result:
                            operating_point = performance_result
                            suitable_pumps = [target_pump]
                            
                            # Performance validation checks
                            efficiency = performance_result.get('efficiency_pct', 0)
                            power_kw = performance_result.get('power_kw', 0)
                            head_delivered = performance_result.get('head_m', 0)
                            
                            # Check if pump operates in reasonable efficiency range
                            is_efficient = efficiency >= 50  # Minimum acceptable efficiency
                            is_very_efficient = efficiency >= 70  # Good efficiency
                            
                            # Check if selection is in top optimal choices
                            is_optimal_choice = any(opt.get('pump_code') == target_pump.pump_code for opt in optimal_selections)
                            
                            # Calculate rank against optimal selections
                            optimal_rank = None
                            for i, opt in enumerate(optimal_selections):
                                if opt.get('pump_code') == target_pump.pump_code:
                                    optimal_rank = i + 1
                                    break
                            
                            # Generate warnings for forced analysis
                            warnings = []
                            if performance_result.get('extrapolated'):
                                warnings.append("Performance extrapolated beyond normal operating range")
                            if performance_result.get('calculation_error'):
                                warnings.append("Performance calculation encountered errors")
                            if efficiency < 40:
                                warnings.append(f"Very low efficiency ({efficiency:.1f}%) at specified operating point")
                            if head_delivered < head * 0.9:  # Less than 90% of required head
                                warnings.append(f"Pump delivers {head_delivered:.1f}m but {head:.1f}m required")
                            if not is_optimal_choice and optimal_selections:
                                best_alt = optimal_selections[0]
                                best_efficiency = best_alt.get('efficiency_pct', 0)
                                if best_efficiency > efficiency + 15:  # 15% efficiency difference
                                    warnings.append(f"Alternative pump {best_alt.get('pump_code')} offers {best_efficiency:.1f}% efficiency vs {efficiency:.1f}%")
                            
                            # Store validation data for warning banner
                            validation_data = {
                                'is_direct_selection': True,
                                'forced_analysis': bool(warnings),
                                'warnings': warnings,
                                'efficiency_pct': efficiency,
                                'is_efficient': is_efficient,
                                'is_very_efficient': is_very_efficient,
                                'is_optimal_choice': is_optimal_choice,
                                'optimal_rank': optimal_rank,
                                'optimal_selections_count': len(optimal_selections),
                                'best_alternative': optimal_selections[0] if optimal_selections else None,
                                'efficiency_difference': None,
                                'power_difference': None
                            }
                            
                            # Calculate performance differences if alternatives exist
                            if optimal_selections:
                                best_alt = optimal_selections[0]
                                best_alt_efficiency = best_alt.get('efficiency_pct', 0)
                                best_alt_power = best_alt.get('operating_point', {}).get('power_kw', 0)
                                
                                validation_data['efficiency_difference'] = efficiency - best_alt_efficiency
                                validation_data['power_difference'] = power_kw - best_alt_power
                                validation_data['best_alternative_code'] = best_alt.get('pump_code')
                                validation_data['best_alternative_efficiency'] = best_alt_efficiency
                            
                            # Store validation data globally for context use
                            globals()['current_validation_data'] = validation_data
                            
                            logger.info(f"Direct search successful for pump: {pump_code}")
                            logger.info(f"Direct selection validation: efficiency={efficiency}%, optimal_rank={optimal_rank}, is_optimal={is_optimal_choice}")
                            if warnings:
                                logger.warning(f"Direct search warnings for {pump_code}: {', '.join(warnings)}")
                            
                        else:
                            # Even forced analysis failed - create minimal error analysis
                            logger.error(f"Both normal and forced performance calculation failed for pump: {pump_code}")
                            
                            # Create minimal analysis to show something to user
                            performance_result = {
                                'flow_m3hr': flow,
                                'head_m': 0,
                                'efficiency_pct': 0,
                                'power_kw': 0,
                                'npshr_m': 0,
                                'calculation_error': True
                            }
                            operating_point = performance_result
                            suitable_pumps = [target_pump]
                            
                            warnings = [
                                "Unable to calculate performance at specified operating point",
                                "Pump may not be suitable for this application",
                                "Consider alternative pump models or operating conditions"
                            ]
                            
                            validation_data = {
                                'is_direct_selection': True,
                                'forced_analysis': True,
                                'warnings': warnings,
                                'efficiency_pct': 0,
                                'is_efficient': False,
                                'is_very_efficient': False,
                                'is_optimal_choice': False,
                                'optimal_rank': None,
                                'optimal_selections_count': len(optimal_selections),
                                'best_alternative': optimal_selections[0] if optimal_selections else None
                            }
                            
                            globals()['current_validation_data'] = validation_data
                            logger.warning(f"Created minimal error analysis for {pump_code}")

                    except Exception as e:
                        logger.error(f"Error in direct search analysis for pump {pump_code}: {str(e)}")
                        
                        # Even exception handling - create basic error analysis
                        performance_result = {
                            'flow_m3hr': flow,
                            'head_m': 0,
                            'efficiency_pct': 0,
                            'power_kw': 0,
                            'npshr_m': 0,
                            'calculation_error': True
                        }
                        operating_point = performance_result
                        suitable_pumps = [target_pump]
                        
                        warnings = [
                            f"Analysis error: {str(e)[:100]}",
                            "Unable to calculate pump performance",
                            "Please verify pump model and operating conditions"
                        ]
                        
                        validation_data = {
                            'is_direct_selection': True,
                            'forced_analysis': True,
                            'warnings': warnings,
                            'efficiency_pct': 0,
                            'calculation_error': True
                        }
                        
                        globals()['current_validation_data'] = validation_data
                        logger.warning(f"Exception-based error analysis created for {pump_code}")
                else:
                    # Normal pump selection process
                    alternative_selections = catalog_engine.select_pumps(
                        flow_m3hr=flow,
                        head_m=head,
                        max_results=5,
                        pump_type=pump_type
                    )

                    # Filter out the selected pump and create alternative data
                    for alt_pump in alternative_selections:
                        if alt_pump.get('pump_code') != pump_code:
                            # Normalize alternative pump score to 0-100% scale
                            raw_alt_score = alt_pump.get('overall_score', 0)
                            normalized_alt_score = min(100.0, (raw_alt_score / 115.0) * 100.0)

                            alternatives.append({
                                'pump_code': alt_pump.get('pump_code'),
                                'overall_score': normalized_alt_score,
                                'efficiency_at_duty': alt_pump.get('efficiency_pct', 0),
                                'operating_point': alt_pump.get('operating_point', {}),
                                'suitable': alt_pump.get('efficiency_pct', 0) > 40,
                                'manufacturer': alt_pump.get('manufacturer', 'APE PUMPS'),
                                'pump_type': alt_pump.get('pump_type', 'Centrifugal'),
                                'test_speed_rpm': alt_pump.get('test_speed_rpm', 1480),
                                'stages': '1'
                            })

                            # Limit to 3 alternatives
                            if len(alternatives) >= 3:
                                break
        except Exception as e:
            logger.warning(f"Failed to generate alternatives: {e}")
            alternatives = []

        # Check if this is a direct selection for validation data
        direct_search = request.args.get('direct_search', 'false').lower() == 'true'
        validation_data = None
        
        if direct_search and 'current_validation_data' in globals():
            validation_data = globals().get('current_validation_data')
            # Clear the global variable after use
            globals().pop('current_validation_data', None)

        context_data = {
            'pump_selections': pump_selections,
            'selected_pump': selected_pump,
            'alternatives': alternatives,
            'site_requirements': {
                'flow_m3hr': site_requirements_data.get('flow_m3hr', 0),
                'head_m': site_requirements_data.get('head_m', 0),
                'pump_type': site_requirements_data.get('pump_type', 'General'),
                'customer_name': site_requirements_data.get('customer_name', 'Client Contact'),
                'project_name': site_requirements_data.get('project_name', 'Water Supply System Project'),
                'application': site_requirements_data.get('application', 'Water Supply'),
                'fluid_type': site_requirements_data.get('fluid_type', 'Water')
            },
            'selected_pump_code': pump_code,
            'current_date': __import__('datetime').datetime.now().strftime('%Y-%m-%d'),
            'direct_selection_validation': validation_data,
            'exclusion_data': exclusion_data  # Add exclusion data for transparency
        }

        # Ensure selected_curve data is available for all pumps
        if selected_pump and isinstance(selected_pump, dict):
            op_point = selected_pump.get('operating_point', {})
            impeller_diameter = op_point.get('impeller_diameter_mm', op_point.get('impeller_size', 501.0))
            selected_pump['selected_curve'] = {
                'impeller_size': impeller_diameter,
                'impeller_diameter_mm': impeller_diameter,
                'is_selected': True,
                'curve_index': op_point.get('curve_index', 0)
            }
            
            # Add validation data warnings to selected_pump for template access
            if validation_data and validation_data.get('warnings'):
                selected_pump['forced_analysis'] = validation_data.get('forced_analysis', False)
                selected_pump['warnings'] = validation_data.get('warnings', [])
            if 'pump_info' not in selected_pump:
                selected_pump['pump_info'] = {
                    'pPumpCode': pump_code,
                    'pSuppName': 'APE PUMPS',
                    'pPumpTestSpeed': '1480',
                    'pFilter1': 'APE PUMPS',
                    'pStages': '1'
                }
            logger.info(f"Template data - selected_pump operating_point: {selected_pump.get('operating_point')}")
            logger.info(f"Template data - selected_pump selected_curve: {selected_pump.get('selected_curve')}")



        return render_template('professional_pump_report.html', **context_data)

    except Exception as e:
        logger.error(f"Error displaying pump report: {str(e)}", exc_info=True)
        safe_flash('Error loading pump report. Please try again.', 'error')
        return redirect(url_for('main_flow.index'))

@reports_bp.route('/professional_pump_report/<path:pump_code>')
def professional_pump_report(pump_code):
    """Generate professional pump report."""
    return pump_report(pump_code)

@reports_bp.route('/generate_pdf/<path:pump_code>')
def generate_pdf(pump_code):  # Renamed to match template usage
    """Generate PDF report using URL parameters instead of session data"""
    try:
        # URL decode the pump code to handle special characters
        from urllib.parse import unquote
        pump_code = unquote(pump_code)

        logger.info(f"PDF generation requested for pump: {pump_code}")

        # Get parameters from URL instead of session
        flow = request.args.get('flow', type=float)
        head = request.args.get('head', type=float)

        if not flow or not head:
            logger.error(f"PDF generation - Missing flow or head parameters")
            safe_flash('Flow and head parameters are required for PDF generation.', 'error')
            return redirect(url_for('main_flow.index'))

        logger.info(f"PDF generation - Parameters: flow={flow}, head={head}")

        # Get catalog pump and calculate performance
        from ..catalog_engine import get_catalog_engine, convert_catalog_pump_to_legacy_format
        catalog_engine = get_catalog_engine()
        catalog_pump = catalog_engine.get_pump_by_code(pump_code)

        if not catalog_pump:
            logger.error(f"PDF generation - Catalog pump {pump_code} not found")
            safe_flash('Pump not found in catalog', 'error')
            return redirect(url_for('main_flow.index'))

        # Calculate performance at duty point
        performance = catalog_pump.get_performance_at_duty(flow, head)

        if not performance:
            logger.error(f"PDF generation - No performance data for {pump_code} at flow={flow}, head={head}")
            safe_flash(f'Pump {pump_code} cannot operate at flow={flow} m³/hr, head={head} m', 'error')
            return redirect(url_for('main_flow.index'))

        logger.info(f"PDF generation - Performance calculated: efficiency={performance.get('efficiency_pct')}%, power={performance.get('power_kw')}kW")

        # Create site requirements from URL parameters
        site_requirements = SiteRequirements(
            flow_m3hr=flow,
            head_m=head,
            customer_name=request.args.get('customer_name', 'Engineering Client'),
            project_name=request.args.get('project_name', 'Pump Selection Project'),
            application_type=request.args.get('application_type', 'general')
        )

        # Convert performance data to PDF template format
        operating_point = {
            'flow_m3hr': flow,
            'head_m': head,
            'achieved_head_m': performance.get('head_m', head),
            'efficiency_pct': performance.get('efficiency_pct', 0),
            'achieved_efficiency_pct': performance.get('efficiency_pct', 0),
            'power_kw': performance.get('power_kw', 0),
            'achieved_power_kw': performance.get('power_kw', 0),
            'npshr_m': performance.get('npshr_m', 0),
            'impeller_diameter_mm': performance.get('impeller_diameter_mm', 0),
            'impeller_size': performance.get('impeller_diameter_mm', 0),
            'test_speed_rpm': performance.get('test_speed_rpm', 1480)
        }

        # Create evaluation data for PDF
        evaluation = {
            'pump_code': pump_code,
            'overall_score': performance.get('efficiency_pct', 0),
            'selection_reason': f"Efficiency: {performance.get('efficiency_pct', 0):.1f}%, Operating at duty point",
            'operating_point': operating_point,
            'pump_info': {
                'manufacturer': catalog_pump.manufacturer,
                'model_series': catalog_pump.model_series,
                'pump_type': catalog_pump.pump_type
            },
            'curve_index': 0,
            'suitable': performance.get('efficiency_pct', 0) > 40
        }

        # Convert to legacy format for PDF compatibility
        legacy_pump = convert_catalog_pump_to_legacy_format(catalog_pump, performance)

        logger.info(f"PDF generation - Legacy pump converted, generating PDF")

        # Generate PDF using the calculated data
        from ..pdf_generator import generate_pdf_report as generate_pdf
        pdf_content = generate_pdf(
            selected_pump_evaluation=evaluation,
            parsed_pump=legacy_pump,
            site_requirements=site_requirements,
            alternatives=[]  # No alternatives in stateless mode
        )

        # Create response
        response = Response(pdf_content, mimetype='application/pdf')
        response.headers['Content-Disposition'] = f'attachment; filename="APE_Pump_Report_{pump_code.replace("/", "_").replace(" ", "_")}.pdf"'
        response.headers['Content-Length'] = len(pdf_content)

        return response

    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
        safe_flash('Error generating PDF report. Please try again.', 'error')
        return redirect(url_for('main_flow.index'))

@reports_bp.route('/generate_pdf', methods=['POST'])
def generate_pdf_post():  # Renamed to be more descriptive
    """API endpoint for PDF report generation."""
    try:
        data = request.get_json() if request.is_json else {}

        if not data:
            return jsonify({'error': 'No pump data provided'}), 400

        pump_code = data.get('pump_code')
        flow_rate = data.get('flow_rate')
        head = data.get('head')

        if not all([pump_code, flow_rate, head]):
            return jsonify({'error': 'Missing required parameters: pump_code, flow_rate, head'}), 400

        # Use catalog_engine directly instead of legacy pump_engine
        from ..catalog_engine import get_catalog_engine, convert_catalog_pump_to_legacy_format
        catalog_engine = get_catalog_engine()

        if not pump_code:
            return jsonify({'error': 'Pump code is required'}), 400

        catalog_pump = catalog_engine.get_pump_by_code(str(pump_code))

        if not catalog_pump:
            return jsonify({'error': f'Pump {pump_code} not found'}), 404

        # Validate and convert parameters with safe fallbacks
        try:
            flow_val = float(flow_rate) if flow_rate is not None else 100.0
            head_val = float(head) if head is not None else 20.0
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid flow_rate or head parameters'}), 400

        site_requirements = SiteRequirements(
            flow_m3hr=flow_val,
            head_m=head_val,
            application="API Request",
            fluid_type="clean_water",
            temperature=20.0,
            viscosity=1.0,
            density=1000.0,
            npsh_available=10.0,
            installation="standard"
        )

        # Get performance at duty point
        performance = catalog_pump.get_performance_at_duty(flow_val, head_val)

        if not performance:
            return jsonify({'error': f'Pump {pump_code} cannot operate at flow={flow_val} m³/hr, head={head_val} m'}), 400

        # Create evaluation data
        evaluation = {
            'pump_code': pump_code,
            'overall_score': performance.get('efficiency_pct', 0),
            'selection_reason': f"Efficiency: {performance.get('efficiency_pct', 0):.1f}%, Operating at duty point",
            'operating_point': performance,
            'pump_info': {
                'manufacturer': catalog_pump.manufacturer,
                'model_series': catalog_pump.model_series,
                'pump_type': catalog_pump.pump_type
            },
            'curve_index': 0,
            'suitable': performance.get('efficiency_pct', 0) > 40
        }

        # Convert to legacy format for PDF compatibility
        legacy_pump = convert_catalog_pump_to_legacy_format(catalog_pump, performance)

        from ..pdf_generator import generate_pdf_report
        pdf_content = generate_pdf_report(evaluation, legacy_pump, site_requirements)

        response = make_response(pdf_content)
        response.headers['Content-Type'] = 'application/pdf'
        safe_pump_code = str(pump_code).replace("/", "_") if pump_code else "unknown"
        response.headers['Content-Disposition'] = f'attachment; filename="pump_report_{safe_pump_code}.pdf"'

        return response

    except Exception as e:
        logger.error(f"Error in PDF generation API: {str(e)}")
        return jsonify({'error': f'PDF generation failed: {str(e)}'}), 500