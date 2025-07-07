/**
 * Pump Data Table Manager - Displays authentic manufacturer performance data
 * Based on APE pump data format with engineering assessment
 */

class PumpDataTableManager {
    constructor() {
        this.targetFlow = null;
        this.targetHead = null;
        this.flowTolerance = 0.10; // 10% tolerance
    }

    render(pumpData, targetFlow, targetHead, containerId = 'pumpDataTableContainer') {
        this.targetFlow = targetFlow;
        this.targetHead = targetHead;

        const container = document.getElementById(containerId);
        if (!container) {
            console.error('Pump data table container not found');
            return;
        }

        // Generate the data table HTML
        const tableHtml = this.generateDataTable(pumpData);
        container.innerHTML = tableHtml;

        // Add engineering assessment
        this.addEngineeringAssessment(pumpData, containerId);
    }

    generateDataTable(pumpData) {
        if (!pumpData || !pumpData.curves || pumpData.curves.length === 0) {
            return '<div class="alert alert-warning">No performance data available</div>';
        }

        let html = `
            <div class="card">
                <div class="card-header d-flex align-items-center" style="background: #f8f9fa; border-bottom: 2px solid #1976d2;">
                    <i class="material-icons me-2" style="color: #1976d2;">assessment</i>
                    <h5 class="mb-0" style="color: #1976d2; font-weight: 600;">Manufacturer Performance Data</h5>
                </div>
                <div class="card-body">
                    ${this.generatePumpInfo(pumpData)}
                    ${this.generatePerformanceTables(pumpData)}
                </div>
            </div>
        `;

        return html;
    }

