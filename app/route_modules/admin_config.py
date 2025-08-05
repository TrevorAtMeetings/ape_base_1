"""
Admin configuration routes
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
import logging
from app.admin_config_service import admin_config_service
from app.database import admin_db

logger = logging.getLogger(__name__)

admin_config_bp = Blueprint('admin_config', __name__, url_prefix='/admin/config')


@admin_config_bp.route('/')
def index():
    """Admin configuration dashboard"""
    # Check admin access (basic implementation)
    # Temporarily disabled for demonstration
    # if not session.get('is_admin'):
    #     flash('Admin access required', 'error')
    #     return redirect(url_for('admin.login'))
    
    profiles = admin_config_service.get_all_profiles()
    constants = admin_config_service.get_engineering_constants()
    
    return render_template('admin/config_dashboard.html',
                         profiles=profiles,
                         constants=constants)


@admin_config_bp.route('/profile/<int:profile_id>')
def profile_details(profile_id):
    """View/edit specific profile"""
    # Temporarily disabled for demonstration
    # if not session.get('is_admin'):
    #     return redirect(url_for('admin.login'))
    
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
        }
    }
    
    audit_log = admin_config_service.get_audit_log(profile_id, limit=50)
    
    return render_template('admin/profile_editor.html',
                         profile=profile,
                         audit_log=audit_log)


@admin_config_bp.route('/api/profile/<int:profile_id>', methods=['GET', 'POST'])
def api_profile(profile_id):
    """API endpoint for profile operations"""
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    if request.method == 'GET':
        # Get profile details
        with admin_db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM admin_config.application_profiles
                    WHERE id = %s
                """, (profile_id,))
                columns = [desc[0] for desc in cursor.description]
                row = cursor.fetchone()
                if row:
                    profile = dict(zip(columns, row))
                    return jsonify(profile)
                return jsonify({'error': 'Profile not found'}), 404
    
    elif request.method == 'POST':
        # Update profile
        updates = request.json
        user = session.get('username', 'admin')
        reason = updates.pop('reason', None)
        
        success = admin_config_service.update_profile(profile_id, updates, user, reason)
        
        if success:
            return jsonify({'success': True, 'message': 'Profile updated successfully'})
        else:
            return jsonify({'error': 'Failed to update profile'}), 400


@admin_config_bp.route('/api/profiles', methods=['GET', 'POST'])
def api_profiles():
    """API endpoint for profile list operations"""
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    if request.method == 'GET':
        profiles = admin_config_service.get_all_profiles()
        return jsonify(profiles)
    
    elif request.method == 'POST':
        # Create new profile
        profile_data = request.json
        user = session.get('username', 'admin')
        
        profile_id = admin_config_service.create_profile(profile_data, user)
        
        if profile_id:
            return jsonify({'success': True, 'profile_id': profile_id})
        else:
            return jsonify({'error': 'Failed to create profile'}), 400


@admin_config_bp.route('/api/constants')
def api_constants():
    """Get engineering constants"""
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
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
def init_database():
    """Initialize admin config database tables"""
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        admin_db.init_tables()
        admin_db.seed_engineering_constants()
        admin_db.seed_default_profiles()
        return jsonify({'success': True, 'message': 'Database initialized successfully'})
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return jsonify({'error': str(e)}), 500