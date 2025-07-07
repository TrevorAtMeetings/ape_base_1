"""
Debug the exact selection process for 28 HC 6P pump
"""
import logging
from catalog_engine import get_catalog_engine

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_28hc6p_selection_process():
    """Debug step by step why 28 HC 6P isn't being selected"""
    
    catalog_engine = get_catalog_engine()
    target_flow = 1781.0
    target_head = 24.0
    
    logger.info("=== Debugging 28 HC 6P Selection Process ===")
    
    # Get the pump
    pump_28hc6p = catalog_engine.get_pump_by_code("28 HC 6P")
    
    if not pump_28hc6p:
        logger.error("28 HC 6P not found")
        return
    
    logger.info(f"Testing pump: {pump_28hc6p.pump_code}")
    
    # Step 1: Get performance at duty point
    logger.info("\n--- Step 1: Getting performance at duty point ---")
    performance = pump_28hc6p.get_performance_at_duty(target_flow, target_head)
    
    if not performance:
        logger.error("No performance data returned")
        return
    
    logger.info(f"Initial performance data:")
    logger.info(f"  Flow: {performance['flow_m3hr']} m³/hr")
    logger.info(f"  Head: {performance['head_m']} m")
    logger.info(f"  Efficiency: {performance['efficiency_pct']}%")
    
    # Step 2: Check if meets basic requirements
    delivered_head = performance['head_m']
    efficiency = performance['efficiency_pct']
    
    logger.info(f"\n--- Step 2: Basic requirement check ---")
    logger.info(f"Delivered head: {delivered_head} m vs required: {target_head} m")
    logger.info(f"Head requirement met: {delivered_head >= target_head}")
    logger.info(f"Efficiency: {efficiency}% (min 40% required)")
    
    meets_head_requirement = delivered_head >= target_head
    
    # Step 3: If doesn't meet head, check tolerance logic
    if not meets_head_requirement:
        logger.info(f"\n--- Step 3: Checking tolerance logic ---")
        
        curve = performance.get('curve', {})
        points = curve.get('performance_points', [])
        max_head_available = max([p.get('head_m', 0) for p in points if p.get('head_m')], default=0)
        
        logger.info(f"Maximum head available: {max_head_available} m")
        
        if max_head_available >= target_head:
            logger.info("Pump has physical capability - checking flow tolerance")
            
            flow_tolerance = 0.10
            min_acceptable_flow = target_flow * (1 - flow_tolerance)
            max_acceptable_flow = target_flow * (1 + flow_tolerance)
            
            logger.info(f"Target flow: {target_flow} m³/hr")
            logger.info(f"Acceptable flow range: {min_acceptable_flow:.1f} - {max_acceptable_flow:.1f} m³/hr")
            
            # Find suitable flows
            suitable_flows = []
            for p in points:
                if p.get('head_m', 0) >= target_head and p.get('flow_m3hr', 0) > 0:
                    suitable_flows.append(p['flow_m3hr'])
                    logger.info(f"  Suitable point: {p['flow_m3hr']} m³/hr → {p['head_m']} m")
            
            within_tolerance_flows = [f for f in suitable_flows if min_acceptable_flow <= f <= max_acceptable_flow]
            logger.info(f"Flows within tolerance: {within_tolerance_flows}")
            
            if within_tolerance_flows:
                logger.info("✓ Should be accepted with tolerance logic")
                best_flow = min(within_tolerance_flows, key=lambda f: abs(f - target_flow))
                logger.info(f"Best flow point: {best_flow} m³/hr")
                
                # Check if performance gets updated
                for p in points:
                    if abs(p.get('flow_m3hr', 0) - best_flow) < 0.1:
                        logger.info(f"Would update to: {p['flow_m3hr']} m³/hr at {p['head_m']} m head")
                        break
            else:
                logger.info("✗ No flows within tolerance")
        else:
            logger.info("Pump lacks physical capability")
    
    # Step 4: Simulate the actual selection process
    logger.info(f"\n--- Step 4: Simulating selection process ---")
    
    # This mimics what happens in select_pumps method
    suitable_pumps = []
    
    performance_test = pump_28hc6p.get_performance_at_duty(target_flow, target_head)
    
    if performance_test:
        delivered_head_test = performance_test['head_m']
        efficiency_test = performance_test['efficiency_pct']
        
        logger.info(f"Selection test - Head: {delivered_head_test}m, Efficiency: {efficiency_test}%")
        
        # The actual logic from select_pumps
        meets_head_requirement_test = delivered_head_test >= target_head
        
        if not meets_head_requirement_test:
            curve_test = performance_test.get('curve', {})
            points_test = curve_test.get('performance_points', [])
            max_head_available_test = max([p.get('head_m', 0) for p in points_test if p.get('head_m')], default=0)
            
            if max_head_available_test >= target_head:
                flow_tolerance_test = 0.10
                min_acceptable_flow_test = target_flow * (1 - flow_tolerance_test)
                max_acceptable_flow_test = target_flow * (1 + flow_tolerance_test)
                
                suitable_flows_test = []
                for p in points_test:
                    if p.get('head_m', 0) >= target_head and p.get('flow_m3hr', 0) > 0:
                        suitable_flows_test.append(p['flow_m3hr'])
                
                within_tolerance_flows_test = [f for f in suitable_flows_test if min_acceptable_flow_test <= f <= max_acceptable_flow_test]
                if within_tolerance_flows_test:
                    meets_head_requirement_test = True
                    best_flow_test = min(within_tolerance_flows_test, key=lambda f: abs(f - target_flow))
                    
                    # Update performance
                    for p in points_test:
                        if abs(p.get('flow_m3hr', 0) - best_flow_test) < 0.1:
                            delivered_head_test = p['head_m']
                            efficiency_test = p['efficiency_pct']
                            performance_test['head_m'] = delivered_head_test
                            performance_test['efficiency_pct'] = efficiency_test
                            performance_test['flow_m3hr'] = best_flow_test
                            logger.info(f"Updated performance: {best_flow_test:.1f} m³/hr at {delivered_head_test:.1f}m head")
                            break
        
        logger.info(f"Final requirement check: {meets_head_requirement_test}")
        logger.info(f"Final efficiency check: {efficiency_test >= 40}")
        
        if meets_head_requirement_test and efficiency_test >= 40:
            logger.info("✓ 28 HC 6P should be included in results")
        else:
            logger.info("✗ 28 HC 6P would be filtered out")
            logger.info(f"  Head requirement: {meets_head_requirement_test}")
            logger.info(f"  Efficiency requirement: {efficiency_test >= 40}")

if __name__ == "__main__":
    debug_28hc6p_selection_process()