// Interactive Pump Performance Charts using Plotly.js
class PumpChartsManager {
    constructor() {
        this.currentChartData = null;
        this.chartsInitialized = false;
        this.chartConfigs = {
            head_flow: {
                title: 'Head vs Flow Rate',
                xAxis: 'Flow Rate (m³/hr)',
                yAxis: 'Head (m)',
                color: '#004d40'
            },
            efficiency_flow: {
                title: 'Efficiency vs Flow Rate',
                xAxis: 'Flow Rate (m³/hr)',
                yAxis: 'Efficiency (%)',
                color: '#2e7d32'
            },
            power_flow: {
                title: 'Power vs Flow Rate',
                xAxis: 'Flow Rate (m³/hr)',
                yAxis: 'Power (kW)',
                color: '#1565c0'
            },
            npshr_flow: {
                title: 'NPSHr vs Flow Rate',
                xAxis: 'Flow Rate (m³/hr)',
                yAxis: 'NPSHr (m)',
                color: '#e65100'
            }
        };
    }

    async loadChartData(pumpCode, flowRate, head) {
        try {
            console.log('Charts.js: loadChartData called with:', { pumpCode, flowRate, head });

            // Use base64 encoding for pump codes with special characters
            const safePumpCode = btoa(pumpCode).replace(/[+/=]/g, function(match) {
                return {'+': '-', '/': '_', '=': ''}[match];
            });
            console.log('Charts.js: Encoded pump code:', safePumpCode);

            const url = `/api/chart_data_safe/${safePumpCode}?flow=${flowRate}&head=${head}`;
            console.log('Charts.js: Fetching from URL:', url);

            const response = await fetch(url);
            console.log('Charts.js: Response status:', response.status);

            const data = await response.json();
            console.log('Charts.js: Response data:', data);

            if (data.error) {
                throw new Error(data.error);
            }

            this.currentChartData = data;
            console.log('Charts.js: Chart data loaded and stored');
            return data;
        } catch (error) {
            console.error('Charts.js: Error details:', error, error.stack);
            console.error('Charts.js: Error loading chart data - Full context:', {
                pumpCode,
                flowRate,
                head,
                errorMessage: error.message,
                errorStack: error.stack,
                errorType: error.constructor.name
            });
            throw error;
        }
    }

