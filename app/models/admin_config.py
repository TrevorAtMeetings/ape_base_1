"""
Admin configuration models for pump selection system
"""
from datetime import datetime
from app import db


class ApplicationProfile(db.Model):
    """Application-specific configuration profiles"""
    __tablename__ = 'application_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    
    # Scoring weights (must total 100)
    bep_weight = db.Column(db.Float, nullable=False, default=40.0)
    efficiency_weight = db.Column(db.Float, nullable=False, default=30.0)
    head_margin_weight = db.Column(db.Float, nullable=False, default=15.0)
    npsh_weight = db.Column(db.Float, nullable=False, default=15.0)
    
    # Zone boundaries
    bep_optimal_min = db.Column(db.Float, nullable=False, default=0.95)
    bep_optimal_max = db.Column(db.Float, nullable=False, default=1.05)
    
    # Efficiency thresholds
    min_acceptable_efficiency = db.Column(db.Float, nullable=False, default=40.0)
    excellent_efficiency = db.Column(db.Float, nullable=False, default=85.0)
    good_efficiency = db.Column(db.Float, nullable=False, default=75.0)
    fair_efficiency = db.Column(db.Float, nullable=False, default=65.0)
    
    # Head margin preferences
    optimal_head_margin_max = db.Column(db.Float, nullable=False, default=5.0)
    acceptable_head_margin_max = db.Column(db.Float, nullable=False, default=10.0)
    
    # NPSH safety factors
    npsh_excellent_margin = db.Column(db.Float, nullable=False, default=3.0)
    npsh_good_margin = db.Column(db.Float, nullable=False, default=1.5)
    npsh_minimum_margin = db.Column(db.Float, nullable=False, default=0.5)
    
    # Modification preferences
    speed_variation_penalty_factor = db.Column(db.Float, nullable=False, default=15.0)
    trimming_penalty_factor = db.Column(db.Float, nullable=False, default=10.0)
    max_acceptable_trim_pct = db.Column(db.Float, nullable=False, default=75.0)
    
    # Reporting preferences
    top_recommendation_threshold = db.Column(db.Float, nullable=False, default=70.0)
    acceptable_option_threshold = db.Column(db.Float, nullable=False, default=50.0)
    near_miss_count = db.Column(db.Integer, nullable=False, default=5)
    
    # Metadata
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(100))
    
    def validate_weights(self):
        """Ensure scoring weights total 100"""
        total = self.bep_weight + self.efficiency_weight + self.head_margin_weight + self.npsh_weight
        return abs(total - 100.0) < 0.01  # Allow small floating point differences
    
    def to_dict(self):
        """Convert to dictionary for easy access"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'scoring_weights': {
                'bep': self.bep_weight,
                'efficiency': self.efficiency_weight,
                'head_margin': self.head_margin_weight,
                'npsh': self.npsh_weight
            },
            'zones': {
                'bep_optimal': (self.bep_optimal_min, self.bep_optimal_max),
                'efficiency_thresholds': {
                    'minimum': self.min_acceptable_efficiency,
                    'fair': self.fair_efficiency,
                    'good': self.good_efficiency,
                    'excellent': self.excellent_efficiency
                },
                'head_margin': {
                    'optimal_max': self.optimal_head_margin_max,
                    'acceptable_max': self.acceptable_head_margin_max
                },
                'npsh_margins': {
                    'excellent': self.npsh_excellent_margin,
                    'good': self.npsh_good_margin,
                    'minimum': self.npsh_minimum_margin
                }
            },
            'modifications': {
                'speed_penalty': self.speed_variation_penalty_factor,
                'trim_penalty': self.trimming_penalty_factor,
                'max_trim_pct': self.max_acceptable_trim_pct
            },
            'reporting': {
                'top_threshold': self.top_recommendation_threshold,
                'acceptable_threshold': self.acceptable_option_threshold,
                'near_miss_count': self.near_miss_count
            }
        }


class LockedEngineeringConstants(db.Model):
    """Immutable engineering constants - for reference only"""
    __tablename__ = 'engineering_constants'
    
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    value = db.Column(db.String(200), nullable=False)
    unit = db.Column(db.String(50))
    description = db.Column(db.Text)
    formula = db.Column(db.Text)
    
    # Make it clear these are immutable
    is_locked = db.Column(db.Boolean, default=True, nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('category', 'name', name='_category_name_uc'),
    )


class ConfigurationAudit(db.Model):
    """Track all configuration changes"""
    __tablename__ = 'configuration_audits'
    
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('application_profiles.id'))
    changed_by = db.Column(db.String(100), nullable=False)
    change_type = db.Column(db.String(50), nullable=False)  # create, update, delete
    field_name = db.Column(db.String(100))
    old_value = db.Column(db.String(200))
    new_value = db.Column(db.String(200))
    reason = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    profile = db.relationship('ApplicationProfile', backref='audit_logs')