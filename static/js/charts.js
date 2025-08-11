/**
 * Clean Charts.js - Brain-Only Architecture
 * SINGLE SOURCE OF TRUTH: Trust API data completely, no client-side transformations
 * DRY PRINCIPLE: One generic chart method instead of 4 duplicates
 */

class ChartManager {
    constructor() {
        this.currentChartData = null;
        
        // Consolidated chart configurations
        this.chartConfigs = {
            head_flow: {
                title: 'Head vs Flow Performance',
                xTitle: 'Flow Rate (m³/hr)', 
                yTitle: 'Head (m)',
                color: '#007BFF',
                dataKey: 'head_data'
            },
            efficiency_flow: {
                title: 'Efficiency vs Flow Performance',
                xTitle: 'Flow Rate (m³/hr)',
                yTitle: 'Efficiency (%)', 
                color: '#28A745',
                dataKey: 'efficiency_data'
            },
            power_flow: {
                title: 'Power vs Flow Performance',
                xTitle: 'Flow Rate (m³/hr)',
                yTitle: 'Power (kW)',
                color: '#DC3545', 
                dataKey: 'power_data'
            },
            npshr_flow: {
                title: 'NPSHr vs Flow Performance',
                xTitle: 'Flow Rate (m³/hr)',
                yTitle: 'NPSHr (m)',
                color: '#FFC107',
                dataKey: 'npshr_data'
            }
        };
    }

    async loadChartData(pumpCode, flowRate, head) {
        try {
            console.log('Charts.js: loadChartData called with:', { pumpCode, flowRate, head });
            
            const safePumpCode = encodeURIComponent(pumpCode);
            const url = `/api/chart_data/${safePumpCode}?flow=${flowRate}&head=${head}`;
            
            const response = await fetch(url);
            console.log('Charts.js: Response status:', response.status);
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.currentChartData = data;
            console.log('Charts.js: Chart data loaded and stored');
            return data;
        } catch (error) {
            console.error('Charts.js: Error loading chart data:', error);
            throw error;
        }
    }

    /**
     * UNIFIED CHART RENDERER - Replaces 4 duplicate methods
     * Uses Brain API data directly with zero client-side transformations
     */
    renderChart(containerId, chartType) {
        console.log(`Charts.js: Rendering ${chartType} chart...`);
        
        if (!this.currentChartData || !this.currentChartData.curves) {
            console.error(`No chart data available for ${chartType} chart`);
            document.getElementById(containerId).innerHTML = 
                '<p style="text-align: center; padding: 50px;">No chart data available</p>';
            return;
        }

        const config = this.chartConfigs[chartType];
        if (!config) {
            console.error(`Unknown chart type: ${chartType}`);
            return;
        }

        const traces = [];
        const opPoint = this.currentChartData.operating_point;

        // BRAIN SYSTEM: Use API data directly - NO CLIENT-SIDE TRANSFORMATIONS
        if (Array.isArray(this.currentChartData.curves)) {
            this.currentChartData.curves.forEach((curve, index) => {
                const flowData = curve.flow_data || [];
                const yData = curve[config.dataKey] || [];
                
                if (flowData.length > 0 && yData.length > 0) {
                    // SINGLE SOURCE OF TRUTH: Use Brain-generated labels and data directly
                    traces.push({
                        x: flowData,  // Direct from API
                        y: yData,     // Direct from API  
                        type: 'scatter',
                        mode: 'lines+markers',
                        name: curve.display_label || `Curve ${index + 1}`, // Brain-generated label
                        line: {
                            color: curve.is_selected ? config.color : this.getAlternateColor(index),
                            width: curve.is_selected ? 3 : 2
                        },
                        marker: {
                            size: curve.is_selected ? 2 : 1.5
                        },
                        hovertemplate: this.createEnhancedHoverTemplate(curve, config, chartType)
                    });
                }
            });
        }

        // Add BEP zones for head-flow charts (enhanced feature restoration)
        if (chartType === 'head_flow') {
            this.addBEPZoneTraces(traces, this.currentChartData.curves || [], [], []);
        }

        // Add system curve if available (enhanced feature restoration)  
        if (opPoint && opPoint.flow_m3hr && opPoint.head_m && chartType === 'head_flow') {
            this.addSystemCurve(traces, opPoint, [], []);
        }

        // Add enhanced operating point with crosshairs
        if (opPoint && opPoint.flow_m3hr) {
            const yValue = this.getOperatingPointValue(opPoint, chartType);
            if (yValue != null) {
                this.addEnhancedOperatingPoint(traces, opPoint, yValue, this.chartConfigs[chartType], chartType);
            }
        }

        // Add BEP annotations from Brain intelligence
        this.addBEPAnnotations(traces, this.currentChartData.brain_config?.annotations || [], [], [], this.chartConfigs[chartType]);

        // Create layout and render
        const layout = this.createLayout(config, traces);
        const plotConfig = {
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['pan2d', 'select2d', 'lasso2d', 'autoScale2d'],
            displaylogo: false
        };

        try {
            Plotly.newPlot(containerId, traces, layout, plotConfig);
            console.log(`Charts.js: ${chartType} chart rendered successfully`);
            this.removeLoadingSpinner(containerId);
        } catch (error) {
            console.error(`Error rendering ${chartType} chart:`, error);
            document.getElementById(containerId).innerHTML = 
                '<p style="text-align: center; padding: 50px; color: red;">Error rendering chart</p>';
            this.removeLoadingSpinner(containerId);
        }
    }

