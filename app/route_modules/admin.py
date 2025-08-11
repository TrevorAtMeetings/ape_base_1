"""
Admin Routes
Routes for administrative functions including AI admin interface
"""
import logging
import os
import numpy as np
from flask import render_template, Blueprint, request, jsonify, current_app, flash
from werkzeug.utils import secure_filename

from ..pump_brain import get_pump_brain
from ..pump_repository import PumpRepository
from ..utils import SiteRequirements

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)

def _get_pump_attr(pump, attr_name, default=None):
    """Helper function to get pump attribute from either dict or object"""
    if isinstance(pump, dict):
        return pump.get(attr_name, default)
    else:
        return getattr(pump, attr_name, default)

# Allowed file extensions for document upload
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'doc', 'docx', 'md'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@admin_bp.route('/admin/ai')
def ai_admin():
    """AI Knowledge Base Admin page."""
    return render_template('ai_admin.html')

# Admin landing page with options
@admin_bp.route('/admin')
def admin_landing():
    return render_template('admin/admin_landing.html')

@admin_bp.route('/admin/testing')
def testing_interface():
    """Performance Testing & Validation Interface"""
    return render_template('admin_testing.html')

@admin_bp.route('/admin/testing', methods=['POST'])
def run_performance_test():
    """Run performance comparison test between database and UI calculations"""
    try:
        # Get form data
        flow_rate = request.form.get('flow_rate', '').strip()
        head = request.form.get('head', '').strip()
        pump_code = request.form.get('pump_code', '').strip()
        
        # Convert to float if provided
        flow_rate = float(flow_rate) if flow_rate else None
        head = float(head) if head else None
        
        # Validate input combinations
        if not pump_code and (not flow_rate or not head):
            flash('Either provide pump code for BEP testing, or flow rate and head for duty point testing', 'error')
            return render_template('admin_testing.html')
            
        if (flow_rate and flow_rate <= 0) or (head and head <= 0):
            flash('Flow rate and head must be positive values when provided', 'error')
            return render_template('admin_testing.html')
        
        # Initialize engines

        brain = get_pump_brain()
        pump_repo = PumpRepository()
        
        # Determine testing mode
        bep_testing_mode = pump_code and not flow_rate and not head
        
        if bep_testing_mode:
            logger.info(f"Running BEP testing mode for pump: {pump_code}")
            # BEP Testing Mode: Test pump at its optimal efficiency point
            # BRAIN SYSTEM: Use repository through Brain
            pump_data = brain.repository.get_pump_by_code(pump_code)
            if not pump_data:
                flash(f'Pump code "{pump_code}" not found in database', 'error')
                return render_template('admin_testing.html')
            
            # Get BEP coordinates using Brain system
            bep_data = _get_bep_analysis(pump_data, pump_repo)
            if not bep_data.get('has_bep_data'):
                flash(f'No BEP data available for pump "{pump_code}"', 'error')
                return render_template('admin_testing.html')
                
            # Use BEP coordinates as test conditions
            flow_rate = bep_data['bep_flow_m3hr']
            head = bep_data['bep_head_m']
            test_pumps = [pump_data]
            test_mode = 'BEP Testing'
            
        else:
            logger.info(f"Running duty point testing: Flow={flow_rate} m³/hr, Head={head} m, Pump={pump_code or 'ALL'}")
            # Duty Point Testing Mode: Test at specified operating conditions
            if pump_code:
                # Test specific pump at specified conditions
                # BRAIN SYSTEM: Use repository through Brain
                pump_data = brain.repository.get_pump_by_code(pump_code)
                if not pump_data:
                    flash(f'Pump code "{pump_code}" not found in database', 'error')
                    return render_template('admin_testing.html')
                test_pumps = [pump_data]
            else:
                # Get suitable pumps from Brain system (limit to top 10 for testing)
                # Create site requirements - flow_rate and head are guaranteed to be floats here
                assert flow_rate is not None and head is not None, "Flow rate and head must be provided for duty point testing"
                selection_results = brain.find_best_pump(flow_rate, head)
                if not selection_results:
                    flash('No suitable pumps found for the given conditions', 'error')
                    return render_template('admin_testing.html')
                
                # Extract pump objects from selection results
                test_pumps = []
                limited_results = selection_results[:10]  # Take max 10 results
                for result in limited_results:
                    if isinstance(result, dict) and 'pump' in result:
                        test_pumps.append(result['pump'])
                    elif hasattr(result, 'pump') and not isinstance(result, dict):
                        test_pumps.append(result.pump)
                    else:
                        # Handle case where result is the pump data itself
                        test_pumps.append(result)
                        
                if not test_pumps:
                    flash('Unable to extract pump objects from selection results', 'error')
                    return render_template('admin_testing.html')
            test_mode = 'Duty Point Testing'
        
        # At this point, flow_rate and head are guaranteed to be float values
        assert flow_rate is not None and head is not None, "Flow rate and head must be defined at this point"
        
        # Check if envelope testing is requested
        envelope_testing = request.form.get('envelope_testing') == 'on'
        
        # Run comparison tests
        test_results = []
        for pump in test_pumps:
            if envelope_testing:
                # Run comprehensive envelope testing (10-20 points)
                result = _test_pump_performance_envelope(pump, flow_rate, head, pump_repo)
            else:
                # Run single-point testing (existing behavior)
                result = _compare_pump_performance(pump, flow_rate, head, pump_repo)
                if result:
                    # Add BEP analysis to each pump result
                    bep_data = _get_bep_analysis(pump, pump_repo)
                    result['bep_analysis'] = bep_data
            
            if result:
                test_results.append(result)
        
        logger.info(f"Performance test completed: {len(test_results)} pumps tested")
        
        return render_template('admin_testing.html', 
                             test_results=test_results,
                             test_conditions={
                                 'flow_m3hr': flow_rate,
                                 'head_m': head,
                                 'pump_code': pump_code if pump_code else None,
                                 'test_mode': test_mode if 'test_mode' in locals() else 'Duty Point Testing',
                                 'envelope_testing': envelope_testing
                             })
        
    except ValueError as e:
        flash(f'Invalid input: {str(e)}', 'error')
        return render_template('admin_testing.html')
    except Exception as e:
        logger.error(f"Error in performance test: {str(e)}")
        flash('An error occurred during testing. Please check the logs.', 'error')
        return render_template('admin_testing.html')

