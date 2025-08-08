"""
Selection Intelligence Module
=============================
Consolidates pump selection logic from catalog_engine.py
"""

import logging
from typing import Dict, List, Any, Optional
import numpy as np
from ..data_models import SiteRequirements, PumpEvaluation, ExclusionReason

logger = logging.getLogger(__name__)


class SelectionIntelligence:
    """Intelligence for pump selection and ranking"""
    
    def __init__(self, brain):
        """
        Initialize with reference to main Brain.
        
        Args:
            brain: Parent PumpBrain instance
        """
        self.brain = brain
        
        # Selection parameters (from catalog_engine)
        self.scoring_weights = {
            'bep_proximity': 40,
            'efficiency': 30,
            'head_margin': 15,
            'npsh_margin': 15
        }
        
        # Operating constraints
        self.min_trim_percent = 85.0
        self.max_trim_percent = 100.0
        self.npsh_safety_factor = 1.5
        self.qbp_min_percent = 60.0
        self.qbp_max_percent = 130.0
    
    def find_best_pumps(self, flow: float, head: float, 
                       constraints: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Find best pumps for given conditions.
        
        Args:
            flow: Required flow rate (m³/hr)
            head: Required head (m)
            constraints: Optional constraints
        
        Returns:
            Ranked list of pump recommendations
        """
        if not self.brain.repository:
            logger.error("Repository not available for pump selection")
            return []
        
        constraints = constraints or {}
        
        # Get all pumps from repository
        pump_models = self.brain.repository.get_pump_models()
        if not pump_models:
            logger.warning("No pump models available in repository")
            return []
        
        evaluations = []
        
        for pump_data in pump_models:
            try:
                # Evaluate each pump
                evaluation = self.evaluate_single_pump(pump_data, flow, head)
                
                # Apply constraints
                if constraints.get('npsh_available'):
                    npsh_available = constraints['npsh_available']
                    if evaluation.get('npshr_m', 0) > npsh_available / self.npsh_safety_factor:
                        evaluation['feasible'] = False
                        evaluation['exclusion_reasons'].append('NPSH insufficient')
                
                if constraints.get('max_power_kw'):
                    max_power = constraints['max_power_kw']
                    if evaluation.get('power_kw', 0) > max_power:
                        evaluation['feasible'] = False
                        evaluation['exclusion_reasons'].append('Power exceeds limit')
                
                evaluations.append(evaluation)
                
            except Exception as e:
                logger.error(f"Error evaluating pump {pump_data.get('pump_code')}: {str(e)}")
                continue
        
        # Filter feasible pumps
        feasible_pumps = [e for e in evaluations if e.get('feasible', False)]
        
        # Sort by score (descending)
        feasible_pumps.sort(key=lambda x: x.get('total_score', 0), reverse=True)
        
        # Return top results (match legacy which returns 5)
        max_results = constraints.get('max_results', 5)
        return feasible_pumps[:max_results]
    
    def evaluate_single_pump(self, pump_data: Dict[str, Any], 
                            flow: float, head: float) -> Dict[str, Any]:
        """
        Evaluate a single pump at operating conditions.
        
        Args:
            pump_data: Pump data dictionary
            flow: Operating flow rate
            head: Operating head
        
        Returns:
            Evaluation results with scoring
        """
        evaluation = {
            'pump_code': pump_data.get('pump_code'),
            'pump_name': pump_data.get('pump_name'),
            'feasible': True,
            'exclusion_reasons': [],
            'score_components': {},
            'total_score': 0.0
        }
        
        try:
            # Get pump specifications
            specs = pump_data.get('specifications', {})
            
            # Check BEP proximity
            bep_flow = specs.get('bep_flow_m3hr', 0)
            bep_head = specs.get('bep_head_m', 0)
            
            if bep_flow > 0 and bep_head > 0:
                # Calculate QBP (% of BEP flow)
                qbp = (flow / bep_flow) * 100
                
                # Check QBP gates
                if qbp < self.qbp_min_percent or qbp > self.qbp_max_percent:
                    evaluation['feasible'] = False
                    evaluation['exclusion_reasons'].append(f'QBP {qbp:.0f}% outside range')
                    return evaluation
                
                # BEP proximity score
                if 95 <= qbp <= 105:
                    bep_score = 100
                elif 85 <= qbp <= 115:
                    bep_score = 80 - abs(qbp - 100) * 2
                else:
                    bep_score = max(0, 60 - abs(qbp - 100))
                
                evaluation['score_components']['bep_proximity'] = bep_score * (self.scoring_weights['bep_proximity'] / 100)
                evaluation['qbp_percent'] = qbp
            
            # Get performance at operating point
            performance = self.brain.performance.calculate_at_point(pump_data, flow, head)
            
            # Validate performance data contract
            if performance:
                required_keys = ['meets_requirements', 'efficiency_pct', 'head_m', 'power_kw']
                missing_keys = [k for k in required_keys if k not in performance]
                if missing_keys:
                    logger.error(f"Performance data for pump {pump_data.get('pump_code')} is missing keys: {missing_keys}")
                    evaluation['feasible'] = False
                    evaluation['exclusion_reasons'].append('Invalid performance data')
                    return evaluation
            
            if performance and performance.get('meets_requirements'):
                # Efficiency score
                efficiency = performance.get('efficiency_pct', 0)
                if efficiency >= 85:
                    eff_score = 100
                elif efficiency >= 75:
                    eff_score = 80 + (efficiency - 75) * 2
                elif efficiency >= 65:
                    eff_score = 60 + (efficiency - 65) * 2
                else:
                    eff_score = max(0, efficiency - 20)
                
                evaluation['score_components']['efficiency'] = eff_score * (self.scoring_weights['efficiency'] / 100)
                evaluation['efficiency_pct'] = efficiency
                
                # Head margin score
                head_margin = performance.get('head_margin_m', 0)
                if head_margin <= 2:
                    margin_score = 100
                elif head_margin <= 5:
                    margin_score = 90 - (head_margin - 2) * 10
                else:
                    margin_score = max(0, 60 - head_margin * 5)
                
                evaluation['score_components']['head_margin'] = margin_score * (self.scoring_weights['head_margin'] / 100)
                evaluation['head_margin_m'] = head_margin
                
                # NPSH score (if available)
                npshr = performance.get('npshr_m')
                if npshr:
                    evaluation['npshr_m'] = npshr
                    # Basic NPSH score (will be refined with constraints)
                    evaluation['score_components']['npsh_margin'] = 15  # Default good score
                
                # Power consumption
                evaluation['power_kw'] = performance.get('power_kw', 0)
                
                # Impeller information
                evaluation['impeller_diameter_mm'] = performance.get('impeller_diameter_mm')
                evaluation['trim_percent'] = performance.get('trim_percent', 100)
                
            else:
                evaluation['feasible'] = False
                evaluation['exclusion_reasons'].append('Cannot meet requirements')
                return evaluation
            
            # Calculate total score
            evaluation['total_score'] = sum(evaluation['score_components'].values())
            
        except Exception as e:
            logger.error(f"Error in pump evaluation: {str(e)}")
            evaluation['feasible'] = False
            evaluation['exclusion_reasons'].append(f'Evaluation error: {str(e)}')
        
        return evaluation
    
    def rank_pumps(self, pump_list: List[str], criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rank pumps based on criteria.
        
        Args:
            pump_list: List of pump codes
            criteria: Ranking criteria
        
        Returns:
            Ranked list with analysis
        """
        flow = criteria.get('flow', 0)
        head = criteria.get('head', 0)
        
        if not flow or not head:
            logger.error("Flow and head required for ranking")
            return []
        
        evaluations = []
        
        for pump_code in pump_list:
            try:
                # Get pump data
                pump_data = self.brain.repository.get_pump_by_code(pump_code)
                if not pump_data:
                    logger.warning(f"Pump {pump_code} not found")
                    continue
                
                # Evaluate pump
                evaluation = self.evaluate_single_pump(pump_data, flow, head)
                evaluations.append(evaluation)
                
            except Exception as e:
                logger.error(f"Error ranking pump {pump_code}: {str(e)}")
                continue
        
        # Sort by score
        evaluations.sort(key=lambda x: x.get('total_score', 0), reverse=True)
        
        return evaluations