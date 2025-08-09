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
                        }
                    });
                }
            });
        }

        // Add operating point if available
        if (opPoint && opPoint.flow_m3hr) {
            const yValue = this.getOperatingPointValue(opPoint, chartType);
            if (yValue != null) {
                traces.push({
                    x: [opPoint.flow_m3hr],
                    y: [yValue],
                    type: 'scatter',
                    mode: 'markers',
                    name: 'Operating Point',
                    marker: {
                        color: 'red',
                        size: 10,
                        symbol: 'diamond'
                    },
                    hovertemplate: this.createHoverTemplate(opPoint, chartType)
                });
            }
        }

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
        // Calculate data ranges from traces
        const allX = traces.flatMap(t => t.x || []);
        const allY = traces.flatMap(t => t.y || []);
        
        const xRange = allX.length > 0 ? [Math.min(...allX) * 0.9, Math.max(...allX) * 1.1] : [0, 100];
        const yRange = allY.length > 0 ? [Math.min(...allY) * 0.9, Math.max(...allY) * 1.1] : [0, 100];

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

// Global functions for compatibility with existing code
function initializeCharts(pumpCode, flowRate, head) {
    chartManager = new ChartManager();
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