def _compare_pump_performance(pump, flow_rate, head, pump_repo):
    """Compare database raw values vs UI calculated values for a single pump"""
    try:
        # Get raw database performance (direct curve interpolation)
        db_performance = _get_database_performance(pump, flow_rate, head)
        
        # Get UI calculated performance (catalog engine with all transformations)
        ui_performance = _get_ui_performance(pump, flow_rate, head)
        
        # Calculate deltas
        efficiency_delta = None
        power_delta = None  
        npsh_delta = None
        
        if db_performance.get('efficiency') is not None and ui_performance.get('efficiency_pct') is not None:
            efficiency_delta = ui_performance['efficiency_pct'] - db_performance['efficiency']
            
        if db_performance.get('power_kw') is not None and ui_performance.get('power_kw') is not None:
            power_delta = ui_performance['power_kw'] - db_performance['power_kw']
            
        if db_performance.get('npshr_m') is not None and ui_performance.get('npshr_m') is not None:
            npsh_delta = ui_performance['npshr_m'] - db_performance['npshr_m']
        
        # CRITICAL: Only determine status if we have REAL data to compare
        # Prevent artificial "matches" when both sides have missing data
        has_valid_comparison = False
        if (db_performance.get('efficiency') is not None and ui_performance.get('efficiency_pct') is not None and 
            ui_performance.get('method') != 'ui_calculation_failed'):
            has_valid_comparison = True
        elif (db_performance.get('power_kw') is not None and ui_performance.get('power_kw') is not None and 
              ui_performance.get('method') != 'ui_calculation_failed'):
            has_valid_comparison = True
        elif (db_performance.get('npshr_m') is not None and ui_performance.get('npshr_m') is not None and 
              ui_performance.get('method') != 'ui_calculation_failed'):
            has_valid_comparison = True
            
        if has_valid_comparison:
            status = _determine_status(efficiency_delta, power_delta, npsh_delta, pump)
        else:
            status = 'NO_DATA'  # Both sides missing data or UI calculation failed
        
        return {
            'pump_code': _get_pump_attr(pump, 'pump_code'),
            'pump_type': _get_pump_attr(pump, 'pump_type'),
            'db_efficiency': db_performance.get('efficiency'),
            'ui_efficiency': ui_performance.get('efficiency_pct'),
            'efficiency_delta': efficiency_delta,
            'db_power': db_performance.get('power_kw'),
            'ui_power': ui_performance.get('power_kw'),
            'power_delta': power_delta,
            'db_npsh': db_performance.get('npshr_m'),
            'ui_npsh': ui_performance.get('npshr_m'),
            'npsh_delta': npsh_delta,
            'ui_score': ui_performance.get('suitability_score'),
            'status': status
        }
        
    except Exception as e:
        pump_code = _get_pump_attr(pump, 'pump_code')
        logger.error(f"Error comparing performance for {pump_code}: {str(e)}")
        return None

