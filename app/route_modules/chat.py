"""
Chat Routes
Routes for AI chat functionality with pump selection capabilities
"""
import logging
import re
import json
from flask import Blueprint, render_template, request, jsonify, url_for
from ..session_manager import safe_flash
from ..catalog_engine import get_catalog_engine
from ..data_models import SiteRequirements
import traceback

logger = logging.getLogger(__name__)

# Create blueprint
chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat')
def chat_page():
    """AI chat interface."""
    return render_template('chat.html')

def extract_pump_parameters(query):
    """Extract flow, head, and pump type from natural language query"""
    import re
    query_lower = query.lower()
    
    flow = None
    head = None
    pump_name = None
    
    # Check for pump name with @ symbol (e.g., "@12 WLN 14A" or "@12 WLN 14A 1400 30")
    # But exclude shorthand "flow @ head" patterns
    if '@' in query:
        # First check if it's a "flow @ head" pattern (e.g., "1781 @ 24")
        flow_head_pattern = r'(\d+(?:\.\d+)?)\s*@\s*(\d+(?:\.\d+)?)'
        flow_head_match = re.search(flow_head_pattern, query)
        
        if flow_head_match:
            # This is a flow @ head pattern, not a pump name
            pass  # Will be handled by shorthand patterns below
        else:
            # Pattern to extract pump name and optional flow/head
            pump_pattern = r'@([A-Za-z0-9\s/\-]+?)(?:\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?))?$'
            match = re.search(pump_pattern, query)
            
            if match:
                pump_name = match.group(1).strip()
                if match.group(2) and match.group(3):
                    # Flow and head provided with pump name
                    flow = float(match.group(2))
                    head = float(match.group(3))
                # Return with pump name prefixed by PUMP: to distinguish from application type
                return flow, head, f'PUMP:{pump_name}'
    
    # First check for shorthand patterns like "1781 @ 24" or "1781 24"
    shorthand_patterns = [
        r'(\d+(?:\.\d+)?)\s*[@]\s*(\d+(?:\.\d+)?)',  # 1781 @ 24
        r'(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s*(?:hsc|vsp|pump)?',  # 1781 24 HSC
        r'(\d+(?:\.\d+)?)\s+and\s+(\d+(?:\.\d+)?)',  # 1781 and 24
    ]
    
    for pattern in shorthand_patterns:
        match = re.search(pattern, query_lower)
        if match:
            num1 = float(match.group(1))
            num2 = float(match.group(2))
            # Assume larger number is flow (m³/hr), smaller is head (m)
            # Unless the second number is clearly too large for head (>200m)
            if num1 > num2 and num2 < 200:
                flow = num1
                head = num2
            elif num2 > num1 and num1 < 200:
                flow = num2
                head = num1
            else:
                # Default assumption: first is flow, second is head
                flow = num1
                head = num2
            break
    
    # If shorthand didn't match, try standard patterns
    if not flow or not head:
        # Extract flow rate (look for patterns like "1500 m³/hr", "1500 m3/hr", "1500m³/hr", etc.)
        flow_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:m³/hr|m3/hr|m³/h|m3/h|cubic\s*meters?\s*per\s*hour)',
            r'(\d+(?:\.\d+)?)\s*flow',
            r'flow\s*(?:rate)?\s*(?:of)?\s*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*(?:at|@)',  # e.g., "1500 at 25m"
        ]
        
        if not flow:
            for pattern in flow_patterns:
                match = re.search(pattern, query_lower)
                if match:
                    flow = float(match.group(1))
                    break
        
        # Extract head (look for patterns like "25 meters", "25m", "25 m head", etc.)
        head_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:meters?\s*head|m\s*head|meters?|m)(?:\s|$|,)',
            r'head\s*(?:of)?\s*(\d+(?:\.\d+)?)\s*(?:meters?|m)?',
            r'(?:at|@)\s*(\d+(?:\.\d+)?)\s*(?:meters?|m)?(?:\s|$|,)',
        ]
        
        if not head:
            for pattern in head_patterns:
                match = re.search(pattern, query_lower)
                if match:
                    head = float(match.group(1))
                    break
    
    # Extract pump type or application
    pump_types = {
        'water supply': ['water supply', 'clean water', 'potable water', 'drinking water'],
        'wastewater': ['wastewater', 'sewage', 'effluent', 'waste water'],
        'industrial': ['industrial', 'process', 'chemical'],
        'irrigation': ['irrigation', 'agricultural', 'farming'],
        'fire': ['fire', 'firefighting', 'fire protection'],
        'booster': ['booster', 'pressure boost'],
        'hsc': ['hsc'],
        'vertical': ['vsp', 'vertical', 'turbine'],
        'general': ['general', 'standard', 'normal']
    }
    
    application_type = 'general'
    for app_type, keywords in pump_types.items():
        for keyword in keywords:
            if keyword in query_lower:
                application_type = app_type
                break
    
    return flow, head, application_type

