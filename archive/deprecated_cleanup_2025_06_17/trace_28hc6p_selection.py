"""
Trace the exact execution path for 28 HC 6P selection
"""
import logging
from catalog_engine import get_catalog_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def trace_28hc6p_execution():
    """Trace step by step execution for 28 HC 6P"""
    
    catalog_engine = get_catalog_engine()
    target_flow = 1781.0
    target_head = 24.0
    
    # Manually execute the selection logic for 28 HC 6P
    pump = catalog_engine.get_pump_by_code("28 HC 6P")
    
    if not pump:
        logger.error("Pump not found")
        return
    
    logger.info("=== Tracing 28 HC 6P Selection Logic ===")
    
    # Step 1: Get performance
    performance = pump.get_performance_at_duty(target_flow, target_head)
    
    if not performance:
        logger.error("No performance data")
        return
    
    logger.info(f"Initial performance: {performance['flow_m3hr']} m³/hr, {performance['head_m']} m, {performance['efficiency_pct']}%")
    
    # Step 2: Find best operating point
    delivered_head, efficiency, best_flow = catalog_engine._find_best_operating_point(
        performance, target_flow, target_head
    )
    
    logger.info(f"Best operating point: {best_flow} m³/hr, {delivered_head} m, {efficiency}%")
    
    # Step 3: Update performance if different
    if best_flow != performance['flow_m3hr']:
        performance['head_m'] = delivered_head
        performance['efficiency_pct'] = efficiency
        performance['flow_m3hr'] = best_flow
        logger.info(f"Performance updated to optimal point")
    
    # Step 4: Check requirements
    meets_head_requirement = delivered_head >= target_head
    meets_efficiency_requirement = efficiency >= 40
    
    logger.info(f"Meets head requirement: {meets_head_requirement} ({delivered_head} >= {target_head})")
    logger.info(f"Meets efficiency requirement: {meets_efficiency_requirement} ({efficiency} >= 40)")
    
    if meets_head_requirement and meets_efficiency_requirement:
        # Step 5: Calculate scoring
        head_margin = delivered_head - target_head
        head_margin_pct = (head_margin / target_head) * 100
        
        logger.info(f"Head margin: {head_margin} m ({head_margin_pct:.1f}%)")
        
        efficiency_score = efficiency
        
        if 5 <= head_margin_pct <= 15:
            margin_bonus = 20
        elif head_margin_pct < 5:
            margin_bonus = head_margin_pct * 2
        else:
            margin_bonus = 15 - (head_margin_pct - 15) * 0.5
            margin_bonus = max(0, margin_bonus)
        
        score = efficiency_score + margin_bonus
        
        logger.info(f"Efficiency score: {efficiency_score}")
        logger.info(f"Margin bonus: {margin_bonus}")
        logger.info(f"Total score: {score}")
        
        # Step 6: Check sizing validation
        sizing_validated = False
        if 'sizing_info' in performance:
            sizing_info = performance['sizing_info']
            sizing_validated = sizing_info.get('meets_requirements', False)
            logger.info(f"Sizing validation: {sizing_validated}")
            
            if not sizing_validated:
                logger.info("FILTERED OUT: Sizing validation failed")
                return
        else:
            logger.info("No sizing info - proceeding without sizing validation")
        
        logger.info("✓ 28 HC 6P SHOULD BE INCLUDED IN RESULTS")
        logger.info(f"Final performance: {performance['flow_m3hr']} m³/hr, {performance['head_m']} m, {performance['efficiency_pct']}%")
        logger.info(f"Score: {score}")
        
    else:
        logger.info("✗ 28 HC 6P filtered out due to requirements check")

if __name__ == "__main__":
    trace_28hc6p_execution()