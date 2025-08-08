"""
Brain System Monitoring Dashboard
==================================
Real-time monitoring and analytics for Brain system performance.
Priority 1: Stability and Monitoring (Hypercare Phase)

Author: APE Pumps Engineering
Date: August 2025
"""

from flask import Blueprint, render_template, jsonify
from datetime import datetime, timedelta
import logging
import statistics
from typing import Dict, List, Any

# Import Brain metrics
from app.pump_brain import BrainMetrics, get_pump_brain
from app.pump_repository import get_pump_repository

logger = logging.getLogger(__name__)

# Create blueprint
brain_monitoring_bp = Blueprint('brain_monitoring', __name__, url_prefix='/brain')


@brain_monitoring_bp.route('/metrics')
def metrics_dashboard():
    """
    Display Brain system metrics dashboard.
    Key metrics for hypercare phase:
    - Response times for critical operations
    - Error rates and types
    - Cache hit rates
    - Discrepancy tracking
    """
    try:
        return render_template('brain/metrics_dashboard.html')
    except Exception as e:
        logger.error(f"Error rendering metrics dashboard: {str(e)}")
        return f"Error loading dashboard: {str(e)}", 500


@brain_monitoring_bp.route('/api/metrics')
def get_metrics_api():
    """
    API endpoint for real-time metrics data.
    Returns JSON data for dashboard updates.
    """
    try:
        metrics = BrainMetrics.get_summary()
        
        # Calculate response time statistics
        operation_stats = {}
        for op_name, operations in metrics.get('operations', {}).items():
            if operations:
                durations = [op['duration_ms'] for op in operations[-100:]]  # Last 100 ops
                operation_stats[op_name] = {
                    'count': len(operations),
                    'avg_ms': round(statistics.mean(durations), 2) if durations else 0,
                    'max_ms': round(max(durations), 2) if durations else 0,
                    'min_ms': round(min(durations), 2) if durations else 0,
                    'p95_ms': round(statistics.quantiles(durations, n=20)[18], 2) if len(durations) > 2 else 0,
                    'last_run': operations[-1]['timestamp'] if operations else None
                }
        
        # Calculate error rates
        recent_errors = [e for e in metrics.get('errors', []) if 
                        datetime.fromisoformat(e['timestamp']) > datetime.now() - timedelta(hours=1)]
        
        # Get cache statistics
        brain = get_pump_brain(get_pump_repository())
        cache_stats = brain.cache.get_stats() if hasattr(brain, 'cache') else {}
        
        # Count discrepancies
        recent_discrepancies = [d for d in metrics.get('discrepancies', []) if
                               datetime.fromisoformat(d['timestamp']) > datetime.now() - timedelta(hours=1)]
        
        # Prepare response
        response_data = {
            'timestamp': datetime.now().isoformat(),
            'status': 'active',  # Brain is now active!
            'operation_stats': operation_stats,
            'error_rate': {
                'last_hour': len(recent_errors),
                'total': len(metrics.get('errors', [])),
                'recent_errors': recent_errors[-5:]  # Last 5 errors
            },
            'cache_performance': cache_stats,
            'discrepancies': {
                'last_hour': len(recent_discrepancies),
                'total': len(metrics.get('discrepancies', [])),
                'recent': recent_discrepancies[-5:]  # Last 5 discrepancies
            },
            'health_checks': {
                'response_time_ok': all(
                    stats.get('avg_ms', 0) < 200 
                    for stats in operation_stats.values()
                ),
                'error_rate_ok': len(recent_errors) < 10,  # Less than 10 errors/hour
                'cache_hit_rate_ok': cache_stats.get('hit_rate', 0) > 0.5  # >50% cache hits
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        return jsonify({'error': str(e)}), 500


@brain_monitoring_bp.route('/api/performance/<operation>')
def get_operation_performance(operation):
    """
    Get detailed performance metrics for a specific operation.
    Useful for drilling down into performance issues.
    """
    try:
        metrics = BrainMetrics.get_summary()
        operations = metrics.get('operations', {}).get(operation, [])
        
        if not operations:
            return jsonify({'error': f'No data for operation: {operation}'}), 404
        
        # Get last 100 operations
        recent_ops = operations[-100:]
        
        # Prepare time series data for charts
        time_series = [
            {
                'timestamp': op['timestamp'],
                'duration_ms': op['duration_ms']
            }
            for op in recent_ops
        ]
        
        # Calculate statistics
        durations = [op['duration_ms'] for op in recent_ops]
        
        response_data = {
            'operation': operation,
            'time_series': time_series,
            'statistics': {
                'count': len(operations),
                'recent_count': len(recent_ops),
                'avg_ms': round(statistics.mean(durations), 2),
                'median_ms': round(statistics.median(durations), 2),
                'stdev_ms': round(statistics.stdev(durations), 2) if len(durations) > 1 else 0,
                'p95_ms': round(statistics.quantiles(durations, n=20)[18], 2) if len(durations) > 2 else 0,
                'p99_ms': round(statistics.quantiles(durations, n=100)[98], 2) if len(durations) > 2 else 0,
                'max_ms': round(max(durations), 2),
                'min_ms': round(min(durations), 2)
            },
            'performance_status': 'good' if statistics.mean(durations) < 200 else 'needs_attention'
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error getting operation performance: {str(e)}")
        return jsonify({'error': str(e)}), 500


@brain_monitoring_bp.route('/health')
def health_check():
    """
    Simple health check endpoint for monitoring tools.
    """
    try:
        brain = get_pump_brain(get_pump_repository())
        
        return jsonify({
            'status': 'healthy',
            'mode': 'active',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@brain_monitoring_bp.route('/api/feedback', methods=['POST'])
def collect_feedback():
    """
    Collect user feedback about Brain selections.
    This is crucial for validating that "smarter" decisions are genuinely better.
    """
    from flask import request
    
    try:
        feedback = request.json
        
        # Log feedback for analysis
        logger.info(f"User feedback received: {feedback}")
        
        # Store feedback in metrics
        BrainMetrics.record_feedback(feedback)
        
        return jsonify({
            'status': 'success',
            'message': 'Feedback recorded'
        })
        
    except Exception as e:
        logger.error(f"Error recording feedback: {str(e)}")
        return jsonify({'error': str(e)}), 500


# Export blueprint
__all__ = ['brain_monitoring_bp']