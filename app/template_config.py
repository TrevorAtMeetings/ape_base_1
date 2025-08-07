"""
Template Configuration and Helper Functions
Centralizes all hard-coded thresholds and business logic from templates
"""

# Efficiency Classification Thresholds
EFFICIENCY_THRESHOLDS = {
    'excellent': 80,
    'good': 70,
    'acceptable': 60
}

# BEP Operating Range Definitions
BEP_OPERATING_RANGES = {
    'optimal': {'min': 90, 'max': 110, 'color': '#c8e6c9', 'label': 'Optimal'},
    'good_low': {'min': 70, 'max': 90, 'color': '#fff3e0', 'label': 'Good'},
    'good_high': {'min': 110, 'max': 120, 'color': '#fff3e0', 'label': 'Good'},
    'marginal_low': {'min': 0, 'max': 70, 'color': '#ffcdd2', 'label': 'Marginal'},
    'marginal_high': {'min': 120, 'max': 150, 'color': '#ffcdd2', 'label': 'Marginal'}
}

# Score Classification for Progress Bars
SCORE_THRESHOLDS = {
    'excellent': {'min': 90, 'gradient': 'var(--gradient-success)', 'class': 'bg-success'},
    'good': {'min': 80, 'gradient': 'var(--gradient-info)', 'class': 'bg-info'},
    'acceptable': {'min': 70, 'gradient': 'var(--gradient-warning)', 'class': 'bg-warning'},
    'poor': {'min': 0, 'gradient': 'var(--gradient-danger)', 'class': 'bg-danger'}
}

def get_efficiency_rating(efficiency_pct):
    """
    Classify efficiency percentage into rating categories
    
    Args:
        efficiency_pct (float): Efficiency percentage
        
    Returns:
        dict: Contains label, class, and badge_class for display
    """
    if efficiency_pct is None:
        return {
            'label': 'Unknown',
            'class': 'bg-secondary',
            'badge_class': 'bg-secondary',
            'text_class': 'text-muted'
        }
    
    if efficiency_pct >= EFFICIENCY_THRESHOLDS['excellent']:
        return {
            'label': 'Excellent',
            'class': 'efficiency-excellent',
            'badge_class': 'bg-success',
            'text_class': 'text-success'
        }
    elif efficiency_pct >= EFFICIENCY_THRESHOLDS['good']:
        return {
            'label': 'Good',
            'class': 'efficiency-good',
            'badge_class': 'bg-info',
            'text_class': 'text-info'
        }
    elif efficiency_pct >= EFFICIENCY_THRESHOLDS['acceptable']:
        return {
            'label': 'Acceptable',
            'class': 'efficiency-acceptable',
            'badge_class': 'bg-warning',
            'text_class': 'text-warning'
        }
    else:
        return {
            'label': 'Poor',
            'class': 'efficiency-poor',
            'badge_class': 'bg-danger',
            'text_class': 'text-danger'
        }

def get_bep_zone_classification(qbep_percentage):
    """
    Classify QBEP percentage into operating zones
    
    Args:
        qbep_percentage (float): Percentage of BEP flow
        
    Returns:
        dict: Zone information including label, color, and position
    """
    if qbep_percentage is None:
        return {
            'label': 'Unknown',
            'color': 'secondary',
            'badge_class': 'bg-secondary',
            'zone_type': 'unknown',
            'marker_position': 50
        }
    
    # Calculate marker position for visual indicator (0-100% scale)
    marker_position = min(max((qbep_percentage / 150) * 100, 5), 95)
    
    if BEP_OPERATING_RANGES['optimal']['min'] <= qbep_percentage <= BEP_OPERATING_RANGES['optimal']['max']:
        return {
            'label': 'Optimal Zone',
            'color': 'success',
            'badge_class': 'bg-success',
            'zone_type': 'optimal',
            'marker_position': marker_position,
            'zone_color': BEP_OPERATING_RANGES['optimal']['color']
        }
    elif (BEP_OPERATING_RANGES['good_low']['min'] <= qbep_percentage < BEP_OPERATING_RANGES['good_low']['max'] or
          BEP_OPERATING_RANGES['good_high']['min'] < qbep_percentage <= BEP_OPERATING_RANGES['good_high']['max']):
        return {
            'label': 'Good Zone',
            'color': 'info',
            'badge_class': 'bg-info',
            'zone_type': 'good',
            'marker_position': marker_position,
            'zone_color': BEP_OPERATING_RANGES['good_low']['color']
        }
    else:
        return {
            'label': 'Marginal Zone',
            'color': 'warning',
            'badge_class': 'bg-warning',
            'zone_type': 'marginal',
            'marker_position': marker_position,
            'zone_color': BEP_OPERATING_RANGES['marginal_low']['color']
        }

def get_score_classification(score):
    """
    Classify numerical score into visual categories
    
    Args:
        score (float): Numerical score (0-100)
        
    Returns:
        dict: Classification with gradient and class information
    """
    if score is None or score < 0:
        return SCORE_THRESHOLDS['poor']
    
    if score >= SCORE_THRESHOLDS['excellent']['min']:
        return SCORE_THRESHOLDS['excellent']
    elif score >= SCORE_THRESHOLDS['good']['min']:
        return SCORE_THRESHOLDS['good']
    elif score >= SCORE_THRESHOLDS['acceptable']['min']:
        return SCORE_THRESHOLDS['acceptable']
    else:
        return SCORE_THRESHOLDS['poor']

