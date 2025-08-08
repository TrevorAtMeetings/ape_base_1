"""
Brain System Monitoring Routes
===============================
Real-time monitoring of Brain system performance and metrics
"""

from flask import Blueprint, render_template, jsonify
import logging
import os

logger = logging.getLogger(__name__)

# Create blueprint
brain_monitor_bp = Blueprint('brain_monitor', __name__)

# Check if Brain is available
try:
    from ..pump_brain import get_pump_brain, BrainMetrics
    BRAIN_AVAILABLE = True
except ImportError:
    BRAIN_AVAILABLE = False
    logger.warning("Brain system not available for monitoring")


@brain_monitor_bp.route('/brain/status')
def brain_status():
    """Get Brain system status and metrics"""
    if not BRAIN_AVAILABLE:
        return jsonify({
            'status': 'unavailable',
            'message': 'Brain system not installed'
        }), 503
    
    try:
        brain = get_pump_brain()
        
        # Get comprehensive status
        status = brain.get_status()
        metrics = BrainMetrics.get_metrics()
        cache_stats = brain._cache.get_stats()
        
        # Calculate operation statistics
        operation_stats = {}
        for op_name, op_data in metrics.get('operations', {}).items():
            if op_data:
                durations = [d['duration_ms'] for d in op_data]
                operation_stats[op_name] = {
                    'count': len(op_data),
                    'avg_ms': sum(durations) / len(durations),
                    'min_ms': min(durations),
                    'max_ms': max(durations)
                }
        
        # Analyze discrepancies
        discrepancies = metrics.get('discrepancies', [])
        discrepancy_summary = {
            'total': len(discrepancies),
            'recent': discrepancies[-5:] if discrepancies else []
        }
        
        # Build response
        response = {
            'status': status['status'],
            'mode': status['mode'],
            'uptime_seconds': status['uptime_seconds'],
            'cache': {
                'hit_rate': cache_stats['hit_rate'],
                'size': cache_stats['size'],
                'max_size': cache_stats['max_size'],
                'hits': cache_stats['hits'],
                'misses': cache_stats['misses']
            },
            'operations': operation_stats,
            'discrepancies': discrepancy_summary,
            'errors': metrics.get('errors', [])[-10:]  # Last 10 errors
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting Brain status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@brain_monitor_bp.route('/brain/metrics')
def brain_metrics_page():
    """Display Brain metrics dashboard"""
    if not BRAIN_AVAILABLE:
        return render_template('brain_unavailable.html')
    
    try:
        brain = get_pump_brain()
        status = brain.get_status()
        
        return render_template('brain_metrics.html', 
                             brain_mode=status['mode'],
                             brain_status=status['status'])
    except:
        return render_template('brain_unavailable.html')


@brain_monitor_bp.route('/brain/toggle/<mode>')
def toggle_brain_mode(mode):
    """Toggle Brain mode (admin only)"""
    # Security check would go here in production
    
    if mode not in ['shadow', 'active', 'disabled']:
        return jsonify({'error': 'Invalid mode'}), 400
    
    # Set environment variable
    os.environ['BRAIN_MODE'] = mode
    
    # Log the change
    logger.info(f"Brain mode changed to: {mode}")
    
    return jsonify({
        'success': True,
        'new_mode': mode,
        'message': f'Brain mode set to {mode}'
    })


@brain_monitor_bp.route('/brain/clear_cache')
def clear_brain_cache():
    """Clear Brain cache (admin only)"""
    if not BRAIN_AVAILABLE:
        return jsonify({'error': 'Brain not available'}), 503
    
    try:
        brain = get_pump_brain()
        brain.clear_cache()
        
        return jsonify({
            'success': True,
            'message': 'Brain cache cleared'
        })
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


# Register the blueprint
def register_brain_monitor(app):
    """Register Brain monitoring routes with the Flask app"""
    app.register_blueprint(brain_monitor_bp)
    logger.info("Brain monitoring routes registered")