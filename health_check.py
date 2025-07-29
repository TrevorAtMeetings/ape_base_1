"""
Health check endpoint for deployment monitoring
"""
import os
import time
from flask import jsonify, request
from app import app

@app.route('/health')
def health_check():
    """Health check endpoint for load balancers and monitoring"""
    
    try:
        # Basic application health
        health_status = {
            'status': 'healthy',
            'timestamp': time.time(),
            'version': '1.0.0',
            'environment': os.environ.get('FLASK_ENV', 'unknown')
        }
        
        # Check database connectivity
        try:
            from app.pump_repository import PumpRepository
            repo = PumpRepository()
            # Simple connectivity test
            pump_count = len(repo.get_all_pumps())
            health_status['database'] = {
                'status': 'connected',
                'pump_count': pump_count
            }
        except Exception as e:
            health_status['database'] = {
                'status': 'error',
                'error': str(e)
            }
            health_status['status'] = 'degraded'
        
        # Check required environment variables
        required_vars = ['SESSION_SECRET', 'DATABASE_URL']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            health_status['environment_variables'] = {
                'status': 'missing',
                'missing': missing_vars
            }
            health_status['status'] = 'unhealthy'
        else:
            health_status['environment_variables'] = {
                'status': 'configured'
            }
        
        # Return appropriate HTTP status
        status_code = 200
        if health_status['status'] == 'degraded':
            status_code = 200  # Still operational
        elif health_status['status'] == 'unhealthy':
            status_code = 503  # Service unavailable
        
        return jsonify(health_status), status_code
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': time.time()
        }), 500

@app.route('/ready')
def readiness_check():
    """Readiness check for Kubernetes/container orchestration"""
    
    try:
        # Check if application is ready to serve requests
        from app.pump_repository import PumpRepository
        
        # Try to initialize repository
        repo = PumpRepository()
        
        return jsonify({
            'status': 'ready',
            'timestamp': time.time()
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'not_ready',
            'error': str(e),
            'timestamp': time.time()
        }), 503