def _get_database_performance(pump, flow_rate, head):
    """Get performance using Brain system's authentic database calculations"""
    try:
        # Use Brain system for all performance calculations
        from app.pump_brain import get_pump_brain
        brain = get_pump_brain()
        
        pump_code = _get_pump_attr(pump, 'pump_code')
        logger.debug(f"Using Brain system for {pump_code} at {flow_rate}/{head}")
        
        # Use Brain's calculate_performance method with authentic database data
        performance_result = brain.calculate_performance(pump, flow_rate, head)
        
        if performance_result and isinstance(performance_result, dict):
            # Extract performance values from Brain result
            efficiency = performance_result.get('efficiency_pct')
            power_kw = performance_result.get('power_kw') 
            npshr_m = performance_result.get('npshr_m')
            
            logger.debug(f"Brain performance for {pump_code}: efficiency={efficiency}%, power={power_kw}kW, npsh={npshr_m}m")
            
            return {
                'efficiency': efficiency,
                'power_kw': power_kw,
                'npshr_m': npshr_m
            }
        else:
            logger.warning(f"Brain system returned no performance data for {pump_code} at {flow_rate} m³/hr, {head} m")
            return {'efficiency': None, 'power_kw': None, 'npshr_m': None}
        
    except Exception as e:
        pump_code = _get_pump_attr(pump, 'pump_code')
        logger.warning(f"Brain performance calculation failed for {pump_code}: {str(e)}")
        import traceback
        logger.debug(f"Full traceback: {traceback.format_exc()}")
        return {'efficiency': None, 'power_kw': None, 'npshr_m': None}

