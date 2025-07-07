/**
 * APE Pumps Micro-Interactions Enhancement
 * Smooth animations and enhanced user feedback
 */

class MicroInteractions {
    constructor() {
        this.init();
    }

    init() {
        this.setupFormEnhancements();
        this.setupButtonEnhancements();
        this.setupLoadingStates();
        this.setupScrollAnimations();
        this.setupValidationAnimations();
        this.setupChartAnimations();
        this.setupNavigationEnhancements();
    }

    setupFormEnhancements() {
        // Enhanced form submission with loading state
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                const submitBtn = form.querySelector('[type="submit"]');
                if (submitBtn) {
                    this.addLoadingState(submitBtn);
                }
            });
        });

        // Input field focus animations
        const inputs = document.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('focus', (e) => {
                this.animateInputFocus(e.target);
            });

            input.addEventListener('blur', (e) => {
                this.animateInputBlur(e.target);
            });

            // Real-time validation feedback
            input.addEventListener('input', (e) => {
                this.validateInputRealTime(e.target);
            });
        });
    }

    setupButtonEnhancements() {
        // Enhanced button interactions
        const buttons = document.querySelectorAll('.btn, .btn-large, .btn-small');
        buttons.forEach(button => {
            button.addEventListener('mouseenter', (e) => {
                this.animateButtonHover(e.target);
            });

            button.addEventListener('mouseleave', (e) => {
                this.resetButtonHover(e.target);
            });

            button.addEventListener('click', (e) => {
                this.animateButtonClick(e.target);
            });
        });
    }

    setupLoadingStates() {
        // Global loading state management
        const loadingIndicators = document.querySelectorAll('.loading-spinner');
        loadingIndicators.forEach(indicator => {
            this.observeLoadingState(indicator);
        });
    }

    setupScrollAnimations() {
        // Intersection Observer for scroll animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.animateElementIntoView(entry.target);
                }
            });
        }, observerOptions);

        // Observe elements with animation classes
        const animatedElements = document.querySelectorAll(
            '.fade-in-up, .stagger-item, .chart-container'
        );
        animatedElements.forEach(el => observer.observe(el));
    }

    setupValidationAnimations() {
        // Form validation with smooth animations
        const requiredFields = document.querySelectorAll('input[required], select[required]');
        requiredFields.forEach(field => {
            field.addEventListener('invalid', (e) => {
                this.animateValidationError(e.target);
            });

            field.addEventListener('input', (e) => {
                if (e.target.validity.valid) {
                    this.animateValidationSuccess(e.target);
                }
            });
        });
    }

    setupChartAnimations() {
        // Chart loading animations
        const chartContainers = document.querySelectorAll('[id*="chart"]');
        chartContainers.forEach((container, index) => {
            container.style.animationDelay = `${index * 0.2}s`;
            container.classList.add('chart-container');
        });
    }

    setupNavigationEnhancements() {
        // Navigation link animations
        const navLinks = document.querySelectorAll('nav a, .sidenav a');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                this.animateNavigation(e.target);
            });
        });

        // Mobile menu animation
        const mobileMenuTrigger = document.querySelector('.sidenav-trigger');
        if (mobileMenuTrigger) {
            mobileMenuTrigger.addEventListener('click', () => {
                this.animateMobileMenu();
            });
        }
    }

    // Animation Methods
    addLoadingState(button) {
        const originalContent = button.innerHTML;
        button.innerHTML = '<span class="loading-spinner"></span> Processing...';
        button.disabled = true;
        button.classList.add('loading');

        // Store original content for restoration
        button.dataset.originalContent = originalContent;
    }

    removeLoadingState(button) {
        if (button.dataset.originalContent) {
            button.innerHTML = button.dataset.originalContent;
            button.disabled = false;
            button.classList.remove('loading');
        }
    }

    animateInputFocus(input) {
        const field = input.closest('.input-field');
        if (field) {
            field.classList.add('focused');
            this.addGlow(input);
        }
    }

    animateInputBlur(input) {
        const field = input.closest('.input-field');
        if (field && input.value === '') {
            field.classList.remove('focused');
        }
        this.removeGlow(input);
    }

    validateInputRealTime(input) {
        const field = input.closest('.input-field');
        if (!field) return;

        // Remove previous validation classes
        field.classList.remove('valid', 'invalid');

        if (input.validity.valid && input.value !== '') {
            field.classList.add('valid');
            this.showSuccessIcon(input);
        } else if (!input.validity.valid && input.value !== '') {
            field.classList.add('invalid');
            this.showErrorIcon(input);
        }
    }

    animateButtonHover(button) {
        button.style.transform = 'translateY(-2px) scale(1.02)';
        button.style.boxShadow = '0 8px 25px rgba(0,0,0,0.15)';
    }

    resetButtonHover(button) {
        button.style.transform = '';
        button.style.boxShadow = '';
    }

    animateButtonClick(button) {
        button.style.transform = 'translateY(0px) scale(0.98)';
        setTimeout(() => {
            button.style.transform = '';
        }, 150);

        // Create ripple effect
        this.createRipple(button);
    }

    animateElementIntoView(element) {
        element.style.opacity = '1';
        element.style.transform = 'translateY(0)';
    }

    animateValidationError(field) {
        field.classList.add('shake');
        field.style.borderColor = '#f44336';
        
        setTimeout(() => {
            field.classList.remove('shake');
        }, 600);
    }

    animateValidationSuccess(field) {
        field.style.borderColor = '#4caf50';
        this.showCheckmark(field);
    }

    animateNavigation(link) {
        link.style.transform = 'scale(0.95)';
        setTimeout(() => {
            link.style.transform = '';
        }, 150);
    }

    animateMobileMenu() {
        const menu = document.querySelector('.sidenav');
        if (menu) {
            menu.style.transform = 'translateX(0)';
        }
    }

    // Helper Methods
    addGlow(element) {
        element.style.boxShadow = '0 0 0 2px rgba(25, 118, 210, 0.3)';
    }

    removeGlow(element) {
        element.style.boxShadow = '';
    }

    showSuccessIcon(input) {
        this.removeStatusIcon(input);
        const icon = document.createElement('i');
        icon.className = 'material-icons success-icon';
        icon.textContent = 'check_circle';
        icon.style.cssText = `
            position: absolute;
            right: 10px;
            top: 50%;
            transform: translateY(-50%);
            color: #4caf50;
            font-size: 20px;
            animation: checkmark 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        `;
        input.parentElement.style.position = 'relative';
        input.parentElement.appendChild(icon);
    }

    showErrorIcon(input) {
        this.removeStatusIcon(input);
        const icon = document.createElement('i');
        icon.className = 'material-icons error-icon';
        icon.textContent = 'error';
        icon.style.cssText = `
            position: absolute;
            right: 10px;
            top: 50%;
            transform: translateY(-50%);
            color: #f44336;
            font-size: 20px;
            animation: shake 0.3s ease;
        `;
        input.parentElement.style.position = 'relative';
        input.parentElement.appendChild(icon);
    }

    removeStatusIcon(input) {
        const existingIcons = input.parentElement.querySelectorAll('.success-icon, .error-icon');
        existingIcons.forEach(icon => icon.remove());
    }

    showCheckmark(field) {
        const checkmark = document.createElement('div');
        checkmark.innerHTML = '✓';
        checkmark.style.cssText = `
            position: absolute;
            right: -30px;
            top: 50%;
            transform: translateY(-50%);
            color: #4caf50;
            font-size: 18px;
            font-weight: bold;
            animation: checkmark 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        `;
        field.parentElement.style.position = 'relative';
        field.parentElement.appendChild(checkmark);

        setTimeout(() => checkmark.remove(), 2000);
    }

    createRipple(button) {
        const ripple = document.createElement('span');
        ripple.classList.add('ripple');
        ripple.style.cssText = `
            position: absolute;
            border-radius: 50%;
            background: rgba(255,255,255,0.4);
            transform: scale(0);
            animation: ripple 0.6s linear;
            pointer-events: none;
        `;

        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = (rect.width / 2 - size / 2) + 'px';
        ripple.style.top = (rect.height / 2 - size / 2) + 'px';

        button.style.position = 'relative';
        button.appendChild(ripple);

        setTimeout(() => ripple.remove(), 600);
    }

    observeLoadingState(indicator) {
        // Monitor loading indicators and add smooth transitions
        const observer = new MutationObserver((mutations) => {
            if (Array.isArray(mutations)) {
                mutations.forEach((mutation) => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
                    const isVisible = window.getComputedStyle(indicator).display !== 'none';
                    if (isVisible) {
                        indicator.style.opacity = '1';
                        indicator.style.transform = 'scale(1)';
                    } else {
                        indicator.style.opacity = '0';
                        indicator.style.transform = 'scale(0.8)';
                    }
                }
            });
            }
        });

        observer.observe(indicator, { attributes: true });
    }

    // Page-specific enhancements
    enhanceResultsPage() {
        // Animate pump cards on results page
        const pumpCards = document.querySelectorAll('.pump-card, .card');
        pumpCards.forEach((card, index) => {
            card.style.animationDelay = `${index * 0.1}s`;
            card.classList.add('stagger-item');
        });
    }

    enhanceComparisonPage() {
        // Animate comparison elements
        const comparisonItems = document.querySelectorAll('.pump-comparison-grid .pump-card');
        comparisonItems.forEach((item, index) => {
            item.style.animationDelay = `${index * 0.2}s`;
            item.classList.add('fade-in-up');
        });
    }

    // Form reset with animation
    resetFormWithAnimation() {
        const form = document.querySelector('#pumpSelectionForm');
        if (form) {
            // Animate form reset
            form.style.opacity = '0.5';
            form.style.transform = 'scale(0.98)';
            
            setTimeout(() => {
                form.reset();
                // Trigger Materialize updates
                M.updateTextFields();
                M.FormSelect.init(document.querySelectorAll('select'));
                
                form.style.opacity = '1';
                form.style.transform = 'scale(1)';
            }, 200);
        }
    }
}

// Auto-initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.microInteractions = new MicroInteractions();
    
    // Page-specific initializations
    if (document.querySelector('.pump-options-container')) {
        window.microInteractions.enhanceResultsPage();
    }
    
    if (document.querySelector('.pump-comparison-grid')) {
        window.microInteractions.enhanceComparisonPage();
    }
});

// Enhanced form reset function for global use
function resetForm() {
    if (window.microInteractions) {
        window.microInteractions.resetFormWithAnimation();
    }
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MicroInteractions;
}