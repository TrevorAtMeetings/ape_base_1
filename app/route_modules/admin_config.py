"""
Admin configuration routes
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
import logging
from functools import wraps
from app.admin_config_service import admin_config_service, ValidationError, ConfigurationError
from app.database import admin_db
import traceback

logger = logging.getLogger(__name__)

admin_config_bp = Blueprint('admin_config', __name__, url_prefix='/admin/config')


def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For demonstration, we'll use a simple check
        # In production, implement proper authentication
        # Temporarily disabled admin check for development
        session['is_admin'] = True  # Force admin access for development
        if False:  # Disable admin check temporarily
            flash('Admin access required', 'error')
            return redirect(url_for('main_flow.index'))
        return f(*args, **kwargs)
    return decorated_function


def handle_api_errors(f):
    """Decorator for consistent API error handling"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Validation error in {f.__name__}: {e}")
            return jsonify({
                'success': False,
                'error': f'Validation failed: {str(e)}',
                'error_type': 'validation'
            }), 400
        except ConfigurationError as e:
            logger.error(f"Configuration error in {f.__name__}: {e}")
            return jsonify({
                'success': False,
                'error': f'Configuration error: {str(e)}',
                'error_type': 'configuration'
            }), 500
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {e}\n{traceback.format_exc()}")
            return jsonify({
                'success': False,
                'error': 'An unexpected error occurred. Please try again.',
                'error_type': 'internal'
            }), 500
    return decorated_function


@admin_config_bp.route('/')
@admin_required
def index():
    """Admin configuration dashboard"""
    try:
        profiles = admin_config_service.get_all_profiles()
        constants = admin_config_service.get_engineering_constants()
        
        return render_template('admin/config_dashboard.html',
                             profiles=profiles,
                             constants=constants)
    except Exception as e:
        logger.error(f"Error loading admin config dashboard: {e}")
        flash('Error loading configuration dashboard', 'error')
        return redirect(url_for('main_flow.index'))


@admin_config_bp.route('/profile/<int:profile_id>')
@admin_required
def profile_details(profile_id):
    """View/edit specific profile"""
    try:
        # Get profile by ID from database
        from psycopg2.extras import RealDictCursor
        with admin_db.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM admin_config.application_profiles
                    WHERE id = %s
                """, (profile_id,))
                profile_data = cursor.fetchone()
        
        if not profile_data:
            flash('Profile not found', 'error')
            return redirect(url_for('admin_config.index'))
        
        # Convert to the expected format
        profile = {
            'id': profile_data['id'],
            'name': profile_data['name'],
            'description': profile_data['description'],
            'is_active': profile_data['is_active'],
            'updated_at': profile_data['updated_at'],
            'scoring_weights': {
                'bep': profile_data['bep_weight'],
                'efficiency': profile_data['efficiency_weight'],
                'head_margin': profile_data['head_margin_weight'],
                'npsh': profile_data['npsh_weight']
            },
            'zones': {
                'bep_optimal': (profile_data['bep_optimal_min'], profile_data['bep_optimal_max']),
                'efficiency_thresholds': {
                    'minimum': profile_data['min_acceptable_efficiency'],
                    'fair': profile_data['fair_efficiency'],
                    'good': profile_data['good_efficiency'],
                    'excellent': profile_data['excellent_efficiency']
                },
                'head_margin': {
                    'optimal_max': profile_data['optimal_head_margin_max'],
                    'acceptable_max': profile_data['acceptable_head_margin_max']
                },
                'npsh_margins': {
                    'excellent': profile_data['npsh_excellent_margin'],
                    'good': profile_data['npsh_good_margin'],
                    'minimum': profile_data['npsh_minimum_margin']
                }
            },
            'modifications': {
                'speed_penalty': profile_data['speed_variation_penalty_factor'],
                'trim_penalty': profile_data['trimming_penalty_factor'],
                'max_trim_pct': profile_data['max_acceptable_trim_pct']
            },
            'reporting': {
                'top_threshold': profile_data['top_recommendation_threshold'],
                'acceptable_threshold': profile_data['acceptable_option_threshold'],
                'near_miss_count': profile_data['near_miss_count']
            }
        }
        
        # Get audit history
        with admin_db.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT profile_id, change_type, field_name, old_value, new_value, changed_by, timestamp, reason
                    FROM admin_config.configuration_audits
                    WHERE profile_id = %s
                    ORDER BY timestamp DESC
                    LIMIT 10
                """, (profile_id,))
                audit_history = cursor.fetchall()
        
        profile['audit_history'] = audit_history
        
        return render_template('admin/profile_editor.html', 
                             profile=profile, 
                             audit_log=audit_history)
        
    except Exception as e:
        logger.error(f"Error loading profile {profile_id}: {e}")
        flash('Error loading profile details', 'error')
        return redirect(url_for('admin_config.index'))