    renderHeadFlowChart(containerId) {
        console.log('Charts.js: Rendering head-flow chart...');
        if (!this.currentChartData || !this.currentChartData.curves) {
            console.error('No chart data available for head-flow chart');
            document.getElementById('head-flow-chart').innerHTML = '<p style="text-align: center; padding: 50px;">No chart data available</p>';
            return;
        }

        const traces = [];
        const config = this.chartConfigs.head_flow;

        // Add curves for each impeller size with data validation
        if (Array.isArray(this.currentChartData.curves)) {
            this.currentChartData.curves.forEach((curve, index) => {
                if (curve && Array.isArray(curve.flow_data) && Array.isArray(curve.head_data) && curve.flow_data.length > 0) {
                    traces.push({
                        x: curve.flow_data,
                        y: curve.head_data,
                        type: 'scatter',
                        mode: 'lines+markers',
                        name: `${curve.impeller_size || `Curve ${index + 1}`}`,
                        line: {
                            color: curve.is_selected ? config.color : this.getAlternateColor(index),
                            width: curve.is_selected ? 3 : 2
                        },
                        marker: {
                            size: curve.is_selected ? 6 : 4
                        }
                    });
                }
            });
        }

        // Add operating point with red triangle marker and reference lines
        const opPoint = this.currentChartData.operating_point;
        if (opPoint && opPoint.flow_m3hr && opPoint.head_m) {
            const pointColor = '#d32f2f'; // Red color for duty point
            const pointSymbol = 'triangle-up'; // Red triangle marker
            
            // Get chart data ranges for proper reference line scaling
            let maxFlow = 500;
            let maxHead = 50;
            let minFlow = 0;
            let minHead = 0;
            if (this.currentChartData.curves.length > 0) {
                const allFlows = this.currentChartData.curves.flatMap(c => c.flow_data || []);
                const allHeads = this.currentChartData.curves.flatMap(c => c.head_data || []);
                if (allFlows.length > 0) {
                    minFlow = Math.min(...allFlows);
                    maxFlow = Math.max(...allFlows);
                }
                if (allHeads.length > 0) {
                    minHead = Math.min(...allHeads);
                    maxHead = Math.max(...allHeads);
                }
            }

            // Calculate reference line boundaries using robust logic
            const flowRange = maxFlow - minFlow;
            const headRange = maxHead - minHead;
            
            // Ensure minimum extension values for small ranges
            const minFlowExtension = Math.max(flowRange * 0.4, 100); // At least 100 units or 40% of range
            const minHeadExtension = Math.max(headRange * 0.4, 10);  // At least 10 units or 40% of range
            
            // Calculate extended boundaries with proper bounds checking
            const extendedMinFlow = Math.max(0, minFlow - minFlowExtension);
            const extendedMaxFlow = maxFlow + minFlowExtension;
            const extendedMinHead = Math.max(0, minHead - minHeadExtension);
            const extendedMaxHead = maxHead + minHeadExtension;
            
            // Vertical reference line (flow) - extends from bottom to top of chart
            traces.push({
                x: [opPoint.flow_m3hr, opPoint.flow_m3hr],
                y: [extendedMinHead, extendedMaxHead],
                type: 'scatter',
                mode: 'lines',
                name: 'Flow Reference',
                line: {
                    color: '#d32f2f',
                    width: 2,
                    dash: 'dot'
                },
                showlegend: false,
                hoverinfo: 'skip'
            });

            // Horizontal reference line (head) - extends from left to right of chart
            traces.push({
                x: [extendedMinFlow, extendedMaxFlow],
                y: [opPoint.head_m, opPoint.head_m],
                type: 'scatter',
                mode: 'lines',
                name: 'Head Reference',
                line: {
                    color: '#d32f2f',
                    width: 2,
                    dash: 'dot'
                },
                showlegend: false,
                hoverinfo: 'skip'
            });

            // Add operating point triangle marker with enhanced visibility
            traces.push({
                x: [opPoint.flow_m3hr],
                y: [opPoint.head_m],
                type: 'scatter',
                mode: 'markers',
                name: opPoint.extrapolated ? 'Operating Point (Extrapolated)' : 'Operating Point',
                marker: {
                    color: pointColor,
                    size: 18,
                    symbol: pointSymbol,
                    line: { color: '#b71c1c', width: 3 }
                },
                hovertemplate: `<b>Operating Point</b><br>Flow: ${opPoint.flow_m3hr.toFixed(1)} m³/hr<br>Head: ${opPoint.head_m.toFixed(1)} m<extra></extra>`
            });
        }

        const title = `${this.currentChartData.pump_code} - ${config.title}`;
        const yAxisTitle = config.yAxis;

        const layout = {
            title: {
                text: title,
                font: { size: 16, color: '#1976d2', family: 'Roboto, sans-serif' },
                x: 0.05,
                xanchor: 'left'
            },
            xaxis: {
                title: {
                    text: 'Flow Rate (m³/hr)',
                    font: { size: 13, color: '#555' }
                },
                gridcolor: '#e0e0e0',
                gridwidth: 1,
                showline: true,
                linecolor: '#ccc',
                linewidth: 1
            },
            yaxis: {
                title: {
                    text: yAxisTitle,
                    font: { size: 13, color: '#555' }
                },
                gridcolor: '#e0e0e0',
                gridwidth: 1,
                showline: true,
                linecolor: '#ccc',
                linewidth: 1
            },
            font: {
                family: 'Roboto, sans-serif',
                size: 12,
                color: '#333'
            },
            paper_bgcolor: '#ffffff',
            plot_bgcolor: '#fafafa',
            margin: { l: 80, r: 80, t: 80, b: 120 },
            showlegend: true,
            legend: {
                orientation: 'h',
                x: 0.5,
                y: -0.25,
                xanchor: 'center',
                yanchor: 'top',
                bgcolor: 'rgba(255,255,255,0.9)',
                bordercolor: '#e0e0e0',
                borderwidth: 1,
                font: { size: 11 }
            }
        };

        const plotConfig = {
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['pan2d', 'select2d', 'lasso2d', 'autoScale2d'],
            displaylogo: false
        };

        try {
            Plotly.newPlot(containerId, traces, layout, plotConfig);
            console.log('Charts.js: Head-flow chart rendered successfully');
        } catch (error) {
            console.error('Error rendering head-flow chart:', error);
            document.getElementById('head-flow-chart').innerHTML = '<p style="text-align: center; padding: 50px; color: red;">Error rendering chart</p>';
        }
    }