def handle_specific_pump_query(pump_name, flow, head):
    """Handle query for specific pump at specific conditions"""
    try:
        from ..catalog_engine import get_catalog_engine
        catalog_engine = get_catalog_engine()
        
        # Find the pump and evaluate at specified conditions
        pumps = catalog_engine.repository.get_pump_models()
        target_pump = None
        for pump in pumps:
            if pump.get('pump_name', '').upper() == pump_name.upper():
                target_pump = pump
                break
        
        if not target_pump:
            return {
                'response': f"I couldn't find pump '{pump_name}' in the database. Please check the name and try again.",
                'is_html': False,
                'processing_time': 0.1,
                'confidence_score': 0.9
            }
        
        # Generate report URL for this pump at these conditions
        pump_url = url_for('reports.engineering_report', 
                          pump_code=target_pump.get('pump_name'),
                          flow=flow, 
                          head=head,
                          force='true',
                          _external=False)
        
        html_response = f"""
        <div class="pump-specific-result">
            <h3 style="color: #10b981; margin-bottom: 0.5rem;">🎯 {target_pump.get('pump_name')}</h3>
            <p style="color: #64748b; margin-bottom: 1rem;">Performance at {flow} m³/hr @ {head}m</p>
            <div class="pump-result-card" style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 0.75rem;">
                <div class="pump-specs" style="margin-bottom: 0.75rem;">
                    <div style="font-size: 0.875rem; color: #4b5563;">
                        <strong>Type:</strong> {target_pump.get('pump_type')}<br>
                        <strong>Speed:</strong> {target_pump.get('speed_rpm')} RPM<br>
                        <strong>Impeller:</strong> {target_pump.get('impeller_dia_mm')}mm
                    </div>
                </div>
                <a href="{pump_url}" target="_blank" class="view-details-btn" style="
                    display: inline-block;
                    width: 100%;
                    padding: 0.5rem;
                    background: #3b82f6;
                    color: white;
                    text-align: center;
                    border-radius: 4px;
                    text-decoration: none;
                    font-size: 0.875rem;
                ">
                    <i class="material-icons" style="vertical-align: middle; font-size: 18px;">visibility</i>
                    View Full Engineering Report
                </a>
            </div>
        </div>
        """
        
        return {
            'response': html_response,
            'is_html': True,
            'processing_time': 0.3,
            'confidence_score': 0.95
        }
    except Exception as e:
        logger.error(f"Error handling specific pump query: {str(e)}")
        return {
            'response': "I encountered an error while looking up that pump. Please try again.",
            'is_html': False,
            'processing_time': 0.1,
            'confidence_score': 0.5
        }

def handle_pump_bep_query(pump_name):
    """Handle query for pump at BEP conditions"""
    try:
        from ..catalog_engine import get_catalog_engine
        catalog_engine = get_catalog_engine()
        
        # Find the pump
        pumps = catalog_engine.repository.get_pump_models()
        target_pump = None
        for pump in pumps:
            if pump.get('pump_name', '').upper() == pump_name.upper():
                target_pump = pump
                break
        
        if not target_pump:
            return {
                'response': f"I couldn't find pump '{pump_name}' in the database. Please check the name and try again.",
                'is_html': False,
                'processing_time': 0.1,
                'confidence_score': 0.9
            }
        
        # Get BEP conditions
        bep_flow = target_pump.get('bep_flow_m3hr')
        bep_head = target_pump.get('bep_head_m')
        
        if not bep_flow or not bep_head:
            return {
                'response': f"BEP data not available for {pump_name}. Please specify flow and head values.",
                'is_html': False,
                'processing_time': 0.1,
                'confidence_score': 0.8
            }
        
        # Generate report URL for BEP conditions
        pump_url = url_for('reports.engineering_report', 
                          pump_code=target_pump.get('pump_name'),
                          flow=bep_flow, 
                          head=bep_head,
                          force='true',
                          _external=False)
        
        html_response = f"""
        <div class="pump-specific-result">
            <h3 style="color: #10b981; margin-bottom: 0.5rem;">🎯 {target_pump.get('pump_name')} at BEP</h3>
            <p style="color: #64748b; margin-bottom: 1rem;">Best Efficiency Point: {bep_flow:.1f} m³/hr @ {bep_head:.1f}m</p>
            <div class="pump-result-card" style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 0.75rem;">
                <div class="pump-specs" style="margin-bottom: 0.75rem;">
                    <div style="font-size: 0.875rem; color: #4b5563;">
                        <strong>Type:</strong> {target_pump.get('pump_type')}<br>
                        <strong>Speed:</strong> {target_pump.get('speed_rpm')} RPM<br>
                        <strong>Impeller:</strong> {target_pump.get('impeller_dia_mm')}mm<br>
                        <strong>Max Efficiency:</strong> {target_pump.get('max_efficiency', 0):.1f}% (at BEP)
                    </div>
                </div>
                <a href="{pump_url}" target="_blank" class="view-details-btn" style="
                    display: inline-block;
                    width: 100%;
                    padding: 0.5rem;
                    background: #3b82f6;
                    color: white;
                    text-align: center;
                    border-radius: 4px;
                    text-decoration: none;
                    font-size: 0.875rem;
                ">
                    <i class="material-icons" style="vertical-align: middle; font-size: 18px;">visibility</i>
                    View Full Engineering Report at BEP
                </a>
            </div>
        </div>
        """
        
        return {
            'response': html_response,
            'is_html': True,
            'processing_time': 0.3,
            'confidence_score': 0.95
        }
    except Exception as e:
        logger.error(f"Error handling BEP pump query: {str(e)}")
        return {
            'response': "I encountered an error while looking up that pump's BEP. Please try again.",
            'is_html': False,
            'processing_time': 0.1,
            'confidence_score': 0.5
        }