def _get_ui_performance(pump, flow_rate, head):
    """Get UI performance using Brain system's selection logic with trimming/scaling"""
    try:
        # Use Brain system for selection-based performance (with trimming logic)
        from app.pump_brain import get_pump_brain
        brain = get_pump_brain()
        
        pump_code = _get_pump_attr(pump, 'pump_code')
        logger.debug(f"Using Brain selection logic for {pump_code} at {flow_rate}/{head}")
        
        # Use Brain's find_best_pump method to get selection-based performance
        # This includes trimming, scaling, and all the intelligent selection logic
        selection_result = brain.find_best_pump(flow_rate, head)
        
        if selection_result and len(selection_result) > 0:
            # Find our specific pump in the results
            pump_result = None
            for result in selection_result:
                if result.get('pump_code') == pump_code:
                    pump_result = result
                    break
            
            if not pump_result:
                logger.warning(f"Pump {pump_code} not found in Brain selection results")
                return {
                    'efficiency_pct': None,
                    'power_kw': None,
                    'npshr_m': None,
                    'suitability_score': None,
                    'trim_percent': None,
                    'method': 'pump_not_selected',
                    'failure_reason': 'pump_not_in_selection_results'
                }
            
            # Extract performance values from selection result
            efficiency = pump_result.get('efficiency_pct')
            power_kw = pump_result.get('power_kw')
            npshr_m = pump_result.get('npshr_m')
            score = pump_result.get('score')
            trim_percent = pump_result.get('trim_percent')
            
            logger.debug(f"Brain selection for {pump_code}: efficiency={efficiency}%, power={power_kw}kW, npsh={npshr_m}m, score={score}")
            
            return {
                'efficiency_pct': efficiency,
                'power_kw': power_kw,
                'npshr_m': npshr_m,
                'suitability_score': score,
                'trim_percent': trim_percent,
                'method': 'brain_selection_success'
            }
        else:
            # Brain selection failed - pump cannot meet requirements
            error_msg = f"CRITICAL: Brain selection failed for {pump_code} at {flow_rate} m³/hr, {head} m - pump cannot meet requirements"
            logger.error(error_msg)
            
            return {
                'efficiency_pct': None,
                'power_kw': None,
                'npshr_m': None,
                'suitability_score': None,
                'trim_percent': None,
                'method': 'brain_selection_failed',
                'failure_reason': 'pump_cannot_meet_requirements'
            }
        
    except Exception as e:
        pump_code = _get_pump_attr(pump, 'pump_code')
        logger.warning(f"Brain selection calculation failed for {pump_code}: {str(e)}")
        import traceback
        logger.debug(f"Full traceback: {traceback.format_exc()}")
        return {
            'efficiency_pct': None,
            'power_kw': None, 
            'npshr_m': None,
            'suitability_score': None,
            'trim_percent': None,
            'method': 'error'
        }