    renderEfficiencyFlowChart(containerId) {
        console.log('Charts.js: Rendering efficiency-flow chart...');
        if (!this.currentChartData || !this.currentChartData.curves) {
            console.error('No chart data available for efficiency-flow chart');
            document.getElementById('efficiency-flow-chart').innerHTML = '<p style="text-align: center; padding: 50px;">No chart data available</p>';
            return;
        }

        const traces = [];
        const config = this.chartConfigs.efficiency_flow;

        if (Array.isArray(this.currentChartData.curves)) {
            this.currentChartData.curves.forEach((curve, index) => {
                if (curve && Array.isArray(curve.flow_data) && Array.isArray(curve.efficiency_data) && curve.efficiency_data.length > 0) {
                    traces.push({
                        x: curve.flow_data,
                        y: curve.efficiency_data,
                        type: 'scatter',
                        mode: 'lines+markers',
                        name: `${curve.impeller_size || `Curve ${index + 1}`}`,
                        line: {
                            color: curve.is_selected ? config.color : this.getAlternateColor(index),
                            width: curve.is_selected ? 3 : 2
                        },
                        marker: {
                            size: curve.is_selected ? 6 : 4
                        }
                    });
                }
            });
        }

        // Add operating point with red triangle marker and reference lines
        const opPoint = this.currentChartData.operating_point;
        if (opPoint && opPoint.flow_m3hr && opPoint.efficiency_pct != null && opPoint.efficiency_pct > 0) {
            const pointColor = '#d32f2f'; // Red color for duty point
            const pointSymbol = 'triangle-up'; // Red triangle marker
            
            // Get chart data ranges for proper reference line scaling
            let maxFlow = 500;
            let minFlow = 0;
            let maxEff = 100;
            let minEff = 0;
            if (Array.isArray(this.currentChartData.curves) && this.currentChartData.curves.length > 0) {
                const allFlows = this.currentChartData.curves.flatMap(c => Array.isArray(c?.flow_data) ? c.flow_data : []);
                const allEffs = this.currentChartData.curves.flatMap(c => Array.isArray(c?.efficiency_data) ? c.efficiency_data : []).filter(e => e != null && e > 0);
                if (allFlows.length > 0) {
                    minFlow = Math.min(...allFlows);
                    maxFlow = Math.max(...allFlows);
                }
                if (allEffs.length > 0) {
                    minEff = Math.min(...allEffs);
                    maxEff = Math.max(...allEffs);
                }
            }

            // Calculate reference line boundaries using robust logic
            const flowRange = maxFlow - minFlow;
            const effRange = maxEff - minEff;
            
            // Ensure minimum extension values for small ranges
            const minFlowExtension = Math.max(flowRange * 0.4, 100); // At least 100 units or 40% of range
            const minEffExtension = Math.max(effRange * 0.4, 10);    // At least 10 units or 40% of range
            
            // Calculate extended boundaries with proper bounds checking
            const extendedMinFlow = Math.max(0, minFlow - minFlowExtension);
            const extendedMaxFlow = maxFlow + minFlowExtension;
            const extendedMinEff = Math.max(0, minEff - minEffExtension);
            const extendedMaxEff = maxEff + minEffExtension;

            // Vertical reference line (flow) - extends from bottom to top of chart
            traces.push({
                x: [opPoint.flow_m3hr, opPoint.flow_m3hr],
                y: [extendedMinEff, extendedMaxEff],
                type: 'scatter',
                mode: 'lines',
                name: 'Flow Reference',
                line: {
                    color: '#d32f2f',
                    width: 2,
                    dash: 'dot'
                },
                showlegend: false,
                hoverinfo: 'skip'
            });

            // Horizontal reference line (efficiency) - extends from left to right of chart
            traces.push({
                x: [extendedMinFlow, extendedMaxFlow],
                y: [opPoint.efficiency_pct, opPoint.efficiency_pct],
                type: 'scatter',
                mode: 'lines',
                name: 'Efficiency Reference',
                line: {
                    color: '#d32f2f',
                    width: 2,
                    dash: 'dot'
                },
                showlegend: false,
                hoverinfo: 'skip'
            });

            // Add operating point triangle marker with enhanced visibility
            traces.push({
                x: [opPoint.flow_m3hr],
                y: [opPoint.efficiency_pct],
                type: 'scatter',
                mode: 'markers',
                name: 'Operating Point',
                marker: {
                    color: pointColor,
                    size: 18,
                    symbol: pointSymbol,
                    line: { color: '#b71c1c', width: 3 }
                },
                hovertemplate: `<b>Operating Point</b><br>Flow: ${opPoint.flow_m3hr.toFixed(1)} m³/hr<br>Efficiency: ${opPoint.efficiency_pct.toFixed(1)}%<extra></extra>`
            });
        }

                const title = `${this.currentChartData.pump_code} - ${config.title}`;
        const yAxisTitle = config.yAxis;

        const layout = {
            title: {
                text: title,
                font: { size: 16, color: '#1976d2', family: 'Roboto, sans-serif' },
                x: 0.05,
                xanchor: 'left'
            },
            xaxis: {
                title: {
                    text: 'Flow Rate (m³/hr)',
                    font: { size: 13, color: '#555' }
                },
                gridcolor: '#e0e0e0',
                gridwidth: 1,
                showline: true,
                linecolor: '#ccc',
                linewidth: 1
            },
            yaxis: {
                title: {
                    text: yAxisTitle,
                    font: { size: 13, color: '#555' }
                },
                gridcolor: '#e0e0e0',
                gridwidth: 1,
                showline: true,
                linecolor: '#ccc',
                linewidth: 1
            },
            font: {
                family: 'Roboto, sans-serif',
                size: 12,
                color: '#333'
            },
            paper_bgcolor: '#ffffff',
            plot_bgcolor: '#fafafa',
            margin: { l: 80, r: 80, t: 80, b: 120 },
            showlegend: true,
            legend: {
                orientation: 'h',
                x: 0.5,
                y: -0.25,
                xanchor: 'center',
                yanchor: 'top',
                bgcolor: 'rgba(255,255,255,0.9)',
                bordercolor: '#e0e0e0',
                borderwidth: 1,
                font: { size: 11 }
            }
        };

        const plotConfig = {
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['pan2d', 'select2d', 'lasso2d', 'autoScale2d'],
            displaylogo: false
        };

        try {
            Plotly.newPlot(containerId, traces, layout, plotConfig);
            console.log('Charts.js: Efficiency-flow chart rendered successfully');
        } catch (error) {
            console.error('Error rendering efficiency-flow chart:', error);
            document.getElementById('efficiency-flow-chart').innerHTML = '<p style="text-align: center; padding: 50px; color: red;">Error rendering chart</p>';
        }
    }

