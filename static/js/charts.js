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

                    // Apply speed scaling to selected curve if applied
                    let flowData = [...curve.flow_data];
                    let headData = [...curve.head_data];
                    
                    if (this.currentChartData.speed_scaling && this.currentChartData.speed_scaling.applied && curve.is_selected) {
                        const speedRatio = this.currentChartData.speed_scaling.speed_ratio;
                        const requiredSpeed = this.currentChartData.speed_scaling.required_speed_rpm;
                        
                        // Apply affinity laws: Flow ∝ speed, Head ∝ speed²
                        flowData = flowData.map(flow => flow * speedRatio);
                        headData = headData.map(head => head * (speedRatio * speedRatio));
                        
                        impellerName += ` (${Math.round(requiredSpeed)} RPM)`;
                        console.log(`Charts.js: Applied speed scaling to selected curve - ratio: ${speedRatio.toFixed(3)}`);
                    }

                    traces.push({
                        x: flowData,
                        y: headData,
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
                // Generate system curve based on actual system requirements
                // System curve should pass through the required duty point, NOT the pump's delivery point
                
                // Use system requirements if available, otherwise fall back to operating point
                let systemFlow = opPoint.flow_m3hr;
                let systemHead = opPoint.head_m;
                
                // Check if we have actual system requirements
                if (this.currentChartData.system_requirements) {
                    systemFlow = this.currentChartData.system_requirements.flow_m3hr;
                    systemHead = this.currentChartData.system_requirements.head_m;
                    console.log('Using actual system requirements:', { systemFlow, systemHead });
                }
                
                // Calculate system curve parameters based on typical system design
                // Assume 40% static head and 60% friction losses at duty point
                const staticHead = systemHead * 0.4; // 40% static head
                const frictionHead = systemHead - staticHead;
                const frictionCoeff = frictionHead / (systemFlow * systemFlow);

                // Generate system curve points from 0 to 150% of duty flow
                const systemFlows = [];
                const systemHeads = [];

                for (let i = 0; i <= 15; i++) {
                    const flow = (systemFlow * i) / 10; // 0% to 150% in 10% increments
                    const head = staticHead + frictionCoeff * flow * flow;
                    systemFlows.push(flow);
                    systemHeads.push(head);
                }

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
                    hovertemplate: '<b>System Curve</b><br>Flow: %{x:.0f} m³/hr<br>Head: %{y:.1f} m<br><i>Static: ' + (staticHead || 0).toFixed(1) + 'm + Friction</i><extra></extra>',
                    showlegend: true
                });
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
                x: [operatingPointFlow, operatingPointFlow],
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
                y: [operatingPointHead, operatingPointHead],
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
                    bepPercentage = ((operatingPointFlow / bepFlow) * 100).toFixed(0);
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
                        impellerInfo = baseDiameter.toFixed(0) + "mm (Base) → " + requiredDiameter.toFixed(0) + "mm (" + trimPercent.toFixed(0) + "% Trim)";
                    } else if (sizingMethod === 'speed_variation') {
                        // Speed variation with effective impeller sizing
                        const speedInfo = this.currentChartData.speed_scaling;
                        const effectiveDiameter = sizingInfo.effective_diameter_mm || actualDiameter;

                        if (speedInfo && speedInfo.applied && Math.abs(speedInfo.speed_ratio - 1.0) > 0.01) {
                            impellerInfo = actualDiameter.toFixed(0) + "mm @ " + speedInfo.required_speed_rpm.toFixed(0) + " RPM";
                        } else {
                            impellerInfo = actualDiameter.toFixed(0) + "mm Diameter";
                        }
                    } else {
                        // Standard operation
                        impellerInfo = actualDiameter.toFixed(0) + "mm Diameter";
                    }
                } else {
                    // No detailed sizing info, but we have the operating point diameter
                    const speedInfo = this.currentChartData.speed_scaling;
                    if (speedInfo && speedInfo.applied && Math.abs(speedInfo.speed_ratio - 1.0) > 0.01) {
                        // Speed scaling - show actual impeller and operating speed
                        impellerInfo = actualDiameter.toFixed(0) + "mm @ " + speedInfo.required_speed_rpm.toFixed(0) + " RPM";
                    } else {
                        // Standard operation
                        impellerInfo = actualDiameter.toFixed(0) + "mm Diameter";
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
                        impellerInfo = selectedCurve.impeller_diameter_mm.toFixed(0) + "mm @ " + speedInfo.required_speed_rpm.toFixed(0) + " RPM (from curve data)";
                    } else {
                        impellerInfo = selectedCurve.impeller_diameter_mm.toFixed(0) + "mm Diameter (from curve data)";
                    }
                }
            }

            // Apply speed scaling to operating point coordinates if speed scaling is active
            let operatingPointFlow = opPoint.flow_m3hr;
            let operatingPointHead = opPoint.head_m;
            
            if (this.currentChartData.speed_scaling && this.currentChartData.speed_scaling.applied) {
                const speedRatio = this.currentChartData.speed_scaling.speed_ratio;
                // Apply affinity laws to operating point: Flow ∝ speed, Head ∝ speed²
                operatingPointFlow = opPoint.flow_m3hr * speedRatio;
                operatingPointHead = opPoint.head_m * (speedRatio * speedRatio);
                console.log(`Charts.js: Applied speed scaling to operating point - Flow: ${opPoint.flow_m3hr.toFixed(1)} → ${operatingPointFlow.toFixed(1)}, Head: ${opPoint.head_m.toFixed(1)} → ${operatingPointHead.toFixed(1)}`);
            }

            traces.push({
                x: [operatingPointFlow],
                y: [operatingPointHead],
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

                    // Apply speed scaling to selected curve if applied
                    let flowData = [...curve.flow_data];
                    let efficiencyData = [...curve.efficiency_data];
                    
                    if (this.currentChartData.speed_scaling && this.currentChartData.speed_scaling.applied && curve.is_selected) {
                        const speedRatio = this.currentChartData.speed_scaling.speed_ratio;
                        const requiredSpeed = this.currentChartData.speed_scaling.required_speed_rpm;
                        
                        // Apply affinity laws: Flow ∝ speed, Efficiency stays constant
                        flowData = flowData.map(flow => flow * speedRatio);
                        // Efficiency data remains unchanged as efficiency is independent of speed
                        
                        impellerName += ` (${Math.round(requiredSpeed)} RPM)`;
                        console.log(`Charts.js: Applied speed scaling to efficiency curve - ratio: ${speedRatio.toFixed(3)}`);
                    }

                    traces.push({
                        x: flowData,
                        y: efficiencyData,
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

                    // Apply speed scaling to selected curve if applied
                    let flowData = [...curve.flow_data];
                    let powerData = [...curve.power_data];
                    
                    if (this.currentChartData.speed_scaling && this.currentChartData.speed_scaling.applied && curve.is_selected) {
                        const speedRatio = this.currentChartData.speed_scaling.speed_ratio;
                        const requiredSpeed = this.currentChartData.speed_scaling.required_speed_rpm;
                        
                        // Apply affinity laws: Flow ∝ speed, Power ∝ speed³
                        flowData = flowData.map(flow => flow * speedRatio);
                        powerData = powerData.map(power => power * (speedRatio * speedRatio * speedRatio));
                        
                        impellerName += ` (${Math.round(requiredSpeed)} RPM)`;
                        console.log(`Charts.js: Applied speed scaling to power curve - ratio: ${speedRatio.toFixed(3)}`);
                    }

                    traces.push({
                        x: flowData,
                        y: powerData,
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

                    // Apply speed scaling to selected curve if applied
                    let flowData = [...curve.flow_data];
                    let npshData = [...curve.npshr_data];
                    
                    if (this.currentChartData.speed_scaling && this.currentChartData.speed_scaling.applied && curve.is_selected) {
                        const speedRatio = this.currentChartData.speed_scaling.speed_ratio;
                        const requiredSpeed = this.currentChartData.speed_scaling.required_speed_rpm;
                        
                        // Apply affinity laws: Flow ∝ speed, NPSH ∝ speed²
                        flowData = flowData.map(flow => flow * speedRatio);
                        npshData = npshData.map(npsh => npsh * (speedRatio * speedRatio));
                        
                        impellerName += ` (${Math.round(requiredSpeed)} RPM)`;
                        console.log(`Charts.js: Applied speed scaling to NPSH curve - ratio: ${speedRatio.toFixed(3)}`);
                    }
                    
                    // Generate smooth mother curve using cubic spline interpolation
                    const minFlow = Math.min(...flowData);
                    const maxFlow = Math.max(...flowData);
                    const smoothedFlowData = [];
                    const smoothedNpshData = [];
                    
                    // Create 100 points for very smooth curve
                    for (let i = 0; i <= 100; i++) {
                        const flow = minFlow + (maxFlow - minFlow) * i / 100;
                        smoothedFlowData.push(flow);
                        
                        // Use cubic spline interpolation for smooth curves with speed-scaled data
                        const npsh = this.cubicSplineInterpolate(flowData, npshData, flow);
                        smoothedNpshData.push(npsh);
                    }
                    
                    // Add smooth mother curve
                    traces.push({
                        x: smoothedFlowData,
                        y: smoothedNpshData,
                        type: 'scatter',
                        mode: 'lines',
                        name: impellerName,
                        line: {
                            color: curve.is_selected ? config.color : this.getAlternateColor(index),
                            width: curve.is_selected ? 3 : 2,
                            shape: 'spline', // Use spline for even smoother rendering
                            smoothing: 1.3 // Add smoothing parameter
                        },
                        hovertemplate: '<b>%{fullData.name}</b><br>Flow: %{x:.1f} m³/hr<br>NPSHr: %{y:.2f} m<extra></extra>'
                    });
                    
                    // Add original test data points as small markers (using speed-scaled data)
                    traces.push({
                        x: flowData,
                        y: npshData,
                        type: 'scatter',
                        mode: 'markers',
                        name: 'Test Data',
                        marker: {
                            color: curve.is_selected ? config.color : this.getAlternateColor(index),
                            size: 4,
                            symbol: 'circle',
                            line: {
                                color: 'white',
                                width: 1
                            }
                        },
                        showlegend: false,
                        hovertemplate: '<b>Test Point</b><br>Flow: %{x:.1f} m³/hr<br>NPSHr: %{y:.2f} m<extra></extra>'
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

            // Vertical reference line (flow) - constrain to calculated y-axis range
            // Use the same range calculation as the y-axis to ensure consistency
            const yAxisMin = Math.max(0, minNpshRef - (maxNpshRef - minNpshRef) * 0.05);
            const yAxisMax = maxNpshRef + (maxNpshRef - minNpshRef) * 0.05;
            
            traces.push({
                x: [opPoint.flow_m3hr, opPoint.flow_m3hr],
                y: [yAxisMin, yAxisMax], // Use exact same range as y-axis
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
        }
        
        if (!hasNpshData) {
            // Show message when no NPSH data is available
            // Use middle of the expected range instead of 0
            traces.push({
                x: [100],
                y: [3],
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
        let maxNpsh = 4;
        let minNpsh = 0;
        if (this.currentChartData.curves && this.currentChartData.curves.length > 0) {
            const allNpsh = this.currentChartData.curves.flatMap(c => c.npshr_data || []).filter(n => n != null && n > 0);
            if (allNpsh.length > 0) {
                const dataMin = Math.min(...allNpsh);
                const dataMax = Math.max(...allNpsh);
                const range = dataMax - dataMin;
                
                // Use tighter padding for better visualization - FIXED LOGIC
                minNpsh = Math.max(0, dataMin - range * 0.05); // 5% padding below minimum
                maxNpsh = dataMax + range * 0.05; // 5% padding above maximum
                
                // Ensure minimum visible range for readability
                if (maxNpsh - minNpsh < 1.0) {
                    const center = (dataMax + dataMin) / 2;
                    minNpsh = Math.max(0, center - 0.5);
                    maxNpsh = center + 0.5;
                }
                
                // Prevent axis from starting at 0 when data is much higher
                if (dataMin > 1.5) {
                    minNpsh = Math.max(0, dataMin - 0.3);
                }
                

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
                range: [minNpsh, maxNpsh], // Explicitly set y-axis range
                autorange: false, // Disable auto-ranging to force our range
                fixedrange: true, // Prevent user from zooming/panning y-axis
                rangemode: 'normal', // Prevent Plotly from extending axis to 0
                autorangeoptions: {
                    minallowed: minNpsh,
                    maxallowed: maxNpsh,
                    clipmin: minNpsh,
                    clipmax: maxNpsh
                }
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
    
    // Cubic spline interpolation for smooth curves
    cubicSplineInterpolate(xData, yData, x) {
        const n = xData.length;
        if (n < 2) return yData[0];
        
        // Find the interval
        let i = 0;
        for (let j = 1; j < n; j++) {
            if (x <= xData[j]) {
                i = j - 1;
                break;
            }
        }
        if (i === 0 && x > xData[n - 1]) {
            i = n - 2;
        }
        
        // Use natural cubic spline approach
        const h = xData[i + 1] - xData[i];
        const t = (x - xData[i]) / h;
        
        // Estimate derivatives using finite differences
        let d0, d1;
        if (i === 0) {
            d0 = (yData[1] - yData[0]) / (xData[1] - xData[0]);
            d1 = (yData[2] - yData[0]) / (xData[2] - xData[0]);
        } else if (i === n - 2) {
            d0 = (yData[n - 1] - yData[n - 3]) / (xData[n - 1] - xData[n - 3]);
            d1 = (yData[n - 1] - yData[n - 2]) / (xData[n - 1] - xData[n - 2]);
        } else {
            d0 = (yData[i + 1] - yData[i - 1]) / (xData[i + 1] - xData[i - 1]);
            d1 = (yData[i + 2] - yData[i]) / (xData[i + 2] - xData[i]);
        }
        
        // Hermite cubic interpolation
        const h00 = 2 * t * t * t - 3 * t * t + 1;
        const h10 = t * t * t - 2 * t * t + t;
        const h01 = -2 * t * t * t + 3 * t * t;
        const h11 = t * t * t - t * t;
        
        return h00 * yData[i] + h10 * h * d0 + h01 * yData[i + 1] + h11 * h * d1;
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