def format_pump_selection_response(pumps, flow, head, application_type):
    """Format pump selection results as HTML cards"""
    if not pumps:
        return """
        <div class="no-results-message">
            <i class="material-icons">warning</i>
            <p>No suitable pumps found for your requirements.</p>
            <p>Try adjusting your flow rate or head values.</p>
        </div>
        """
    
    # Build HTML response with pump cards
    html_response = f"""
    <div class="pump-selection-results">
        <div class="results-header">
            <h3>✓ Found {len(pumps)} suitable pump{'s' if len(pumps) > 1 else ''}</h3>
            <p class="requirements-summary">
                <strong>Requirements:</strong> {flow} m³/hr @ {head}m head
                {f'• Application: {application_type.title()}' if application_type != 'general' else ''}
            </p>
        </div>
        <div class="pump-cards-container">
    """
    
    for i, pump in enumerate(pumps[:5], 1):  # Show top 5 pumps
        pump_code = pump.get('pump_code', 'N/A')
        score = pump.get('suitability_score', 0)
        efficiency = pump.get('performance', {}).get('efficiency_pct', 0)
        power = pump.get('performance', {}).get('power_kw', 0)
        trim = pump.get('performance', {}).get('sizing_info', {}).get('trim_percent', 100)
        method = pump.get('performance', {}).get('sizing_info', {}).get('sizing_method', 'direct')
        
        # Determine badge color based on score
        badge_color = 'success' if score >= 80 else 'warning' if score >= 60 else 'info'
        
        # Build pump details URL - use engineering report with force=true to load pump directly
        pump_url = url_for('reports.engineering_report', 
                          pump_code=pump_code, 
                          flow=flow, 
                          head=head,
                          force='true')
        
        html_response += f"""
        <div class="pump-result-card" data-pump-code="{pump_code}">
            <div class="pump-card-header">
                <div class="pump-rank">#{i}</div>
                <div class="pump-title">
                    <h4>{pump_code}</h4>
                    <span class="score-badge {badge_color}">{score:.1f} pts</span>
                </div>
            </div>
            <div class="pump-card-body">
                <div class="pump-specs">
                    <div class="spec-item">
                        <i class="material-icons">speed</i>
                        <span>Efficiency: <strong>{efficiency:.1f}%</strong></span>
                    </div>
                    <div class="spec-item">
                        <i class="material-icons">bolt</i>
                        <span>Power: <strong>{power:.1f} kW</strong></span>
                    </div>
                    <div class="spec-item">
                        <i class="material-icons">settings</i>
                        <span>Trim: <strong>{trim:.0f}%</strong></span>
                    </div>
                    <div class="spec-item">
                        <i class="material-icons">build</i>
                        <span>Method: <strong>{method.replace('_', ' ').title()}</strong></span>
                    </div>
                </div>
            </div>
            <div class="pump-card-footer">
                <a href="{pump_url}" target="_blank" class="view-details-btn">
                    <i class="material-icons">visibility</i>
                    View Details
                </a>
                <button class="compare-btn" onclick="addToComparison('{pump_code}')">
                    <i class="material-icons">compare_arrows</i>
                    Compare
                </button>
            </div>
        </div>
        """
    
    html_response += """
        </div>
        <div class="results-footer">
            <p class="help-text">
                <i class="material-icons">info</i>
                Click "View Details" to see complete specifications and performance curves.
            </p>
        </div>
    </div>
    """
    
    return html_response