    renderPowerFlowChart(containerId) {
        console.log('Charts.js: Rendering power-flow chart...');
        if (!this.currentChartData || !this.currentChartData.curves) {
            console.error('No chart data available for power-flow chart');
            document.getElementById('power-flow-chart').innerHTML = '<p style="text-align: center; padding: 50px;">No chart data available</p>';
            return;
        }

        const traces = [];
        const config = this.chartConfigs.power_flow;

        if (Array.isArray(this.currentChartData.curves)) {
            this.currentChartData.curves.forEach((curve, index) => {
                if (curve && Array.isArray(curve.flow_data) && Array.isArray(curve.power_data) && curve.power_data.length > 0) {
                    traces.push({
                        x: curve.flow_data,
                        y: curve.power_data,
                        type: 'scatter',
                        mode: 'lines+markers',
                        name: `${curve.impeller_size || `Curve ${index + 1}`}`,
                        line: {
                            color: curve.is_selected ? config.color : this.getAlternateColor(index),
                            width: curve.is_selected ? 3 : 2
                        },
                        marker: {
                            size: curve.is_selected ? 6 : 4
                        }
                    });
                }
            });
        }

        // Add operating point with red triangle marker and reference lines
        const opPoint = this.currentChartData.operating_point;
        if (opPoint && opPoint.flow_m3hr && opPoint.power_kw != null && opPoint.power_kw > 0) {
            const pointColor = '#d32f2f'; // Red color for duty point
            const pointSymbol = 'triangle-up'; // Red triangle marker
            
            // Get chart data ranges for proper reference line scaling
            let maxFlow = 500;
            let maxPower = 200;
            let minFlow = 0;
            let minPower = 0;
            if (Array.isArray(this.currentChartData.curves) && this.currentChartData.curves.length > 0) {
                const allFlows = this.currentChartData.curves.flatMap(c => Array.isArray(c?.flow_data) ? c.flow_data : []);
                const allPowers = this.currentChartData.curves.flatMap(c => Array.isArray(c?.power_data) ? c.power_data : []).filter(p => p != null && p > 0);
                if (allFlows.length > 0) {
                    minFlow = Math.min(...allFlows);
                    maxFlow = Math.max(...allFlows);
                }
                if (allPowers.length > 0) {
                    minPower = Math.min(...allPowers);
                    maxPower = Math.max(...allPowers);
                }
            }

            // Calculate reference line boundaries using robust logic
            const flowRange = maxFlow - minFlow;
            const powerRange = maxPower - minPower;
            
            // Ensure minimum extension values for small ranges
            const minFlowExtension = Math.max(flowRange * 0.4, 100); // At least 100 units or 40% of range
            const minPowerExtension = Math.max(powerRange * 0.4, 20); // At least 20 units or 40% of range
            
            // Calculate extended boundaries with proper bounds checking
            const extendedMinFlow = Math.max(0, minFlow - minFlowExtension);
            const extendedMaxFlow = maxFlow + minFlowExtension;
            const extendedMinPower = Math.max(0, minPower - minPowerExtension);
            const extendedMaxPower = maxPower + minPowerExtension;

            // Vertical reference line (flow) - extends from bottom to top of chart
            traces.push({
                x: [opPoint.flow_m3hr, opPoint.flow_m3hr],
                y: [extendedMinPower, extendedMaxPower],
                type: 'scatter',
                mode: 'lines',
                name: 'Flow Reference',
                line: {
                    color: '#d32f2f',
                    width: 2,
                    dash: 'dot'
                },
                showlegend: false,
                hoverinfo: 'skip'
            });

            // Horizontal reference line (power) - extends from left to right of chart
            traces.push({
                x: [extendedMinFlow, extendedMaxFlow],
                y: [opPoint.power_kw, opPoint.power_kw],
                type: 'scatter',
                mode: 'lines',
                name: 'Power Reference',
                line: {
                    color: '#d32f2f',
                    width: 2,
                    dash: 'dot'
                },
                showlegend: false,
                hoverinfo: 'skip'
            });

            // Add operating point triangle marker with enhanced visibility
            traces.push({
                x: [opPoint.flow_m3hr],
                y: [opPoint.power_kw],
                type: 'scatter',
                mode: 'markers',
                name: 'Operating Point',
                marker: {
                    color: pointColor,
                    size: 18,
                    symbol: pointSymbol,
                    line: { color: '#b71c1c', width: 3 }
                },
                hovertemplate: `<b>Operating Point</b><br>Flow: ${opPoint.flow_m3hr.toFixed(1)} m³/hr<br>Power: ${opPoint.power_kw.toFixed(1)} kW<extra></extra>`
            });
        }

                const title = `${this.currentChartData.pump_code} - ${config.title}`;
        const yAxisTitle = config.yAxis;

        const layout = {
            title: {
                text: title,
                font: { size: 16, color: '#1976d2', family: 'Roboto, sans-serif' },
                x: 0.05,
                xanchor: 'left'
            },
            xaxis: {
                title: {
                    text: 'Flow Rate (m³/hr)',
                    font: { size: 13, color: '#555' }
                },
                gridcolor: '#e0e0e0',
                gridwidth: 1,
                showline: true,
                linecolor: '#ccc',
                linewidth: 1
            },
            yaxis: {
                title: {
                    text: yAxisTitle,
                    font: { size: 13, color: '#555' }
                },
                gridcolor: '#e0e0e0',
                gridwidth: 1,
                showline: true,
                linecolor: '#ccc',
                linewidth: 1
            },
            font: {
                family: 'Roboto, sans-serif',
                size: 12,
                color: '#333'
            },
            paper_bgcolor: '#ffffff',
            plot_bgcolor: '#fafafa',
            margin: { l: 80, r: 80, t: 80, b: 120 },
            showlegend: true,
            legend: {
                orientation: 'h',
                x: 0.5,
                y: -0.25,
                xanchor: 'center',
                yanchor: 'top',
                bgcolor: 'rgba(255,255,255,0.9)',
                bordercolor: '#e0e0e0',
                borderwidth: 1,
                font: { size: 11 }
            }
        };

        const plotConfig = {
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['pan2d', 'select2d', 'lasso2d', 'autoScale2d'],
            displaylogo: false
        };
        try {
            Plotly.newPlot(containerId, traces, layout, plotConfig);
            console.log('Charts.js: Power-flow chart rendered successfully');
        } catch (error) {
            console.error('Error rendering power-flow chart:', error);
            document.getElementById('power-flow-chart').innerHTML = '<p style="text-align: center; padding: 50px; color: red;">Error rendering chart</p>';
        }
    }