def format_trim_display(trim_percent):
    """
    Format impeller trim percentage for display.
    Shows 0% when no trimming (100% of diameter), otherwise shows actual trim amount.
    
    Args:
        trim_percent (float): Trim percentage (100 = no trim, <100 = trimmed)
        
    Returns:
        str: Formatted trim display string
    """
    if trim_percent is None:
        return "0"
    
    # Convert from diameter percentage to trim amount
    # 100% diameter = 0% trim
    # 85% diameter = 15% trim
    trim_amount = 100 - float(trim_percent)
    return f"{trim_amount:.1f}".rstrip('0').rstrip('.')

def get_pump_status_badges(pump_data):
    """
    Generate status badges for pump operating parameters
    
    Args:
        pump_data (dict): Pump operating point data
        
    Returns:
        dict: Status badges for various parameters
    """
    operating_point = pump_data.get('operating_point', {})
    
    # Determine pump type from model code
    pump_code = pump_data.get('pump_code', '')
    if 'WLN' in pump_code or 'HSC' in pump_code:
        pump_type = 'High Speed Centrifugal'
    elif 'ALE' in pump_code or 'BLE' in pump_code:
        pump_type = 'Low Speed Centrifugal'
    elif 'AXIAL' in pump_code or '8312' in pump_code:
        pump_type = 'Axial Flow'
    else:
        pump_type = 'Centrifugal Pump'
    
    # Determine impeller status based on trim percentage
    sizing_info = operating_point.get('sizing_info', {})
    trim_percent = sizing_info.get('trim_percent', 100)
    
    if trim_percent >= 95:
        impeller_status = {'label': 'Optimal', 'class': 'bg-success'}
    elif trim_percent >= 85:
        impeller_status = {'label': 'Good', 'class': 'bg-info'}
    elif trim_percent >= 75:
        impeller_status = {'label': 'Acceptable', 'class': 'bg-warning'}
    else:
        impeller_status = {'label': 'Trimmed', 'class': 'bg-warning'}
    
    # Speed status
    test_speed = operating_point.get('test_speed_rpm', 0)
    if 1450 <= test_speed <= 1500:
        speed_status = {'label': 'Standard', 'class': 'bg-primary'}
    elif 2900 <= test_speed <= 3000:
        speed_status = {'label': 'High Speed', 'class': 'bg-info'}
    elif test_speed > 0:
        speed_status = {'label': 'Variable', 'class': 'bg-warning'}
    else:
        speed_status = {'label': 'Unknown', 'class': 'bg-secondary'}
    
    return {
        'pump_type': pump_type,
        'impeller_status': impeller_status,
        'speed_status': speed_status,
        'efficiency_rating': get_efficiency_rating(operating_point.get('efficiency_pct')),
        'flow_status': {'label': 'Target', 'class': 'bg-warning text-dark'},
        'head_status': {'label': 'Achieved', 'class': 'bg-warning text-dark'},
        'power_status': {'label': 'Calculated', 'class': 'bg-primary'},
        'npshr_status': {'label': 'Available' if operating_point.get('npshr_m') else 'N/A', 
                        'class': 'bg-info' if operating_point.get('npshr_m') else 'bg-secondary'}
    }

def calculate_bep_range_visual():
    """
    Generate BEP visual range indicator configuration
    
    Returns:
        dict: Visual range configuration for template
    """
    return {
        'zones': [
            {'start': 0, 'width': 20, 'color': BEP_OPERATING_RANGES['marginal_low']['color'], 'label': 'Marginal'},
            {'start': 20, 'width': 10, 'color': BEP_OPERATING_RANGES['good_low']['color'], 'label': 'Good'},
            {'start': 30, 'width': 40, 'color': BEP_OPERATING_RANGES['optimal']['color'], 'label': 'Optimal'},
            {'start': 70, 'width': 10, 'color': BEP_OPERATING_RANGES['good_high']['color'], 'label': 'Good'},
            {'start': 80, 'width': 20, 'color': BEP_OPERATING_RANGES['marginal_high']['color'], 'label': 'Marginal'}
        ],
        'labels': [
            {'position': 0, 'text': '0%'},
            {'position': 20, 'text': '70%'},
            {'position': 30, 'text': '90%'},
            {'position': 70, 'text': '110%'},
            {'position': 80, 'text': '120%'},
            {'position': 95, 'text': '150%'}
        ],
        'legend': [
            {'color': BEP_OPERATING_RANGES['optimal']['color'], 'label': 'Optimal (90-110%)'},
            {'color': BEP_OPERATING_RANGES['good_low']['color'], 'label': 'Good (70-90%, 110-120%)'},
            {'color': BEP_OPERATING_RANGES['marginal_low']['color'], 'label': 'Marginal (<70%, >120%)'}
        ]
    }