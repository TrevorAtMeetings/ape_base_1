// Direct legend positioning fix for Plotly charts
// This script overrides the default Plotly layout after charts are rendered

// Override the original Plotly.newPlot function to apply legend fixes
(function() {
    const originalNewPlot = Plotly.newPlot;
    
    Plotly.newPlot = function(graphDiv, data, layout, config) {
        // Apply legend positioning fix for professional pump report charts
        if (typeof graphDiv === 'string' && 
            ['headFlowChart', 'efficiencyFlowChart', 'powerFlowChart', 'npshrFlowChart'].includes(graphDiv)) {
            
            // Override layout to fix legend positioning
            layout = layout || {};
            layout.legend = {
                orientation: 'h',
                y: -0.25,
                x: 0.5,
                xanchor: 'center',
                yanchor: 'top'
            };
            layout.margin = {
                t: 80,
                b: 120,
                l: 80,
                r: 80
            };
        }
        
        return originalNewPlot.apply(this, arguments);
    };
})();

// Additional post-render fix
document.addEventListener('DOMContentLoaded', function() {
    // Monitor for chart rendering and apply fixes
    const observer = new MutationObserver(function(mutations) {
        if (Array.isArray(mutations)) {
            mutations.forEach(function(mutation) {
                if (mutation.addedNodes && mutation.addedNodes.length > 0) {
                    Array.from(mutation.addedNodes).forEach(function(node) {
                        if (node.nodeType === 1 && node.classList && node.classList.contains('plotly-graph-div')) {
                            const chartId = node.id;
                            if (['head-flow-chart', 'efficiency-flow-chart', 'power-flow-chart', 'npshr-flow-chart'].includes(chartId)) {
                                setTimeout(function() {
                                    try {
                                        Plotly.relayout(chartId, {
                                            'legend.orientation': 'h',
                                            'legend.y': -0.25,
                                            'legend.x': 0.5,
                                            'legend.xanchor': 'center',
                                            'legend.yanchor': 'top',
                                            'margin.b': 120
                                        });
                                    } catch (e) {
                                        console.log('Legend fix applied via relayout for', chartId);
                                    }
                                }, 100);
                            }
                        }
            });
        }
    });
    
    observer.observe(document.body, { childList: true, subtree: true });
});