    renderNPSHrFlowChart(containerId) {
        console.log('Charts.js: Rendering npshr-flow chart...');
        if (!this.currentChartData || !this.currentChartData.curves) {
            console.error('No chart data available for npshr-flow chart');
            document.getElementById('npshr-flow-chart').innerHTML = '<p style="text-align: center; padding: 50px;">No chart data available</p>';
            return;
        }

        const traces = [];
        const config = this.chartConfigs.npshr_flow;

        if (Array.isArray(this.currentChartData.curves)) {
            this.currentChartData.curves.forEach((curve, index) => {
                if (curve && Array.isArray(curve.flow_data) && Array.isArray(curve.npshr_data) && curve.npshr_data.length > 0) {
                    traces.push({
                        x: curve.flow_data,
                        y: curve.npshr_data,
                        type: 'scatter',
                        mode: 'lines+markers',
                        name: `${curve.impeller_size || `Curve ${index + 1}`}`,
                        line: {
                            color: curve.is_selected ? config.color : this.getAlternateColor(index),
                            width: curve.is_selected ? 3 : 2
                        },
                        marker: {
                            size: curve.is_selected ? 6 : 4
                        }
                    });
                }
            });
        }

        // Add operating point with red triangle marker and reference lines (only if NPSH data exists)
        const opPoint = this.currentChartData.operating_point;
        const hasNpshData = Array.isArray(this.currentChartData.curves) && 
            this.currentChartData.curves.some(curve => 
                curve && Array.isArray(curve.npshr_data) && curve.npshr_data.length > 0 && curve.npshr_data.some(val => val > 0)
            );
        
        if (opPoint && opPoint.flow_m3hr && opPoint.npshr_m != null && opPoint.npshr_m > 0 && hasNpshData) {
            const pointColor = '#d32f2f'; // Red color for duty point
            const pointSymbol = 'triangle-up'; // Red triangle marker
            
            // Get chart data ranges for proper reference line scaling
            let maxFlow = 500;
            let maxNpsh = 10;
            let minFlow = 0;
            let minNpsh = 0;
            if (Array.isArray(this.currentChartData.curves) && this.currentChartData.curves.length > 0) {
                const allFlows = this.currentChartData.curves.flatMap(c => Array.isArray(c?.flow_data) ? c.flow_data : []);
                const allNpsh = this.currentChartData.curves.flatMap(c => Array.isArray(c?.npshr_data) ? c.npshr_data : []).filter(val => val != null && val > 0);
                if (allFlows.length > 0) {
                    minFlow = Math.min(...allFlows);
                    maxFlow = Math.max(...allFlows);
                }
                if (allNpsh.length > 0) {
                    minNpsh = Math.min(...allNpsh);
                    maxNpsh = Math.max(...allNpsh);
                }
            }

            // Calculate reference line boundaries using robust logic
            const flowRange = maxFlow - minFlow;
            const npshRange = maxNpsh - minNpsh;
            
            // Ensure minimum extension values for small ranges
            const minFlowExtension = Math.max(flowRange * 0.4, 100); // At least 100 units or 40% of range
            const minNpshExtension = Math.max(npshRange * 0.4, 2);   // At least 2 units or 40% of range
            
            // Calculate extended boundaries with proper bounds checking
            const extendedMinFlow = Math.max(0, minFlow - minFlowExtension);
            const extendedMaxFlow = maxFlow + minFlowExtension;
            const extendedMinNpsh = Math.max(0, minNpsh - minNpshExtension);
            const extendedMaxNpsh = maxNpsh + minNpshExtension;

            // Vertical reference line (flow) - extends from bottom to top of chart
            traces.push({
                x: [opPoint.flow_m3hr, opPoint.flow_m3hr],
                y: [extendedMinNpsh, extendedMaxNpsh],
                type: 'scatter',
                mode: 'lines',
                name: 'Flow Reference',
                line: {
                    color: '#d32f2f',
                    width: 2,
                    dash: 'dot'
                },
                showlegend: false,
                hoverinfo: 'skip'
            });

            // Horizontal reference line (NPSH) - extends from left to right of chart
            traces.push({
                x: [extendedMinFlow, extendedMaxFlow],
                y: [opPoint.npshr_m, opPoint.npshr_m],
                type: 'scatter',
                mode: 'lines',
                name: 'NPSH Reference',
                line: {
                    color: '#d32f2f',
                    width: 2,
                    dash: 'dot'
                },
                showlegend: false,
                hoverinfo: 'skip'
            });

            // Add operating point triangle marker with enhanced visibility
            traces.push({
                x: [opPoint.flow_m3hr],
                y: [opPoint.npshr_m],
                type: 'scatter',
                mode: 'markers',
                name: 'Operating Point',
                marker: {
                    color: pointColor,
                    size: 18,
                    symbol: pointSymbol,
                    line: { color: '#b71c1c', width: 3 }
                },
                hovertemplate: `<b>Operating Point</b><br>Flow: ${opPoint.flow_m3hr.toFixed(1)} m³/hr<br>NPSHr: ${opPoint.npshr_m.toFixed(1)} m<extra></extra>`
            });
        } else if (!hasNpshData) {
            // Show message when no NPSH data is available
            traces.push({
                x: [0],
                y: [0],
                type: 'scatter',
                mode: 'text',
                text: ['No NPSH Data Available'],
                textposition: 'middle center',
                textfont: { size: 16, color: '#666' },
                showlegend: false,
                hoverinfo: 'skip'
            });
        }

                const title = `${this.currentChartData.pump_code} - ${config.title}`;
        const yAxisTitle = config.yAxis;

        const layout = {
            title: {
                text: title,
                font: { size: 16, color: '#1976d2', family: 'Roboto, sans-serif' },
                x: 0.05,
                xanchor: 'left'
            },
            xaxis: {
                title: {
                    text: 'Flow Rate (m³/hr)',
                    font: { size: 13, color: '#555' }
                },
                gridcolor: '#e0e0e0',
                gridwidth: 1,
                showline: true,
                linecolor: '#ccc',
                linewidth: 1
            },
            yaxis: {
                title: {
                    text: yAxisTitle,
                    font: { size: 13, color: '#555' }
                },
                gridcolor: '#e0e0e0',
                gridwidth: 1,
                showline: true,
                linecolor: '#ccc',
                linewidth: 1
            },
            font: {
                family: 'Roboto, sans-serif',
                size: 12,
                color: '#333'
            },
            paper_bgcolor: '#ffffff',
            plot_bgcolor: '#fafafa',
            margin: { l: 80, r: 80, t: 80, b: 120 },
            showlegend: true,
            legend: {
                orientation: 'h',
                x: 0.5,
                y: -0.25,
                xanchor: 'center',
                yanchor: 'top',
                bgcolor: 'rgba(255,255,255,0.9)',
                bordercolor: '#e0e0e0',
                borderwidth: 1,
                font: { size: 11 }
            }
        };

        const plotConfig = {
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['pan2d', 'select2d', 'lasso2d', 'autoScale2d'],
            displaylogo: false
        };

        try {
            Plotly.newPlot(containerId, traces, layout, plotConfig);
            console.log('Charts.js: NPSHr-flow chart rendered successfully');
        } catch (error) {
            console.error('Error rendering npshr-flow chart:', error);
            document.getElementById('npshr-flow-chart').innerHTML = '<p style="text-align: center; padding: 50px; color: red;">Error rendering chart</p>';
        }
    }