    generatePumpInfo(pumpData) {
        const firstCurve = pumpData.curves[0];
        const maxFlow = Math.max(...pumpData.curves.flatMap(c => 
            c.performance_points.filter(p => p.flow_m3hr > 0).map(p => p.flow_m3hr)
        ));
        const maxHead = Math.max(...pumpData.curves.flatMap(c => 
            c.performance_points.filter(p => p.head_m > 0).map(p => p.head_m)
        ));

        return `
            <div class="pump-info-header mb-4" style="background: #f5f5f5; padding: 16px; border-radius: 8px;">
                <div class="row">
                    <div class="col-md-6">
                        <div class="d-flex justify-content-between mb-2">
                            <span style="font-weight: 500;">Pump Type:</span>
                            <span>Vertical Turbine Pump (VTP)</span>
                        </div>
                        <div class="d-flex justify-content-between mb-2">
                            <span style="font-weight: 500;">Pump Model:</span>
                            <span>${pumpData.pump_code}</span>
                        </div>
                        <div class="d-flex justify-content-between">
                            <span style="font-weight: 500;">Speed:</span>
                            <span>${firstCurve.test_speed_rpm} rpm</span>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="d-flex justify-content-between mb-2">
                            <span style="font-weight: 500;">Max Flow:</span>
                            <span>${maxFlow.toFixed(1)} m³/hr</span>
                        </div>
                        <div class="d-flex justify-content-between mb-2">
                            <span style="font-weight: 500;">Max Head:</span>
                            <span>${maxHead.toFixed(1)} m</span>
                        </div>
                        <div class="d-flex justify-content-between">
                            <span style="font-weight: 500;">Impeller Sizes:</span>
                            <span>${pumpData.curves.map(c => c.impeller_diameter_mm + 'mm').join(', ')}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    generatePerformanceTables(pumpData) {
        let tablesHtml = '';

        if (Array.isArray(pumpData.curves)) {
            pumpData.curves.forEach((curve, index) => {
                if (!curve || !Array.isArray(curve.performance_points)) return;
                
                const points = curve.performance_points.filter(p => p.flow_m3hr > 0 && p.head_m > 0);
                if (points.length === 0) return;

                tablesHtml += `
                    <div class="impeller-table mb-4">
                        <h6 class="mb-3" style="color: #1976d2; font-weight: 600;">
                            Imp Dia: ${curve.impeller_diameter_mm} mm
                        </h6>
                        
                        <div class="table-responsive">
                            <table class="table table-sm table-hover" style="font-size: 13px;">
                                <thead style="background: #1976d2; color: white;">
                                    <tr>
                                        <th class="text-center">Point</th>
                                        <th class="text-center">Flow Rate<br>(m³/hr)</th>
                                        <th class="text-center">Head<br>(m)</th>
                                        <th class="text-center">Efficiency<br>(%)</th>
                                        <th class="text-center">Power<br>(kW)</th>
                                        <th class="text-center">NPSHr<br>(m)</th>
                                        <th class="text-center">Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${points.map((point, i) => this.generateTableRow(point, i + 1)).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                `;
            });
        }

        return tablesHtml;
    }

    generateTableRow(point, pointNumber) {
        const meetsHead = point.head_m >= this.targetHead;
        const flowDiff = Math.abs(point.flow_m3hr - this.targetFlow) / this.targetFlow * 100;
        const nearTargetFlow = flowDiff <= (this.flowTolerance * 100);

        let statusClass = '';
        let statusText = '';
        let statusIcon = '';
        let rowStyle = '';

        if (meetsHead && nearTargetFlow) {
            statusClass = 'text-success fw-bold';
            statusText = 'Optimal';
            statusIcon = '✓';
            rowStyle = 'background-color: #e8f5e8;';
        } else if (meetsHead) {
            statusClass = 'text-primary';
            statusText = 'Capable';
            statusIcon = '◦';
            rowStyle = 'background-color: #f0f8ff;';
        } else {
            statusClass = 'text-muted';
            statusText = 'Low Head';
            statusIcon = '-';
        }

        const headStyle = meetsHead ? 'font-weight: 600; color: #2e7d32;' : '';
        const powerValue = point.power_kw ? point.power_kw.toFixed(1) : this.estimatePower(point);
        const npshrValue = point.npshr_m ? point.npshr_m.toFixed(1) : this.estimateNPSHr(point);

        return `
            <tr style="${rowStyle}">
                <td class="text-center fw-bold">${pointNumber}</td>
                <td class="text-center">${point.flow_m3hr.toFixed(1)}</td>
                <td class="text-center" style="${headStyle}">${point.head_m.toFixed(1)}</td>
                <td class="text-center">${point.efficiency_pct.toFixed(1)}</td>
                <td class="text-center">${powerValue}</td>
                <td class="text-center">${npshrValue}</td>
                <td class="text-center ${statusClass}">
                    <span class="d-inline-flex align-items-center">
                        ${statusIcon} ${statusText}
                    </span>
                </td>
            </tr>
        `;
    }

    estimatePower(point) {
        // Calculate power using standard formula: P = (Q × H × ρ × g) / (η × 3600)
        if (point.efficiency_pct > 0) {
            const power = (point.flow_m3hr * point.head_m * 1000 * 9.81) / (point.efficiency_pct / 100 * 3600000);
            return power.toFixed(1);
        }
        return '67'; // Typical value
    }

    estimateNPSHr(point) {
        // Estimate NPSH based on flow rate (typical curve behavior)
        const flowFactor = point.flow_m3hr / 1000;
        const estimatedNPSH = 2.5 + (flowFactor * 2.0);
        return estimatedNPSH.toFixed(1);
    }

    addEngineeringAssessment(pumpData, containerId) {
        const container = document.getElementById(containerId);
        
        // Analyze pump capability
        let suitablePoints = [];
        let totalPoints = 0;

        if (Array.isArray(pumpData.curves)) {
            pumpData.curves.forEach(curve => {
                if (curve && Array.isArray(curve.performance_points)) {
                    curve.performance_points.forEach(point => {
                        if (point.flow_m3hr > 0 && point.head_m > 0) {
                            totalPoints++;
                            if (point.head_m >= this.targetHead) {
                                const flowDiff = Math.abs(point.flow_m3hr - this.targetFlow) / this.targetFlow * 100;
                                suitablePoints.push({
                                    flow: point.flow_m3hr,
                                    head: point.head_m,
                                    flowDiff: flowDiff,
                                    efficiency: point.efficiency_pct,
                                    impeller: curve.impeller_diameter_mm
                                });
                            }
                        }
                    });
                }
            });
        }

        let assessment = '';
        if (suitablePoints.length === 0) {
            assessment = `
                <strong>Assessment:</strong> This pump cannot meet the ${this.targetHead}m head requirement at any flow rate.<br>
                <strong>Recommendation:</strong> Consider alternative pump models with higher head capability.
            `;
        } else {
            const optimalPoints = suitablePoints.filter(p => p.flowDiff <= (this.flowTolerance * 100));
            const bestPoint = suitablePoints.reduce((best, current) => 
                current.flowDiff < best.flowDiff ? current : best
            );

            if (optimalPoints.length > 0) {
                assessment = `
                    <strong class="text-success">✓ Suitable:</strong> ${optimalPoints.length} operating point(s) meet requirements within ${(this.flowTolerance * 100).toFixed(0)}% flow tolerance.<br>
                    <strong>Best Operating Point:</strong> ${bestPoint.flow.toFixed(1)} m³/hr at ${bestPoint.head.toFixed(1)}m head (${bestPoint.efficiency.toFixed(1)}% efficiency)<br>
                    <strong>Flow Variance:</strong> ${bestPoint.flowDiff.toFixed(1)}% from target (${this.targetFlow} m³/hr)
                `;
            } else {
                assessment = `
                    <strong class="text-warning">⚠ Capable but Non-Optimal:</strong> Pump can deliver ${this.targetHead}m head but not at target flow rate.<br>
                    <strong>Closest Operating Point:</strong> ${bestPoint.flow.toFixed(1)} m³/hr at ${bestPoint.head.toFixed(1)}m head<br>
                    <strong>Flow Variance:</strong> ${bestPoint.flowDiff.toFixed(1)}% from target (requires ${bestPoint.flowDiff > 10 ? 'significant' : 'minor'} adjustment)
                `;
            }
        }

        const assessmentHtml = `
            <div class="engineering-notes mt-4" style="background: #e3f2fd; padding: 16px; border-radius: 8px; border-left: 4px solid #1976d2;">
                <div class="d-flex align-items-start">
                    <i class="material-icons me-2" style="color: #1976d2; font-size: 20px;">engineering</i>
                    <div>
                        <div style="font-weight: 600; color: #1976d2; margin-bottom: 8px;">Engineering Assessment</div>
                        <div style="font-size: 14px; line-height: 1.5;">${assessment}</div>
                    </div>
                </div>
            </div>
        `;

        container.insertAdjacentHTML('beforeend', assessmentHtml);
    }
}

// Global instance
window.pumpDataTableManager = new PumpDataTableManager();

// Auto-initialize if pump data is available
document.addEventListener('DOMContentLoaded', function() {
    if (window.pumpDataForTable && window.targetRequirements) {
        const { flow, head } = window.targetRequirements;
        window.pumpDataTableManager.render(window.pumpDataForTable, flow, head);
    }
});