@chat_bp.route('/api/chat/query', methods=['POST'])
def chat_query():
    """Handle chat queries with pump selection capability"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        history = data.get('history', [])
        
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        
        # Check if this is a pump selection query
        flow, head, application_type = extract_pump_parameters(query)
        
        # Handle pump name queries
        if isinstance(application_type, str) and application_type.startswith('PUMP:'):
            pump_name = application_type.replace('PUMP:', '')
            if flow and head:
                # Specific pump at specific conditions
                response = handle_specific_pump_query(pump_name, flow, head)
            else:
                # Pump at BEP conditions
                response = handle_pump_bep_query(pump_name)
        elif flow and head:
            # This is a pump selection query
            logger.info(f"Pump selection query detected: Flow={flow}, Head={head}, Type={application_type}")
            
            try:
                # Create site requirements
                site_requirements = SiteRequirements(
                    flow_m3hr=flow,
                    head_m=head,
                    application_type=application_type,
                    liquid_type='clean_water',
                    npsha_available=None
                )
                
                # Get catalog engine and find suitable pumps
                catalog_engine = get_catalog_engine()
                # Don't pass pump_type filter - it's too restrictive for chat queries
                # Let the selection engine find all suitable pumps regardless of type
                pump_type_filter = None
                    
                results = catalog_engine.select_pumps(
                    flow_m3hr=flow,
                    head_m=head,
                    pump_type=pump_type_filter,
                    max_results=10
                )
                
                # Extract suitable pumps from results
                suitable_pumps = results if isinstance(results, list) else results.get('suitable_pumps', [])
                
                # Format response
                if suitable_pumps:
                    # Don't store complex pump objects in session - the engineering report
                    # will load them directly using force=true parameter
                    html_response = format_pump_selection_response(
                        suitable_pumps, flow, head, application_type
                    )
                    
                    response = {
                        'response': html_response,
                        'is_html': True,
                        'pump_selection': True,
                        'processing_time': 0.5,
                        'confidence_score': 0.95,
                        'suggestions': [
                            f"Compare top {min(3, len(suitable_pumps))} pumps",
                            "Adjust flow or head for more options",
                            "Add NPSH requirements for better selection"
                        ]
                    }
                else:
                    response = {
                        'response': f"No suitable pumps found for {flow} m³/hr @ {head}m head. Try adjusting your requirements or ask for alternatives.",
                        'is_html': False,
                        'pump_selection': True,
                        'processing_time': 0.3,
                        'confidence_score': 0.9,
                        'suggestions': [
                            "Try a lower flow rate",
                            "Consider a different head value",
                            "Ask about pump modifications"
                        ]
                    }
                    
            except Exception as e:
                logger.error(f"Error in pump selection: {str(e)}\n{traceback.format_exc()}")
                response = {
                    'response': "I encountered an error while searching for pumps. Please try rephrasing your query or use the main selection form.",
                    'is_html': False,
                    'processing_time': 0.1,
                    'confidence_score': 0.5,
                    'suggestions': []
                }
        else:
            # Not a pump selection query - provide helpful response
            intro_text = """
            <div class="chat-help-message">
                <h3>🔧 I'm your AI Pump Selection Assistant!</h3>
                <p><strong>I can help you find the perfect pump. Just tell me:</strong></p>
                <ul>
                    <li>• Flow rate (in m³/hr)</li>
                    <li>• Head (in meters)</li>
                    <li>• Application type (optional)</li>
                </ul>
                
                <div class="example-queries">
                    <p><strong>Try these example queries:</strong></p>
                    <div class="example-cards">
                        <button class="example-btn" onclick="sendQuickQuery('I need a pump for 1500 m³/hr at 25 meters head')">
                            💧 1500 m³/hr @ 25m
                        </button>
                        <button class="example-btn" onclick="sendQuickQuery('Find pumps for 500 m³/hr at 40m for water supply')">
                            🚰 Water Supply: 500 @ 40m
                        </button>
                        <button class="example-btn" onclick="sendQuickQuery('Show me pumps for 2000 m³/hr at 15 meters for industrial use')">
                            🏭 Industrial: 2000 @ 15m
                        </button>
                    </div>
                </div>
                
                <p class="metric-note">
                    <i class="material-icons">info</i>
                    <strong>Note:</strong> I work with metric units (m³/hr for flow, meters for head)
                </p>
            </div>
            """
            
            response = {
                'response': intro_text,
                'is_html': True,
                'pump_selection': False,
                'processing_time': 0.1,
                'confidence_score': 0.95,
                'suggestions': []
            }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in chat query: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'An error occurred processing your request'}), 500 