    // PUBLIC METHODS - Simple wrappers for the unified renderer
    renderHeadFlowChart(containerId) {
        this.renderChart(containerId, 'head_flow');
    }

    renderEfficiencyFlowChart(containerId) {
        this.renderChart(containerId, 'efficiency_flow');
    }

    renderPowerFlowChart(containerId) {
        this.renderChart(containerId, 'power_flow');
    }

    renderNPSHrFlowChart(containerId) {
        this.renderChart(containerId, 'npshr_flow');
    }

    // HELPER METHODS - Simplified, no transformations
    getOperatingPointValue(opPoint, chartType) {
        switch (chartType) {
            case 'head_flow': return opPoint.head_m;
            case 'efficiency_flow': return opPoint.efficiency_pct;
            case 'power_flow': return opPoint.power_kw;
            case 'npshr_flow': return opPoint.npshr_m;
            default: return null;
        }
    }

    createHoverTemplate(opPoint, chartType) {
        const value = this.getOperatingPointValue(opPoint, chartType);
        const unit = this.getUnit(chartType);
        return `<b>Operating Point</b><br>Flow: ${opPoint.flow_m3hr?.toFixed(1)} m³/hr<br>` +
               `${this.getYLabel(chartType)}: ${value?.toFixed(1)} ${unit}<extra></extra>`;
    }

    getUnit(chartType) {
        const units = {
            head_flow: 'm', 
            efficiency_flow: '%',
            power_flow: 'kW', 
            npshr_flow: 'm'
        };
        return units[chartType] || '';
    }

    getYLabel(chartType) {
        const labels = {
            head_flow: 'Head',
            efficiency_flow: 'Efficiency', 
            power_flow: 'Power',
            npshr_flow: 'NPSHr'
        };
        return labels[chartType] || '';
    }

    getAlternateColor(index) {
        const colors = ['#6C757D', '#17A2B8', '#FD7E14', '#6F42C1', '#E83E8C'];
        return colors[index % colors.length];
    }

    createLayout(config, traces) {
        // Calculate data ranges from traces - only show actual pump curve data
        const allX = traces.flatMap(t => t.x || []).filter(x => !isNaN(x));
        const allY = traces.flatMap(t => t.y || []).filter(y => !isNaN(y));
        
        // For pump curves, only show the actual data range with minimal padding
        // Don't extend beyond the valid pump curve data
        let xRange, yRange;
        
        if (allX.length > 0) {
            const minX = Math.min(...allX);
            const maxX = Math.max(...allX);
            const xPadding = (maxX - minX) * 0.02; // Only 2% padding for visibility
            xRange = [Math.max(0, minX - xPadding), maxX + xPadding];
        } else {
            xRange = [0, 100];
        }
        
        if (allY.length > 0) {
            const minY = Math.min(...allY);
            const maxY = Math.max(...allY);
            const yPadding = (maxY - minY) * 0.05; // 5% padding for y-axis
            yRange = [Math.max(0, minY - yPadding), maxY + yPadding];
        } else {
            yRange = [0, 100];
        }

        return {
            title: {
                text: config.title,
                font: { size: 16, family: 'Arial, sans-serif' }
            },
            xaxis: {
                title: config.xTitle,
                range: xRange,
                showgrid: true,
                gridcolor: '#E1E5E9'
            },
            yaxis: {
                title: config.yTitle, 
                range: yRange,
                showgrid: true,
                gridcolor: '#E1E5E9'
            },
            margin: { l: 60, r: 40, t: 60, b: 60 },
            legend: {
                x: 0.02,
                y: 0.98,
                bgcolor: 'rgba(255,255,255,0.8)',
                bordercolor: '#CCCCCC',
                borderwidth: 1
            },
            hovermode: 'closest'
        };
    }

