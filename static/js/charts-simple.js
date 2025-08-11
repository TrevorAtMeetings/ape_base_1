/**
 * Simplified Charts.js for Testing
 */

console.log('Simple Charts.js: Script executing...');

// Simple test class
class SimpleChartManager {
    constructor() {
        console.log('SimpleChartManager: Constructor called');
        this.initialized = true;
    }
    
    initializeCharts(pumpCode, flowRate, head) {
        console.log('SimpleChartManager: initializeCharts called with:', { pumpCode, flowRate, head });
        
        // Just create basic placeholder charts
        const containers = ['head-flow-chart', 'efficiency-flow-chart', 'power-flow-chart', 'npshr-flow-chart'];
        
        containers.forEach(id => {
            const container = document.getElementById(id);
            if (container) {
                container.innerHTML = `<div style="padding: 50px; text-align: center; background: #f0f0f0;">
                    <h3>${id}</h3>
                    <p>Chart would be here</p>
                    <p>Data: ${pumpCode} at ${flowRate}m³/hr, ${head}m head</p>
                </div>`;
                console.log('SimpleChartManager: Placeholder created for', id);
            } else {
                console.log('SimpleChartManager: Container not found:', id);
            }
        });
    }
}

// Create global instance
if (typeof window !== 'undefined') {
    console.log('Simple Charts.js: Creating global instance...');
    window.pumpChartsManager = new SimpleChartManager();
    console.log('Simple Charts.js: Global pumpChartsManager created successfully');
} else {
    console.log('Simple Charts.js: Window not available');
}