// APE Pumps Main JavaScript - Simplified Version
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Materialize components
    initializeMaterialize();
    
    // Ensure all form sections are visible
    showAllFormSections();
    
    // Setup form validation and submission
    setupFormHandling();
    
    // Setup essential requirements monitoring
    setupEssentialRequirementsWatcher();
    
    // Hide any persistent progress bars after page load
    hidePersistentProgressBars();
});

function hidePersistentProgressBars() {
    // Hide any progress bars that might be stuck visible
    const progressBars = document.querySelectorAll('.progress');
    progressBars.forEach(progressBar => {
        if (progressBar.style.display !== 'none') {
            // Add a small delay to ensure the page is fully loaded
            setTimeout(() => {
                progressBar.style.display = 'none';
            }, 1000);
        }
    });
    
    // Also hide any indeterminate progress bars specifically
    const indeterminateBars = document.querySelectorAll('.progress .indeterminate');
    indeterminateBars.forEach(bar => {
        const parent = bar.closest('.progress');
        if (parent && parent.style.display !== 'none') {
            setTimeout(() => {
                parent.style.display = 'none';
            }, 1000);
        }
    });
}

/**
 * Initialize all Materialize components
 */
function initializeMaterialize() {
    // Auto-initialize all components
    M.AutoInit();
    
    // Custom initialization for specific components
    const selects = document.querySelectorAll('select');
    M.FormSelect.init(selects);
    
    const tooltips = document.querySelectorAll('.tooltipped');
    M.Tooltip.init(tooltips);
    
    const modals = document.querySelectorAll('.modal');
    M.Modal.init(modals);
}

/**
 * Ensure all form sections are visible immediately
 */
function showAllFormSections() {
    const sections = document.querySelectorAll('.section-card');
    
    if (sections && sections.length > 0) {
        sections.forEach(function(section) {
            section.style.display = 'block';
            section.style.visibility = 'visible';
            section.style.opacity = '1';
            section.classList.remove('hidden-section', 'hidden');
        });
    }
    
    // Ensure submit button is visible
    const submitBtn = document.getElementById('submit-btn');
    if (submitBtn) {
        submitBtn.style.display = 'inline-block';
        submitBtn.style.visibility = 'visible';
    }
    
    // Ensure reset button is visible
    const resetBtn = document.querySelector('button[type="reset"]');
    if (resetBtn) {
        resetBtn.style.display = 'inline-block';
        resetBtn.style.visibility = 'visible';
    }
}

/**
 * Setup form handling and validation
 */
function setupFormHandling() {
    const form = document.getElementById('pumpSelectionForm');
    if (!form) return;
    
    // Form submission handling
    form.addEventListener('submit', function(e) {
        // Show loading state
        const submitBtn = document.getElementById('submit-btn');
        if (submitBtn) {
            submitBtn.innerHTML = '<i class="material-icons left">hourglass_empty</i>Processing...';
            submitBtn.disabled = true;
        }
    });
    
    // Reset button handling
    const resetBtn = document.querySelector('button[type="reset"]');
    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            // Reinitialize Materialize selects after reset
            setTimeout(function() {
                const selects = document.querySelectorAll('select');
                M.FormSelect.init(selects);
            }, 100);
        });
    }
}

/**
 * Reset form function for global access
 */
function resetForm() {
    const form = document.getElementById('pumpSelectionForm');
    if (form) {
        form.reset();
        // Reinitialize Materialize components
        setTimeout(function() {
            M.AutoInit();
        }, 100);
    }
}

/**
 * Monitor essential requirements and show/hide Find Best Pump button
 */
function setupEssentialRequirementsWatcher() {
    const flowInput = document.getElementById('flow_rate');
    const headInput = document.getElementById('total_head');
    const pumpTypeInputs = document.querySelectorAll('input[name="pump_type"]');
    const findBestPumpSection = document.getElementById('find-best-pump-section');
    
    if (!flowInput || !headInput || !pumpTypeInputs.length || !findBestPumpSection) {
        return;
    }
    
    function checkEssentialRequirements() {
        const flowValue = parseFloat(flowInput.value);
        const headValue = parseFloat(headInput.value);
        const pumpTypeSelected = Array.from(pumpTypeInputs).some(input => input.checked);
        
        const hasFlow = !isNaN(flowValue) && flowValue > 0;
        const hasHead = !isNaN(headValue) && headValue > 0;
        
        if (hasFlow && hasHead && pumpTypeSelected) {
            // Show the Find Best Pump button with smooth animation
            findBestPumpSection.style.display = 'block';
            setTimeout(() => {
                findBestPumpSection.style.opacity = '1';
                findBestPumpSection.style.transform = 'translateY(0)';
            }, 50);
        } else {
            // Hide the Find Best Pump button
            findBestPumpSection.style.opacity = '0';
            findBestPumpSection.style.transform = 'translateY(20px)';
            setTimeout(() => {
                if (findBestPumpSection.style.opacity === '0') {
                    findBestPumpSection.style.display = 'none';
                }
            }, 300);
        }
    }
    
    // Add event listeners
    flowInput.addEventListener('input', checkEssentialRequirements);
    flowInput.addEventListener('change', checkEssentialRequirements);
    headInput.addEventListener('input', checkEssentialRequirements);
    headInput.addEventListener('change', checkEssentialRequirements);
    
    pumpTypeInputs.forEach(input => {
        input.addEventListener('change', checkEssentialRequirements);
    });
    
    // Set initial styles for smooth transitions
    findBestPumpSection.style.transition = 'all 0.3s ease';
    findBestPumpSection.style.opacity = '0';
    findBestPumpSection.style.transform = 'translateY(20px)';
    
    // Check initially
    checkEssentialRequirements();
}