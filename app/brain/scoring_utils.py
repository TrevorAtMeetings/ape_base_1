"""
Scoring Utilities Module
========================
Utilities for pump selection scoring explanations and calculations
"""

import logging

logger = logging.getLogger(__name__)


class ScoringUtils:
    """Utility functions for pump selection scoring"""
    
    @staticmethod
    def get_scoring_reason(component: str, score: float, evaluation: dict) -> str:
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
                if score >= 45:
                    return f"Perfect BEP match: {qbp:.1f}% (95-105% optimal)"
                elif score >= 40:
                    return f"Excellent BEP match: {qbp:.1f}% ({0.90*100:.0f}-{1.10*100:.0f}% range)"
                elif score >= 30:
                    return f"Good BEP match: {qbp:.1f}% ({0.80*100:.0f}-{1.20*100:.0f}% range)"
                elif score >= 20:
                    return f"Acceptable BEP match: {qbp:.1f}% ({0.70*100:.0f}-{1.30*100:.0f}% range)"
                else:
                    return f"Poor BEP match: {qbp:.1f}% (outside optimal ranges)"
            
            elif component == 'efficiency':
                efficiency = evaluation.get('efficiency_pct', 0)
                if score >= 35:
                    return f"Excellent efficiency: {efficiency:.1f}% (≥{85:.0f}%)"
                elif score >= 30:
                    return f"Very good efficiency: {efficiency:.1f}% ({75:.0f}-{85:.0f}%)"
                elif score >= 25:
                    return f"Good efficiency: {efficiency:.1f}% ({65:.0f}-{75:.0f}%)"
                elif score >= 10:
                    return f"Acceptable efficiency: {efficiency:.1f}% ({45:.0f}-{65:.0f}%)"
                else:
                    return f"Low efficiency: {efficiency:.1f}% (<{45:.0f}%)"
            
            elif component == 'head_margin':
                margin_pct = evaluation.get('head_margin_pct', 0)
                if score >= 20:
                    return f"Perfect head margin: {margin_pct:.1f}% (≤{5:.0f}%)"
                elif score >= 15:
                    return f"Good head margin: {margin_pct:.1f}% ({5:.0f}-{10:.0f}%)"
                elif score >= 5:
                    return f"Acceptable head margin: {margin_pct:.1f}% ({10:.0f}-{15:.0f}%)"
                else:
                    return f"High head margin: {margin_pct:.1f}% (>{15:.0f}%)"
            
            elif component == 'head_oversizing_penalty':
                oversizing_pct = evaluation.get('bep_head_oversizing_pct', 0)
                if score == 0:
                    return f"No oversizing penalty: BEP head appropriately sized ({oversizing_pct:.1f}%)"
                elif score >= -15:
                    return f"Moderate oversizing penalty: BEP head {oversizing_pct:.1f}% above requirement"
                else:
                    return f"Severe oversizing penalty: BEP head {oversizing_pct:.1f}% above requirement"
            
            elif component == 'physical_limitation_penalty':
                if score == -50:
                    detail = evaluation.get('physical_limitation_detail', 'Unknown limitation')
                    return f"Cannot achieve required performance: {detail}"
                else:
                    return "Physical capability verified"
            
            elif component == 'trim_penalty':
                trim_pct = evaluation.get('trim_percent', 100)
                if score == -2:
                    return f"Small trim penalty: {trim_pct:.1f}% impeller (90-95%)"
                elif score == -5:
                    return f"Moderate trim penalty: {trim_pct:.1f}% impeller (85-90%)"
                elif score == -10:
                    return f"Large trim penalty: {trim_pct:.1f}% impeller (<85%)"
                else:
                    return f"Full impeller: {trim_pct:.1f}%"
            
            else:
                return f"Score: {score:.1f} pts"
                
        except Exception:
            return f"Score: {score:.1f} pts"