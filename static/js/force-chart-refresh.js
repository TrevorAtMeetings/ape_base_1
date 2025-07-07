// Force refresh of chart styling - cache buster for red dot update
console.log('Force chart refresh script loaded - clearing chart cache');

// Clear any cached chart data and force reload
if (window.pumpChartsManager) {
    window.pumpChartsManager.currentChartData = null;
}

// Force browser to invalidate script cache
const timestamp = new Date().getTime();
console.log('Chart cache timestamp:', timestamp);

// Add cache-busting to any existing chart elements
document.addEventListener('DOMContentLoaded', function() {
    // Force re-render of any existing charts
    const chartContainers = ['head-flow-chart', 'efficiency-flow-chart', 'power-flow-chart', 'npshr-flow-chart'];
    if (Array.isArray(chartContainers)) {
        chartContainers.forEach(containerId => {
        const container = document.getElementById(containerId);
        if (container && container.innerHTML.trim()) {
            console.log('Clearing cached chart:', containerId);
            container.innerHTML = '';
        }
    });
    }
});