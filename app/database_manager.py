"""
Database Manager Module
Advanced pump database management with catalog synchronization and inventory tracking
"""

import logging
import json
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import sqlite3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from pump_engine import ParsedPumpData

logger = logging.getLogger(__name__)

@dataclass
class PumpInventoryStatus:
    """Pump inventory and availability information"""
    pump_code: str
    availability_status: str  # "in_stock", "limited", "backorder", "discontinued"
    lead_time_weeks: int
    stock_quantity: Optional[int] = None
    last_updated: Optional[str] = None
    price_estimate: Optional[float] = None

@dataclass
class PumpCatalogInfo:
    """Pump catalog metadata"""
    catalog_name: str
    region: str
    currency: str
    last_updated: str
    pump_count: int
    version: str

class DatabaseManager:
    """Advanced database management for pump catalogs and inventory"""
    
    def __init__(self, db_path: str = "pump_database.sqlite"):
        self.db_path = db_path
        self.catalog_cache = {}
        self.inventory_cache = {}
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize SQLite database for pump data management"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create pump catalogs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pump_catalogs (
                    catalog_id TEXT PRIMARY KEY,
                    catalog_name TEXT NOT NULL,
                    region TEXT,
                    currency TEXT,
                    last_updated TEXT,
                    pump_count INTEGER,
                    version TEXT,
                    data_json TEXT
                )
            ''')
            
            # Create pump inventory table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pump_inventory (
                    pump_code TEXT PRIMARY KEY,
                    availability_status TEXT,
                    lead_time_weeks INTEGER,
                    stock_quantity INTEGER,
                    last_updated TEXT,
                    price_estimate REAL
                )
            ''')
            
            # Create selection history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS selection_history (
                    selection_id TEXT PRIMARY KEY,
                    pump_code TEXT,
                    customer_name TEXT,
                    project_name TEXT,
                    flow_m3hr REAL,
                    head_m REAL,
                    efficiency_pct REAL,
                    selection_date TEXT,
                    notes TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
    
    def load_enhanced_pump_catalog(self, region: str = "global") -> List[ParsedPumpData]:
        """Load pump catalog with enhanced metadata and availability"""
        try:
            # Load base pump data
            base_data = self._load_base_pump_data()
            
            # Enhance with inventory information
            enhanced_data = []
            for pump_data in base_data:
                enhanced_pump = self._enhance_pump_with_inventory(pump_data)
                enhanced_data.append(enhanced_pump)
            
            logger.info(f"Loaded {len(enhanced_data)} pumps with enhanced data")
            return enhanced_data
            
        except Exception as e:
            logger.error(f"Error loading enhanced catalog: {str(e)}")
            return []
    
    def update_pump_inventory(self, inventory_updates: List[PumpInventoryStatus]):
        """Update pump inventory information"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for item in inventory_updates:
                cursor.execute('''
                    INSERT OR REPLACE INTO pump_inventory 
                    (pump_code, availability_status, lead_time_weeks, stock_quantity, last_updated, price_estimate)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    item.pump_code,
                    item.availability_status,
                    item.lead_time_weeks,
                    item.stock_quantity,
                    datetime.now().isoformat(),
                    item.price_estimate
                ))
            
            conn.commit()
            conn.close()
            
            # Update cache
            for item in inventory_updates:
                self.inventory_cache[item.pump_code] = item
            
            logger.info(f"Updated inventory for {len(inventory_updates)} pumps")
            
        except Exception as e:
            logger.error(f"Error updating inventory: {str(e)}")
    
    def get_pump_availability(self, pump_code: str) -> Optional[PumpInventoryStatus]:
        """Get availability information for a specific pump"""
        try:
            # Check cache first
            if pump_code in self.inventory_cache:
                return self.inventory_cache[pump_code]
            
            # Query database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM pump_inventory WHERE pump_code = ?
            ''', (pump_code,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                inventory_status = PumpInventoryStatus(
                    pump_code=row[0],
                    availability_status=row[1],
                    lead_time_weeks=row[2],
                    stock_quantity=row[3],
                    last_updated=row[4],
                    price_estimate=row[5]
                )
                
                # Cache the result
                self.inventory_cache[pump_code] = inventory_status
                return inventory_status
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting pump availability: {str(e)}")
            return None
    
    def save_selection_history(self, selection_data: Dict[str, Any]):
        """Save pump selection to history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            selection_id = f"SEL_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            cursor.execute('''
                INSERT INTO selection_history 
                (selection_id, pump_code, customer_name, project_name, flow_m3hr, head_m, efficiency_pct, selection_date, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                selection_id,
                selection_data.get('pump_code', ''),
                selection_data.get('customer_name', ''),
                selection_data.get('project_name', ''),
                selection_data.get('flow_m3hr', 0),
                selection_data.get('head_m', 0),
                selection_data.get('efficiency_pct', 0),
                datetime.now().isoformat(),
                selection_data.get('notes', '')
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved selection history: {selection_id}")
            
        except Exception as e:
            logger.error(f"Error saving selection history: {str(e)}")
    
    def get_selection_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get analytics on recent pump selections"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Get selection statistics
            cursor.execute('''
                SELECT pump_code, COUNT(*) as selection_count 
                FROM selection_history 
                WHERE selection_date > ? 
                GROUP BY pump_code 
                ORDER BY selection_count DESC
                LIMIT 10
            ''', (cutoff_date,))
            
            popular_pumps = [{'pump_code': row[0], 'selections': row[1]} for row in cursor.fetchall()]
            
            # Get flow range analytics
            cursor.execute('''
                SELECT AVG(flow_m3hr), MIN(flow_m3hr), MAX(flow_m3hr), AVG(head_m), MIN(head_m), MAX(head_m)
                FROM selection_history 
                WHERE selection_date > ?
            ''', (cutoff_date,))
            
            stats_row = cursor.fetchone()
            
            analytics = {
                'period_days': days,
                'popular_pumps': popular_pumps,
                'flow_statistics': {
                    'average_flow': round(stats_row[0] or 0, 1),
                    'min_flow': stats_row[1] or 0,
                    'max_flow': stats_row[2] or 0
                },
                'head_statistics': {
                    'average_head': round(stats_row[3] or 0, 1),
                    'min_head': stats_row[4] or 0,
                    'max_head': stats_row[5] or 0
                }
            }
            
            conn.close()
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting selection analytics: {str(e)}")
            return {}
    
    def generate_inventory_report(self) -> Dict[str, Any]:
        """Generate comprehensive inventory status report"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get availability distribution
            cursor.execute('''
                SELECT availability_status, COUNT(*) 
                FROM pump_inventory 
                GROUP BY availability_status
            ''')
            
            availability_dist = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Get lead time statistics
            cursor.execute('''
                SELECT AVG(lead_time_weeks), MIN(lead_time_weeks), MAX(lead_time_weeks)
                FROM pump_inventory
            ''')
            
            lead_time_stats = cursor.fetchone()
            
            # Get pumps with long lead times
            cursor.execute('''
                SELECT pump_code, lead_time_weeks 
                FROM pump_inventory 
                WHERE lead_time_weeks > 8 
                ORDER BY lead_time_weeks DESC
                LIMIT 10
            ''')
            
            long_lead_times = [{'pump_code': row[0], 'weeks': row[1]} for row in cursor.fetchall()]
            
            report = {
                'report_date': datetime.now().isoformat(),
                'availability_distribution': availability_dist,
                'lead_time_statistics': {
                    'average_weeks': round(lead_time_stats[0] or 0, 1),
                    'min_weeks': lead_time_stats[1] or 0,
                    'max_weeks': lead_time_stats[2] or 0
                },
                'long_lead_times': long_lead_times,
                'recommendations': self._generate_inventory_recommendations(availability_dist, long_lead_times)
            }
            
            conn.close()
            return report
            
        except Exception as e:
            logger.error(f"Error generating inventory report: {str(e)}")
            return {}
    
    def search_pumps_advanced(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Advanced pump search with multiple criteria"""
        try:
            # Load all pumps
            all_pumps = self.load_enhanced_pump_catalog()
            
            filtered_pumps = []
            
            for pump in all_pumps:
                if self._matches_criteria(pump, criteria):
                    pump_dict = {
                        'pump_code': pump.pump_code,
                        'pump_type': pump.pump_type,
                        'bep_flow': pump.bep_flow,
                        'bep_head': pump.bep_head,
                        'bep_efficiency': pump.bep_efficiency,
                        'availability': self.get_pump_availability(pump.pump_code)
                    }
                    filtered_pumps.append(pump_dict)
            
            # Sort by relevance score
            filtered_pumps.sort(key=lambda x: self._calculate_relevance_score(x, criteria), reverse=True)
            
            return filtered_pumps[:20]  # Return top 20 matches
            
        except Exception as e:
            logger.error(f"Error in advanced search: {str(e)}")
            return []
    
    def _load_base_pump_data(self) -> List[ParsedPumpData]:
        """Load base pump data from JSON file"""
        # Legacy database no longer exists - return empty list for compatibility
        logger.warning("Legacy pump database no longer exists - returning empty data for compatibility")
        return []
    
    def _enhance_pump_with_inventory(self, pump_data: ParsedPumpData) -> ParsedPumpData:
        """Enhance pump data with inventory information"""
        try:
            inventory_info = self.get_pump_availability(pump_data.pump_code)
            
            # Add inventory information to pump data
            if inventory_info:
                pump_data.availability_status = inventory_info.availability_status
                pump_data.lead_time_weeks = inventory_info.lead_time_weeks
                pump_data.price_estimate = inventory_info.price_estimate
            else:
                # Default values for pumps without inventory data
                pump_data.availability_status = "available"
                pump_data.lead_time_weeks = 4
                pump_data.price_estimate = None
            
            return pump_data
            
        except Exception as e:
            logger.error(f"Error enhancing pump with inventory: {str(e)}")
            return pump_data
    
    def _matches_criteria(self, pump: ParsedPumpData, criteria: Dict[str, Any]) -> bool:
        """Check if pump matches search criteria"""
        try:
            # Flow range check
            if 'min_flow' in criteria and pump.bep_flow < criteria['min_flow']:
                return False
            if 'max_flow' in criteria and pump.bep_flow > criteria['max_flow']:
                return False
            
            # Head range check
            if 'min_head' in criteria and pump.bep_head < criteria['min_head']:
                return False
            if 'max_head' in criteria and pump.bep_head > criteria['max_head']:
                return False
            
            # Pump type check
            if 'pump_type' in criteria and pump.pump_type != criteria['pump_type']:
                return False
            
            # Availability check
            if 'availability_required' in criteria and criteria['availability_required']:
                availability = getattr(pump, 'availability_status', 'available')
                if availability not in ['available', 'in_stock']:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking criteria match: {str(e)}")
            return False
    
    def _calculate_relevance_score(self, pump_dict: Dict[str, Any], criteria: Dict[str, Any]) -> float:
        """Calculate relevance score for search results"""
        score = 0.0
        
        try:
            # Score based on flow match
            if 'target_flow' in criteria:
                flow_diff = abs(pump_dict['bep_flow'] - criteria['target_flow'])
                flow_score = max(0, 100 - flow_diff)
                score += flow_score * 0.4
            
            # Score based on head match
            if 'target_head' in criteria:
                head_diff = abs(pump_dict['bep_head'] - criteria['target_head'])
                head_score = max(0, 100 - head_diff)
                score += head_score * 0.4
            
            # Score based on efficiency
            efficiency = pump_dict.get('bep_efficiency', 0)
            score += efficiency * 0.2
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculating relevance score: {str(e)}")
            return 0.0
    
    def _generate_inventory_recommendations(self, availability_dist: Dict[str, int], 
                                         long_lead_times: List[Dict[str, Any]]) -> List[str]:
        """Generate inventory management recommendations"""
        recommendations = []
        
        # Check for stock issues
        backorder_count = availability_dist.get('backorder', 0)
        if backorder_count > 0:
            recommendations.append(f"Review {backorder_count} pumps on backorder for alternative options")
        
        # Check for discontinued items
        discontinued_count = availability_dist.get('discontinued', 0)
        if discontinued_count > 0:
            recommendations.append(f"Update catalog to remove {discontinued_count} discontinued pumps")
        
        # Check for long lead times
        if len(long_lead_times) > 5:
            recommendations.append("Consider stocking alternatives for pumps with extended lead times")
        
        if not recommendations:
            recommendations.append("Inventory status is healthy - no immediate actions required")
        
        return recommendations

# Global instance for use across the application
database_manager = DatabaseManager()