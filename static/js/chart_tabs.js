
function hideAllCharts(chartContainers) {
    chartContainers.forEach(container => {
        container.style.setProperty('display', 'none', 'important');
    });
}

function showChart(container) {
    container.style.setProperty('display', 'block', 'important');
}

document.addEventListener('DOMContentLoaded', function () {

    const tabButtons = document.querySelectorAll('[data-chart]');

    const chartContainers = document.querySelectorAll('[id*="-chart"]');

    // Hide all charts initially
    hideAllCharts(chartContainers);

    // Show only the first chart
    if (chartContainers.length > 0) {
        showChart(chartContainers[0]);
    }

    // Add click handlers
    tabButtons.forEach((button, idx) => {
        button.addEventListener('click', function() {

            // Hide all charts
            hideAllCharts(chartContainers);

            // Show the selected chart
            const chartId = this.getAttribute('data-chart') + '-chart';
            const targetChart = document.getElementById(chartId);
            if (targetChart) {
                showChart(targetChart);
            }

            // Update button styles
            tabButtons.forEach(btn => {
                btn.style.background = '#f5f5f5';
                btn.style.color = '#666';
            });
            this.style.background = '#1976d2';
            this.style.color = 'white';
        });
    });

    // MutationObserver to re-apply hiding logic if charts are re-rendered
    const observer = new MutationObserver(() => {
        // Only show the currently visible chart, hide others
        let shown = false;
        chartContainers.forEach(container => {
            if (container.style.display === 'block' && !shown) {
                showChart(container);
                shown = true;
            } else {
                hideAllCharts([container]);
            }
        });
    });

    chartContainers.forEach(container => {
        observer.observe(container, { attributes: true, attributeFilter: ['style'] });
    });
}); 