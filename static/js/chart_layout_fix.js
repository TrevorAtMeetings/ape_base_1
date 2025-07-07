// Chart layout fix for professional pump report
// Override Plotly layouts to prevent legend overlap

document.addEventListener('DOMContentLoaded', function() {
    // Wait for charts to be rendered, then fix their layouts
    setTimeout(function() {
        const chartIds = ['headFlowChart', 'efficiencyFlowChart', 'powerFlowChart', 'npshrFlowChart'];
        
        if (Array.isArray(chartIds)) {
            chartIds.forEach(function(chartId) {
            const chartElement = document.getElementById(chartId);
            if (chartElement && chartElement.data) {
                // Update layout to fix legend positioning
                const update = {
                    'legend.orientation': 'h',
                    'legend.y': -0.25,
                    'legend.x': 0.5,
                    'legend.xanchor': 'center',
                    'legend.yanchor': 'top',
                    'margin.b': 120,
                    'margin.t': 80,
                    'margin.l': 80,
                    'margin.r': 80
                };
                
                Plotly.relayout(chartId, update);
            }
        });
        }
    }, 2000);
    
    // Additional fix - monitor for chart rendering completion
    const observer = new MutationObserver(function(mutations) {
        if (Array.isArray(mutations)) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' && mutation.addedNodes) {
                    Array.from(mutation.addedNodes).forEach(function(node) {
                        if (node.nodeType === 1 && node.classList && node.classList.contains('plotly-graph-div')) {
                        setTimeout(function() {
                            const chartId = node.id;
                            if (['head-flow-chart', 'efficiency-flow-chart', 'power-flow-chart', 'npshr-flow-chart'].includes(chartId)) {
                                const update = {
                                    'legend.orientation': 'h',
                                    'legend.y': -0.25,
                                    'legend.x': 0.5,
                                    'legend.xanchor': 'center',
                                    'legend.yanchor': 'top',
                                    'margin.b': 120
                                };
                                Plotly.relayout(chartId, update);
                            }
                        }, 500);
                        }
                    });
                }
            });
        }
    });
    
    observer.observe(document.body, { childList: true, subtree: true });
});