    renderAllCharts(pumpCode, flowRate, head) {
        console.log('Charts.js: Starting renderAllCharts for:', {pumpCode, flowRate, head});

        // Prevent multiple initializations for the same pump
        const chartKey = `${pumpCode}_${flowRate}_${head}`;
        if (this.chartsInitialized === chartKey) {
            console.log('Charts.js: Charts already initialized for this pump, skipping...');
            return;
        }

        // Ensure chart containers are visible
        const chartContainers = [
            'head-flow-chart', 
            'efficiency-flow-chart', 
            'power-flow-chart', 
            'npshr-flow-chart'
        ];

        if (Array.isArray(chartContainers)) {
            chartContainers.forEach(containerId => {
                const container = document.getElementById(containerId);
                if (container) {
                    container.style.display = 'block';
                    container.style.minHeight = '400px';
                    console.log(`Charts.js: Made container ${containerId} visible`);
                } else {
                    console.warn(`Charts.js: Container ${containerId} not found`);
                }
            });
        }

        this.loadChartData(pumpCode, flowRate, head).then(() => {
            console.log('Chart data loaded, rendering with PumpChartsManager');
            this.renderHeadFlowChart('head-flow-chart');
            this.renderEfficiencyFlowChart('efficiency-flow-chart');
            this.renderPowerFlowChart('power-flow-chart');
            this.renderNPSHrFlowChart('npshr-flow-chart');
            
            // Mark charts as initialized for this pump
            this.chartsInitialized = chartKey;
            console.log('Charts.js: Charts successfully initialized for pump:', chartKey);
        }).catch(error => {
            console.error('Error loading chart data:', error);
            this.showChartError(error.message);
        });
    }

