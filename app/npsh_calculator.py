"""
NPSH Calculator for APE Pumps Selection System
Provides engineering-standard NPSHa calculations based on system parameters
"""

import logging
import math

logger = logging.getLogger(__name__)

class NPSHCalculator:
    """Calculate NPSHa (Net Positive Suction Head Available) using engineering principles"""
    
    @staticmethod
    def calculate_npsha(temperature_c: float = 20.0, 
                       elevation_m: float = 0.0,
                       static_suction_head_m: float = 1.0,
                       friction_losses_m: float = 0.5,
                       vapor_pressure_kpa: float = None) -> dict:
        """
        Calculate NPSHa using standard engineering formula:
        NPSHa = Atmospheric Pressure Head + Static Suction Head - Vapor Pressure Head - Friction Losses
        
        Args:
            temperature_c: Liquid temperature in Celsius (default: 20°C)
            elevation_m: Site elevation above sea level in meters (default: 0m - sea level)
            static_suction_head_m: Static head from liquid surface to pump centerline 
                                 (+ve if tank above pump, -ve if below) (default: +1.0m flooded suction)
            friction_losses_m: Friction losses in suction piping (default: 0.5m typical)
            vapor_pressure_kpa: Vapor pressure of liquid in kPa (default: calculated for water)
            
        Returns:
            dict: NPSHa calculation results with breakdown and assumptions
        """
        try:
            # Calculate atmospheric pressure head based on elevation
            atm_pressure_head_m = NPSHCalculator._calculate_atmospheric_pressure_head(elevation_m)
            
            # Calculate vapor pressure head
            if vapor_pressure_kpa is None:
                vapor_pressure_kpa = NPSHCalculator._get_water_vapor_pressure(temperature_c)
            
            vapor_pressure_head_m = NPSHCalculator._convert_pressure_to_head(vapor_pressure_kpa)
            
            # Calculate NPSHa
            npsha_m = (atm_pressure_head_m + 
                      static_suction_head_m - 
                      vapor_pressure_head_m - 
                      friction_losses_m)
            
            # Create detailed result
            result = {
                'npsha_m': round(npsha_m, 2),
                'breakdown': {
                    'atmospheric_pressure_head_m': round(atm_pressure_head_m, 2),
                    'static_suction_head_m': round(static_suction_head_m, 2),
                    'vapor_pressure_head_m': round(vapor_pressure_head_m, 3),
                    'friction_losses_m': round(friction_losses_m, 2)
                },
                'assumptions': {
                    'temperature_c': temperature_c,
                    'elevation_m': elevation_m,
                    'vapor_pressure_kpa': round(vapor_pressure_kpa, 3),
                    'calculation_method': 'Engineering standard formula'
                },
                'notes': [
                    f"Atmospheric pressure at {elevation_m}m elevation",
                    f"Water vapor pressure at {temperature_c}°C",
                    "Static head: +ve = flooded suction, -ve = suction lift",
                    "Friction losses include piping, fittings, strainers"
                ]
            }
            
            logger.debug(f"NPSHa calculated: {npsha_m:.2f} m (breakdown: {result['breakdown']})")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating NPSHa: {e}")
            # Return conservative fallback
            return {
                'npsha_m': 8.0,
                'breakdown': {'error': 'Calculation failed, using conservative estimate'},
                'assumptions': {'method': 'Conservative fallback'},
                'notes': ['Calculation error occurred - using conservative 8.0m value']
            }
    
    @staticmethod
    def _calculate_atmospheric_pressure_head(elevation_m: float) -> float:
        """
        Calculate atmospheric pressure head based on elevation
        Uses standard atmospheric pressure formula
        """
        # Standard atmospheric pressure at sea level = 101.325 kPa = 10.33 m water
        sea_level_pressure_kpa = 101.325
        
        # Pressure decreases approximately 12 Pa per meter of elevation
        pressure_kpa = sea_level_pressure_kpa - (elevation_m * 0.012)
        
        # Convert to meters of water head
        pressure_head_m = pressure_kpa / 9.81  # kPa to m water
        
        return pressure_head_m
    
    @staticmethod
    def _get_water_vapor_pressure(temperature_c: float) -> float:
        """
        Get water vapor pressure in kPa for given temperature
        Uses Antoine equation for water
        """
        if temperature_c < 0 or temperature_c > 100:
            logger.warning(f"Temperature {temperature_c}°C outside normal range (0-100°C)")
        
        # Antoine equation constants for water (temperature in °C, pressure in kPa)
        # log10(P) = A - B/(C + T)
        A = 8.07131
        B = 1730.63
        C = 233.426
        
        try:
            log_p = A - (B / (C + temperature_c))
            pressure_kpa = 10 ** log_p / 1000  # Convert from Pa to kPa
            return pressure_kpa
        except:
            # Fallback for calculation errors
            return 0.023  # Approximate value at 20°C
    
    @staticmethod
    def _convert_pressure_to_head(pressure_kpa: float) -> float:
        """Convert pressure in kPa to meters of water head"""
        # 1 kPa = 0.102 m water (approximately)
        return pressure_kpa * 0.102
    
    @staticmethod
    def get_engineering_defaults() -> dict:
        """Get standard engineering defaults for NPSHa calculation"""
        return {
            'temperature_c': 20.0,
            'elevation_m': 0.0,  # Sea level
            'static_suction_head_m': 1.0,  # Flooded suction
            'friction_losses_m': 0.5,  # Typical piping losses
            'description': 'Conservative engineering assumptions for general applications'
        }
    
    @staticmethod
    def calculate_npsha_with_defaults() -> dict:
        """Calculate NPSHa using engineering defaults"""
        defaults = NPSHCalculator.get_engineering_defaults()
        return NPSHCalculator.calculate_npsha(**defaults)