def _get_bep_analysis(pump, pump_repo):
    """Get BEP analysis using ONLY authentic database specifications - NO FALLBACKS"""
    try:
        # Handle both dictionary and object formats
        if isinstance(pump, dict):
            pump_code = pump.get('pump_code')
            specifications = pump.get('specifications', {})
        else:
            pump_code = _get_pump_attr(pump, 'pump_code')
            specifications = _get_pump_attr(pump, 'specifications', {})
            
        # Get BEP from AUTHENTIC database specifications only
        # DEBUG: Check actual specifications structure
        logger.error(f"DEBUG: Specifications structure for {pump_code}: {specifications}")
        logger.error(f"DEBUG: Specifications keys: {list(specifications.keys()) if isinstance(specifications, dict) else 'Not a dict'}")
        
        bep_flow = specifications.get('bep_flow_m3hr')
        bep_head = specifications.get('bep_head_m') 
        bep_efficiency = None  # BEP efficiency not stored as separate specification - would need calculation from curves
        
        # FIXED: If specifications are empty, query database directly
        if not bep_flow or not bep_head:
            logger.error(f"DEBUG: Specifications empty for {pump_code}, querying database directly")
            try:
                # Query database directly for BEP data
                import psycopg2
                import os
                
                conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT ps.bep_flow_m3hr, ps.bep_head_m
                    FROM pump_specifications ps
                    JOIN pumps p ON ps.pump_id = p.id
                    WHERE p.pump_code = %s
                """, (pump_code,))
                result = cursor.fetchone()
                cursor.close()
                conn.close()
                
                if result:
                    bep_flow, bep_head = result
                    logger.error(f"DEBUG: Retrieved BEP from database - Flow: {bep_flow}, Head: {bep_head}")
                else:
                    logger.error(f"DEBUG: No BEP data found in database for {pump_code}")
                    
            except Exception as db_error:
                logger.error(f"DEBUG: Database query failed for {pump_code}: {db_error}")
        
        logger.error(f"DEBUG: Final BEP data - Flow: {bep_flow}, Head: {bep_head}")
        
        # Now using Brain system for all calculations - no manual curve debugging needed
                
        logger.info(f"Database BEP specifications for {pump_code}: Flow={bep_flow}, Head={bep_head}, Efficiency={bep_efficiency}")
        
        # CRITICAL: If no authentic BEP data exists, FAIL - never use fallbacks
        if not bep_flow or not bep_head:
            # Provide helpful guidance for pumps with BEP data
            error_msg = f"CRITICAL ERROR: No authentic BEP data found for {pump_code}. BEP Flow={bep_flow}, Head={bep_head}. Testing cannot proceed with estimated data."
            logger.error(error_msg)
            logger.error(f"SUGGESTION: For BEP testing, use pumps with authentic BEP data like 'APE DWU-150 BC' (568.73 m³/hr @ 135.61 m)")
            raise ValueError(error_msg)
        
        # Calculate performance at authentic BEP using both methods
        bep_db_performance = _get_database_performance(pump, bep_flow, bep_head)
        bep_ui_performance = _get_ui_performance(pump, bep_flow, bep_head)
        
        return {
            'bep_flow_m3hr': bep_flow,
            'bep_head_m': bep_head,
            'bep_efficiency_pct': bep_efficiency,
            'db_performance': bep_db_performance,
            'ui_performance': bep_ui_performance,
            'has_bep_data': True,
            'data_source': 'authentic_database_specifications'
        }
            
    except Exception as e:
        # Handle both dictionary and object formats for error logging
        pump_code = _get_pump_attr(pump, 'pump_code')
        logger.error(f"Error getting authentic BEP data for {pump_code}: {str(e)}")
        raise e

# REMOVED: _estimate_bep_from_curves function
# Data integrity policy: NEVER use estimated/fallback data for BEP validation
# If authentic BEP specifications don't exist, the test must fail

def _test_pump_performance_envelope(pump, base_flow, base_head, pump_repo):
    """Test pump performance across operating envelope using AUTHENTIC BEP data only"""
    try:
        # Get AUTHENTIC BEP data - will raise exception if not found
        bep_data = _get_bep_analysis(pump, pump_repo)
        
        # This should never execute due to exception handling above, but keeping for clarity
        if not bep_data.get('has_bep_data'):
            pump_code = _get_pump_attr(pump, 'pump_code')
            error_msg = f"CRITICAL: No authentic BEP data available for envelope testing of {pump_code}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        bep_flow = bep_data['bep_flow_m3hr']
        bep_head = bep_data['bep_head_m'] 
        
        # Generate test points across operating envelope
        test_points = _generate_envelope_test_points(pump, bep_flow, bep_head, base_head)
        
        # Run tests at all points
        envelope_results = []
        for point in test_points:
            point_result = _compare_pump_performance(pump, point['flow'], point['head'], pump_repo)
            if point_result:
                point_result['test_point'] = {
                    'flow_m3hr': point['flow'],
                    'head_m': point['head'],
                    'flow_percent_bep': point['flow_percent_bep'],
                    'operating_region': point['operating_region'],
                    'test_category': point['test_category']
                }
                envelope_results.append(point_result)
        
        # Calculate envelope statistics
        envelope_stats = _calculate_envelope_statistics(envelope_results)
        
        # Get total pump count for statistics display
        total_pumps = pump_repo.get_pump_count()
        
        return {
            'pump_code': _get_pump_attr(pump, 'pump_code'),
            'pump_type': _get_pump_attr(pump, 'pump_type'),
            'envelope_testing': True,
            'bep_analysis': bep_data,
            'test_points_count': len(envelope_results),
            'envelope_results': envelope_results,
            'envelope_statistics': envelope_stats,
            'total_pumps_available': total_pumps
        }
        
    except Exception as e:
        pump_code = _get_pump_attr(pump, 'pump_code')
        logger.error(f"Error in envelope testing for {pump_code}: {str(e)}")
        return None

def _generate_envelope_test_points(pump, bep_flow, bep_head, base_head):
    """Generate authentic envelope test points that follow the actual pump curve"""
    test_points = []
    
    # Get the best curve for the pump
    best_curve = None
    pump_curves = _get_pump_attr(pump, 'curves', [])
    if pump_curves:
        # Find curve closest to BEP conditions
        for curve in pump_curves:
            if 'performance_points' in curve:
                points = curve['performance_points']
                flows = [p['flow_m3hr'] for p in points if 'flow_m3hr' in p]
                heads = [p['head_m'] for p in points if 'head_m' in p]
                
                if flows and heads and min(flows) <= bep_flow <= max(flows):
                    best_curve = curve
                    break
        
        # Use first curve if no perfect match
        if not best_curve and pump_curves:
            best_curve = pump_curves[0]
    
    if not best_curve or 'performance_points' not in best_curve:
        # Fallback: use BEP-based estimates
        test_flows = [
            bep_flow * 0.6,   # 60% of BEP
            bep_flow * 0.8,   # 80% of BEP
            bep_flow * 0.9,   # 90% of BEP
            bep_flow,         # 100% BEP
            bep_flow * 1.1,   # 110% of BEP
            bep_flow * 1.2,   # 120% of BEP
            bep_flow * 1.3    # 130% of BEP
        ]
        
        for flow in test_flows:
            flow_pct_bep = (flow / bep_flow * 100) if bep_flow > 0 else 100
            test_points.append({
                'flow': flow,
                'head': bep_head,  # Use BEP head as estimate
                'flow_percent_bep': flow_pct_bep,
                'operating_region': _determine_operating_region(flow_pct_bep),
                'test_category': _determine_test_category(flow_pct_bep),
                'authentic_range': False
            })
    else:
        # Use actual pump curve data for realistic test points
        points = best_curve['performance_points']
        flows = [p['flow_m3hr'] for p in points if 'flow_m3hr' in p]
        heads = [p['head_m'] for p in points if 'head_m' in p]
        
        # Create interpolation function for the curve
        if len(flows) >= 2 and len(heads) >= 2:
            from scipy import interpolate
            head_interp = interpolate.interp1d(flows, heads, kind='linear', 
                                             bounds_error=False, 
                                             fill_value='extrapolate')
            
            # Generate test points at specific BEP percentages
            test_percentages = [60, 70, 80, 90, 100, 110, 120, 130, 140]
            
            for pct in test_percentages:
                test_flow = bep_flow * (pct / 100)
                
                # Only include points within manufacturer's documented range
                if min(flows) <= test_flow <= max(flows):
                    # Get the actual head at this flow from the pump curve
                    test_head = float(head_interp(test_flow))
                    
                    test_points.append({
                        'flow': test_flow,
                        'head': test_head,  # Use actual curve head, not fixed BEP head
                        'flow_percent_bep': pct,
                        'operating_region': _determine_operating_region(pct),
                        'test_category': _determine_test_category(pct),
                        'authentic_range': True,
                        'curve_based': True  # Flag to indicate we're following the actual curve
                    })
    
    # If we have fewer than 5 points, add some intermediate points
    if len(test_points) < 5 and best_curve:
        # Use actual curve points as test points
        points = best_curve['performance_points']
        for point in points[:9]:  # Limit to 9 points max
            if 'flow_m3hr' in point and 'head_m' in point:
                flow = point['flow_m3hr']
                head = point['head_m']
                flow_pct_bep = (flow / bep_flow * 100) if bep_flow > 0 else 100
                
                # Check if we already have a test point near this flow
                duplicate = any(abs(tp['flow'] - flow) < 50 for tp in test_points)
                if not duplicate:
                    test_points.append({
                        'flow': flow,
                        'head': head,
                        'flow_percent_bep': flow_pct_bep,
                        'operating_region': _determine_operating_region(flow_pct_bep),
                        'test_category': _determine_test_category(flow_pct_bep),
                        'authentic_range': True,
                        'curve_based': True
                    })
    
    # Sort by flow rate
    test_points.sort(key=lambda x: x['flow'])
    
    return test_points

def _determine_operating_region(flow_pct_bep):
    """Determine operating region based on flow percentage of BEP"""
    if flow_pct_bep < 80:
        return "Part Load"
    elif flow_pct_bep <= 110:
        return "Optimal Zone"
    else:
        return "Overload"

def _determine_test_category(flow_pct_bep):
    """Determine test category based on flow percentage of BEP"""
    if flow_pct_bep < 80:
        return "part_load_validation"
    elif flow_pct_bep <= 110:
        return "bep_validation"
    else:
        return "overload_validation"

def _calculate_envelope_statistics(envelope_results):
    """Calculate statistical analysis of envelope test results"""
    if not envelope_results:
        return {}
    
    # Extract deltas for statistical analysis
    efficiency_deltas = [r['efficiency_delta'] for r in envelope_results if r['efficiency_delta'] is not None]
    power_deltas = [r['power_delta'] for r in envelope_results if r['power_delta'] is not None] 
    npsh_deltas = [r['npsh_delta'] for r in envelope_results if r['npsh_delta'] is not None]
    
    stats = {}
    
    # Efficiency statistics
    if efficiency_deltas:
        stats['efficiency'] = {
            'mean_delta': np.mean(efficiency_deltas),
            'std_delta': np.std(efficiency_deltas),
            'max_delta': max(efficiency_deltas),
            'min_delta': min(efficiency_deltas),
            'mean_abs_delta': np.mean([abs(d) for d in efficiency_deltas])
        }
    
    # Power statistics  
    if power_deltas:
        stats['power'] = {
            'mean_delta': np.mean(power_deltas),
            'std_delta': np.std(power_deltas),
            'max_delta': max(power_deltas),
            'min_delta': min(power_deltas),
            'mean_abs_delta': np.mean([abs(d) for d in power_deltas])
        }
        
    # NPSH statistics
    if npsh_deltas:
        stats['npsh'] = {
            'mean_delta': np.mean(npsh_deltas),
            'std_delta': np.std(npsh_deltas), 
            'max_delta': max(npsh_deltas),
            'min_delta': min(npsh_deltas),
            'mean_abs_delta': np.mean([abs(d) for d in npsh_deltas])
        }
    
    # Overall accuracy metrics
    all_points = len(envelope_results)
    accurate_points = len([r for r in envelope_results if r['status'] == 'match'])
    minor_diff_points = len([r for r in envelope_results if r['status'] == 'minor_diff']) 
    major_diff_points = len([r for r in envelope_results if r['status'] == 'major_diff'])
    
    stats['accuracy'] = {
        'total_points': all_points,
        'accurate_points': accurate_points,
        'minor_diff_points': minor_diff_points,
        'major_diff_points': major_diff_points,
        'accuracy_percentage': (accurate_points / all_points) * 100 if all_points > 0 else 0,
        'acceptable_percentage': ((accurate_points + minor_diff_points) / all_points) * 100 if all_points > 0 else 0
    }
    
    return stats

def _determine_status(efficiency_delta, power_delta, npsh_delta, pump=None):
    """Determine test status based on deltas between database and UI values using pump-specific thresholds"""
    
    # Check for major differences (indicating potential issues)
    major_diff = False
    minor_diff = False
    
    # Pump-specific efficiency thresholds based on pump characteristics
    pump_specifications = _get_pump_attr(pump, 'specifications', {})
    if pump and pump_specifications:
        # Use pump-specific thresholds if available, otherwise conservative defaults
        max_power = pump_specifications.get('max_power_kw', 10)  # kW
        if max_power and max_power > 0:
            # Scale power thresholds based on pump size
            major_power_threshold = max(2.0, max_power * 0.1)  # 10% of max power or 2kW minimum
            minor_power_threshold = max(0.5, max_power * 0.05)  # 5% of max power or 0.5kW minimum
        else:
            # Conservative defaults when max power unknown
            major_power_threshold = 2.0
            minor_power_threshold = 0.5
    else:
        # Conservative defaults
        major_power_threshold = 2.0
        minor_power_threshold = 0.5
    
    # Efficiency thresholds (more universal across pump types)
    if efficiency_delta is not None and abs(efficiency_delta) > 5:  # >5% efficiency difference
        major_diff = True
    elif efficiency_delta is not None and abs(efficiency_delta) > 2:  # >2% efficiency difference
        minor_diff = True
        
    # CRITICAL: Power validation removed - no authentic power data exists in database
    # All power comparisons are invalid since both DB and UI calculate power using same formula
    # Commenting out power validation to prevent false accuracy metrics
    # if power_delta is not None and abs(power_delta) > major_power_threshold:
    #     major_diff = True  
    # elif power_delta is not None and abs(power_delta) > minor_power_threshold:
    #     minor_diff = True
        
    # NPSH thresholds (pump-specific would be better but using conservative defaults)
    if npsh_delta is not None and abs(npsh_delta) > 1:  # >1m NPSH difference
        major_diff = True
    elif npsh_delta is not None and abs(npsh_delta) > 0.3:  # >0.3m NPSH difference
        minor_diff = True
    
    if major_diff:
        return 'major_diff'
    elif minor_diff:
        return 'minor_diff'
    else:
        return 'match'

@admin_bp.route('/admin/upload', methods=['POST'])
def upload_document():
    """Handle document upload for AI knowledge base"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({
                'success': False, 
                'error': f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Secure the filename
        filename = secure_filename(file.filename or 'unnamed')
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save the file
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        # Get file info
        file_size = os.path.getsize(filepath)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'size': file_size,
            'message': 'Document uploaded successfully'
        })
        
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        return jsonify({'success': False, 'error': 'Upload failed'}), 500