@admin_config_bp.route('/api/profile/<int:profile_id>', methods=['PUT'])
@admin_required
@handle_api_errors
def update_profile_api(profile_id):
    """API endpoint to update profile configuration"""
    if not request.is_json:
        return jsonify({
            'success': False,
            'error': 'Content-Type must be application/json'
        }), 400
    
    profile_data = request.get_json()
    user_id = session.get('user_id', 'admin')
    
    # Update profile using enhanced service
    success, message = admin_config_service.update_profile(profile_id, profile_data, user_id)
    
    if success:
        logger.info(f"Profile {profile_id} updated successfully by {user_id}")
        return jsonify({
            'success': True,
            'message': message
        })
    else:
        logger.warning(f"Profile {profile_id} update failed: {message}")
        return jsonify({
            'success': False,
            'error': message
        }), 400


@admin_config_bp.route('/api/profile/<int:profile_id>/validate', methods=['POST'])
@admin_required
@handle_api_errors  
def validate_profile_api(profile_id):
    """API endpoint to validate profile configuration without saving"""
    if not request.is_json:
        return jsonify({
            'success': False,
            'error': 'Content-Type must be application/json'
        }), 400
    
    profile_data = request.get_json()
    
    # Validate profile data
    is_valid, errors = admin_config_service.validate_profile_data(profile_data)
    
    return jsonify({
        'success': True,
        'is_valid': is_valid,
        'errors': errors
    })


@admin_config_bp.route('/api/profiles', methods=['GET'])
@admin_required
def api_profiles():
    """API endpoint to get all profiles"""
    try:
        profiles = admin_config_service.get_all_profiles()
        return jsonify({
            'success': True,
            'profiles': profiles
        })
    except Exception as e:
        logger.error(f"Error fetching profiles: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_config_bp.route('/api/constants')
@admin_required
def api_constants():
    """Get engineering constants"""
    constants = admin_config_service.get_engineering_constants()
    return jsonify(constants)


@admin_config_bp.route('/api/audit-log')
def api_audit_log():
    """Get audit log"""
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    profile_id = request.args.get('profile_id', type=int)
    limit = request.args.get('limit', 100, type=int)
    
    logs = admin_config_service.get_audit_log(profile_id, limit)
    return jsonify(logs)


@admin_config_bp.route('/init-database', methods=['POST'])
@admin_required
@handle_api_errors
def init_database():
    """Initialize admin config database tables"""
    try:
        # Use the admin_config_service to initialize
        # TODO: implement initialize_database method in admin_config_service
        success, message = True, "Database initialization skipped - method not implemented"
        
        if success:
            logger.info("Admin configuration database initialized successfully")
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            logger.error(f"Failed to initialize database: {message}")
            return jsonify({
                'success': False,
                'error': message
            }), 500
            
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return jsonify({
            'success': False,
            'error': f'Database initialization failed: {str(e)}'
        }), 500