    removeLoadingSpinner(containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            const spinner = container.querySelector('.loading-spinner');
            if (spinner) {
                spinner.remove();
            }
        }
    }

    // ENHANCED FEATURE: Detailed hover templates with operating point data
    createEnhancedHoverTemplate(data, config, chartType) {
        if (data && data.flow_m3hr) {
            // Enhanced operating point hover
            return `<b>Operating Point</b><br>` +
                   `Flow: ${data.flow_m3hr} m³/hr<br>` +
                   `Head: ${data.head_m || 'N/A'} m<br>` +
                   `Efficiency: ${data.efficiency_pct || 'N/A'}%<br>` +
                   `Power: ${data.power_kw || 'N/A'} kW<br>` +
                   `NPSH: ${data.npshr_m || 'N/A'} m<br>` +
                   `<extra></extra>`;
        } else {
            // Enhanced curve point hover  
            return `<b>%{fullData.name}</b><br>` +
                   `${config.xTitle}: %{x}<br>` +
                   `${config.yTitle}: %{y}<br>` +
                   `Diameter: ${data.impeller_diameter_mm || 'N/A'}mm<br>` +
                   `<extra></extra>`;
        }
    }

    // ENHANCED FEATURE: Add BEP zone visualizations for head-flow charts
    addBEPZoneTraces(traces, curves, allX, allY) {
        if (!curves || curves.length === 0) return;

        // Create BEP efficiency zone (80-110% of BEP flow)
        curves.forEach(curve => {
            if (curve.bep_flow_m3hr && curve.is_selected) {
                const bepFlow = curve.bep_flow_m3hr;
                const flowData = curve.flow_data || [];
                const headData = curve.head_data || [];
                
                // Find BEP zone boundaries (80-110% of BEP flow)
                const minFlow = bepFlow * 0.8;
                const maxFlow = bepFlow * 1.1;
                
                // Find corresponding head values
                const zoneFlows = [];
                const zoneHeads = [];
                
                for (let i = 0; i < flowData.length; i++) {
                    if (flowData[i] >= minFlow && flowData[i] <= maxFlow) {
                        zoneFlows.push(flowData[i]);
                        zoneHeads.push(headData[i]);
                    }
                }
                
                if (zoneFlows.length > 1) {
                    traces.push({
                        x: zoneFlows,
                        y: zoneHeads,
                        type: 'scatter',
                        mode: 'lines',
                        name: 'BEP Zone',
                        line: { color: 'rgba(40, 167, 69, 0.3)', width: 8 },
                        showlegend: true,
                        hovertemplate: '<b>BEP Efficiency Zone</b><br>Flow: %{x} m³/hr<br>Head: %{y} m<extra></extra>'
                    });
                }
            }
        });
    }

    // ENHANCED FEATURE: Add system curve visualization  
    addSystemCurve(traces, operatingPoint, allX, allY) {
        if (!operatingPoint.flow_m3hr || !operatingPoint.head_m) return;
        
        const opFlow = operatingPoint.flow_m3hr;
        const opHead = operatingPoint.head_m;
        
        // Generate system curve (parabolic: H = H_static + K * Q^2)
        const maxFlow = Math.max(...allX) * 1.2;
        const systemFlows = [];
        const systemHeads = [];
        
        // Assume 30% static head for typical systems
        const staticHead = opHead * 0.3;
        const frictionCoeff = (opHead - staticHead) / (opFlow * opFlow);
        
        for (let flow = 0; flow <= maxFlow; flow += maxFlow / 50) {
            systemFlows.push(flow);
            systemHeads.push(staticHead + frictionCoeff * flow * flow);
        }
        
        traces.push({
            x: systemFlows,
            y: systemHeads,
            type: 'scatter',
            mode: 'lines',
            name: 'System Curve',
            line: { color: 'rgba(220, 53, 69, 0.6)', width: 2, dash: 'dash' },
            showlegend: true,
            hovertemplate: '<b>System Curve</b><br>Flow: %{x} m³/hr<br>Head: %{y} m<extra></extra>'
        });
    }

    // ENHANCED FEATURE: Enhanced operating point with crosshairs
    addEnhancedOperatingPoint(traces, operatingPoint, yValue, config, chartType) {
        const flow = operatingPoint.flow_m3hr;
        
        // Main operating point marker
        traces.push({
            x: [flow],
            y: [yValue],
            type: 'scatter',
            mode: 'markers',
            name: 'Operating Point',
            marker: { 
                color: 'red', 
                size: 12, 
                symbol: 'diamond',
                line: { color: 'darkred', width: 2 }
            },
            hovertemplate: this.createEnhancedHoverTemplate(operatingPoint, config, chartType)
        });
        
        // Add crosshairs for better visibility
        const maxX = Math.max(...traces.map(t => Math.max(...(t.x || []))));
        const maxY = Math.max(...traces.map(t => Math.max(...(t.y || []))));
        
        // Vertical crosshair
        traces.push({
            x: [flow, flow],
            y: [0, maxY],
            type: 'scatter',
            mode: 'lines',
            name: 'Flow Reference',
            line: { color: 'rgba(255, 0, 0, 0.3)', width: 1, dash: 'dot' },
            showlegend: false,
            hoverinfo: 'none'
        });
        
        // Horizontal crosshair
        traces.push({
            x: [0, maxX],
            y: [yValue, yValue],
            type: 'scatter',
            mode: 'lines',
            name: 'Head Reference',
            line: { color: 'rgba(255, 0, 0, 0.3)', width: 1, dash: 'dot' },
            showlegend: false,
            hoverinfo: 'none'
        });
    }

    // ENHANCED FEATURE: Add BEP annotations from Brain intelligence
    addBEPAnnotations(traces, annotations, allX, allY, config) {
        annotations.forEach(annotation => {
            if (annotation.type === 'bep_marker' && annotation.x && annotation.y) {
                traces.push({
                    x: [annotation.x],
                    y: [annotation.y],
                    type: 'scatter',
                    mode: 'markers+text',
                    name: 'BEP',
                    marker: { color: 'green', size: 8, symbol: 'star' },
                    text: ['BEP'],
                    textposition: 'top center',
                    textfont: { color: 'green', size: 10 },
                    showlegend: false,
                    hovertemplate: '<b>Best Efficiency Point</b><br>Flow: %{x} m³/hr<br>Head: %{y} m<extra></extra>'
                });
            }
        });
    }

    // Initialize all charts
    async initializeCharts(pumpCode, flowRate, head) {
        try {
            await this.loadChartData(pumpCode, flowRate, head);
            
            // Render all charts using unified method
            this.renderHeadFlowChart('head-flow-chart');
            this.renderEfficiencyFlowChart('efficiency-flow-chart'); 
            this.renderPowerFlowChart('power-flow-chart');
            this.renderNPSHrFlowChart('npshr-flow-chart');
            
            console.log('Charts.js: All charts initialized successfully');
        } catch (error) {
            console.error('Charts.js: Failed to initialize charts:', error);
        }
    }
}

