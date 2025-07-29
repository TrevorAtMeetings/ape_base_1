// APE Pumps Main JavaScript - Simplified Version
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Materialize components
    initializeMaterialize();
    
    // Ensure all form sections are visible
    showAllFormSections();
    
    // Setup form validation and submission
    setupFormHandling();
    
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