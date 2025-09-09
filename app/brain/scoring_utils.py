"""
Scoring Utilities Module
========================
Utilities for pump selection scoring explanations and calculations
"""

import logging
from .config_manager import config

logger = logging.getLogger(__name__)


class ScoringUtils:
    """Utility functions for pump selection scoring"""
    
    def __init__(self):
        """Initialize with config values for scoring thresholds."""
        # Load configuration values for scoring utilities
        # BEP proximity scores
        self.bep_score_excellent = config.get('scoring_utils', 'maximum_bep_proximity_score_excellent_range')
        self.bep_score_high = config.get('scoring_utils', 'high_bep_proximity_score_good_range')
        self.bep_score_medium = config.get('scoring_utils', 'medium_bep_proximity_score_fair_range')
        self.bep_score_low = config.get('scoring_utils', 'low_bep_proximity_score_acceptable_range')
        
        # BEP range factors
        self.bep_excellent_min = config.get('scoring_utils', 'bep_excellent_range_minimum_factor_90')
        self.bep_excellent_max = config.get('scoring_utils', 'bep_excellent_range_maximum_factor_110')
        self.bep_good_min = config.get('scoring_utils', 'bep_good_range_minimum_factor_80')
        self.bep_good_max = config.get('scoring_utils', 'bep_good_range_maximum_factor_120')
        self.bep_fair_min = config.get('scoring_utils', 'bep_fair_range_minimum_factor_70')
        self.bep_fair_max = config.get('scoring_utils', 'bep_fair_range_maximum_factor_130')
        
        # BEP optimal ranges
        self.bep_optimal_min = config.get('scoring_utils', 'bep_optimal_range_minimum_percentage')
        self.bep_optimal_max = config.get('scoring_utils', 'bep_optimal_range_maximum_percentage')
        
        # Efficiency scores
        self.eff_score_excellent = config.get('scoring_utils', 'maximum_efficiency_score_excellent_efficiency')
        self.eff_score_high = config.get('scoring_utils', 'high_efficiency_score_good_efficiency')
        self.eff_score_medium = config.get('scoring_utils', 'medium_efficiency_score_fair_efficiency')
        self.eff_score_low = config.get('scoring_utils', 'low_efficiency_score_poor_efficiency')
        
        # Efficiency thresholds
        self.eff_excellent_threshold = config.get('scoring_utils', 'excellent_efficiency_threshold_percentage')
        self.eff_good_threshold = config.get('scoring_utils', 'good_efficiency_threshold_percentage')
        self.eff_fair_threshold = config.get('scoring_utils', 'fair_efficiency_threshold_percentage')
        self.eff_poor_threshold = config.get('scoring_utils', 'poor_efficiency_threshold_percentage')
        
        # Head margin scores
        self.head_score_max = config.get('scoring_utils', 'maximum_head_margin_score')
        self.head_score_high = config.get('scoring_utils', 'high_head_margin_score')
        self.head_score_low = config.get('scoring_utils', 'low_head_margin_score')
        
        # Head margin thresholds
        self.head_excellent_threshold = config.get('scoring_utils', 'head_margin_excellent_threshold_percentage')
        self.head_good_threshold = config.get('scoring_utils', 'head_margin_good_threshold_percentage')
        self.head_fair_threshold = config.get('scoring_utils', 'head_margin_fair_threshold_percentage')
        
        # Penalty scores
        self.physical_limitation_penalty = config.get('scoring_utils', 'physical_limitation_penalty_score')
        self.trim_light_penalty = config.get('scoring_utils', 'light_trim_penalty_score_9095_range')
        self.trim_moderate_penalty = config.get('scoring_utils', 'moderate_trim_penalty_score_8590_range')
        self.trim_heavy_penalty = config.get('scoring_utils', 'heavy_trim_penalty_score_below_85_range')
        self.oversizing_moderate_penalty = config.get('scoring_utils', 'moderate_oversizing_penalty_threshold')
        
        # Trim thresholds
        self.trim_light_threshold = config.get('scoring_utils', 'light_trim_threshold_percentage')
        self.trim_minimal_threshold = config.get('scoring_utils', 'minimal_trim_threshold_percentage')
    
    def get_scoring_reason(self, component: str, score: float, evaluation: dict) -> str:
        """
        Provide detailed reasoning for each scoring component.
        
        Args:
            component: The scoring component name
            score: The score value
            evaluation: The evaluation dictionary containing context
        
        Returns:
            Detailed reasoning string for the score
        """
        try:
            if component == 'bep_proximity':
                qbp = evaluation.get('qbp_percent', 0)
                if score >= self.bep_score_excellent:
                    return f"Perfect BEP match: {qbp:.1f}% ({self.bep_optimal_min}-{self.bep_optimal_max}% optimal)"
                elif score >= self.bep_score_high:
                    return f"Excellent BEP match: {qbp:.1f}% ({self.bep_excellent_min*100:.0f}-{self.bep_excellent_max*100:.0f}% range)"
                elif score >= self.bep_score_medium:
                    return f"Good BEP match: {qbp:.1f}% ({self.bep_good_min*100:.0f}-{self.bep_good_max*100:.0f}% range)"
                elif score >= self.bep_score_low:
                    return f"Acceptable BEP match: {qbp:.1f}% ({self.bep_fair_min*100:.0f}-{self.bep_fair_max*100:.0f}% range)"
                else:
                    return f"Poor BEP match: {qbp:.1f}% (outside optimal ranges)"
            
            elif component == 'efficiency':
                efficiency = evaluation.get('efficiency_pct', 0)
                if score >= self.eff_score_excellent:
                    return f"Excellent efficiency: {efficiency:.1f}% (≥{self.eff_excellent_threshold:.0f}%)"
                elif score >= self.eff_score_high:
                    return f"Very good efficiency: {efficiency:.1f}% ({self.eff_good_threshold:.0f}-{self.eff_excellent_threshold:.0f}%)"
                elif score >= self.eff_score_medium:
                    return f"Good efficiency: {efficiency:.1f}% ({self.eff_fair_threshold:.0f}-{self.eff_good_threshold:.0f}%)"
                elif score >= self.eff_score_low:
                    return f"Acceptable efficiency: {efficiency:.1f}% ({self.eff_poor_threshold:.0f}-{self.eff_fair_threshold:.0f}%)"
                else:
                    return f"Low efficiency: {efficiency:.1f}% (<{self.eff_poor_threshold:.0f}%)"
            
            elif component == 'head_margin':
                margin_pct = evaluation.get('head_margin_pct', 0)
                if score >= self.head_score_max:
                    return f"Perfect head margin: {margin_pct:.1f}% (≤{self.head_excellent_threshold:.0f}%)"
                elif score >= self.head_score_high:
                    return f"Good head margin: {margin_pct:.1f}% ({self.head_excellent_threshold:.0f}-{self.head_good_threshold:.0f}%)"
                elif score >= self.head_score_low:
                    return f"Acceptable head margin: {margin_pct:.1f}% ({self.head_good_threshold:.0f}-{self.head_fair_threshold:.0f}%)"
                else:
                    return f"High head margin: {margin_pct:.1f}% (>{self.head_fair_threshold:.0f}%)"
            
            elif component == 'head_oversizing_penalty':
                oversizing_pct = evaluation.get('bep_head_oversizing_pct', 0)
                if score == 0:
                    return f"No oversizing penalty: BEP head appropriately sized ({oversizing_pct:.1f}%)"
                elif score >= self.oversizing_moderate_penalty:
                    return f"Moderate oversizing penalty: BEP head {oversizing_pct:.1f}% above requirement"
                else:
                    return f"Severe oversizing penalty: BEP head {oversizing_pct:.1f}% above requirement"
            
            elif component == 'physical_limitation_penalty':
                if score == self.physical_limitation_penalty:
                    detail = evaluation.get('physical_limitation_detail', 'Unknown limitation')
                    return f"Cannot achieve required performance: {detail}"
                else:
                    return "Physical capability verified"
            
            elif component == 'trim_penalty':
                trim_pct = evaluation.get('trim_percent', 100)
                if score == self.trim_light_penalty:
                    return f"Small trim penalty: {trim_pct:.1f}% impeller ({self.trim_light_threshold}-{self.trim_minimal_threshold}%)"
                elif score == self.trim_moderate_penalty:
                    return f"Moderate trim penalty: {trim_pct:.1f}% impeller (85-{self.trim_light_threshold}%)"
                elif score == self.trim_heavy_penalty:
                    return f"Large trim penalty: {trim_pct:.1f}% impeller (<85%)"
                else:
                    return f"Full impeller: {trim_pct:.1f}%"
            
            else:
                return f"Score: {score:.1f} pts"
                
        except Exception:
            return f"Score: {score:.1f} pts"