    getAlternateColor(index) {
        const colors = ['#00695c', '#1976d2', '#7b1fa2', '#f57c00', '#5d4037'];
        return colors[index % colors.length];
    }

    showChartError(message) {
        const chartContainers = ['head-flow-chart', 'efficiency-flow-chart', 'power-flow-chart', 'npshr-flow-chart'];
        if (Array.isArray(chartContainers)) {
            chartContainers.forEach(containerId => {
                const container = document.getElementById(containerId);
                if (container) {
                    // Create elements safely to prevent XSS
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'center-align';
                    errorDiv.style.padding = '40px';

                    const icon = document.createElement('i');
                    icon.className = 'material-icons large red-text';
                    icon.textContent = 'error';

                    const errorText = document.createElement('p');
                    errorText.className = 'red-text';
                    errorText.textContent = `Error loading chart data: ${message}`;

                    errorDiv.appendChild(icon);
                    errorDiv.appendChild(errorText);

                    container.innerHTML = '';
                    container.appendChild(errorDiv);
                }
            });
        }
    }
}

// Cache for chart data to avoid redundant API calls
    let chartDataCache = {};
    const CACHE_DURATION = 300000; // 5 minutes

// Global chart manager instance
window.pumpChartsManager = new PumpChartsManager();

// Auto-initialize charts if pump data is available on page load
let chartsInitialized = false;
let initializationAttempts = 0;