// Global instance for compatibility
let chartManager;

// Create global instance that templates expect  
console.log('Charts.js: Script is executing...');

// Mark that this script has executed
if (typeof window !== 'undefined') {
    window.chartsJsExecuted = true;
}

// Robust initialization with error handling
if (typeof window !== 'undefined') {
    try {
        console.log('Charts.js: Creating ChartManager...');
        window.pumpChartsManager = new ChartManager();
        console.log('Charts.js: Global pumpChartsManager instance created successfully');
        console.log('Charts.js: pumpChartsManager methods:', Object.getOwnPropertyNames(Object.getPrototypeOf(window.pumpChartsManager)));
    } catch (error) {
        console.error('Charts.js: Failed to create ChartManager:', error);
        console.error('Charts.js: Error stack:', error.stack);
        
        // Create a fallback minimal manager
        window.pumpChartsManager = {
            initializeCharts: function(pumpCode, flowRate, head) {
                console.log('Fallback pumpChartsManager: Charts would initialize with', { pumpCode, flowRate, head });
                // Create placeholder content
                ['head-flow-chart', 'efficiency-flow-chart', 'power-flow-chart', 'npshr-flow-chart'].forEach(id => {
                    const container = document.getElementById(id);
                    if (container) {
                        container.innerHTML = `<div style="padding: 50px; text-align: center; background: #f0f0f0; border-radius: 8px;">
                            <h3>Chart Loading Error</h3>
                            <p>Unable to load ${id}</p>
                            <p>Pump: ${pumpCode} | Flow: ${flowRate} m³/hr | Head: ${head} m</p>
                        </div>`;
                    }
                });
            }
        };
        console.log('Charts.js: Fallback pumpChartsManager created');
    }
} else {
    console.log('Charts.js: Window object not available');
}

// Global functions for compatibility with existing code
function initializeCharts(pumpCode, flowRate, head) {
    chartManager = new ChartManager();
    window.pumpChartsManager = chartManager; // Ensure consistency
    return chartManager.initializeCharts(pumpCode, flowRate, head);
}

function loadChartData(pumpCode, flowRate, head) {
    if (!chartManager) chartManager = new ChartManager();
    return chartManager.loadChartData(pumpCode, flowRate, head);
}

function renderHeadFlowChart(containerId) {
    if (chartManager) chartManager.renderHeadFlowChart(containerId);
}

function renderEfficiencyFlowChart(containerId) {
    if (chartManager) chartManager.renderEfficiencyFlowChart(containerId);
}

function renderPowerFlowChart(containerId) {
    if (chartManager) chartManager.renderPowerFlowChart(containerId);
}

function renderNPSHrFlowChart(containerId) {
    if (chartManager) chartManager.renderNPSHrFlowChart(containerId);
}