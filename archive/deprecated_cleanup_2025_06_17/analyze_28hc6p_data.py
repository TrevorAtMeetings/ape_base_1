"""
Analyze 28 HC 6P pump data based on actual manufacturer specifications
"""
import logging
from catalog_engine import get_catalog_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_28hc6p_detailed():
    """Detailed analysis of 28 HC 6P pump using actual data"""
    
    catalog_engine = get_catalog_engine()
    pump = catalog_engine.get_pump_by_code("28 HC 6P")
    
    if not pump:
        logger.error("28 HC 6P pump not found in catalog")
        return
    
    logger.info("=== 28 HC 6P Detailed Analysis ===")
    logger.info(f"Pump Code: {pump.pump_code}")
    logger.info(f"Manufacturer: {pump.manufacturer}")
    logger.info(f"Available curves: {len(pump.curves)}")
    
    # Target requirements
    target_flow = 1781.0  # m³/hr
    target_head = 24.0    # m
    
    logger.info(f"\nTarget Requirements: {target_flow} m³/hr at {target_head} m")
    logger.info("=" * 60)
    
    for i, curve in enumerate(pump.curves, 1):
        logger.info(f"\n--- Curve {i}: {curve['impeller_diameter_mm']}mm impeller ---")
        logger.info(f"Test Speed: {curve['test_speed_rpm']} RPM")
        
        # Display performance points table
        points = curve['performance_points']
        flows = [p['flow_m3hr'] for p in points]
        heads = [p['head_m'] for p in points]
        effs = [p['efficiency_pct'] for p in points]
        powers = [p['power_kw'] for p in points]
        
        logger.info("\nPerformance Table:")
        logger.info("Flow(m³/hr) | Head(m) | Eff(%) | Power(kW)")
        logger.info("-" * 45)
        
        for j, point in enumerate(points):
            if point['flow_m3hr'] and point['flow_m3hr'] > 0 and point['head_m'] and point['head_m'] > 0:  # Skip zero/null points
                power_val = point.get('power_kw', 0) or 0
                logger.info(f"{point['flow_m3hr']:10.1f} | {point['head_m']:6.1f} | {point['efficiency_pct']:5.1f} | {power_val:8.1f}")
        
        # Check if target flow is within range
        min_flow = min([p['flow_m3hr'] for p in points if p['flow_m3hr'] > 0])
        max_flow = max([p['flow_m3hr'] for p in points if p['flow_m3hr'] > 0])
        max_head = max([p['head_m'] for p in points if p['head_m'] > 0])
        
        logger.info(f"\nFlow Range: {min_flow:.1f} - {max_flow:.1f} m³/hr")
        logger.info(f"Maximum Head: {max_head:.1f} m")
        
        if min_flow <= target_flow <= max_flow:
            logger.info(f"✓ Target flow {target_flow} m³/hr is within pump range")
            
            # Get performance at target flow
            performance = pump.get_performance_at_duty(target_flow, target_head)
            if performance and performance['curve']['impeller_diameter_mm'] == curve['impeller_diameter_mm']:
                delivered_head = performance['head_m']
                efficiency = performance['efficiency_pct']
                power = performance['power_kw']
                
                logger.info(f"At {target_flow} m³/hr:")
                logger.info(f"  Delivered head: {delivered_head:.1f} m")
                logger.info(f"  Efficiency: {efficiency:.1f}%")
                logger.info(f"  Power: {power:.1f} kW")
                
                if delivered_head >= target_head:
                    logger.info(f"  ✓ Meets requirement ({delivered_head:.1f}m >= {target_head}m)")
                else:
                    head_deficit = target_head - delivered_head
                    logger.info(f"  ✗ Falls short by {head_deficit:.1f}m ({delivered_head:.1f}m < {target_head}m)")
                    
                    # Check if higher head is available at lower flow
                    if max_head >= target_head:
                        logger.info(f"  💡 Pump can deliver {max_head:.1f}m at lower flows")
                        logger.info("     Consider impeller trimming or speed adjustment")
        else:
            logger.info(f"✗ Target flow {target_flow} m³/hr is outside pump range")
    
    logger.info("\n" + "=" * 60)
    logger.info("ENGINEERING ASSESSMENT:")
    
    # Get the best performance available
    best_performance = pump.get_performance_at_duty(target_flow, target_head)
    if best_performance:
        delivered = best_performance['head_m']
        if delivered >= target_head:
            logger.info(f"✓ 28 HC 6P CAN meet requirements: delivers {delivered:.1f}m")
        else:
            logger.info(f"✗ 28 HC 6P CANNOT meet requirements: delivers {delivered:.1f}m vs required {target_head}m")
            logger.info("  The pump's maximum capability at this flow rate is insufficient")
    else:
        logger.info("✗ No suitable performance curve found for target flow")

if __name__ == "__main__":
    analyze_28hc6p_detailed()