"""
Impeller diameter utilities for ensuring curve-spec consistency
"""

from typing import Iterable, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def compute_impeller_min_max_from_curves(curves: Iterable[dict]) -> Tuple[Optional[float], Optional[float]]:
    """Return (min_mm, max_mm) using curve['impeller_diameter_mm'] or curve['impeller_size'] when it holds a numeric mm string.
    
    Args:
        curves: Iterable of curve dictionaries containing impeller diameter information
        
    Returns:
        Tuple of (min_diameter_mm, max_diameter_mm) or (None, None) if no valid diameters found
    """
    vals = []
    for c in curves or []:
        raw = c.get('impeller_diameter_mm')
        if raw is None:
            raw = c.get('impeller_size')
        
        # Minimal parsing: accept int/float or numeric strings in mm
        try:
            if raw is None: 
                continue
            mm = float(raw) if isinstance(raw, (int, float)) else float(str(raw).strip())
            if mm > 0:
                vals.append(mm)
        except (ValueError, TypeError):
            continue
    
    if not vals:
        return None, None
    return min(vals), max(vals)