// Force chart refresh function
window.forceChartRefresh = function(pumpCode, flowRate, head) {
    console.log('Force refreshing charts for:', {pumpCode, flowRate, head});
    
    // Clear existing charts
    const chartIds = ['head-flow-chart', 'efficiency-flow-chart', 'power-flow-chart', 'npshr-flow-chart'];
    if (Array.isArray(chartIds)) {
        chartIds.forEach(id => {
            const element = document.getElementById(id);
            if (element && element.data) {
                Plotly.purge(id);
            }
            if (element) {
                element.innerHTML = '<div style="text-align: center; padding: 20px;">Loading chart...</div>';
            }
        });
    }
    
    // Clear cache and reset initialization flag
    chartDataCache = {};
    chartsInitialized = false;
    window.pumpChartsManager.chartsInitialized = false;
    
    // Re-initialize
    setTimeout(() => {
        window.pumpChartsManager.renderAllCharts(pumpCode, flowRate, head);
    }, 500);
};

async function loadChartData(pumpCode, flowRate, head) {
        console.log('Charts.js: loadChartData called with:', {pumpCode, flowRate, head});

        // Check cache first
        const cacheKey = `${pumpCode}_${flowRate}_${head}`;
        const cached = chartDataCache[cacheKey];
        if (cached && (Date.now() - cached.timestamp) < CACHE_DURATION) {
            console.log('Charts.js: Using cached data');
            return cached.data;
        }

        try {
            // Encode pump code to handle special characters
            const encodedPumpCode = btoa(pumpCode).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
            console.log('Charts.js: Encoded pump code:', encodedPumpCode);

            const url = `/api/chart_data_safe/${encodedPumpCode}?flow=${flowRate}&head=${head}`;
            console.log('Charts.js: Fetching from URL:', url);

            const response = await fetch(url);
            console.log('Charts.js: Response status:', response.status);

            const data = await response.json();
            console.log('Charts.js: Response data:', data);

            if (data.error) {
                throw new Error(data.error);
            }

             // Store in cache
            chartDataCache[cacheKey] = {
                timestamp: Date.now(),
                data: data
            };

            return data;
        } catch (error) {
            console.error('Charts.js: Error loading chart data:', error);
            throw error;
        }
    }

document.addEventListener('DOMContentLoaded', function() {
    initializationAttempts++;
    console.log(`Charts.js: DOM loaded (attempt ${initializationAttempts}), checking for charts...`);

    // Prevent multiple initializations
    if (chartsInitialized) {
        console.log('Charts.js: Charts already initialized, skipping...');
        return;
    }

    // Look for chart containers first
    const chartContainers = [
        'head-flow-chart', 
        'efficiency-flow-chart', 
        'power-flow-chart', 
        'npshr-flow-chart'
    ];

    const containersFound = chartContainers.filter(id => document.getElementById(id));
    console.log('Charts.js: Chart containers found:', containersFound);

    if (containersFound.length === 0) {
        console.log('Charts.js: No chart containers found on this page');
        return;
    }

    // Try multiple data sources for pump information
    let pumpCode, flowRate, head;

    // Method 1: chartData element
    const chartDataElement = document.getElementById('chartData');
    if (chartDataElement) {
        pumpCode = chartDataElement.dataset.pumpCode;
        flowRate = parseFloat(chartDataElement.dataset.flowRate);
        head = parseFloat(chartDataElement.dataset.head);
        console.log('Charts.js: Data from chartData element:', { pumpCode, flowRate, head });
    }

    // Method 2: Look for data attributes in other elements
    if (!pumpCode) {
        const pumpCodeElement = document.querySelector('[data-pump-code]');
        const flowRateElement = document.querySelector('[data-flow-rate]');
        const headElement = document.querySelector('[data-head]');

        if (pumpCodeElement && flowRateElement && headElement) {
            pumpCode = pumpCodeElement.dataset.pumpCode;
            flowRate = parseFloat(flowRateElement.dataset.flowRate);
            head = parseFloat(headElement.dataset.head);
            console.log('Charts.js: Data from individual elements:', { pumpCode, flowRate, head });
        }
    }

    // Method 3: Try to extract from page content (authentic data only)
    if (!pumpCode) {
        const titleElement = document.querySelector('h1, h2, h3, h4, h5, h6');
        if (titleElement) {
            const matches = titleElement.textContent.match(/([A-Z0-9\/\-\s]+)/);
            if (matches) {
                pumpCode = matches[1].trim();
                console.log('Charts.js: Extracted pump code from title:', pumpCode);
            }
        }
    }

    if (pumpCode && !isNaN(flowRate) && !isNaN(head) && !chartsInitialized) {
        console.log('Charts.js: Initializing charts with data:', { pumpCode, flowRate, head });
        chartsInitialized = true;
        window.pumpChartsManager.renderAllCharts(pumpCode, flowRate, head);
    } else {
        console.log('Charts.js: Missing or invalid chart data:', { 
            pumpCode, 
            flowRate, 
            head, 
            alreadyInitialized: chartsInitialized 
        });
    }
});