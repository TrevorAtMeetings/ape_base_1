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
                return { '+': '-', '/': '_', '=': '' }[match];
            });
            console.log('Charts.js: Encoded pump code:', safePumpCode);

            const url = '/api/chart_data_safe/' + safePumpCode + '?flow=' + flowRate + '&head=' + head;
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
        const opPoint = this.currentChartData.operating_point;

        // Add curves for each impeller size with data validation
        if (Array.isArray(this.currentChartData.curves)) {
            this.currentChartData.curves.forEach((curve, index) => {
                if (curve && Array.isArray(curve.flow_data) && Array.isArray(curve.head_data) && curve.flow_data.length > 0) {
                    // Generate proper impeller size name
                    let impellerName = 'Unknown Size';
                    if (curve.impeller_diameter_mm) {
                        impellerName = curve.impeller_diameter_mm + "mm Impeller";
                    } else if (curve.impeller_size && curve.impeller_size !== "Curve " + (index + 1) && !curve.impeller_size.includes('Curve')) {
                        impellerName = curve.impeller_size + "mm Impeller";
                    } else {
                        impellerName = "Impeller " + (index + 1);
                    }

                    // Add speed scaling information to selected curve if applied
                    if (this.currentChartData.speed_scaling && this.currentChartData.speed_scaling.applied && curve.is_selected) {
                        const requiredSpeed = this.currentChartData.speed_scaling.required_speed_rpm;
                        impellerName += ` (${requiredSpeed} RPM)`;
                    }

                    traces.push({
                        x: curve.flow_data,
                        y: curve.head_data,
                        type: 'scatter',
                        mode: 'lines+markers',
                        name: impellerName,
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

        // Add BEP Operating Range Visualization (80% - 110% of duty point flow)
        if (opPoint && opPoint.flow_m3hr && opPoint.head_m) {
            const bep80Flow = opPoint.flow_m3hr * 0.8;
            const bep110Flow = opPoint.flow_m3hr * 1.1;

            // Get chart data ranges for shaded zone - extend across chart range
            let maxHead = 60;
            let minHead = 0;
            if (this.currentChartData.curves.length > 0) {
                const allHeads = this.currentChartData.curves.flatMap(c => c.head_data || []);
                if (allHeads.length > 0) {
                    const dataMin = Math.min(...allHeads);
                    const dataMax = Math.max(...allHeads);
                    const range = dataMax - dataMin;
                    minHead = Math.max(0, dataMin - range * 0.05);
                    maxHead = dataMax + range * 0.05;
                }
            }

            // BEP Preferred Operating Zone (80%-110%) - Shaded area spanning full chart height
            traces.push({
                x: [bep80Flow, bep110Flow, bep110Flow, bep80Flow, bep80Flow],
                y: [minHead, minHead, maxHead, maxHead, minHead],
                type: 'scatter',
                mode: 'lines',
                fill: 'toself',
                fillcolor: 'rgba(76, 175, 80, 0.15)',
                line: { color: 'rgba(76, 175, 80, 0.3)', width: 1 },
                name: 'BEP Operating Zone (80%-110%)',
                hoverinfo: 'text',
                text: 'Preferred Operating Range<br>80% - 110% of BEP Flow',
                showlegend: true
            });

            // 80% BEP minimum preferred flow line - full height
            traces.push({
                x: [bep80Flow, bep80Flow],
                y: [0, maxHead],
                type: 'scatter',
                mode: 'lines',
                name: '80% BEP Min Flow',
                line: {
                    color: '#ff9800',
                    width: 2,
                    dash: 'dash'
                },
                hovertemplate: "<b>80% BEP Minimum</b><br>Flow: " + (bep80Flow || 0).toFixed(0) + " m³/hr<extra></extra>",
                showlegend: true
            });

            // 110% BEP maximum preferred flow line - full height
            traces.push({
                x: [bep110Flow, bep110Flow],
                y: [0, maxHead],
                type: 'scatter',
                mode: 'lines',
                name: '110% BEP Max Flow',
                line: {
                    color: '#f44336',
                    width: 2,
                    dash: 'dash'
                },
                hovertemplate: "<b>110% BEP Maximum</b><br>Flow: " + (bep110Flow || 0).toFixed(0) + " m³/hr<extra></extra>",
                showlegend: true
            });

            // Add System Curve to show system requirements
            if (this.currentChartData.system_curve && this.currentChartData.system_curve.length > 0) {
                const systemFlows = this.currentChartData.system_curve.map(point => point.flow_m3hr);
                const systemHeads = this.currentChartData.system_curve.map(point => point.head_m);

                traces.push({
                    x: systemFlows,
                    y: systemHeads,
                    type: 'scatter',
                    mode: 'lines',
                    name: 'System Curve',
                    line: {
                        color: '#666666',
                        width: 2,
                        dash: 'dashdot'
                    },
                    hovertemplate: '<b>System Curve</b><br>Flow: %{x:.0f} m³/hr<br>Head: %{y:.1f} m<extra></extra>',
                    showlegend: true
                });
            } else {
                // Generate a more realistic system curve if none provided
                // System curve should intersect with pump curve at operating point
                // Use the actual pump curve data to find the intersection point

                // Find the pump curve that contains the operating point
                let pumpCurve = null;
                for (const curve of this.currentChartData.curves) {
                    if (curve.is_selected && Array.isArray(curve.flow_data) && Array.isArray(curve.head_data)) {
                        pumpCurve = curve;
                        break;
                    }
                }

                if (pumpCurve) {
                    // Find the pump head at operating flow rate
                    let pumpHeadAtOpFlow = opPoint.head_m;

                    // Interpolate to find exact pump head at operating flow
                    for (let i = 0; i < pumpCurve.flow_data.length - 1; i++) {
                        if (pumpCurve.flow_data[i] <= opPoint.flow_m3hr && pumpCurve.flow_data[i + 1] >= opPoint.flow_m3hr) {
                            const flow1 = pumpCurve.flow_data[i];
                            const flow2 = pumpCurve.flow_data[i + 1];
                            const head1 = pumpCurve.head_data[i];
                            const head2 = pumpCurve.head_data[i + 1];

                            // Linear interpolation
                            const ratio = (opPoint.flow_m3hr - flow1) / (flow2 - flow1);
                            pumpHeadAtOpFlow = head1 + ratio * (head2 - head1);
                            break;
                        }
                    }

                    // Calculate system curve parameters to intersect at operating point
                    const staticHead = pumpHeadAtOpFlow * 0.3; // 30% static head
                    const frictionHead = pumpHeadAtOpFlow - staticHead;
                    const frictionCoeff = frictionHead / (opPoint.flow_m3hr * opPoint.flow_m3hr);

                    // Generate system curve points from 0 to 150% of duty flow
                    const systemFlows = [];
                    const systemHeads = [];

                    for (let i = 0; i <= 15; i++) {
                        const flow = (opPoint.flow_m3hr * i) / 10; // 0% to 150% in 10% increments
                        const head = staticHead + frictionCoeff * flow * flow;
                        systemFlows.push(flow);
                        systemHeads.push(head);
                    }

                    traces.push({
                        x: systemFlows,
                        y: systemHeads,
                        type: 'scatter',
                        mode: 'lines',
                        name: 'System Curve (Estimated)',
                        line: {
                            color: '#666666',
                            width: 2,
                            dash: 'dashdot'
                        },
                        hovertemplate: '<b>System Curve</b><br>Flow: %{x:.0f} m³/hr<br>Head: %{y:.1f} m<br><i>Static: ' + (staticHead || 0).toFixed(1) + 'm + Friction</i><extra></extra>',
                        showlegend: true
                    });
                } else {
                    // Fallback to original calculation if no pump curve found
                    const staticHead = opPoint.head_m * 0.4; // 40% static head assumption
                    const frictionHead = opPoint.head_m - staticHead;
                    const frictionCoeff = frictionHead / (opPoint.flow_m3hr * opPoint.flow_m3hr);

                    // Generate system curve points from 0 to 150% of duty flow
                    const systemFlows = [];
                    const systemHeads = [];

                    for (let i = 0; i <= 15; i++) {
                        const flow = (opPoint.flow_m3hr * i) / 10; // 0% to 150% in 10% increments
                        const head = staticHead + frictionCoeff * flow * flow;
                        systemFlows.push(flow);
                        systemHeads.push(head);
                    }

                    traces.push({
                        x: systemFlows,
                        y: systemHeads,
                        type: 'scatter',
                        mode: 'lines',
                        name: 'System Curve (Estimated)',
                        line: {
                            color: '#666666',
                            width: 2,
                            dash: 'dashdot'
                        },
                        hovertemplate: '<b>System Curve</b><br>Flow: %{x:.0f} m³/hr<br>Head: %{y:.1f} m<br><i>Static: ' + (staticHead || 0).toFixed(1) + 'm + Friction</i><extra></extra>',
                        showlegend: true
                    });
                }
            }
        }

        // Enhanced Operating Point Display with comprehensive hover information
        if (opPoint && opPoint.flow_m3hr && opPoint.head_m) {
            const pointColor = '#d32f2f'; // Red color for duty point
            const pointSymbol = 'triangle-up'; // Red triangle marker

            // Get chart data ranges for proper reference line scaling
            let refMaxFlow = 500;
            let refMaxHead = 50;
            let refMinFlow = 0;
            let refMinHead = 0;
            if (this.currentChartData.curves.length > 0) {
                const allFlows = this.currentChartData.curves.flatMap(c => c.flow_data || []);
                const allHeads = this.currentChartData.curves.flatMap(c => c.head_data || []);
                if (allFlows.length > 0) {
                    refMinFlow = Math.min(...allFlows);
                    refMaxFlow = Math.max(...allFlows);
                }
                if (allHeads.length > 0) {
                    refMinHead = Math.min(...allHeads);
                    refMaxHead = Math.max(...allHeads);
                }
            }

            // Calculate reference line boundaries extending beyond chart boundaries
            const flowRange = refMaxFlow - refMinFlow;
            const headRange = refMaxHead - refMinHead;

            // Extended boundaries well beyond chart limits
            const extendedMinFlow = Math.max(0, refMinFlow - flowRange * 0.6);
            const extendedMaxFlow = refMaxFlow + flowRange * 0.6;
            const extendedMinHead = Math.max(0, refMinHead - headRange * 0.6);
            const extendedMaxHead = refMaxHead + headRange * 0.6;

            // Reference line extensions beyond chart boundaries - Vertical (flow)
            traces.push({
                x: [opPoint.flow_m3hr, opPoint.flow_m3hr],
                y: [extendedMinHead, extendedMaxHead],
                type: 'scatter',
                mode: 'lines',
                name: 'Flow Reference Line',
                line: {
                    color: '#d32f2f',
                    width: 2,
                    dash: 'dot'
                },
                showlegend: false,
                hoverinfo: 'skip'
            });

            // Reference line extensions beyond chart boundaries - Horizontal (head)
            traces.push({
                x: [extendedMinFlow, extendedMaxFlow],
                y: [opPoint.head_m, opPoint.head_m],
                type: 'scatter',
                mode: 'lines',
                name: 'Head Reference Line',
                line: {
                    color: '#d32f2f',
                    width: 2,
                    dash: 'dot'
                },
                showlegend: false,
                hoverinfo: 'skip'
            });

            // Enhanced Operating Point Triangle Marker with comprehensive hover information
            // Calculate BEP percentage using real BEP data if available
            let bepPercentage = 'N/A';
            if (this.currentChartData.bep_analysis && this.currentChartData.bep_analysis.bep_available) {
                const bepFlow = this.currentChartData.bep_analysis.bep_flow;
                if (bepFlow > 0) {
                    bepPercentage = ((opPoint.flow_m3hr / bepFlow) * 100).toFixed(0);
                }
            }

            const efficiencyRating = opPoint.efficiency_pct >= 80 ? 'Excellent' :
                opPoint.efficiency_pct >= 70 ? 'Good' :
                    opPoint.efficiency_pct >= 60 ? 'Acceptable' : 'Poor';

            // Format impeller sizing information - use actual operating point requirements
            let impellerInfo = 'N/A';
            
            // First, try to get impeller information from the operating point data
            if (opPoint.impeller_diameter_mm) {
                const actualDiameter = opPoint.impeller_diameter_mm;
                
                // Check if sizing information is available (trimming/scaling details)
                if (opPoint.sizing_info) {
                    const sizingInfo = opPoint.sizing_info;
                    const baseDiameter = sizingInfo.base_diameter_mm;
                    const requiredDiameter = sizingInfo.required_diameter_mm;
                    const trimPercent = sizingInfo.trim_percent;
                    const sizingMethod = sizingInfo.sizing_method;
                    
                    if (sizingMethod === 'impeller_trimming' && baseDiameter && requiredDiameter && baseDiameter !== requiredDiameter) {
                        // Impeller trimming is applied
                        impellerInfo = `${baseDiameter.toFixed(0)}mm (Base) → ${requiredDiameter.toFixed(0)}mm (${trimPercent.toFixed(0)}% Trim)`;
                    } else if (sizingMethod === 'speed_variation') {
                        // Speed variation with effective impeller sizing
                        const speedInfo = this.currentChartData.speed_scaling;
                        const effectiveDiameter = sizingInfo.effective_diameter_mm || actualDiameter;
                        
                        if (speedInfo && speedInfo.applied && Math.abs(speedInfo.speed_ratio - 1.0) > 0.01) {
                            if (effectiveDiameter !== actualDiameter) {
                                // Show both actual and equivalent diameter
                                impellerInfo = `${actualDiameter.toFixed(0)}mm @ ${speedInfo.required_speed_rpm.toFixed(0)} RPM (equiv. ${effectiveDiameter.toFixed(0)}mm @ ${speedInfo.base_speed_rpm.toFixed(0)} RPM)`;
                            } else {
                                impellerInfo = `${actualDiameter.toFixed(0)}mm @ ${speedInfo.required_speed_rpm.toFixed(0)} RPM (scaled from ${speedInfo.base_speed_rpm.toFixed(0)} RPM)`;
                            }
                        } else {
                            impellerInfo = `${actualDiameter.toFixed(0)}mm Diameter`;
                        }
                    } else {
                        // Standard operation
                        impellerInfo = `${actualDiameter.toFixed(0)}mm Diameter`;
                    }
                } else {
                    // No detailed sizing info, but we have the operating point diameter
                    const speedInfo = this.currentChartData.speed_scaling;
                    if (speedInfo && speedInfo.applied && Math.abs(speedInfo.speed_ratio - 1.0) > 0.01) {
                        // Speed scaling is applied
                        impellerInfo = `${actualDiameter.toFixed(0)}mm @ ${speedInfo.required_speed_rpm.toFixed(0)} RPM (scaled from ${speedInfo.base_speed_rpm.toFixed(0)} RPM)`;
                    } else {
                        // Standard operation
                        impellerInfo = `${actualDiameter.toFixed(0)}mm Diameter`;
                    }
                }
            } else {
                // Fallback: try to get from selected curve if operating point data is missing
                let selectedCurve = null;
                if (this.currentChartData.curves && this.currentChartData.curves.length > 0) {
                    selectedCurve = this.currentChartData.curves.find(curve => curve.is_selected);
                    if (!selectedCurve) {
                        selectedCurve = this.currentChartData.curves[0];
                    }
                }
                
                if (selectedCurve && selectedCurve.impeller_diameter_mm) {
                    const speedInfo = this.currentChartData.speed_scaling;
                    if (speedInfo && speedInfo.applied && Math.abs(speedInfo.speed_ratio - 1.0) > 0.01) {
                        impellerInfo = `${selectedCurve.impeller_diameter_mm.toFixed(0)}mm @ ${speedInfo.required_speed_rpm.toFixed(0)} RPM (from curve data)`;
                    } else {
                        impellerInfo = `${selectedCurve.impeller_diameter_mm.toFixed(0)}mm Diameter (from curve data)`;
                    }
                }
            }

            traces.push({
                x: [opPoint.flow_m3hr],
                y: [opPoint.head_m],
                type: 'scatter',
                mode: 'markers',
                name: opPoint.extrapolated ? 'Operating Point (Extrapolated)' : 'Operating Point',
                marker: {
                    color: 'rgba(255,255,255,0)', // Transparent fill
                    size: 24, // Larger triangle marker for enhanced visibility
                    symbol: pointSymbol,
                    line: { color: '#d32f2f', width: 3 }
                },
                hovertemplate: '<b>🎯 OPERATING POINT ANALYSIS</b><br>' +
                    '<b>Flow Rate:</b> ' + (opPoint.flow_m3hr || 0).toFixed(1) + ' m³/hr<br>' +
                    '<b>Head:</b> ' + (opPoint.head_m || 0).toFixed(1) + ' m<br>' +
                    '<b>Efficiency:</b> ' + (opPoint.efficiency_pct || 0).toFixed(1) + '% (' + efficiencyRating + ')<br>' +
                    '<b>Power:</b> ' + (opPoint.power_kw ? opPoint.power_kw.toFixed(1) + ' kW' : 'Calculated') + '<br>' +
                    '<b>NPSH Required:</b> ' + (opPoint.npshr_m ? opPoint.npshr_m.toFixed(1) + ' m' : 'N/A') + '<br>' +
                    '<b>Impeller:</b> ' + impellerInfo + '<br>' +
                    '<b>BEP Position:</b> ' + bepPercentage + '% of optimal flow<br>' +
                    '<b>Status:</b> ' + (opPoint.extrapolated ? 'Extrapolated' : 'Within Curve') + '<extra></extra>'
            });
        }

        const title = this.currentChartData.pump_code + " - " + config.title;
        const yAxisTitle = config.yAxis;

        // Calculate proper y-axis range based on actual data
        let chartMaxHead = 60;
        let chartMinHead = 0;
        if (this.currentChartData.curves.length > 0) {
            const allHeads = this.currentChartData.curves.flatMap(c => c.head_data || []);
            if (allHeads.length > 0) {
                const dataMin = Math.min(...allHeads);
                const dataMax = Math.max(...allHeads);
                const range = dataMax - dataMin;
                chartMinHead = Math.max(0, dataMin - range * 0.05); // 5% padding below minimum, but not below 0
                chartMaxHead = dataMax + range * 0.05; // 5% padding above maximum
            }
        }

        const layout = {
            title: {
                text: title,
                font: { size: 18, color: '#1976d2', family: 'Roboto, sans-serif' },
                x: 0.05,
                xanchor: 'left'
            },
            xaxis: {
                title: {
                    text: 'Flow Rate (m³/hr)',
                    font: { size: 14, color: '#555' }
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
                    font: { size: 14, color: '#555' }
                },
                gridcolor: '#e0e0e0',
                gridwidth: 1,
                showline: true,
                linecolor: '#ccc',
                linewidth: 1,
                range: [chartMinHead, chartMaxHead] // Explicitly set y-axis range to match BEP zone
            },
            font: {
                family: 'Roboto, sans-serif',
                size: 12,
                color: '#333'
            },
            paper_bgcolor: '#ffffff',
            plot_bgcolor: '#fafafa',
            margin: { l: 90, r: 90, t: 100, b: 140 },
            showlegend: true,
            legend: {
                orientation: 'h',
                x: 0.5,
                y: -0.3,
                xanchor: 'center',
                yanchor: 'top',
                bgcolor: 'rgba(255,255,255,0.95)',
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
            console.log('Charts.js: Attempting to render head-flow chart with', traces.length, 'traces');
            console.log('Charts.js: Container ID:', containerId);
            console.log('Charts.js: Container element:', document.getElementById(containerId));

            Plotly.newPlot(containerId, traces, layout, plotConfig);
            console.log('Charts.js: Head-flow chart rendered successfully');
            // Remove loading spinner after successful render
            this.removeLoadingSpinner(containerId);
        } catch (error) {
            console.error('Error rendering head-flow chart:', error);
            document.getElementById('head-flow-chart').innerHTML = '<p style="text-align: center; padding: 50px; color: red;">Error rendering chart</p>';
            this.removeLoadingSpinner(containerId);
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
                    // Generate proper impeller size name
                    let impellerName = 'Unknown Size';
                    if (curve.impeller_diameter_mm) {
                        impellerName = curve.impeller_diameter_mm + "mm Impeller";
                    } else if (curve.impeller_size && curve.impeller_size !== "Curve " + (index + 1) && !curve.impeller_size.includes('Curve')) {
                        impellerName = curve.impeller_size + "mm Impeller";
                    } else {
                        impellerName = "Impeller " + (index + 1);
                    }

                    traces.push({
                        x: curve.flow_data,
                        y: curve.efficiency_data,
                        type: 'scatter',
                        mode: 'lines+markers',
                        name: impellerName,
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

        // Add BEP Operating Range Visualization to Efficiency Chart
        const opPoint = this.currentChartData.operating_point;
        if (opPoint && opPoint.flow_m3hr && opPoint.efficiency_pct != null && opPoint.efficiency_pct > 0) {
            const bep80Flow = opPoint.flow_m3hr * 0.8;
            const bep110Flow = opPoint.flow_m3hr * 1.1;

            // Get efficiency range for shaded zone based on actual data
            let maxEffForZone = 100;
            let minEffForZone = 0;
            if (Array.isArray(this.currentChartData.curves) && this.currentChartData.curves.length > 0) {
                const allEffs = this.currentChartData.curves.flatMap(c => Array.isArray(c?.efficiency_data) ? c.efficiency_data : []).filter(e => e != null && e > 0);
                if (allEffs.length > 0) {
                    minEffForZone = Math.max(0, Math.min(...allEffs) * 0.9); // Start 10% below minimum but not below 0
                    maxEffForZone = Math.max(...allEffs) * 1.1; // Extend slightly beyond max for full coverage
                }
            }

            // BEP Preferred Operating Zone for Efficiency (80%-110%) - Shaded area
            traces.push({
                x: [bep80Flow, bep110Flow, bep110Flow, bep80Flow, bep80Flow],
                y: [minEffForZone, minEffForZone, maxEffForZone, maxEffForZone, minEffForZone],
                type: 'scatter',
                mode: 'lines',
                fill: 'toself',
                fillcolor: 'rgba(255, 193, 7, 0.15)',
                line: { color: 'rgba(255, 193, 7, 0.3)', width: 1 },
                name: 'Preferred Operating Zone',
                hoverinfo: 'text',
                text: 'Optimal Efficiency Range<br>80% - 110% of BEP Flow',
                showlegend: true
            });
            const pointColor = '#d32f2f'; // Red color for duty point
            const pointSymbol = 'triangle-up'; // Red triangle marker

            // Get chart data ranges for proper reference line scaling
            let chartMaxFlow = 500;
            let chartMinFlow = 0;
            let chartMaxEff = 100;
            let chartMinEff = 0;
            if (Array.isArray(this.currentChartData.curves) && this.currentChartData.curves.length > 0) {
                const allFlows = this.currentChartData.curves.flatMap(c => Array.isArray(c?.flow_data) ? c.flow_data : []);
                const allEffs = this.currentChartData.curves.flatMap(c => Array.isArray(c?.efficiency_data) ? c.efficiency_data : []).filter(e => e != null && e > 0);
                if (allFlows.length > 0) {
                    chartMinFlow = Math.min(...allFlows);
                    chartMaxFlow = Math.max(...allFlows);
                }
                if (allEffs.length > 0) {
                    chartMinEff = Math.min(...allEffs);
                    chartMaxEff = Math.max(...allEffs);
                }
            }

            // Calculate reference line boundaries using robust logic
            const flowRange = chartMaxFlow - chartMinFlow;
            const effRange = chartMaxEff - chartMinEff;

            // Ensure minimum extension values for small ranges
            const minFlowExtension = Math.max(flowRange * 0.4, 100); // At least 100 units or 40% of range
            const minEffExtension = Math.max(effRange * 0.4, 10);    // At least 10 units or 40% of range

            // Calculate extended boundaries with proper bounds checking
            const extendedMinFlow = Math.max(0, chartMinFlow - minFlowExtension);
            const extendedMaxFlow = chartMaxFlow + minFlowExtension;
            const extendedMinEff = Math.max(0, chartMinEff - minEffExtension);
            const extendedMaxEff = chartMaxEff + minEffExtension;

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
                    color: 'rgba(255,255,255,0)', // Transparent fill
                    size: 18,
                    symbol: pointSymbol,
                    line: { color: '#d32f2f', width: 3 }
                },
                hovertemplate: '<b>Operating Point</b><br>Flow: %{x:.0f} m³/hr<br>Efficiency: %{y:.1f}%<extra></extra>'
            });
        }

        const title = this.currentChartData.pump_code + " - " + config.title;
        const yAxisTitle = config.yAxis;

        // Calculate proper y-axis range based on actual efficiency data
        let maxEfficiency = 100;
        let minEfficiency = 0;
        if (this.currentChartData.curves.length > 0) {
            const allEfficiencies = this.currentChartData.curves.flatMap(c => c.efficiency_data || []);
            if (allEfficiencies.length > 0) {
                const dataMin = Math.min(...allEfficiencies);
                const dataMax = Math.max(...allEfficiencies);
                const range = dataMax - dataMin;
                minEfficiency = Math.max(0, dataMin - range * 0.05); // 5% padding below minimum, but not below 0
                maxEfficiency = Math.min(100, dataMax + range * 0.05); // 5% padding above maximum, but not above 100%
            }
        }

        const layout = {
            title: {
                text: title,
                font: { size: 18, color: '#1976d2', family: 'Roboto, sans-serif' },
                x: 0.05,
                xanchor: 'left'
            },
            xaxis: {
                title: {
                    text: 'Flow Rate (m³/hr)',
                    font: { size: 14, color: '#555' }
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
                    font: { size: 14, color: '#555' }
                },
                gridcolor: '#e0e0e0',
                gridwidth: 1,
                showline: true,
                linecolor: '#ccc',
                linewidth: 1,
                range: [minEfficiency, maxEfficiency] // Explicitly set y-axis range
            },
            font: {
                family: 'Roboto, sans-serif',
                size: 12,
                color: '#333'
            },
            paper_bgcolor: '#ffffff',
            plot_bgcolor: '#fafafa',
            margin: { l: 90, r: 90, t: 100, b: 140 },
            showlegend: true,
            legend: {
                orientation: 'h',
                x: 0.5,
                y: -0.3,
                xanchor: 'center',
                yanchor: 'top',
                bgcolor: 'rgba(255,255,255,0.95)',
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
            // Remove loading spinner after successful render
            this.removeLoadingSpinner(containerId);
        } catch (error) {
            console.error('Error rendering efficiency-flow chart:', error);
            document.getElementById('efficiency-flow-chart').innerHTML = '<p style="text-align: center; padding: 50px; color: red;">Error rendering chart</p>';
            this.removeLoadingSpinner(containerId);
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
                    // Generate proper impeller size name
                    let impellerName = 'Unknown Size';
                    if (curve.impeller_diameter_mm) {
                        impellerName = curve.impeller_diameter_mm + "mm Impeller";
                    } else if (curve.impeller_size && curve.impeller_size !== "Curve " + (index + 1) && !curve.impeller_size.includes('Curve')) {
                        impellerName = curve.impeller_size + "mm Impeller";
                    } else {
                        impellerName = "Impeller " + (index + 1);
                    }

                    traces.push({
                        x: curve.flow_data,
                        y: curve.power_data,
                        type: 'scatter',
                        mode: 'lines+markers',
                        name: impellerName,
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

        // Add BEP Operating Range Visualization to Power Chart
        const opPoint = this.currentChartData.operating_point;
        if (opPoint && opPoint.flow_m3hr && opPoint.power_kw != null && opPoint.power_kw > 0) {
            const bep80Flow = opPoint.flow_m3hr * 0.8;
            const bep110Flow = opPoint.flow_m3hr * 1.1;

            // Get power range for shaded zone based on actual data
            let maxPowerZone = 300;
            let minPowerZone = 0;
            if (Array.isArray(this.currentChartData.curves) && this.currentChartData.curves.length > 0) {
                const allPowers = this.currentChartData.curves.flatMap(c => Array.isArray(c?.power_data) ? c.power_data : []).filter(p => p != null && p > 0);
                if (allPowers.length > 0) {
                    minPowerZone = Math.max(0, Math.min(...allPowers) * 0.9); // Start 10% below minimum but not below 0
                    maxPowerZone = Math.max(...allPowers) * 1.2; // Extend slightly beyond max for full coverage
                }
            }

            // BEP Preferred Operating Zone for Power (80%-110%) - Shaded area
            traces.push({
                x: [bep80Flow, bep110Flow, bep110Flow, bep80Flow, bep80Flow],
                y: [minPowerZone, minPowerZone, maxPowerZone, maxPowerZone, minPowerZone],
                type: 'scatter',
                mode: 'lines',
                fill: 'toself',
                fillcolor: 'rgba(33, 150, 243, 0.15)',
                line: { color: 'rgba(33, 150, 243, 0.3)', width: 1 },
                name: 'Efficient Power Zone',
                hoverinfo: 'text',
                text: 'Optimal Power Range<br>80% - 110% of BEP Flow',
                showlegend: true
            });
            const pointColor = '#d32f2f'; // Red color for duty point
            const pointSymbol = 'triangle-up'; // Red triangle marker

            // Get chart data ranges for proper reference line scaling
            let maxFlowRef = 500;
            let maxPowerRef = 200;
            let minFlowRef = 0;
            let minPowerRef = 0;
            if (Array.isArray(this.currentChartData.curves) && this.currentChartData.curves.length > 0) {
                const allFlows = this.currentChartData.curves.flatMap(c => Array.isArray(c?.flow_data) ? c.flow_data : []);
                const allPowers = this.currentChartData.curves.flatMap(c => Array.isArray(c?.power_data) ? c.power_data : []).filter(p => p != null && p > 0);
                if (allFlows.length > 0) {
                    minFlowRef = Math.min(...allFlows);
                    maxFlowRef = Math.max(...allFlows);
                }
                if (allPowers.length > 0) {
                    minPowerRef = Math.min(...allPowers);
                    maxPowerRef = Math.max(...allPowers);
                }
            }

            // Calculate reference line boundaries using robust logic
            const flowRange = maxFlowRef - minFlowRef;
            const powerRange = maxPowerRef - minPowerRef;

            // Ensure minimum extension values for small ranges
            const minFlowExtension = Math.max(flowRange * 0.4, 100); // At least 100 units or 40% of range
            const minPowerExtension = Math.max(powerRange * 0.4, 20); // At least 20 units or 40% of range

            // Calculate extended boundaries with proper bounds checking
            const extendedMinFlow = Math.max(0, minFlowRef - minFlowExtension);
            const extendedMaxFlow = maxFlowRef + minFlowExtension;
            const extendedMinPower = Math.max(0, minPowerRef - minPowerExtension);
            const extendedMaxPower = maxPowerRef + minPowerExtension;

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
                    color: 'rgba(255,255,255,0)', // Transparent fill
                    size: 18,
                    symbol: pointSymbol,
                    line: { color: '#d32f2f', width: 3 }
                },
                hovertemplate: '<b>Operating Point</b><br>Flow: %{x:.0f} m³/hr<br>Power: %{y:.1f} kW<extra></extra>'
            });
        }

        const title = this.currentChartData.pump_code + " - " + config.title;
        const yAxisTitle = config.yAxis;

        // Calculate proper y-axis range based on actual power data
        let maxPower = 200;
        let minPower = 0;
        if (this.currentChartData.curves.length > 0) {
            const allPowers = this.currentChartData.curves.flatMap(c => c.power_data || []).filter(p => p != null && p > 0);
            if (allPowers.length > 0) {
                const dataMin = Math.min(...allPowers);
                const dataMax = Math.max(...allPowers);
                const range = dataMax - dataMin;
                minPower = Math.max(0, dataMin - range * 0.05); // 5% padding below minimum, but not below 0
                maxPower = dataMax + range * 0.05; // 5% padding above maximum
            }
        }

        const layout = {
            title: {
                text: title,
                font: { size: 18, color: '#1976d2', family: 'Roboto, sans-serif' },
                x: 0.05,
                xanchor: 'left'
            },
            xaxis: {
                title: {
                    text: 'Flow Rate (m³/hr)',
                    font: { size: 14, color: '#555' }
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
                    font: { size: 14, color: '#555' }
                },
                gridcolor: '#e0e0e0',
                gridwidth: 1,
                showline: true,
                linecolor: '#ccc',
                linewidth: 1,
                range: [minPower, maxPower] // Explicitly set y-axis range
            },
            font: {
                family: 'Roboto, sans-serif',
                size: 12,
                color: '#333'
            },
            paper_bgcolor: '#ffffff',
            plot_bgcolor: '#fafafa',
            margin: { l: 90, r: 90, t: 100, b: 140 },
            showlegend: true,
            legend: {
                orientation: 'h',
                x: 0.5,
                y: -0.3,
                xanchor: 'center',
                yanchor: 'top',
                bgcolor: 'rgba(255,255,255,0.95)',
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
            // Remove loading spinner after successful render
            this.removeLoadingSpinner(containerId);
        } catch (error) {
            console.error('Error rendering power-flow chart:', error);
            document.getElementById('power-flow-chart').innerHTML = '<p style="text-align: center; padding: 50px; color: red;">Error rendering chart</p>';
            this.removeLoadingSpinner(containerId);
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
                    // Generate proper impeller size name
                    let impellerName = 'Unknown Size';
                    if (curve.impeller_diameter_mm) {
                        impellerName = curve.impeller_diameter_mm + "mm Impeller";
                    } else if (curve.impeller_size && curve.impeller_size !== "Curve " + (index + 1) && !curve.impeller_size.includes('Curve')) {
                        impellerName = curve.impeller_size + "mm Impeller";
                    } else {
                        impellerName = "Impeller " + (index + 1);
                    }

                    traces.push({
                        x: curve.flow_data,
                        y: curve.npshr_data,
                        type: 'scatter',
                        mode: 'lines+markers',
                        name: impellerName,
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
            let maxFlowNpsh = 500;
            let maxNpshRef = 10;
            let minFlowNpsh = 0;
            let minNpshRef = 0;
            if (Array.isArray(this.currentChartData.curves) && this.currentChartData.curves.length > 0) {
                const allFlows = this.currentChartData.curves.flatMap(c => Array.isArray(c?.flow_data) ? c.flow_data : []);
                const allNpsh = this.currentChartData.curves.flatMap(c => Array.isArray(c?.npshr_data) ? c.npshr_data : []).filter(val => val != null && val > 0);
                if (allFlows.length > 0) {
                    minFlowNpsh = Math.min(...allFlows);
                    maxFlowNpsh = Math.max(...allFlows);
                }
                if (allNpsh.length > 0) {
                    minNpshRef = Math.min(...allNpsh);
                    maxNpshRef = Math.max(...allNpsh);
                }
            }

            // Calculate reference line boundaries using robust logic
            const flowRange = maxFlowNpsh - minFlowNpsh;
            const npshRange = maxNpshRef - minNpshRef;

            // Ensure minimum extension values for small ranges
            const minFlowExtension = Math.max(flowRange * 0.4, 100); // At least 100 units or 40% of range
            const minNpshExtension = Math.max(npshRange * 0.4, 2);   // At least 2 units or 40% of range

            // Calculate extended boundaries with proper bounds checking
            const extendedMinFlow = Math.max(0, minFlowNpsh - minFlowExtension);
            const extendedMaxFlow = maxFlowNpsh + minFlowExtension;
            const extendedMinNpsh = Math.max(0, minNpshRef - minNpshExtension);
            const extendedMaxNpsh = maxNpshRef + minNpshExtension;

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
                    color: 'rgba(255,255,255,0)', // Transparent fill
                    size: 18,
                    symbol: pointSymbol,
                    line: { color: '#d32f2f', width: 3 }
                },
                hovertemplate: '<b>Operating Point</b><br>Flow: %{x:.0f} m³/hr<br>NPSHr: %{y:.1f} m<extra></extra>'
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

        const title = this.currentChartData.pump_code + " - " + config.title;
        const yAxisTitle = config.yAxis;

        // Calculate proper y-axis range based on actual NPSH data
        let maxNpsh = 20;
        let minNpsh = 0;
        if (this.currentChartData.curves.length > 0) {
            const allNpsh = this.currentChartData.curves.flatMap(c => c.npshr_data || []).filter(n => n != null && n > 0);
            if (allNpsh.length > 0) {
                const dataMin = Math.min(...allNpsh);
                const dataMax = Math.max(...allNpsh);
                const range = dataMax - dataMin;
                minNpsh = Math.max(0, dataMin - range * 0.05); // 5% padding below minimum, but not below 0
                maxNpsh = dataMax + range * 0.05; // 5% padding above maximum
            }
        }

        const layout = {
            title: {
                text: title,
                font: { size: 18, color: '#1976d2', family: 'Roboto, sans-serif' },
                x: 0.05,
                xanchor: 'left'
            },
            xaxis: {
                title: {
                    text: 'Flow Rate (m³/hr)',
                    font: { size: 14, color: '#555' }
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
                    font: { size: 14, color: '#555' }
                },
                gridcolor: '#e0e0e0',
                gridwidth: 1,
                showline: true,
                linecolor: '#ccc',
                linewidth: 1,
                range: [minNpsh, maxNpsh] // Explicitly set y-axis range
            },
            font: {
                family: 'Roboto, sans-serif',
                size: 12,
                color: '#333'
            },
            paper_bgcolor: '#ffffff',
            plot_bgcolor: '#fafafa',
            margin: { l: 90, r: 90, t: 100, b: 140 },
            showlegend: true,
            legend: {
                orientation: 'h',
                x: 0.5,
                y: -0.3,
                xanchor: 'center',
                yanchor: 'top',
                bgcolor: 'rgba(255,255,255,0.95)',
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
            // Remove loading spinner after successful render
            this.removeLoadingSpinner(containerId);
        } catch (error) {
            console.error('Error rendering npshr-flow chart:', error);
            document.getElementById('npshr-flow-chart').innerHTML = '<p style="text-align: center; padding: 50px; color: red;">Error rendering chart</p>';
            this.removeLoadingSpinner(containerId);
        }
    }

    renderAllCharts(pumpCode, flowRate, head) {
        console.log('Charts.js: Starting renderAllCharts for:', { pumpCode, flowRate, head });

        // Prevent multiple initializations for the same pump
        const chartKey = pumpCode + '_' + flowRate + '_' + head;
        if (this.chartsInitialized === chartKey) {
            console.log('Charts.js: Charts already initialized for this pump, skipping...');
            return;
        }

        // Ensure chart containers are visible and show loading state
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
                    // Show loading indicator
                    container.innerHTML = '<div style="display: flex; justify-content: center; align-items: center; height: 100%; min-height: 400px; flex-direction: column;">' +
                        '<div class="spinner-border text-primary mb-3" role="status">' +
                        '<span class="visually-hidden">Loading...</span>' +
                        '</div>' +
                        '<div class="text-muted">Loading ' + containerId.replace('-', ' ').replace('chart', '') + ' chart...</div>' +
                        '</div>';
                    console.log('Charts.js: Made container ' + containerId + ' visible with loading indicator');
                } else {
                    console.warn('Charts.js: Container ' + containerId + ' not found');
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

    removeLoadingSpinner(containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            // Remove any existing spinner elements
            const spinner = container.querySelector('.spinner-border');
            if (spinner) {
                spinner.remove();
            }
            // Remove loading text
            const loadingText = container.querySelector('.text-muted');
            if (loadingText) {
                loadingText.remove();
            }
        }
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
                    errorText.textContent = "Error loading chart data: " + message;

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
    console.log('Force refreshing charts for:', { pumpCode, flowRate, head });

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



document.addEventListener('DOMContentLoaded', function() {
    initializationAttempts++;
    console.log("Charts.js: DOM loaded (attempt " + initializationAttempts + "), checking for charts...");

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