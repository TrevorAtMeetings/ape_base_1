"""
Tests for impeller specification vs curve consistency
Ensures min/max impeller values are correctly derived from curves
"""

import pytest
from app.catalog_engine import CatalogPump
from app.utils_impeller import compute_impeller_min_max_from_curves


def _pump(curves):
    """Helper to create test pump with specified curves"""
    return CatalogPump({
        'pump_code': 'TEST_PUMP',
        'manufacturer': 'APE PUMPS',
        'pump_type': 'END SUCTION',
        'model_series': 'Test Series',
        'specifications': {},
        'curves': curves,
        'curve_count': len(curves),
        'total_points': 0,
        'npsh_curves': [],
        'power_curves': []
    })


def test_min_max_from_curves_numbers():
    """Test min/max computation from numeric impeller diameters"""
    p = _pump([
        {'impeller_diameter_mm': 330.2, 'performance_points': []},
        {'impeller_diameter_mm': 406.4, 'performance_points': []},
    ])
    assert float(p.specifications['min_impeller_mm']) == 330.2
    assert float(p.specifications['max_impeller_mm']) == 406.4


def test_min_max_from_curves_strings_mm():
    """Test min/max computation from string impeller sizes"""
    p = _pump([
        {'impeller_size': '330.2', 'performance_points': []},
        {'impeller_size': '406.4', 'performance_points': []},
    ])
    assert float(p.specifications['min_impeller_mm']) == 330.2
    assert float(p.specifications['max_impeller_mm']) == 406.4


def test_min_max_from_mixed_fields():
    """Test min/max computation from mixed field names"""
    p = _pump([
        {'impeller_diameter_mm': 330.2, 'performance_points': []},
        {'impeller_size': '406.4', 'performance_points': []},
    ])
    assert float(p.specifications['min_impeller_mm']) == 330.2
    assert float(p.specifications['max_impeller_mm']) == 406.4


def test_single_curve():
    """Test with single curve"""
    p = _pump([
        {'impeller_diameter_mm': 380.0, 'performance_points': []},
    ])
    assert float(p.specifications['min_impeller_mm']) == 380.0
    assert float(p.specifications['max_impeller_mm']) == 380.0


def test_three_curves_ordering():
    """Test correct min/max with three curves"""
    p = _pump([
        {'impeller_diameter_mm': 406.4, 'performance_points': []},
        {'impeller_diameter_mm': 330.2, 'performance_points': []},
        {'impeller_diameter_mm': 380.0, 'performance_points': []},
    ])
    assert float(p.specifications['min_impeller_mm']) == 330.2
    assert float(p.specifications['max_impeller_mm']) == 406.4


def test_no_curves():
    """Test behavior with no curves"""
    p = _pump([])
    # Should default to 0 when no curves available
    assert float(p.specifications['min_impeller_mm']) == 0
    assert float(p.specifications['max_impeller_mm']) == 0


def test_invalid_impeller_data():
    """Test behavior with invalid impeller data"""
    p = _pump([
        {'impeller_diameter_mm': None, 'performance_points': []},
        {'impeller_size': 'invalid', 'performance_points': []},
        {'performance_points': []},  # No impeller field at all
    ])
    # Should default to 0 when no valid impeller data
    assert float(p.specifications['min_impeller_mm']) == 0
    assert float(p.specifications['max_impeller_mm']) == 0


def test_helper_function_directly():
    """Test the helper function directly"""
    curves = [
        {'impeller_diameter_mm': 330.2},
        {'impeller_diameter_mm': 406.4},
    ]
    min_mm, max_mm = compute_impeller_min_max_from_curves(curves)
    assert min_mm == 330.2
    assert max_mm == 406.4


def test_helper_function_with_strings():
    """Test helper function with string values"""
    curves = [
        {'impeller_size': '330.2'},
        {'impeller_size': '406.4'},
    ]
    min_mm, max_mm = compute_impeller_min_max_from_curves(curves)
    assert min_mm == 330.2
    assert max_mm == 406.4


def test_helper_function_empty_curves():
    """Test helper function with empty curves"""
    min_mm, max_mm = compute_impeller_min_max_from_curves([])
    assert min_mm is None
    assert max_mm is None


def test_helper_function_invalid_data():
    """Test helper function with invalid data"""
    curves = [
        {'impeller_diameter_mm': None},
        {'impeller_size': 'invalid'},
        {'other_field': 123},
    ]
    min_mm, max_mm = compute_impeller_min_max_from_curves(curves)
    assert min_mm is None
    assert max_mm is None


def test_real_world_8k_scenario():
    """Test scenario similar to 8K pump issue"""
    # Simulate 8K pump with two curves: 406.4mm and 330.2mm
    p = _pump([
        {'impeller_diameter_mm': 406.4, 'performance_points': [
            {'flow_m3hr': 366.64, 'head_m': 50.01, 'efficiency_pct': 75.0}
        ]},
        {'impeller_diameter_mm': 330.2, 'performance_points': [
            {'flow_m3hr': 250.0, 'head_m': 29.3, 'efficiency_pct': 70.0}
        ]},
    ])
    
    # Should show the full capability envelope
    assert float(p.specifications['min_impeller_mm']) == 330.2
    assert float(p.specifications['max_impeller_mm']) == 406.4
    
    # Verify the curves are available
    assert len(p.curves) == 2
    assert any(c['impeller_diameter_mm'] == 406.4 for c in p.curves)
    assert any(c['impeller_diameter_mm'] == 330.2 for c in p.curves)