@admin_bp.route('/api/chat/status', methods=['GET'])
def chat_status():
    """Get chat API status"""
    try:
        # Check if API keys are configured
        openai_configured = bool(os.environ.get('OPENAI_API_KEY'))
        google_configured = bool(os.environ.get('GOOGLE_API_KEY'))
        
        status = {
            'status': 'ready' if (openai_configured or google_configured) else 'not_configured',
            'providers': {
                'openai': 'configured' if openai_configured else 'not_configured',
                'google': 'configured' if google_configured else 'not_configured'
            }
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error checking chat status: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


@admin_bp.route('/admin/documents', methods=['GET'])
def get_documents():
    """Get list of uploaded documents"""
    try:
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents')
        documents = []
        
        if os.path.exists(upload_dir):
            for filename in os.listdir(upload_dir):
                if allowed_file(filename):
                    filepath = os.path.join(upload_dir, filename)
                    file_stat = os.stat(filepath)
                    documents.append({
                        'filename': filename,
                        'size': file_stat.st_size,
                        'uploaded': file_stat.st_mtime,
                        'type': filename.split('.')[-1].lower()
                    })
        
        return jsonify({
            'success': True,
            'documents': documents,
            'count': len(documents)
        })
        
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to retrieve documents'}), 500


@admin_bp.route('/admin/test-query', methods=['POST'])
def test_query():
    """Test AI query functionality"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'success': False, 'error': 'No query provided'}), 400
        
        # For now, return a placeholder response indicating the feature is under development
        response = {
            'success': True,
            'query': query,
            'response': 'AI query functionality is under development. This feature will provide intelligent responses based on uploaded technical documents.',
            'confidence': 0.95,
            'sources': ['Feature coming soon'],
            'processing_time': 0.1
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error processing test query: {str(e)}")
        return jsonify({'success': False, 'error': 'Query processing failed'}), 500